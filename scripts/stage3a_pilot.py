#!/usr/bin/env python3
"""Create and validate the Stage 3a pilot worklist from Stage 1/2 artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE2_DIR = ROOT / "data/jacs_2025/stage2"
STAGE3_DIR = ROOT / "data/jacs_2025/stage3"
DEFAULT_RECORDS = STAGE2_DIR / "curated-reaction-records.jsonl"
DEFAULT_SEED_SET = STAGE2_DIR / "feature-ready-seed-set.json"
DEFAULT_STAGE1_REPORT_DIR = ROOT / "data/jacs_2025/stage1/panel"
DEFAULT_STAGE3_CONTRACT = STAGE3_DIR / "stage3-contract.json"
DEFAULT_STAGE3_ENVIRONMENT = STAGE3_DIR / "stage3-environment.json"
DEFAULT_OUTPUT_DIR = STAGE3_DIR / "pilot"
DEFAULT_WORKLIST = DEFAULT_OUTPUT_DIR / "stage3a-lite-reference-optimization-worklist.jsonl"
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "stage3a-lite-pilot-manifest.json"
DEFAULT_SCAFFOLD_POLICY = DEFAULT_OUTPUT_DIR / "stage3a-scaffold-constraint-policy.json"
DEFAULT_STARTING_POSE_COUNT = 1


class PilotError(Exception):
    """Raised when the Stage 3a pilot worklist cannot be created or validated."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotError(message)


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def contract_substage(contract: dict[str, Any], substage_id: str) -> dict[str, Any]:
    matches = [substage for substage in contract.get("substages", []) if substage.get("substage_id") == substage_id]
    require(len(matches) == 1, f"Contract must define exactly one {substage_id} substage")
    return matches[0]


def selected_seed_ids(seed_set: dict[str, Any]) -> list[str]:
    ids = seed_set.get("selected_seed_substrate_ids")
    require(isinstance(ids, list) and len(ids) == 12, "Seed set must define the 12 selected Stage 3a pilot substrates")
    require(len(set(ids)) == len(ids), "Selected seed substrate ids must be unique")
    return ids


def stage1_report_path(report_dir: Path, substrate_id: str) -> Path:
    return report_dir / f"stage-1-smoke-{substrate_id}.json"


def load_stage1_report(report_dir: Path, substrate_id: str) -> dict[str, Any]:
    path = stage1_report_path(report_dir, substrate_id)
    require(path.exists(), f"{substrate_id}: missing Stage 1 report at {display_path(path)}")
    report = read_json(path)
    reported_ids = report.get("pose_generation_run", {}).get("substrate_ids", [])
    require(reported_ids == [substrate_id], f"{substrate_id}: Stage 1 report substrate id mismatch")
    return report


def selected_starting_poses(report: dict[str, Any], count: int) -> list[dict[str, Any]]:
    poses = list(report.get("pose_records", []))
    require(poses, "Stage 1 report has no pose records")
    low_energy = [pose for pose in poses if pose.get("selection_bucket") == "low_energy"]
    candidates = sorted(low_energy or poses, key=lambda pose: (pose.get("score_rank", 10**9), pose.get("pose_id", "")))
    require(len(candidates) >= count, f"Stage 1 report has only {len(candidates)} eligible starting poses")
    return candidates[:count]


def build_worklist(
    records: list[dict[str, Any]],
    seed_set: dict[str, Any],
    contract: dict[str, Any],
    environment: dict[str, Any],
    report_dir: Path,
    output_dir: Path,
    starting_pose_count: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    stage3a = contract_substage(contract, "stage3a_nci_guided_pose_v2")
    reference = stage3a["reference_optimization"]
    scaffold_policy = stage3a["scaffold_constraint_policy"]
    pose_generation = stage3a["pose_generation"]
    seed_ids = selected_seed_ids(seed_set)
    records_by_id = {record["substrate_id"]: record for record in records}

    require(
        1 <= starting_pose_count <= reference["starting_pose_count_range"][1],
        "Starting pose count must be between 1 and the Stage 3a contract maximum",
    )
    xtb_path = environment["chemistry_environment"]["tools"]["xtb"]["path"]
    worklist: list[dict[str, Any]] = []
    per_substrate_counts: dict[str, int] = {}

    for substrate_id in seed_ids:
        record = records_by_id.get(substrate_id)
        require(record is not None, f"{substrate_id}: selected seed is missing from Stage 2 records")
        require(record.get("curation_status") == "feature_ready", f"{substrate_id}: pilot substrate must be feature_ready")
        require(record.get("reaction_center", {}).get("review_status") == "checked", f"{substrate_id}: reaction center must be checked")

        report = load_stage1_report(report_dir, substrate_id)
        pose_run = report.get("pose_generation_run", {})
        for index, pose in enumerate(selected_starting_poses(report, starting_pose_count), start=1):
            geometry_path = resolve_path(pose["fe_bound_assembly_xyz_path"])
            require(geometry_path.exists(), f"{pose['pose_id']}: assembly XYZ is missing at {display_path(geometry_path)}")
            work_dir = output_dir / "reference-optimizations" / substrate_id / f"start-{index:04d}"
            worklist.append(
                {
                    "schema_version": "stage3a-reference-optimization-worklist-v1",
                    "work_item_id": f"stage3a-{substrate_id}-xtb-ref-{index:04d}",
                    "substrate_id": substrate_id,
                    "reaction_id": record["reaction_id"],
                    "family_id": record["family"]["family_id"],
                    "stage1_pose_id": pose["pose_id"],
                    "stage1_pose_generation_run_id": pose["pose_generation_run_id"],
                    "stage1_score_rank": pose["score_rank"],
                    "stage1_selection_bucket": pose["selection_bucket"],
                    "stage1_uff_pose_score": pose["uff_pose_score"],
                    "input_assembly_xyz_path": display_path(geometry_path),
                    "work_dir": display_path(work_dir),
                    "xtb_command_template": [
                        xtb_path,
                        str(geometry_path),
                        "--gfn",
                        "2",
                        "--alpb",
                        "ether",
                        "--opt",
                    ],
                    "optimization_contract": {
                        "method": reference["method"],
                        "solvent_model": reference["solvent_model"],
                        "dft_required_for_gate": reference["dft_required_for_gate"],
                    },
                    "scaffold_constraint_policy_id": "stage3a-core-frozen-ligand-restrained-v1",
                    "required_outputs": [
                        "optimized_complex_xyz",
                        "xtb_output_log",
                        "optimization_status",
                        "final_relative_energy",
                        "scaffold_deviation_summary",
                    ],
                    "provenance": {
                        "stage1_report_path": display_path(stage1_report_path(report_dir, substrate_id)),
                        "constraint_profile_id": pose_run.get("constraint_profile_id"),
                        "reference_geometry_id": pose_run.get("reference_geometry_id"),
                        "candidate_site_policy": contract["substrate_scope"]["candidate_site_policy"],
                        "reported_reactive_site": record["reaction_center"]["reported_reactive_site"],
                        "candidate_site_count": len(record["reaction_center"]["candidate_sites"]),
                        "frozen_core_atom_count": pose["frozen_core_atom_count"],
                    },
                }
            )
        per_substrate_counts[substrate_id] = starting_pose_count

    manifest = {
        "schema_version": "stage3a-pilot-manifest-v1",
        "pilot_id": "stage3a-lite-seed-12-single-reference-optimization-pilot",
        "status": "worklist_declared_not_yet_computed",
        "substrate_scope": "feature_ready_seed_12",
        "pilot_mode": "stage3a_lite_single_reference_per_substrate",
        "scale_up_policy": "increase_starting_pose_count_to_20_50_and_cluster_to_3_5_reference_motifs_after_lite_delta",
        "selected_seed_substrate_ids": seed_ids,
        "substrate_count": len(seed_ids),
        "starting_pose_count_per_substrate": starting_pose_count,
        "total_work_item_count": len(worklist),
        "per_substrate_work_item_counts": per_substrate_counts,
        "reference_optimization": reference,
        "pose_generation_contract": {
            "candidate_pose_count_per_substrate": pose_generation["candidate_pose_count_per_substrate"],
            "retained_pose_count_per_substrate": pose_generation["retained_pose_count_per_substrate"],
            "retention_policy": pose_generation["retention_policy"],
            "max_retained_per_viable_motif": pose_generation["max_retained_per_viable_motif"],
        },
        "worklist_path": display_path(DEFAULT_WORKLIST),
    }
    scaffold = {
        "schema_version": "stage3a-scaffold-constraint-policy-v1",
        "scaffold_constraint_policy_id": "stage3a-core-frozen-ligand-restrained-v1",
        "source_contract": "data/jacs_2025/stage3/stage3-contract.json",
        **scaffold_policy,
    }
    return worklist, manifest, scaffold


def validate_worklist(
    worklist_path: Path,
    manifest_path: Path,
    scaffold_policy_path: Path,
    records_path: Path,
    seed_set_path: Path,
) -> dict[str, Any]:
    worklist = read_jsonl(worklist_path)
    manifest = read_json(manifest_path)
    scaffold_policy = read_json(scaffold_policy_path)
    records = read_jsonl(records_path)
    seed_set = read_json(seed_set_path)
    seed_ids = selected_seed_ids(seed_set)
    records_by_id = {record["substrate_id"]: record for record in records}

    require(manifest.get("schema_version") == "stage3a-pilot-manifest-v1", "Invalid Stage 3a pilot manifest schema")
    require(scaffold_policy.get("schema_version") == "stage3a-scaffold-constraint-policy-v1", "Invalid scaffold policy schema")
    require(scaffold_policy.get("frozen_atom_groups"), "Scaffold policy must define frozen atom groups")
    require(scaffold_policy.get("restrained_atom_groups"), "Scaffold policy must define restrained atom groups")
    require(scaffold_policy.get("mobile_atom_groups") == ["substrate_atoms"], "Scaffold policy must keep substrate atoms mobile")
    require(len(worklist) == manifest["total_work_item_count"], "Worklist count disagrees with manifest")
    require(manifest["selected_seed_substrate_ids"] == seed_ids, "Pilot manifest seed ids drifted")
    require(manifest["substrate_count"] == 12, "Stage 3a pilot must contain 12 seed substrates")
    require(manifest["pilot_mode"] == "stage3a_lite_single_reference_per_substrate", "Pilot manifest must declare Stage 3a-lite mode")
    require(manifest["starting_pose_count_per_substrate"] >= 1, "Pilot must select at least one start per substrate")

    seen = set()
    counts = {substrate_id: 0 for substrate_id in seed_ids}
    for row in worklist:
        require(row.get("schema_version") == "stage3a-reference-optimization-worklist-v1", "Invalid worklist row schema")
        work_item_id = row.get("work_item_id")
        require(work_item_id not in seen, f"Duplicate work item id: {work_item_id}")
        seen.add(work_item_id)
        substrate_id = row.get("substrate_id")
        require(substrate_id in seed_ids, f"{substrate_id}: worklist row is outside the seed pilot")
        require(records_by_id[substrate_id]["curation_status"] == "feature_ready", f"{substrate_id}: worklist row is not feature_ready")
        require(resolve_path(row["input_assembly_xyz_path"]).exists(), f"{work_item_id}: input XYZ is missing")
        require(row.get("stage1_selection_bucket") == "low_energy", f"{work_item_id}: pilot starts must come from low-energy Stage 1 poses")
        command = row.get("xtb_command_template", [])
        require(command and command[0].endswith("/xtb"), f"{work_item_id}: xTB command template is missing")
        require("--alpb" in command and "ether" in command, f"{work_item_id}: xTB command must declare ALPB ether")
        require(row["optimization_contract"]["method"] == "GFN2-xTB", f"{work_item_id}: wrong optimization method")
        require(row["optimization_contract"]["dft_required_for_gate"] is False, f"{work_item_id}: DFT must not be a pilot gate")
        require(row["provenance"]["candidate_site_count"] > 0, f"{work_item_id}: missing candidate-site provenance")
        require(row["provenance"]["frozen_core_atom_count"] >= 2, f"{work_item_id}: missing frozen-core atom count")
        counts[substrate_id] += 1

    expected = manifest["starting_pose_count_per_substrate"]
    require(set(counts.values()) == {expected}, "Every pilot substrate must have the same number of starting poses")
    return {
        "manifest_path": display_path(manifest_path),
        "worklist_path": display_path(worklist_path),
        "scaffold_policy_path": display_path(scaffold_policy_path),
        "substrate_count": len(seed_ids),
        "work_item_count": len(worklist),
        "starting_pose_count_per_substrate": expected,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--seed-set", type=Path, default=DEFAULT_SEED_SET)
    parser.add_argument("--stage1-report-dir", type=Path, default=DEFAULT_STAGE1_REPORT_DIR)
    parser.add_argument("--stage3-contract", type=Path, default=DEFAULT_STAGE3_CONTRACT)
    parser.add_argument("--stage3-environment", type=Path, default=DEFAULT_STAGE3_ENVIRONMENT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--worklist", type=Path, default=DEFAULT_WORKLIST)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--scaffold-policy", type=Path, default=DEFAULT_SCAFFOLD_POLICY)
    parser.add_argument("--starting-pose-count", type=int, default=DEFAULT_STARTING_POSE_COUNT)
    parser.add_argument("--bootstrap", action="store_true", help="Write Stage 3a pilot artifacts.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.bootstrap:
            worklist, manifest, scaffold = build_worklist(
                read_jsonl(args.records),
                read_json(args.seed_set),
                read_json(args.stage3_contract),
                read_json(args.stage3_environment),
                args.stage1_report_dir,
                args.output_dir,
                args.starting_pose_count,
            )
            write_jsonl(args.worklist, worklist)
            write_json(args.manifest, manifest)
            write_json(args.scaffold_policy, scaffold)
            print(
                "Wrote Stage 3a pilot artifacts to "
                f"{display_path(args.worklist)}, {display_path(args.manifest)}, and {display_path(args.scaffold_policy)}"
            )
        report = validate_worklist(args.worklist, args.manifest, args.scaffold_policy, args.records, args.seed_set)
    except PilotError as exc:
        print(f"Stage 3a pilot validation failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

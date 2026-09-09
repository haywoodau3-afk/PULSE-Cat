#!/usr/bin/env python3
"""Extract Stage 3a-lite reference summaries from successful xTB optimizations."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import numpy


ROOT = Path(__file__).resolve().parents[1]
STAGE2_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
STAGE1_REPORT_DIR = ROOT / "data/jacs_2025/stage1/panel"
STAGE3_PILOT_DIR = ROOT / "data/jacs_2025/stage3/pilot"
STAGE3_FEATURE_DIR = ROOT / "data/jacs_2025/stage3/features"
DEFAULT_WORKLIST = STAGE3_PILOT_DIR / "stage3a-lite-reference-optimization-worklist.jsonl"
DEFAULT_RESULTS = STAGE3_PILOT_DIR / "stage3a-lite-constrained-reference-optimization-results.jsonl"
DEFAULT_SUMMARY = STAGE3_FEATURE_DIR / "stage3a-lite-reference-summary.jsonl"
DEFAULT_CENTERS = STAGE3_FEATURE_DIR / "local-3d-shell-centers.jsonl"
DEFAULT_SHELL_FEATURES = STAGE3_FEATURE_DIR / "local-3d-shell-features.jsonl"
STAGE2_POSE_INTERACTION = ROOT / "scripts/stage2_pose_interaction.py"
STAGE3A_LOCAL_SHELL = ROOT / "scripts/stage3a_local_shell_features.py"
FE_ATOM_INDEX_ONE_BASED = 47


stage2_spec = importlib.util.spec_from_file_location("stage2_pose_interaction", STAGE2_POSE_INTERACTION)
stage2_pose_interaction = importlib.util.module_from_spec(stage2_spec)
assert stage2_spec.loader is not None
stage2_spec.loader.exec_module(stage2_pose_interaction)

shell_spec = importlib.util.spec_from_file_location("stage3a_local_shell_features", STAGE3A_LOCAL_SHELL)
stage3a_local_shell_features = importlib.util.module_from_spec(shell_spec)
assert shell_spec.loader is not None
shell_spec.loader.exec_module(stage3a_local_shell_features)


class ReferenceFeatureError(Exception):
    """Raised when Stage 3a reference features cannot be extracted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReferenceFeatureError(message)


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def xyz_list(array: numpy.ndarray) -> list[float]:
    return [round(float(value), 6) for value in array]


def distance(left: numpy.ndarray, right: numpy.ndarray) -> float:
    return float(numpy.linalg.norm(left - right))


def angle_degrees(left: numpy.ndarray, vertex: numpy.ndarray, right: numpy.ndarray) -> float | None:
    left_vector = left - vertex
    right_vector = right - vertex
    denominator = numpy.linalg.norm(left_vector) * numpy.linalg.norm(right_vector)
    if denominator == 0:
        return None
    cosine = float(numpy.dot(left_vector, right_vector) / denominator)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def rounded(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(value, digits)


def parse_xyz(path: Path) -> list[dict[str, Any]]:
    atoms = stage2_pose_interaction.parse_xyz(path)
    for index, atom in enumerate(atoms, start=1):
        atom["index_one_based"] = index
    return atoms


def report_pose_by_id(report: dict[str, Any], pose_id: str) -> dict[str, Any]:
    matches = [pose for pose in report.get("pose_records", []) if pose.get("pose_id") == pose_id]
    require(len(matches) == 1, f"{pose_id}: expected exactly one Stage 1 pose record")
    return matches[0]


def atom_ownership(frozen_core_atom_count: int, atom_count: int) -> list[dict[str, Any]]:
    return [
        {
            "index_one_based": index,
            "owner": "core" if index <= frozen_core_atom_count else "substrate",
        }
        for index in range(1, atom_count + 1)
    ]


def scaffold_deviation(input_atoms: list[dict[str, Any]], optimized_atoms: list[dict[str, Any]], frozen_core_atom_count: int) -> dict[str, Any]:
    require(len(input_atoms) == len(optimized_atoms), "Input and optimized XYZ atom counts differ")
    displacements = [
        distance(input_atoms[index]["xyz"], optimized_atoms[index]["xyz"])
        for index in range(frozen_core_atom_count)
    ]
    fe_index = FE_ATOM_INDEX_ONE_BASED - 1
    return {
        "frozen_core_atom_count": frozen_core_atom_count,
        "frozen_core_rmsd_angstrom": rounded(math.sqrt(mean([value * value for value in displacements]))),
        "frozen_core_displacement_mean_angstrom": rounded(mean(displacements)),
        "frozen_core_displacement_max_angstrom": rounded(max(displacements)),
        "fe_displacement_angstrom": rounded(distance(input_atoms[fe_index]["xyz"], optimized_atoms[fe_index]["xyz"])),
    }


def map_candidate_sites(record: dict[str, Any], posed_molecule: Any, frozen_core_atom_count: int) -> dict[int, int]:
    atom_map_to_stage1 = stage2_pose_interaction.map_ids_to_stage1_atom_indices(record, posed_molecule)
    stage1_to_assembly = stage2_pose_interaction.stage1_index_to_assembly_index(posed_molecule, frozen_core_atom_count)
    return {
        atom_map_id: stage1_to_assembly[stage1_index]
        for atom_map_id, stage1_index in atom_map_to_stage1.items()
        if stage1_index in stage1_to_assembly
    }


def transferable_hydrogen_assembly_index(
    posed_molecule: Any,
    candidate_stage1_index: int,
    optimized_atoms: list[dict[str, Any]],
    stage1_to_assembly: dict[int, int],
) -> int | None:
    candidate_atom = posed_molecule.GetAtomWithIdx(candidate_stage1_index)
    hydrogen_indices = [neighbor.GetIdx() for neighbor in candidate_atom.GetNeighbors() if neighbor.GetSymbol() == "H"]
    if not hydrogen_indices:
        return None
    nitrene_xyz = optimized_atoms[stage1_to_assembly[0]]["xyz"]
    return stage1_to_assembly[
        min(
            hydrogen_indices,
            key=lambda hydrogen_index: distance(nitrene_xyz, optimized_atoms[stage1_to_assembly[hydrogen_index]]["xyz"]),
        )
    ]


def build_rows_for_result(
    result: dict[str, Any],
    work_item: dict[str, Any],
    record: dict[str, Any],
    stage1_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    require(result["optimization_status"] == "success", f"{result['work_item_id']}: result is not successful")
    pose = report_pose_by_id(stage1_report, result["stage1_pose_id"])
    input_atoms = parse_xyz(resolve_path(result["local_input_xyz_path"]))
    optimized_atoms = parse_xyz(resolve_path(result["optimized_complex_xyz_path"]))
    frozen_core_atom_count = int(pose["frozen_core_atom_count"])
    nitrene_index = int(pose["assembly_anchor_atom_index_one_based"]) - 1
    fe_index = FE_ATOM_INDEX_ONE_BASED - 1
    nitrene_xyz = optimized_atoms[nitrene_index]["xyz"]
    fe_xyz = optimized_atoms[fe_index]["xyz"]
    scaffold = scaffold_deviation(input_atoms, optimized_atoms, frozen_core_atom_count)

    posed_molecule = stage2_pose_interaction.stage1_pose_molecule(pose["input_nitrene_smiles"])
    atom_map_to_stage1 = stage2_pose_interaction.map_ids_to_stage1_atom_indices(record, posed_molecule)
    stage1_to_assembly = stage2_pose_interaction.stage1_index_to_assembly_index(posed_molecule, frozen_core_atom_count)
    atom_map_to_assembly = map_candidate_sites(record, posed_molecule, frozen_core_atom_count)
    ownership = atom_ownership(frozen_core_atom_count, len(optimized_atoms))

    summary_rows = []
    center_rows = []
    for candidate_site in record["reaction_center"]["candidate_sites"]:
        atom_map_id = candidate_site["atom_map_id"]
        if atom_map_id not in atom_map_to_assembly:
            continue
        candidate_stage1_index = atom_map_to_stage1[atom_map_id]
        candidate_assembly_index = atom_map_to_assembly[atom_map_id]
        transferable_h_index = transferable_hydrogen_assembly_index(
            posed_molecule,
            candidate_stage1_index,
            optimized_atoms,
            stage1_to_assembly,
        )
        if transferable_h_index is None:
            continue
        candidate_c_xyz = optimized_atoms[candidate_assembly_index]["xyz"]
        transferable_h_xyz = optimized_atoms[transferable_h_index]["xyz"]
        c_h_midpoint = (candidate_c_xyz + transferable_h_xyz) / 2.0
        approach_midpoint = (nitrene_xyz + transferable_h_xyz) / 2.0
        fe_n_candidate_c_angle = angle_degrees(fe_xyz, nitrene_xyz, candidate_c_xyz)
        n_c_h_angle = angle_degrees(nitrene_xyz, candidate_c_xyz, transferable_h_xyz)

        candidate_site_id = candidate_site["site_id"]
        summary_rows.append(
            {
                "schema_version": "stage3a-lite-reference-summary-v1",
                "substrate_id": result["substrate_id"],
                "reaction_id": result["reaction_id"],
                "work_item_id": result["work_item_id"],
                "stage1_pose_id": result["stage1_pose_id"],
                "candidate_site_id": candidate_site_id,
                "candidate_atom_map_id": atom_map_id,
                "candidate_site_type": candidate_site.get("site_type"),
                "is_reported_reactive_site": candidate_site_id == record["reaction_center"]["reported_reactive_site"]["site_id"],
                "feature_status": "computed_from_stage3a_lite_xtb_reference",
                "feature_blocks": {
                    "stage3a_lite_reference": {
                        "final_energy_hartree": result["final_energy_hartree"],
                        "nitrene_n_to_candidate_c_distance_angstrom": rounded(distance(nitrene_xyz, candidate_c_xyz)),
                        "nitrene_n_to_transferable_h_distance_angstrom": rounded(distance(nitrene_xyz, transferable_h_xyz)),
                        "candidate_c_to_transferable_h_distance_angstrom": rounded(distance(candidate_c_xyz, transferable_h_xyz)),
                        "fe_n_candidate_c_angle_degrees": rounded(fe_n_candidate_c_angle),
                        "nitrene_n_candidate_c_transferable_h_angle_degrees": rounded(n_c_h_angle),
                        **scaffold,
                    }
                },
                "provenance": {
                    "optimized_complex_xyz_path": result["optimized_complex_xyz_path"],
                    "xtb_stdout_log_path": result["xtb_stdout_log_path"],
                    "scaffold_constraint_policy_id": result["provenance"]["scaffold_constraint_policy_id"],
                    "candidate_assembly_index_one_based": candidate_assembly_index + 1,
                    "transferable_h_assembly_index_one_based": transferable_h_index + 1,
                    "nitrene_assembly_index_one_based": nitrene_index + 1,
                    "fe_atom_index_one_based": FE_ATOM_INDEX_ONE_BASED,
                },
            }
        )
        center_rows.append(
            {
                "schema_version": "stage3a-local-3d-shell-centers-v1",
                "substrate_id": result["substrate_id"],
                "pose_id": result["work_item_id"],
                "candidate_site_id": candidate_site_id,
                "geometry_path": result["optimized_complex_xyz_path"],
                "center_source": "stage3a_lite_xtb_reference_geometry",
                "centers": {
                    "nitrene_center": {"xyz": xyz_list(nitrene_xyz), "atom_index_one_based": nitrene_index + 1},
                    "candidate_c_h_haa_center": {
                        "xyz": xyz_list(c_h_midpoint),
                        "candidate_c_index_one_based": candidate_assembly_index + 1,
                        "transferable_h_index_one_based": transferable_h_index + 1,
                    },
                    "reactive_approach_midpoint": {
                        "xyz": xyz_list(approach_midpoint),
                        "nitrene_index_one_based": nitrene_index + 1,
                        "transferable_h_index_one_based": transferable_h_index + 1,
                    },
                },
                "atom_ownership": ownership,
                "provenance": {
                    "work_item_id": result["work_item_id"],
                    "candidate_atom_map_id": atom_map_id,
                    "candidate_site_type": candidate_site.get("site_type"),
                },
            }
        )
    return summary_rows, center_rows


def extract_reference_features(
    worklist_path: Path,
    results_path: Path,
    records_path: Path,
    stage1_report_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    worklist = {row["work_item_id"]: row for row in read_jsonl(worklist_path)}
    records = {row["substrate_id"]: row for row in read_jsonl(records_path)}
    summaries: list[dict[str, Any]] = []
    centers: list[dict[str, Any]] = []
    for result in read_jsonl(results_path):
        if result["optimization_status"] != "success":
            continue
        work_item = worklist[result["work_item_id"]]
        record = records[result["substrate_id"]]
        stage1_report = read_json(stage1_report_dir / f"stage-1-smoke-{result['substrate_id']}.json")
        result_summaries, result_centers = build_rows_for_result(result, work_item, record, stage1_report)
        summaries.extend(result_summaries)
        centers.extend(result_centers)
    return summaries, centers


def validate_outputs(summary_path: Path, centers_path: Path, shell_features_path: Path) -> dict[str, Any]:
    summaries = read_jsonl(summary_path)
    centers = read_jsonl(centers_path)
    shell_features = read_jsonl(shell_features_path)
    require(summaries, "Reference summary output is empty")
    require(len(summaries) == len(centers), "Reference summary and center row counts differ")
    require(len(centers) == len(shell_features), "Center and shell feature row counts differ")
    summary_keys = {(row["substrate_id"], row["work_item_id"], row["candidate_site_id"]) for row in summaries}
    center_keys = {(row["substrate_id"], row["pose_id"], row["candidate_site_id"]) for row in centers}
    shell_keys = {(row["substrate_id"], row["pose_id"], row["candidate_site_id"]) for row in shell_features}
    require(summary_keys == center_keys == shell_keys, "Summary, center, and shell feature keys differ")
    substrate_ids = {row["substrate_id"] for row in summaries}
    reported_count = sum(1 for row in summaries if row["is_reported_reactive_site"])
    require(reported_count == len(substrate_ids), "Each substrate must have exactly one reported-site summary")
    return {
        "summary_path": display_path(summary_path),
        "centers_path": display_path(centers_path),
        "shell_features_path": display_path(shell_features_path),
        "substrate_count": len(substrate_ids),
        "candidate_site_summary_count": len(summaries),
        "reported_site_summary_count": reported_count,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worklist", type=Path, default=DEFAULT_WORKLIST)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--records", type=Path, default=STAGE2_RECORDS)
    parser.add_argument("--stage1-report-dir", type=Path, default=STAGE1_REPORT_DIR)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--centers-output", type=Path, default=DEFAULT_CENTERS)
    parser.add_argument("--shell-features-output", type=Path, default=DEFAULT_SHELL_FEATURES)
    parser.add_argument("--write", action="store_true", help="Write summary, center, and shell-feature artifacts.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.write:
            summaries, centers = extract_reference_features(args.worklist, args.results, args.records, args.stage1_report_dir)
            write_jsonl(args.summary_output, summaries)
            write_jsonl(args.centers_output, centers)
            shell_rows = stage3a_local_shell_features.extract_features(args.centers_output)
            stage3a_local_shell_features.write_jsonl(args.shell_features_output, shell_rows)
            print(
                "Wrote Stage 3a reference features to "
                f"{display_path(args.summary_output)}, {display_path(args.centers_output)}, "
                f"and {display_path(args.shell_features_output)}"
            )
        report = validate_outputs(args.summary_output, args.centers_output, args.shell_features_output)
    except ReferenceFeatureError as exc:
        print(f"Stage 3a reference feature extraction failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Stage 3a reference feature extraction failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

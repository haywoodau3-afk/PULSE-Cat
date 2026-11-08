#!/usr/bin/env python3
"""Select Stage 1-v2 poses using Stage 3a-lite xTB reference geometry rules."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POSE_INTERACTION = ROOT / "data/jacs_2025/stage2/features/pose-interaction.jsonl"
DEFAULT_REFERENCE_SUMMARY = ROOT / "data/jacs_2025/stage3/features/stage3a-lite-reference-summary.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "data/jacs_2025/stage3/v2-pose"
DEFAULT_SELECTED_POSES = DEFAULT_OUTPUT_DIR / "stage1-v2-pose-selection.jsonl"
DEFAULT_SUMMARY = DEFAULT_OUTPUT_DIR / "stage1-v2-pose-summary.jsonl"
DEFAULT_RULE_PACKETS = DEFAULT_OUTPUT_DIR / "stage1-v2-rule-packets.jsonl"
SCHEMA_VERSION = "stage1-v2-reported-site-anchor-selection-v1"
RULE_SCHEMA_VERSION = "stage1-v2-rule-packet-v1"
SUMMARY_SCHEMA_VERSION = "stage1-v2-pose-summary-v1"


class Stage1V2PoseSelectionError(Exception):
    """Raised when Stage 1-v2 pose selection cannot be completed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage1V2PoseSelectionError(message)


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def reported_references(reference_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    references = {}
    for row in reference_rows:
        if row.get("is_reported_reactive_site"):
            substrate_id = row["substrate_id"]
            require(substrate_id not in references, f"{substrate_id}: duplicate reported Stage 3a reference row")
            references[substrate_id] = row
    return references


def pose_rows_by_substrate(pose_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pose_rows:
        grouped[row["substrate_id"]].append(row)
    return dict(grouped)


def min_max(values: list[float]) -> tuple[float, float]:
    return min(values), max(values)


def normalized(value: float, minimum: float, maximum: float) -> float:
    if maximum == minimum:
        return 0.0
    return (value - minimum) / (maximum - minimum)


def build_rule_packet(reference: dict[str, Any], retain_count: int) -> dict[str, Any]:
    features = reference["feature_blocks"]["stage3a_lite_reference"]
    provenance = reference["provenance"]
    return {
        "schema_version": RULE_SCHEMA_VERSION,
        "substrate_id": reference["substrate_id"],
        "reaction_id": reference["reaction_id"],
        "anchor_policy": "reported_reactive_site_from_stage2_pose_rows",
        "motif_id": "stage3a-lite-single-xtb-reference-reported-site",
        "work_item_id": reference["work_item_id"],
        "reference_stage1_pose_id": reference["stage1_pose_id"],
        "reference_candidate_site_id": reference["candidate_site_id"],
        "reference_candidate_atom_map_id": reference["candidate_atom_map_id"],
        "reference_candidate_site_type": reference["candidate_site_type"],
        "reference_geometry": {
            "nitrene_n_to_candidate_c_distance_angstrom": features["nitrene_n_to_candidate_c_distance_angstrom"],
            "nitrene_n_to_transferable_h_distance_angstrom": features["nitrene_n_to_transferable_h_distance_angstrom"],
            "fe_n_candidate_c_angle_degrees": features["fe_n_candidate_c_angle_degrees"],
            "nitrene_n_candidate_c_transferable_h_angle_degrees": features["nitrene_n_candidate_c_transferable_h_angle_degrees"],
            "candidate_c_to_transferable_h_distance_angstrom": features["candidate_c_to_transferable_h_distance_angstrom"],
        },
        "selection_contract": {
            "candidate_source": "stage2 pose-interaction rows generated from Stage 1 retained poses",
            "eventual_target_pool_size": 5000,
            "current_candidate_pool": "existing_stage1_retained_poses",
            "retain_count": retain_count,
            "distance_delta_scale_angstrom": 1.0,
            "angle_delta_scale_degrees": 30.0,
            "clash_penalty_weight": 2.0,
            "close_contact_floor_angstrom": 1.0,
            "close_contact_penalty_weight": 5.0,
            "uff_relative_weight": 0.25,
        },
        "provenance": {
            "optimized_complex_xyz_path": provenance["optimized_complex_xyz_path"],
            "xtb_stdout_log_path": provenance["xtb_stdout_log_path"],
            "scaffold_constraint_policy_id": provenance["scaffold_constraint_policy_id"],
            "stage3a_reference_schema_version": reference["schema_version"],
        },
    }


def score_pose(pose: dict[str, Any], reference: dict[str, Any], uff_min: float, uff_max: float) -> dict[str, Any]:
    pose_features = pose["feature_blocks"]["pose_interaction"]
    reference_features = reference["feature_blocks"]["stage3a_lite_reference"]

    n_c_delta = abs(
        pose_features["nitrene_n_to_reported_c_distance_angstrom"]
        - reference_features["nitrene_n_to_candidate_c_distance_angstrom"]
    )
    n_h_delta = abs(
        pose_features["nitrene_n_to_transferred_h_distance_angstrom"]
        - reference_features["nitrene_n_to_transferable_h_distance_angstrom"]
    )
    fe_n_c_angle_delta = abs(
        pose_features["fe_n_reported_c_angle_degrees"]
        - reference_features["fe_n_candidate_c_angle_degrees"]
    )
    n_c_h_angle_delta = abs(
        pose_features["nitrene_n_reported_c_transferred_h_angle_degrees"]
        - reference_features["nitrene_n_candidate_c_transferable_h_angle_degrees"]
    )
    clash_count = float(pose_features["core_substrate_covalent_floor_clash_count"])
    min_core_distance = float(pose_features["minimum_core_substrate_distance_angstrom"])
    close_contact_penalty = max(0.0, 1.0 - min_core_distance) * 5.0
    uff_relative = normalized(float(pose_features["uff_pose_score"]), uff_min, uff_max)
    total = (
        n_c_delta
        + n_h_delta
        + (fe_n_c_angle_delta / 30.0)
        + (n_c_h_angle_delta / 30.0)
        + (clash_count * 2.0)
        + close_contact_penalty
        + (uff_relative * 0.25)
    )

    return {
        "n_c_distance_abs_delta_angstrom": rounded(n_c_delta),
        "n_h_distance_abs_delta_angstrom": rounded(n_h_delta),
        "fe_n_c_angle_abs_delta_degrees": rounded(fe_n_c_angle_delta),
        "n_c_h_angle_abs_delta_degrees": rounded(n_c_h_angle_delta),
        "clash_penalty": rounded(clash_count * 2.0),
        "close_contact_penalty": rounded(close_contact_penalty),
        "uff_relative_score": rounded(uff_relative),
        "v2_pose_score": rounded(total),
    }


def select_for_substrate(reference: dict[str, Any], poses: list[dict[str, Any]], retain_count: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require(poses, f"{reference['substrate_id']}: no Stage 2 pose-interaction rows available")
    uff_values = [float(pose["feature_blocks"]["pose_interaction"]["uff_pose_score"]) for pose in poses]
    uff_min, uff_max = min_max(uff_values)
    scored = []
    for pose in poses:
        score = score_pose(pose, reference, uff_min, uff_max)
        pose_features = pose["feature_blocks"]["pose_interaction"]
        scored.append(
            {
                "schema_version": SCHEMA_VERSION,
                "substrate_id": pose["substrate_id"],
                "reaction_id": pose["reaction_id"],
                "pose_generation_run_id": pose["pose_generation_run_id"],
                "pose_id": pose["pose_id"],
                "selection_rank": 0,
                "anchor_policy": "reported_reactive_site_from_stage2_pose_rows",
                "motif_id": "stage3a-lite-single-xtb-reference-reported-site",
                "feature_status": "selected_by_stage3a_lite_reference_geometry",
                "feature_blocks": {
                    "stage1_v2_pose_selection": {
                        **score,
                        "reference_nitrene_n_to_candidate_c_distance_angstrom": reference["feature_blocks"]["stage3a_lite_reference"][
                            "nitrene_n_to_candidate_c_distance_angstrom"
                        ],
                        "reference_nitrene_n_to_transferable_h_distance_angstrom": reference["feature_blocks"]["stage3a_lite_reference"][
                            "nitrene_n_to_transferable_h_distance_angstrom"
                        ],
                        "reference_fe_n_candidate_c_angle_degrees": reference["feature_blocks"]["stage3a_lite_reference"][
                            "fe_n_candidate_c_angle_degrees"
                        ],
                        "pose_nitrene_n_to_reported_c_distance_angstrom": pose_features[
                            "nitrene_n_to_reported_c_distance_angstrom"
                        ],
                        "pose_nitrene_n_to_transferred_h_distance_angstrom": pose_features[
                            "nitrene_n_to_transferred_h_distance_angstrom"
                        ],
                        "pose_fe_n_reported_c_angle_degrees": pose_features["fe_n_reported_c_angle_degrees"],
                        "pose_uff_pose_score": pose_features["uff_pose_score"],
                        "pose_core_substrate_covalent_floor_clash_count": pose_features[
                            "core_substrate_covalent_floor_clash_count"
                        ],
                        "pose_minimum_core_substrate_distance_angstrom": pose_features[
                            "minimum_core_substrate_distance_angstrom"
                        ],
                    }
                },
                "provenance": {
                    "stage2_pose_interaction_schema_version": pose["schema_version"],
                    "stage3a_reference_schema_version": reference["schema_version"],
                    "source_fe_bound_assembly_xyz_path": pose["provenance"]["fe_bound_assembly_xyz_path"],
                    "source_stage1_report_path": pose["provenance"]["stage1_report_path"],
                    "reference_optimized_complex_xyz_path": reference["provenance"]["optimized_complex_xyz_path"],
                    "reference_work_item_id": reference["work_item_id"],
                    "reported_reactive_site": pose["provenance"]["reported_reactive_site"],
                },
            }
        )
    selected = sorted(scored, key=lambda row: (row["feature_blocks"]["stage1_v2_pose_selection"]["v2_pose_score"], row["pose_id"]))[
        :retain_count
    ]
    for rank, row in enumerate(selected, start=1):
        row["selection_rank"] = rank

    scores = [row["feature_blocks"]["stage1_v2_pose_selection"]["v2_pose_score"] for row in selected]
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "substrate_id": reference["substrate_id"],
        "reaction_id": reference["reaction_id"],
        "candidate_pose_count": len(poses),
        "selected_pose_count": len(selected),
        "requested_retain_count": retain_count,
        "underfilled": len(selected) < retain_count,
        "anchor_policy": "reported_reactive_site_from_stage2_pose_rows",
        "motif_id": "stage3a-lite-single-xtb-reference-reported-site",
        "reference_candidate_site_id": reference["candidate_site_id"],
        "score_summary": {
            "min_v2_pose_score": rounded(min(scores)),
            "median_v2_pose_score": rounded(median(scores)),
            "max_v2_pose_score": rounded(max(scores)),
        },
        "provenance": {
            "reference_work_item_id": reference["work_item_id"],
            "reference_optimized_complex_xyz_path": reference["provenance"]["optimized_complex_xyz_path"],
        },
    }
    return selected, summary


def select_stage1_v2_poses(
    pose_interaction_path: Path,
    reference_summary_path: Path,
    selected_output_path: Path,
    summary_output_path: Path,
    rule_packet_output_path: Path,
    retain_count: int,
) -> dict[str, Any]:
    require(retain_count > 0, "retain_count must be positive")
    pose_rows = read_jsonl(pose_interaction_path)
    references = reported_references(read_jsonl(reference_summary_path))
    grouped_poses = pose_rows_by_substrate(pose_rows)

    selected_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    rule_packets: list[dict[str, Any]] = []
    for substrate_id in sorted(references):
        reference = references[substrate_id]
        selected, summary = select_for_substrate(reference, grouped_poses.get(substrate_id, []), retain_count)
        selected_rows.extend(selected)
        summary_rows.append(summary)
        rule_packets.append(build_rule_packet(reference, retain_count))

    write_jsonl(selected_output_path, selected_rows)
    write_jsonl(summary_output_path, summary_rows)
    write_jsonl(rule_packet_output_path, rule_packets)
    return {
        "schema_version": "stage1-v2-pose-selection-run-report-v1",
        "substrate_count": len(references),
        "selected_pose_count": len(selected_rows),
        "retain_count": retain_count,
        "selected_pose_output": display_path(selected_output_path),
        "summary_output": display_path(summary_output_path),
        "rule_packet_output": display_path(rule_packet_output_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pose-interaction", type=Path, default=DEFAULT_POSE_INTERACTION)
    parser.add_argument("--reference-summary", type=Path, default=DEFAULT_REFERENCE_SUMMARY)
    parser.add_argument("--selected-output", type=Path, default=DEFAULT_SELECTED_POSES)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--rule-packet-output", type=Path, default=DEFAULT_RULE_PACKETS)
    parser.add_argument("--retain-count", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = select_stage1_v2_poses(
        args.pose_interaction,
        args.reference_summary,
        args.selected_output,
        args.summary_output,
        args.rule_packet_output,
        args.retain_count,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

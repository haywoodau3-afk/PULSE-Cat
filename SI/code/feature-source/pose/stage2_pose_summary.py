#!/usr/bin/env python3
"""Generate Stage 2 pose-summary features from Stage 1 report artifacts."""

from __future__ import annotations

import argparse
import json
import math
import platform
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_REPORT_DIR = ROOT / "data/jacs_2025/stage1/panel"
DEFAULT_OUTPUT = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def quantile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    sorted_values = sorted(values)
    position = fraction * (len(sorted_values) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    lower = sorted_values[lower_index]
    upper = sorted_values[upper_index]
    weight = position - lower_index
    return lower + (upper - lower) * weight


def numeric_summary(values: list[float], prefix: str) -> dict[str, float | int | None]:
    if not values:
        return {
            f"{prefix}_count": 0,
            f"{prefix}_min": None,
            f"{prefix}_q05": None,
            f"{prefix}_median": None,
            f"{prefix}_mean": None,
            f"{prefix}_q95": None,
            f"{prefix}_max": None,
            f"{prefix}_std": None,
        }
    return {
        f"{prefix}_count": len(values),
        f"{prefix}_min": min(values),
        f"{prefix}_q05": quantile(values, 0.05),
        f"{prefix}_median": median(values),
        f"{prefix}_mean": mean(values),
        f"{prefix}_q95": quantile(values, 0.95),
        f"{prefix}_max": max(values),
        f"{prefix}_std": pstdev(values),
    }


def boolean_count(poses: list[dict[str, Any]], key: str) -> int:
    return sum(1 for pose in poses if pose.get(key) is True or pose.get("validity_flags", {}).get(key) is True)


def numeric_pose_values(poses: list[dict[str, Any]], key: str) -> list[float]:
    return [float(pose[key]) for pose in poses if isinstance(pose.get(key), int | float)]


def bucket_score_summary(poses: list[dict[str, Any]], bucket: str) -> dict[str, float | int | None]:
    bucket_poses = [pose for pose in poses if pose.get("selection_bucket") == bucket]
    return numeric_summary(numeric_pose_values(bucket_poses, "uff_pose_score"), f"{bucket}_uff_pose_score")


def report_substrate_id(report: dict[str, Any]) -> str:
    substrate_ids = report.get("pose_generation_run", {}).get("substrate_ids", [])
    if len(substrate_ids) == 1:
        return substrate_ids[0]
    return report.get("substrate_record", {}).get("substrate_id")


def has_checked_reaction_center(record: dict[str, Any] | None) -> bool:
    return bool(record and record.get("reaction_center", {}).get("review_status") == "checked")


def build_pose_summary_row(
    report_path: Path,
    report: dict[str, Any],
    records_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    substrate_id = report_substrate_id(report)
    if not substrate_id:
        raise ValueError(f"{report_path}: could not infer substrate_id")
    if substrate_id not in records_by_id:
        raise ValueError(f"{report_path}: substrate_id {substrate_id!r} is absent from Stage 2 records")

    pose_run = report.get("pose_generation_run", {})
    diversity = report.get("diversity_summary", {})
    clash_screen = diversity.get("clash_screen", {})
    pairwise_rmsd = diversity.get("selected_pairwise_heavy_atom_rmsd_angstrom", {})
    minimum_distance_screen = clash_screen.get("minimum_core_substrate_distance_angstrom", {})
    poses = report.get("pose_records", [])
    if not poses:
        raise ValueError(f"{report_path}: pose_records is empty")

    bucket_counts = {
        "low_energy_pose_count": sum(1 for pose in poses if pose.get("selection_bucket") == "low_energy"),
        "high_energy_pose_count": sum(1 for pose in poses if pose.get("selection_bucket") == "high_energy"),
    }
    features: dict[str, Any] = {
        "generated_pool_size": pose_run.get("generated_pool_size", diversity.get("generated_pool_size")),
        "valid_conformer_count": diversity.get("valid_conformer_count"),
        "clash_screened_valid_conformer_count": diversity.get("clash_screened_valid_conformer_count"),
        "clash_screen_passed_count": clash_screen.get("passed_count"),
        "clash_screen_failed_count": clash_screen.get("failed_count"),
        "written_pose_count": pose_run.get("written_pose_count", diversity.get("written_pose_count")),
        "retained_low_energy_count": pose_run.get("retained_low_energy_count"),
        "retained_high_energy_count": pose_run.get("retained_high_energy_count"),
        "selected_pairwise_heavy_atom_rmsd_pair_count": pairwise_rmsd.get("pair_count"),
        "selected_pairwise_heavy_atom_rmsd_min": pairwise_rmsd.get("min"),
        "selected_pairwise_heavy_atom_rmsd_mean": pairwise_rmsd.get("mean"),
        "selected_pairwise_heavy_atom_rmsd_max": pairwise_rmsd.get("max"),
        "pool_uff_score_min": diversity.get("pool_uff_score_min"),
        "pool_uff_score_max": diversity.get("pool_uff_score_max"),
        "clash_screen_minimum_core_substrate_distance_min": minimum_distance_screen.get("min"),
        "clash_screen_minimum_core_substrate_distance_max": minimum_distance_screen.get("max"),
        "connectivity_preserved_count": boolean_count(poses, "connectivity_preserved"),
        "uff_optimisation_converged_count": boolean_count(poses, "uff_optimisation_converged"),
        "severe_clash_screen_passed_count": boolean_count(poses, "severe_clash_screen_passed"),
        "frozen_core_preserved_count": boolean_count(poses, "frozen_core_preserved"),
        "fe_n_distance_within_constraint_count": boolean_count(poses, "fe_n_distance_within_constraint"),
        "catalyst_uff_optimised_count": boolean_count(poses, "catalyst_uff_optimised"),
        "frozen_core_atom_count_min": min(numeric_pose_values(poses, "frozen_core_atom_count")),
        "frozen_core_atom_count_max": max(numeric_pose_values(poses, "frozen_core_atom_count")),
        "assembled_atom_count_min": min(numeric_pose_values(poses, "assembled_atom_count")),
        "assembled_atom_count_max": max(numeric_pose_values(poses, "assembled_atom_count")),
    }
    features.update(bucket_counts)
    features.update(numeric_summary(numeric_pose_values(poses, "uff_pose_score"), "uff_pose_score"))
    features.update(bucket_score_summary(poses, "low_energy"))
    features.update(bucket_score_summary(poses, "high_energy"))
    features.update(numeric_summary(numeric_pose_values(poses, "fe_n_distance_angstrom"), "fe_n_distance_angstrom"))
    features.update(numeric_summary(numeric_pose_values(poses, "core_rmsd_angstrom"), "core_rmsd_angstrom"))
    features.update(
        numeric_summary(
            numeric_pose_values(poses, "minimum_core_substrate_distance_angstrom"),
            "minimum_core_substrate_distance_angstrom",
        )
    )

    record = records_by_id[substrate_id]
    return {
        "schema_version": "stage2-pose-summary-features-v1",
        "substrate_id": substrate_id,
        "reaction_id": record["reaction_id"],
        "curation_status": record["curation_status"],
        "feature_status": "computed_from_stage1_report",
        "feature_blocks": {"pose_summary": features},
        "provenance": {
            "stage1_report_path": display_path(report_path),
            "pose_generation_run_id": pose_run.get("pose_generation_run_id"),
            "constraint_profile_id": pose_run.get("constraint_profile_id"),
            "reference_geometry_id": pose_run.get("reference_geometry_id"),
            "manual_substrates_sha256": pose_run.get("manual_substrates_sha256"),
            "constraint_profile_sha256": pose_run.get("constraint_profile_sha256"),
            "reference_geometry_sha256": pose_run.get("reference_geometry_sha256"),
            "rdkit_version": report.get("toolkit", {}).get("rdkit_version"),
            "python_version": platform.python_version(),
            "stage1_python_version": report.get("toolkit", {}).get("python_version"),
            "clash_screen_method": clash_screen.get("method"),
            "clash_screen_radius_scale": clash_screen.get("radius_scale"),
            "pose_count": len(poses),
        },
    }


def generate_pose_summary(records_path: Path, report_dir: Path) -> list[dict[str, Any]]:
    records_by_id = {record["substrate_id"]: record for record in read_jsonl(records_path)}
    rows = []
    for report_path in sorted(report_dir.glob("stage-1-smoke-*.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        substrate_id = report_substrate_id(report)
        if not has_checked_reaction_center(records_by_id.get(substrate_id)):
            continue
        rows.append(build_pose_summary_row(report_path, report, records_by_id))
    return sorted(rows, key=lambda row: row["substrate_id"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--stage1-report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate_pose_summary(args.records, args.stage1_report_dir)
    write_jsonl(args.output, rows)
    print(f"Wrote Stage 2 pose-summary features for {len(rows)} records to {display_path(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

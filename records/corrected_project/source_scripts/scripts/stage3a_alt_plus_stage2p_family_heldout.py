#!/usr/bin/env python3
"""Compare corrected Stage 2p against Stage 2p plus Stage 3a-alt rules."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_STAGE2P_FEATURES = ROOT / "data/jacs_2025/stage2/features/stage2p-features.jsonl"
DEFAULT_STAGE3A_MATRIX = ROOT / "data/jacs_2025/stage3/model-comparison/stage3a-alt-full-scope-training-matrix.csv"
DEFAULT_STAGE3B_FEATURES = ROOT / "data/jacs_2025/stage3/features/bde.jsonl"
DEFAULT_METRICS = ROOT / "data/jacs_2025/stage3/model-comparison/stage3a-alt-plus-stage2p-family-heldout-p7-modelable-metrics.json"
DEFAULT_PREDICTIONS = ROOT / "data/jacs_2025/stage3/model-comparison/stage3a-alt-plus-stage2p-family-heldout-p7-modelable-predictions.csv"
EXCLUDED_SUBSTRATES = {"1ad", "1z"}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


stage2p = load_module("stage2p_representation_for_stage3a_alt", ROOT / "scripts/stage2p_representation.py")
family_heldout = load_module("stage2p_family_heldout_for_stage3a_alt", ROOT / "scripts/stage2p_family_heldout.py")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage3a_alt_features(path: Path) -> tuple[dict[str, dict[str, float]], list[str]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    names = [name for name in rows[0] if name.startswith("stage3a_alt_hetero_site.")]
    values = {
        row["substrate_id"]: {name: float(row[name]) for name in names}
        for row in rows
    }
    return values, names


def stage3b_features(path: Path) -> tuple[dict[str, dict[str, float]], list[str]]:
    rows = read_jsonl(path)
    values: dict[str, dict[str, float]] = {}
    names: set[str] = set()
    for row in rows:
        block = row.get("feature_blocks", {}).get("stage3b_bde_features", {})
        numeric = {
            f"stage3b_bde.{name}": float(value)
            for name, value in block.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        values[row["substrate_id"]] = numeric
        names.update(numeric)
    return values, sorted(names)


def filter_model_rows(
    rows: list[dict[str, Any]], feature_names: list[str], x: numpy.ndarray, y: numpy.ndarray
) -> tuple[list[dict[str, Any]], list[str], numpy.ndarray, numpy.ndarray]:
    keep = [index for index, row in enumerate(rows) if row["substrate_id"] not in EXCLUDED_SUBSTRATES]
    return ([rows[index] for index in keep], feature_names, x[keep], y[keep])


def run(records_path: Path, stage2p_features_path: Path, stage3a_matrix_path: Path, stage3b_features_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    stage2p_rows = read_jsonl(stage2p_features_path)
    model_rows = stage2p.model_feature_rows(
        records_path,
        stage2p.DEFAULT_POSE_SUMMARY,
        stage2p.DEFAULT_POSE_INTERACTION,
        stage2p.DEFAULT_POSE_FOLDING,
        stage2p_rows,
    )
    stage2p_rows_model = filter_model_rows(*model_rows["stage2p_geometry"])
    base_rows, base_names, base_x, base_y = stage2p_rows_model

    stage3a_by_id, stage3a_names = stage3a_alt_features(stage3a_matrix_path)
    stage3b_by_id, stage3b_names = stage3b_features(stage3b_features_path)
    ids = [row["substrate_id"] for row in base_rows]
    missing = [substrate_id for substrate_id in ids if substrate_id not in stage3a_by_id]
    if missing:
        raise ValueError(f"Missing Stage 3a-alt features for: {', '.join(missing)}")
    missing_bde = [substrate_id for substrate_id in ids if substrate_id not in stage3b_by_id]
    if missing_bde:
        raise ValueError(f"Missing Stage 3b BDE features for: {', '.join(missing_bde)}")
    stage3a_x = numpy.asarray([[stage3a_by_id[substrate_id][name] for name in stage3a_names] for substrate_id in ids], dtype=float)
    stage3b_x = numpy.asarray([[stage3b_by_id[substrate_id].get(name, 0.0) for name in stage3b_names] for substrate_id in ids], dtype=float)
    combined_x = numpy.column_stack([base_x, stage3a_x])
    bde_x = numpy.column_stack([base_x, stage3b_x])
    full_x = numpy.column_stack([base_x, stage3a_x, stage3b_x])

    metadata = family_heldout.family_metadata(records_path)
    family_ids = [metadata[substrate_id]["family_id"] for substrate_id in ids]
    family_labels = {value["family_id"]: value["family_label"] for value in metadata.values()}
    reports: dict[str, Any] = {
        "schema_version": "stage3a-alt-plus-stage2p-family-heldout-v1",
        "target": "ee_percent_magnitude",
        "cohort": {
            "substrate_count": len(ids),
            "family_count": len(set(family_ids)),
            "excluded_substrates": sorted(EXCLUDED_SUBSTRATES),
            "family_labels": family_labels,
        },
        "stage3b_status": "uncalibrated_xtb_features_computed",
        "models": {},
    }
    prediction_rows: list[dict[str, Any]] = []
    for name, names, x in (
        ("stage2p_geometry", base_names, base_x),
        ("stage2p_plus_stage3a_alt", base_names + stage3a_names, combined_x),
        ("stage2p_plus_stage3b", base_names + stage3b_names, bde_x),
        ("stage2p_plus_stage3a_alt_plus_stage3b", base_names + stage3a_names + stage3b_names, full_x),
    ):
        report, predictions = family_heldout.family_heldout_model(
            base_rows, names, x, base_y, family_ids, family_labels
        )
        report["comparison_scope"] = "corrected_p7_modelable_family_heldout"
        reports["models"][name] = report
        for prediction in predictions:
            prediction["feature_set"] = name
            prediction_rows.append(prediction)
    return reports, prediction_rows


def write_predictions(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["feature_set", "substrate_id", "family_id", "family_label", "observed_ee", "prediction", "abs_error"]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--stage2p-features", type=Path, default=DEFAULT_STAGE2P_FEATURES)
    parser.add_argument("--stage3a-matrix", type=Path, default=DEFAULT_STAGE3A_MATRIX)
    parser.add_argument("--stage3b-features", type=Path, default=DEFAULT_STAGE3B_FEATURES)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reports, predictions = run(args.records, args.stage2p_features, args.stage3a_matrix, args.stage3b_features)
    write_json(args.metrics, reports)
    write_predictions(args.predictions, predictions)
    print(f"Wrote combined family-held-out metrics for {reports['cohort']['substrate_count']} substrates")


if __name__ == "__main__":
    raise SystemExit(main())

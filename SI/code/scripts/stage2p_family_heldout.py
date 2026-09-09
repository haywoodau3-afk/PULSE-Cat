#!/usr/bin/env python3
"""Run strict leave-one-family-out validation for Stage 2p model matrices."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import warnings
from pathlib import Path
from typing import Any

import numpy
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
STAGE2P_SCRIPT = ROOT / "scripts/stage2p_representation.py"
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_FEATURES = ROOT / "data/jacs_2025/stage2/features/stage2p-features.jsonl"
DEFAULT_METRICS = ROOT / "data/jacs_2025/stage2/modeling/stage2p-family-heldout-metrics.json"
DEFAULT_PREDICTIONS = ROOT / "data/jacs_2025/stage2/modeling/stage2p-family-heldout-predictions.csv"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


stage2p = load_module("stage2p_representation_for_family_heldout", STAGE2P_SCRIPT)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def family_metadata(records_path: Path) -> dict[str, dict[str, str]]:
    metadata = {}
    for record in read_jsonl(records_path):
        if record.get("outcome", {}).get("ee_percent") is None:
            continue
        if record.get("reaction_center", {}).get("review_status") != "checked":
            continue
        family = record.get("family", {})
        family_id = family.get("family_id")
        if not family_id:
            raise ValueError(f"{record['substrate_id']}: missing family_id")
        metadata[record["substrate_id"]] = {
            "family_id": family_id,
            "family_label": family.get("family_label", family_id),
        }
    return metadata


def elastic_net_grid() -> list[tuple[float, float]]:
    return [(alpha, l1_ratio) for alpha in (0.01, 0.1, 1.0, 10.0, 100.0) for l1_ratio in (0.2, 0.5, 0.8, 1.0)]


def fit_predict(
    train_x: numpy.ndarray,
    train_y: numpy.ndarray,
    test_x: numpy.ndarray,
    alpha: float,
    l1_ratio: float,
) -> numpy.ndarray:
    active = numpy.std(train_x, axis=0) > 0.0
    if not numpy.any(active):
        return numpy.full(len(test_x), float(numpy.mean(train_y)))
    scaler = StandardScaler()
    scaled_train = scaler.fit_transform(train_x[:, active])
    scaled_test = scaler.transform(test_x[:, active])
    model = ElasticNet(
        alpha=alpha,
        l1_ratio=l1_ratio,
        max_iter=5000,
        tol=1e-3,
        random_state=0,
        selection="random",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(scaled_train, train_y)
    return numpy.asarray(model.predict(scaled_test), dtype=float)


def select_inner_params(
    x: numpy.ndarray,
    y: numpy.ndarray,
    families: list[str],
    train_indices: numpy.ndarray,
) -> tuple[float, float, float]:
    train_family_set = sorted(set(families[index] for index in train_indices))
    scores: list[tuple[float, float, float]] = []
    for alpha, l1_ratio in elastic_net_grid():
        predictions = numpy.zeros(len(train_indices), dtype=float)
        for inner_family in train_family_set:
            inner_test_positions = numpy.array(
                [position for position, index in enumerate(train_indices) if families[index] == inner_family],
                dtype=int,
            )
            inner_train_positions = numpy.array(
                [position for position, index in enumerate(train_indices) if families[index] != inner_family],
                dtype=int,
            )
            predictions[inner_test_positions] = fit_predict(
                x[train_indices[inner_train_positions]],
                y[train_indices[inner_train_positions]],
                x[train_indices[inner_test_positions]],
                alpha,
                l1_ratio,
            )
        scores.append((float(mean_absolute_error(y[train_indices], predictions)), alpha, l1_ratio))
    scores.sort(key=lambda item: (item[0], item[1], item[2]))
    return scores[0]


def metrics(y: numpy.ndarray, prediction: numpy.ndarray) -> dict[str, Any]:
    absolute = numpy.abs(y - prediction)
    return {
        "record_count": int(len(y)),
        "mae": float(mean_absolute_error(y, prediction)),
        "rmse": float(mean_squared_error(y, prediction) ** 0.5),
        "r2": float(r2_score(y, prediction)) if len(y) > 1 else None,
        "median_abs_error": float(numpy.median(absolute)),
        "within_10_count": int(numpy.sum(absolute <= 10.0)),
        "within_15_count": int(numpy.sum(absolute <= 15.0)),
        "within_20_count": int(numpy.sum(absolute <= 20.0)),
    }


def family_heldout_model(
    rows: list[dict[str, Any]],
    feature_names: list[str],
    x: numpy.ndarray,
    y: numpy.ndarray,
    family_ids: list[str],
    family_labels: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    predictions = numpy.zeros(len(y), dtype=float)
    fold_records: list[dict[str, Any]] = []
    for family_id in sorted(set(family_ids)):
        test_indices = numpy.array([index for index, value in enumerate(family_ids) if value == family_id], dtype=int)
        train_indices = numpy.array([index for index, value in enumerate(family_ids) if value != family_id], dtype=int)
        inner_mae, alpha, l1_ratio = select_inner_params(x, y, family_ids, train_indices)
        predictions[test_indices] = fit_predict(
            x[train_indices], y[train_indices], x[test_indices], alpha, l1_ratio
        )
        fold_records.append(
            {
                "family_id": family_id,
                "family_label": family_labels[family_id],
                "train_record_count": int(len(train_indices)),
                "test_record_count": int(len(test_indices)),
                "inner_family_heldout_mae": inner_mae,
                "selected_alpha": alpha,
                "selected_l1_ratio": l1_ratio,
            }
        )

    family_metrics = {}
    for family_id in sorted(set(family_ids)):
        indices = numpy.array([index for index, value in enumerate(family_ids) if value == family_id], dtype=int)
        family_metric = metrics(y[indices], predictions[indices])
        family_metric["family_label"] = family_labels[family_id]
        family_metric["mean_signed_error"] = float(numpy.mean(predictions[indices] - y[indices]))
        family_metric["max_abs_error"] = float(numpy.max(numpy.abs(predictions[indices] - y[indices])))
        family_metrics[family_id] = family_metric

    pooled = metrics(y, predictions)
    pooled["macro_family_mae"] = float(numpy.mean([value["mae"] for value in family_metrics.values()]))
    report = {
        "feature_count": len(feature_names),
        "protocol": "outer_leave_one_family_out_with_inner_leave_one_family_out_hyperparameter_selection",
        "pooled_metrics": pooled,
        "family_metrics": family_metrics,
        "folds": fold_records,
        "selected_alpha_counts": {
            str(alpha): sum(1 for fold in fold_records if fold["selected_alpha"] == alpha)
            for alpha in sorted({fold["selected_alpha"] for fold in fold_records})
        },
        "selected_l1_ratio_counts": {
            str(ratio): sum(1 for fold in fold_records if fold["selected_l1_ratio"] == ratio)
            for ratio in sorted({fold["selected_l1_ratio"] for fold in fold_records})
        },
    }
    prediction_rows = []
    for index, row in enumerate(rows):
        prediction_rows.append(
            {
                "feature_set": "",
                "substrate_id": row["substrate_id"],
                "family_id": family_ids[index],
                "family_label": family_labels[family_ids[index]],
                "observed_ee": float(y[index]),
                "prediction": float(predictions[index]),
                "abs_error": float(abs(predictions[index] - y[index])),
            }
        )
    return report, prediction_rows


def run(records_path: Path, features_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = family_metadata(records_path)
    stage2p_rows = read_jsonl(features_path)
    model_rows = stage2p.model_feature_rows(records_path, stage2p.DEFAULT_POSE_SUMMARY, stage2p.DEFAULT_POSE_INTERACTION, stage2p.DEFAULT_POSE_FOLDING, stage2p_rows)
    ordered_ids = [row["substrate_id"] for row in model_rows["stage2_alt"][0]]
    missing = sorted(set(ordered_ids) - set(records))
    if missing:
        raise ValueError(f"Missing family metadata for: {', '.join(missing)}")
    family_ids = [records[substrate_id]["family_id"] for substrate_id in ordered_ids]
    family_labels = {value["family_id"]: value["family_label"] for value in records.values()}
    reports = {
        "schema_version": "stage2p-family-heldout-model-comparison-v1",
        "target": "ee_percent_magnitude",
        "cohort": {
            "substrate_count": len(ordered_ids),
            "family_count": len(set(family_ids)),
            "family_sizes": {family_id: family_ids.count(family_id) for family_id in sorted(set(family_ids))},
            "family_labels": family_labels,
        },
        "models": {},
    }
    prediction_rows: list[dict[str, Any]] = []
    for model_name, (rows, feature_names, x, y) in model_rows.items():
        report, model_predictions = family_heldout_model(rows, feature_names, x, y, family_ids, family_labels)
        report["comparison_scope"] = "primary_four_way" if model_name in {
            "stage2_pose_summary", "stage2_alt", "stage2p_geometry", "stage2_alt_stage2p"
        } else "rigorous_ablation_only"
        reports["models"][model_name] = report
        for prediction in model_predictions:
            prediction["feature_set"] = model_name
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
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reports, predictions = run(args.records, args.features)
    write_json(args.metrics, reports)
    write_predictions(args.predictions, predictions)
    print(f"Wrote family-held-out metrics for {reports['cohort']['substrate_count']} substrates across {reports['cohort']['family_count']} families")
    print(f"Wrote predictions to {args.predictions}")


if __name__ == "__main__":
    raise SystemExit(main())

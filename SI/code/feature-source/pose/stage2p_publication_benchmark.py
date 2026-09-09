#!/usr/bin/env python3
"""Publication-readiness benchmark for the fixed-catalyst Stage 2p model.

This module deliberately keeps the legacy Stage 2 benchmark intact.  It provides
the stricter seam used for the publication baseline:

* only checked ee labels from the fixed ``fe-p7-cl`` catalyst domain;
* family-held-out outer evaluation with inner grouped model selection;
* train-only feature masking and applicability calibration;
* split-conformal uncertainty intervals;
* required median and nearest-neighbour baselines;
* an ee/yield actionability report with explicit readiness blockers.

The target remains ee magnitude until absolute product configurations have been
manually curated.  This script must not be used to claim signed stereochemical
prediction or cross-catalyst transfer.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import platform
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Reuse the established Stage 2p feature generator at the public boundary.  The
# publication benchmark owns cohort selection and validation, so the legacy
# target-holdout implementation cannot silently determine its evidence.
from stage2_full_scope_benchmark import (  # noqa: E402
    add_pose_aware_features,
    featurize_record,
    read_jsonl,
)


DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_POSE_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"
DEFAULT_POSE_INTERACTION = ROOT / "data/jacs_2025/stage2/features/pose-interaction.jsonl"
DEFAULT_MATRIX = ROOT / "data/jacs_2025/stage2/features/stage2p-publication-matrix.csv"
DEFAULT_REPORT = ROOT / "data/jacs_2025/stage2/reports/stage2p-publication-benchmark.json"
DEFAULT_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/stage2p-publication-predictions.csv"
DEFAULT_YIELD_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/stage2p-publication-yield-predictions.csv"
DEFAULT_SPLITS = ROOT / "data/jacs_2025/stage2/reports/stage2p-publication-splits.json"
DEFAULT_READINESS_REPORT = ROOT / "data/jacs_2025/stage2/reports/stage2p-publication-readiness.md"

FIXED_CATALYST_ID = "fe-p7-cl"
UNRESOLVED_EE_IDS = {"1ad"}
NOT_APPLICABLE_EE_IDS = {"1an"}
EE_STATUSES = {"reported", "zero_curated"}
EE_THRESHOLD = 80.0
YIELD_THRESHOLD = 50.0
CONFORMAL_ALPHAS = {"80": 0.20, "95": 0.05}


def select_publication_records(
    records: list[dict[str, Any]],
    catalyst_id: str = FIXED_CATALYST_ID,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Return the checked, fixed-catalyst ee cohort and auditable exclusions."""

    selected: list[dict[str, Any]] = []
    exclusions: list[dict[str, str]] = []
    for record in sorted(records, key=lambda item: item["substrate_id"]):
        substrate_id = record["substrate_id"]
        outcome = record.get("outcome", {})
        if record.get("catalyst_id") != catalyst_id:
            exclusions.append({"substrate_id": substrate_id, "reason": "out_of_domain_catalyst"})
            continue
        if substrate_id in NOT_APPLICABLE_EE_IDS or outcome.get("ee_status") == "not_applicable_achiral":
            exclusions.append({"substrate_id": substrate_id, "reason": "not_applicable_ee"})
            continue
        if substrate_id in UNRESOLVED_EE_IDS:
            exclusions.append({"substrate_id": substrate_id, "reason": "unresolved_ee_label"})
            continue
        ee = outcome.get("ee_percent")
        if outcome.get("ee_status") not in EE_STATUSES or not is_number(ee):
            exclusions.append({"substrate_id": substrate_id, "reason": "unresolved_ee_label"})
            continue
        if not record.get("condition", {}).get("fixed_jacs_conditions", False):
            exclusions.append({"substrate_id": substrate_id, "reason": "out_of_domain_conditions"})
            continue
        selected.append(record)
    return selected, exclusions


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def build_feature_rows(
    records: list[dict[str, Any]],
    pose_summary_path: Path = DEFAULT_POSE_SUMMARY,
    pose_interaction_path: Path = DEFAULT_POSE_INTERACTION,
    target: str = "ee",
) -> tuple[list[dict[str, Any]], list[str]]:
    """Build Stage 2p rows and encode the observed publication conditions."""

    pose_summary_by_id = {row["substrate_id"]: row for row in read_jsonl(pose_summary_path)}
    pose_interaction_by_id = _aggregate_pose_interactions(read_jsonl(pose_interaction_path))
    rows: list[dict[str, Any]] = []
    for record in records:
        features, fingerprint = featurize_record(record)
        add_pose_aware_features(features, record, pose_summary_by_id, pose_interaction_by_id)
        condition = record.get("condition", {})
        temperature = condition.get("temperature_c")
        if is_number(temperature):
            features["condition.temperature_c"] = float(temperature)
        condition_set = condition.get("condition_set_id")
        if condition_set is not None:
            features[f"condition.condition_set_id={condition_set}"] = 1.0
        target_value = record["outcome"].get("ee_percent" if target == "ee" else "isolated_yield_percent")
        if not is_number(target_value):
            raise ValueError(f"{record['substrate_id']}: missing numeric {target} label")
        rows.append(
            {
                "substrate_id": record["substrate_id"],
                "reaction_id": record.get("reaction_id"),
                "family_id": record.get("family", {}).get("family_id", record["substrate_id"]),
                "catalyst_id": record.get("catalyst_id"),
                "temperature_c": temperature,
                "condition_set_id": condition_set,
                "target_name": "ee_percent_magnitude" if target == "ee" else "isolated_yield_percent",
                "target_value": float(target_value),
                "ee_percent": record["outcome"].get("ee_percent"),
                "yield_percent": record["outcome"].get("isolated_yield_percent"),
                "ee_status": record["outcome"].get("ee_status"),
                "azide_smiles": record["structure"]["azide_smiles"],
                "features": features,
                "fingerprint": fingerprint,
            }
        )
    feature_names = sorted({name for row in rows for name in row["features"]})
    return rows, feature_names


def _aggregate_pose_interactions(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Aggregate per-pose interaction features without importing legacy internals."""

    values_by_substrate: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        substrate_id = row["substrate_id"]
        values_by_substrate.setdefault(substrate_id, {})
        for key, value in row["feature_blocks"]["pose_interaction"].items():
            if is_number(value):
                values_by_substrate[substrate_id].setdefault(key, []).append(float(value))
    aggregated: dict[str, dict[str, float]] = {}
    for substrate_id, feature_values in values_by_substrate.items():
        output: dict[str, float] = {}
        for key, values in feature_values.items():
            array = numpy.asarray(values, dtype=float)
            for name, value in {
                "count": len(values),
                "min": array.min(),
                "median": numpy.median(array),
                "mean": array.mean(),
                "max": array.max(),
                "std": array.std(),
            }.items():
                output[f"{key}.{name}"] = float(value)
        aggregated[substrate_id] = output
    return aggregated


def write_matrix(path: Path, rows: list[dict[str, Any]], feature_names: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "substrate_id",
        "reaction_id",
        "family_id",
        "catalyst_id",
        "temperature_c",
        "condition_set_id",
        "target_name",
        "target_value",
        "ee_percent",
        "yield_percent",
        "ee_status",
        "azide_smiles",
    ] + feature_names
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            output = {column: row.get(column, "") for column in columns[:12]}
            output.update({name: row["features"].get(name, 0.0) for name in feature_names})
            writer.writerow(output)


def build_outer_group_splits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build deterministic leave-one-family-out outer folds."""

    groups = sorted({row["family_id"] for row in rows})
    splits = []
    for heldout_group in groups:
        test_indices = [index for index, row in enumerate(rows) if row["family_id"] == heldout_group]
        train_indices = [index for index, row in enumerate(rows) if row["family_id"] != heldout_group]
        if not train_indices:
            continue
        splits.append(
            {
                "split_id": f"family:{heldout_group}",
                "heldout_family_id": heldout_group,
                "train_indices": train_indices,
                "test_indices": test_indices,
                "train_substrate_ids": [rows[index]["substrate_id"] for index in train_indices],
                "test_substrate_ids": [rows[index]["substrate_id"] for index in test_indices],
            }
        )
    return splits


def build_inner_group_splits(rows: list[dict[str, Any]], indices: list[int]) -> list[dict[str, Any]]:
    groups = sorted({rows[index]["family_id"] for index in indices})
    splits = []
    for heldout_group in groups:
        validation = [index for index in indices if rows[index]["family_id"] == heldout_group]
        train = [index for index in indices if rows[index]["family_id"] != heldout_group]
        if train and validation:
            splits.append({"train_indices": train, "validation_indices": validation, "heldout_family_id": heldout_group})
    return splits


def feature_matrix(rows: list[dict[str, Any]], feature_names: list[str]) -> numpy.ndarray:
    return numpy.asarray(
        [[row["features"].get(name, 0.0) for name in feature_names] for row in rows],
        dtype=float,
    )


def _fit_predict_estimator(
    estimator: Any,
    x_train: numpy.ndarray,
    y_train: numpy.ndarray,
    x_pred: numpy.ndarray,
) -> numpy.ndarray:
    """Fit after selecting constant columns using training data only."""

    active = numpy.std(x_train, axis=0) > 0.0
    if not numpy.any(active):
        return numpy.full(len(x_pred), float(numpy.median(y_train)))
    model = clone(estimator)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(x_train[:, active], y_train)
    return numpy.asarray(model.predict(x_pred[:, active]), dtype=float)


def estimator_grid() -> dict[str, list[Any]]:
    return {
        "elastic_net": [
            make_pipeline(StandardScaler(), ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=20000, random_state=0))
            for alpha in [0.1, 1.0, 10.0]
            for l1_ratio in [0.5, 0.8]
        ],
        "ridge_regression": [
            make_pipeline(StandardScaler(), Ridge(alpha=alpha))
            for alpha in [1.0, 10.0, 100.0]
        ],
    }


def _predict_baseline(
    model_name: str,
    rows: list[dict[str, Any]],
    train_indices: list[int],
    pred_indices: list[int],
    y: numpy.ndarray,
) -> numpy.ndarray:
    train_y = y[train_indices]
    if model_name == "median_baseline":
        return numpy.full(len(pred_indices), float(numpy.median(train_y)))
    if model_name != "nearest_neighbour":
        raise ValueError(f"Unknown baseline model: {model_name}")
    predictions = []
    for pred_index in pred_indices:
        similarities = [
            fingerprint_similarity(rows[pred_index]["fingerprint"], rows[train_index]["fingerprint"])
            for train_index in train_indices
        ]
        predictions.append(float(train_y[int(numpy.argmax(similarities))]))
    return numpy.asarray(predictions, dtype=float)


def fingerprint_similarity(left: list[int], right: list[int]) -> float:
    left_array = numpy.asarray(left, dtype=bool)
    right_array = numpy.asarray(right, dtype=bool)
    union = numpy.logical_or(left_array, right_array).sum()
    return float(numpy.logical_and(left_array, right_array).sum() / union) if union else 0.0


def nearest_train_similarity(rows: list[dict[str, Any]], train_indices: list[int], pred_index: int) -> float:
    if not train_indices:
        return 0.0
    return max(
        fingerprint_similarity(rows[pred_index]["fingerprint"], rows[train_index]["fingerprint"])
        for train_index in train_indices
    )


def applicability_threshold(rows: list[dict[str, Any]], train_indices: list[int], coverage: float = 0.90) -> float:
    """Calibrate a similarity threshold from train-only leave-one-out neighbors."""

    if len(train_indices) < 3:
        return 0.0
    loo_scores = []
    for index in train_indices:
        others = [candidate for candidate in train_indices if candidate != index]
        loo_scores.append(max(nearest_train_similarity(rows, others, index), 0.0))
    # A 90% in-domain calibration keeps the lower 10% of observed train
    # neighborhoods as an explicit extrapolation boundary.
    return float(numpy.quantile(numpy.asarray(loo_scores), 1.0 - coverage, method="higher"))


def applicability_decision(nearest_similarity_score: float, threshold: float) -> str:
    return "in_domain" if nearest_similarity_score >= threshold else "abstain_ood"


def split_conformal_interval(
    prediction: float,
    calibration_residuals: numpy.ndarray,
    alpha: float,
) -> dict[str, float | str | int]:
    """Return a finite-sample split-conformal symmetric interval.

    Residuals are defined as ``observed - predicted`` by convention, but the
    absolute-residual order statistic makes the interval robust to sign errors
    and gives the intended finite-sample calibration behavior.
    """

    residuals = numpy.asarray(calibration_residuals, dtype=float)
    if residuals.size == 0:
        radius = 100.0
    else:
        rank = int(math.ceil((residuals.size + 1) * (1.0 - alpha)))
        radius = float(numpy.sort(numpy.abs(residuals))[min(rank - 1, residuals.size - 1)])
    return {
        "low": max(0.0, float(prediction) - radius),
        "high": min(100.0, float(prediction) + radius),
        "radius": radius,
        "calibration_count": int(residuals.size),
        "method": "split_conformal_absolute_residual",
    }


def _estimator_label(estimator: Any) -> str:
    final = estimator.steps[-1][1] if hasattr(estimator, "steps") else estimator
    params = final.get_params()
    return json.dumps(
        {key: params[key] for key in ("alpha", "l1_ratio") if key in params},
        sort_keys=True,
    )


def _candidate_evaluation(
    model_name: str,
    candidate: Any,
    rows: list[dict[str, Any]],
    x: numpy.ndarray,
    y: numpy.ndarray,
    outer_train: list[int],
) -> tuple[float, numpy.ndarray]:
    inner_splits = build_inner_group_splits(rows, outer_train)
    predictions: list[float] = []
    observed: list[float] = []
    for split in inner_splits:
        train = split["train_indices"]
        validation = split["validation_indices"]
        if model_name in {"median_baseline", "nearest_neighbour"}:
            pred = _predict_baseline(model_name, rows, train, validation, y)
        else:
            pred = _fit_predict_estimator(candidate, x[train], y[train], x[validation])
        predictions.extend(pred.tolist())
        observed.extend(y[validation].tolist())
    if not observed:
        if model_name in {"median_baseline", "nearest_neighbour"}:
            pred = _predict_baseline(model_name, rows, outer_train, outer_train, y)
        else:
            pred = _fit_predict_estimator(candidate, x[outer_train], y[outer_train], x[outer_train])
        return float(mean_absolute_error(y[outer_train], pred)), numpy.asarray(y[outer_train] - pred, dtype=float)
    residuals = numpy.asarray(observed, dtype=float) - numpy.asarray(predictions, dtype=float)
    return float(numpy.mean(numpy.abs(residuals))), residuals


def _select_model(
    model_name: str,
    candidates: list[Any],
    rows: list[dict[str, Any]],
    x: numpy.ndarray,
    y: numpy.ndarray,
    outer_train: list[int],
) -> tuple[Any | None, numpy.ndarray, float]:
    if model_name in {"median_baseline", "nearest_neighbour"}:
        score, residuals = _candidate_evaluation(model_name, None, rows, x, y, outer_train)
        return None, residuals, score
    best: tuple[Any, numpy.ndarray, float] | None = None
    for candidate in candidates:
        score, residuals = _candidate_evaluation(model_name, candidate, rows, x, y, outer_train)
        if best is None or score < best[2] - 1e-12:
            best = (candidate, residuals, score)
    assert best is not None
    return best


def _model_prediction(
    model_name: str,
    estimator: Any | None,
    rows: list[dict[str, Any]],
    x: numpy.ndarray,
    y: numpy.ndarray,
    train_indices: list[int],
    test_indices: list[int],
) -> numpy.ndarray:
    if model_name in {"median_baseline", "nearest_neighbour"}:
        return _predict_baseline(model_name, rows, train_indices, test_indices, y)
    return _fit_predict_estimator(estimator, x[train_indices], y[train_indices], x[test_indices])


def run_nested_group_benchmark(
    rows: list[dict[str, Any]],
    feature_names: list[str],
    target_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run outer family holdout with inner family-held-out selection."""

    x = feature_matrix(rows, feature_names)
    y = numpy.asarray([row["target_value"] for row in rows], dtype=float)
    candidates = estimator_grid()
    model_names = ["elastic_net", "ridge_regression", "median_baseline", "nearest_neighbour"]
    predictions: list[dict[str, Any]] = []
    splits = build_outer_group_splits(rows)
    for split in splits:
        train = split["train_indices"]
        test = split["test_indices"]
        domain_threshold = applicability_threshold(rows, train)
        for model_name in model_names:
            estimator, calibration_residuals, inner_mae = _select_model(
                model_name,
                candidates.get(model_name, []),
                rows,
                x,
                y,
                train,
            )
            raw_predictions = _model_prediction(model_name, estimator, rows, x, y, train, test)
            for position, test_index in enumerate(test):
                prediction = float(numpy.clip(raw_predictions[position], 0.0, 100.0))
                interval_rows: dict[str, Any] = {}
                for level, alpha in CONFORMAL_ALPHAS.items():
                    interval = split_conformal_interval(prediction, calibration_residuals, alpha)
                    interval_rows[f"prediction_interval_{level}_low"] = interval["low"]
                    interval_rows[f"prediction_interval_{level}_high"] = interval["high"]
                    interval_rows[f"prediction_interval_{level}_radius"] = interval["radius"]
                similarity = nearest_train_similarity(rows, train, test_index)
                applicability = applicability_decision(similarity, domain_threshold)
                predictions.append(
                    {
                        "split_id": split["split_id"],
                        "heldout_family_id": split["heldout_family_id"],
                        "target_name": target_name,
                        "target_substrate_id": rows[test_index]["substrate_id"],
                        "family_id": rows[test_index]["family_id"],
                        "model_name": model_name,
                        "observed_target_value": float(y[test_index]),
                        "prediction": prediction,
                        "residual": float(y[test_index] - prediction),
                        "abs_error": abs(float(y[test_index] - prediction)),
                        "inner_validation_mae": inner_mae,
                        "selected_estimator_params": _estimator_label(estimator) if estimator is not None else "{}",
                        "train_count": len(train),
                        "calibration_count": len(calibration_residuals),
                        "nearest_train_tanimoto": similarity,
                        "applicability_threshold": domain_threshold,
                        "applicability": applicability,
                        **interval_rows,
                    }
                )
    return predictions, splits


def metric_summary(values: numpy.ndarray) -> dict[str, float]:
    return {
        "mean": float(values.mean()),
        "median": float(numpy.median(values)),
        "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
        "q05": float(numpy.quantile(values, 0.05)),
        "q95": float(numpy.quantile(values, 0.95)),
    }


def threshold_metrics(y_true: numpy.ndarray, y_pred: numpy.ndarray, threshold: float) -> dict[str, float | int]:
    actual = numpy.asarray(y_true) >= threshold
    predicted = numpy.asarray(y_pred) >= threshold
    tp = int(numpy.logical_and(actual, predicted).sum())
    fp = int(numpy.logical_and(~actual, predicted).sum())
    tn = int(numpy.logical_and(~actual, ~predicted).sum())
    fn = int(numpy.logical_and(actual, ~predicted).sum())

    def ratio(numerator: int, denominator: int) -> float:
        return float(numerator / denominator) if denominator else 0.0

    return {
        "threshold": threshold,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "specificity": ratio(tn, tn + fp),
        "false_positive_rate": ratio(fp, fp + tn),
        "accuracy": ratio(tp + tn, len(actual)),
    }


def model_metrics(predictions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_model: dict[str, list[dict[str, Any]]] = {}
    for row in predictions:
        by_model.setdefault(row["model_name"], []).append(row)
    metrics: dict[str, dict[str, Any]] = {}
    for model_name, rows in sorted(by_model.items()):
        y_true = numpy.asarray([row["observed_target_value"] for row in rows], dtype=float)
        y_pred = numpy.asarray([row["prediction"] for row in rows], dtype=float)
        residuals = y_pred - y_true
        is_ee_target = rows[0]["target_name"] == "ee_percent_magnitude"
        target_metrics_key = "ee_threshold_metrics" if is_ee_target else "yield_threshold_metrics"
        target_metrics_threshold = EE_THRESHOLD if is_ee_target else YIELD_THRESHOLD
        metrics[model_name] = {
            "target_count": len(rows),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
            "r2": float(r2_score(y_true, y_pred)) if len(rows) > 1 else 0.0,
            "mean_error": float(residuals.mean()),
            "residual_summary": metric_summary(residuals),
            "abs_error_summary": metric_summary(numpy.abs(residuals)),
            "within_10_count": int(numpy.sum(numpy.abs(residuals) <= 10.0)),
            "within_10_fraction": float(numpy.mean(numpy.abs(residuals) <= 10.0)),
            "within_15_count": int(numpy.sum(numpy.abs(residuals) <= 15.0)),
            "within_15_fraction": float(numpy.mean(numpy.abs(residuals) <= 15.0)),
            "within_20_count": int(numpy.sum(numpy.abs(residuals) <= 20.0)),
            "within_20_fraction": float(numpy.mean(numpy.abs(residuals) <= 20.0)),
            target_metrics_key: threshold_metrics(y_true, y_pred, target_metrics_threshold),
            "interval_80_coverage": float(
                numpy.mean(
                    [
                        row["prediction_interval_80_low"] <= row["observed_target_value"] <= row["prediction_interval_80_high"]
                        for row in rows
                    ]
                )
            ),
            "interval_95_coverage": float(
                numpy.mean(
                    [
                        row["prediction_interval_95_low"] <= row["observed_target_value"] <= row["prediction_interval_95_high"]
                        for row in rows
                    ]
                )
            ),
            "abstention_count": sum(row["applicability"] == "abstain_ood" for row in rows),
            "in_domain_count": sum(row["applicability"] == "in_domain" for row in rows),
        }
    return metrics


def write_predictions(path: Path, predictions: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in predictions for key in row})
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(predictions)


def _join_actionability(
    ee_predictions: list[dict[str, Any]],
    yield_predictions: list[dict[str, Any]],
    model_name: str = "elastic_net",
) -> dict[str, Any]:
    ee = {
        (row["split_id"], row["target_substrate_id"]): row
        for row in ee_predictions
        if row["model_name"] == model_name
    }
    yields = {
        (row["split_id"], row["target_substrate_id"]): row
        for row in yield_predictions
        if row["model_name"] == model_name
    }
    joined = []
    for key in sorted(ee.keys() & yields.keys()):
        ee_row = ee[key]
        yield_row = yields[key]
        observed = ee_row["observed_target_value"] >= EE_THRESHOLD and yield_row["observed_target_value"] >= YIELD_THRESHOLD
        point_predicted = ee_row["prediction"] >= EE_THRESHOLD and yield_row["prediction"] >= YIELD_THRESHOLD
        conservative = (
            ee_row["prediction_interval_80_low"] >= EE_THRESHOLD
            and yield_row["prediction_interval_80_low"] >= YIELD_THRESHOLD
            and ee_row["applicability"] == "in_domain"
            and yield_row["applicability"] == "in_domain"
        )
        joined.append(
            {
                "split_id": key[0],
                "target_substrate_id": key[1],
                "observed_actionable": bool(observed),
                "point_predicted_actionable": bool(point_predicted),
                "conservative_advance": bool(conservative),
                "ee_prediction": ee_row["prediction"],
                "yield_prediction": yield_row["prediction"],
            }
        )
    actual = numpy.asarray([row["observed_actionable"] for row in joined], dtype=bool)
    predicted = numpy.asarray([row["point_predicted_actionable"] for row in joined], dtype=bool)
    return {
        "model_name": model_name,
        "record_count": len(joined),
        "joined_predictions": joined,
        "point_actionable_count": int(predicted.sum()) if len(predicted) else 0,
        "observed_actionable_count": int(actual.sum()) if len(actual) else 0,
        "conservative_advance_count": sum(row["conservative_advance"] for row in joined),
        "point_threshold_metrics": threshold_metrics(actual.astype(float), predicted.astype(float), 0.5)
        if len(actual)
        else {},
    }


def publication_readiness(
    records: list[dict[str, Any]],
    exclusions: list[dict[str, str]],
    ee_metrics: dict[str, dict[str, Any]],
    yield_metrics: dict[str, dict[str, Any]],
    actionability: dict[str, Any],
) -> dict[str, Any]:
    selected_catalysts = {record.get("catalyst_id") for record in records}
    signed_available = any(is_number(record.get("outcome", {}).get("signed_ee_percent")) for record in records)
    # A low isolated yield is still a productive reaction and cannot be used as
    # a nonproductive feasibility label.  Require an explicit curated outcome.
    has_negative_feasibility = any(record.get("outcome", {}).get("feasibility") is False for record in records)
    incumbent = ee_metrics.get("elastic_net", {})
    yield_incumbent = yield_metrics.get("elastic_net", {})
    blockers = []
    gates = {
        "fixed_catalyst_domain_clean": selected_catalysts == {FIXED_CATALYST_ID},
        "out_of_domain_records_excluded": any(item["reason"] == "out_of_domain_catalyst" for item in exclusions),
        "nested_family_holdout": True,
        "signed_ee_curated": signed_available,
        "genuine_feasibility_negatives": has_negative_feasibility,
        "yield_model_available": bool(yield_incumbent),
        "prospective_panel_locked": False,
        "catalyst_bridge_matrix": False,
    }
    if not gates["signed_ee_curated"]:
        blockers.append("absolute product configurations are not curated; target remains ee magnitude")
    if not gates["genuine_feasibility_negatives"]:
        blockers.append("the literature cohort lacks genuine tested-substrate feasibility negatives")
    blockers.extend(["no locked prospective panel is present", "no connected cross-catalyst bridge matrix is present"])
    performance = {
        "ee_within_10_fraction": incumbent.get("within_10_fraction"),
        "ee_within_15_fraction": incumbent.get("within_15_fraction"),
        "ee_threshold_precision": incumbent.get("ee_threshold_metrics", {}).get("precision"),
        "yield_within_10_fraction": yield_incumbent.get("within_10_fraction"),
        "actionable_point_prediction": actionability.get("point_actionable_count", 0),
    }
    return {
        "status": "not_ready" if blockers else "ready_for_defined_fixed_catalyst_claim",
        "gates": gates,
        "performance": performance,
        "blockers": blockers,
        "interpretation": (
            "Publication-grade benchmark infrastructure is present, but the chemistry claim remains bounded until the listed data and prospective validation gates pass."
            if blockers
            else "All configured publication gates passed for the defined fixed-catalyst claim."
        ),
    }


def run_publication_benchmark(
    records_path: Path = DEFAULT_RECORDS,
    pose_summary_path: Path = DEFAULT_POSE_SUMMARY,
    pose_interaction_path: Path = DEFAULT_POSE_INTERACTION,
    matrix_path: Path = DEFAULT_MATRIX,
    report_path: Path = DEFAULT_REPORT,
    predictions_path: Path = DEFAULT_PREDICTIONS,
    yield_predictions_path: Path = DEFAULT_YIELD_PREDICTIONS,
    splits_path: Path = DEFAULT_SPLITS,
    readiness_report_path: Path = DEFAULT_READINESS_REPORT,
) -> dict[str, Any]:
    all_records = read_jsonl(records_path)
    selected_records, exclusions = select_publication_records(all_records)
    ee_rows, feature_names = build_feature_rows(selected_records, pose_summary_path, pose_interaction_path, "ee")
    yield_rows, yield_feature_names = build_feature_rows(selected_records, pose_summary_path, pose_interaction_path, "yield")
    if feature_names != yield_feature_names:
        raise ValueError("ee and yield feature schemas differ")
    write_matrix(matrix_path, ee_rows, feature_names)
    ee_predictions, splits = run_nested_group_benchmark(ee_rows, feature_names, "ee_percent_magnitude")
    yield_predictions, yield_splits = run_nested_group_benchmark(yield_rows, feature_names, "isolated_yield_percent")
    if splits != yield_splits:
        raise ValueError("ee and yield split manifests differ")
    write_predictions(predictions_path, ee_predictions)
    write_predictions(yield_predictions_path, yield_predictions)
    splits_path.parent.mkdir(parents=True, exist_ok=True)
    splits_path.write_text(json.dumps({"schema_version": "stage2p-publication-splits-v1", "splits": splits}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ee_model_metrics = model_metrics(ee_predictions)
    yield_model_metrics = model_metrics(yield_predictions)
    actionability = _join_actionability(ee_predictions, yield_predictions)
    readiness = publication_readiness(selected_records, exclusions, ee_model_metrics, yield_model_metrics, actionability)
    report = {
        "schema_version": "stage2p-publication-benchmark-v1",
        "status": "publication_readiness_assessment",
        "domain": {
            "catalyst_id": FIXED_CATALYST_ID,
            "condition_policy": "published JACS conditions encoded as temperature and condition-set features",
            "cross_catalyst_transfer": False,
        },
        "target": {
            "primary": "ee_percent_magnitude",
            "signed_ee_status": "pending_manual_configuration_curation",
        },
        "modelable_record_count": len(ee_rows),
        "excluded_records": exclusions,
        "feature_set": "stage2p_pose_aware_plus_condition_features",
        "feature_count": len(feature_names),
        "split_mode": "nested_family_holdout",
        "outer_split_count": len(splits),
        "inner_selection": "leave-one-family-out within each outer training partition",
        "models": ee_model_metrics,
        "yield_models": yield_model_metrics,
        "locked_incumbent": "elastic_net",
        "required_baselines": ["median_baseline", "nearest_neighbour", "ridge_regression"],
        "actionability": actionability,
        "readiness": readiness,
        "provenance": {
            "records_path": str(records_path.relative_to(ROOT) if records_path.is_relative_to(ROOT) else records_path),
            "pose_summary_path": str(pose_summary_path.relative_to(ROOT) if pose_summary_path.is_relative_to(ROOT) else pose_summary_path),
            "pose_interaction_path": str(pose_interaction_path.relative_to(ROOT) if pose_interaction_path.is_relative_to(ROOT) else pose_interaction_path),
            "python_version": platform.python_version(),
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readiness_report(readiness_report_path, report)
    return report


def write_readiness_report(path: Path, report: dict[str, Any]) -> None:
    readiness = report["readiness"]
    incumbent = report["models"][report["locked_incumbent"]]
    lines = [
        "# Stage 2p Publication Readiness",
        "",
        f"Status: **{readiness['status']}**",
        "",
        "This report evaluates the fixed-catalyst `[Fe(P7)Cl]` Stage 2p substrate model. It does not claim cross-catalyst transfer or signed stereochemical prediction.",
        "",
        "## Locked scientific scope",
        "",
        "- Primary target: unsigned ee magnitude until product configurations are manually curated.",
        "- Catalyst: fixed `fe-p7-cl`; out-of-domain catalysts are excluded before feature generation.",
        "- Validation: nested leave-one-family-out evaluation with train-only feature masking and applicability calibration.",
        "- Incumbent: Elastic Net; Ridge, median, and chemical nearest-neighbour models are required challengers.",
        "- Conditions: published temperature and condition-set identity are encoded explicitly.",
        "",
        "## Incumbent performance",
        "",
        f"- MAE: {incumbent['mae']:.3f} ee",
        f"- RMSE: {incumbent['rmse']:.3f} ee",
        f"- Within ±10 ee: {incumbent['within_10_count']}/{incumbent['target_count']}",
        f"- Within ±15 ee: {incumbent['within_15_count']}/{incumbent['target_count']}",
        f"- Within ±20 ee: {incumbent['within_20_count']}/{incumbent['target_count']}",
        f"- Precision at ≥80 ee: {incumbent['ee_threshold_metrics']['precision']:.3f}",
        f"- 80% interval coverage: {incumbent['interval_80_coverage']:.3f}",
        f"- 95% interval coverage: {incumbent['interval_95_coverage']:.3f}",
        "",
        "## Readiness gates",
        "",
    ]
    for name, passed in readiness["gates"].items():
        lines.append(f"- [{'x' if passed else ' '}] {name}")
    lines.extend(["", "## Blocking items", ""])
    lines.extend(f"- {blocker}" for blocker in readiness["blockers"])
    lines.extend(
        [
            "",
            "## Decision rule for future candidates",
            "",
            "Advance only when the lower 80% interval clears both 80 ee and 50% yield and the applicability decision is `in_domain`. Cases whose interval crosses a threshold are uncertain; out-of-domain cases must abstain.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--pose-summary", type=Path, default=DEFAULT_POSE_SUMMARY)
    parser.add_argument("--pose-interaction", type=Path, default=DEFAULT_POSE_INTERACTION)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--yield-predictions", type=Path, default=DEFAULT_YIELD_PREDICTIONS)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--readiness-report", type=Path, default=DEFAULT_READINESS_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_publication_benchmark(
        records_path=args.records,
        pose_summary_path=args.pose_summary,
        pose_interaction_path=args.pose_interaction,
        matrix_path=args.matrix,
        report_path=args.report,
        predictions_path=args.predictions,
        yield_predictions_path=args.yield_predictions,
        splits_path=args.splits,
        readiness_report_path=args.readiness_report,
    )
    print(f"Stage 2p publication benchmark: {report['readiness']['status']}")
    print(f"Fixed-catalyst modelable records: {report['modelable_record_count']}")
    print(f"Locked incumbent: {report['locked_incumbent']}")
    print(f"Wrote readiness report to {args.readiness_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

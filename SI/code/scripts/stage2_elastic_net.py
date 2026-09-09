#!/usr/bin/env python3
"""Build the Stage 2 ee matrix and run an Elastic Net baseline."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import median
from typing import Any

import numpy


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_TIER1 = ROOT / "data/jacs_2025/stage2/features/tier1.jsonl"
DEFAULT_POSE_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"
DEFAULT_POSE_INTERACTION = ROOT / "data/jacs_2025/stage2/features/pose-interaction.jsonl"
DEFAULT_MATRIX = ROOT / "data/jacs_2025/stage2/features/seed-ee-matrix.csv"
DEFAULT_REPORT = ROOT / "data/jacs_2025/stage2/reports/seed-ee-elastic-net.json"
DEFAULT_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/seed-ee-elastic-net-predictions.csv"
AGGREGATIONS = ["count", "min", "q05", "median", "mean", "q95", "max", "std"]
ALPHA_GRID = [0.1, 1.0, 10.0]
L1_RATIO_GRID = [0.2, 0.5, 0.8]
BAYESIAN_BOOTSTRAP_DRAWS = 20000
BAYESIAN_BOOTSTRAP_SEED = 20260730


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def add_numeric_features(target: dict[str, float], prefix: str, values: dict[str, Any]) -> None:
    for key, value in values.items():
        feature_name = f"{prefix}.{key}"
        if is_number(value):
            target[feature_name] = float(value)
        elif isinstance(value, bool):
            target[feature_name] = float(value)


def add_one_hot(target: dict[str, float], prefix: str, key: str, value: Any) -> None:
    if value is not None:
        target[f"{prefix}.{key}={value}"] = 1.0


def quantile(values: list[float], fraction: float) -> float:
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = fraction * (len(sorted_values) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    lower = sorted_values[lower_index]
    upper = sorted_values[upper_index]
    return lower + (upper - lower) * (position - lower_index)


def aggregate_values(values: list[float]) -> dict[str, float]:
    array = numpy.array(values, dtype=float)
    return {
        "count": float(len(values)),
        "min": float(array.min()),
        "q05": quantile(values, 0.05),
        "median": float(median(values)),
        "mean": float(array.mean()),
        "q95": quantile(values, 0.95),
        "max": float(array.max()),
        "std": float(array.std()),
    }


def aggregate_pose_interactions(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    values_by_substrate: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        substrate_id = row["substrate_id"]
        values_by_substrate.setdefault(substrate_id, {})
        features = row["feature_blocks"]["pose_interaction"]
        for key, value in features.items():
            if is_number(value) or isinstance(value, bool):
                values_by_substrate[substrate_id].setdefault(key, []).append(float(value))

    aggregated: dict[str, dict[str, float]] = {}
    for substrate_id, feature_values in values_by_substrate.items():
        substrate_features = {}
        for key, values in feature_values.items():
            for agg_key, agg_value in aggregate_values(values).items():
                substrate_features[f"{key}.{agg_key}"] = agg_value
        aggregated[substrate_id] = substrate_features
    return aggregated


def build_feature_rows(
    records_path: Path,
    tier1_path: Path,
    pose_summary_path: Path,
    pose_interaction_path: Path,
) -> list[dict[str, Any]]:
    records = {
        record["substrate_id"]: record
        for record in read_jsonl(records_path)
        if record["curation_status"] == "feature_ready" and is_number(record["outcome"].get("ee_percent"))
    }
    tier1 = {row["substrate_id"]: row for row in read_jsonl(tier1_path)}
    pose_summary = {row["substrate_id"]: row for row in read_jsonl(pose_summary_path)}
    pose_interaction = aggregate_pose_interactions(read_jsonl(pose_interaction_path))

    rows = []
    for substrate_id in sorted(records):
        record = records[substrate_id]
        feature_values: dict[str, float] = {}
        tier1_blocks = tier1[substrate_id]["feature_blocks"]
        add_numeric_features(feature_values, "tier1_physchem", tier1_blocks["tier1_physchem"])
        fingerprint = tier1_blocks["tier1_fingerprint"]
        add_numeric_features(
            feature_values,
            "tier1_fingerprint",
            {"on_bit_count": fingerprint["on_bit_count"], "radius": fingerprint["radius"], "n_bits": fingerprint["n_bits"]},
        )
        reported_sites = [
            site
            for site in tier1_blocks["candidate_site_features"]
            if site["is_reported_reactive_site"]
        ]
        if len(reported_sites) != 1:
            raise ValueError(f"{substrate_id}: expected exactly one reported candidate-site feature row")
        reported_site = reported_sites[0]
        add_numeric_features(feature_values, "reported_site", reported_site)
        add_one_hot(feature_values, "reported_site", "site_type", reported_site.get("site_type"))
        add_one_hot(feature_values, "reported_site", "hybridization", reported_site.get("hybridization"))
        add_numeric_features(feature_values, "pose_summary", pose_summary[substrate_id]["feature_blocks"]["pose_summary"])
        add_numeric_features(feature_values, "pose_interaction", pose_interaction[substrate_id])
        rows.append(
            {
                "substrate_id": substrate_id,
                "reaction_id": record["reaction_id"],
                "family_id": record["family"]["family_id"],
                "ee_percent": float(record["outcome"]["ee_percent"]),
                "ee_status": record["outcome"]["ee_status"],
                "features": feature_values,
            }
        )
    return rows


def write_matrix(path: Path, rows: list[dict[str, Any]]) -> list[str]:
    feature_names = sorted({name for row in rows for name in row["features"]})
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["substrate_id", "reaction_id", "family_id", "ee_percent", "ee_status"] + feature_names
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            output_row = {
                "substrate_id": row["substrate_id"],
                "reaction_id": row["reaction_id"],
                "family_id": row["family_id"],
                "ee_percent": row["ee_percent"],
                "ee_status": row["ee_status"],
            }
            output_row.update({name: row["features"].get(name, 0.0) for name in feature_names})
            writer.writerow(output_row)
    return feature_names


def matrix_arrays(rows: list[dict[str, Any]], feature_names: list[str]) -> tuple[numpy.ndarray, numpy.ndarray]:
    x = numpy.array([[row["features"].get(name, 0.0) for name in feature_names] for row in rows], dtype=float)
    y = numpy.array([row["ee_percent"] for row in rows], dtype=float)
    return x, y


def soft_threshold(value: float, threshold: float) -> float:
    if value > threshold:
        return value - threshold
    if value < -threshold:
        return value + threshold
    return 0.0


class ElasticNetModel:
    def __init__(self, alpha: float, l1_ratio: float, max_iter: int = 200, tolerance: float = 1e-4) -> None:
        self.alpha = alpha
        self.l1_ratio = l1_ratio
        self.max_iter = max_iter
        self.tolerance = tolerance
        self.x_mean: numpy.ndarray | None = None
        self.x_scale: numpy.ndarray | None = None
        self.y_mean: float | None = None
        self.coefficients: numpy.ndarray | None = None

    def fit(self, x: numpy.ndarray, y: numpy.ndarray) -> "ElasticNetModel":
        self.x_mean = x.mean(axis=0)
        scale = x.std(axis=0)
        scale[scale == 0] = 1.0
        self.x_scale = scale
        self.y_mean = float(y.mean())
        x_scaled = (x - self.x_mean) / self.x_scale
        y_centered = y - self.y_mean
        coefficients = numpy.zeros(x_scaled.shape[1], dtype=float)
        gram = (x_scaled.T @ x_scaled) / x_scaled.shape[0]
        x_y = (x_scaled.T @ y_centered) / x_scaled.shape[0]
        column_norms = numpy.diag(gram)
        l1_penalty = self.alpha * self.l1_ratio
        l2_penalty = self.alpha * (1.0 - self.l1_ratio)

        for _ in range(self.max_iter):
            previous = coefficients.copy()
            for column_index in range(x_scaled.shape[1]):
                rho = float(x_y[column_index] - gram[column_index] @ coefficients + column_norms[column_index] * coefficients[column_index])
                updated = soft_threshold(rho, l1_penalty) / (column_norms[column_index] + l2_penalty)
                coefficients[column_index] = updated
            if numpy.max(numpy.abs(coefficients - previous)) < self.tolerance:
                break

        self.coefficients = coefficients
        return self

    def predict(self, x: numpy.ndarray) -> numpy.ndarray:
        if self.x_mean is None or self.x_scale is None or self.y_mean is None or self.coefficients is None:
            raise ValueError("Model is not fitted")
        return ((x - self.x_mean) / self.x_scale) @ self.coefficients + self.y_mean


def metrics(y_true: numpy.ndarray, y_pred: numpy.ndarray) -> dict[str, float]:
    residuals = y_pred - y_true
    total = ((y_true - y_true.mean()) ** 2).sum()
    r2 = 1.0 - float((residuals * residuals).sum() / total) if total else float("nan")
    return {
        "mae": float(numpy.abs(residuals).mean()),
        "rmse": float(numpy.sqrt((residuals * residuals).mean())),
        "max_abs_error": float(numpy.abs(residuals).max()),
        "r2": r2,
    }


def weighted_metrics(y_true: numpy.ndarray, y_pred: numpy.ndarray, weights: numpy.ndarray) -> dict[str, float]:
    residuals = y_pred - y_true
    centered = y_true - float(numpy.sum(weights * y_true))
    total = float(numpy.sum(weights * centered * centered))
    weighted_sse = float(numpy.sum(weights * residuals * residuals))
    return {
        "mae": float(numpy.sum(weights * numpy.abs(residuals))),
        "rmse": float(numpy.sqrt(weighted_sse)),
        "mean_error": float(numpy.sum(weights * residuals)),
        "r2": 1.0 - weighted_sse / total if total else float("nan"),
    }


def interval(values: numpy.ndarray, low: float = 0.025, high: float = 0.975) -> dict[str, float]:
    return {
        "mean": float(values.mean()),
        "median": float(numpy.quantile(values, 0.5)),
        "ci95_low": float(numpy.quantile(values, low)),
        "ci95_high": float(numpy.quantile(values, high)),
    }


def bayesian_bootstrap_metric_intervals(
    y_true: numpy.ndarray,
    y_pred: numpy.ndarray,
    draws: int = BAYESIAN_BOOTSTRAP_DRAWS,
    seed: int = BAYESIAN_BOOTSTRAP_SEED,
) -> dict[str, dict[str, float] | int | str]:
    rng = numpy.random.default_rng(seed)
    samples = {"mae": [], "rmse": [], "mean_error": [], "r2": []}
    for _ in range(draws):
        weights = rng.dirichlet(numpy.ones(len(y_true)))
        draw_metrics = weighted_metrics(y_true, y_pred, weights)
        for key in samples:
            samples[key].append(draw_metrics[key])
    return {
        "method": "bayesian_bootstrap_over_oof_residual_records",
        "draw_count": draws,
        "random_seed": seed,
        "mae": interval(numpy.array(samples["mae"], dtype=float)),
        "rmse": interval(numpy.array(samples["rmse"], dtype=float)),
        "mean_error": interval(numpy.array(samples["mean_error"], dtype=float)),
        "r2": interval(numpy.array(samples["r2"], dtype=float)),
    }


def residual_distribution_summary(residuals: numpy.ndarray) -> dict[str, float]:
    abs_residuals = numpy.abs(residuals)
    return {
        "mean_error": float(residuals.mean()),
        "median_error": float(numpy.median(residuals)),
        "residual_std": float(residuals.std(ddof=1)),
        "residual_q05": float(numpy.quantile(residuals, 0.05)),
        "residual_q25": float(numpy.quantile(residuals, 0.25)),
        "residual_q75": float(numpy.quantile(residuals, 0.75)),
        "residual_q95": float(numpy.quantile(residuals, 0.95)),
        "abs_error_median": float(numpy.median(abs_residuals)),
        "abs_error_q75": float(numpy.quantile(abs_residuals, 0.75)),
        "abs_error_q90": float(numpy.quantile(abs_residuals, 0.90)),
        "within_10_ee_fraction": float(numpy.mean(abs_residuals <= 10.0)),
        "within_20_ee_fraction": float(numpy.mean(abs_residuals <= 20.0)),
    }


def pearson_correlation(left: numpy.ndarray, right: numpy.ndarray) -> float:
    if len(left) < 2 or left.std() == 0 or right.std() == 0:
        return float("nan")
    return float(numpy.corrcoef(left, right)[0, 1])


def calibration_summary(y_true: numpy.ndarray, y_pred: numpy.ndarray) -> dict[str, float]:
    design = numpy.column_stack([numpy.ones(len(y_pred)), y_pred])
    intercept, slope = numpy.linalg.lstsq(design, y_true, rcond=None)[0]
    return {
        "observed_vs_predicted_pearson_r": pearson_correlation(y_true, y_pred),
        "actual_on_predicted_intercept": float(intercept),
        "actual_on_predicted_slope": float(slope),
    }


def empirical_prediction_interval(prediction: float, calibration_residuals: numpy.ndarray) -> dict[str, float]:
    if len(calibration_residuals) == 0:
        return {
            "pred_interval_80_low": prediction,
            "pred_interval_80_high": prediction,
            "pred_interval_95_low": prediction,
            "pred_interval_95_high": prediction,
        }
    return {
        "pred_interval_80_low": float(prediction + numpy.quantile(calibration_residuals, 0.10)),
        "pred_interval_80_high": float(prediction + numpy.quantile(calibration_residuals, 0.90)),
        "pred_interval_95_low": float(prediction + numpy.quantile(calibration_residuals, 0.025)),
        "pred_interval_95_high": float(prediction + numpy.quantile(calibration_residuals, 0.975)),
    }


def leave_one_out_predictions(x: numpy.ndarray, y: numpy.ndarray, alpha: float, l1_ratio: float) -> numpy.ndarray:
    predictions = numpy.zeros(len(y), dtype=float)
    for holdout_index in range(len(y)):
        train_indices = [index for index in range(len(y)) if index != holdout_index]
        model = ElasticNetModel(alpha=alpha, l1_ratio=l1_ratio).fit(x[train_indices], y[train_indices])
        predictions[holdout_index] = model.predict(x[[holdout_index]])[0]
    return predictions


def select_hyperparameters(x: numpy.ndarray, y: numpy.ndarray) -> dict[str, float]:
    best: dict[str, float] | None = None
    for alpha in ALPHA_GRID:
        for l1_ratio in L1_RATIO_GRID:
            predictions = leave_one_out_predictions(x, y, alpha, l1_ratio)
            score = metrics(y, predictions)["mae"]
            if best is None or score < best["mae"]:
                best = {"alpha": alpha, "l1_ratio": l1_ratio, "mae": score}
    assert best is not None
    return best


def top_coefficients(model: ElasticNetModel, feature_names: list[str], limit: int = 25) -> list[dict[str, float | str]]:
    if model.coefficients is None or model.x_scale is None:
        raise ValueError("Model is not fitted")
    original_scale_coefficients = model.coefficients / model.x_scale
    ranked = sorted(
        [
            {"feature": feature_names[index], "coefficient": float(original_scale_coefficients[index])}
            for index in range(len(feature_names))
            if abs(original_scale_coefficients[index]) > 1e-12
        ],
        key=lambda item: abs(item["coefficient"]),
        reverse=True,
    )
    return ranked[:limit]


def run_baseline(
    records_path: Path,
    tier1_path: Path,
    pose_summary_path: Path,
    pose_interaction_path: Path,
    matrix_path: Path,
    report_path: Path,
    predictions_path: Path,
) -> dict[str, Any]:
    rows = build_feature_rows(records_path, tier1_path, pose_summary_path, pose_interaction_path)
    feature_names = write_matrix(matrix_path, rows)
    x, y = matrix_arrays(rows, feature_names)
    active_feature_mask = x.std(axis=0) > 0
    x_model = x[:, active_feature_mask]
    model_feature_names = [name for name, active in zip(feature_names, active_feature_mask, strict=True) if active]
    selected_params = select_hyperparameters(x_model, y)
    elastic_predictions = leave_one_out_predictions(
        x_model,
        y,
        alpha=selected_params["alpha"],
        l1_ratio=selected_params["l1_ratio"],
    )
    mean_predictions = numpy.array([
        y[[index for index in range(len(y)) if index != holdout_index]].mean()
        for holdout_index in range(len(y))
    ])
    final_params = selected_params
    final_model = ElasticNetModel(alpha=final_params["alpha"], l1_ratio=final_params["l1_ratio"]).fit(x_model, y)
    final_predictions = final_model.predict(x_model)
    elastic_residuals = elastic_predictions - y
    mean_residuals = mean_predictions - y
    elastic_metrics = metrics(y, elastic_predictions)
    mean_metrics = metrics(y, mean_predictions)
    elastic_residual_summary = residual_distribution_summary(elastic_residuals)
    mean_residual_summary = residual_distribution_summary(mean_residuals)
    elastic_calibration = calibration_summary(y, elastic_predictions)
    mean_calibration = calibration_summary(y, mean_predictions)
    elastic_bayesian_bootstrap = bayesian_bootstrap_metric_intervals(y, elastic_predictions)
    mean_bayesian_bootstrap = bayesian_bootstrap_metric_intervals(y, mean_predictions, seed=BAYESIAN_BOOTSTRAP_SEED + 1)

    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    with predictions_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "fold_index",
                "substrate_id",
                "family_id",
                "train_substrate_ids",
                "train_count",
                "ee_percent",
                "elastic_net_loo_prediction",
                "elastic_net_residual",
                "mean_loo_prediction",
                "mean_residual",
                "elastic_net_abs_error",
                "mean_abs_error",
                "elastic_net_pred_interval_80_low",
                "elastic_net_pred_interval_80_high",
                "elastic_net_pred_interval_95_low",
                "elastic_net_pred_interval_95_high",
                "selected_alpha",
                "selected_l1_ratio",
            ],
        )
        writer.writeheader()
        for index, row in enumerate(rows):
            train_substrate_ids = [
                train_row["substrate_id"]
                for train_index, train_row in enumerate(rows)
                if train_index != index
            ]
            intervals = empirical_prediction_interval(
                elastic_predictions[index],
                numpy.delete(elastic_residuals, index),
            )
            writer.writerow(
                {
                    "fold_index": index + 1,
                    "substrate_id": row["substrate_id"],
                    "family_id": row["family_id"],
                    "train_substrate_ids": "|".join(train_substrate_ids),
                    "train_count": len(train_substrate_ids),
                    "ee_percent": y[index],
                    "elastic_net_loo_prediction": elastic_predictions[index],
                    "elastic_net_residual": elastic_residuals[index],
                    "mean_loo_prediction": mean_predictions[index],
                    "mean_residual": mean_residuals[index],
                    "elastic_net_abs_error": abs(elastic_predictions[index] - y[index]),
                    "mean_abs_error": abs(mean_predictions[index] - y[index]),
                    "elastic_net_pred_interval_80_low": intervals["pred_interval_80_low"],
                    "elastic_net_pred_interval_80_high": intervals["pred_interval_80_high"],
                    "elastic_net_pred_interval_95_low": intervals["pred_interval_95_low"],
                    "elastic_net_pred_interval_95_high": intervals["pred_interval_95_high"],
                    "selected_alpha": selected_params["alpha"],
                    "selected_l1_ratio": selected_params["l1_ratio"],
                }
            )

    report = {
        "schema_version": "stage2-ee-elastic-net-report-v1",
        "status": "training_smoke_test_not_predictive_claim",
        "target": "ee_percent",
        "record_count": len(rows),
        "feature_count": len(feature_names),
        "nonconstant_feature_count": len(model_feature_names),
        "feature_policy": "numeric_tier1_reported_site_pose_summary_and_aggregated_pose_interaction_no_full_fingerprint_bits",
        "matrix_path": display_path(matrix_path),
        "predictions_path": display_path(predictions_path),
        "validation": "leave_one_out_cv_with_seed_level_hyperparameter_selection",
        "oof_design": {
            "fold_count": len(rows),
            "holdout_count_per_fold": 1,
            "train_count_per_fold": len(rows) - 1,
            "folds": [
                {
                    "fold_index": index + 1,
                    "holdout_substrate_id": row["substrate_id"],
                    "train_substrate_ids": [
                        train_row["substrate_id"]
                        for train_index, train_row in enumerate(rows)
                        if train_index != index
                    ],
                }
                for index, row in enumerate(rows)
            ],
        },
        "elastic_net": {
            "implementation": "local_coordinate_descent",
            "alpha_grid": ALPHA_GRID,
            "l1_ratio_grid": L1_RATIO_GRID,
            "selected_hyperparameters": {
                "alpha": selected_params["alpha"],
                "l1_ratio": selected_params["l1_ratio"],
                "selection_loo_mae": selected_params["mae"],
            },
            "loo_metrics": elastic_metrics,
            "residual_summary": elastic_residual_summary,
            "calibration_summary": elastic_calibration,
            "bayesian_bootstrap_metric_intervals": elastic_bayesian_bootstrap,
            "final_full_seed_hyperparameters": {
                "alpha": final_params["alpha"],
                "l1_ratio": final_params["l1_ratio"],
                "loo_mae_used_for_selection": final_params["mae"],
            },
            "full_seed_fit_metrics": metrics(y, final_predictions),
            "nonzero_coefficient_count": int(numpy.sum(numpy.abs(final_model.coefficients) > 1e-12)),
            "top_coefficients": top_coefficients(final_model, model_feature_names),
        },
        "mean_baseline": {
            "loo_metrics": mean_metrics,
            "residual_summary": mean_residual_summary,
            "calibration_summary": mean_calibration,
            "bayesian_bootstrap_metric_intervals": mean_bayesian_bootstrap,
        },
        "plot_ready_series": [
            {
                "fold_index": index + 1,
                "substrate_id": row["substrate_id"],
                "family_id": row["family_id"],
                "observed_ee_percent": float(y[index]),
                "elastic_net_oof_prediction": float(elastic_predictions[index]),
                "elastic_net_oof_residual": float(elastic_residuals[index]),
                "elastic_net_abs_error": float(abs(elastic_residuals[index])),
                "mean_oof_prediction": float(mean_predictions[index]),
                "mean_oof_residual": float(mean_residuals[index]),
            }
            for index, row in enumerate(rows)
        ],
        "caveats": [
            "Only 12 seed records are available; this is a pipeline smoke test, not a robust predictive model.",
            "Hyperparameters are selected once by seed-level leave-one-out CV; this is faster and less strict than nested CV.",
            "Bayesian intervals are Bayesian-bootstrap summaries over the 12 OOF residual records, not a full Bayesian Elastic Net posterior.",
            "Per-substrate prediction intervals are empirical residual intervals and should be treated as calibration diagnostics.",
            "Family-held-out scoring is not yet meaningful for mostly singleton families.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--tier1", type=Path, default=DEFAULT_TIER1)
    parser.add_argument("--pose-summary", type=Path, default=DEFAULT_POSE_SUMMARY)
    parser.add_argument("--pose-interaction", type=Path, default=DEFAULT_POSE_INTERACTION)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_baseline(
        args.records,
        args.tier1,
        args.pose_summary,
        args.pose_interaction,
        args.matrix,
        args.report,
        args.predictions,
    )
    elastic = report["elastic_net"]["loo_metrics"]
    mean_baseline = report["mean_baseline"]["loo_metrics"]
    print(
        "Wrote Stage 2 Elastic Net ee baseline: "
        f"MAE={elastic['mae']:.3f}, RMSE={elastic['rmse']:.3f}; "
        f"mean-baseline MAE={mean_baseline['mae']:.3f} to {display_path(args.report)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

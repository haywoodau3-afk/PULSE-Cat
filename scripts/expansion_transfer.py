#!/usr/bin/env python3
"""Evaluate structure-only transfer learning from Fe(P7)Cl to Angew catalysts.

The public evaluation seam is :func:`compare_models`.  It takes source and target
rows with a common numeric feature vector and evaluates family-held-out target
folds.  The command-line wrapper adds the repository's curated source matrix and
extension JSONL records, then writes a JSON report and a flat prediction table.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

import numpy
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "data/expansion/records.jsonl"
DEFAULT_SOURCE_MATRIX = ROOT / "data/jacs_2025/stage2/features/full-scope-structure-ee-matrix.csv"
DEFAULT_REPORT = ROOT / "data/expansion/results/transfer-model-comparison.json"
DEFAULT_PREDICTIONS = ROOT / "data/expansion/results/transfer-predictions.csv"
MODEL_NAMES = (
    "target_only",
    "source_zero_shot",
    "pooled_domain_indicator",
    "source_coefficient_regularized",
    "source_prediction_residual",
)
SOURCE_METADATA_FIELDS = {
    "substrate_id",
    "reaction_id",
    "family_id",
    "catalyst_id",
    "temperature_c",
    "target_name",
    "target_value",
    "ee_percent",
    "isolated_yield_percent",
    "yield_qualifier",
    "ee_status",
    "azide_smiles",
    "feature_set",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _feature_vector(row: dict[str, Any], feature_names: list[str] | None = None) -> numpy.ndarray:
    features = row["features"]
    if isinstance(features, dict):
        if feature_names is None:
            feature_names = sorted(features)
        return numpy.array([float(features.get(name, 0.0)) for name in feature_names], dtype=float)
    return numpy.asarray(features, dtype=float)


def family_heldout_folds(source_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build target-family folds while excluding paired compounds from source training."""

    folds = []
    for family_id in sorted({row["family_id"] for row in target_rows}):
        target_test = [row for row in target_rows if row["family_id"] == family_id]
        target_train = [row for row in target_rows if row["family_id"] != family_id]
        heldout_compounds = {row["compound_id"] for row in target_test}
        source_train = [row for row in source_rows if row["compound_id"] not in heldout_compounds]
        if not target_test or not target_train:
            continue
        folds.append(
            {
                "heldout_family": family_id,
                "target_train": target_train,
                "target_test": target_test,
                "source_train": source_train,
            }
        )
    if not folds:
        raise ValueError("family-heldout evaluation needs at least two target families")
    return folds


def _arrays(rows: list[dict[str, Any]]) -> tuple[numpy.ndarray, numpy.ndarray]:
    if not rows:
        raise ValueError("cannot fit a model without training rows")
    return (
        numpy.vstack([_feature_vector(row) for row in rows]),
        numpy.array([float(row["ee_percent"]) for row in rows], dtype=float),
    )


def _fit_ridge(train_rows: list[dict[str, Any]], alpha: float) -> tuple[StandardScaler, Ridge]:
    x_train, y_train = _arrays(train_rows)
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x_train)
    model = Ridge(alpha=alpha)
    model.fit(x_scaled, y_train)
    return scaler, model


def _predict(model: tuple[StandardScaler, Ridge], rows: list[dict[str, Any]]) -> numpy.ndarray:
    scaler, estimator = model
    x = numpy.vstack([_feature_vector(row) for row in rows])
    return estimator.predict(scaler.transform(x))


def _metrics(y_true: Iterable[float], y_pred: Iterable[float]) -> dict[str, Any]:
    observed = numpy.asarray(list(y_true), dtype=float)
    predicted = numpy.asarray(list(y_pred), dtype=float)
    residuals = predicted - observed
    result: dict[str, Any] = {
        "target_count": int(len(observed)),
        "mae": float(mean_absolute_error(observed, predicted)),
        "rmse": float(mean_squared_error(observed, predicted) ** 0.5),
        "mean_error": float(residuals.mean()),
        "within_10_ee_fraction": float(numpy.mean(numpy.abs(residuals) <= 10.0)),
        "within_20_ee_fraction": float(numpy.mean(numpy.abs(residuals) <= 20.0)),
    }
    result["r2"] = (
        float(r2_score(observed, predicted))
        if len(observed) > 1 and float(numpy.var(observed)) > 0
        else None
    )
    return result


def _pooled_features(
    rows: list[dict[str, Any]],
    feature_length: int,
    catalyst_levels: list[str],
) -> numpy.ndarray:
    vectors = []
    for row in rows:
        base = _feature_vector(row)
        domain = 0.0 if row.get("domain") == "source" else 1.0
        catalyst = [1.0 if row.get("catalyst_id") == level else 0.0 for level in catalyst_levels]
        vectors.append(numpy.concatenate([base, numpy.array([domain], dtype=float), numpy.array(catalyst)]))
    return numpy.vstack(vectors) if vectors else numpy.empty((0, feature_length + 1 + len(catalyst_levels)))


def _fit_pooled(source_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]], alpha: float) -> tuple[StandardScaler, Ridge, list[str]]:
    combined = [dict(row, domain="source") for row in source_rows] + [dict(row, domain="target") for row in target_rows]
    levels = sorted({str(row["catalyst_id"]) for row in combined})
    feature_length = len(_feature_vector(combined[0]))
    x = _pooled_features(combined, feature_length, levels)
    y = numpy.array([float(row["ee_percent"]) for row in combined], dtype=float)
    scaler = StandardScaler()
    model = Ridge(alpha=alpha)
    model.fit(scaler.fit_transform(x), y)
    return scaler, model, levels


def _predict_pooled(
    fitted: tuple[StandardScaler, Ridge, list[str]],
    rows: list[dict[str, Any]],
) -> numpy.ndarray:
    scaler, model, levels = fitted
    feature_length = len(_feature_vector(rows[0]))
    x = _pooled_features([dict(row, domain="target") for row in rows], feature_length, levels)
    return model.predict(scaler.transform(x))


def _fit_coefficient_regularized(
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    alpha: float,
    transfer_lambda: float,
) -> tuple[StandardScaler, numpy.ndarray, float]:
    source_scaler, source_model = _fit_ridge(source_rows, alpha)
    x_target = source_scaler.transform(numpy.vstack([_feature_vector(row) for row in target_rows]))
    y_target = numpy.array([float(row["ee_percent"]) for row in target_rows], dtype=float)
    y_centered = y_target - float(y_target.mean())
    identity = numpy.eye(x_target.shape[1])
    lhs = x_target.T @ x_target + (alpha + transfer_lambda) * identity
    rhs = x_target.T @ y_centered + transfer_lambda * source_model.coef_
    coefficients = numpy.linalg.solve(lhs, rhs)
    return source_scaler, coefficients, float(y_target.mean())


def _predict_coefficient_regularized(
    fitted: tuple[StandardScaler, numpy.ndarray, float], rows: list[dict[str, Any]]
) -> numpy.ndarray:
    scaler, coefficients, intercept = fitted
    x = scaler.transform(numpy.vstack([_feature_vector(row) for row in rows]))
    return intercept + x @ coefficients


def _fit_residual_model(source_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]], alpha: float):
    source_model = _fit_ridge(source_rows, alpha)
    source_predictions = _predict(source_model, target_rows)
    residual_rows = [dict(row, ee_percent=float(row["ee_percent"]) - prediction) for row, prediction in zip(target_rows, source_predictions)]
    residual_model = _fit_ridge(residual_rows, alpha)
    return source_model, residual_model


def compare_models(
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    *,
    alpha: float = 10.0,
    transfer_lambda: float = 10.0,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Compare transfer strategies on family-held-out target predictions."""

    if not source_rows:
        raise ValueError("source rows are required for transfer evaluation")
    folds = family_heldout_folds(source_rows, target_rows)
    predictions: list[dict[str, Any]] = []
    for fold in folds:
        source_train = fold["source_train"]
        target_train = fold["target_train"]
        target_test = fold["target_test"]
        target_model = _fit_ridge(target_train, alpha)
        source_model = _fit_ridge(source_train, alpha)
        pooled_model = _fit_pooled(source_train, target_train, alpha)
        regularized_model = _fit_coefficient_regularized(source_train, target_train, alpha, transfer_lambda)
        residual_source_model, residual_model = _fit_residual_model(source_train, target_train, alpha)
        prediction_vectors = {
            "target_only": _predict(target_model, target_test),
            "source_zero_shot": _predict(source_model, target_test),
            "pooled_domain_indicator": _predict_pooled(pooled_model, target_test),
            "source_coefficient_regularized": _predict_coefficient_regularized(regularized_model, target_test),
            "source_prediction_residual": _predict(residual_source_model, target_test)
            + _predict(residual_model, target_test),
        }
        for index, row in enumerate(target_test):
            row_predictions = {name: float(values[index]) for name, values in prediction_vectors.items()}
            predictions.append(
                {
                    "compound_id": row["compound_id"],
                    "catalyst_id": row["catalyst_id"],
                    "family_id": row["family_id"],
                    "heldout_family": fold["heldout_family"],
                    "observed_ee_percent": float(row["ee_percent"]),
                    "predictions": row_predictions,
                    "absolute_errors": {
                        name: abs(value - float(row["ee_percent"])) for name, value in row_predictions.items()
                    },
                }
            )

    report_models = {
        name: _metrics(
            [row["observed_ee_percent"] for row in predictions],
            [row["predictions"][name] for row in predictions],
        )
        for name in MODEL_NAMES
    }
    per_catalyst: dict[str, dict[str, dict[str, Any]]] = {}
    for catalyst_id in sorted({row["catalyst_id"] for row in predictions}):
        catalyst_rows = [row for row in predictions if row["catalyst_id"] == catalyst_id]
        per_catalyst[catalyst_id] = {
            name: _metrics(
                [row["observed_ee_percent"] for row in catalyst_rows],
                [row["predictions"][name] for row in catalyst_rows],
            )
            for name in MODEL_NAMES
        }
    baseline_mae = report_models["target_only"]["mae"]
    transfer_gate = {}
    for name in MODEL_NAMES:
        delta = (baseline_mae - report_models[name]["mae"]) / baseline_mae if baseline_mae else 0.0
        transfer_gate[name] = {
            "relative_mae_delta_vs_target_only": float(delta),
            "passes_10_percent_gate": bool(name != "target_only" and delta >= 0.10),
            "negative_transfer": bool(name != "target_only" and delta < 0.0),
        }
    per_catalyst_transfer_gate: dict[str, dict[str, dict[str, Any]]] = {}
    for catalyst_id, catalyst_models in per_catalyst.items():
        catalyst_baseline = catalyst_models["target_only"]["mae"]
        per_catalyst_transfer_gate[catalyst_id] = {}
        for name in MODEL_NAMES:
            delta = (
                (catalyst_baseline - catalyst_models[name]["mae"]) / catalyst_baseline
                if catalyst_baseline
                else 0.0
            )
            per_catalyst_transfer_gate[catalyst_id][name] = {
                "relative_mae_delta_vs_target_only": float(delta),
                "passes_10_percent_gate": bool(name != "target_only" and delta >= 0.10),
                "negative_transfer": bool(name != "target_only" and delta < 0.0),
            }
    return {
        "models": report_models,
        "per_catalyst": per_catalyst,
        "transfer_gate": transfer_gate,
        "per_catalyst_transfer_gate": per_catalyst_transfer_gate,
        "fold_count": len(folds),
        "fold_families": [fold["heldout_family"] for fold in folds],
    }, predictions


def _load_benchmark_module():
    path = ROOT / "scripts" / "stage2_full_scope_benchmark.py"
    spec = importlib.util.spec_from_file_location("stage2_full_scope_benchmark", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_source_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        raw_rows = list(csv.DictReader(stream))
    raw_rows = [row for row in raw_rows if row.get("catalyst_id") == "fe-p7-cl" and row.get("ee_percent") not in {None, ""}]
    if not raw_rows:
        raise ValueError(f"no modelable Fe(P7)Cl source rows in {path}")
    feature_names = sorted(
        key for key in raw_rows[0] if key not in SOURCE_METADATA_FIELDS
    )
    rows = []
    for row in raw_rows:
        rows.append(
            {
                "compound_id": f"cmp-{row['substrate_id']}",
                "family_id": row["family_id"],
                "catalyst_id": row["catalyst_id"],
                "features": [float(row.get(name) or 0.0) for name in feature_names],
                "ee_percent": float(row["ee_percent"]),
            }
        )
    return rows, feature_names


def load_target_rows(path: Path, feature_names: list[str], pathway: str = "aryl") -> list[dict[str, Any]]:
    benchmark = _load_benchmark_module()
    rows = []
    for record in read_jsonl(path):
        if record.get("record_role") != "primary_scope":
            continue
        if pathway != "all" and record.get("pathway_id") != pathway:
            continue
        outcome = record.get("outcome", {})
        smiles = record.get("substrate", {}).get("smiles")
        ee = outcome.get("ee_percent")
        if outcome.get("ee_status") not in {"reported", "true_zero"} or ee is None or not smiles:
            continue
        feature_dict, _ = benchmark.featurize_record({"substrate_id": record["compound_id"], "structure": {"azide_smiles": smiles}})
        family = record.get("family", {})
        family_id = family.get("family_id") or record["split_group"]
        rows.append(
            {
                "compound_id": record["compound_id"],
                "family_id": family_id,
                "catalyst_id": record["catalyst_id"],
                "features": [float(feature_dict.get(name, 0.0)) for name in feature_names],
                "ee_percent": float(ee),
            }
        )
    if not rows:
        raise ValueError(f"no modelable extension rows for pathway={pathway} in {path}")
    return rows


def write_predictions(path: Path, predictions: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "compound_id",
        "catalyst_id",
        "family_id",
        "heldout_family",
        "observed_ee_percent",
    ] + [name for model in MODEL_NAMES for name in (f"{model}_prediction", f"{model}_absolute_error")]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in predictions:
            flat = {key: row[key] for key in fieldnames if key in row}
            for model in MODEL_NAMES:
                flat[f"{model}_prediction"] = row["predictions"][model]
                flat[f"{model}_absolute_error"] = row["absolute_errors"][model]
            writer.writerow(flat)


def run_pipeline(
    records_path: Path = DEFAULT_RECORDS,
    source_matrix_path: Path = DEFAULT_SOURCE_MATRIX,
    pathway: str = "aryl",
    report_path: Path = DEFAULT_REPORT,
    predictions_path: Path = DEFAULT_PREDICTIONS,
) -> dict[str, Any]:
    source_rows, feature_names = load_source_rows(source_matrix_path)
    target_rows = load_target_rows(records_path, feature_names, pathway)
    report, predictions = compare_models(source_rows, target_rows)
    report.update(
        {
            "status": "valid",
            "pilot_scope": "curated exact-overlap Angew extension records",
            "mapping_confidence": "high for exact JACS/Angew substrate identity; not a full Angew scope curation",
            "pathway": pathway,
            "feature_set": "common structure-only descriptors plus Morgan fingerprints",
            "source": {"paper": "jacs-2025", "catalyst_id": "fe-p7-cl", "row_count": len(source_rows)},
            "target": {
                "paper": "angew-2023",
                "row_count": len(target_rows),
                "catalyst_counts": {
                    catalyst: sum(row["catalyst_id"] == catalyst for row in target_rows)
                    for catalyst in sorted({row["catalyst_id"] for row in target_rows})
                },
            },
        }
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_predictions(predictions_path, predictions)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--source-matrix", type=Path, default=DEFAULT_SOURCE_MATRIX)
    parser.add_argument("--pathway", choices=("aryl", "sulfonyl", "all"), default="aryl")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_pipeline(args.records, args.source_matrix, args.pathway, args.report, args.predictions)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

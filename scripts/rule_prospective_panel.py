#!/usr/bin/env python3
"""Score the predeclared P7 late-stage panel with structure plus hard rules.

This is a prospective computational checkpoint.  The five latest-stage
substrates are kept unlabelled; their existing records are used only as
candidate structures.  The historical P7 training scope is fixed to the same
38-substrate analysis used by the rule-mixture benchmarks.  V0 is the current
structure-only comparator, while V4 and V6 add the new frozen rule blocks.

The output is deliberately separate from the existing Stage 2/Stage 3a
latest-stage predictions because this analysis does not use pose-aware Stage
2p features.  It is therefore a representation ablation and candidate-ranking
artifact, not an experimental result.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import rule_based_diversity as rules  # noqa: E402
import rule_scope_progression as rule_progression  # noqa: E402
import scope_progression as baseline  # noqa: E402


SCHEMA_VERSION = "rule-prospective-panel-v1"
DEFAULT_SEED = 20260824
DEFAULT_VERSIONS = ("v0", "v4", "v6")
DEFAULT_EXCLUDE_IDS = ("1ad", "1z", "1an")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def numeric_target(table: baseline.FeatureTable, target: str) -> np.ndarray:
    values = [baseline.outcome_value(row.record, target) for row in table.rows]
    return np.asarray([value if value is not None else np.nan for value in values], dtype=float)


def version_matrix(
    base_table: baseline.FeatureTable,
    rule_table: rules.RuleFeatureTable,
    version: str,
) -> np.ndarray:
    base = base_table.matrix("rdkit_morgan")
    if version == "v0":
        return base
    return np.column_stack([base, rule_table.matrix(version, scaled=True)])


def loo_predictions(
    table: baseline.FeatureTable,
    matrix: np.ndarray,
    target_values: np.ndarray,
    train_indices: Sequence[int],
) -> dict[str, np.ndarray]:
    predictions: dict[str, list[float]] = {"ridge": [], "elastic_net": [], "tanimoto_knn": []}
    observed: list[float] = []
    for held_out in train_indices:
        train = [index for index in train_indices if index != held_out]
        output = baseline.fit_predict_models(
            matrix,
            table.fingerprint_matrix,
            train,
            [held_out],
            target_values,
            include_elastic_net=True,
        )
        if not output:
            continue
        observed.append(float(target_values[held_out]))
        for model_name in predictions:
            predictions[model_name].append(float(output[model_name][0]))
    return {name: np.asarray(values, dtype=float) for name, values in predictions.items()}


def loo_metrics(
    table: baseline.FeatureTable,
    matrix: np.ndarray,
    target_values: np.ndarray,
    train_indices: Sequence[int],
) -> dict[str, dict[str, Any]]:
    predictions: dict[str, list[float]] = {"ridge": [], "elastic_net": [], "tanimoto_knn": []}
    observed: list[float] = []
    for held_out in train_indices:
        train = [index for index in train_indices if index != held_out]
        output = baseline.fit_predict_models(
            matrix,
            table.fingerprint_matrix,
            train,
            [held_out],
            target_values,
            include_elastic_net=True,
        )
        if not output:
            continue
        observed.append(float(target_values[held_out]))
        for model_name in predictions:
            predictions[model_name].append(float(output[model_name][0]))
    observed_array = np.asarray(observed, dtype=float)
    return {
        name: baseline.metrics(observed_array, np.asarray(values, dtype=float))
        for name, values in predictions.items()
    }


def candidate_components(
    table: baseline.FeatureTable,
    rule_table: rules.RuleFeatureTable,
    matrix: np.ndarray,
    target_values: np.ndarray,
    train_indices: Sequence[int],
    candidate_indices: Sequence[int],
    version: str,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Score candidates after the fixed two-substrate diversity seed."""

    rng = random.Random(DEFAULT_SEED)
    selected = baseline.seed_indices(table, train_indices, "diversity_first", rng)
    return rule_progression.selection_components(
        table,
        rule_table,
        matrix,
        target_values,
        selected,
        candidate_indices,
        "uncertainty_diversity",
        version,
    )


def candidate_rule_fields(rule_row: rules.RuleFeatureRow) -> dict[str, Any]:
    target_bde = rule_row.numeric.get("target_estimated_bde", 0.0)
    competition_gap = rule_row.numeric.get("bde_competition_gap", 0.0)
    return {
        "target_site_type": rule_row.categorical.get("target_site_class"),
        "target_bde_class": rule_row.categorical.get("target_bde_class"),
        "target_estimated_bde": target_bde,
        "minimum_estimated_bde": target_bde - competition_gap,
        "bde_competition_gap": competition_gap,
        "candidate_site_count": rule_row.numeric.get("candidate_site_count"),
        "reaction_competition_class": rule_row.categorical.get("reaction_competition_class"),
        "path_accessibility_class": rule_row.categorical.get("path_accessibility_class"),
        "local_reactivity_regime": rule_row.categorical.get("local_reactivity_regime"),
    }


def run(
    records_path: Path,
    latestage_path: Path,
    output_dir: Path,
    versions: Sequence[str] = DEFAULT_VERSIONS,
    exclude_ids: Sequence[str] = DEFAULT_EXCLUDE_IDS,
) -> dict[str, Any]:
    historical_records = baseline.read_jsonl(records_path)
    latestage_records = baseline.read_jsonl(latestage_path)
    excluded = set(exclude_ids)
    historical_records = [record for record in historical_records if str(record["substrate_id"]) not in excluded]
    historical_rows = baseline.load_scope_rows_from_records(historical_records, "fe-p7-cl")
    candidate_rows = baseline.load_scope_rows_from_records(latestage_records, "fe-p7-cl")
    combined_records = [row.record for row in historical_rows] + [row.record for row in candidate_rows]
    combined_rows = baseline.load_scope_rows_from_records(combined_records, "fe-p7-cl")
    historical_count = len(historical_rows)
    train_indices = list(range(historical_count))
    candidate_indices = list(range(historical_count, len(combined_rows)))
    table = baseline.build_feature_table(combined_rows, None)
    rule_table = rules.build_rule_feature_table(combined_records)
    target_values = numeric_target(table, "ee_percent")
    if any(not np.isfinite(target_values[index]) for index in train_indices):
        raise ValueError("the historical P7 training scope must have finite ee_percent values")

    prediction_rows: list[dict[str, Any]] = []
    model_diagnostics: dict[str, Any] = {}
    initial_seed = [table.rows[index].substrate_id for index in baseline.seed_indices(table, train_indices, "diversity_first", random.Random(DEFAULT_SEED))]
    for version in versions:
        if not rules.is_valid_version_spec(version):
            raise ValueError(f"unsupported rule feature version: {version}")
        matrix = version_matrix(table, rule_table, version)
        final_predictions = baseline.fit_predict_models(
            matrix,
            table.fingerprint_matrix,
            train_indices,
            candidate_indices,
            target_values,
            include_elastic_net=True,
        )
        scores, components = candidate_components(
            table, rule_table, matrix, target_values, train_indices, candidate_indices, version
        )
        model_diagnostics[version] = {
            "matrix_columns": int(matrix.shape[1]),
            "rule_block_signature": "+".join(rules.blocks_for_version(version)) or "none",
            "leave_one_out": loo_metrics(table, matrix, target_values, train_indices),
        }
        for position, index in enumerate(candidate_indices):
            rule_fields = candidate_rule_fields(rule_table.rows[index])
            row = {
                "schema_version": SCHEMA_VERSION,
                "substrate_id": table.rows[index].substrate_id,
                "feature_version": version,
                "block_signature": "+".join(rules.blocks_for_version(version)) or "none",
                "ridge_ee_prediction": float(final_predictions["ridge"][position]),
                "elastic_net_ee_prediction": float(final_predictions["elastic_net"][position]),
                "tanimoto_knn_ee_prediction": float(final_predictions["tanimoto_knn"][position]),
                "acquisition_route": "uncertainty_diversity_after_diversity_seed",
                "acquisition_score": float(scores[position]),
            }
            row.update({name: float(values[position]) for name, values in components.items()})
            row.update(rule_fields)
            prediction_rows.append(row)

    fields = [
        "schema_version", "substrate_id", "feature_version", "block_signature",
        "ridge_ee_prediction", "elastic_net_ee_prediction", "tanimoto_knn_ee_prediction",
        "acquisition_route", "acquisition_score", "diversity_score", "chemical_coverage_score",
        "family_coverage_score", "coverage_score", "uncertainty_score", "predicted_performance_score",
        "target_site_type", "target_bde_class", "target_estimated_bde", "minimum_estimated_bde",
        "bde_competition_gap", "candidate_site_count", "reaction_competition_class",
        "path_accessibility_class", "local_reactivity_regime",
    ]
    write_csv(output_dir / "predictions.csv", prediction_rows, fields)
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "computational_panel_complete_experimental_validation_pending",
        "target": "ee_percent",
        "catalyst_id": "fe-p7-cl",
        "training": {
            "records_path": str(records_path),
            "historical_substrates": len(historical_rows),
            "excluded_ids": sorted(excluded),
            "feature_set": "rdkit_morgan",
            "stage2p_pose_features_used": False,
        },
        "candidate_panel": {
            "records_path": str(latestage_path),
            "candidate_substrates": len(candidate_rows),
            "candidate_ids": [row.substrate_id for row in candidate_rows],
            "initial_diversity_seed": initial_seed,
            "labels_available": False,
            "experimental_validation": "pending_external_measurement",
        },
        "versions": list(versions),
        "model_diagnostics": model_diagnostics,
        "interpretation": {
            "v0": "structure-only comparator",
            "v4": "structure plus BDE/electronic/reaction-contrast rules",
            "v6": "structure plus BDE/electronic/reaction-contrast/path-accessibility/local-regime rules",
            "prediction_status": "hypotheses for panel prioritization, not measured outcomes",
        },
        "preservation": {
            "existing_latestage_predictions_overwritten": False,
            "existing_rule_versions_overwritten": False,
        },
    }
    write_json(output_dir / "report.json", report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--latestage", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--versions", nargs="+", default=list(DEFAULT_VERSIONS))
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    result = run(arguments.records, arguments.latestage, arguments.output_dir, arguments.versions)
    print(json.dumps({"status": result["status"], "candidate_panel": result["candidate_panel"]}, sort_keys=True))

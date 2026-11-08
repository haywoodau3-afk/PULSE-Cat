#!/usr/bin/env python3
"""Compare frozen rule-based diversity versions in substrate progression.

The acquisition ablation keeps the current RDKit/Morgan/Stage 2p predictor
fixed and changes only the diversity representation.  With
``--prediction-ablation`` the same V0--V6 rule blocks are appended to the
predictor while the acquisition route is held fixed by version.  All routes
select whole substrates and preserve the existing grouped learning-curve
contract.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import random
import sys
import warnings
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import mean_absolute_error


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import rule_based_diversity as rules  # noqa: E402
import scope_progression as baseline  # noqa: E402


SCHEMA_VERSION = "rule-scope-progression-v1"
DEFAULT_SEED = 20260824
DEFAULT_REPLICATES = 50


def write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def route_seed(
    seed: int,
    route: str,
    replicate: int,
    route_index: int,
    version_index: int,
    target_index: int,
) -> int:
    """Build a reproducible seed; random routes are paired across versions."""
    version_offset = 0 if route == "random" else version_index * 10_007
    return seed + replicate * 1009 + route_index * 100_003 + version_offset + target_index * 1_000_003


def numeric_target(rows: Sequence[baseline.ScopeRow], target: str) -> np.ndarray:
    return np.asarray(
        [baseline.outcome_value(row.record, target) if baseline.outcome_value(row.record, target) is not None else np.nan for row in rows],
        dtype=float,
    )


def augmented_matrix(
    base_table: baseline.FeatureTable,
    rule_table: rules.RuleFeatureTable,
    feature_set: str,
    version: str,
    include_rules: bool,
) -> np.ndarray:
    base = base_table.matrix(feature_set)
    if not include_rules or version == "v0":
        return base
    return np.column_stack([base, rule_table.matrix(version, scaled=True)])


def reference_metrics_matrix(
    table: baseline.FeatureTable,
    X: np.ndarray,
    target: str,
    active_indices: Sequence[int],
) -> dict[str, Any]:
    values = np.asarray([baseline.outcome_value(table.rows[index].record, target) for index in active_indices], dtype=object)
    numeric = np.asarray([value if value is not None else np.nan for value in values], dtype=float)
    valid = [position for position, value in enumerate(numeric) if not np.isnan(value)]
    if len(valid) < 3:
        return {"baseline_mae": None, "ridge_loo_mae": None, "elastic_net_loo_mae": None, "tanimoto_knn_loo_mae": None}
    baseline_prediction = float(np.mean(numeric[valid]))
    observed: list[float] = []
    predictions: dict[str, list[float]] = {"ridge": [], "elastic_net": [], "tanimoto_knn": []}
    all_values = np.asarray(
        [baseline.outcome_value(row.record, target) if baseline.outcome_value(row.record, target) is not None else np.nan for row in table.rows],
        dtype=float,
    )
    for position in valid:
        train_positions = [other for other in valid if other != position]
        output = baseline.fit_predict_models(
            X,
            table.fingerprint_matrix,
            [active_indices[item] for item in train_positions],
            [active_indices[position]],
            all_values,
        )
        if not output:
            continue
        observed.append(float(numeric[position]))
        for name in predictions:
            predictions[name].append(float(output[name][0]))
    result = {"baseline_mae": float(np.mean(np.abs(numeric[valid] - baseline_prediction)))}
    for name, values_for_model in predictions.items():
        result[f"{name}_loo_mae"] = float(mean_absolute_error(observed, values_for_model)) if observed else None
    return result


def selection_components(
    base_table: baseline.FeatureTable,
    rule_table: rules.RuleFeatureTable,
    X: np.ndarray,
    target_values: np.ndarray,
    selected: Sequence[int],
    candidates: Sequence[int],
    route: str,
    version: str,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    if version == "v0":
        novelty = baseline.minmax(baseline.novelty_scores(base_table, candidates, selected))
    else:
        novelty = baseline.minmax(rules.rule_novelty_scores(rule_table, candidates, selected, version))
    family_coverage = baseline.family_coverage(base_table, candidates, selected)
    rule_coverage = rules.rule_coverage_scores(rule_table, candidates, selected, version) if version != "v0" else np.zeros(len(candidates), dtype=float)
    coverage = family_coverage if version == "v0" else 0.5 * family_coverage + 0.5 * rule_coverage
    predictions = baseline.fit_predict_models(X, base_table.fingerprint_matrix, selected, candidates, target_values)
    uncertainty = baseline.uncertainty_scores(predictions, novelty)
    predicted_performance = baseline.minmax(predictions.get("ridge", np.zeros(len(candidates), dtype=float)))
    if route == "diversity_first":
        score = 0.8 * novelty + 0.2 * coverage
    elif route == "uncertainty_diversity":
        score = 0.4 * novelty + 0.4 * uncertainty + 0.2 * coverage
    elif route == "performance_first":
        score = 0.5 * predicted_performance + 0.3 * uncertainty + 0.2 * novelty
    else:
        score = np.zeros(len(candidates), dtype=float)
    return score, {
        "diversity_score": novelty,
        "chemical_coverage_score": rule_coverage if version != "v0" else np.zeros(len(candidates), dtype=float),
        "family_coverage_score": family_coverage,
        "coverage_score": coverage,
        "uncertainty_score": uncertainty,
        "predicted_performance_score": predicted_performance,
    }


def evaluate_prefix(
    table: baseline.FeatureTable,
    X: np.ndarray,
    target_values: np.ndarray,
    selected: Sequence[int],
    evaluation_pool: Sequence[int],
    route: str,
    replicate: int,
    n_labeled: int,
    target: str,
) -> list[dict[str, Any]]:
    test = [index for index in evaluation_pool if index not in selected and not np.isnan(target_values[index])]
    train = [index for index in selected if not np.isnan(target_values[index])]
    if len(train) < 2 or not test:
        return []
    predictions = baseline.fit_predict_models(X, table.fingerprint_matrix, train, test, target_values)
    observed = target_values[np.asarray(test, dtype=int)]
    rows = []
    for model_name, predicted in predictions.items():
        row = {
            "schema_version": SCHEMA_VERSION,
            "route": route,
            "replicate": replicate,
            "target": target,
            "n_labeled": n_labeled,
            "model": model_name,
        }
        row.update(baseline.metrics(observed, predicted))
        rows.append(row)
    return rows


def simulate_route(
    base_table: baseline.FeatureTable,
    rule_table: rules.RuleFeatureTable,
    X: np.ndarray,
    target: str,
    active_indices: Sequence[int],
    route: str,
    version: str,
    replicate: int,
    rng: random.Random,
    selection_version: str | None = None,
    selection_X: np.ndarray | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selection_version = version if selection_version is None else selection_version
    selection_X = X if selection_X is None else selection_X
    values = numeric_target(base_table.rows, target)
    pool = list(active_indices)
    seed_route = "random" if route == "random" else "historical_order" if route == "historical_order" else "diversity_first"
    selected = baseline.seed_indices(base_table, pool, seed_route, rng)
    route_name = f"rule_{version}_{route}"
    events: list[dict[str, Any]] = []
    learning: list[dict[str, Any]] = []
    for rank, index in enumerate(selected, start=1):
        events.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route": route_name,
                "version": version,
                "replicate": replicate,
                "target": target,
                "step": rank,
                "selection_phase": "initial_seed",
                "selected_substrate_id": base_table.rows[index].substrate_id,
                "family_id": base_table.rows[index].family_id,
                "pathway_id": rule_table.rows[index].pathway_id,
                "selection_score": None,
                "diversity_score": None,
                "chemical_coverage_score": None,
                "family_coverage_score": None,
                "coverage_score": None,
                "uncertainty_score": None,
                "predicted_performance_score": None,
            }
        )
    learning.extend(evaluate_prefix(base_table, X, values, selected, pool, route_name, replicate, 2, target))
    for step in range(3, len(pool) + 1):
        candidates = [index for index in pool if index not in selected]
        if route == "random":
            chosen = rng.choice(candidates)
            score = 0.0
            components = {name: None for name in ("diversity_score", "chemical_coverage_score", "family_coverage_score", "coverage_score", "uncertainty_score", "predicted_performance_score")}
        elif route == "historical_order":
            chosen = min(candidates, key=lambda index: base_table.rows[index].source_order)
            scores, component_values = selection_components(
                base_table, rule_table, selection_X, values, selected, candidates, "diversity_first", selection_version
            )
            chosen_position = candidates.index(chosen)
            score = float(scores[chosen_position])
            components = {name: float(values_for_name[chosen_position]) for name, values_for_name in component_values.items()}
        else:
            scores, component_values = selection_components(
                base_table, rule_table, selection_X, values, selected, candidates, route, selection_version
            )
            chosen_position = max(range(len(candidates)), key=lambda position: (scores[position], -base_table.rows[candidates[position]].source_order))
            chosen = candidates[chosen_position]
            score = float(scores[chosen_position])
            components = {name: float(values_for_name[chosen_position]) for name, values_for_name in component_values.items()}
        selected.append(chosen)
        events.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route": route_name,
                "version": version,
                "replicate": replicate,
                "target": target,
                "step": step,
                "selection_phase": "sequential",
                "selected_substrate_id": base_table.rows[chosen].substrate_id,
                "family_id": base_table.rows[chosen].family_id,
                "pathway_id": rule_table.rows[chosen].pathway_id,
                "selection_score": score,
                **components,
            }
        )
        learning.extend(evaluate_prefix(base_table, X, values, selected, pool, route_name, replicate, step, target))
    return learning, events


def choose_audit(rows: Sequence[baseline.ScopeRow], fraction: float) -> list[str]:
    return baseline.choose_auto_audit(rows, fraction)


def summarize(rows: Sequence[dict[str, Any]], references: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, int], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["route"]), str(row["model"]), str(row["target"]), int(row["n_labeled"])), []).append(row)
    output = []
    for (route, model, target, count), values in sorted(grouped.items()):
        maes = np.asarray([row["mae"] for row in values if row.get("mae") is not None], dtype=float)
        if not len(maes):
            continue
        reference = references.get(target, {})
        baseline_mae = reference.get("baseline_mae")
        full_mae = reference.get(f"{model}_loo_mae")
        threshold = None if baseline_mae is None or full_mae is None else baseline_mae - 0.9 * (baseline_mae - full_mae)
        output.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route": route,
                "model": model,
                "target": target,
                "n_labeled": count,
                "replicates": len(values),
                "mae_mean": float(np.mean(maes)),
                "mae_std": float(np.std(maes, ddof=1)) if len(maes) > 1 else 0.0,
                "mae_median": float(np.median(maes)),
                "mae_q25": float(np.quantile(maes, 0.25)),
                "mae_q75": float(np.quantile(maes, 0.75)),
                "threshold_90_percent_error_reduction": threshold,
                "threshold_reached": bool(threshold is not None and np.median(maes) <= threshold),
            }
        )
    return output


def summarize_convergence(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["route"]), str(row["model"]), str(row["target"])), []).append(row)
    output: dict[str, Any] = {}
    for (route, model, target), values in sorted(grouped.items()):
        ordered = sorted(values, key=lambda row: int(row["n_labeled"]))
        reached = [row for row in ordered if row.get("threshold_reached")]
        x = np.asarray([float(row["n_labeled"]) for row in ordered], dtype=float)
        y = np.asarray([float(row["mae_median"]) for row in ordered], dtype=float)
        output[f"{target}:{route}:{model}"] = {
            "target": target,
            "route": route,
            "model": model,
            "n90": int(reached[0]["n_labeled"]) if reached else None,
            "auc_mae": float(np.trapezoid(y, x)) if len(ordered) > 1 else None,
            "observed_n_labeled": [int(row["n_labeled"]) for row in ordered],
        }
    return output


def run_rule_analysis(
    records_path: Path,
    stage2p_path: Path | None,
    output_dir: Path,
    catalyst: str | None,
    targets: Sequence[str],
    feature_set: str,
    audit_ids: Sequence[str],
    audit_fraction: float,
    replicates: int,
    seed: int,
    versions: Sequence[str],
    prediction_ablation: bool,
    exclude_ids: Sequence[str] = (),
) -> dict[str, Any]:
    rows = baseline.load_scope_rows(records_path, catalyst)
    excluded = set(exclude_ids)
    rows = [row for row in rows if row.substrate_id not in excluded]
    base_table = baseline.build_feature_table(rows, stage2p_path)
    rule_table = rules.build_rule_feature_table([row.record for row in rows])
    requested_audit = set(audit_ids) | set(choose_audit(rows, audit_fraction))
    audit_indices = [index for index, row in enumerate(rows) if row.substrate_id in requested_audit]
    active_indices = [index for index in range(len(rows)) if index not in audit_indices]
    if len(active_indices) < 4:
        raise ValueError("at least four active substrates are required")
    all_learning: list[dict[str, Any]] = []
    all_events: list[dict[str, Any]] = []
    references: dict[str, dict[str, Any]] = {}
    routes = ("diversity_first", "uncertainty_diversity", "performance_first", "historical_order", "random")
    for version in versions:
        X = augmented_matrix(base_table, rule_table, feature_set, version, prediction_ablation)
        for target in targets:
            target_active = [index for index in active_indices if baseline.outcome_value(rows[index].record, target) is not None]
            if len(target_active) < 4:
                continue
            reference_key = f"{version}:{target}" if prediction_ablation else target
            references[reference_key] = reference_metrics_matrix(base_table, X, target, target_active)
            for route in routes:
                count = replicates if route == "random" else 1
                for replicate in range(count):
                    rng = random.Random(
                        route_seed(
                            seed,
                            route,
                            replicate,
                            routes.index(route),
                            versions.index(version),
                            targets.index(target),
                        )
                    )
                    selection_version = "v0" if prediction_ablation else version
                    selection_X = base_table.matrix(feature_set) if prediction_ablation else X
                    learning, events = simulate_route(
                        base_table,
                        rule_table,
                        X,
                        target,
                        target_active,
                        route,
                        version,
                        replicate,
                        rng,
                        selection_version=selection_version,
                        selection_X=selection_X,
                    )
                    all_learning.extend(learning)
                    all_events.extend(events)
    output_dir.mkdir(parents=True, exist_ok=True)
    serialization_version = versions[-1] if versions else rules.RULE_VERSION
    rules.write_jsonl(
        output_dir / "rule-features.jsonl",
        (row.as_json(version=serialization_version) for row in rule_table.rows),
    )
    write_csv(output_dir / "learning-curve.csv", all_learning)
    write_csv(output_dir / "selection-events.csv", all_events)
    summary_references = references
    summary_rows = []
    for version in versions:
        version_learning = [row for row in all_learning if row["route"].startswith(f"rule_{version}_")]
        version_refs = {target: references.get(f"{version}:{target}", references.get(target, {})) for target in targets}
        summary_rows.extend(summarize(version_learning, version_refs))
    write_csv(output_dir / "learning-curve-summary.csv", summary_rows)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "rule_schema_version": rules.SCHEMA_VERSION,
        "rule_version_set": list(versions),
        "records_path": str(records_path),
        "stage2p_features_path": str(stage2p_path) if stage2p_path else None,
        "catalyst_id": catalyst,
        "target_names": list(targets),
        "feature_set": feature_set,
        "mode": "prediction_ablation" if prediction_ablation else "acquisition_ablation",
        "acquisition_policy": {
            "unit": "whole_substrate",
            "routes": [f"rule_{version}_{route}" for version in versions for route in routes],
            "diversity_first_weights": {"chemical_novelty": 0.8, "coverage": 0.2},
            "uncertainty_diversity_weights": {"chemical_novelty": 0.4, "uncertainty": 0.4, "coverage": 0.2},
            "coverage_definition": "mean of family coverage and rule-category coverage",
            "initial_seed": "same Morgan central-plus-diverse seed for deterministic V0-V6 routes",
            "random_route_replicates": replicates,
        },
        "rule_policy": {
            "quantum_calculation": False,
            "label_derived_parameters": False,
            "electronegativity": "Pauling",
            "version_blocks": {version: list(rules.blocks_for_version(version)) for version in versions},
            "feature_mixture_mode": "explicit_version_specs",
            "shell_distances": list(rules.SHELL_DISTANCES),
            "bde_range_kcal_mol": [70.0, 115.0],
            "flexibility_values": {"free": 1.0, "hindered": 0.5, "conjugated": 0.25, "locked": 0.0},
            "path_distance_primary": rules.PATH_DISTANCE_PRIMARY,
            "path_distance_relaxed": rules.PATH_DISTANCE_RELAXED,
        },
        "scope_counts": {
            "input_records": len(rows),
            "active_records": len(active_indices),
            "locked_audit_records": len(audit_indices),
        },
        "excluded_ids": sorted(excluded),
        "locked_audit_ids": [rows[index].substrate_id for index in audit_indices],
        "references": summary_references,
        "convergence": summarize_convergence(summary_rows),
        "outputs": {
            "rule_features": "rule-features.jsonl",
            "learning_curve": "learning-curve.csv",
            "learning_curve_summary": "learning-curve-summary.csv",
            "selection_events": "selection-events.csv",
        },
    }
    (output_dir / "rule-scope-progression-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def parse_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--stage2p-features", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--catalyst-id")
    parser.add_argument("--target", action="append", choices=["ee_percent", "isolated_yield_percent"])
    parser.add_argument("--feature-set", choices=["rdkit_morgan", "rdkit_morgan_stage2p"], default="rdkit_morgan_stage2p")
    parser.add_argument("--audit-ids", default="")
    parser.add_argument("--audit-fraction", type=float, default=0.0)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--versions", default="v0,v1,v2,v3")
    parser.add_argument("--feature-mixtures", choices=["prefixes", "all"])
    parser.add_argument("--prediction-ablation", action="store_true")
    parser.add_argument("--exclude-ids", default="")
    args = parser.parse_args()
    versions = parse_ids(args.versions)
    if args.feature_mixtures:
        versions = ["v0", *rules.feature_mixture_versions(args.feature_mixtures)]
    invalid = [version for version in versions if not rules.is_valid_version_spec(version)]
    if invalid:
        raise SystemExit(f"unsupported rule versions: {', '.join(invalid)}")
    manifest = run_rule_analysis(
        records_path=args.records,
        stage2p_path=args.stage2p_features,
        output_dir=args.output_dir,
        catalyst=args.catalyst_id,
        targets=args.target or ["ee_percent", "isolated_yield_percent"],
        feature_set=args.feature_set,
        audit_ids=parse_ids(args.audit_ids),
        audit_fraction=args.audit_fraction,
        replicates=args.replicates,
        seed=args.seed,
        versions=versions,
        prediction_ablation=args.prediction_ablation,
        exclude_ids=parse_ids(args.exclude_ids),
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Benchmark V1--V6 feature unions on model-selected learning curves.

Each non-random feature union selects its own progression with the union's
rule novelty, coverage, uncertainty, and Ridge predictor. A paired random
route is retained as a score-free benchmark. Textual mixtures that produce the
same union of rule blocks are evaluated once and expanded in the output with
their equivalent block signature.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
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


SCHEMA_VERSION = "rule-feature-mixture-benchmark-v2"
DEFAULT_SEED = 20260824
DEFAULT_REPLICATES = 10
ROUTES = ("uncertainty_diversity", "random")
TARGETS = ("ee_percent", "isolated_yield_percent")


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def numeric_target(rows: Sequence[baseline.ScopeRow], target: str) -> np.ndarray:
    return np.asarray(
        [baseline.outcome_value(row.record, target) if baseline.outcome_value(row.record, target) is not None else np.nan for row in rows],
        dtype=float,
    )


def feature_specs() -> list[str]:
    return ["v0", *rules.feature_mixture_versions("all")]


def feature_signature(version: str) -> str:
    return "+".join(rules.blocks_for_version(version)) or "none"


def make_feature_matrix(
    base_table: baseline.FeatureTable,
    rule_table: rules.RuleFeatureTable,
    version: str,
    cache: dict[str, np.ndarray],
) -> np.ndarray:
    signature = feature_signature(version)
    if signature not in cache:
        base = base_table.matrix("rdkit_morgan_stage2p")
        cache[signature] = base if version == "v0" else np.column_stack([base, rule_table.matrix(version, scaled=True)])
    return cache[signature]


def paired_seed(seed: int, route: str, target_index: int, replicate: int) -> int:
    route_index = ROUTES.index(route)
    return seed + route_index * 100_003 + target_index * 1_000_003 + replicate * 1009


def selection_order(
    table: baseline.FeatureTable,
    rule_table: rules.RuleFeatureTable,
    target: str,
    active_indices: Sequence[int],
    route: str,
    replicate: int,
    seed: int,
    version: str,
    X: np.ndarray,
) -> list[int]:
    values = numeric_target(table.rows, target)
    rng = random.Random(paired_seed(seed, route, TARGETS.index(target), replicate))
    selected = baseline.seed_indices(table, active_indices, "random" if route == "random" else "diversity_first", rng)
    for _ in range(3, len(active_indices) + 1):
        candidates = [index for index in active_indices if index not in selected]
        if route == "random":
            chosen = rng.choice(candidates)
        else:
            scores, _ = rule_progression.selection_components(
                table,
                rule_table,
                X,
                values,
                selected,
                candidates,
                route,
                version,
            )
            chosen_position = max(
                range(len(candidates)),
                key=lambda position: (scores[position], -table.rows[candidates[position]].source_order),
            )
            chosen = candidates[chosen_position]
        selected.append(chosen)
    return selected


def learning_rows_for_order(
    table: baseline.FeatureTable,
    X: np.ndarray,
    target_values: np.ndarray,
    selected_order: Sequence[int],
    route: str,
    replicate: int,
    target: str,
    version: str,
) -> list[dict[str, Any]]:
    rows = []
    pool = [index for index, value in enumerate(target_values) if not np.isnan(value)]
    for n_labeled in range(2, len(selected_order) + 1):
        selected = list(selected_order[:n_labeled])
        train = [index for index in selected if not np.isnan(target_values[index])]
        test = [index for index in pool if index not in selected]
        if len(train) < 2 or not test:
            continue
        predictions = baseline.fit_predict_models(
            X,
            table.fingerprint_matrix,
            train,
            test,
            target_values,
            include_elastic_net=False,
        )
        observed = target_values[np.asarray(test, dtype=int)]
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "feature_spec": version,
                "block_signature": feature_signature(version),
                "route": route,
                "replicate": replicate,
                "target": target,
                "n_labeled": n_labeled,
                "model": "ridge",
                "mae": baseline.metrics(observed, predictions["ridge"])["mae"],
            }
        )
    return rows


def median_curves(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, int], list[float]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["feature_spec"]), str(row["route"]), str(row["target"]), int(row["n_labeled"]))].append(float(row["mae"]))
    return [
        {
            "feature_spec": key[0],
            "route": key[1],
            "target": key[2],
            "n_labeled": key[3],
            "mae_median": float(np.median(values)),
            "mae_mean": float(np.mean(values)),
            "replicates": len(values),
        }
        for key, values in sorted(grouped.items())
    ]


def curve_metrics(curves: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in curves:
        grouped[(str(row["feature_spec"]), str(row["route"]), str(row["target"]))].append(row)
    output = []
    for (version, route, target), values in sorted(grouped.items()):
        ordered = sorted(values, key=lambda row: int(row["n_labeled"]))
        y = np.asarray([float(row["mae_median"]) for row in ordered], dtype=float)
        x = np.asarray([float(row["n_labeled"]) for row in ordered], dtype=float)
        deltas = np.abs(np.diff(y))
        mean_mae = float(np.mean(y)) if len(y) else float("nan")
        output.append(
            {
                "feature_spec": version,
                "block_signature": feature_signature(version),
                "route": route,
                "target": target,
                "auc_mae_normalized": float(np.trapezoid(y, x) / (x[-1] - x[0])) if len(x) > 1 and x[-1] > x[0] else None,
                "raw_fluctuation": float(np.mean(deltas)) if len(deltas) else 0.0,
                "normalized_fluctuation": float(np.mean(deltas) / mean_mae) if len(deltas) and mean_mae else 0.0,
                "max_jump": float(np.max(deltas)) if len(deltas) else 0.0,
                "n_points": len(ordered),
            }
        )
    return output


def aggregate_metrics(metrics: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        grouped[(str(row["feature_spec"]), str(row["route"]))].append(row)
    output = []
    for (version, route), values in sorted(grouped.items()):
        output.append(
            {
                "feature_spec": version,
                "block_signature": feature_signature(version),
                "route": route,
                "cells": len(values),
                "mean_auc_mae_normalized": float(np.mean([row["auc_mae_normalized"] for row in values])),
                "mean_raw_fluctuation": float(np.mean([row["raw_fluctuation"] for row in values])),
                "mean_normalized_fluctuation": float(np.mean([row["normalized_fluctuation"] for row in values])),
                "max_jump": float(np.max([row["max_jump"] for row in values])),
            }
        )
    return output


def run_benchmark(
    records_path: Path,
    stage2p_path: Path | None,
    output_dir: Path,
    catalyst: str | None,
    audit_ids: Sequence[str],
    audit_fraction: float,
    replicates: int,
    seed: int,
    exclude_ids: Sequence[str],
) -> dict[str, Any]:
    rows = baseline.load_scope_rows(records_path, catalyst)
    excluded = set(exclude_ids)
    rows = [row for row in rows if row.substrate_id not in excluded]
    table = baseline.build_feature_table(rows, stage2p_path)
    rule_table = rules.build_rule_feature_table([row.record for row in rows])
    requested_audit = set(audit_ids) | set(baseline.choose_auto_audit(rows, audit_fraction))
    audit_indices = {index for index, row in enumerate(rows) if row.substrate_id in requested_audit}
    active_indices = [index for index in range(len(rows)) if index not in audit_indices]
    specs = feature_specs()
    by_signature: dict[str, str] = {}
    for version in specs:
        by_signature.setdefault(feature_signature(version), version)
    matrices = {
        signature: make_feature_matrix(table, rule_table, version, {})
        for signature, version in by_signature.items()
    }
    all_rows: list[dict[str, Any]] = []
    all_events: list[dict[str, Any]] = []
    for target in TARGETS:
        values = numeric_target(table.rows, target)
        target_active = [index for index in active_indices if not np.isnan(values[index])]
        for route in ROUTES:
            for signature, matrix in matrices.items():
                representative = by_signature[signature]
                count = replicates if route == "random" else 1
                orders = [
                    selection_order(
                        table,
                        rule_table,
                        target,
                        target_active,
                        route,
                        replicate,
                        seed,
                        representative,
                        matrix,
                    )
                    for replicate in range(count)
                ]
                for replicate, order in enumerate(orders):
                    all_events.extend(
                        {
                            "schema_version": SCHEMA_VERSION,
                            "feature_spec": representative,
                            "block_signature": signature,
                            "route": route,
                            "replicate": replicate,
                            "target": target,
                            "step": step,
                            "selected_substrate_id": table.rows[index].substrate_id,
                        }
                        for step, index in enumerate(order, start=1)
                    )
                    all_rows.extend(
                        learning_rows_for_order(
                            table,
                            matrix,
                            values,
                            order,
                            route,
                            replicate,
                            target,
                            representative,
                        )
                    )
    # Expand one measured curve to every textual mixture with the same block union.
    expanded_rows = []
    for row in all_rows:
        labels = [version for version in specs if feature_signature(version) == row["block_signature"]]
        for version in labels:
            expanded_rows.append({**row, "feature_spec": version})
    curves = median_curves(expanded_rows)
    metrics = curve_metrics(curves)
    aggregates = aggregate_metrics(metrics)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "learning-curve.csv", expanded_rows)
    write_csv(output_dir / "learning-curve-median.csv", curves)
    write_csv(output_dir / "mixture-cell-metrics.csv", metrics)
    write_csv(output_dir / "mixture-summary.csv", aggregates)
    write_csv(output_dir / "selection-events.csv", all_events)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "records_path": str(records_path),
        "stage2p_features_path": str(stage2p_path) if stage2p_path else None,
        "catalyst_id": catalyst,
        "feature_specs": specs,
        "unique_block_signatures": len(matrices),
        "routes": list(ROUTES),
        "targets": list(TARGETS),
        "random_route_replicates": replicates,
        "acquisition_order": {
            "nonrandom": "generated independently for each feature union from that union's rule novelty, coverage, uncertainty, and Ridge predictor",
            "random": "paired score-free benchmark order, generated independently of feature union",
        },
        "scope_counts": {
            "input_records": len(rows),
            "active_records": len(active_indices),
            "locked_audit_records": len(audit_indices),
        },
        "locked_audit_ids": [rows[index].substrate_id for index in sorted(audit_indices)],
        "excluded_ids": sorted(excluded),
        "outputs": {
            "learning_curve": "learning-curve.csv",
            "learning_curve_median": "learning-curve-median.csv",
            "mixture_cell_metrics": "mixture-cell-metrics.csv",
            "mixture_summary": "mixture-summary.csv",
            "selection_events": "selection-events.csv",
        },
    }
    (output_dir / "rule-feature-mixture-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def parse_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--stage2p-features", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--catalyst-id")
    parser.add_argument("--audit-ids", default="")
    parser.add_argument("--audit-fraction", type=float, default=0.20)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--exclude-ids", default="")
    args = parser.parse_args()
    run_benchmark(
        records_path=args.records,
        stage2p_path=args.stage2p_features,
        output_dir=args.output_dir,
        catalyst=args.catalyst_id,
        audit_ids=parse_ids(args.audit_ids),
        audit_fraction=args.audit_fraction,
        replicates=args.replicates,
        seed=args.seed,
        exclude_ids=parse_ids(args.exclude_ids),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

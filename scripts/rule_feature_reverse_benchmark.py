#!/usr/bin/env python3
"""Run a separate worst-first acquisition benchmark for the leading models.

The forward benchmark remains untouched.  This companion run keeps the same
initial diversity-first seed and feature-specific uncertainty-plus-diversity
score, then deliberately chooses the lowest-scoring candidate at every later
step.  It is an adversarial diagnostic, not a proposed acquisition policy.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import rule_based_diversity as rules  # noqa: E402
import rule_feature_mixture_benchmark as forward  # noqa: E402
import rule_scope_progression as rule_progression  # noqa: E402
import scope_progression as baseline  # noqa: E402


SCHEMA_VERSION = "rule-feature-reverse-benchmark-v1"
DEFAULT_SEED = forward.DEFAULT_SEED
TARGETS = forward.TARGETS
LEADING_VERSIONS = ("v4", "v6", "v4+v5")
REVERSE_ROUTE = "reverse_uncertainty_diversity"


def write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def selection_order(
    table: baseline.FeatureTable,
    rule_table: rules.RuleFeatureTable,
    target: str,
    active_indices: Sequence[int],
    version: str,
    replicate: int,
    seed: int,
    X: np.ndarray,
) -> list[int]:
    """Select the standard seed, then the lowest current acquisition score."""

    values = forward.numeric_target(table.rows, target)
    rng = random.Random(forward.paired_seed(seed, "uncertainty_diversity", TARGETS.index(target), replicate))
    selected = baseline.seed_indices(table, active_indices, "diversity_first", rng)
    for _ in range(3, len(active_indices) + 1):
        candidates = [index for index in active_indices if index not in selected]
        scores, _ = rule_progression.selection_components(
            table,
            rule_table,
            X,
            values,
            selected,
            candidates,
            "uncertainty_diversity",
            version,
        )
        chosen_position = min(
            range(len(candidates)),
            key=lambda position: (scores[position], table.rows[candidates[position]].source_order),
        )
        selected.append(candidates[chosen_position])
    return selected


def reverse_learning_rows(
    table: baseline.FeatureTable,
    rule_table: rules.RuleFeatureTable,
    X: np.ndarray,
    target: str,
    active_indices: Sequence[int],
    version: str,
    seed: int,
    replicate: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    values = forward.numeric_target(table.rows, target)
    order = selection_order(table, rule_table, target, active_indices, version, replicate, seed, X)
    events: list[dict[str, Any]] = []
    for step, index in enumerate(order, start=1):
        event = {
            "schema_version": SCHEMA_VERSION,
            "feature_spec": version,
            "block_signature": forward.feature_signature(version),
            "route": REVERSE_ROUTE,
            "replicate": replicate,
            "target": target,
            "step": step,
            "selected_substrate_id": table.rows[index].substrate_id,
        }
        if step >= 3:
            selected = order[: step - 1]
            candidates = [candidate for candidate in active_indices if candidate not in selected]
            scores, components = rule_progression.selection_components(
                table,
                rule_table,
                X,
                values,
                selected,
                candidates,
                "uncertainty_diversity",
                version,
            )
            position = candidates.index(index)
            event["selection_score"] = float(scores[position])
            event.update({name: float(values_for_name[position]) for name, values_for_name in components.items()})
        else:
            event["selection_score"] = None
            event.update(
                {
                    name: None
                    for name in (
                        "diversity_score",
                        "chemical_coverage_score",
                        "family_coverage_score",
                        "coverage_score",
                        "uncertainty_score",
                        "predicted_performance_score",
                    )
                }
            )
        events.append(event)

    learning = forward.learning_rows_for_order(
        table,
        X,
        values,
        order,
        REVERSE_ROUTE,
        replicate,
        target,
        version,
    )
    return learning, events


def run_benchmark(
    records_path: Path,
    stage2p_path: Path | None,
    output_dir: Path,
    catalyst: str | None,
    audit_ids: Sequence[str],
    audit_fraction: float,
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
    cache: dict[str, np.ndarray] = {}
    matrices = {
        version: forward.make_feature_matrix(table, rule_table, version, cache)
        for version in LEADING_VERSIONS
    }

    all_rows: list[dict[str, Any]] = []
    all_events: list[dict[str, Any]] = []
    for target in TARGETS:
        values = forward.numeric_target(table.rows, target)
        target_active = [index for index in active_indices if not np.isnan(values[index])]
        for version, matrix in matrices.items():
            learning, events = reverse_learning_rows(
                table,
                rule_table,
                matrix,
                target,
                target_active,
                version,
                seed,
                0,
            )
            all_rows.extend(learning)
            all_events.extend(events)

    curves = forward.median_curves(all_rows)
    metrics = forward.curve_metrics(curves)
    aggregates = forward.aggregate_metrics(metrics)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "learning-curve.csv", all_rows)
    write_csv(output_dir / "learning-curve-median.csv", curves)
    write_csv(output_dir / "mixture-cell-metrics.csv", metrics)
    write_csv(output_dir / "mixture-summary.csv", aggregates)
    write_csv(output_dir / "selection-events.csv", all_events)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "records_path": str(records_path),
        "stage2p_features_path": str(stage2p_path) if stage2p_path else None,
        "catalyst_id": catalyst,
        "feature_specs": list(LEADING_VERSIONS),
        "route": REVERSE_ROUTE,
        "selection_rule": "same uncertainty_plus_diversity score as standard route, but choose the minimum score after the shared initial seed",
        "randomized": False,
        "seed": seed,
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
    (output_dir / "rule-feature-reverse-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
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
        seed=args.seed,
        exclude_ids=parse_ids(args.exclude_ids),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

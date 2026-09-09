#!/usr/bin/env python3
"""Compute paired scaffold-bootstrap intervals for a scaffold replay report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _group_metrics(rows: list[dict], key: str) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for row in rows:
        grouped.setdefault(row["heldout_scaffold"], []).append(abs(float(row["predictions"][key]) - float(row["observed"])))
    return {group: float(np.mean(values)) for group, values in grouped.items()}


def bootstrap_report(report: dict, *, replicates: int = 2000, seed: int = 20260901) -> dict:
    rows = list(report.get("rows", []))
    if not rows:
        raise ValueError("scaffold report has no prediction rows")
    target_key = "target_only"
    source_key = "p7" if report.get("source_domain") == "fe-p7-cl" else "cmcpor"
    grouped = {"target_only": _group_metrics(rows, target_key), "active_source": _group_metrics(rows, source_key), "combined": _group_metrics(rows, "combined")}
    guarded: dict[str, list[float]] = {}
    for row in rows:
        guarded.setdefault(row["heldout_scaffold"], []).append(float(row["ensemble_absolute_error"]))
    grouped["guarded"] = {group: float(np.mean(values)) for group, values in guarded.items()}
    groups = sorted(grouped["target_only"])
    rng = np.random.default_rng(seed)
    samples = rng.integers(0, len(groups), size=(replicates, len(groups)))
    estimates: dict[str, np.ndarray] = {}
    for metric, values in grouped.items():
        array = np.asarray([values[group] for group in groups], dtype=float)
        estimates[metric] = np.mean(array[samples], axis=1)
    deltas = {
        "active_source_minus_target": estimates["active_source"] - estimates["target_only"],
        "combined_minus_target": estimates["combined"] - estimates["target_only"],
        "guarded_minus_target": estimates["guarded"] - estimates["target_only"],
    }

    def interval(values: np.ndarray) -> dict[str, float]:
        return {"mean": float(np.mean(values)), "lower_2.5": float(np.quantile(values, 0.025)), "upper_97.5": float(np.quantile(values, 0.975))}

    return {
        "schema_version": "pptl-scaffold-bootstrap-v1",
        "source_domain": report.get("source_domain"),
        "target_domain": report.get("target_domain"),
        "target": report.get("target"),
        "feature_arm": report.get("feature_arm"),
        "scaffold_count": len(groups),
        "replicates": replicates,
        "seed": seed,
        "mae_intervals": {metric: interval(values) for metric, values in estimates.items()},
        "delta_intervals": {metric: interval(values) for metric, values in deltas.items()},
        "policy": "paired resampling of held-out scaffolds; all prefixes within a sampled scaffold move together",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260901)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = bootstrap_report(json.loads(args.report.read_text(encoding="utf-8")), replicates=args.replicates, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["delta_intervals"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

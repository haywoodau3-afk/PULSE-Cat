#!/usr/bin/env python3
"""Paired scaffold bootstrap for incremental P3/P4 improvement over B5."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def bootstrap(pose_report: dict, baseline_report: dict, *, replicates: int = 2000, seed: int = 20260901) -> dict:
    base = {(r["heldout_scaffold"], r["prefix_size"], r["test_substrate_id"]): r for r in baseline_report.get("rows", [])}
    paired = []
    for row in pose_report.get("rows", []):
        key = (row["heldout_scaffold"], row["prefix_size"], row["test_substrate_id"])
        if key not in base:
            continue
        baseline = base[key]
        paired.append({
            "scaffold": row["heldout_scaffold"],
            "target_delta": abs(float(row["predictions"]["target_only"]) - float(row["observed"])) - abs(float(baseline["predictions"]["target_only"]) - float(baseline["observed"])),
            "guarded_delta": float(row["ensemble_absolute_error"]) - float(baseline["ensemble_absolute_error"]),
        })
    if not paired:
        raise ValueError("pose and baseline reports have no matched scaffold/prefix/substrate rows")
    scaffolds = sorted({row["scaffold"] for row in paired})
    grouped = {metric: {scaffold: float(np.mean([row[metric] for row in paired if row["scaffold"] == scaffold])) for scaffold in scaffolds} for metric in ("target_delta", "guarded_delta")}
    rng = np.random.default_rng(seed)
    samples = rng.integers(0, len(scaffolds), size=(replicates, len(scaffolds)))
    intervals = {}
    for metric, values in grouped.items():
        array = np.asarray([values[scaffold] for scaffold in scaffolds], dtype=float)
        draws = np.mean(array[samples], axis=1)
        intervals[metric] = {"mean": float(np.mean(draws)), "lower_2.5": float(np.quantile(draws, 0.025)), "upper_97.5": float(np.quantile(draws, 0.975))}
    return {"schema_version": "pptl-pose-incremental-bootstrap-v1", "pose_arm": pose_report.get("feature_arm"), "baseline_arm": baseline_report.get("feature_arm"), "source_domain": pose_report.get("source_domain"), "target_domain": pose_report.get("target_domain"), "target": pose_report.get("target"), "paired_rows": len(paired), "scaffold_count": len(scaffolds), "replicates": replicates, "seed": seed, "delta_intervals": intervals, "policy": "paired resampling of held-out scaffolds with matched prefix and substrate keys; negative delta favors pose"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pose-report", type=Path, required=True)
    parser.add_argument("--baseline-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=2000)
    args = parser.parse_args()
    report = bootstrap(json.loads(args.pose_report.read_text(encoding="utf-8")), json.loads(args.baseline_report.read_text(encoding="utf-8")), replicates=args.replicates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["delta_intervals"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Paired bootstrap comparing pose route AUC/MAE against matched B5 routes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def bootstrap(pose: dict, baseline: dict, *, replicates: int = 2000, seed: int = 20260901) -> dict:
    outputs = {}
    for direction, pose_dir in pose.get("directions", {}).items():
        base_dir = baseline.get("directions", {}).get(direction)
        if base_dir is None:
            raise ValueError(f"missing baseline direction {direction}")
        base_by_seed = {int(row["seed"]): row for row in base_dir.get("replicates", [])}
        deltas = []
        for row in pose_dir.get("replicates", []):
            baseline_row = base_by_seed.get(int(row["seed"]))
            if baseline_row is None:
                continue
            deltas.append({
                "mae": float(row["guarded"]["mae"]) - float(baseline_row["guarded"]["mae"]),
                "auc": float(row["guarded"]["auc_mae"]) - float(baseline_row["guarded"]["auc_mae"]),
            })
        if not deltas:
            raise ValueError(f"no matched route seeds for {direction}")
        rng = np.random.default_rng(seed)
        sample = rng.integers(0, len(deltas), size=(replicates, len(deltas)))
        result = {}
        for metric in ("mae", "auc"):
            values = np.asarray([item[metric] for item in deltas], dtype=float)
            draws = np.mean(values[sample], axis=1)
            result[f"{metric}_delta_pose_minus_b5"] = {"mean": float(np.mean(draws)), "lower_2.5": float(np.quantile(draws, 0.025)), "upper_97.5": float(np.quantile(draws, 0.975))}
        outputs[direction] = {"route_count": len(deltas), "intervals": result}
    return {"schema_version": "pptl-route-incremental-bootstrap-v1", "pose_arm": pose.get("feature_arm"), "baseline_arm": baseline.get("feature_arm"), "target": pose.get("target"), "replicates": replicates, "seed": seed, "directions": outputs, "policy": "matched route seeds; negative delta favors pose"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pose-report", type=Path, required=True)
    parser.add_argument("--baseline-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = bootstrap(json.loads(args.pose_report.read_text(encoding="utf-8")), json.loads(args.baseline_report.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v["intervals"] for k, v in report["directions"].items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

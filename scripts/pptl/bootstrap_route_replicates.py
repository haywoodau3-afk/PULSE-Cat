#!/usr/bin/env python3
"""Summarize paired uncertainty across random-route replicates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def bootstrap_direction(direction: dict, *, replicates: int = 2000, seed: int = 20260901) -> dict:
    rows = direction.get("replicates", [])
    if not rows:
        raise ValueError("route report contains no replicates")
    target_mae = np.asarray([row["target_only"]["mae"] for row in rows], dtype=float)
    guarded_mae = np.asarray([row["guarded"]["mae"] for row in rows], dtype=float)
    target_auc = np.asarray([row["target_only"]["auc_mae"] for row in rows], dtype=float)
    guarded_auc = np.asarray([row["guarded"]["auc_mae"] for row in rows], dtype=float)
    rng = np.random.default_rng(seed)
    sample = rng.integers(0, len(rows), size=(replicates, len(rows)))
    values = {
        "target_mae": np.mean(target_mae[sample], axis=1),
        "guarded_mae": np.mean(guarded_mae[sample], axis=1),
        "target_auc_mae": np.mean(target_auc[sample], axis=1),
        "guarded_auc_mae": np.mean(guarded_auc[sample], axis=1),
    }
    values["mae_delta_guarded_minus_target"] = values["guarded_mae"] - values["target_mae"]
    values["auc_delta_guarded_minus_target"] = values["guarded_auc_mae"] - values["target_auc_mae"]

    def interval(array: np.ndarray) -> dict[str, float]:
        return {"mean": float(np.mean(array)), "lower_2.5": float(np.quantile(array, 0.025)), "upper_97.5": float(np.quantile(array, 0.975))}

    return {
        "source_domain": direction.get("source_domain"),
        "target_domain": direction.get("target_domain"),
        "target": direction.get("target"),
        "feature_arm": direction.get("feature_arm"),
        "route_count": len(rows),
        "bootstrap_replicates": replicates,
        "seed": seed,
        "intervals": {key: interval(value) for key, value in values.items()},
        "policy": "paired bootstrap over complete random-route replicates",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260901)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    result = {
        "schema_version": "pptl-route-bootstrap-v1",
        "target": report.get("target"),
        "feature_arm": report.get("feature_arm"),
        "directions": {
            name: bootstrap_direction(direction, replicates=args.replicates, seed=args.seed)
            for name, direction in report.get("directions", {}).items()
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({name: value["intervals"]["auc_delta_guarded_minus_target"] for name, value in result["directions"].items()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

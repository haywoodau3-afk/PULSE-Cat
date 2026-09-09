#!/usr/bin/env python3
"""Run the fixed-prefix feature/pose ablation on a target replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import FEATURE_ARMS, curve_metrics, load_reaction_rows, prediction_metrics, run_fixed_prefix


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-records", type=Path, required=True)
    parser.add_argument("--target-records", type=Path, required=True)
    parser.add_argument("--source-catalyst", action="append", required=True)
    parser.add_argument("--target-catalyst", required=True)
    parser.add_argument("--source-stage2p", type=Path)
    parser.add_argument("--target-stage2p", type=Path)
    parser.add_argument("--target", choices=("ee_percent", "isolated_yield_percent"), default="ee_percent")
    parser.add_argument("--arms", default="B1,B2,B3,B4,B5,P0,P1,P2")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = []
    for catalyst in args.source_catalyst:
        source.extend(load_reaction_rows(args.source_records, catalyst=catalyst, target=args.target, include_unlabelled=False, pose_features_path=args.source_stage2p))
    target = load_reaction_rows(args.target_records, catalyst=args.target_catalyst, target=args.target, include_unlabelled=True, pose_features_path=args.target_stage2p)
    results = {}
    for arm in [value.strip() for value in args.arms.split(",") if value.strip()]:
        if arm not in FEATURE_ARMS:
            raise ValueError(f"unknown feature arm: {arm}")
        rows = run_fixed_prefix(source, target, target_name=args.target, arm=arm)
        results[arm] = {
            "feature_arm": arm,
            "target": args.target,
            "target_only": prediction_metrics(rows, "target_only"),
            "guarded_ensemble": curve_metrics(rows),
            "prefix_rows": rows,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({arm: {"target_only": value["target_only"], "guarded_ensemble": value["guarded_ensemble"]} for arm, value in results.items()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

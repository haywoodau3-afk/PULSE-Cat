#!/usr/bin/env python3
"""Run the same reciprocal replay across a frozen feature-arm ladder."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_bidirectional import run_bidirectional


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p7-records", type=Path, required=True)
    parser.add_argument("--cmcpor-records", type=Path, required=True)
    parser.add_argument("--p7-stage2p", type=Path)
    parser.add_argument("--cmcpor-stage2p", type=Path)
    parser.add_argument("--p7-catalyst-features", type=Path)
    parser.add_argument("--cmcpor-catalyst-features", type=Path)
    parser.add_argument("--target", choices=("ee_percent", "isolated_yield_percent"), default="ee_percent")
    parser.add_argument("--arms", default="B1,B2,B3,B4,B5,P0,P1,P2")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results: dict[str, dict] = {}
    for arm in [value.strip() for value in args.arms.split(",") if value.strip()]:
        report = run_bidirectional(
            args.p7_records,
            args.cmcpor_records,
            p7_stage2p=args.p7_stage2p,
            cmcpor_stage2p=args.cmcpor_stage2p,
            p7_catalyst_features=args.p7_catalyst_features,
            cmcpor_catalyst_features=args.cmcpor_catalyst_features,
            target=args.target,
            arm=arm,
        )
        results[arm] = report
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"schema_version": "pptl-bidirectional-matrix-v1", "target": args.target, "arms": results}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {}
    for arm, report in results.items():
        summary[arm] = {}
        for direction, values in report["directions"].items():
            guarded = sum(float(row["ensemble_absolute_error"]) for row in values["rows"]) / len(values["rows"])
            summary[arm][direction] = {"target_only_mae": values["target_only"]["mae"], "guarded_mae": guarded, "n": len(values["rows"])}
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

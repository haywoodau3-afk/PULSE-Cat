#!/usr/bin/env python3
"""Run a fixed-prefix PPTL replay for one endpoint and feature arm."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import load_reaction_rows, run_fixed_prefix, curve_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="combined source reaction JSONL")
    parser.add_argument("--p7-records", type=Path, help="P7 source reaction JSONL")
    parser.add_argument("--cmcpor-records", type=Path, help="CMC-Por source reaction JSONL")
    parser.add_argument("--p7-stage2p", type=Path)
    parser.add_argument("--cmcpor-stage2p", type=Path)
    parser.add_argument("--target-stage2p", type=Path)
    parser.add_argument("--target-records", type=Path, required=True, help="label-masked target reaction JSONL")
    parser.add_argument("--source-catalyst", action="append", default=[])
    parser.add_argument("--target-catalyst", required=True)
    parser.add_argument("--target", dest="target_name", choices=("ee_percent", "isolated_yield_percent"), default="ee_percent")
    parser.add_argument("--feature-arm", choices=sorted(__import__("core").FEATURE_ARMS), default="B5")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_rows: list = []
    source_domains = {}
    if args.p7_records:
        source_domains["p7"] = load_reaction_rows(args.p7_records, catalyst="fe-p7-cl", target=args.target_name, include_unlabelled=False, pose_features_path=args.p7_stage2p)
        source_rows.extend(source_domains["p7"])
    if args.cmcpor_records:
        source_domains["cmcpor"] = load_reaction_rows(args.cmcpor_records, catalyst="cmcpor-fecl", target=args.target_name, include_unlabelled=False, pose_features_path=args.cmcpor_stage2p)
        source_rows.extend(source_domains["cmcpor"])
    if args.source:
        if not args.source_catalyst:
            raise ValueError("--source-catalyst is required with --source")
        for catalyst in args.source_catalyst:
            source_rows.extend(load_reaction_rows(args.source, catalyst=catalyst, target=args.target_name, include_unlabelled=False))
    if not source_rows:
        raise ValueError("provide --source or one of --p7-records/--cmcpor-records")
    target_rows = load_reaction_rows(args.target_records, catalyst=args.target_catalyst, target=args.target_name, include_unlabelled=True, pose_features_path=args.target_stage2p)
    results = run_fixed_prefix(source_rows, target_rows, target_name=args.target_name, arm=args.feature_arm, source_domains=source_domains or None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    summary = curve_metrics(results)
    print(json.dumps({"output": str(args.output), "feature_arm": args.feature_arm, "target": args.target_name, **summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a manifest for the frozen PPTL feature ladder."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import FEATURE_ARMS, build_feature_matrix, load_reaction_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--catalyst", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arms", default="B0,B1,B2,B3,B4,B5,P0,P1,P2,P3,P4")
    parser.add_argument("--pathway", choices=("aryl", "sulfonyl", "all"), default="all")
    args = parser.parse_args()
    pathway = None if args.pathway == "all" else args.pathway
    rows = load_reaction_rows(args.records, catalyst=args.catalyst, pathway=pathway)
    arms = [value.strip() for value in args.arms.split(",") if value.strip()]
    manifest = {"schema_version": "pptl-feature-arm-manifest-v1", "records": str(args.records), "catalyst": args.catalyst, "row_count": len(rows), "arms": {}}
    for arm in arms:
        if arm not in FEATURE_ARMS:
            raise ValueError(f"unknown feature arm: {arm}")
        try:
            matrix, names = build_feature_matrix(rows, arm)
            manifest["arms"][arm] = {"status": "valid", "rows": int(matrix.shape[0]), "features": int(matrix.shape[1]), "feature_names": names}
        except ValueError as exc:
            manifest["arms"][arm] = {"status": "blocked", "reason": str(exc)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

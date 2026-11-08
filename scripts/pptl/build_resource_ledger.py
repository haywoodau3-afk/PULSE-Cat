#!/usr/bin/env python3
"""Measure reproducible feature-generation and artifact resource costs."""

from __future__ import annotations

import argparse
import json
import resource
import time
import platform
from pathlib import Path

from core import build_feature_matrix, load_reaction_rows


def _measure(rows, arm: str) -> dict[str, object]:
    start = time.perf_counter()
    matrix, names = build_feature_matrix(rows, arm)
    elapsed = time.perf_counter() - start
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_bytes = int(rss if platform.system() == "Darwin" else rss * 1024)
    return {"rows": len(rows), "features": int(matrix.shape[1]), "seconds": elapsed, "peak_rss_bytes": rss_bytes, "arm": arm}


def build_ledger(p7_records: Path, cmcpor_records: Path, *, p7_stage2p: Path | None = None, cmcpor_stage2p: Path | None = None, p7_catalyst_features: Path | None = None, cmcpor_catalyst_features: Path | None = None, artifacts_root: Path | None = None) -> dict:
    p7 = load_reaction_rows(p7_records, catalyst="fe-p7-cl", include_unlabelled=True, pose_features_path=p7_stage2p, catalyst_features_path=p7_catalyst_features)
    cmc = load_reaction_rows(cmcpor_records, catalyst="cmcpor-fecl", include_unlabelled=True, pose_features_path=cmcpor_stage2p, catalyst_features_path=cmcpor_catalyst_features)
    cmc = [row for row in cmc if row.family_id == "angew-aryl-c-h-amination"]
    result = {"schema_version": "pptl-resource-ledger-v1", "domains": {}, "artifacts": {}}
    for domain, rows in (("p7", p7), ("cmcpor_aryl", cmc)):
        result["domains"][domain] = {arm: _measure(rows, arm) for arm in ("B1", "B5", "P0", "P2", "P3", "P4")}
    if artifacts_root and artifacts_root.exists():
        for path in sorted(artifacts_root.rglob("*")):
            if path.is_file():
                result["artifacts"][str(path.relative_to(artifacts_root))] = path.stat().st_size
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p7-records", type=Path, required=True)
    parser.add_argument("--cmcpor-records", type=Path, required=True)
    parser.add_argument("--p7-stage2p", type=Path)
    parser.add_argument("--cmcpor-stage2p", type=Path)
    parser.add_argument("--p7-catalyst-features", type=Path)
    parser.add_argument("--cmcpor-catalyst-features", type=Path)
    parser.add_argument("--artifacts-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_ledger(args.p7_records, args.cmcpor_records, p7_stage2p=args.p7_stage2p, cmcpor_stage2p=args.cmcpor_stage2p, p7_catalyst_features=args.p7_catalyst_features, cmcpor_catalyst_features=args.cmcpor_catalyst_features, artifacts_root=args.artifacts_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({domain: {arm: {"seconds": value["seconds"], "features": value["features"]} for arm, value in arms.items()} for domain, arms in result["domains"].items()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

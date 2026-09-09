#!/usr/bin/env python3
"""Generate label-independent Stage 2p features for records without an EE label."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from stage2p_representation import generate_substrate_feature_row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--stage1-report-dir", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--substrate-id", action="append", required=True)
    args = parser.parse_args()
    records = {row["substrate_id"]: row for row in (json.loads(line) for line in args.records.read_text(encoding="utf-8").splitlines() if line.strip())}
    existing = {row["substrate_id"]: row for row in (json.loads(line) for line in args.features.read_text(encoding="utf-8").splitlines() if line.strip())}
    with tempfile.TemporaryDirectory(prefix="stage2p-missing-") as temporary:
        temporary_dir = Path(temporary)
        for substrate_id in args.substrate_id:
            if substrate_id not in records:
                raise ValueError(f"unknown substrate ID: {substrate_id}")
            reports = sorted(args.stage1_report_dir.glob(f"stage-1-smoke-{substrate_id}.json"))
            if len(reports) != 1:
                raise ValueError(f"expected one Stage 1 report for {substrate_id}, found {len(reports)}")
            report = json.loads(reports[0].read_text(encoding="utf-8"))
            existing[substrate_id] = generate_substrate_feature_row(records[substrate_id], report, temporary_dir)
    args.features.write_text("".join(json.dumps(existing[key], sort_keys=True) + "\n" for key in sorted(existing)), encoding="utf-8")
    print(json.dumps({"generated": args.substrate_id, "total_rows": len(existing)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Fail-closed gate for revealing sealed prospective ee outcomes."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = list(csv.DictReader(args.panel.open(encoding="utf-8")))
    missing = [r.get("candidate_id", "unknown") for r in rows if not r.get("outcome_ee", "").strip()]
    if missing:
        print(json.dumps({"status": "blocked", "reason": "outcomes_missing", "missing_candidate_ids": missing}, indent=2))
        return 2
    invalid = []
    for r in rows:
        try:
            value = float(r["outcome_ee"])
            if not 0 <= value <= 100:
                invalid.append(r["candidate_id"])
        except ValueError:
            invalid.append(r["candidate_id"])
    if invalid:
        print(json.dumps({"status": "blocked", "reason": "invalid_ee_values", "candidate_ids": invalid}, indent=2))
        return 2
    for r in rows:
        r["outcome_revealed"] = "true"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"status": "ready_for_refit", "revealed_count": len(rows), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate ordering and completeness of the prospective closed-loop ledger."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def truth(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "complete", "passed", "received"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    errors: list[str] = []
    rows = list(csv.DictReader(args.input.open(encoding="utf-8")))
    for row in rows:
        cid = row.get("candidate_id", "unknown")
        if not row.get("universe_hash", "").strip():
            errors.append(f"{cid}:universe_hash_missing")
        if truth(row.get("outcome_revealed", "")) and not truth(row.get("test_status", "")):
            errors.append(f"{cid}:outcome_revealed_before_test")
        if truth(row.get("refit_status", "")) and not truth(row.get("outcome_revealed", "")):
            errors.append(f"{cid}:refit_before_outcome_reveal")
        if truth(row.get("material_status", "")) and not truth(row.get("safety_status", "")):
            errors.append(f"{cid}:material_before_safety_review")
    print(f"checked {len(rows)} ledger rows")
    if errors:
        for error in errors:
            print(error)
        return 2
    print("closed-loop ordering valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

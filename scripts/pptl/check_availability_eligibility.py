"""Apply the deterministic availability/route/safety eligibility rule."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with args.input.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            grouped[row["candidate_id"]].append(row)
    output = []
    for candidate_id, records in sorted(grouped.items()):
        suppliers = {r.get("supplier", "").strip() for r in records if r.get("supplier", "").strip()}
        levels = {r.get("evidence_level", "").strip() for r in records}
        exact_identity = all(r.get("identity_match", "").lower() == "true" for r in records)
        route_ok = all(r.get("route_enabled", "").lower() == "true" for r in records)
        safety_ok = all(r.get("safety_reviewer", "").strip() for r in records)
        availability_ok = bool(levels & {"E0", "E1"}) or ("E2" in levels and len(suppliers) >= 2)
        eligible = availability_ok and exact_identity and route_ok and safety_ok
        reasons = []
        if not availability_ok:
            reasons.append("insufficient_availability_evidence")
        if not exact_identity:
            reasons.append("identity_not_confirmed")
        if not route_ok:
            reasons.append("route_not_accepted")
        if not safety_ok:
            reasons.append("safety_review_missing")
        output.append({"candidate_id": candidate_id, "supplier_count": len(suppliers), "evidence_levels": ";".join(sorted(levels)), "experimentally_eligible": str(eligible).lower(), "reasons": ";".join(reasons)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]) if output else ["candidate_id", "supplier_count", "evidence_levels", "experimentally_eligible", "reasons"])
        writer.writeheader()
        writer.writerows(output)
    print(f"checked {len(output)} candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

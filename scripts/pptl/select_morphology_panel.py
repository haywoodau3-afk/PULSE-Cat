"""Select a deterministic balanced morphology panel."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=16)
    args = parser.parse_args()
    rows = list(csv.DictReader(args.input.open(encoding="utf-8")))
    families = sorted({r["morphology_family"] for r in rows})
    selected = []
    for offset in range(args.size):
        family = families[offset % len(families)]
        candidates = [r for r in rows if r["morphology_family"] == family and r not in selected]
        if candidates:
            selected.append(candidates[0])
    for rank, row in enumerate(selected, 1):
        row["panel_rank"] = str(rank)
        row["selection_status"] = "morphology_balanced_pending_ee_scoring"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        fields = list(selected[0]) if selected else ["candidate_id", "morphology_family"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(selected)
    print(f"selected {len(selected)} candidates across {len(families)} morphology families")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Select top predicted-ee candidates under a fixed acquisition budget."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--enumeration", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--size", type=int, default=16)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, path in (("generator", args.generator), ("enumeration", args.enumeration)):
        rows = [r for r in csv.DictReader(path.open(encoding="utf-8")) if r.get("contract_valid") == "true" and r.get("ad_status") == "in_domain"]
        rows.sort(key=lambda r: (-float(r["ee_prediction_development"]), r.get("canonical_smiles", "")))
        chosen = rows[: args.size]
        for rank, row in enumerate(chosen, 1):
            row["acquisition_rank"] = str(rank)
            row["acquisition_objective"] = "predicted_ee_descending"
        output = args.output_dir / f"{name}-ee-aware-panel.csv"
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(chosen[0]) if chosen else ["candidate_id"])
            writer.writeheader(); writer.writerows(chosen)
        values = [float(r["ee_prediction_development"]) for r in chosen]
        summary[name] = {"eligible_pool": len(rows), "selected": len(chosen), "mean_predicted_ee": sum(values) / len(values) if values else None, "min_selected": min(values) if values else None, "max_selected": max(values) if values else None, "panel": str(output)}
    (args.output_dir / "ee-aware-acquisition-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

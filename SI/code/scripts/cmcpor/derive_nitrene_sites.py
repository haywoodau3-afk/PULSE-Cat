#!/usr/bin/env python3
"""Build cmcpor-specific aryl nitrene and C-H-site substrate records.

The source bundle is deliberately kept inside the cmcpor namespace.  This
script does not read the P7 data tree at runtime; the one-time source curation
file is the auditable boundary for the Angew scope workbook.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "data/expansion/catalyst_rerun/cmcpor/source-structures.jsonl"
DEFAULT_OUTPUT = ROOT / "data/expansion/catalyst_rerun/cmcpor/substrates.jsonl"
DEFAULT_REPORT = ROOT / "data/expansion/catalyst_rerun/cmcpor/derived-nitrene-sites.csv"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(value)
    return rows


def build_record(row: dict[str, Any]) -> dict[str, Any]:
    reported = row["reported_reactive_site"]
    candidates = row["candidate_sites"]
    record = {
        "compound_id": f"angew-cmp-{row['paper_substrate_id']}",
        "paper_substrate_id": row["paper_substrate_id"],
        "pathway_id": "aryl",
        "family_id": row["family_id"],
        "azide_smiles": row["azide_smiles"],
        "nitrene_smiles": row["nitrene_smiles"],
        "atom_mapped_substrate_smiles": row["atom_mapped_substrate_smiles"],
        "product_smiles": row.get("product_smiles"),
        "reported_reactive_site_atom_map_id": reported["atom_map_id"],
        "candidate_site_atom_map_ids": [site["atom_map_id"] for site in candidates],
        "reported_reactive_site": reported,
        "candidate_sites": candidates,
        "site_derivation": {
            "method": "product_connectivity_inference",
            "status": "derived_not_product_atom_mapped",
            "note": (
                "The aryl products are 2-substituted indolines; the reported C-H "
                "site is the carbon that forms the new intramolecular C-N bond. "
                "Product atom mapping remains a required review step."
            ),
        },
        "source": row["source"],
    }
    return record


def write_report(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "paper_substrate_id",
        "nitrene_smiles",
        "reported_atom_map_id",
        "reported_site_type",
        "reported_hydrogen_count",
        "candidate_atom_map_ids",
        "assignment_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            site = record["reported_reactive_site"]
            writer.writerow(
                {
                    "paper_substrate_id": record["paper_substrate_id"],
                    "nitrene_smiles": record["nitrene_smiles"],
                    "reported_atom_map_id": site["atom_map_id"],
                    "reported_site_type": site.get("site_type", ""),
                    "reported_hydrogen_count": site.get("hydrogen_count", ""),
                    "candidate_atom_map_ids": ",".join(
                        str(value) for value in record["candidate_site_atom_map_ids"]
                    ),
                    "assignment_status": record["site_derivation"]["status"],
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    rows = load_jsonl(args.source)
    records = [build_record(row) for row in rows]
    records.sort(key=lambda row: row["paper_substrate_id"])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    write_report(args.report, records)
    print(json.dumps({"status": "complete", "record_count": len(records), "output": str(args.output), "report": str(args.report)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

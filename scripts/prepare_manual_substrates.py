#!/usr/bin/env python3
"""Extract manual JACS azide SMILES and derive conservative nitrene SMILES."""

from __future__ import annotations

import csv
from datetime import timedelta
from pathlib import Path

from numbers_parser import Document


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "substrate_manual_1.numbers"
OUTCOMES = ROOT / "data/jacs_2025/scope-outcomes.csv"
OUTPUT = ROOT / "data/jacs_2025/manual-substrates.csv"
PREFIX_AZIDE = "N#N=N"
SUFFIX_AZIDE = "N=N#N"


def to_nitrene(smiles: str) -> tuple[str, str]:
    """Keep the aryl-bound azide N and remove the terminal N2 fragment."""
    prefix_matches = smiles.count(PREFIX_AZIDE)
    suffix_matches = smiles.count(SUFFIX_AZIDE)

    if prefix_matches + suffix_matches != 1:
        raise ValueError(f"Expected one terminal azide in {smiles!r}")
    if prefix_matches:
        return smiles.replace(PREFIX_AZIDE, "[N]", 1), "prefix"
    if suffix_matches:
        return smiles.replace(SUFFIX_AZIDE, "[N]", 1), "suffix"
    raise ValueError(f"Expected a supported azide fragment in {smiles!r}")


def raw_entry(value: object) -> str:
    if isinstance(value, timedelta):
        return "Numbers auto-coerced entry label"
    return str(value) if value is not None else ""


def main() -> None:
    outcomes = list(csv.DictReader(OUTCOMES.open(encoding="utf-8", newline="")))
    if len(outcomes) != 41:
        raise ValueError(f"Expected 41 scope outcomes, found {len(outcomes)}")

    workbook = Document(WORKBOOK)
    table = workbook.sheets[0].tables[0]
    rows = table.rows(values_only=True)[1:]
    populated = [(entry, smiles) for entry, smiles, *_ in rows if smiles is not None]
    if len(populated) != len(outcomes):
        raise ValueError(f"Expected {len(outcomes)} populated SMILES rows, found {len(populated)}")

    output_rows = []
    for manual_row, ((entry, smiles), outcome) in enumerate(zip(populated, outcomes), start=1):
        if not isinstance(smiles, str):
            raise ValueError(f"Manual row {manual_row} does not contain a SMILES string")
        nitrene_smiles, azide_position = to_nitrene(smiles)
        output_rows.append(
            {
                "manual_row": manual_row,
                "source_entry_raw": raw_entry(entry),
                "substrate_id": outcome["substrate_id"],
                "product_id": outcome["product_id"],
                "azide_smiles": smiles,
                "nitrene_smiles": nitrene_smiles,
                "azide_position": azide_position,
                "removed_species": "N2",
                "retained_atom": "aryl-bound proximal azide N",
                "intermediate_scope": "free nitrene representation; Fe coordination is added in the constrained pose pipeline",
                "validation_status": "terminal-azide pattern validated; RDKit atom-map and valence validation pending",
            }
        )

    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=output_rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(output_rows)} terminal-azide to nitrene records.")


if __name__ == "__main__":
    main()

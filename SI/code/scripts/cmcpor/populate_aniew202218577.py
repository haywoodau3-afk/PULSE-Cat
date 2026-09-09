#!/usr/bin/env python3
"""Populate the cmcporphyrin Angew. 2023 aryl scope inputs.

The source bundle is intentionally catalyst-specific: substrate/product
structures come from the user-supplied ``d4cmcscope.numbers`` table, while
the cmcpor yield/ee observations come from Table 1 of the Angewandte main
paper.  Product strings are canonicalized with RDKit after applying the
reported intramolecular C--N closure to the atom-mapped substrate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rdkit import Chem


ROOT = Path(__file__).resolve().parents[2]
NAMESPACE = ROOT / "data/expansion/catalyst_rerun/cmcpor"
SUBSTRATES = NAMESPACE / "substrates.jsonl"
OUTCOMES = NAMESPACE / "outcomes.jsonl"
STAGE2_RECORDS = NAMESPACE / "stage2-records.jsonl"
CURATED_STAGE2 = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"

# First line for each entry in Table 1 is the (S,R)-cmcporFeCl result.
# Values are isolated yield (%) and ee (%), respectively.
TABLE_1_OUTCOMES: dict[str, tuple[int, int, str | None, str | None]] = {
    "2b": (99, 88, "R", None),
    "2c": (80, 79, "R", None),
    "2d": (82, 86, "R", None),
    "2e": (75, 82, "R", None),
    "2f": (99, 84, "R", None),
    "2g": (62, 86, "R", None),
    "2h": (76, 90, "R", None),
    "2i": (72, 73, "R", None),
    "2j": (95, 79, "R", None),
    "2k": (82, 90, "R", None),
    "2l": (61, 78, "R", None),
    "2m": (97, 87, "R", None),
    "2n": (95, 60, "R", None),
    "2o": (30, 56, "R", None),
    "2p": (74, 71, "R", None),
    "2q": (56, 51, "R", None),
    "2r": (63, 80, "R", None),
    "2s": (70, 72, "R", None),
    "2t": (81, 74, "R", None),
    "2u": (97, 84, "R", None),
    "2v": (84, 84, "R", None),
    "2w": (35, 81, "R", None),
    "2x": (71, 79, "R", None),
    "2y": (73, 71, "R", None),
    "2z": (70, 70, "R", None),
    # The paper reports an optical-rotation sign rather than R/S for 2aa.
    "2aa": (89, 45, None, "+"),
}

CONDITIONS = {
    "temperature_c": -10,
    "solvent": "toluene",
    "light": "410 nm blue LEDs",
    "atmosphere": "argon",
    "additives": ["Boc2O (0.4 mmol, 2.0 equiv.)"],
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _azide_component(mol: Chem.Mol, proximal_idx: int) -> set[int]:
    """Return the N-only azide component containing the proximal N."""

    component = {proximal_idx}
    stack = [proximal_idx]
    while stack:
        idx = stack.pop()
        for neighbor in mol.GetAtomWithIdx(idx).GetNeighbors():
            if neighbor.GetSymbol() == "N" and neighbor.GetIdx() not in component:
                component.add(neighbor.GetIdx())
                stack.append(neighbor.GetIdx())
    return component


def _product_from_closure(row: dict[str, Any], mapped: bool) -> str:
    """Make the free indoline product by closing N to the reported C-H site."""

    substrate = Chem.MolFromSmiles(row["atom_mapped_substrate_smiles"])
    if substrate is None:
        raise ValueError(f"cannot parse mapped substrate for {row['paper_substrate_id']}")
    proximal = next(
        atom.GetIdx()
        for atom in substrate.GetAtoms()
        if atom.GetSymbol() == "N"
        and any(neighbor.GetSymbol() == "C" for neighbor in atom.GetNeighbors())
        and any(neighbor.GetSymbol() == "N" for neighbor in atom.GetNeighbors())
    )
    target = next(
        atom.GetIdx()
        for atom in substrate.GetAtoms()
        if atom.GetAtomMapNum() == row["reported_reactive_site_atom_map_id"]
    )
    azide_atoms = _azide_component(substrate, proximal)
    removable = sorted(azide_atoms - {proximal}, reverse=True)

    editable = Chem.RWMol(substrate)
    target_atom = editable.GetAtomWithIdx(target)
    target_atom.SetNumExplicitHs(max(0, target_atom.GetNumExplicitHs() - 1))
    target_atom.SetNoImplicit(True)
    target_atom.SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
    nitrene_atom = editable.GetAtomWithIdx(proximal)
    nitrene_atom.SetFormalCharge(0)
    nitrene_atom.SetNumExplicitHs(1)
    nitrene_atom.SetNoImplicit(True)

    for idx in removable:
        editable.RemoveAtom(idx)
        if idx < proximal:
            proximal -= 1
        if idx < target:
            target -= 1
    editable.AddBond(proximal, target, Chem.BondType.SINGLE)
    product = editable.GetMol()
    Chem.SanitizeMol(product)
    if not mapped:
        for atom in product.GetAtoms():
            atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(product, canonical=True)


def _outcome(row: dict[str, Any]) -> dict[str, Any]:
    paper_id = row["paper_substrate_id"]
    yield_percent, ee_percent, configuration, rotation = TABLE_1_OUTCOMES[paper_id]
    result: dict[str, Any] = {
        "compound_id": row["compound_id"],
        "paper_substrate_id": paper_id,
        "catalyst_id": "cmcpor-fecl",
        "condition_id": "angew-aryl-published",
        "record_role": "primary_scope",
        "isolated_yield_percent": yield_percent,
        "yield_status": "exact",
        "ee_percent": ee_percent,
        "ee_status": "reported",
        "feasibility_status": "productive",
        "major_product_configuration": configuration,
        "source": {
            "document_id": "anie-2023-main-paper",
            "location": f"Main paper Table 1 entry {paper_id} (cmcpor line)",
            "confidence": "primary_table",
        },
        "conditions": CONDITIONS,
    }
    if rotation:
        result["notes"] = "Table 1 reports (+) enantiomeric excess sign; no absolute R/S assignment is given for 2aa."
    return result


def _stage2_record(row: dict[str, Any], curated: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
    paper_id = row["paper_substrate_id"]
    record = {
        "schema_version": "stage2-reaction-record-v1",
        "substrate_id": paper_id,
        "product_id": paper_id,
        "reaction_id": f"angew-2023-aryl-{paper_id}-cmcpor",
        "catalyst_id": "cmcpor-fecl",
        "condition": {
            "condition_set_id": "angew-2023-table1-cmcpor",
            "temperature_c": -10,
            "solvent": "toluene",
            "light": "410 nm blue LEDs",
            "atmosphere": "argon",
        },
        "curation_status": "feature_ready",
        "family": curated.get("family", {"family_id": row["family_id"], "family_label": row["family_id"]}),
        "outcome": {
            "ee_percent": outcome["ee_percent"],
            "ee_status": "reported",
            "ee_status_stage0": "reported",
            "feasibility_status": "productive",
            "isolated_yield_percent": outcome["isolated_yield_percent"],
            "label_review_status": "checked",
            "major_product_configuration": outcome["major_product_configuration"],
            "yield_qualifier": "exact",
        },
        "reaction_center": curated["reaction_center"],
        "source": {
            "confidence": "primary_table",
            "curation_status_stage0": "source_indexed",
            "document_id": "anie-2023-main-paper",
            "location": f"Main paper Table 1 entry {paper_id}",
        },
        "structure": {
            "atom_mapped_product_smiles": _product_from_closure(row, mapped=True),
            "atom_mapped_substrate_smiles": row["atom_mapped_substrate_smiles"],
            "azide_nitrene_precursor_linkage": "aryl-bound proximal azide N",
            "azide_position": "prefix" if row["azide_smiles"].startswith(("N#N=N", "N=N#N")) else "suffix",
            "azide_smiles": row["azide_smiles"],
            "nitrene_smiles": row["nitrene_smiles"],
        },
    }
    return record


def main() -> None:
    substrates = _read_jsonl(SUBSTRATES)
    curated_by_product = {
        row["product_id"]: row for row in _read_jsonl(CURATED_STAGE2) if row.get("product_id") in TABLE_1_OUTCOMES
    }
    if set(row["paper_substrate_id"] for row in substrates) != set(TABLE_1_OUTCOMES):
        raise SystemExit("cmcpor substrates must contain exactly 2b–2aa before population")

    outcomes: list[dict[str, Any]] = []
    stage2: list[dict[str, Any]] = []
    for row in sorted(substrates, key=lambda value: (len(value["paper_substrate_id"]), value["paper_substrate_id"])):
        paper_id = row["paper_substrate_id"]
        row["product_smiles"] = _product_from_closure(row, mapped=False)
        row["product_smiles_source"] = {
            "document_id": "d4cmcscope.numbers",
            "location": f"Table 1 Product column entry {paper_id}",
            "normalization": "RDKit canonical free-indoline form",
        }
        outcome = _outcome(row)
        outcomes.append(outcome)
        curated = curated_by_product.get(paper_id)
        if curated is None:
            raise SystemExit(f"missing curated reaction-center record for {paper_id}")
        stage2.append(_stage2_record(row, curated, outcome))

    _write_jsonl(SUBSTRATES, substrates)
    _write_jsonl(OUTCOMES, outcomes)
    _write_jsonl(STAGE2_RECORDS, stage2)
    print(json.dumps({"substrates": len(substrates), "outcomes": len(outcomes), "stage2_records": len(stage2)}, indent=2))


if __name__ == "__main__":
    main()

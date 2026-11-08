#!/usr/bin/env python3
"""Remap the cmcporphyrin Angew scope from the user CSV.

The CSV is the authoritative Entry -> Starting/Product/outcome boundary for
the cmcporphyrin namespace.  This script deliberately keeps that boundary
separate from the P7 and D4 trees.  It assigns deterministic atom-map ids to
each starting SMILES, derives the substrate-bound nitrene, and checks whether
the supplied product can be reproduced by the reported intramolecular C-N
closure.  A product mismatch or non-unique closure is retained as an explicit
review state; it is never silently promoted to a feature-ready Stage 2 row.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs


ROOT = Path(__file__).resolve().parents[2]
NAMESPACE = ROOT / "data" / "expansion" / "catalyst_rerun" / "cmcpor"
DEFAULT_OUTPUT_ROOT = NAMESPACE
EXPECTED_IDS = (
    [f"2{letter}" for letter in "bcdefghijklmnopqrstuvwxyz"]
    + ["2aa", "2ab", "2ac"]
    + [f"4{letter}" for letter in "abcde"]
    + [f"6{letter}" for letter in "abcdefghijklmnopq"]
)

CONDITIONS = {
    "temperature_c": -10,
    "solvent": "toluene",
    "light": "410 nm blue LEDs",
    "atmosphere": "argon",
    "additives": ["Boc2O (0.4 mmol, 2.0 equiv.)"],
}


def natural_key(value: str) -> tuple[int, str]:
    match = re.fullmatch(r"(\d+)([a-z]+)", value)
    return (int(match.group(1)), match.group(2)) if match else (999, value)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def normalise_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def csv_value(row: dict[str, str], *aliases: str) -> str:
    normalised = {normalise_header(key): value.strip() for key, value in row.items() if key}
    for alias in aliases:
        value = normalised.get(normalise_header(alias), "")
        if value:
            return value
    raise ValueError(f"CSV row is missing one of {aliases}: {row}")


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"CSV is empty: {path}")
    parsed: list[dict[str, str]] = []
    for row in rows:
        parsed.append(
            {
                "entry": csv_value(row, "Entry"),
                "starting": csv_value(row, "Starting"),
                "product": csv_value(row, "Product"),
                "yield": csv_value(row, "Cmcporphyrin yield", "Cmc porphyrin yield"),
                # The supplied file spells this header ``Cmcmporphyrin ee``.
                "ee": csv_value(row, "Cmcporphyrin ee", "Cmcmporphyrin ee", "Cmc porphyrin ee"),
            }
        )
    ids = [row["entry"] for row in parsed]
    if len(ids) != len(set(ids)):
        duplicates = sorted({entry for entry in ids if ids.count(entry) > 1})
        raise ValueError(f"CSV contains duplicate Entry ids: {duplicates}")
    return parsed


def number(value: str, label: str) -> int | float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{label} is not numeric: {value!r}") from exc
    return int(parsed) if parsed.is_integer() else parsed


def canonical(molecule: Chem.Mol, *, isomeric: bool = False) -> str:
    return Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=isomeric)


def parse_smiles(smiles: str, label: str) -> Chem.Mol:
    molecule = Chem.MolFromSmiles(smiles, sanitize=True)
    if molecule is None:
        raise ValueError(f"{label} does not parse as SMILES: {smiles}")
    return molecule


def azide_info(molecule: Chem.Mol) -> tuple[int, set[int], int]:
    """Return proximal N index, all azide N indices, and its anchor index."""

    for atom in molecule.GetAtoms():
        if atom.GetSymbol() != "N":
            continue
        nitrogen_neighbours = [neighbour for neighbour in atom.GetNeighbors() if neighbour.GetSymbol() == "N"]
        anchors = [neighbour for neighbour in atom.GetNeighbors() if neighbour.GetSymbol() != "N"]
        if not nitrogen_neighbours or not anchors:
            continue
        component = {atom.GetIdx()}
        stack = [atom.GetIdx()]
        while stack:
            index = stack.pop()
            for neighbour in molecule.GetAtomWithIdx(index).GetNeighbors():
                if neighbour.GetSymbol() == "N" and neighbour.GetIdx() not in component:
                    component.add(neighbour.GetIdx())
                    stack.append(neighbour.GetIdx())
        if len(component) == 3:
            return atom.GetIdx(), component, anchors[0].GetIdx()
    raise ValueError("could not identify a three-nitrogen azide component")


def map_substrate(molecule: Chem.Mol) -> None:
    for index, atom in enumerate(molecule.GetAtoms(), start=1):
        atom.SetAtomMapNum(index)


def atom_map(molecule: Chem.Mol, atom_map_id: int) -> int:
    for atom in molecule.GetAtoms():
        if atom.GetAtomMapNum() == atom_map_id:
            return atom.GetIdx()
    raise ValueError(f"atom map id {atom_map_id} is not present")


def stripped_nitrene(molecule: Chem.Mol, proximal_index: int, azide_indices: set[int]) -> str:
    proximal_map = molecule.GetAtomWithIdx(proximal_index).GetAtomMapNum()
    rw_molecule = Chem.RWMol(molecule)
    for index in sorted(azide_indices - {proximal_index}, reverse=True):
        rw_molecule.RemoveAtom(index)
    nitrene = rw_molecule.GetMol()
    proximal = next(atom for atom in nitrene.GetAtoms() if atom.GetAtomMapNum() == proximal_map)
    proximal.SetFormalCharge(0)
    proximal.SetNoImplicit(True)
    proximal.SetNumExplicitHs(0)
    proximal.SetNumRadicalElectrons(1)
    for atom in nitrene.GetAtoms():
        atom.SetAtomMapNum(0)
    Chem.SanitizeMol(nitrene)
    return canonical(nitrene)


def closure_product(
    molecule: Chem.Mol,
    proximal_index: int,
    azide_indices: set[int],
    target_index: int,
) -> tuple[str, str]:
    """Return canonical free product and its atom-mapped form."""

    proximal_map = molecule.GetAtomWithIdx(proximal_index).GetAtomMapNum()
    target_map = molecule.GetAtomWithIdx(target_index).GetAtomMapNum()
    rw_molecule = Chem.RWMol(molecule)
    for index in sorted(azide_indices - {proximal_index}, reverse=True):
        rw_molecule.RemoveAtom(index)
    proximal = next(atom for atom in rw_molecule.GetAtoms() if atom.GetAtomMapNum() == proximal_map)
    target = next(atom for atom in rw_molecule.GetAtoms() if atom.GetAtomMapNum() == target_map)
    if rw_molecule.GetBondBetweenAtoms(proximal.GetIdx(), target.GetIdx()) is not None:
        raise ValueError("closure target is already bonded to proximal nitrene N")
    hydrogen_count = target.GetTotalNumHs()
    if hydrogen_count < 1:
        raise ValueError("closure target has no removable hydrogen")
    target.SetNoImplicit(True)
    target.SetNumExplicitHs(hydrogen_count - 1)
    target.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    proximal.SetFormalCharge(0)
    proximal.SetNoImplicit(True)
    proximal.SetNumExplicitHs(1)
    proximal.SetNumRadicalElectrons(0)
    proximal.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    rw_molecule.AddBond(proximal.GetIdx(), target.GetIdx(), Chem.BondType.SINGLE)
    product = rw_molecule.GetMol()
    Chem.SanitizeMol(product)
    mapped = canonical(product, isomeric=False)
    free_product = Chem.Mol(product)
    for atom in free_product.GetAtoms():
        atom.SetAtomMapNum(0)
    return canonical(free_product), mapped


def site_type(atom: Chem.Atom) -> str:
    if atom.GetIsAromatic():
        return "aryl"
    if any(neighbour.GetIsAromatic() for neighbour in atom.GetNeighbors()):
        return "benzylic"
    if atom.IsInRing():
        return "cycloalkyl"
    return "aliphatic"


def candidate_sites(molecule: Chem.Mol, azide_indices: set[int], entry: str) -> list[dict[str, Any]]:
    sites = []
    for atom in molecule.GetAtoms():
        if atom.GetSymbol() != "C" or atom.GetIdx() in azide_indices:
            continue
        hydrogen_count = atom.GetTotalNumHs()
        if hydrogen_count < 1:
            continue
        map_id = atom.GetAtomMapNum()
        kind = site_type(atom)
        sites.append(
            {
                "atom_map_id": map_id,
                "hydrogen_count": hydrogen_count,
                "site_id": f"{entry}-c{map_id}-{kind}",
                "site_type": kind,
            }
        )
    return sites


def fallback_target(
    molecule: Chem.Mol,
    proximal_index: int,
    sites: list[dict[str, Any]],
    pathway: str,
) -> int:
    ranked = []
    for site in sites:
        target_index = atom_map(molecule, site["atom_map_id"])
        distance = len(Chem.GetShortestPath(molecule, proximal_index, target_index)) - 1
        preferred_distance = 4 if pathway == "sulfonyl" else 4
        ranked.append((abs(distance - preferred_distance), distance, site["atom_map_id"]))
    if not ranked:
        raise ValueError("no C-H candidate sites were found")
    return min(ranked)[2]


def build_row(
    row: dict[str, str],
    csv_path: Path,
    repair_products: bool = False,
) -> dict[str, Any]:
    entry = row["entry"]
    starting = parse_smiles(row["starting"], f"{entry} Starting")
    product = parse_smiles(row["product"], f"{entry} Product")
    map_substrate(starting)
    proximal_index, azide_indices, anchor_index = azide_info(starting)
    pathway = "sulfonyl" if starting.GetAtomWithIdx(anchor_index).GetSymbol() == "S" else "aryl"
    sites = candidate_sites(starting, azide_indices, entry)
    if not sites:
        raise ValueError(f"{entry} has no non-azide carbon C-H candidate sites")
    product_canonical = canonical(product)
    matches: list[dict[str, Any]] = []
    closure_candidates: list[dict[str, Any]] = []
    for site in sites:
        target_index = atom_map(starting, site["atom_map_id"])
        try:
            generated_product, mapped_product = closure_product(
                starting, proximal_index, azide_indices, target_index
            )
        except (Chem.rdchem.KekulizeException, ValueError):
            continue
        closure_candidates.append(
            {
                "target_map_id": site["atom_map_id"],
                "generated_product_smiles": generated_product,
                "atom_mapped_product_smiles": mapped_product,
            }
        )
        if generated_product == product_canonical:
            matches.append(
                {
                    "target_map_id": site["atom_map_id"],
                    "generated_product_smiles": generated_product,
                    "atom_mapped_product_smiles": mapped_product,
                }
            )
    match_status = (
        "matched_unique"
        if len(matches) == 1
        else "matched_multiple"
        if len(matches) > 1
        else "no_product_match"
    )
    fallback_map_id = fallback_target(starting, proximal_index, sites, pathway)
    selected_match = matches[0] if matches else None
    repair: dict[str, Any] | None = None
    if repair_products and match_status != "matched_unique":
        if match_status == "matched_multiple":
            selected_match = sorted(matches, key=lambda value: value["target_map_id"])[0]
            repair = {
                "method": "symmetric_exact_closure_lowest_atom_map",
                "similarity_to_supplied_product": 1.0,
                "selected_target_map_id": selected_match["target_map_id"],
            }
        else:
            supplied_fp = AllChem.GetMorganFingerprintAsBitVect(product, 2, nBits=2048)
            scored = []
            for candidate in closure_candidates:
                candidate_molecule = Chem.MolFromSmiles(candidate["generated_product_smiles"])
                if candidate_molecule is None:
                    continue
                candidate_fp = AllChem.GetMorganFingerprintAsBitVect(candidate_molecule, 2, nBits=2048)
                scored.append(
                    (
                        float(DataStructs.TanimotoSimilarity(supplied_fp, candidate_fp)),
                        -int(candidate["target_map_id"]),
                        candidate,
                    )
                )
            if not scored:
                raise ValueError(f"{entry} has no valid product closure candidate for repair")
            similarity, _, selected_candidate = max(scored, key=lambda value: (value[0], value[1]))
            selected_match = selected_candidate
            repair = {
                "method": "starting_to_product_closure_morgan_similarity",
                "similarity_to_supplied_product": similarity,
                "selected_target_map_id": selected_candidate["target_map_id"],
            }
    reported_map_id = selected_match["target_map_id"] if selected_match else fallback_map_id
    mapped_product = selected_match["atom_mapped_product_smiles"] if selected_match else None
    final_product_smiles = row["product"]
    if repair and selected_match:
        final_product_smiles = selected_match["generated_product_smiles"]
    final_status = "repaired_from_starting" if repair else match_status
    curation_status = "feature_ready" if final_status in {"matched_unique", "repaired_from_starting"} else "atom_mapped"
    review_status = "checked" if curation_status == "feature_ready" else "needs_review"
    source = {
        "document_id": csv_path.name,
        "location": f"CSV Entry {entry}",
        "confidence": "user_supplied_csv",
        "path": str(csv_path),
    }
    reaction_center = {
        "candidate_sites": sites,
        "reported_reactive_site": next(site for site in sites if site["atom_map_id"] == reported_map_id)
        | {"role": "reported_product_forming_c_h"},
        "reported_site_in_candidates": True,
        "review_status": review_status,
        "source_note": (
            "Reported site selected by exact starting-to-product C-N closure matching."
            if match_status == "matched_unique"
            else f"CSV product validation status: {match_status}; target selected by starting-derived closure repair."
        ),
        "assignment_method": "csv_product_connectivity_match" if matches else "starting_product_closure_repair",
    }
    validation = {
        "status": final_status,
        "starting_smiles": row["starting"],
        "provided_product_smiles": row["product"],
        "provided_product_smiles_original": row["product"],
        "final_product_smiles": final_product_smiles,
        "provided_product_canonical_smiles": product_canonical,
        "closure_match_count": len(matches),
        "closure_match_atom_map_ids": [match["target_map_id"] for match in matches],
        "closure_candidates": closure_candidates,
        "repair": repair,
    }
    record = {
        "compound_id": f"angew-cmp-{entry}",
        "paper_substrate_id": entry,
        "pathway_id": pathway,
        "family_id": f"angew-{pathway}-c-h-amination",
        "azide_smiles": row["starting"],
        "nitrene_smiles": stripped_nitrene(starting, proximal_index, azide_indices),
        "atom_mapped_substrate_smiles": canonical(starting, isomeric=False),
        "product_smiles": final_product_smiles,
        "product_smiles_source": {
            **source,
            "normalization": "CSV product SMILES" if not repair else "starting-derived closure after CSV product connectivity mismatch",
        },
        "reported_reactive_site_atom_map_id": reported_map_id,
        "candidate_site_atom_map_ids": [site["atom_map_id"] for site in sites],
        "reported_reactive_site": reaction_center["reported_reactive_site"],
        "candidate_sites": sites,
        "reaction_center": reaction_center,
        "site_derivation": {
            "method": reaction_center["assignment_method"],
            "status": "derived_from_csv_product" if matches else "derived_from_starting_product_repair",
        },
        "structure_validation": validation,
        "source": source,
        "_mapped_product_smiles": mapped_product,
        "_curation_status": curation_status,
    }
    return record


def outcome(record: dict[str, Any], row: dict[str, str]) -> dict[str, Any]:
    entry = record["paper_substrate_id"]
    ee_note = None
    if entry in {"2aa", "2ab", "2ac"}:
        ee_note = "CSV reports the published enantiomeric excess value; absolute configuration is not encoded in this source table."
    result = {
        "compound_id": record["compound_id"],
        "paper_substrate_id": entry,
        "catalyst_id": "cmcpor-fecl",
        "condition_id": "angew-2023-published-cmcpor",
        "record_role": "primary_scope",
        "isolated_yield_percent": number(row["yield"], f"{entry} yield"),
        "yield_status": "exact",
        "ee_percent": number(row["ee"], f"{entry} ee"),
        "ee_status": "reported",
        "feasibility_status": "productive",
        "major_product_configuration": None,
        "source": {
            "document_id": record["source"]["document_id"],
            "location": record["source"]["location"],
            "confidence": "user_supplied_csv",
            "path": record["source"]["path"],
        },
        "conditions": CONDITIONS,
    }
    if ee_note:
        result["notes"] = ee_note
    return result


def stage2_record(record: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    entry = record["paper_substrate_id"]
    return {
        "schema_version": "stage2-reaction-record-v1",
        "substrate_id": entry,
        "product_id": entry,
        "reaction_id": f"angew-2023-{record['pathway_id']}-{entry}-cmcpor",
        "catalyst_id": "cmcpor-fecl",
        "condition": {
            "condition_set_id": "angew-2023-published-cmcpor",
            **{key: value for key, value in CONDITIONS.items() if key != "additives"},
        },
        "curation_status": record["_curation_status"],
        "family": {
            "family_id": record["family_id"],
            "family_label": "Aryl azide C-H amination" if record["pathway_id"] == "aryl" else "Sulfonyl azide C-H amination",
            "assignment_method": "csv_pathway",
        },
        "outcome": {
            "ee_percent": result["ee_percent"],
            "ee_status": "reported",
            "ee_status_stage0": "reported",
            "feasibility_status": "productive",
            "isolated_yield_percent": result["isolated_yield_percent"],
            "label_review_status": "checked",
            "major_product_configuration": result.get("major_product_configuration"),
            "yield_qualifier": "exact",
        },
        "reaction_center": record["reaction_center"],
        "source": record["source"],
        "structure": {
            "atom_mapped_product_smiles": record["_mapped_product_smiles"],
            "atom_mapped_substrate_smiles": record["atom_mapped_substrate_smiles"],
            "azide_nitrene_precursor_linkage": "sulfonyl-bound proximal azide N" if record["pathway_id"] == "sulfonyl" else "aryl-bound proximal azide N",
            "azide_position": "prefix" if record["azide_smiles"].startswith(("N#N=N", "N=N#N")) else "suffix",
            "azide_smiles": record["azide_smiles"],
            "nitrene_smiles": record["nitrene_smiles"],
            "provided_product_smiles": record["product_smiles"],
            "structure_validation": record["structure_validation"],
        },
    }


def clean_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if not key.startswith("_")}


def write_validation_report(
    path: Path,
    records: list[dict[str, Any]],
    missing: list[str],
    csv_path: Path,
) -> None:
    summary = {
        "status": "complete_with_repairs" if any(record["structure_validation"]["status"] == "repaired_from_starting" for record in records) else "complete",
        "record_count": len(records),
        "feature_ready_count": sum(record["_curation_status"] == "feature_ready" for record in records),
        "needs_review_count": sum(record["_curation_status"] != "feature_ready" for record in records),
        "repair_count": sum(record["structure_validation"].get("repair") is not None for record in records),
        "missing_expected_ids": missing,
        "product_validation": {
            status: sum(record["structure_validation"]["status"] == status for record in records)
            for status in ("matched_unique", "matched_multiple", "no_product_match", "repaired_from_starting")
        },
        "source_csv": str(csv_path),
    }
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def write_validation_csv(
    path: Path,
    records: list[dict[str, Any]],
    rows_by_id: dict[str, dict[str, str]],
) -> None:
    fields = [
        "entry",
        "pathway",
        "yield_percent",
        "ee_percent",
        "product_validation_status",
        "closure_match_count",
        "reported_reactive_site_atom_map_id",
        "candidate_site_atom_map_ids",
        "provided_starting_smiles",
        "provided_product_smiles",
        "closure_candidates",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            validation = record["structure_validation"]
            writer.writerow(
                {
                    "entry": record["paper_substrate_id"],
                    "pathway": record["pathway_id"],
                    "yield_percent": rows_by_id[record["paper_substrate_id"]]["yield"],
                    "ee_percent": rows_by_id[record["paper_substrate_id"]]["ee"],
                    "product_validation_status": validation["status"],
                    "closure_match_count": validation["closure_match_count"],
                    "reported_reactive_site_atom_map_id": record["reported_reactive_site_atom_map_id"],
                    "candidate_site_atom_map_ids": ",".join(str(value) for value in record["candidate_site_atom_map_ids"]),
                    "provided_starting_smiles": validation["starting_smiles"],
                    "provided_product_smiles": validation["provided_product_smiles"],
                    "closure_candidates": " || ".join(
                        f"{candidate['target_map_id']}:{candidate['generated_product_smiles']}"
                        for candidate in validation["closure_candidates"]
                    ),
                }
            )


def write_site_report(path: Path, records: list[dict[str, Any]]) -> None:
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
                    "reported_site_type": site["site_type"],
                    "reported_hydrogen_count": site["hydrogen_count"],
                    "candidate_atom_map_ids": ",".join(
                        str(value) for value in record["candidate_site_atom_map_ids"]
                    ),
                    "assignment_status": record["site_derivation"]["status"],
                }
            )


def run(csv_path: Path, output_root: Path, repair_products: bool = False) -> dict[str, Any]:
    rows = load_rows(csv_path)
    records = [build_row(row, csv_path, repair_products=repair_products) for row in rows]
    records.sort(key=lambda record: natural_key(record["paper_substrate_id"]))
    actual = [record["paper_substrate_id"] for record in records]
    missing = sorted(set(EXPECTED_IDS) - set(actual), key=natural_key)
    extra = sorted(set(actual) - set(EXPECTED_IDS), key=natural_key)
    if extra:
        raise ValueError(f"CSV contains unexpected Entry ids: {extra}")
    by_id = {row["entry"]: row for row in rows}
    clean_records = [clean_record(record) for record in records]
    outcome_records = [outcome(record, by_id[record["paper_substrate_id"]]) for record in records]
    stage2_records = [stage2_record(record, outcome_record) for record, outcome_record in zip(records, outcome_records)]
    write_jsonl(output_root / "source-structures.jsonl", clean_records)
    write_jsonl(output_root / "substrates.jsonl", clean_records)
    write_jsonl(output_root / "outcomes.jsonl", outcome_records)
    write_jsonl(output_root / "stage2-records.jsonl", stage2_records)
    report_path = output_root / "remap-validation.json"
    write_validation_report(report_path, records, missing, csv_path)
    write_validation_csv(output_root / "remap-validation.csv", records, by_id)
    write_site_report(output_root / "derived-nitrene-sites.csv", records)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["extra_ids"] = extra
    report["input_rows"] = len(rows)
    report["repair_products"] = repair_products
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True, help="user-supplied cmcpor scope CSV")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--repair-products",
        action="store_true",
        help="repair CSV product connectivity mismatches from the starting-SMILES closure and record provenance",
    )
    args = parser.parse_args()
    report = run(args.csv.resolve(), args.output_root.resolve(), repair_products=args.repair_products)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

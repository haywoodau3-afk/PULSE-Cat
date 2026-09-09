#!/usr/bin/env python3
"""Build the SI2 record-level RDKit + Morgan feature table.

The table is intentionally generated from the un-mapped aryl-azide SMILES so
it is suitable for structure-only modelling and does not encode the reported
product-forming atom.  The script writes one row per substrate and keeps the
feature order explicit in a companion JSON manifest.
"""

from __future__ import annotations

import argparse
import csv
import json
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdFingerprintGenerator, rdMolDescriptors


SI2_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUTS = [
    SI2_ROOT / "data/inputs/p7-curated-reaction-records.jsonl",
    SI2_ROOT / "data/inputs/cmcpor-curated-reaction-records.jsonl",
]
DEFAULT_OUTPUT = SI2_ROOT / "data/rdkit-morgan/rdkit-morgan-features.csv"
DEFAULT_MANIFEST = SI2_ROOT / "data/rdkit-morgan/rdkit-morgan-features-manifest.json"
RADIUS = 2
MORGAN_BITS = 1024


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def substrate_smiles(record: dict[str, Any]) -> str:
    value = record.get("structure", {}).get("azide_smiles")
    if not value:
        raise ValueError(f"{record.get('substrate_id', '<unknown>')}: missing structure.azide_smiles")
    return str(value)


def descriptor_values(molecule: Chem.Mol) -> dict[str, float]:
    return {
        "heavy_atom_count": float(molecule.GetNumHeavyAtoms()),
        "molecular_weight": float(Descriptors.MolWt(molecule)),
        "logp": float(Crippen.MolLogP(molecule)),
        "tpsa": float(rdMolDescriptors.CalcTPSA(molecule)),
        "formal_charge": float(Chem.GetFormalCharge(molecule)),
        "fraction_csp3": float(rdMolDescriptors.CalcFractionCSP3(molecule)),
        "rotatable_bonds": float(Lipinski.NumRotatableBonds(molecule)),
        "rings": float(rdMolDescriptors.CalcNumRings(molecule)),
        "aromatic_rings": float(rdMolDescriptors.CalcNumAromaticRings(molecule)),
        "h_bond_acceptors": float(Lipinski.NumHAcceptors(molecule)),
        "h_bond_donors": float(Lipinski.NumHDonors(molecule)),
        "hetero_atoms": float(rdMolDescriptors.CalcNumHeteroatoms(molecule)),
        "aliphatic_rings": float(rdMolDescriptors.CalcNumAliphaticRings(molecule)),
        "spiro_atoms": float(rdMolDescriptors.CalcNumSpiroAtoms(molecule)),
        "chiral_centers": float(len(Chem.FindMolChiralCenters(molecule, includeUnassigned=True))),
    }


def fingerprint_values(molecule: Chem.Mol) -> list[float]:
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=RADIUS, fpSize=MORGAN_BITS)
    fingerprint = generator.GetFingerprint(molecule)
    values = np.zeros((MORGAN_BITS,), dtype=np.float64)
    DataStructs.ConvertToNumpyArray(fingerprint, values)
    return values.tolist()


def rdkit_version() -> str:
    try:
        return metadata.version("rdkit")
    except metadata.PackageNotFoundError:
        return "unknown"


def build_records(input_paths: list[Path]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    descriptor_names = list(descriptor_values(Chem.MolFromSmiles("C")).keys())
    fingerprint_names = [f"morgan_r{RADIUS}_bit_{index:04d}" for index in range(MORGAN_BITS)]
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for input_path in input_paths:
        domain = "p7" if input_path.name.startswith("p7-") else "cmcpor"
        for record in read_jsonl(input_path):
            substrate_id = str(record["substrate_id"])
            if substrate_id in seen:
                raise ValueError(f"duplicate substrate_id: {substrate_id}")
            seen.add(substrate_id)
            molecule = Chem.MolFromSmiles(substrate_smiles(record), sanitize=True)
            if molecule is None:
                raise ValueError(f"{substrate_id}: RDKit could not parse azide_smiles")
            values: dict[str, Any] = {
                "domain": domain,
                "substrate_id": substrate_id,
                "reaction_id": record.get("reaction_id", ""),
                "family_id": record.get("family", {}).get("family_id", ""),
                "catalyst_id": record.get("catalyst_id", ""),
                "azide_smiles": substrate_smiles(record),
                "ee_percent": record.get("outcome", {}).get("ee_percent", ""),
                "isolated_yield_percent": record.get("outcome", {}).get("isolated_yield_percent", ""),
            }
            values.update(descriptor_values(molecule))
            values.update(dict(zip(fingerprint_names, fingerprint_values(molecule), strict=True)))
            rows.append(values)
    return rows, descriptor_names, fingerprint_names


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    rows, descriptor_names, fingerprint_names = build_records(args.inputs)
    metadata_names = ["domain", "substrate_id", "reaction_id", "family_id", "catalyst_id", "azide_smiles", "ee_percent", "isolated_yield_percent"]
    fieldnames = metadata_names + descriptor_names + fingerprint_names
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "schema_version": "si2-rdkit-morgan-table-v1",
        "row_count": len(rows),
        "domains": {"p7": sum(row["domain"] == "p7" for row in rows), "cmcpor": sum(row["domain"] == "cmcpor" for row in rows)},
        "input_paths": [str(path) for path in args.inputs],
        "smiles_field": "structure.azide_smiles",
        "rdkit": {"version": rdkit_version(), "sanitize": True},
        "descriptors": {"count": len(descriptor_names), "names": descriptor_names},
        "morgan": {"radius": RADIUS, "n_bits": MORGAN_BITS, "include_chirality": False, "bit_order": "morgan_r2_bit_0000 through morgan_r2_bit_1023"},
        "feature_count": len(descriptor_names) + len(fingerprint_names),
        "leakage_policy": "unmapped substrate-only SMILES; no product or reported reactive-site fields are used",
        "output_path": str(args.output),
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} rows and {manifest['feature_count']} features to {args.output}")


if __name__ == "__main__":
    main()

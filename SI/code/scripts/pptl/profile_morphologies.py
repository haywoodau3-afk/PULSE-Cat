"""Profile aryl-azide starting-material morphology axes."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski


def family(mol: Chem.Mol) -> str:
    rings = Lipinski.RingCount(mol)
    sp3 = sum(a.GetHybridization() == Chem.HybridizationType.SP3 for a in mol.GetAtoms()) / max(1, mol.GetNumAtoms())
    hetero = sum(a.GetAtomicNum() not in {1, 6} for a in mol.GetAtoms())
    if rings >= 3:
        return "fused_or_polycyclic"
    if sp3 >= 0.35:
        return "flexible_sp3_rich"
    if hetero >= 5:
        return "heteroatom_rich"
    if rings == 2:
        return "diaryl_or_bicyclic"
    return "simple_aryl_tether"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = []
    for row in csv.DictReader(args.input.open(encoding="utf-8")):
        if row.get("contract_valid") != "true" or row.get("ad_status") not in {"in_domain", ""}:
            continue
        smi = row.get("canonical_smiles", "")
        mol = Chem.MolFromSmiles(smi) if smi else None
        if mol is None:
            continue
        row["morphology_family"] = family(mol)
        row["molecular_weight"] = f"{Descriptors.MolWt(mol):.3f}"
        row["ring_count"] = str(Lipinski.RingCount(mol))
        row["sp3_fraction"] = f"{sum(a.GetHybridization() == Chem.HybridizationType.SP3 for a in mol.GetAtoms()) / max(1, mol.GetNumAtoms()):.4f}"
        row["heteroatom_count"] = str(sum(a.GetAtomicNum() not in {1, 6} for a in mol.GetAtoms()))
        out.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        fields = list(out[0]) if out else ["candidate_id", "morphology_family"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out)
    counts = {}
    for row in out:
        counts[row["morphology_family"]] = counts.get(row["morphology_family"], 0) + 1
    print(json.dumps({"candidate_count": len(out), "morphology_counts": counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

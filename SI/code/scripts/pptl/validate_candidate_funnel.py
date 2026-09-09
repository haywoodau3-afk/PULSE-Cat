"""Validate raw candidate records without making experimental decisions."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from rdkit import Chem


def validate(smiles: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False, ["rdkit_parse_failed"]
    try:
        Chem.SanitizeMol(mol)
    except Exception:
        return False, ["rdkit_sanitize_failed"]
    azide = mol.HasSubstructMatch(Chem.MolFromSmarts("[c][N-]=[N+]=N")) or mol.HasSubstructMatch(
        Chem.MolFromSmarts("[c]N=[N+]=[N-]")
    )
    if not azide:
        reasons.append("aryl_azide_not_detected")
    conservative = False
    closure_valid = False
    # Conservative contract: an aryl-azide ring carbon has an ortho ring
    # neighbour bearing a two-carbon sp3 tether ending at a H-bearing carbon.
    for atom in mol.GetAtoms():
        if not atom.GetIsAromatic() or atom.GetAtomicNum() != 6:
            continue
        proximal = next((n for n in atom.GetNeighbors() if n.GetAtomicNum() == 7 and not n.GetIsAromatic()), None)
        if proximal is None:
            continue
        for ring_neighbor in atom.GetNeighbors():
            if not ring_neighbor.GetIsAromatic() or ring_neighbor.GetAtomicNum() != 6:
                continue
            for tether in ring_neighbor.GetNeighbors():
                if tether.GetIsAromatic() or tether.GetAtomicNum() != 6 or tether.GetHybridization() != Chem.HybridizationType.SP3:
                    continue
                for target in tether.GetNeighbors():
                    if target is tether or target.GetIsAromatic() or target.GetAtomicNum() != 6 or target.GetHybridization() != Chem.HybridizationType.SP3:
                        continue
                    if target.GetTotalNumHs() >= 1:
                        conservative = True
                        path = Chem.GetShortestPath(mol, proximal.GetIdx(), target.GetIdx())
                        if len(path) - 1 == 4:
                            closure_valid = True
    if azide and not conservative:
        reasons.append("conservative_ortho_two_carbon_tether_not_detected")
    if conservative and not closure_valid:
        reasons.append("five_member_cn_closure_not_detected")
    if any(atom.GetAtomicNum() == 9 for atom in mol.GetAtoms()):
        pass
    if mol.GetNumAtoms() > 80:
        reasons.append("size_limit_exceeded")
    azide_matches = mol.GetSubstructMatches(Chem.MolFromSmarts("[N-]=[N+]=N"))
    if not azide_matches:
        azide_matches = mol.GetSubstructMatches(Chem.MolFromSmarts("N=[N+]=[N-]"))
    if len(azide_matches) > 1:
        reasons.append("multiple_azides")
    if mol.HasSubstructMatch(Chem.MolFromSmarts("OO")):
        reasons.append("peroxide_like_oo_bond")
    if mol.HasSubstructMatch(Chem.MolFromSmarts("S(=O)(=O)N=[N+]=[N-]")):
        reasons.append("sulfonyl_azide_pathway")
    return not reasons, reasons


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="JSONL with candidate_id, smiles, provenance")
    parser.add_argument("--output", type=Path, required=True, help="CSV funnel report")
    args = parser.parse_args()
    rows = []
    seen_canonical: set[str] = set()
    duplicate_count = 0
    for line_number, line in enumerate(args.input.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        smiles = str(record.get("smiles", ""))
        valid, reasons = validate(smiles)
        canonical = ""
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            canonical = Chem.MolToSmiles(mol, canonical=True)
            if canonical in seen_canonical:
                reasons.append("duplicate_canonical")
                valid = False
                duplicate_count += 1
            else:
                seen_canonical.add(canonical)
        rows.append(
            {
                "candidate_id": record.get("candidate_id", f"line-{line_number}"),
                "smiles": smiles,
                "provenance": record.get("provenance", "unknown"),
                "canonical_smiles": canonical,
                "contract_valid": str(valid).lower(),
                "rejection_reasons": ";".join(reasons),
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["candidate_id", "smiles", "provenance", "contract_valid", "rejection_reasons"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"input_count": len(rows), "unique_count": len(seen_canonical), "duplicate_count": duplicate_count, "contract_valid_count": sum(r["contract_valid"] == "true" for r in rows), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

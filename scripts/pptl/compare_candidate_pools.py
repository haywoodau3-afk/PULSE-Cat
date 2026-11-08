"""Compare candidate pools on uniqueness, Morgan diversity and reference novelty."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem


def fingerprints(path: Path, limit: int = 500):
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    rows = [r for r in rows if r.get("contract_valid") == "true" and r.get("canonical_smiles")]
    random.Random(1101).shuffle(rows)
    rows = rows[:limit]
    fps = []
    for row in rows:
        mol = Chem.MolFromSmiles(row["canonical_smiles"])
        if mol is not None:
            fps.append(AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048))
    return rows, fps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--enumeration", type=Path, required=True)
    parser.add_argument("--references", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    refs = []
    for path in args.references:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            smi = obj.get("smiles") or obj.get("structure", {}).get("atom_mapped_substrate_smiles")
            mol = Chem.MolFromSmiles(smi) if smi else None
            if mol is not None:
                refs.append(AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048))
    result = {"reference_count": len(refs), "availability_status": "not_assessed_without_real_supplier_evidence"}
    for name, path in (("generator", args.generator), ("enumeration", args.enumeration)):
        rows, fps = fingerprints(path)
        sims = [max(DataStructs.TanimotoSimilarity(fp, ref) for ref in refs) for fp in fps] if refs else []
        pairwise = [DataStructs.TanimotoSimilarity(a, b) for i, a in enumerate(fps) for b in fps[i + 1 :]]
        result[name] = {
            "contract_valid_count": sum(r.get("contract_valid") == "true" for r in csv.DictReader(path.open(encoding="utf-8"))),
            "sample_count": len(fps),
            "mean_pairwise_tanimoto": sum(pairwise) / len(pairwise) if pairwise else None,
            "mean_pairwise_distance": 1 - sum(pairwise) / len(pairwise) if pairwise else None,
            "mean_max_reference_similarity": sum(sims) / len(sims) if sims else None,
            "novelty_proxy": 1 - sum(sims) / len(sims) if sims else None,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Score candidate applicability domain by Morgan similarity to reference SMILES."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem


def load_reference(path: Path) -> list:
    refs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        smi = obj.get("smiles") or obj.get("structure", {}).get("atom_mapped_substrate_smiles")
        if smi:
            mol = Chem.MolFromSmiles(smi)
            if mol is not None:
                refs.append(AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048))
    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--references", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.35)
    args = parser.parse_args()
    refs = [fp for p in args.references for fp in load_reference(p)]
    out = []
    for row in csv.DictReader(args.candidates.open(encoding="utf-8")):
        smi = row.get("canonical_smiles", "")
        mol = Chem.MolFromSmiles(smi) if smi else None
        score = None
        if mol is not None and refs:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            score = max(DataStructs.TanimotoSimilarity(fp, ref) for ref in refs)
        row["ad_max_morgan_tanimoto"] = "" if score is None else f"{score:.6f}"
        row["ad_status"] = "in_domain" if score is not None and score >= args.threshold else "ood_or_unscored"
        out.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        fields = list(out[0]) if out else ["canonical_smiles", "ad_max_morgan_tanimoto", "ad_status"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out)
    print(json.dumps({"candidate_count": len(out), "reference_count": len(refs), "threshold": args.threshold}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

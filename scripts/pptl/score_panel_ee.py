"""Fit a frozen-development Morgan/Ridge ee model and score a morphology panel."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.linear_model import Ridge


def fp(smiles: str) -> np.ndarray:
    mol = Chem.MolFromSmiles(smiles)
    bit = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
    return np.asarray(bit, dtype=float)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, nargs="+", required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    x, y = [], []
    for path in args.records:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            ee = r.get("outcome", {}).get("ee_percent")
            smi = r.get("structure", {}).get("atom_mapped_substrate_smiles")
            if isinstance(ee, (int, float)) and smi:
                x.append(fp(smi)); y.append(float(ee))
    model = Ridge(alpha=10.0).fit(np.asarray(x), np.asarray(y))
    rows = list(csv.DictReader(args.panel.open(encoding="utf-8")))
    for row in rows:
        row["ee_prediction_development"] = f"{float(model.predict(fp(row['canonical_smiles']).reshape(1, -1))[0]):.4f}"
        row["ee_model_status"] = "frozen_development_ridge_not_prospective_truth"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print(f"scored {len(rows)} panel candidates using {len(y)} labelled ee records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

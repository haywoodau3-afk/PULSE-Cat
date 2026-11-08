"""Simulate locked 0->4->8 ee-aware acquisition without revealing outcomes."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--enumeration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {}
    for name, path in (("generator", args.generator), ("enumeration", args.enumeration)):
        rows = [r for r in csv.DictReader(path.open(encoding="utf-8")) if r.get("contract_valid") == "true" and r.get("ad_status") == "in_domain"]
        # Round A: top predicted-ee candidates. Round B: maximize diversity while
        # remaining within the upper predicted-ee quartile.
        rows.sort(key=lambda r: (-float(r["ee_prediction_development"]), r["canonical_smiles"]))
        round_a = rows[:4]
        chosen = list(round_a)
        fps = [AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(r["canonical_smiles"]), 2, nBits=2048) for r in chosen]
        pool = rows[4:]
        cutoff = sorted(float(r["ee_prediction_development"]) for r in rows)[int(0.75 * len(rows))]
        pool = [r for r in pool if float(r["ee_prediction_development"]) >= cutoff]
        while len(chosen) < 8 and pool:
            best = max(pool, key=lambda r: min(1 - DataStructs.TanimotoSimilarity(AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(r["canonical_smiles"]), 2, nBits=2048), fp) for fp in fps))
            chosen.append(best); pool.remove(best)
            fps.append(AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(best["canonical_smiles"]), 2, nBits=2048))
        report[name] = {"eligible_pool": len(rows), "round_a_ids": [r["candidate_id"] for r in round_a], "round_b_ids": [r["candidate_id"] for r in chosen[4:]], "round_a_mean_predicted_ee": sum(float(r["ee_prediction_development"]) for r in round_a) / 4, "round_b_mean_predicted_ee": sum(float(r["ee_prediction_development"]) for r in chosen[4:]) / max(1, len(chosen[4:])), "total_selected": len(chosen)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

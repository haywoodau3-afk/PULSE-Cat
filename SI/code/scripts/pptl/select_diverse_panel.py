"""Select a deterministic, diversity-aware development panel."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=16)
    args = parser.parse_args()
    rows = list(csv.DictReader(args.input.open(encoding="utf-8")))
    rows = [r for r in rows if r.get("contract_valid") == "true" and r.get("ad_status") == "in_domain" and r.get("canonical_smiles")]
    fps = []
    kept = []
    for row in rows:
        mol = Chem.MolFromSmiles(row["canonical_smiles"])
        if mol is not None:
            fps.append(AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048))
            kept.append(row)
    selected: list[int] = []
    if fps:
        selected.append(0)
    while len(selected) < min(args.size, len(fps)):
        best = max((i for i in range(len(fps)) if i not in selected), key=lambda i: min(1 - DataStructs.TanimotoSimilarity(fps[i], fps[j]) for j in selected))
        selected.append(best)
    chosen = [kept[i] for i in selected]
    for rank, row in enumerate(chosen, 1):
        row["panel_rank"] = str(rank)
        row["selection_status"] = "development_shortlist_pending_route_availability_ehs"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        fields = list(chosen[0]) if chosen else ["candidate_id", "canonical_smiles", "panel_rank", "selection_status"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(chosen)
    print(f"selected {len(chosen)} from {len(kept)} eligible-by-model candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

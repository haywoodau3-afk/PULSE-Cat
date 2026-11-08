"""Rank corrected occupancy overlap for all shared P7/CMC substrate identities."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from rdkit import Chem

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P7_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
CMC_RECORDS = ROOT / "data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl"
P7_DENSITY = HERE / "stage2pp_p7/density"
CMC_DENSITY = HERE / "stage2pp_cmc/density"
OUT = HERE / "corrected_project"
CHANNEL = "nitrene__all_heavy__all_200"


def read_records(path: Path, catalyst: str) -> dict[str, str]:
    output: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        catalyst_id = record.get("catalyst_id") or record.get("catalyst", {}).get("catalyst_id")
        if catalyst_id != catalyst:
            continue
        smiles = record["structure"]["atom_mapped_substrate_smiles"]
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise ValueError(f"{record['substrate_id']}: invalid mapped substrate SMILES")
        for atom in molecule.GetAtoms():
            atom.SetAtomMapNum(0)
        canonical = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
        if canonical in output:
            raise ValueError(f"Duplicate canonical substrate identity in {path}: {canonical}")
        output[canonical] = record["substrate_id"]
    return output


def normalised(path: Path) -> np.ndarray:
    with np.load(path) as archive:
        grid = np.maximum(archive[CHANNEL].astype(float), 0.0)
    total = float(grid.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError(f"Empty or invalid occupancy grid: {path}")
    return grid / total


def metrics(p: np.ndarray, q: np.ndarray) -> dict[str, float]:
    if p.shape != q.shape:
        raise ValueError(f"Occupancy grids have different shapes: {p.shape} and {q.shape}")
    midpoint = 0.5 * (p + q)
    positive_p = p > 0
    positive_q = q > 0
    js = 0.5 * float(np.sum(p[positive_p] * np.log2(p[positive_p] / midpoint[positive_p])))
    js += 0.5 * float(np.sum(q[positive_q] * np.log2(q[positive_q] / midpoint[positive_q])))
    return {
        "bhattacharyya_coefficient": float(np.sqrt(p * q).sum()),
        "total_variation_distance": 0.5 * float(np.abs(p - q).sum()),
        "jensen_shannon_divergence_bits": js,
        "grid_cells": int(p.size),
    }


def main() -> None:
    p7 = read_records(P7_RECORDS, "fe-p7-cl")
    cmc = read_records(CMC_RECORDS, "cmcpor-fecl")
    shared = sorted(set(p7) & set(cmc))
    if len(shared) != 13:
        raise ValueError(f"Expected 13 canonical shared identities; found {len(shared)}")

    rows = []
    for identity in shared:
        p7_id, cmc_id = p7[identity], cmc[identity]
        p = normalised(P7_DENSITY / f"{p7_id}.npz")
        q = normalised(CMC_DENSITY / f"{cmc_id}.npz")
        rows.append({"p7_substrate_id": p7_id, "cmc_substrate_id": cmc_id, **metrics(p, q)})
    rows.sort(key=lambda row: (-row["jensen_shannon_divergence_bits"], row["p7_substrate_id"], row["cmc_substrate_id"]))
    for rank, row in enumerate(rows, start=1):
        row["corrected_js_rank"] = rank

    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "cross_catalyst_occupancy_scan.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "status": "corrected all-shared-identity scan",
        "shared_identity_count": len(rows),
        "identity_matching": "canonical isomeric SMILES after removing atom-map numbers",
        "feature": "Stage 2pp nitrene-centred all-heavy-atom occupancy, all 200 poses",
        "normalization": "Each non-negative occupancy grid normalized to unit sum before overlap and divergence metrics",
        "metrics": {
            "bhattacharyya_coefficient": "sum(sqrt(p*q)); 1 is identical",
            "total_variation_distance": "0.5*sum(abs(p-q)); range 0 to 1",
            "jensen_shannon_divergence_bits": "symmetric base-2 Jensen-Shannon divergence; range 0 to 1",
        },
        "ranking": rows,
        "previously_illustrated_pair": next(row for row in rows if (row["p7_substrate_id"], row["cmc_substrate_id"]) == ("1i", "2r")),
        "highest_corrected_divergence_pair": rows[0],
        "interpretation_limit": "These are similarities between computed descriptor grids, not measured conformer populations or mechanistic evidence.",
    }
    (OUT / "cross_catalyst_occupancy_scan.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": rows, "csv": str(csv_path.relative_to(HERE))}, indent=2))


if __name__ == "__main__":
    main()

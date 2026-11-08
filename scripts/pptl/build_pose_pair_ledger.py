#!/usr/bin/env python3
"""Compare persisted Stage 2p vectors for canonical P7/CMC-Por pairs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from core import build_feature_matrix, canonical_overlap, load_reaction_rows


def _pair_distance(left: np.ndarray, right: np.ndarray) -> dict[str, float | None]:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    delta = left - right
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    cosine = None if left_norm == 0.0 or right_norm == 0.0 else float(np.dot(left, right) / (left_norm * right_norm))
    return {
        "l1": float(np.sum(np.abs(delta))),
        "rmse": float(np.sqrt(np.mean(delta * delta))),
        "cosine": cosine,
        "left_mean": float(np.mean(left)),
        "right_mean": float(np.mean(right)),
    }


def build_pose_pair_ledger(p7_records: Path, cmcpor_records: Path, p7_stage2p: Path, cmcpor_stage2p: Path, *, target: str = "ee_percent") -> dict:
    p7 = load_reaction_rows(p7_records, catalyst="fe-p7-cl", target=target, include_unlabelled=True, pose_features_path=p7_stage2p)
    cmc = load_reaction_rows(cmcpor_records, catalyst="cmcpor-fecl", target=target, include_unlabelled=True, pose_features_path=cmcpor_stage2p)
    overlap = canonical_overlap(p7, cmc)
    p7_by_id = {row.substrate_id: row for row in p7}
    cmc_by_id = {row.substrate_id: row for row in cmc}
    p7_rows = [p7_by_id[item["left_id"]] for item in overlap.values()]
    cmc_rows = [cmc_by_id[item["right_id"]] for item in overlap.values()]
    p7_matrix, p7_names = build_feature_matrix(p7_rows, "P0")
    cmc_matrix, cmc_names = build_feature_matrix(cmc_rows, "P0")
    if p7_names != cmc_names:
        raise ValueError("P7 and CMC-Por Stage 2p feature names differ")
    p7_compact, p7_compact_names = build_feature_matrix(p7_rows, "P3")
    cmc_compact, cmc_compact_names = build_feature_matrix(cmc_rows, "P3")
    if p7_compact_names != cmc_compact_names:
        raise ValueError("P7 and CMC-Por compact Stage 2p feature names differ")
    compact_count = len(p7_compact_names) - 1039
    if compact_count <= 0:
        raise ValueError("P3 compact pose block is empty")
    # P3 is B5 followed by compact pose columns; retain only that suffix.
    p7_compact = p7_compact[:, -compact_count:]
    cmc_compact = cmc_compact[:, -compact_count:]
    pairs = []
    for index, canonical in enumerate(sorted(overlap)):
        pair = overlap[canonical]
        pairs.append({
            "canonical_compound_group": canonical,
            "p7_substrate_id": pair["left_id"],
            "cmcpor_substrate_id": pair["right_id"],
            "p7_ee_percent": p7_by_id[pair["left_id"]].value("ee_percent"),
            "cmcpor_ee_percent": cmc_by_id[pair["right_id"]].value("ee_percent"),
            "p7_yield_percent": p7_by_id[pair["left_id"]].value("isolated_yield_percent"),
            "cmcpor_yield_percent": cmc_by_id[pair["right_id"]].value("isolated_yield_percent"),
            "pose_distance": _pair_distance(p7_matrix[index], cmc_matrix[index]),
            "compact_pose_distance": _pair_distance(p7_compact[index], cmc_compact[index]),
        })
    return {
        "schema_version": "pptl-paired-pose-ledger-v1",
        "target": target,
        "pair_count": len(pairs),
        "feature_arm": "P0",
        "feature_count": len(p7_names),
        "compact_pose_feature_count": compact_count,
        "feature_names": p7_names,
        "pairs": pairs,
        "policy": {
            "atom_maps_removed_before_matching": True,
            "paired_rows_are_diagnostic_only": True,
            "distance_is_feature_space_diagnostic_not_electron_density": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p7-records", type=Path, required=True)
    parser.add_argument("--cmcpor-records", type=Path, required=True)
    parser.add_argument("--p7-stage2p", type=Path, required=True)
    parser.add_argument("--cmcpor-stage2p", type=Path, required=True)
    parser.add_argument("--target", choices=("ee_percent", "isolated_yield_percent"), default="ee_percent")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_pose_pair_ledger(args.p7_records, args.cmcpor_records, args.p7_stage2p, args.cmcpor_stage2p, target=args.target)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pair_count": report["pair_count"], "feature_count": report["feature_count"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

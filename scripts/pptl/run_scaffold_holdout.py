#!/usr/bin/env python3
"""Run leakage-safe scaffold-held-out reciprocal transfer replays."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

from core import (
    GuardedEnsemble,
    _feature_alignment,
    _fit_target,
    _source_target_prediction,
    canonical_smiles,
    load_reaction_rows,
    predict_ridge,
    remove_canonical_overlap,
)


def scaffold_group(smiles: str) -> str:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"invalid SMILES for scaffold grouping: {smiles}")
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=molecule, includeChirality=False)
    return canonical_smiles(scaffold) if scaffold else "acyclic"


def run_scaffold_holdout(source, target, *, source_domain: str, target_name: str, arm: str = "B5", seed_size: int = 2, alpha: float = 10.0) -> list[dict]:
    active = [row for row in target if row.value(target_name) is not None]
    groups: dict[str, list] = defaultdict(list)
    for row in active:
        groups[scaffold_group(row.smiles)].append(row)
    source = remove_canonical_overlap(source, active)
    results: list[dict] = []
    for heldout_group in sorted(groups):
        heldout = sorted(groups[heldout_group], key=lambda row: row.source_order)
        train_pool = sorted([row for row in active if scaffold_group(row.smiles) != heldout_group], key=lambda row: row.source_order)
        if len(train_pool) <= seed_size:
            continue
        ensemble = GuardedEnsemble()
        for prefix_size in range(seed_size, len(train_pool)):
            train = train_pool[:prefix_size]
            fitted, names = _fit_target(train, target_name, arm, alpha)
            target_predictions = _feature_alignment(heldout, names, arm)
            target_values = predict_ridge(fitted, target_predictions)
            predictions = {"target_only": target_values}
            transfer = _source_target_prediction(source, train, heldout, target_name, arm, alpha)
            source_zero = transfer["source_zero_shot"]
            pooled = transfer.get("pooled_domain_indicator", source_zero)
            expert_predictions = {
                "target_only": target_values,
                "p7": source_zero if source_domain == "fe-p7-cl" else target_values,
                "cmcpor": source_zero if source_domain == "cmcpor-fecl" else target_values,
                "combined": pooled,
            }
            for index, row in enumerate(heldout):
                scalar_experts = {key: float(value[index]) for key, value in expert_predictions.items()}
                combined, before = ensemble.combine(scalar_experts)
                observed = float(row.value(target_name))
                update = ensemble.update(scalar_experts, observed)
                results.append({
                    "source_domain": source_domain,
                    "target_name": target_name,
                    "feature_arm": arm,
                    "heldout_scaffold": heldout_group,
                    "prefix_size": prefix_size,
                    "test_substrate_id": row.substrate_id,
                    "observed": observed,
                    "predictions": {key: float(value[index]) for key, value in expert_predictions.items()},
                    "ensemble_prediction_before_update": combined,
                    "weights_before_update": before,
                    "weights_after_update": update["weights"],
                    "ensemble_absolute_error": abs(combined - observed),
                })
    return results


def _metrics(rows: list[dict], key: str) -> dict[str, float | int | None]:
    if not rows:
        return {"count": 0, "mae": None}
    return {"count": len(rows), "mae": float(np.mean([abs(float(row["predictions"][key]) - float(row["observed"])) for row in rows]))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-records", type=Path, required=True)
    parser.add_argument("--target-records", type=Path, required=True)
    parser.add_argument("--source-catalyst", required=True)
    parser.add_argument("--target-catalyst", required=True)
    parser.add_argument("--source-family")
    parser.add_argument("--target-family")
    parser.add_argument("--source-stage2p", type=Path)
    parser.add_argument("--target-stage2p", type=Path)
    parser.add_argument("--source-catalyst-features", type=Path)
    parser.add_argument("--target-catalyst-features", type=Path)
    parser.add_argument("--target", choices=("ee_percent", "isolated_yield_percent"), default="ee_percent")
    parser.add_argument("--feature-arm", default="B5")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = load_reaction_rows(args.source_records, catalyst=args.source_catalyst, target=args.target, include_unlabelled=False, pose_features_path=args.source_stage2p, catalyst_features_path=args.source_catalyst_features)
    target = load_reaction_rows(args.target_records, catalyst=args.target_catalyst, target=args.target, include_unlabelled=True, pose_features_path=args.target_stage2p, catalyst_features_path=args.target_catalyst_features)
    if args.source_family:
        source = [row for row in source if row.family_id == args.source_family]
    if args.target_family:
        target = [row for row in target if row.family_id == args.target_family]
    rows = run_scaffold_holdout(source, target, source_domain=args.source_catalyst, target_name=args.target, arm=args.feature_arm)
    report = {
        "schema_version": "pptl-scaffold-holdout-report-v1",
        "source_domain": args.source_catalyst,
        "target_domain": args.target_catalyst,
        "target": args.target,
        "feature_arm": args.feature_arm,
        "scaffold_count": len({row["heldout_scaffold"] for row in rows}),
        "row_count": len(rows),
        "target_only": _metrics(rows, "target_only"),
        "active_source": _metrics(rows, "p7" if args.source_catalyst == "fe-p7-cl" else "cmcpor"),
        "combined": _metrics(rows, "combined"),
        "guarded_mae": float(np.mean([row["ensemble_absolute_error"] for row in rows])) if rows else None,
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("source_domain", "target_domain", "target", "feature_arm", "scaffold_count", "row_count", "target_only", "active_source", "combined", "guarded_mae")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

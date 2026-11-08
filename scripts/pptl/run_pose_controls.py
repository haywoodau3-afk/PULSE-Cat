#!/usr/bin/env python3
"""Run matched B5/Stage-2p/random/permuted pose controls in both directions."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from core import GuardedEnsemble, build_feature_matrix, canonical_overlap, fit_ridge, load_reaction_rows, predict_ridge, remove_canonical_overlap


def _replay(source, target, source_domain: str, target_name: str, *, seed: int = 20260901) -> dict[str, dict]:
    source = [row for row in source if row.value(target_name) is not None]
    target = [row for row in target if row.value(target_name) is not None]
    source = remove_canonical_overlap(source, target)
    source_b5, names = build_feature_matrix(source, "B5")
    target_b5, target_names = build_feature_matrix(target, "B5")
    source_pose, pose_names = build_feature_matrix(source, "P0")
    target_pose, target_pose_names = build_feature_matrix(target, "P0")
    source_compact_full, compact_names = build_feature_matrix(source, "P3")
    target_compact_full, target_compact_names = build_feature_matrix(target, "P3")
    if names != target_names or pose_names != target_pose_names:
        raise ValueError("source and target feature names do not align")
    if compact_names != target_compact_names:
        raise ValueError("source and target compact pose feature names do not align")
    compact_pose = source_compact_full[:, - (len(compact_names) - len(names)):]
    target_compact_pose = target_compact_full[:, - (len(compact_names) - len(names)):]
    rng = np.random.default_rng(seed)
    source_random = rng.normal(size=source_pose.shape)
    target_random = rng.normal(size=target_pose.shape)
    source_perm = source_pose[rng.permutation(len(source_pose))]
    target_perm = target_pose[rng.permutation(len(target_pose))]
    source_compact_random = rng.normal(size=compact_pose.shape)
    target_compact_random = rng.normal(size=target_compact_pose.shape)
    source_compact_perm = compact_pose[rng.permutation(len(compact_pose))]
    target_compact_perm = target_compact_pose[rng.permutation(len(target_compact_pose))]
    arms = {
        "B5": (source_b5, target_b5),
        "P2": (np.column_stack([source_b5, source_pose]), np.column_stack([target_b5, target_pose])),
        "P2_random": (np.column_stack([source_b5, source_random]), np.column_stack([target_b5, target_random])),
        "P2_permuted": (np.column_stack([source_b5, source_perm]), np.column_stack([target_b5, target_perm])),
        "P3": (source_compact_full, target_compact_full),
        "P3_random": (np.column_stack([source_b5, source_compact_random]), np.column_stack([target_b5, target_compact_random])),
        "P3_permuted": (np.column_stack([source_b5, source_compact_perm]), np.column_stack([target_b5, target_compact_perm])),
    }
    results = {}
    for arm, (source_X, target_X) in arms.items():
        source_y = np.asarray([row.value(target_name) for row in source], dtype=float)
        source_model = fit_ridge(source_X, source_y, 10.0)
        ensemble = GuardedEnsemble()
        rows = []
        for prefix_size in range(2, len(target)):
            train_X = target_X[:prefix_size]
            train_y = np.asarray([row.value(target_name) for row in target[:prefix_size]], dtype=float)
            test_X = target_X[prefix_size:prefix_size + 1]
            target_model = fit_ridge(train_X, train_y, 10.0)
            target_pred = float(predict_ridge(target_model, test_X)[0])
            source_pred = float(predict_ridge(source_model, test_X)[0])
            pooled_X = np.vstack([source_X, train_X])
            pooled_y = np.concatenate([source_y, train_y])
            domain = np.concatenate([np.zeros(len(source_X)), np.ones(len(train_X))])[:, None]
            pooled_model = fit_ridge(np.column_stack([pooled_X, domain]), pooled_y, 10.0)
            combined_pred = float(predict_ridge(pooled_model, np.column_stack([test_X, np.ones((1, 1))]))[0])
            predictions = {"target_only": target_pred, "p7": source_pred if source_domain == "fe-p7-cl" else target_pred, "cmcpor": source_pred if source_domain == "cmcpor-fecl" else target_pred, "combined": combined_pred}
            observed = float(target[prefix_size].value(target_name))
            guarded, weights = ensemble.combine(predictions)
            ensemble.update(predictions, observed)
            rows.append({"prefix_size": prefix_size, "observed": observed, "predictions": predictions, "ensemble_prediction_before_update": guarded, "ensemble_absolute_error": abs(guarded - observed), "weights_before_update": weights})
        def mae(key):
            return float(np.mean([abs(float(row["predictions"][key]) - float(row["observed"])) for row in rows]))
        results[arm] = {"target_only_mae": mae("target_only"), "guarded_mae": float(np.mean([row["ensemble_absolute_error"] for row in rows])), "combined_mae": mae("combined"), "row_count": len(rows), "rows": rows}
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p7-records", type=Path, required=True)
    parser.add_argument("--cmcpor-records", type=Path, required=True)
    parser.add_argument("--p7-stage2p", type=Path, required=True)
    parser.add_argument("--cmcpor-stage2p", type=Path, required=True)
    parser.add_argument("--target", choices=("ee_percent", "isolated_yield_percent"), default="ee_percent")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    p7 = load_reaction_rows(args.p7_records, catalyst="fe-p7-cl", target=args.target, include_unlabelled=True, pose_features_path=args.p7_stage2p)
    cmc = load_reaction_rows(args.cmcpor_records, catalyst="cmcpor-fecl", target=args.target, include_unlabelled=True, pose_features_path=args.cmcpor_stage2p)
    cmc_aryl = [row for row in cmc if row.family_id == "angew-aryl-c-h-amination"]
    result = {"schema_version": "pptl-pose-control-report-v1", "target": args.target, "canonical_overlap_count": len(canonical_overlap(p7, cmc_aryl)), "directions": {"p7_to_cmcpor_aryl": _replay(p7, cmc_aryl, "fe-p7-cl", args.target), "cmcpor_to_p7_aryl": _replay(cmc_aryl, p7, "cmcpor-fecl", args.target)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({direction: {arm: {key: value[key] for key in ("target_only_mae", "guarded_mae", "combined_mae", "row_count")} for arm, value in arms.items()} for direction, arms in result["directions"].items()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run reproducible random-route reciprocal progressive replays."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from core import build_feature_matrix, canonical_overlap, curve_metrics, fit_ridge, load_reaction_rows, predict_ridge, prediction_metrics, remove_canonical_overlap, run_fixed_prefix, GuardedEnsemble


def _random_order(rows, seed: int):
    rng = np.random.default_rng(seed)
    permutation = rng.permutation(len(rows))
    return [replace(rows[index], source_order=position) for position, index in enumerate(permutation)]


def _one_replicate(args):
    source, target, source_domain, target_name, arm, seed = args
    ordered = _random_order(target, seed)
    source_labelled = [row for row in source if row.value(target_name) is not None]
    source_X, source_names = build_feature_matrix(source_labelled, arm)
    source_y = np.asarray([row.value(target_name) for row in source_labelled], dtype=float)
    source_model = fit_ridge(source_X, source_y, 10.0)
    target_X, target_names = build_feature_matrix(ordered, arm)
    if source_names != target_names:
        positions = {name: index for index, name in enumerate(target_names)}
        source_X = np.column_stack([source_X[:, positions[name]] if name in positions else np.zeros(len(source_X)) for name in source_names])
    ensemble = GuardedEnsemble()
    replay = []
    for prefix_size in range(2, len(ordered)):
        train_X = target_X[:prefix_size]
        train_y = np.asarray([row.value(target_name) for row in ordered[:prefix_size]], dtype=float)
        target_model = fit_ridge(train_X, train_y, 10.0)
        test_X = target_X[prefix_size:prefix_size + 1]
        target_pred = float(predict_ridge(target_model, test_X)[0])
        source_pred = float(predict_ridge(source_model, test_X)[0])
        pooled_X = np.vstack([source_X, train_X])
        pooled_y = np.concatenate([source_y, train_y])
        pooled_domain = np.concatenate([np.zeros(len(source_X)), np.ones(len(train_X))])[:, None]
        pooled_model = fit_ridge(np.column_stack([pooled_X, pooled_domain]), pooled_y, 10.0)
        combined_pred = float(predict_ridge(pooled_model, np.column_stack([test_X, np.ones((1, 1))]))[0])
        expert_predictions = {"target_only": target_pred, "p7": source_pred if source_domain == "fe-p7-cl" else target_pred, "cmcpor": source_pred if source_domain == "cmcpor-fecl" else target_pred, "combined": combined_pred}
        observed = float(ordered[prefix_size].value(target_name))
        combined, weights = ensemble.combine(expert_predictions)
        ensemble.update(expert_predictions, observed)
        replay.append({"prefix_size": prefix_size, "predictions": expert_predictions, "observed": observed, "ensemble_prediction_before_update": combined, "ensemble_absolute_error": abs(combined - observed)})
    return {
        "seed": seed,
        "target_order": [row.substrate_id for row in ordered],
        "target_only": prediction_metrics(replay, "target_only"),
        "guarded": curve_metrics(replay),
    }


def _direction(source, target, *, source_domain: str, target_domain: str, target_name: str, arm: str, seeds: list[int], workers: int) -> dict:
    target = [row for row in target if row.value(target_name) is not None]
    source = remove_canonical_overlap(source, target)
    jobs = [(source, target, source_domain, target_name, arm, seed) for seed in seeds]
    if workers <= 1:
        replicates = [_one_replicate(job) for job in jobs]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            replicates = list(pool.map(_one_replicate, jobs))
    return {"source_domain": source_domain, "target_domain": target_domain, "target": target_name, "feature_arm": arm, "replicate_count": len(replicates), "replicates": replicates}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p7-records", type=Path, required=True)
    parser.add_argument("--cmcpor-records", type=Path, required=True)
    parser.add_argument("--p7-stage2p", type=Path)
    parser.add_argument("--cmcpor-stage2p", type=Path)
    parser.add_argument("--p7-catalyst-features", type=Path)
    parser.add_argument("--cmcpor-catalyst-features", type=Path)
    parser.add_argument("--target", choices=("ee_percent", "isolated_yield_percent"), default="ee_percent")
    parser.add_argument("--feature-arm", default="B1")
    parser.add_argument("--replicates", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260901)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    p7 = load_reaction_rows(args.p7_records, catalyst="fe-p7-cl", target=args.target, include_unlabelled=True, pose_features_path=args.p7_stage2p, catalyst_features_path=args.p7_catalyst_features)
    cmc = load_reaction_rows(args.cmcpor_records, catalyst="cmcpor-fecl", target=args.target, include_unlabelled=True, pose_features_path=args.cmcpor_stage2p, catalyst_features_path=args.cmcpor_catalyst_features)
    cmc_aryl = [row for row in cmc if row.family_id == "angew-aryl-c-h-amination"]
    seeds = [args.seed + index for index in range(args.replicates)]
    report = {
        "schema_version": "pptl-random-route-replicates-v1",
        "target": args.target,
        "feature_arm": args.feature_arm,
        "replicate_count": args.replicates,
        "seed_start": args.seed,
        "canonical_overlap_count": len(canonical_overlap(p7, cmc_aryl)),
        "directions": {
            "p7_to_cmcpor_aryl": _direction(p7, cmc_aryl, source_domain="fe-p7-cl", target_domain="cmcpor-fecl", target_name=args.target, arm=args.feature_arm, seeds=seeds, workers=args.workers),
            "cmcpor_to_p7_aryl": _direction(cmc_aryl, p7, source_domain="cmcpor-fecl", target_domain="fe-p7-cl", target_name=args.target, arm=args.feature_arm, seeds=seeds, workers=args.workers),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: {"replicate_count": value["replicate_count"]} for key, value in report["directions"].items()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Retrospective sensitivity of the acquisition score to its three weights.

Uses the R1.1 common held-out splits and shared starting pairs. The project
scoring code and datasets are read-only; only this revision folder is written.
"""
import csv
import hashlib
import itertools
import json
import math
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "reviewer1_comment1"
sys.path.insert(0, str(PREVIOUS))
import common_test_experiment as common  # noqa: E402
rr = common.rr
sp = common.sp
ROOT = rr.ROOT
DEST = HERE / "results" / "weight_sensitivity"
GRID_STEP = 0.20
DEFAULT = (0.40, 0.40, 0.20)  # diversity, uncertainty, family coverage
BUDGETS = (2, 6, 10, 15, 20)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def simplex_grid():
    # Integer tenths of 0.20 sum to five; sorted lexicographically for replay.
    vals = []
    for d in range(6):
        for u in range(6 - d):
            c = 5 - d - u
            vals.append((round(d * GRID_STEP, 2), round(u * GRID_STEP, 2), round(c * GRID_STEP, 2)))
    assert len(vals) == 21 and DEFAULT in vals
    return vals


def load_design(domain, table, active):
    base = PREVIOUS / "results" / "common_test" / domain
    id_to_index = {sid: i for i, sid in enumerate(table.ids)}
    active_ids = {table.ids[i] for i in active}
    split_rows = read_rows(base / "outer_splits.csv")
    pair_rows = read_rows(base / "initial_pairs.csv")
    pairs_by_split = defaultdict(list)
    for row in pair_rows:
        pairs_by_split[int(row["split_id"])].append(
            (int(row["pair_id"]), (id_to_index[row["substrate_1"]], id_to_index[row["substrate_2"]]))
        )
    design = []
    for row in split_rows:
        split_id = int(row["split_id"])
        test_ids = row["held_out_ids"].split("|")
        pool_ids = row["candidate_ids"].split("|")
        assert set(test_ids) <= active_ids and set(pool_ids) <= active_ids
        assert not set(test_ids) & set(pool_ids)
        test = [id_to_index[x] for x in test_ids]
        pool = [id_to_index[x] for x in pool_ids]
        pairs = pairs_by_split[split_id]
        assert len(pairs) == common.PAIRS_PER_SPLIT
        assert all(set(pair) <= set(pool) for _, pair in pairs)
        design.append((split_id, test, pool, pairs))
    assert len(design) == common.SPLITS
    return design


def simulate(table, X, y, pool, test, pair, weights, component_cache, prediction_cache):
    selected = list(pair)
    predictions = []
    maes = {}
    for n in range(2, max(BUDGETS) + 1):
        if n in BUDGETS:
            key = tuple(selected)
            pkey = (key, tuple(test))
            if pkey not in prediction_cache:
                rows = sp.audit_prediction_rows(
                    table, X, y, selected, test, "uncertainty_diversity", 0, "ee_percent", n
                )
                prediction_cache[pkey] = [r for r in rows if r["model"] == "ridge"]
            rows = prediction_cache[pkey]
            assert len(rows) == len(test)
            errors = []
            for row in rows:
                observed = float(row["observed_value"])
                predicted = float(row["predicted_value"])
                err = abs(observed - predicted)
                errors.append(err)
                predictions.append({
                    "n_labeled": n,
                    "substrate_id": row["substrate_id"],
                    "observed_ee": observed,
                    "predicted_ee": predicted,
                    "absolute_error": err,
                })
            maes[n] = statistics.mean(errors)
        if n == max(BUDGETS):
            break
        candidates = [i for i in pool if i not in selected]
        state_key = (tuple(selected), tuple(candidates))
        if state_key not in component_cache:
            _, components = sp.selection_components(
                table, X, y, selected, candidates, "uncertainty_diversity"
            )
            component_cache[state_key] = components
        components = component_cache[state_key]
        wd, wu, wc = weights
        score = (
            wd * components["diversity_score"]
            + wu * components["uncertainty_score"]
            + wc * components["family_coverage_score"]
        )
        chosen = candidates[max(
            range(len(candidates)),
            key=lambda i: (score[i], -table.rows[candidates[i]].source_order),
        )]
        selected.append(chosen)
    return predictions, statistics.mean(maes[n] for n in BUDGETS), selected


def main(domain):
    started = time.time()
    DEST.mkdir(parents=True, exist_ok=True)
    out = DEST / domain
    out.mkdir(exist_ok=True)
    table, active = rr.load(domain)
    design = load_design(domain, table, active)
    locked = set(rr.CONFIG[domain]["audit"])
    assert not locked & {table.ids[i] for i in active}
    expected_test = common.TEST_SIZES[domain]
    assert all(len(test) == expected_test for _, test, _, _ in design)
    if domain == "cmcpor":
        # The locked late-stage audit IDs are separate from this 26-record aryl set.
        assert len(active) == 26 and all(len(pool) == 21 for _, _, pool, _ in design)
    elif domain == "p7":
        assert len(active) == 38 and all(len(pool) == 32 for _, _, pool, _ in design)

    X = table.matrix(rr.FEATURE)
    y = np.asarray([
        sp.outcome_value(row.record, "ee_percent")
        if sp.outcome_value(row.record, "ee_percent") is not None else np.nan
        for row in table.rows
    ], dtype=float)
    grid = simplex_grid()
    grid_rows = [
        {"weight_id": i, "w_diversity": d, "w_uncertainty": u, "w_family_coverage": c,
         "is_default": (d, u, c) == DEFAULT}
        for i, (d, u, c) in enumerate(grid, 1)
    ]
    runs, predictions, sequences = [], [], []
    component_cache, prediction_cache = {}, {}
    for split_id, test, pool, pairs in design:
        for pair_id, pair in pairs:
            for weight_id, weights in enumerate(grid, 1):
                pred, mean_mae, selection = simulate(
                    table, X, y, pool, test, pair, weights, component_cache, prediction_cache
                )
                row = {
                    "domain": domain, "split_id": split_id, "pair_id": pair_id,
                    "weight_id": weight_id, "w_diversity": weights[0],
                    "w_uncertainty": weights[1], "w_family_coverage": weights[2],
                    "is_default": weights == DEFAULT, "mean_heldout_mae": mean_mae,
                }
                row.update({f"mae_at_{n}": next(
                    statistics.mean(p["absolute_error"] for p in pred if p["n_labeled"] == n)
                    for _ in [0]
                ) for n in BUDGETS})
                runs.append(row)
                sequences.append({
                    "domain": domain, "split_id": split_id, "pair_id": pair_id,
                    "weight_id": weight_id, "w_diversity": weights[0],
                    "w_uncertainty": weights[1], "w_family_coverage": weights[2],
                    "selected_ids_at_20": "|".join(table.ids[i] for i in selection),
                })
                for p in pred:
                    predictions.append({
                        "domain": domain, "split_id": split_id, "pair_id": pair_id,
                        "weight_id": weight_id, "w_diversity": weights[0],
                        "w_uncertainty": weights[1], "w_family_coverage": weights[2],
                        "is_default": weights == DEFAULT, **p,
                    })
        print(domain, "split", split_id, "/", len(design), "cached states", len(component_cache), flush=True)

    # Verify the base equation against the unchanged production implementation.
    first_split, test, pool, pairs = design[0]
    pair_id, pair = pairs[0]
    key = (tuple(pair), tuple(i for i in pool if i not in pair))
    comp = component_cache[key]
    legacy, _ = sp.selection_components(table, X, y, pair, [i for i in pool if i not in pair], "uncertainty_diversity")
    custom = (DEFAULT[0] * comp["diversity_score"] + DEFAULT[1] * comp["uncertainty_score"]
              + DEFAULT[2] * comp["family_coverage_score"])
    assert np.allclose(legacy, custom, atol=1e-12, rtol=0)
    # Also compare the complete default-weight path with the previously validated R1.1 simulator.
    old_pred, old_sequence = common.simulate(table, pool, test, pair, "uncertainty_diversity", 0)
    new_row = next(r for r in runs if r["split_id"] == first_split and r["pair_id"] == pair_id and r["is_default"])
    new_sequence = next(s for s in sequences if s["split_id"] == first_split and s["pair_id"] == pair_id and s["weight_id"] == new_row["weight_id"])
    assert [table.ids[i] for i in old_sequence] == new_sequence["selected_ids_at_20"].split("|")
    current_pred = [p for p in predictions if p["split_id"] == first_split and p["pair_id"] == pair_id and p["is_default"]]
    old_by = {(p["n_labeled"], p["substrate_id"]): float(p["predicted_value"]) for p in old_pred if p["model"] == "ridge"}
    new_by = {(p["n_labeled"], p["substrate_id"]): p["predicted_ee"] for p in current_pred}
    assert old_by.keys() == new_by.keys() and max(abs(old_by[k] - new_by[k]) for k in old_by) < 1e-10

    # Summarize each setting at pair and split levels; compare every setting to default.
    grouped = defaultdict(list)
    for row in runs:
        grouped[(row["split_id"], row["pair_id"], row["weight_id"])].append(row["mean_heldout_mae"])
    pair_mae = {key: statistics.mean(vals) for key, vals in grouped.items()}
    split_rows = []
    for split_id, *_ in design:
        for weight_id, weights in enumerate(grid, 1):
            values = [pair_mae[(split_id, pair_id, weight_id)] for pair_id, _ in pairs_by_id(design, split_id)]
            split_rows.append({
                "domain": domain, "split_id": split_id, "weight_id": weight_id,
                "w_diversity": weights[0], "w_uncertainty": weights[1],
                "w_family_coverage": weights[2], "mean_heldout_mae": statistics.mean(values),
            })
    split_by_weight = defaultdict(list)
    for row in split_rows:
        split_by_weight[row["weight_id"]].append(row["mean_heldout_mae"])
    default_id = grid.index(DEFAULT) + 1
    default_by_split = {row["split_id"]: row["mean_heldout_mae"] for row in split_rows if row["weight_id"] == default_id}
    weight_summaries = []
    for weight_id, weights in enumerate(grid, 1):
        vals = np.asarray(split_by_weight[weight_id], dtype=float)
        deltas = vals - np.asarray([default_by_split[i] for i in range(1, len(design) + 1)])
        weight_summaries.append({
            "domain": domain, "weight_id": weight_id, "w_diversity": weights[0],
            "w_uncertainty": weights[1], "w_family_coverage": weights[2],
            "is_default": weights == DEFAULT, "mean_split_mae": float(vals.mean()),
            "median_split_mae": float(np.median(vals)),
            "split_mae_q25": float(np.quantile(vals, .25)), "split_mae_q75": float(np.quantile(vals, .75)),
            "min_split_mae": float(vals.min()), "max_split_mae": float(vals.max()),
            "mean_paired_delta_vs_default": float(deltas.mean()),
            "median_paired_delta_vs_default": float(np.median(deltas)),
            "delta_q25_vs_default": float(np.quantile(deltas, .25)),
            "delta_q75_vs_default": float(np.quantile(deltas, .75)),
            "splits_default_lower_mae": int(np.sum(deltas > 0)),
            "splits_equal_mae": int(np.sum(np.isclose(deltas, 0, atol=1e-12))),
        })
    sorted_ids = [r["weight_id"] for r in sorted(weight_summaries, key=lambda r: (r["mean_split_mae"], r["weight_id"]))]
    for row in weight_summaries:
        row["mean_mae_rank_lowest_is_1"] = sorted_ids.index(row["weight_id"]) + 1

    seq_by_key = {(r["split_id"], r["pair_id"], r["weight_id"]): r["selected_ids_at_20"].split("|") for r in sequences}
    overlap_by_weight = defaultdict(list)
    for split_id, _, _, pairs in design:
        for pair_id, _ in pairs:
            base = set(seq_by_key[(split_id, pair_id, default_id)])
            for weight_id in range(1, len(grid) + 1):
                selected = set(seq_by_key[(split_id, pair_id, weight_id)])
                overlap_by_weight[weight_id].append(len(base & selected) / len(base | selected))
    for row in weight_summaries:
        overlaps = overlap_by_weight[row["weight_id"]]
        row["mean_selected_set_jaccard_at_20_vs_default"] = float(statistics.mean(overlaps))

    def write_csv(path, rows):
        if not rows:
            raise ValueError(f"no rows for {path}")
        with Path(path).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    write_csv(out / "weight_grid.csv", grid_rows)
    write_csv(out / "trajectory_results.csv", runs)
    write_csv(out / "split_results.csv", split_rows)
    write_csv(out / "weight_summary.csv", weight_summaries)
    write_csv(out / "selected_sets_at_20.csv", sequences)
    write_csv(out / "heldout_predictions.csv", predictions)
    metadata = {
        "domain": domain, "default_weights_diversity_uncertainty_coverage": DEFAULT,
        "grid_step": GRID_STEP, "n_weight_combinations": len(grid),
        "n_outer_splits": len(design), "n_initial_pairs_per_split": common.PAIRS_PER_SPLIT,
        "n_trajectories": len(runs), "label_budgets": BUDGETS,
        "test_size": expected_test, "active_records": len(active),
        "locked_audit_records_excluded": sorted(locked),
        "component_equations": {"D": "min-max normalized structural novelty",
                                "Q": "min-max normalized standard deviation of Ridge/Elastic Net/Tanimoto-kNN predictions",
                                "U": "0.5*D + 0.5*Q", "C": "normalized family coverage",
                                "S": "wD*D + wU*U + wC*C",
                                "default_expanded": "0.60*D + 0.20*Q + 0.20*C"},
        "validation": {"default_component_score_matches_legacy": True,
                       "default_first_trajectory_matches_r1c1_sequence_and_predictions": True,
                       "max_abs_default_prediction_difference": max(abs(old_by[k]-new_by[k]) for k in old_by)},
        "source_common_test_split_seed": common.SEEDS[domain],
        "input_sha256": {rr.CONFIG[domain][k]: sha(ROOT / rr.CONFIG[domain][k]) for k in ["records", "features", "archived"]},
        "original_code_sha256": sha(ROOT / "scripts/scope_progression.py"),
        "wrapper_sha256": sha(Path(__file__)), "python": sys.version,
        "numpy": np.__version__, "scikit_learn": rr.sklearn.__version__, "rdkit": rr.rdkit.__version__,
        "elapsed_seconds": time.time() - started,
        "limitations": "This is a descriptive retrospective weight-sensitivity analysis on fixed observed data. Outer test sets overlap; the 21-point grid is not used to select a policy; rankings are not independent validation or evidence of an optimum or population-level significance.",
    }
    (out / "summary.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"domain": domain, "elapsed_seconds": metadata["elapsed_seconds"],
                      "cache_states": len(component_cache), "summary": metadata["validation"]}, indent=2), flush=True)


def pairs_by_id(design, split_id):
    return next(pairs for sid, _, _, pairs in design if sid == split_id)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", choices=["p7", "cmcpor"], required=True)
    main(parser.parse_args().domain)

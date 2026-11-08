#!/usr/bin/env python3
"""Independently reconstruct and cross-check the weight-grid outputs."""
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "reviewer1_comment1"
sys.path.insert(0, str(PREVIOUS))
import initial_pair_replay as rr  # noqa: E402

BASE = HERE / "results" / "weight_sensitivity"
COMMON = PREVIOUS / "results" / "common_test"
BUDGETS = (2, 6, 10, 15, 20)


def read(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def close(a, b, tol=1e-10):
    return abs(float(a) - float(b)) <= tol


def validate(domain):
    path = BASE / domain
    preds = read(path / "heldout_predictions.csv")
    trajectories = read(path / "trajectory_results.csv")
    split_rows = read(path / "split_results.csv")
    summaries = read(path / "weight_summary.csv")
    sequences = read(path / "selected_sets_at_20.csv")
    common_preds = read(COMMON / domain / "predictions.csv")
    common_events = read(COMMON / domain / "selection_events.csv")
    raw_splits = read(COMMON / domain / "outer_splits.csv")
    raw_pairs = read(COMMON / domain / "initial_pairs.csv")
    splits = {int(r["split_id"]): set(r["held_out_ids"].split("|")) for r in raw_splits}
    pairs = {(int(r["split_id"]), int(r["pair_id"])) for r in raw_pairs}
    default_id = int(next(r["weight_id"] for r in summaries if r["is_default"] == "True"))

    byrun = defaultdict(list)
    ids_by_budget = defaultdict(set)
    for r in preds:
        k = (int(r["split_id"]), int(r["pair_id"]), int(r["weight_id"]), int(r["n_labeled"]))
        byrun[k].append(abs(float(r["observed_ee"]) - float(r["predicted_ee"])))
        ids_by_budget[k].add(r["substrate_id"])
    assert len(trajectories) == 20 * 3 * 21
    assert len(summaries) == 21 and len(split_rows) == 20 * 21
    assert len(sequences) == 20 * 3 * 21
    assert len(preds) == sum(len(splits[i]) * len(BUDGETS) * 3 * 21 for i in splits)
    for (split_id, pair_id, weight_id, budget), errors in byrun.items():
        assert (split_id, pair_id) in pairs and budget in BUDGETS
        assert len(errors) == len(splits[split_id])
        assert ids_by_budget[(split_id, pair_id, weight_id, budget)] == splits[split_id]
    trajectory_map = {(int(r["split_id"]), int(r["pair_id"]), int(r["weight_id"])): r for r in trajectories}
    for key, row in trajectory_map.items():
        budget_means = {n: statistics.mean(byrun[(*key, n)]) for n in BUDGETS}
        assert close(row["mean_heldout_mae"], statistics.mean(budget_means.values()))
        for n in BUDGETS:
            assert close(row[f"mae_at_{n}"], budget_means[n])

    # Recreate split aggregates from per-substrate predictions, without using
    # the experiment's trajectory or summary files as arithmetic inputs.
    bysplitweight = defaultdict(list)
    for split_id in splits:
        for pair_id in range(1, 4):
            for weight_id in range(1, 22):
                bysplitweight[(split_id, weight_id)].append(
                    statistics.mean(statistics.mean(byrun[(split_id, pair_id, weight_id, n)]) for n in BUDGETS)
                )
    split_map = {(int(r["split_id"]), int(r["weight_id"])): r for r in split_rows}
    for key, pair_values in bysplitweight.items():
        assert close(split_map[key]["mean_heldout_mae"], statistics.mean(pair_values))
    summary_map = {int(r["weight_id"]): r for r in summaries}
    for weight_id in range(1, 22):
        values = [float(split_map[(i, weight_id)]["mean_heldout_mae"]) for i in splits]
        assert close(summary_map[weight_id]["mean_split_mae"], statistics.mean(values))

    # The default route must match every R1.1 sequence and held-out prediction.
    old_events = defaultdict(list)
    for r in common_events:
        if r["route"] == "uncertainty_diversity":
            old_events[(int(r["split_id"]), int(r["pair_id"]))].append((int(r["step"]), r["substrate_id"]))
    seq_map = {(int(r["split_id"]), int(r["pair_id"]), int(r["weight_id"])): r["selected_ids_at_20"].split("|") for r in sequences}
    seq_matches = 0
    for split_id, pair_id in pairs:
        old = [sid for _, sid in sorted(old_events[(split_id, pair_id)])]
        new = seq_map[(split_id, pair_id, default_id)]
        assert old == new
        seq_matches += 1
    old_pred = {(int(r["split_id"]), int(r["pair_id"]), int(r["n_labeled"]), r["substrate_id"]): float(r["predicted_ee"])
                for r in common_preds if r["route"] == "uncertainty_diversity"}
    default_pred = {(int(r["split_id"]), int(r["pair_id"]), int(r["n_labeled"]), r["substrate_id"]): float(r["predicted_ee"])
                    for r in preds if int(r["weight_id"]) == default_id}
    assert old_pred.keys() == default_pred.keys()
    maxdiff = max(abs(old_pred[k] - default_pred[k]) for k in old_pred)
    assert maxdiff < 1e-10

    # The locked audit IDs are disjoint from active/test/candidate records.
    table, active = rr.load(domain)
    active_ids = {table.ids[i] for i in active}
    assert not active_ids.intersection(rr.CONFIG[domain]["audit"])
    assert set().union(*splits.values()) <= active_ids
    return {
        "domain": domain, "weight_combinations": len(summaries), "trajectories": len(trajectories),
        "heldout_predictions": len(preds), "split_weight_rows": len(split_rows),
        "default_sequences_matching_r1c1": seq_matches,
        "default_prediction_max_abs_difference": maxdiff,
        "heldout_membership_and_aggregate_reconstruction": "passed",
        "locked_audit_exclusion": "passed",
    }


def main():
    lines = ["# Weight-sensitivity validation", "", "The following checks were reconstructed from individual saved predictions and compared with the R1.1 common-test records:", ""]
    for domain in ("p7", "cmcpor"):
        result = validate(domain)
        lines.extend([f"## {result['domain']}", ""])
        for key, value in result.items():
            if key != "domain":
                lines.append(f"- {key.replace('_', ' ')}: {value}")
        lines.append("")
    out = HERE / "validation_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out.read_text(), end="")


if __name__ == "__main__":
    main()

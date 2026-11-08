#!/usr/bin/env python3
"""Calibrate transparent rule-based BDE priors against the existing xTB panel.

The rule feature system intentionally keeps its frozen priors unchanged.  This
script creates a separate, auditable calibration artifact: it joins the
reaction-centre rule estimates to the completed GFN2-xTB/ALPB(ether) site
calculations, reports raw and affine-corrected agreement, and selects a small
panel for a future higher-level reference calculation.

The xTB values are an interim computed reference, not a higher-level DFT
calibration.  The output therefore records the missing higher-level gate rather
than silently treating xTB as a final calibration standard.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import rule_based_diversity as rules  # noqa: E402
import scope_progression as baseline  # noqa: E402


SCHEMA_VERSION = "rule-bde-calibration-v1"
DEFAULT_PANEL_SIZE = 12


def fit_affine(rule_values: np.ndarray, reference_values: np.ndarray) -> tuple[float, float]:
    """Fit ``reference = intercept + slope * rule`` using finite pairs."""

    rule_values = np.asarray(rule_values, dtype=float)
    reference_values = np.asarray(reference_values, dtype=float)
    if rule_values.shape != reference_values.shape:
        raise ValueError("rule and reference arrays must have the same shape")
    valid = np.isfinite(rule_values) & np.isfinite(reference_values)
    if int(valid.sum()) == 0:
        raise ValueError("no finite rule/reference pairs")
    x = rule_values[valid]
    y = reference_values[valid]
    if len(x) < 2 or float(np.ptp(x)) == 0.0:
        return float(np.mean(y)), 0.0
    design = np.column_stack([np.ones(len(x)), x])
    intercept, slope = np.linalg.lstsq(design, y, rcond=None)[0]
    return float(intercept), float(slope)


def leave_one_group_out_affine(
    rule_values: np.ndarray,
    reference_values: np.ndarray,
    groups: Sequence[str],
) -> np.ndarray:
    """Predict each reference value from an affine fit that excludes its group."""

    rule_values = np.asarray(rule_values, dtype=float)
    reference_values = np.asarray(reference_values, dtype=float)
    if rule_values.shape != reference_values.shape or len(groups) != len(rule_values):
        raise ValueError("rule, reference, and group arrays must have matching lengths")
    predictions = np.full(reference_values.shape, np.nan, dtype=float)
    group_values = np.asarray([str(group) for group in groups], dtype=object)
    for group in sorted(set(group_values.tolist())):
        held_out = group_values == group
        train = ~held_out & np.isfinite(rule_values) & np.isfinite(reference_values)
        test = held_out & np.isfinite(rule_values)
        if not np.any(test):
            continue
        if not np.any(train):
            predictions[test] = float(np.nanmean(reference_values))
            continue
        intercept, slope = fit_affine(rule_values[train], reference_values[train])
        predictions[test] = intercept + slope * rule_values[test]
    return predictions


def regression_metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float | None]:
    """Return finite-pair MAE, RMSE, bias, and Pearson correlation."""

    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    valid = np.isfinite(observed) & np.isfinite(predicted)
    if int(valid.sum()) == 0:
        return {"n": 0, "mae": None, "rmse": None, "bias": None, "pearson_r": None}
    residual = predicted[valid] - observed[valid]
    pearson: float | None = None
    if int(valid.sum()) >= 2 and np.ptp(observed[valid]) > 0 and np.ptp(predicted[valid]) > 0:
        pearson = float(np.corrcoef(observed[valid], predicted[valid])[0, 1])
    return {
        "n": int(valid.sum()),
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "bias": float(np.mean(residual)),
        "pearson_r": pearson,
    }


def deterministic_rank(values: Sequence[float], keys: Sequence[str]) -> dict[str, int]:
    """Assign one-based deterministic ranks, breaking ties by stable key."""

    order = sorted(range(len(values)), key=lambda index: (float(values[index]), str(keys[index])))
    return {str(keys[index]): rank for rank, index in enumerate(order, start=1)}


def rank_metrics(pairs: Sequence[dict[str, Any]]) -> dict[str, float | int | None]:
    """Compare rule and xTB within-substrate site ordering."""

    by_substrate: dict[str, list[dict[str, Any]]] = {}
    for pair in pairs:
        by_substrate.setdefault(str(pair["substrate_id"]), []).append(pair)
    exact = 0
    within_one = 0
    total = 0
    rank_deltas: list[float] = []
    for substrate_id, substrate_pairs in sorted(by_substrate.items()):
        keys = [f"{substrate_id}:{pair['atom_map_id']}" for pair in substrate_pairs]
        rule_ranks = deterministic_rank([pair["rule_estimated_bde"] for pair in substrate_pairs], keys)
        xtb_ranks = deterministic_rank([pair["reference_xtb_bde"] for pair in substrate_pairs], keys)
        for key in keys:
            delta = rule_ranks[key] - xtb_ranks[key]
            exact += int(delta == 0)
            within_one += int(abs(delta) <= 1)
            rank_deltas.append(float(delta))
            total += 1
    if not total:
        return {"substrates": 0, "sites": 0, "exact_rank_agreement": None, "within_one_rank_agreement": None, "mean_rank_delta": None}
    return {
        "substrates": len(by_substrate),
        "sites": total,
        "exact_rank_agreement": float(exact / total),
        "within_one_rank_agreement": float(within_one / total),
        "mean_rank_delta": float(np.mean(rank_deltas)),
    }


def collect_pairs(
    records: Sequence[dict[str, Any]],
    xtb_records: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Join each rule candidate site to its completed xTB value by atom map."""

    xtb_by_id = {str(record["substrate_id"]): record for record in xtb_records}
    rule_table = rules.build_rule_feature_table(records)
    pairs: list[dict[str, Any]] = []
    for row in rule_table.rows:
        reference = xtb_by_id.get(row.substrate_id)
        if reference is None:
            continue
        reference_sites = {
            int(site["atom_map_id"]): site
            for site in reference.get("candidate_site_records", [])
            if site.get("status") == "completed" and site.get("atom_map_id") is not None and site.get("absolute_intrinsic_c_h_bde") is not None
        }
        for site in row.sites:
            atom_map_id = site.get("atom_map_id")
            if atom_map_id is None or int(atom_map_id) not in reference_sites:
                continue
            reference_site = reference_sites[int(atom_map_id)]
            pairs.append(
                {
                    "substrate_id": row.substrate_id,
                    "family_id": row.family_id,
                    "pathway_id": row.pathway_id,
                    "atom_map_id": int(atom_map_id),
                    "site_id": str(reference_site.get("site_id", f"{row.substrate_id}-c{atom_map_id}")),
                    "site_type": str(site.get("site_type", reference_site.get("site_type", "unknown"))),
                    "is_target_site": bool(row.target_atom_map_id == int(atom_map_id)),
                    "rule_estimated_bde": float(site["estimated_bde"]),
                    "rule_bde_class": str(site.get("bde_class", "unknown")),
                    "reference_xtb_bde": float(reference_site["absolute_intrinsic_c_h_bde"]),
                    "xtb_within_substrate_rank": int(reference_site.get("within_substrate_bde_rank", 0)),
                    "rule_bde_confidence": str(site.get("bde_confidence", "unknown")),
                }
            )
    return pairs


def select_panel(pairs: Sequence[dict[str, Any]], panel_size: int) -> list[dict[str, Any]]:
    """Select a deterministic rule-only panel spanning site and prior classes."""

    if panel_size <= 0:
        return []
    remaining = list(pairs)
    selected: list[dict[str, Any]] = []
    represented: dict[str, set[str]] = {"site_type": set(), "bde_class": set(), "target": set(), "family": set()}
    while remaining and len(selected) < panel_size:
        def score(pair: dict[str, Any]) -> tuple[float, float, str, int]:
            target_key = "target" if pair["is_target_site"] else "competitor"
            novelty = (
                3.0 * float(pair["site_type"] not in represented["site_type"])
                + 2.0 * float(pair["rule_bde_class"] not in represented["bde_class"])
                + 2.0 * float(target_key not in represented["target"])
                + 1.0 * float(pair["family_id"] not in represented["family"])
            )
            separation = 0.0
            if selected:
                separation = min(
                    abs(float(pair["rule_estimated_bde"]) - float(previous["rule_estimated_bde"]))
                    for previous in selected
                ) / 10.0
            return (novelty + min(separation, 1.0), -float(pair["rule_estimated_bde"]), str(pair["substrate_id"]), int(pair["atom_map_id"]))

        chosen = max(remaining, key=score)
        remaining.remove(chosen)
        selected.append(chosen)
        represented["site_type"].add(str(chosen["site_type"]))
        represented["bde_class"].add(str(chosen["rule_bde_class"]))
        represented["target"].add("target" if chosen["is_target_site"] else "competitor")
        represented["family"].add(str(chosen["family_id"]))
    return selected


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report(pairs: Sequence[dict[str, Any]], panel_size: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rule_values = np.asarray([pair["rule_estimated_bde"] for pair in pairs], dtype=float)
    reference_values = np.asarray([pair["reference_xtb_bde"] for pair in pairs], dtype=float)
    groups = [str(pair["substrate_id"]) for pair in pairs]
    intercept, slope = fit_affine(rule_values, reference_values)
    corrected = intercept + slope * rule_values
    loo_corrected = leave_one_group_out_affine(rule_values, reference_values, groups)
    panel = select_panel(pairs, panel_size)
    panel_keys = {(pair["substrate_id"], pair["atom_map_id"]) for pair in panel}
    for index, pair in enumerate(panel, start=1):
        pair["panel_rank"] = index
        pair["calibration_role"] = "target_site" if pair["is_target_site"] else "competitor_site"
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": "interim_calibration_complete_against_gfn2_xtb",
        "scope": {
            "substrates": len({pair["substrate_id"] for pair in pairs}),
            "site_pairs": len(pairs),
            "selected_panel_sites": len(panel),
            "selected_panel_keys": [f"{substrate_id}:c{atom_map_id}" for substrate_id, atom_map_id in sorted(panel_keys)],
        },
        "rule_method": {
            "source": "rule_based_diversity.py",
            "bde_interpretation": "coarse ordinal prior, not a calculated energy",
            "versions_unchanged": ["v0", "v1", "v2", "v3", "v4", "v5", "v6"],
        },
        "interim_reference": {
            "method": "GFN2-xTB",
            "solvent": "ALPB(ether)",
            "definition": "substrate radical + H atom - substrate",
            "role": "interim computed reference for hard-rule prior",
        },
        "raw_rule_vs_xtb": {
            "regression": regression_metrics(reference_values, rule_values),
            "within_substrate_rank": rank_metrics(pairs),
        },
        "global_affine_correction": {
            "equation": "xtb_bde = intercept + slope * rule_bde",
            "intercept_kcal_mol": intercept,
            "slope": slope,
            "in_sample_regression": regression_metrics(reference_values, corrected),
        },
        "leave_one_substrate_out_affine": {
            "regression": regression_metrics(reference_values, loo_corrected),
            "grouping": "substrate_id",
        },
        "higher_level_gate": {
            "higher_level_reference_available": False,
            "status": "blocked_missing_higher_level_executable_and_reference_results",
            "required_next_step": "run the selected panel with one consistent higher-level reference method and compare rankings before claiming final BDE calibration",
        },
        "preservation": {
            "existing_xtb_feature_file_overwritten": False,
            "existing_rule_versions_overwritten": False,
        },
    }
    return summary, panel


def run(records_path: Path, xtb_path: Path, output_dir: Path, panel_size: int) -> dict[str, Any]:
    records = baseline.read_jsonl(records_path)
    xtb_records = baseline.read_jsonl(xtb_path)
    pairs = collect_pairs(records, xtb_records)
    if not pairs:
        raise ValueError("no completed rule/xTB candidate-site pairs were found")
    summary, panel = build_report(pairs, panel_size)
    pair_fields = [
        "substrate_id", "family_id", "pathway_id", "atom_map_id", "site_id", "site_type",
        "is_target_site", "rule_estimated_bde", "rule_bde_class", "reference_xtb_bde",
        "xtb_within_substrate_rank", "rule_bde_confidence",
    ]
    panel_fields = ["panel_rank", "calibration_role", *pair_fields]
    write_csv(output_dir / "bde-calibration-pairs.csv", pairs, pair_fields)
    write_csv(output_dir / "bde-calibration-panel.csv", panel, panel_fields)
    write_json(output_dir / "bde-calibration-summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--xtb-features", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--panel-size", type=int, default=DEFAULT_PANEL_SIZE)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    result = run(arguments.records, arguments.xtb_features, arguments.output_dir, arguments.panel_size)
    print(json.dumps({"status": result["status"], "scope": result["scope"]}, sort_keys=True))

#!/usr/bin/env python3
"""Compare matched P7 UFF and MMFF94 Stage 2p/2pp prediction errors."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy
from scipy.stats import wilcoxon


ROOT = Path(__file__).resolve().parents[2]
UFF_ROOT = ROOT / "data/jacs_2025"
MMFF_ROOT = ROOT / "data/jacs_2025_mmff94"
DEFAULT_OUTPUT = MMFF_ROOT / "model-comparison/uff-vs-mmff94.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def numeric(row: dict[str, str], field: str) -> float:
    return float(row[field])


def bootstrap_ci(values: numpy.ndarray, draws: int = 20_000, seed: int = 20260807) -> tuple[float, float]:
    generator = numpy.random.default_rng(seed)
    samples = generator.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    low, high = numpy.quantile(samples, [0.025, 0.975])
    return float(low), float(high)


def paired_summary(
    uff_rows: list[dict[str, str]],
    mmff_rows: list[dict[str, str]],
    key_fields: tuple[str, ...],
) -> dict[str, Any]:
    def keyed(rows: list[dict[str, str]]) -> dict[tuple[str, ...], dict[str, str]]:
        return {tuple(row[field] for field in key_fields): row for row in rows}

    uff = keyed(uff_rows)
    mmff = keyed(mmff_rows)
    keys = sorted(set(uff) & set(mmff))
    if not keys or set(uff) != set(mmff):
        raise ValueError("UFF and MMFF94 prediction rows do not share the same holdout cohort")
    uff_errors = numpy.asarray([numeric(uff[key], "abs_error") for key in keys], dtype=float)
    mmff_errors = numpy.asarray([numeric(mmff[key], "abs_error") for key in keys], dtype=float)
    deltas = mmff_errors - uff_errors
    ci_low, ci_high = bootstrap_ci(deltas)
    try:
        p_value = float(wilcoxon(deltas, alternative="two-sided", zero_method="wilcox").pvalue)
    except ValueError:
        p_value = 1.0
    return {
        "record_count": len(keys),
        "uff_mae": float(uff_errors.mean()),
        "mmff94_mae": float(mmff_errors.mean()),
        "mean_delta_mae_mmff94_minus_uff": float(deltas.mean()),
        "median_delta_abs_error_mmff94_minus_uff": float(numpy.median(deltas)),
        "bootstrap_95_ci_mean_delta": [ci_low, ci_high],
        "wilcoxon_two_sided_p_value": p_value,
        "mmff94_lower_abs_error_count": int((deltas < 0).sum()),
        "uff_lower_abs_error_count": int((deltas > 0).sum()),
        "tie_count": int((deltas == 0).sum()),
    }


def select_stage2p(path: Path, track: str, feature_set: str) -> list[dict[str, str]]:
    return [
        row
        for row in read_csv(path)
        if row["track"] == track and row["feature_set"] == feature_set
    ]


def select_stage2pp(path: Path, feature_set: str) -> list[dict[str, str]]:
    return [
        row
        for row in read_csv(path)
        if row["model_name"] == "elastic_net" and row["feature_set"] == feature_set
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    uff_stage2p = UFF_ROOT / "stage2/modeling/stage2p-predictions.csv"
    mmff_stage2p = MMFF_ROOT / "stage2p/modeling/stage2p-predictions.csv"
    uff_stage2pp = UFF_ROOT / "stage2pp/modeling/stage2pp-predictions.csv"
    mmff_stage2pp = MMFF_ROOT / "stage2pp/modeling/stage2pp-predictions.csv"
    result = {
        "schema_version": "p7-force-field-comparison-v1",
        "scope": {
            "catalyst": "P7-porphyrin",
            "generated_pool_size": 5000,
            "retained_pose_count": 200,
            "random_seed": 20260730,
            "baseline_force_field": "uff",
            "candidate_force_field": "mmff94",
        },
        "comparisons": {
            "stage2p_geometry_compatibility_loo": paired_summary(
                select_stage2p(uff_stage2p, "compatibility", "stage2p_geometry"),
                select_stage2p(mmff_stage2p, "compatibility", "stage2p_geometry"),
                ("substrate_id",),
            ),
            "stage2p_geometry_rigorous_nested_loo": paired_summary(
                select_stage2p(uff_stage2p, "rigorous_nested_loo", "stage2p_geometry"),
                select_stage2p(mmff_stage2p, "rigorous_nested_loo", "stage2p_geometry"),
                ("substrate_id",),
            ),
            "stage2pp_stage2p_elastic_net_family_holdout": paired_summary(
                select_stage2pp(uff_stage2pp, "stage2p"),
                select_stage2pp(mmff_stage2pp, "stage2p"),
                ("target_substrate_id", "split_id"),
            ),
            "stage2pp_augmented_elastic_net_family_holdout": paired_summary(
                select_stage2pp(uff_stage2pp, "stage2p_plus_stage2pp"),
                select_stage2pp(mmff_stage2pp, "stage2p_plus_stage2pp"),
                ("target_substrate_id", "split_id"),
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

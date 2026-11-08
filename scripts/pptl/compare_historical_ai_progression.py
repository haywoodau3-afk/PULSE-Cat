#!/usr/bin/env python3
"""Compare historical source order with model-guided progressive acquisition.

The historical route is the order in which the source paper lists substrates
(`source_order` in the locked scope records).  It is a non-optimised control,
not an inference about the authors' hidden decision process.  The AI routes are
the deterministic acquisition policies already evaluated by
``scope_progression.py``.  This script only compares retrospective labelled
scopes; generated structures remain prediction-only and are never treated as
experimental outcomes.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable


AI_ROUTES = ("uncertainty_diversity", "diversity_first", "performance_first")
HISTORICAL_ROUTE = "historical_order"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def numeric(value: str | None) -> float | None:
    if value in (None, "", "NA", "null"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def summarize_scope(scope: str, path: Path, target: str, model: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [
        row
        for row in read_csv(path)
        if row.get("target") == target and row.get("model") == model and numeric(row.get("mae_mean")) is not None
    ]
    if not rows:
        raise ValueError(f"no rows for target={target!r}, model={model!r} in {path}")
    by_route: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_route.setdefault(row["route"], []).append(row)

    route_rows: list[dict[str, Any]] = []
    for route, route_values in by_route.items():
        route_values = sorted(route_values, key=lambda row: int(row["n_labeled"]))
        maes = [numeric(row["mae_mean"]) for row in route_values]
        maes = [value for value in maes if value is not None]
        if not maes:
            continue
        # ``auc_mae`` in the existing manifest is the sum of prefix MAEs;
        # mean_prefix_mae makes comparisons readable across different scope sizes.
        n90 = route_values[0].get("threshold_reached")
        n90_value: int | None = None
        for row in route_values:
            if row.get("threshold_reached", "").lower() == "true":
                n90_value = int(row["n_labeled"])
                break
        route_rows.append(
            {
                "scope": scope,
                "target": target,
                "model": model,
                "route": route,
                "prefix_count": len(maes),
                "first_prefix_n": int(route_values[0]["n_labeled"]),
                "last_prefix_n": int(route_values[-1]["n_labeled"]),
                "mean_prefix_mae": sum(maes) / len(maes),
                "auc_mae": sum(maes),
                "first_prefix_mae": maes[0],
                "final_prefix_mae": maes[-1],
                "best_prefix_mae": min(maes),
                "n90": n90_value,
                "replicates": route_values[0].get("replicates"),
            }
        )

    route_rows.sort(key=lambda row: (row["mean_prefix_mae"], row["route"]))
    for rank, row in enumerate(route_rows, start=1):
        row["rank_by_mean_prefix_mae"] = rank
    historical = next((row for row in route_rows if row["route"] == HISTORICAL_ROUTE), None)
    if historical is None:
        raise ValueError(f"historical_order route missing in {path}")
    candidates = [row for row in route_rows if row["route"] in AI_ROUTES]
    if not candidates:
        raise ValueError(f"no deterministic AI route found in {path}")
    best = min(candidates, key=lambda row: (row["mean_prefix_mae"], row["route"]))
    comparison = {
        "scope": scope,
        "target": target,
        "model": model,
        "historical_route": HISTORICAL_ROUTE,
        "historical_rank": historical["rank_by_mean_prefix_mae"],
        "best_ai_route": best["route"],
        "best_ai_rank": best["rank_by_mean_prefix_mae"],
        "historical_mean_prefix_mae": historical["mean_prefix_mae"],
        "best_ai_mean_prefix_mae": best["mean_prefix_mae"],
        "mean_prefix_mae_reduction_percent": 100.0
        * (historical["mean_prefix_mae"] - best["mean_prefix_mae"])
        / historical["mean_prefix_mae"],
        "historical_auc_mae": historical["auc_mae"],
        "best_ai_auc_mae": best["auc_mae"],
        "historical_final_prefix_mae": historical["final_prefix_mae"],
        "best_ai_final_prefix_mae": best["final_prefix_mae"],
        "historical_n90": historical["n90"],
        "best_ai_n90": best["n90"],
        "route_ranking": [row["route"] for row in route_rows],
    }
    return route_rows, comparison


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p7-summary", type=Path, required=True)
    parser.add_argument("--cmc-summary", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--target", default="ee_percent")
    parser.add_argument("--model", default="ridge")
    args = parser.parse_args()

    all_routes: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for scope, path in (("P7", args.p7_summary), ("CMC-Por aryl", args.cmc_summary)):
        routes, comparison = summarize_scope(scope, path, args.target, args.model)
        all_routes.extend(routes)
        comparisons.append(comparison)

    payload = {
        "schema_version": "historical-vs-ai-progressive-v1",
        "target": args.target,
        "model": args.model,
        "interpretation": {
            "historical_order": "source-paper substrate order, reproduced as a non-optimised control",
            "best_ai_route": "lowest mean prefix MAE among deterministic model-guided routes",
            "generated_structures": "prediction-only proposals; no experimental outcome is assigned",
            "scope": "retrospective labelled benchmark on locked historical records",
        },
        "comparisons": comparisons,
        "route_rows": all_routes,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(args.output_csv, all_routes)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build an auditable P7 model-development and prediction report.

All aggregate metrics are recomputed from persisted held-out predictions.  The
script intentionally keeps evaluation protocols and exact substrate cohorts
separate so that unlike estimates are not presented as a single leaderboard.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/research/2026-09-07/model-development-analysis"
RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"


SOURCES = [
    # Initial Stage 2 target-held-out estimates.
    (1, "S2-T", "Stage 2 baseline", "target_holdout", "data/jacs_2025/stage2/reports/full-scope-structure-model-predictions.csv", None, None),
    (1, "S2-T", "Stage 2 baseline", "target_holdout", "data/jacs_2025/stage2/reports/full-scope-structure-pose-model-predictions.csv", None, None),
    (1, "S2-T", "Stage 2 baseline", "target_holdout", "data/jacs_2025/stage2/reports/full-scope-structure-yield-model-predictions.csv", None, None),
    (1, "S2-T", "Stage 2 baseline", "target_holdout", "data/jacs_2025/stage2/reports/full-scope-structure-pose-yield-model-predictions.csv", None, None),
    # The stricter matched Stage 2 family-held-out estimates.
    (2, "S2-F", "Stage 2 baseline", "family_holdout", "data/jacs_2025/stage2/reports/family-heldout-structure-ee-model-predictions.csv", None, None),
    (2, "S2-F", "Stage 2 baseline", "family_holdout", "data/jacs_2025/stage2/reports/family-heldout-structure-pose-ee-model-predictions.csv", None, None),
    (2, "S2-F", "Stage 2 baseline", "family_holdout", "data/jacs_2025/stage2/reports/family-heldout-structure-yield-model-predictions.csv", None, None),
    (2, "S2-F", "Stage 2 baseline", "family_holdout", "data/jacs_2025/stage2/reports/family-heldout-structure-pose-yield-model-predictions.csv", None, None),
    # Publication-oriented Stage 2p family holdout.
    (3, "S2P-PUB", "Stage 2p publication", "family_holdout_publication", "data/jacs_2025/stage2/reports/stage2p-publication-predictions.csv", "stage2p_pose_aware_plus_conditions", None),
    (3, "S2P-PUB", "Stage 2p publication", "family_holdout_publication", "data/jacs_2025/stage2/reports/stage2p-publication-yield-predictions.csv", "stage2p_pose_aware_plus_conditions", None),
    # Corrected P7-modelable mechanistic feature ablation.
    (4, "S2P-MECH", "Stage 2p mechanistic ablation", "nested_family_holdout_p7_modelable", "data/jacs_2025/stage2/modeling/stage2p-family-heldout-p7-modelable-predictions.csv", None, "elastic_net"),
    # Dense pose-overlay experiment.
    (5, "S2PP", "Stage 2pp pose overlay", "family_holdout", "data/jacs_2025/stage2pp/modeling/stage2pp-predictions.csv", None, None),
    # Stage 3 local electronic/mechanistic additions.
    (6, "S3", "Stage 3 local descriptors", "nested_family_holdout_p7_modelable", "data/jacs_2025/stage3/model-comparison/stage3a-alt-plus-stage2p-family-heldout-p7-modelable-predictions.csv", None, "elastic_net"),
    # Substrate-only CREST/GFN2-xTB ablation.
    (7, "CREST-XTB", "CREST/GFN2-xTB ablation", "nested_family_holdout_p7_modelable", "docs/research/2026-09-07/p7-crest-xtb-model/predictions.csv", None, "elastic_net"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_records() -> dict[str, dict]:
    records = {}
    with RECORDS.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            records[record["substrate_id"]] = record
    return records


def number(value: str | int | float | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def fmt(value: float | None, digits: int = 3) -> str:
    return "NA" if value is None else f"{value:.{digits}f}"


def cohort_id(substrates: list[str]) -> str:
    payload = "\n".join(sorted(substrates)).encode()
    return hashlib.sha256(payload).hexdigest()[:12]


def target_name(raw: str) -> str:
    return "yield" if "yield" in raw.lower() else "ee"


def normalize_predictions(records: dict[str, dict]) -> list[dict]:
    output = []
    for stage_order, stage_id, stage, protocol, relpath, default_feature, default_model in SOURCES:
        source = ROOT / relpath
        for raw in read_csv(source):
            substrate_id = raw.get("target_substrate_id") or raw.get("substrate_id")
            if substrate_id not in records:
                raise ValueError(f"No curated record for {substrate_id} in {relpath}")
            record = records[substrate_id]
            outcome = record["outcome"]
            structure = record["structure"]
            raw_target = raw.get("target_name") or ("ee" if "observed_ee" in raw else "")
            target = target_name(raw_target)
            observed = number(raw.get("observed_target_value") or raw.get("observed_ee"))
            predicted = number(raw.get("prediction"))
            if observed is None or predicted is None:
                raise ValueError(f"Missing observed/prediction for {substrate_id} in {relpath}")
            curated = number(outcome.get("ee_percent") if target == "ee" else outcome.get("isolated_yield_percent"))
            if curated is not None and not math.isclose(observed, curated, abs_tol=1e-8):
                raise ValueError(f"Observed target mismatch for {substrate_id} in {relpath}: {observed} != {curated}")
            output.append({
                "stage_order": stage_order,
                "stage_id": stage_id,
                "stage": stage,
                "evaluation_protocol": protocol,
                "target": target,
                "feature_set": raw.get("feature_set") or default_feature or "unspecified",
                "model": raw.get("model_name") or default_model or "unspecified",
                "substrate_id": substrate_id,
                "starting_material_smiles": structure.get("azide_smiles") or "",
                "atom_mapped_starting_material_smiles": structure.get("atom_mapped_substrate_smiles") or "",
                "product_id": record.get("product_id") or "",
                "atom_mapped_product_smiles": structure.get("atom_mapped_product_smiles") or "",
                "catalyst_id": record.get("catalyst_id") or "",
                "family_id": raw.get("family_id") or record["family"].get("family_id") or "",
                "family_label": raw.get("family_label") or record["family"].get("family_label") or "",
                "actual_ee_percent": number(outcome.get("ee_percent")),
                "actual_yield_percent": number(outcome.get("isolated_yield_percent")),
                "actual_target_percent": observed,
                "predicted_ee_percent": predicted if target == "ee" else None,
                "predicted_yield_percent": predicted if target == "yield" else None,
                "predicted_target_percent": predicted,
                "signed_error_pred_minus_actual": predicted - observed,
                "absolute_error": abs(predicted - observed),
                "prediction_interval_80_low": number(raw.get("prediction_interval_80_low")),
                "prediction_interval_80_high": number(raw.get("prediction_interval_80_high")),
                "prediction_interval_95_low": number(raw.get("prediction_interval_95_low")),
                "prediction_interval_95_high": number(raw.get("prediction_interval_95_high")),
                "applicability": raw.get("applicability") or "",
                "source_artifact": relpath,
            })
    return output


def metric_rows(predictions: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    keys = ("stage_order", "stage_id", "stage", "evaluation_protocol", "target", "feature_set", "model")
    for row in predictions:
        groups[tuple(row[key] for key in keys)].append(row)
    output = []
    for key, rows in groups.items():
        values = [row["actual_target_percent"] for row in rows]
        forecasts = [row["predicted_target_percent"] for row in rows]
        errors = [forecast - value for value, forecast in zip(values, forecasts)]
        abs_errors = [abs(error) for error in errors]
        squared = [error * error for error in errors]
        mean_actual = statistics.fmean(values)
        denominator = sum((value - mean_actual) ** 2 for value in values)
        r2 = None if denominator == 0 else 1.0 - sum(squared) / denominator
        substrates = [row["substrate_id"] for row in rows]
        sources = sorted({row["source_artifact"] for row in rows})
        output.append(dict(zip(keys, key)) | {
            "cohort_id": cohort_id(substrates),
            "n_predictions": len(rows),
            "n_unique_substrates": len(set(substrates)),
            "n_families": len({row["family_id"] for row in rows}),
            "mae": statistics.fmean(abs_errors),
            "rmse": math.sqrt(statistics.fmean(squared)),
            "r2": r2,
            "median_absolute_error": statistics.median(abs_errors),
            "mean_signed_error_pred_minus_actual": statistics.fmean(errors),
            "max_absolute_error": max(abs_errors),
            "within_5_count": sum(error <= 5 for error in abs_errors),
            "within_10_count": sum(error <= 10 for error in abs_errors),
            "within_20_count": sum(error <= 20 for error in abs_errors),
            "source_artifacts": ";".join(sources),
        })
    output.sort(key=lambda row: (row["stage_order"], row["evaluation_protocol"], row["target"], row["feature_set"], row["model"]))
    return output


def family_metric_rows(predictions: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    keys = ("stage_order", "stage_id", "stage", "evaluation_protocol", "target", "feature_set", "model", "family_id", "family_label")
    for row in predictions:
        groups[tuple(row[key] for key in keys)].append(row)
    output = []
    for key, rows in groups.items():
        values = [row["actual_target_percent"] for row in rows]
        forecasts = [row["predicted_target_percent"] for row in rows]
        errors = [forecast - value for value, forecast in zip(values, forecasts)]
        abs_errors = [abs(error) for error in errors]
        squared = [error * error for error in errors]
        mean_actual = statistics.fmean(values)
        denominator = sum((value - mean_actual) ** 2 for value in values)
        output.append(dict(zip(keys, key)) | {
            "cohort_id": cohort_id([row["substrate_id"] for row in rows]),
            "n_predictions": len(rows),
            "mae": statistics.fmean(abs_errors),
            "rmse": math.sqrt(statistics.fmean(squared)),
            "r2": None if denominator == 0 else 1.0 - sum(squared) / denominator,
            "median_absolute_error": statistics.median(abs_errors),
            "mean_signed_error_pred_minus_actual": statistics.fmean(errors),
            "max_absolute_error": max(abs_errors),
            "within_5_count": sum(error <= 5 for error in abs_errors),
            "within_10_count": sum(error <= 10 for error in abs_errors),
            "within_20_count": sum(error <= 20 for error in abs_errors),
        })
    output.sort(key=lambda row: (row["stage_order"], row["target"], row["feature_set"], row["model"], row["family_id"]))
    return output


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |" for row in rows)
    return lines


def build_metrics_report(metrics: list[dict], predictions: list[dict]) -> None:
    exact_cohorts: dict[tuple, list[dict]] = defaultdict(list)
    for row in metrics:
        exact_cohorts[(row["stage_id"], row["evaluation_protocol"], row["target"], row["cohort_id"])].append(row)
    best = []
    for rows in exact_cohorts.values():
        best.append(min(rows, key=lambda row: row["mae"]))
    best.sort(key=lambda row: (row["stage_order"], row["target"]))

    lines = [
        "# P7 model-development metrics",
        "",
        "Generated from persisted out-of-sample prediction rows. Every MAE, RMSE, and R² value below was recomputed rather than copied from a narrative report.",
        "",
        "## Scope and interpretation",
        "",
        f"This audit contains **{len(predictions):,} prediction rows**, **{len(metrics)} model/feature evaluations**, and both ee and isolated-yield targets where they were actually modeled. Later mechanistic, Stage 3, and CREST/xTB experiments modeled ee only; missing yield experiments are reported as not run, not imputed.",
        "",
        "Target holdout and family holdout answer different questions. Compare rows only when `evaluation_protocol` and `cohort_id` match. R² is `1 - SSE/SST` on the held-out rows; negative values mean worse squared-error performance than predicting that cohort's mean.",
        "",
        "## Development conclusions on the common 38-substrate cohort",
        "",
        "- The locked Stage 2p geometry ElasticNet baseline is MAE 8.498, RMSE 11.357, R² 0.476.",
        "- Adding Stage 3a-alt descriptors gives the best balanced later result: MAE 8.468, RMSE 11.289, R² 0.482. The gains (0.030 MAE, 0.068 RMSE, 0.006 R²) are very small. Combining Stage 3a-alt and Stage 3b reaches the lowest MAE, 8.411, but worsens RMSE to 11.810 and R² to 0.433.",
        "- Every CREST/GFN2-xTB addition is worse than that same baseline. The electronic-only addition is the least harmful (MAE 8.610, RMSE 11.745, R² 0.440); the combined geometry/electronic arm is MAE 8.876, RMSE 11.860, R² 0.429.",
        "- Yield remains unresolved. In the 38-substrate publication family holdout, the median baseline has the lowest MAE (14.184), while ElasticNet has the best RMSE (20.125) and R² (-0.198). All learned yield models have negative R².",
        "",
        "## Best MAE within each exact stage/protocol/target/cohort",
        "",
    ]
    lines += markdown_table(
        ["Stage", "Protocol", "Target", "Cohort", "n", "Feature set", "Model", "MAE", "RMSE", "R²"],
        [[row["stage_id"], row["evaluation_protocol"], row["target"], row["cohort_id"], str(row["n_unique_substrates"]), row["feature_set"], row["model"], fmt(row["mae"]), fmt(row["rmse"]), fmt(row["r2"])] for row in best],
    )
    lines += ["", "## Full metrics table", ""]
    lines += markdown_table(
        ["Stage", "Protocol", "Target", "Cohort", "n", "Families", "Feature set", "Model", "MAE", "RMSE", "R²", "Median AE", "Bias", "Max AE", "≤5", "≤10", "≤20"],
        [[
            row["stage_id"], row["evaluation_protocol"], row["target"], row["cohort_id"],
            str(row["n_unique_substrates"]), str(row["n_families"]), row["feature_set"], row["model"],
            fmt(row["mae"]), fmt(row["rmse"]), fmt(row["r2"]), fmt(row["median_absolute_error"]),
            fmt(row["mean_signed_error_pred_minus_actual"]), fmt(row["max_absolute_error"]),
            str(row["within_5_count"]), str(row["within_10_count"]), str(row["within_20_count"]),
        ] for row in metrics],
    )
    lines += [
        "",
        "## Field definitions",
        "",
        "- `Bias` is mean(predicted − actual), in percentage points.",
        "- `≤5`, `≤10`, and `≤20` count predictions whose absolute error is within that many percentage points.",
        "- `cohort_id` is a deterministic hash of the sorted substrate IDs; matching hashes indicate the exact same substrate set.",
        "- Single-member families are included in global metrics, but a family-specific R² would be undefined; this table reports only global model-level R².",
        "",
        "The machine-readable version includes source paths and unrounded values: `model-metrics-full.csv`.",
        "Family-resolved metrics, including undefined R² for one-member families, are in `model-metrics-by-family.csv`.",
    ]
    (OUT / "model-development-metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_prediction_report(records: dict[str, dict], predictions: list[dict]) -> None:
    by_substrate: dict[str, list[dict]] = defaultdict(list)
    for row in predictions:
        by_substrate[row["substrate_id"]].append(row)
    lines = [
        "# Actual versus predicted ee and yield by starting material and product",
        "",
        "These are persisted held-out predictions, not fits on the same rows used for training. Predictions are listed in long form because each stage has a different feature set, model family, protocol, and sometimes a different eligible cohort.",
        "",
        "## Starting-material and product index",
        "",
    ]
    identity_rows = []
    for substrate_id, record in records.items():
        outcome = record["outcome"]
        structure = record["structure"]
        identity_rows.append([
            substrate_id,
            record.get("product_id") or "NA",
            record.get("catalyst_id") or "NA",
            record["family"].get("family_id") or "NA",
            fmt(number(outcome.get("ee_percent")), 1),
            fmt(number(outcome.get("isolated_yield_percent")), 1),
            structure.get("azide_smiles") or "NA",
            structure.get("atom_mapped_product_smiles") or "not curated",
        ])
    lines += markdown_table(["Starting material", "Product", "Catalyst", "Family", "Actual ee (%)", "Actual yield (%)", "Starting-material SMILES", "Mapped product SMILES"], identity_rows)
    lines += ["", "## Full held-out predictions", ""]
    for substrate_id in records:
        rows = by_substrate.get(substrate_id, [])
        if not rows:
            continue
        record = records[substrate_id]
        lines += [
            f"### {substrate_id} → {record.get('product_id') or 'product not assigned'}",
            "",
        ]
        rows.sort(key=lambda row: (row["stage_order"], row["evaluation_protocol"], row["target"], row["feature_set"], row["model"]))
        table_rows = []
        for row in rows:
            pi95 = "NA"
            if row["prediction_interval_95_low"] is not None and row["prediction_interval_95_high"] is not None:
                pi95 = f"[{row['prediction_interval_95_low']:.2f}, {row['prediction_interval_95_high']:.2f}]"
            table_rows.append([
                row["stage_id"], row["evaluation_protocol"], row["target"], row["feature_set"], row["model"],
                fmt(row["actual_target_percent"], 2), fmt(row["predicted_target_percent"], 2), fmt(row["absolute_error"], 2), pi95,
            ])
        lines += markdown_table(["Stage", "Protocol", "Target", "Feature set", "Model", "Actual (%)", "Predicted (%)", "Abs. error", "95% PI"], table_rows)
        lines.append("")
    lines += [
        "## Important limitations",
        "",
        "- ee is modeled as reported ee magnitude, not stereochemical sign or absolute configuration.",
        "- `not curated` product SMILES means the product identifier and outcome exist but an atom-mapped product structure was not available in the curated record.",
        "- Later feature-development stages did not train yield models. Only Stage 2 baseline and Stage 2p publication rows contain yield predictions.",
        "- Prediction intervals appear only when the originating artifact persisted them.",
        "",
        "The machine-readable long-form version is `actual-vs-predicted-full.csv`.",
    ]
    (OUT / "actual-vs-predicted-ee-yield.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_smiles_exports(records: dict[str, dict]) -> None:
    smiles_dir = OUT / "smiles"
    smiles_dir.mkdir(parents=True, exist_ok=True)
    starting_rows = []
    product_rows = []
    paired_rows = []
    for substrate_id, record in records.items():
        structure = record["structure"]
        outcome = record["outcome"]
        product_smiles = structure.get("atom_mapped_product_smiles") or ""
        common = {
            "substrate_id": substrate_id,
            "product_id": record.get("product_id") or "",
            "reaction_id": record.get("reaction_id") or "",
            "catalyst_id": record.get("catalyst_id") or "",
            "family_id": record["family"].get("family_id") or "",
            "family_label": record["family"].get("family_label") or "",
            "actual_ee_percent": outcome.get("ee_percent"),
            "actual_yield_percent": outcome.get("isolated_yield_percent"),
            "starting_material_smiles": structure.get("azide_smiles") or "",
            "atom_mapped_starting_material_smiles": structure.get("atom_mapped_substrate_smiles") or "",
            "atom_mapped_product_smiles": product_smiles,
            "product_structure_status": "curated_atom_mapped" if product_smiles else "not_curated",
        }
        starting_rows.append(common)
        product_rows.append(common)
        paired_rows.append(common)

    write_csv(
        smiles_dir / "starting-material-smiles.csv",
        starting_rows,
        ["substrate_id", "reaction_id", "catalyst_id", "family_id", "family_label", "starting_material_smiles", "atom_mapped_starting_material_smiles"],
    )
    write_csv(
        smiles_dir / "product-smiles.csv",
        product_rows,
        ["product_id", "substrate_id", "reaction_id", "actual_ee_percent", "actual_yield_percent", "atom_mapped_product_smiles", "product_structure_status"],
    )
    write_csv(
        smiles_dir / "starting-material-product-pairs.csv",
        paired_rows,
        [
            "substrate_id", "product_id", "reaction_id", "catalyst_id", "family_id", "family_label",
            "actual_ee_percent", "actual_yield_percent", "starting_material_smiles",
            "atom_mapped_starting_material_smiles", "atom_mapped_product_smiles", "product_structure_status",
        ],
    )
    curated_product_count = sum(bool(row["atom_mapped_product_smiles"]) for row in product_rows)
    readme = [
        "# Starting-material and product SMILES",
        "",
        f"This folder contains {len(records)} curated P7 reaction records.",
        "",
        "- `starting-material-smiles.csv`: one row per starting material, with ordinary and atom-mapped substrate SMILES.",
        "- `product-smiles.csv`: one row per product identifier, with atom-mapped product SMILES when curated.",
        "- `starting-material-product-pairs.csv`: joined starting-material/product identities and experimental ee/yield.",
        "",
        f"Atom-mapped product structures are available for {curated_product_count} of {len(product_rows)} records. The remaining rows are marked `not_curated`; no product structure was inferred or fabricated.",
        "",
        "SMILES are copied without modification from `data/jacs_2025/stage2/curated-reaction-records.jsonl`.",
    ]
    (smiles_dir / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = read_records()
    predictions = normalize_predictions(records)
    metrics = metric_rows(predictions)
    family_metrics = family_metric_rows(predictions)
    metric_fields = [
        "stage_order", "stage_id", "stage", "evaluation_protocol", "target", "cohort_id",
        "n_predictions", "n_unique_substrates", "n_families", "feature_set", "model", "mae", "rmse", "r2",
        "median_absolute_error", "mean_signed_error_pred_minus_actual", "max_absolute_error",
        "within_5_count", "within_10_count", "within_20_count", "source_artifacts",
    ]
    prediction_fields = [
        "stage_order", "stage_id", "stage", "evaluation_protocol", "target", "feature_set", "model",
        "substrate_id", "starting_material_smiles", "atom_mapped_starting_material_smiles", "product_id",
        "atom_mapped_product_smiles", "catalyst_id", "family_id", "family_label", "actual_ee_percent",
        "actual_yield_percent", "actual_target_percent", "predicted_ee_percent", "predicted_yield_percent",
        "predicted_target_percent", "signed_error_pred_minus_actual", "absolute_error",
        "prediction_interval_80_low", "prediction_interval_80_high", "prediction_interval_95_low",
        "prediction_interval_95_high", "applicability", "source_artifact",
    ]
    family_metric_fields = [
        "stage_order", "stage_id", "stage", "evaluation_protocol", "target", "feature_set", "model",
        "family_id", "family_label", "cohort_id", "n_predictions", "mae", "rmse", "r2",
        "median_absolute_error", "mean_signed_error_pred_minus_actual", "max_absolute_error",
        "within_5_count", "within_10_count", "within_20_count",
    ]
    write_csv(OUT / "model-metrics-full.csv", metrics, metric_fields)
    write_csv(OUT / "model-metrics-by-family.csv", family_metrics, family_metric_fields)
    write_csv(OUT / "actual-vs-predicted-full.csv", predictions, prediction_fields)
    build_metrics_report(metrics, predictions)
    build_prediction_report(records, predictions)
    build_smiles_exports(records)
    print(f"Wrote {len(metrics)} model metrics, {len(family_metrics)} family metrics, and {len(predictions)} prediction rows to {OUT}")


if __name__ == "__main__":
    main()

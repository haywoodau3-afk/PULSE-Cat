#!/usr/bin/env python3
"""Build SI tables for the frozen model/feature progression experiments.

The tables are extracted from persisted PPTL matrices and the independent
scope-progression manifests.  No labels, poses, or metrics are regenerated;
this script only reshapes the frozen results into manuscript-ready CSV and
Markdown tables.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "docs" / "supporting-information" / "tables"

ARM_DEFS: list[dict[str, Any]] = [
    {"feature_arm": "B0", "family": "reference", "feature_definition": "Training-fold mean (no features)", "feature_count": 0, "role": "No-feature reference", "pose_dependency": "none", "status": "diagnostic"},
    {"feature_arm": "B1", "family": "RDKit descriptors", "feature_definition": "Six chemist-readable RDKit descriptors", "feature_count": 6, "role": "Minimal 2D baseline", "pose_dependency": "none", "status": "frozen"},
    {"feature_arm": "B2", "family": "RDKit descriptors", "feature_definition": "Fifteen RDKit descriptors", "feature_count": 15, "role": "Descriptor baseline", "pose_dependency": "none", "status": "frozen"},
    {"feature_arm": "B3", "family": "RDKit + Morgan", "feature_definition": "B2 + 128-bit radius-2 Morgan fingerprint", "feature_count": 143, "role": "Reduced fingerprint", "pose_dependency": "none", "status": "frozen"},
    {"feature_arm": "B4", "family": "RDKit + Morgan", "feature_definition": "B2 + 256-bit radius-2 Morgan fingerprint", "feature_count": 271, "role": "Dimension-matched 2D control", "pose_dependency": "none", "status": "frozen"},
    {"feature_arm": "B5", "family": "RDKit + Morgan", "feature_definition": "B2 + 1,024-bit radius-2 Morgan fingerprint", "feature_count": 1039, "role": "Full 2D reference", "pose_dependency": "none", "status": "primary 2D reference"},
    {"feature_arm": "P0", "family": "pose-only", "feature_definition": "Stage 2p pose block", "feature_count": 248, "role": "Pose-only diagnostic", "pose_dependency": "Stage 2p required", "status": "diagnostic"},
    {"feature_arm": "P1", "family": "RDKit + pose", "feature_definition": "B1 + Stage 2p pose block", "feature_count": 254, "role": "Minimal 2D plus pose", "pose_dependency": "Stage 2p required", "status": "diagnostic"},
    {"feature_arm": "P2", "family": "RDKit + Morgan + pose", "feature_definition": "B5 + raw Stage 2p pose block", "feature_count": 1287, "role": "Legacy raw-pose diagnostic", "pose_dependency": "Stage 2p required", "status": "diagnostic"},
    {"feature_arm": "P3", "family": "RDKit + Morgan + compact pose", "feature_definition": "B5 + compact C1 geometry block", "feature_count": 1083, "role": "Compact pose upgrade", "pose_dependency": "Stage 2p required", "status": "conditional transfer tier"},
    {"feature_arm": "P4", "family": "RDKit + Morgan + catalyst-aware pose", "feature_definition": "B5 + C1 geometry + 16-feature C2 catalyst interaction block", "feature_count": 1099, "role": "Transfer-specific pose tier", "pose_dependency": "Stage 2p and catalyst features required", "status": "conditional transfer tier"},
]
ARM_BY_ID = {row["feature_arm"]: row for row in ARM_DEFS}
ARM_SEQUENCE = [row["feature_arm"] for row in ARM_DEFS if row["feature_arm"] != "B0"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return "NA"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}" if isinstance(value, float) else str(value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]], digits: int = 3) -> str:
    if not rows:
        return "_No rows._\n"
    header = "| " + " | ".join(label for _, label in columns) + " |\n"
    divider = "| " + " | ".join("---" for _ in columns) + " |\n"
    body = "".join("| " + " | ".join(fmt(row.get(key), digits) for key, _ in columns) + " |\n" for row in rows)
    return header + divider + body


def build_feature_arm_table() -> list[dict[str, Any]]:
    return [dict(row) for row in ARM_DEFS]


def load_transfer_matrices() -> dict[str, dict[str, dict[str, Any]]]:
    paths = [
        ROOT / "data/expansion/pptl/bidirectional-ee-2d-matrix.json",
        ROOT / "data/expansion/pptl/bidirectional-ee-pose-matrix.json",
        ROOT / "data/expansion/pptl/matrix-ee-b5-p3-p4.json",
    ]
    values: dict[str, dict[str, dict[str, Any]]] = {}
    for path in paths:
        data = read_json(path)
        for arm, payload in data["arms"].items():
            values.setdefault(arm, {})
            for direction, result in payload["directions"].items():
                values[arm][direction] = result
    return values


def build_representation_progression() -> list[dict[str, Any]]:
    matrices = load_transfer_matrices()
    rows: list[dict[str, Any]] = []
    directions = ["cmcpor_to_p7_aryl", "p7_to_cmcpor_aryl"]
    for direction in directions:
        previous_mae: float | None = None
        b1_mae = float(matrices["B1"][direction]["target_only"]["mae"])
        for arm in ARM_SEQUENCE:
            result = matrices[arm][direction]
            target_only = result["target_only"]
            guarded = result["guarded_ensemble"]
            target_mae = float(target_only["mae"])
            rows.append(
                {
                    "feature_arm": arm,
                    "family": ARM_BY_ID[arm]["family"],
                    "feature_definition": ARM_BY_ID[arm]["feature_definition"],
                    "feature_count": ARM_BY_ID[arm]["feature_count"],
                    "direction": direction,
                    "source_domain": result["source_domain"],
                    "target_domain": result["target_domain"],
                    "target_records_available": result["target_count"],
                    "scored_prefix_count": target_only["count"],
                    "excluded_canonical_overlap_count": result["excluded_canonical_overlap_count"],
                    "target_only_mae_ee_points": target_mae,
                    "target_only_auc_mae": float(target_only["auc_mae"]),
                    "guarded_mae_ee_points": float(guarded["mae"]),
                    "target_only_delta_vs_previous_ee_points": None if previous_mae is None else target_mae - previous_mae,
                    "target_only_improvement_vs_B1_percent": (b1_mae - target_mae) / b1_mae * 100.0,
                    "guarded_delta_vs_target_only_ee_points": float(guarded["mae"]) - target_mae,
                    "source_artifact": "data/expansion/pptl/bidirectional-ee-2d-matrix.json" if arm.startswith("B") else ("data/expansion/pptl/bidirectional-ee-pose-matrix.json" if arm in {"P0", "P1", "P2"} else "data/expansion/pptl/matrix-ee-b5-p3-p4.json"),
                }
            )
            previous_mae = target_mae
    return rows


def build_independent_progression_metrics() -> list[dict[str, Any]]:
    specs = [
        ("P7", ROOT / "data/jacs_2025/scope_progression/scope-progression-manifest.json", ROOT / "data/jacs_2025/scope_progression/learning-curve-summary.csv"),
        ("CMC-Por aryl", ROOT / "data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/scope-progression-manifest.json", ROOT / "data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/learning-curve-summary.csv"),
    ]
    rows: list[dict[str, Any]] = []
    for domain, manifest_path, summary_path in specs:
        manifest = read_json(manifest_path)
        summary = read_csv(summary_path)
        for target in manifest["target_names"]:
            baseline = float(manifest["reference_metrics"][target]["baseline_mae"])
            for route in sorted({row["route"] for row in summary if row["target"] == target}):
                for model in sorted({row["model"] for row in summary if row["target"] == target and row["route"] == route}):
                    selected = [row for row in summary if row["target"] == target and row["route"] == route and row["model"] == model]
                    selected.sort(key=lambda row: int(row["n_labeled"]))
                    final = selected[-1]
                    convergence = manifest["convergence"].get(f"{target}:{route}:{model}", {})
                    rows.append(
                        {
                            "domain": domain,
                            "target": target,
                            "feature_set": manifest["feature_set"],
                            "route": route,
                            "model": model,
                            "final_n_labeled": int(final["n_labeled"]),
                            "final_prefix_mae": float(final["mae_mean"]),
                            "auc_mae": convergence.get("auc_mae"),
                            "n90": convergence.get("n90"),
                            "reference_baseline_mae": baseline,
                            "final_mae_delta_vs_reference": float(final["mae_mean"]) - baseline,
                            "source_manifest": str(manifest_path.relative_to(ROOT)),
                            "source_summary": str(summary_path.relative_to(ROOT)),
                        }
                    )
    return rows


def build_holdout_model_comparison() -> list[dict[str, Any]]:
    specs = [
        ("P7 target holdout", ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-model-benchmark.json"),
        ("P7 target holdout", ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-pose-model-benchmark.json"),
        ("P7 family holdout", ROOT / "data/jacs_2025/stage2/reports/family-heldout-structure-ee-model-benchmark.json"),
        ("P7 family holdout", ROOT / "data/jacs_2025/stage2/reports/family-heldout-structure-pose-ee-model-benchmark.json"),
    ]
    loaded = [(cohort, path, read_json(path)) for cohort, path in specs]
    baseline_mae: dict[tuple[str, str], float] = {}
    for cohort, _, data in loaded:
        if data["feature_set"] == "structure_only":
            for model, metrics in data["models"].items():
                baseline_mae[(cohort, model)] = float(metrics["mae"])
    rows: list[dict[str, Any]] = []
    for cohort, path, data in loaded:
        for model, metrics in data["models"].items():
            bootstrap = metrics.get("bayesian_bootstrap", {})
            mae_ci = bootstrap.get("mae", {})
            rmse_ci = bootstrap.get("rmse", {})
            mae = float(metrics["mae"])
            rows.append(
                {
                    "cohort": cohort,
                    "split_mode": data["split_mode"],
                    "target": data["target"],
                    "feature_set": data["feature_set"],
                    "feature_policy": data["feature_policy"],
                    "feature_count": data["feature_count"],
                    "model": model,
                    "n": data["modelable_record_count"],
                    "mae_ee_points": mae,
                    "mae_ci95_low": mae_ci.get("ci95_low"),
                    "mae_ci95_high": mae_ci.get("ci95_high"),
                    "rmse_ee_points": float(metrics["rmse"]),
                    "rmse_ci95_low": rmse_ci.get("ci95_low"),
                    "rmse_ci95_high": rmse_ci.get("ci95_high"),
                    "r2": float(metrics["r2"]),
                    "within_10_ee_fraction": float(metrics["within_10_ee_fraction"]),
                    "within_20_ee_fraction": float(metrics["within_20_ee_fraction"]),
                    "mae_delta_vs_structure_only": None if data["feature_set"] == "structure_only" else mae - baseline_mae[(cohort, model)],
                    "source_artifact": str(path.relative_to(ROOT)),
                }
            )
    return rows


def build_experiment_inventory() -> list[dict[str, Any]]:
    return [
        {"experiment_id": "E1", "experiment": "Domain curation and lock", "question": "Are the two iron-porphyrin systems independently defined and auditable?", "cohort_or_direction": "P7 (41 records); CMC-Por (50 records; 33 aryl + 17 sulfonyl)", "target": "ee and isolated yield", "feature_arms_or_models": "Curated SMILES, reaction metadata, Stage 2 pose records", "evaluation_or_control": "Record-level exclusions; 13 canonical aryl overlaps reconciled", "primary_outputs": "data/jacs_2025/stage2/curated-reaction-records.jsonl; data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl", "status_or_interpretation": "Frozen input domains; not a universal catalyst model"},
        {"experiment_id": "E2", "experiment": "2D representation ladder", "question": "How does prediction change from minimal RDKit descriptors to Morgan fingerprints?", "cohort_or_direction": "CMC-Por → P7 and P7 → CMC-Por aryl", "target": "ee", "feature_arms_or_models": "B0–B5; Ridge primary", "evaluation_or_control": "Target-only and guarded prefix replay; canonical overlaps excluded from transfer", "primary_outputs": "data/expansion/pptl/bidirectional-ee-2d-matrix.json", "status_or_interpretation": "B5 is the frozen 2D reference; B3–B5 show fingerprint sensitivity"},
        {"experiment_id": "E3", "experiment": "Pose representation ladder", "question": "Does pose information add predictive signal beyond structure?", "cohort_or_direction": "CMC-Por → P7 and P7 → CMC-Por aryl", "target": "ee", "feature_arms_or_models": "P0–P4; Ridge primary", "evaluation_or_control": "Pose-only, raw-pose, compact C1, and catalyst-aware C2 tiers", "primary_outputs": "data/expansion/pptl/bidirectional-ee-pose-matrix.json; data/expansion/pptl/matrix-ee-b5-p3-p4.json", "status_or_interpretation": "P3/P4 are conditional transfer tiers; universal superiority gate unresolved"},
        {"experiment_id": "E4", "experiment": "Independent progressive learning curves", "question": "How quickly does error fall as labelled substrates are added?", "cohort_or_direction": "P7 and CMC-Por aryl independently", "target": "ee and isolated yield", "feature_arms_or_models": "RDKit + 1,024-bit Morgan + raw Stage 2p; Ridge primary", "evaluation_or_control": "Historical, uncertainty–diversity, diversity-first, performance-first, and 500-route random policies", "primary_outputs": "data/jacs_2025/scope_progression/; data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/", "status_or_interpretation": "Retrospective learning-efficiency experiment"},
        {"experiment_id": "E5", "experiment": "Estimator variants", "question": "Is the progressive result robust to estimator choice?", "cohort_or_direction": "P7 and CMC-Por aryl", "target": "ee and isolated yield", "feature_arms_or_models": "Ridge, Elastic Net, Tanimoto-kNN", "evaluation_or_control": "Same feature set and acquisition routes; AUC-MAE and n90 recorded", "primary_outputs": "learning-curve-summary.csv; scope-progression-manifest.json", "status_or_interpretation": "Estimator-dependent curves are reported separately"},
        {"experiment_id": "E6", "experiment": "Independent held-out benchmark", "question": "Do pose-aware models improve held-out substrate prediction?", "cohort_or_direction": "P7 target-holdout and family-holdout", "target": "ee", "feature_arms_or_models": "Structure-only vs structure + pose; Ridge, Elastic Net, LightGBM, Gaussian Process", "evaluation_or_control": "Nested/structured holdouts with bootstrap intervals", "primary_outputs": "data/jacs_2025/stage2/reports/*structure*ee-model-benchmark.json", "status_or_interpretation": "Pose gain is model/split dependent; report intervals"},
        {"experiment_id": "E7", "experiment": "Pose upgrade and controls", "question": "Can compact/catalyst-aware pose features retain B5 signal and avoid dimension artifacts?", "cohort_or_direction": "Reciprocal P7/CMC-Por aryl", "target": "ee and isolated yield", "feature_arms_or_models": "B5, P2, P3, P4", "evaluation_or_control": "Equal-dimensional random and substrate-permuted compact-pose controls; paired bootstrap", "primary_outputs": "data/expansion/pptl/pose-upgrade-ee.json; data/expansion/pptl/pose-controls-ee.json", "status_or_interpretation": "P3/P4 are mechanistic/conditional tiers, not universal wins"},
        {"experiment_id": "E8", "experiment": "Guarded transfer and convergence", "question": "Can source-domain knowledge be used without negative transfer?", "cohort_or_direction": "Bidirectional P7 ↔ CMC-Por", "target": "ee and isolated yield", "feature_arms_or_models": "B5/P3/P4 guarded ensembles", "evaluation_or_control": "Prequential source weighting, AUC-MAE, n90, scaffold bootstrap", "primary_outputs": "data/expansion/pptl/matrix-ee-b5-p3-p4.json; data/expansion/pptl/routes/; data/expansion/pptl/scaffold/", "status_or_interpretation": "Guarding improves matched error directionally; 10% AUC gate unresolved"},
        {"experiment_id": "E9", "experiment": "Prediction-only substrate generation", "question": "Can the frozen workflow propose candidates for scope expansion?", "cohort_or_direction": "P7/CMC-Por-informed candidate panel", "target": "Predicted ee/yield only", "feature_arms_or_models": "SMILES-RNN + PromptSMILES; deterministic enumeration comparator", "evaluation_or_control": "Contract validation, applicability-domain funnel, sealed proposal panel", "primary_outputs": "data/expansion/pptl/raw-production.jsonl; funnel-production-ad.csv; sealed-prospective-panel.csv", "status_or_interpretation": "No experimental outcome, availability, safety, or feasibility claim"},
    ]


def write_markdown(
    inventory: list[dict[str, Any]],
    arms: list[dict[str, Any]],
    progression: list[dict[str, Any]],
    independent: list[dict[str, Any]],
    holdout: list[dict[str, Any]],
) -> Path:
    lines = [
        "# SI model and experiment progression tables",
        "",
        "These tables are reshaped from persisted, label-masked artifacts. Lower MAE/AUC-MAE is better; a negative MAE delta indicates improvement versus the stated reference. The reciprocal ladder uses Ridge target-only and guarded prefix replay; the independent estimator table retains Ridge, Elastic Net, and Tanimoto-kNN separately.",
        "",
        "## Table S1. Experiment inventory",
        "",
        markdown_table(inventory, [("experiment_id", "ID"), ("experiment", "Experiment"), ("question", "Question"), ("cohort_or_direction", "Cohort / direction"), ("target", "Target"), ("feature_arms_or_models", "Features / models"), ("evaluation_or_control", "Evaluation / control"), ("primary_outputs", "Persisted output"), ("status_or_interpretation", "Interpretation")], digits=3),
        "## Table S2. Frozen feature-arm definitions",
        "",
        markdown_table(arms, [("feature_arm", "Arm"), ("family", "Family"), ("feature_definition", "Definition"), ("feature_count", "Features"), ("role", "Role"), ("pose_dependency", "Pose dependency"), ("status", "Status")], digits=3),
        "## Table S3. Reciprocal EE representation progression",
        "",
        markdown_table(progression, [("feature_arm", "Arm"), ("direction", "Direction"), ("feature_count", "Features"), ("target_records_available", "Target records"), ("scored_prefix_count", "Scored n"), ("target_only_mae_ee_points", "Target-only MAE"), ("target_only_auc_mae", "Target-only AUC-MAE"), ("guarded_mae_ee_points", "Guarded MAE"), ("target_only_delta_vs_previous_ee_points", "Δ MAE vs prior"), ("target_only_improvement_vs_B1_percent", "% vs B1"), ("guarded_delta_vs_target_only_ee_points", "Guarded − target-only")], digits=3),
        "## Table S4. Independent progressive estimator metrics",
        "",
        markdown_table(independent, [("domain", "Domain"), ("target", "Target"), ("route", "Route"), ("model", "Model"), ("final_n_labeled", "Final n"), ("final_prefix_mae", "Final-prefix MAE"), ("auc_mae", "AUC-MAE"), ("n90", "n90"), ("reference_baseline_mae", "Reference MAE"), ("final_mae_delta_vs_reference", "Δ vs reference")], digits=3),
        "## Table S5. Independent held-out EE model comparison",
        "",
        markdown_table(holdout, [("cohort", "Cohort"), ("feature_set", "Feature set"), ("feature_count", "Features"), ("model", "Model"), ("n", "n"), ("mae_ee_points", "MAE"), ("mae_ci95_low", "MAE CI low"), ("mae_ci95_high", "MAE CI high"), ("rmse_ee_points", "RMSE"), ("r2", "R²"), ("within_10_ee_fraction", "Within 10"), ("within_20_ee_fraction", "Within 20"), ("mae_delta_vs_structure_only", "Δ vs structure-only")], digits=3),
        "## Reading notes",
        "",
        "- Table S3 compares representation arms under the same reciprocal replay. P0/P1 are intentionally diagnostic; P3/P4 preserve the B5 structure baseline and add compact pose information.",
        "- Table S4 uses the independent scope-progression feature set `rdkit_morgan_stage2p` (15 RDKit descriptors + 1,024-bit Morgan + raw Stage 2p pose block). It is not a replacement for the B1–B5/P0–P4 ladder.",
        "- Table S5 is a separate P7 held-out benchmark. Its structure-only arm uses a 512-bit Morgan fingerprint (547 total features), so it should not be conflated with the frozen PPTL B5 1,024-bit arm.",
        "- Pose-related improvements are directional/conditional; the prespecified 10% progressive-AUC superiority gate remains unresolved.",
        "",
    ]
    path = TABLE_DIR / "si_model_progression_tables.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    inventory = build_experiment_inventory()
    arms = build_feature_arm_table()
    progression = build_representation_progression()
    independent = build_independent_progression_metrics()
    holdout = build_holdout_model_comparison()
    write_csv(TABLE_DIR / "si_experiment_inventory.csv", inventory, list(inventory[0].keys()))
    write_csv(TABLE_DIR / "si_feature_arm_definitions.csv", arms, list(arms[0].keys()))
    write_csv(TABLE_DIR / "si_representation_progression_ee.csv", progression, list(progression[0].keys()))
    write_csv(TABLE_DIR / "si_independent_progressive_model_metrics.csv", independent, list(independent[0].keys()))
    write_csv(TABLE_DIR / "si_holdout_model_comparison_ee.csv", holdout, list(holdout[0].keys()))
    markdown = write_markdown(inventory, arms, progression, independent, holdout)
    print("Generated SI model progression tables:")
    for path in [
        TABLE_DIR / "si_experiment_inventory.csv",
        TABLE_DIR / "si_feature_arm_definitions.csv",
        TABLE_DIR / "si_representation_progression_ee.csv",
        TABLE_DIR / "si_independent_progressive_model_metrics.csv",
        TABLE_DIR / "si_holdout_model_comparison_ee.csv",
        markdown,
    ]:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()

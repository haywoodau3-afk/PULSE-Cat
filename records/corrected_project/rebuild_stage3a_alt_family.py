from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / "stage3a_alt_family"
RECORDS = ROOT / "revision/reviewer2_comment1/results/p7_source_corrected_copy.jsonl"
STAGE2P = HERE / "features/p7/stage2p.jsonl"
POSE_INTERACTION = HERE / "features/p7/pose_interaction.jsonl"
POSE_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"
POSE_FOLDING = ROOT / "data/jacs_2025/stage2/features/pose-folding-features.jsonl"
STAGE3B = ROOT / "data/jacs_2025/stage3/features/bde.jsonl"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_modelable_stage2p_rows(path: Path) -> int:
    rows = [json.loads(line) for line in STAGE2P.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [row for row in rows if row.get("target_value") is not None]
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
    return len(rows)


def write_corrected_stage3a_alt_matrix(stage3a_full, path: Path) -> dict[str, int]:
    records = stage3a_full.training_records(RECORDS, include_zero_curated=True)
    rows = stage3a_full.featurize_records(records, feature_set="stage3a_alt")
    fields = sorted({name for row in rows for name in row["features"] if name.startswith("stage3a_alt_hetero_site.")})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["substrate_id", "target_value", *fields], lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({"substrate_id": row["substrate_id"], "target_value": row["target_value"], **{name: row["features"][name] for name in fields}})
    return {"substrate_count": len(rows), "feature_count": len(fields)}


def main() -> None:
    stage3a_full = load_module("stage3a_alt_full_scope_predict", ROOT / "scripts/stage3a_alt_full_scope_predict.py")
    family_model = load_module("stage3a_alt_plus_stage2p_family_heldout", ROOT / "scripts/stage3a_alt_plus_stage2p_family_heldout.py")

    OUT.mkdir(parents=True, exist_ok=True)
    graph_matrix = OUT / "stage3a-alt-full-scope-training-matrix-corrected.csv"
    graph_counts = write_corrected_stage3a_alt_matrix(stage3a_full, graph_matrix)
    stage2p_modelable = OUT / "stage2p-ee-modelable-corrected.jsonl"
    stage2p_modelable_count = write_modelable_stage2p_rows(stage2p_modelable)

    # The family benchmark calls these module constants to assemble its base
    # feature rows. Point them at the corrected interaction data and the
    # preserved, label-blind Stage 1-derived summaries.
    family_model.stage2p.DEFAULT_POSE_SUMMARY = POSE_SUMMARY
    family_model.stage2p.DEFAULT_POSE_INTERACTION = POSE_INTERACTION
    family_model.stage2p.DEFAULT_POSE_FOLDING = POSE_FOLDING
    family_model.EXCLUDED_SUBSTRATES = {"1ad", "1an", "1z"}

    metrics, predictions = family_model.run(RECORDS, stage2p_modelable, graph_matrix, STAGE3B)
    metrics["status"] = "corrected_feature_rerun; retrospective family-held-out analysis"
    metrics["corrected_inputs"] = {
        "records": str(RECORDS.relative_to(ROOT)),
        "stage2p_features": str(stage2p_modelable.relative_to(ROOT)),
        "stage2_pose_interaction": str(POSE_INTERACTION.relative_to(ROOT)),
        "stage1_pose_summary": str(POSE_SUMMARY.relative_to(ROOT)),
        "stage1_pose_folding": str(POSE_FOLDING.relative_to(ROOT)),
        "stage3a_graph_features": str(graph_matrix.relative_to(ROOT)),
        "stage3b_bde_features": str(STAGE3B.relative_to(ROOT)),
        "stage3b_mapping_audit": "BDE generation uses atom-map IDs to locate candidate C-H sites and does not use the faulty nitrene atom-index assumption; source file retained.",
    }
    metrics["graph_feature_matrix_coverage"] = graph_counts
    metrics["modelable_stage2p_row_count"] = stage2p_modelable_count
    metrics["input_sha256"] = {str(path.relative_to(ROOT)): sha256(path) for path in [RECORDS, STAGE2P, POSE_INTERACTION, POSE_SUMMARY, POSE_FOLDING, STAGE3B, graph_matrix, stage2p_modelable]}

    metrics_path = OUT / "stage3a-alt-plus-stage2p-family-heldout-corrected.json"
    predictions_path = OUT / "stage3a-alt-plus-stage2p-family-heldout-corrected.csv"
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    family_model.write_predictions(predictions_path, predictions)
    print(json.dumps({"metrics_path": str(metrics_path.relative_to(ROOT)), "predictions_path": str(predictions_path.relative_to(ROOT)), "models": metrics["models"], "cohort": metrics["cohort"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

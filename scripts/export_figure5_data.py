from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "figures" / "figure5_data"
OUT.mkdir(parents=True, exist_ok=True)


def write_csv(name, fieldnames, rows):
    with (OUT / name).open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def export_panel_a():
    stages = [
        (1, "raw molecular strings", 50560),
        (2, "unique canonical structures", None),
        (3, "structurally eligible", None),
        (4, "within applicability domain", None),
        (5, "scored", None),
    ]
    values = {
        "Generated": [50560, 9184, 563, 483, 483],
        "Enumerated": [50560, 25955, 18545, 18350, 18223],
    }
    rows = []
    for route, counts in values.items():
        for (stage_order, stage, _), count in zip(stages, counts):
            rows.append({
                "route": route,
                "stage_order": stage_order,
                "stage": stage,
                "candidate_count": count,
                "population_status": "frozen scored population" if stage_order == 5 else "screening-stage population",
                "source": "user-provided Figure 5 specification / manuscript report",
            })
    write_csv(
        "panel5a_funnels.csv",
        ["route", "stage_order", "stage", "candidate_count", "population_status", "source"],
        rows,
    )
    write_csv(
        "panel5a_enumeration_provenance.csv",
        ["route", "in_domain_candidates", "scored_candidates", "eligible_without_prediction_rows", "excluded_from_panel_c", "note"],
        [{
            "route": "Enumerated",
            "in_domain_candidates": 18350,
            "scored_candidates": 18223,
            "eligible_without_prediction_rows": 127,
            "excluded_from_panel_c": "true",
            "note": "The 127 records are eligible and in-domain but lack frozen prediction rows; they are excluded from the frozen scored-population comparison.",
        }],
    )


def export_panel_b():
    rows = [
        {"provenance": "Generated", "diagnostic_sample_n": 500, "metric": "mean_internal_pairwise_tanimoto", "mean_value": 0.31249, "reported_display_value": 0.312, "interpretation": "greater internal diversity", "raw_distribution_available": "false"},
        {"provenance": "Enumerated", "diagnostic_sample_n": 500, "metric": "mean_internal_pairwise_tanimoto", "mean_value": 0.41197, "reported_display_value": 0.412, "interpretation": "lower internal diversity than generated sample", "raw_distribution_available": "false"},
        {"provenance": "Generated", "diagnostic_sample_n": 500, "metric": "mean_maximum_similarity_to_experimental_reference", "mean_value": 0.48725, "reported_display_value": 0.487, "interpretation": "average similarity to known chemistry", "raw_distribution_available": "false"},
        {"provenance": "Enumerated", "diagnostic_sample_n": 500, "metric": "mean_maximum_similarity_to_experimental_reference", "mean_value": 0.45724, "reported_display_value": 0.457, "interpretation": "average similarity to known chemistry", "raw_distribution_available": "false"},
    ]
    write_csv(
        "panel5b_similarity_summary.csv",
        ["provenance", "diagnostic_sample_n", "metric", "mean_value", "reported_display_value", "interpretation", "raw_distribution_available"],
        rows,
    )


def export_panel_c():
    sources = {
        "Generated": ROOT / "data/expansion/pptl/funnel-production-ee.csv",
        "Enumerated": ROOT / "data/expansion/pptl/funnel-enumeration-ee.csv",
    }
    all_rows = []
    for provenance, path in sources.items():
        rows = read_csv(path)
        kept = [r for r in rows if r["contract_valid"] == "true" and r["ad_status"] == "in_domain"]
        values = sorted((float(r["ee_prediction_development"]) for r in kept), reverse=True)
        for rank, r in enumerate(sorted(kept, key=lambda q: float(q["ee_prediction_development"]), reverse=True), start=1):
            all_rows.append({
                "provenance": provenance,
                "candidate_id": r["candidate_id"],
                "canonical_smiles": r["canonical_smiles"],
                "predicted_ee_percent": r["ee_prediction_development"],
                "ad_max_morgan_tanimoto": r["ad_max_morgan_tanimoto"],
                "ad_status": r["ad_status"],
                "contract_valid": r["contract_valid"],
                "model_status": r["ee_model_status"],
                "rank_within_provenance_by_raw_score": rank,
                "raw_top10_flag": "true" if rank <= 10 else "false",
            })
        # Keep the values variable in this function as an explicit audit of the
        # exact candidate-level source population used for export.
        assert len(values) == len(kept)
    write_csv(
        "panel5c_candidate_predicted_ee.csv",
        ["provenance", "candidate_id", "canonical_smiles", "predicted_ee_percent", "ad_max_morgan_tanimoto", "ad_status", "contract_valid", "model_status", "rank_within_provenance_by_raw_score", "raw_top10_flag"],
        all_rows,
    )
    write_csv(
        "panel5c_summary.csv",
        ["provenance", "candidate_n", "mean_predicted_ee_reported", "top10_mean_predicted_ee_reported", "mean_predicted_ee_recomputed_from_export", "top10_mean_predicted_ee_recomputed_from_export", "note"],
        [
            {"provenance": "Generated", "candidate_n": 483, "mean_predicted_ee_reported": 56.017, "top10_mean_predicted_ee_reported": 69.411, "mean_predicted_ee_recomputed_from_export": 56.01670062111801, "top10_mean_predicted_ee_recomputed_from_export": 78.12105, "note": "The exported candidate rows reproduce the reported mean; the supplied report's top-10 summary does not match a direct top-10 calculation from these rows."},
            {"provenance": "Enumerated", "candidate_n": 18223, "mean_predicted_ee_reported": 75.305, "top10_mean_predicted_ee_reported": 85.806, "mean_predicted_ee_recomputed_from_export": 75.30483037919113, "top10_mean_predicted_ee_recomputed_from_export": 94.62885, "note": "The exported candidate rows reproduce the reported mean; the supplied report's top-10 summary does not match a direct top-10 calculation from these rows."},
        ],
    )


def export_panel_d():
    rows = read_csv(ROOT / "data/expansion/pptl/sealed-prospective-panel.csv")
    for r in rows:
        r["branch_label"] = "PULSE-Cat branch" if r["branch"] == "copilot" else "Comparator branch"
        r["round_label"] = "Proposed Round 1" if r["round"] == "A" else "Proposed Round 2"
        r["proposal_status"] = "sealed prospective proposal"
    write_csv(
        "panel5d_sealed_prospective_panel.csv",
        ["candidate_id", "branch", "branch_label", "round", "round_label", "canonical_smiles", "predicted_ee", "ad_status", "outcome_ee", "outcome_revealed", "proposal_status"],
        rows,
    )


def write_readme():
    (OUT / "README.md").write_text(
        "# Figure 5 raw plotting data\n\n"
        "These files contain the raw or directly reported values used to construct Figure 5.\n\n"
        "## Files\n\n"
        "- `panel5a_funnels.csv`: candidate counts at each funnel stage for generated and enumerated routes.\n"
        "- `panel5a_enumeration_provenance.csv`: the 127 eligible, in-domain enumeration candidates without prediction rows.\n"
        "- `panel5b_similarity_summary.csv`: reported means for the matched 500-candidate diagnostics. The underlying pairwise and reference-similarity observations were not present in the supplied workspace, so no raw distributions are claimed.\n"
        "- `panel5c_candidate_predicted_ee.csv`: candidate-level frozen predicted-ee rows after contract-validity and in-domain filtering.\n"
        "- `panel5c_summary.csv`: reported Panel C means/top-10 means plus values recomputed from the exported candidate rows. The supplied top-10 summaries do not equal the direct top-10 calculation from the candidate-level files; both are retained transparently.\n"
        "- `panel5d_sealed_prospective_panel.csv`: exact 16-member sealed proposal panel, with branch and round labels added.\n\n"
        "All percentages are percentage points, not fractions. Panel C predictions are computational prioritizations from the frozen model, not experimental outcomes.\n"
    )


if __name__ == "__main__":
    export_panel_a()
    export_panel_b()
    export_panel_c()
    export_panel_d()
    write_readme()
    print(OUT)

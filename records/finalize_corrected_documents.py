from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

HERE = Path(__file__).resolve().parent
PYTHON = sys.executable


def rebuild_working_documents() -> None:
    subprocess.run([PYTHON, str(HERE / "update_manuscript.py")], check=True)
    subprocess.run([PYTHON, str(HERE / "update_supporting_information.py")], check=True)


def replace_paragraph(doc, start: str, text: str) -> None:
    matches = [p for p in doc.paragraphs if p.text.startswith(start)]
    if not matches:
        raise ValueError(f"paragraph not found: {start}")
    p = matches[0]
    p.clear()
    p.add_run(text)


def following_table(doc, caption_start: str) -> Table:
    body = doc._body._body
    children = list(body)
    for i, child in enumerate(children):
        if child.tag == qn("w:p"):
            p = Paragraph(child, doc._body)
            if p.text.startswith(caption_start):
                for later in children[i + 1 :]:
                    if later.tag == qn("w:tbl"):
                        return Table(later, doc._body)
                    if later.tag == qn("w:p") and Paragraph(later, doc._body).text.strip():
                        break
    raise ValueError(f"table following caption not found: {caption_start}")


def fill_table(table: Table, rows: list[list[str]]) -> None:
    if len(rows) != len(table.rows):
        raise ValueError(f"row count mismatch: got {len(rows)}, table has {len(table.rows)}")
    if any(len(row) != len(table.columns) for row in rows):
        raise ValueError("column count mismatch")
    for row, values in zip(table.rows, rows):
        for cell, value in zip(row.cells, values):
            cell.text = value


def prevent_row_split(table: Table) -> None:
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        if tr_pr.find(qn("w:cantSplit")) is None:
            tr_pr.append(OxmlElement("w:cantSplit"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(value: str, places: int = 3) -> str:
    try:
        return f"{float(value):.{places}f}"
    except (TypeError, ValueError):
        return value


def replace_picture(paragraph: Paragraph, path: Path, width_inches: float = 6.2) -> None:
    p = paragraph._p
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(path), width=__import__("docx").shared.Inches(width_inches))


def clear_picture_paragraph(paragraph: Paragraph) -> None:
    p = paragraph._p
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)


def update_si() -> None:
    path = HERE / "Supporting_Information_corrected_working.docx"
    doc = Document(path)

    for table in doc.tables:
        for row in table.rows:
            if row.cells and "55.3%/33.2%" in row.cells[0].text:
                row.cells[0].text = row.cells[0].text.replace("55.3%/33.2%", "70.7%/43.2%")
                if len(row.cells) > 1:
                    row.cells[1].text = row.cells[1].text.replace(
                        "mean-prefix MAEs reproduced from identified raw learning curves, with populations and acquisition sequences linked through the corresponding manifests and event records.",
                        "corrected mean-prefix replay with source-order and uncertainty–diversity trajectories; three random continuations are used in this corrected route table.",
                    )

    replace_paragraph(
        doc,
        "Pair 05 had the largest JS divergence",
        "Across all 13 canonical shared aryl identities, pair 1i/2r ranks first by corrected Jensen–Shannon divergence (0.030961 bits), with total variation distance 0.171882 and Bhattacharyya overlap 0.978082. The ranking is computed from unit-sum, nitrene-centred all-heavy-atom Stage 2pp grids over all 200 poses. These are descriptor-field comparisons, not conformer populations or mechanistic evidence.",
    )
    replace_paragraph(
        doc,
        "The relative reductions from reported order to uncertainty–diversity",
        "In the corrected dedicated Ridge mean-prefix replay, uncertainty–diversity lowers mean-prefix ee MAE relative to reported order from 25.508 to 7.475 points for Fe(P7)Cl (70.7%) and from 16.977 to 9.641 for the Fe(CMC-Por)Cl aryl cohort (43.2%). These route-specific trajectories combine the starting pair and subsequent order. The corrected random comparator uses three continuations, so it is not directly comparable to the archived 500-continuation random summary.",
    )
    replace_paragraph(
        doc,
        "A current-code replay reproduced every recorded Ridge prefix MAE",
        "The corrected independent progression uses 500 random continuations per endpoint, fixed feature-version inputs, and a separately recorded analysis seed. Its AUC-MAE tables and plots are reported below. AUC-MAE integrates route-specific learning curves and is distinct from the common-test mean MAE and dedicated remaining-pool mean-prefix metric.",
    )
    replace_paragraph(
        doc,
        "Uncertainty–diversity minimises ee AUC-MAE",
        "In the corrected independent progression, uncertainty–diversity has lower ee AUC-MAE than reported order for all three estimators in Fe(P7)Cl (Elastic Net 221.159 vs 802.319; Ridge 256.065 vs 905.664; Tanimoto-kNN 306.288 vs 601.044) and for all three estimators in the Fe(CMC-Por)Cl aryl cohort (205.592 vs 328.341; 214.062 vs 392.226; 199.611 vs 238.721). For CMC ee, diversity-first gives a still lower AUC-MAE than uncertainty–diversity with Tanimoto-kNN (171.515 vs 199.611).",
    )
    replace_paragraph(
        doc,
        "Yield was evaluated as a separate secondary endpoint",
        "Yield was evaluated as a separate secondary endpoint rather than part of a composite acquisition objective. In the corrected independent progression, reported-order / uncertainty–diversity yield AUC-MAE is 994.635 / 557.995 (Elastic Net), 1062.441 / 574.215 (Ridge), and 633.651 / 470.038 (Tanimoto-kNN) for Fe(P7)Cl; corresponding values are 545.784 / 391.542, 552.810 / 414.914, and 398.990 / 294.337 for the Fe(CMC-Por)Cl aryl cohort. In the separate common-test analysis, UD also has lower mean yield MAE than source order and random in both datasets, though split-level results vary. Neither retrospective analysis establishes a chemical mechanism for endpoint-dependent performance.",
    )

    # Correct the archived primary progression tables in place.
    fill_table(
        following_table(doc, "Table S8."),
        [
            ["Acquisition route", "Fe(P7)Cl", "Fe(CMC-Por)Cl aryl"],
            ["Reported order", "25.508", "16.977"],
            ["Diversity-first", "9.374", "8.740"],
            ["Random (3 continuations)", "9.723", "12.514"],
            ["Performance-first", "11.106", "10.850"],
            ["Uncertainty–diversity", "7.475", "9.641"],
        ],
    )
    csv_paths = {
        "Table S9.": "corrected_Table_S9_p7_ee.csv",
        "Table S10.": "corrected_Table_S10_p7_yield.csv",
        "Table S11.": "corrected_Table_S11_cmc_ee.csv",
        "Table S12.": "corrected_Table_S12_cmc_yield.csv",
    }
    for caption, filename in csv_paths.items():
        rows = read_csv(HERE / "corrected_project" / "independent_progression_tables" / filename)
        table_rows = [["Route", "Model", "Final n", "Final MAE", "AUC-MAE", "n₉₀", "Ref. MAE", "Δ"]]
        for row in rows:
            table_rows.append([
                row["route"], row["model"], row["final_n"], fmt(row["final_mae"]),
                fmt(row["auc_mae"]), row["n90"], fmt(row["reference_loo_mae"]),
                fmt(row["final_minus_reference"]),
            ])
        fill_table(following_table(doc, caption), table_rows)

    # Correct the 50-start and common-test summaries.
    fill_table(
        following_table(doc, "Table S17."),
        [
            ["Catalyst", "Comparator", "Mean difference / (ee points)", "Conditional 95% / interval", "Pairs favouring / uncertainty–diversity"],
            ["Fe(P7)Cl", "Reported order", "9.83", "8.61 to 11.04", "50/50"],
            ["Fe(P7)Cl", "Random (3 continuations)", "1.38", "0.96 to 1.82", "39/50"],
            ["Fe(CMC-Por)Cl", "Reported order", "4.84", "3.96 to 5.69", "45/50"],
            ["Fe(CMC-Por)Cl", "Random (3 continuations)", "3.07", "2.46 to 3.68", "46/50"],
        ],
    )
    fill_table(
        following_table(doc, "Table S18."),
        [
            ["Catalyst", "Comparator", "Mean difference / (ee points)", "Median (IQR) / (ee points)", "Splits favouring / uncertainty–diversity"],
            ["Fe(P7)Cl", "Source order", "6.99", "5.64 (3.99 to 7.75)", "19/20"],
            ["Fe(P7)Cl", "Random", "1.45", "1.20 (−0.01 to 2.97)", "15/20"],
            ["Fe(CMC-Por)Cl", "Source order", "2.50", "0.13 (−0.92 to 4.30)", "11/20"],
            ["Fe(CMC-Por)Cl", "Random", "1.22", "1.17 (−1.46 to 2.74)", "12/20"],
        ],
    )

    for caption, domain in [("Table S19a.", "p7"), ("Table S19b.", "cmcpor")]:
        grid = read_csv(HERE / "corrected_project" / "analysis_runs" / "corrected_weight_sensitivity" / domain / "weight_summary.csv")
        rows = [["D", "U", "C", "Mean MAE", "Δ vs default", "Default lower / (splits/20)"]]
        for row in grid:
            rows.append([
                fmt(row["w_diversity"], 1), fmt(row["w_uncertainty"], 1), fmt(row["w_family_coverage"], 1),
                fmt(row["mean_split_mae"], 2), fmt(row["mean_paired_delta_vs_default"], 2),
                f"{row['splits_default_lower_mae']}/20",
            ])
        fill_table(following_table(doc, caption), rows)

    # Correct the most consequential stale prose in reviewer analyses.
    replacements = [
        ("For Fe(P7)Cl, the default ranked 11th of 21", "For Fe(P7)Cl, the corrected default ranks 8th of 21 with mean split MAE 13.72 ee points (range 13.31–15.40); for Fe(CMC-Por)Cl it ranks 11th of 21 with mean 13.83 (range 13.45–16.33). No weighting is established as generally optimal by this exploratory grid."),
        ("Mean held-out MAEs in ee points, in the order structure/source", "After correction, mean held-out MAEs in ee points, in the order structure/source, structure/acquisition, full-pose/source and full-pose/acquisition, were 11.34, 12.07, 20.71 and 13.72 for Fe(P7)Cl, and 9.62, 10.77, 16.33 and 13.83 for Fe(CMC-Por)Cl. The full-pose/acquisition cell does not outperform the structure-only/source cell in either dataset."),
        ("In the mixed-pool replay, mean MAEs for source order", "After correction, the mixed-pool replay gives mean MAEs for source order / uncertainty–diversity / random of 23.06 / 15.80 / 17.14 ee points overall; for held-out aryls they are 15.96 / 14.24 / 15.56, and for sulfonyl records 33.71 / 18.15 / 19.53. The corrected sulfonyl-only replay gives 17.98 / 19.22 / 19.63; thus the UD advantage over source order does not extend to this separate sulfonyl-only pool. The source study used different conditions for the substrate classes, so these are descriptive, confounded retrospective comparisons."),
        ("Mean held-out yield MAEs for source / uncertainty–diversity / random", "In the corrected common-test yield analysis, mean held-out MAE for source / uncertainty–diversity / random was 25.36 / 18.38 / 20.93 for Fe(P7)Cl and 25.48 / 23.49 / 24.53 for the Fe(CMC-Por)Cl aryl cohort. UD was lower in 19/20 and 15/20 splits for P7, and 12/20 and 16/20 for CMC, respectively. The results are split-dependent and do not provide a mechanistic explanation."),
        ("QBC gave lower mean common-test error than PULSE", "After correction, QBC has lower mean common-test ee error than uncertainty–diversity in both datasets; EI also has lower mean error for Fe(P7)Cl. The corrected means are reported in the main manuscript and the accompanying corrected analysis tables. These are implementation-specific retrospective comparisons, not a universal method ranking."),
    ]
    for start, text in replacements:
        replace_paragraph(doc, start, text)

    replace_paragraph(
        doc,
        "This analysis is distinct from the seven-record Fe(CMC-Por)Cl audit",
        "This common-test analysis is distinct from the seven-record Fe(CMC-Por)Cl audit and from the dedicated mean-prefix route comparison. The original 55.3% and 33.2% reductions are superseded by corrected replay estimates of 70.7% and 43.2%, respectively. Neither set of route-specific trajectory reductions is a fixed-test estimate or evidence of population-level significance.",
    )

    # Correct the matched representation table and family-level diagnostics.
    fill_table(
        following_table(doc, "Table S5."),
        [
            ["Protocol and representation", "MAE", "RMSE", "R²"],
            ["Target holdout: structure only", "12.612", "15.183", "0.064"],
            ["Target holdout: structure + pose", "7.979", "10.964", "0.512"],
            ["Family holdout: structure only", "10.406", "13.525", "0.257"],
            ["Family holdout: structure + pose", "8.538", "11.447", "0.468"],
            ["Occupancy comparison: local geometry", "10.281", "13.023", "0.311"],
            ["Occupancy comparison: +655 features", "14.132", "17.005", "-0.175"],
            ["Nested families: corrected Stage 2p geometry", "9.801", "14.150", "0.187"],
            ["Nested families: +Stage 3a-alt", "9.834", "13.998", "0.204"],
            ["Nested families: +Stage 3b only (unstable)", "Not reported", "Not reported", "Not reported"],
            ["Nested families: +Stage 3a-alt +Stage 3b", "9.653", "13.371", "0.274"],
        ],
    )
    prevent_row_split(following_table(doc, "Table S5."))
    replace_paragraph(
        doc,
        "The target- and family-holdout pose gains are",
        "After correction, the Fe(P7)Cl Elastic Net target-held-out and family-held-out MAEs are 7.979 and 8.538 for structure plus pose, versus 12.612 and 10.406 for structure-only models. The family-held-out improvement is modest and heterogeneous: pose error is lower for 11/17 families and 23/38 substrates, while the largest family favours structure-only. Corrected nested-family ablations using regenerated Stage 2p features are also listed in Table S5. The Stage 2p + Stage 3b-only arm produced extreme out-of-family predictions under the selected low-regularisation setting and is labelled unstable rather than assigned a performance estimate.",
    )
    replace_paragraph(
        doc,
        "The archived structure-only and structure-plus-pose Elastic Net ee predictions",
        "The corrected structure-only and structure-plus-pose Elastic Net ee predictions were paired by substrate and checked against the 17 family-held-out split definitions. Across the 38 records, pose error is lower for 23; it lowers family MAE in 11 of 17 groups. Equal-weight family MAE is 11.99 points for structure-only and 8.72 for structure plus pose. The largest group (n=12) favours structure-only, 5.25 versus 6.23 points. These are retrospective, imbalanced family summaries, not evidence of reliable extrapolation to unseen chemical families.",
    )
    replace_paragraph(
        doc,
        "There are nine singleton families",
        "There are nine singleton families, four families of two, three of three, and one of 12. In the corrected evaluation, pose lowers family MAE in 11/17 families and substrate-level absolute error in 23/38 records. Family sizes remain unequal, and overlapping training sets mean these counts are descriptive rather than independent replications.",
    )

    # Recalculate the CREST/GFN2-xTB ablation using corrected Stage 2p inputs.
    crest_metrics_path = HERE / "corrected_project" / "crest_family" / "corrected_metrics.json"
    crest_metrics = json.loads(crest_metrics_path.read_text(encoding="utf-8"))
    crest_rows = [["Representation", "Columns", "MAE", "RMSE", "R²"]]
    crest_labels = [
        ("stage2p_geometry", "Corrected Stage 2p geometry"),
        ("stage2p_plus_crest_geometry", "+CREST geometry"),
        ("stage2p_plus_xtb_electronics", "+dense GFN2-xTB electronics"),
        ("stage2p_plus_crest_and_xtb", "+CREST geometry + GFN2-xTB"),
    ]
    for model_name, label in crest_labels:
        model = crest_metrics["models"][model_name]
        pooled = model["pooled_metrics"]
        crest_rows.append([
            label,
            str(model["feature_count"]),
            fmt(str(pooled["mae"])),
            fmt(str(pooled["rmse"])),
            fmt(str(pooled["r2"])),
        ])
    crest_table = following_table(doc, "Table S6.")
    fill_table(crest_table, crest_rows)
    prevent_row_split(crest_table)
    replace_paragraph(
        doc,
        "Table S6. Nested-family CREST ablations",
        "Table S6. Corrected nested-family CREST/GFN2-xTB ablations on 38 Fe(P7)Cl ee records using regenerated Stage 2p features. Dimensions are before fold-local filtering.",
    )

    bootstrap_rows = [["Augmentation", "Mean improvement", "95% percentile interval (ee points)", "Bootstrap fraction > 0"]]
    for model_name, label in [
        ("stage2p_plus_crest_geometry", "CREST geometry"),
        ("stage2p_plus_xtb_electronics", "xTB electronic"),
        ("stage2p_plus_crest_and_xtb", "Combined"),
    ]:
        value = crest_metrics["paired_bootstrap_improvements"][model_name]
        lo, hi = value["percentile_95_interval_ee_points"]
        bootstrap_rows.append([
            label,
            fmt(str(value["mean_improvement_ee_points"])),
            f"[{fmt(str(lo))}, {fmt(str(hi))}]",
            fmt(str(value["bootstrap_fraction_above_zero"]), 3),
        ])
    bootstrap_table = following_table(doc, "Table S7.")
    bootstrap_table.add_column(__import__("docx").shared.Inches(1.05))
    bootstrap_table.add_column(__import__("docx").shared.Inches(1.05))
    fill_table(bootstrap_table, bootstrap_rows)
    bootstrap_table.autofit = False
    column_widths = [1.45, 1.3, 2.2, 1.2]
    for index, width in enumerate(column_widths):
        bootstrap_table.columns[index].width = __import__("docx").shared.Inches(width)
        for row in bootstrap_table.rows:
            row.cells[index].width = __import__("docx").shared.Inches(width)
    prevent_row_split(bootstrap_table)
    replace_paragraph(
        doc,
        "Table S7. Reported paired-bootstrap MAE improvement intervals",
        "Table S7. Corrected paired-bootstrap MAE improvement intervals (baseline minus augmentation) on 38 substrates. Positive values favour augmentation; intervals are substrate-bootstrap, not family-cluster intervals.",
    )
    replace_paragraph(
        doc,
        "The unrounded combined improvement is reported as",
        "After correction, all three augmentation arms have lower point-estimate MAE than the Stage 2p baseline; paired 20,000-draw substrate-bootstrap 95% intervals include zero for CREST geometry (mean improvement 0.453 points), GFN2-xTB electronics (1.476), and the combined block (0.794). These overlapping retrospective family-held-out estimates do not establish a reliable improvement, and the bootstrap is not clustered by substrate family. The CREST conformer set contains one retained minimum per substrate, so its population fields contain no ensemble diversity. No corresponding CREST yield experiment was reported.",
    )

    replace_paragraph(
        doc,
        "The cylindrical-field centroids are nearly identical",
        "In the corrected normalised fields, the mean axial positions are 2.243 and 2.248 Å, and the mean radial positions are 2.566 and 2.634 Å for Fe(P7)Cl 1i and Fe(CMC-Por)Cl 2r, respectively. These first moments are similar even though the complete grid distributions differ; they describe sampled descriptor fields, not thermodynamic populations.",
    )
    replace_paragraph(
        doc,
        "The cylindrical NPZ fields were converted to Cartesian CUBE volumes",
        "The archived Cartesian CUBE volume visualisation was generated from pre-correction fields and is removed from this working revision. The corrected cylindrical fields are shown in Figure S2. A corrected atom-resolved volume rendering has not been generated, so no CUBE surface is used to support the present comparison.",
    )

    # Recompute the per-family table from corrected held-out predictions.
    family_dir = HERE / "corrected_project" / "model_comparisons" / "p7"
    per_family: dict[str, dict[str, list[float]]] = {}
    for filename, key in [
        ("family_holdout_ee_predictions.csv", "structure"),
        ("family_holdout_ee_pose_predictions.csv", "pose"),
    ]:
        for row in read_csv(family_dir / filename):
            if row["model_name"] == "elastic_net":
                per_family.setdefault(row["family_id"], {"structure": [], "pose": []})[key].append(float(row["abs_error"]))
    family_rows = [["Substrate family", "n", "Structure", "+ pose", "Difference"]]
    for family in sorted(per_family):
        item = per_family[family]
        n = len(item["structure"])
        structure_mae = sum(item["structure"]) / n
        pose_mae = sum(item["pose"]) / n
        family_rows.append([family, str(n), f"{structure_mae:.2f}", f"{pose_mae:.2f}", f"{structure_mae - pose_mae:+.2f}"])
    fill_table(following_table(doc, "Table S20."), family_rows)

    # Update the corrected grid moments and remove the obsolete field table row.
    moments = next(
        table for table in doc.tables
        if any("Fe(P7)Cl 1i" in cell.text for row in table.rows for cell in row.cells)
        and any("Mean axial z" in cell.text for row in table.rows for cell in row.cells)
    )
    moment_rows = [
        ["Quantity", "Fe(P7)Cl 1i", "Fe(CMC-Por)Cl 2r"],
        ["Mean axial z (Å)", "2.243", "2.248"],
        ["Mean radial ρ (Å)", "2.566", "2.634"],
        ["Axial standard deviation (Å)", "1.943", "2.239"],
        ["Radial standard deviation (Å)", "1.131", "1.069"],
        ["z–ρ covariance (Å²)", "0.129", "0.166"],
    ]
    while len(moments.rows) > len(moment_rows):
        moments._tbl.remove(moments.rows[-1]._tr)
    fill_table(moments, moment_rows)

    # Replace progression plots with figures generated from corrected outputs.
    paras = doc.paragraphs
    for i, p in enumerate(paras):
        if p.text.startswith("Figure S2."):
            prior_images = [paras[j] for j in range(max(0, i - 7), i) if paras[j]._p.xpath(".//w:drawing")]
            if not prior_images:
                raise ValueError("Figure S2 image paragraph not found")
            replace_picture(prior_images[-1], HERE / "figures" / "figure5_corrected_cross_catalyst.png")
            for obsolete in prior_images[:-1]:
                clear_picture_paragraph(obsolete)
            p.clear()
            p.add_run("Figure S2. Corrected nitrene-centred all-heavy-atom occupancy grids for the shared substrate identity Fe(P7)Cl 1i / Fe(CMC-Por)Cl 2r, which ranks first by Jensen–Shannon divergence among 13 canonical matches. The grids include all 200 poses and are normalised to unit sum. Corrected metrics are JS 0.0310 bits, total variation 0.1719, and Bhattacharyya overlap 0.9781. These are sampled descriptor fields, not measured populations or mechanistic evidence.")
        if p.text.startswith("Figure S5."):
            prior = next((paras[j] for j in range(i - 1, max(-1, i - 4), -1) if paras[j]._p.xpath(".//w:drawing")), None)
            if prior is None:
                raise ValueError("Figure S5 image paragraph not found")
            replace_picture(prior, HERE / "figures" / "figureS5_corrected_yield_auc.png")
            p.clear()
            p.add_run("Figure S5. Corrected independent-progression yield AUC-MAE for reported-order and uncertainty–diversity routes, using Elastic Net, Ridge, and Tanimoto-kNN. Lower values indicate lower integrated prediction error; the curves are route-specific and retrospective.")
        if p.text.startswith("Figure S6."):
            preceding = [paras[j] for j in range(max(0, i - 4), i) if paras[j]._p.xpath(".//w:drawing")]
            if not preceding:
                raise ValueError("Figure S6 image paragraphs not found")
            replace_picture(preceding[0], HERE / "figures" / "figureS6_corrected_independent_acquisition.png")
            for extra in preceding[1:]:
                clear_picture_paragraph(extra)
            p.clear()
            p.add_run("Figure S6. Corrected independent acquisition progression summaries for Fe(P7)Cl and Fe(CMC-Por)Cl aryl records. The random trajectories use 500 continuations in this independent analysis; the separate dedicated mean-prefix table uses three. AUC-MAE and mean-prefix MAE are distinct metrics.")
        if p.text.startswith("Figure S4."):
            prior = next((paras[j] for j in range(i - 1, max(-1, i - 4), -1) if paras[j]._p.xpath(".//w:drawing")), None)
            if prior is not None:
                clear_picture_paragraph(prior)
            p.clear()
            p.add_run("Figure S4. Archived CUBE rendering removed because it was derived from pre-correction occupancy fields. The corrected cylindrical occupancy comparison is provided in Figure S2; an updated atom-resolved volumetric rendering is not available in this revision draft.")

    doc.save(path)


def main() -> None:
    subprocess.run([PYTHON, str(HERE / "build_corrected_si_sensitivity_figures.py")], check=True)
    rebuild_working_documents()
    update_si()
    subprocess.run([PYTHON, str(HERE / "closeout_corrected_documents.py")], check=True)
    print(HERE / "Manuscript_corrected_working.docx")
    print(HERE / "Supporting_Information_corrected_working.docx")


if __name__ == "__main__":
    main()

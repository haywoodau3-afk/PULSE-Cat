#!/usr/bin/env python3
"""Create cumulative, highlighted R1.2 manuscript and SI review copies."""
import csv
import json
import sys
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "reviewer1_comment1"
sys.path.insert(0, str(PREVIOUS))
from update_documents import replacement, insert_after, before, cell_text, keep_captions_with_content

RESULTS = HERE / "results" / "weight_sensitivity"
DEFAULT = (0.40, 0.40, 0.20)


def find(doc, needle):
    found = [p for p in doc.paragraphs if needle in p.text]
    assert len(found) == 1, (needle, len(found))
    return found[0]


def load_summary(domain):
    with (RESULTS / domain / "weight_summary.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def summarize():
    data = {}
    for domain in ("p7", "cmcpor"):
        rows = load_summary(domain)
        default = next(r for r in rows if r["is_default"].lower() == "true")
        means = [float(r["mean_split_mae"]) for r in rows]
        default_mean = float(default["mean_split_mae"])
        rank_low = sum(x < default_mean - 1e-10 for x in means) + 1
        rank_high = sum(x <= default_mean + 1e-10 for x in means)
        rank_label = f"{rank_low}th" if rank_low == rank_high else f"{rank_low}th–{rank_high}th (tied)"
        data[domain] = {
            "default": default,
            "rank_label": rank_label,
            "rank_low": rank_low,
            "rank_high": rank_high,
            "min": min(means), "max": max(means),
            "best": min(rows, key=lambda r: float(r["mean_split_mae"])),
            "worst": max(rows, key=lambda r: float(r["mean_split_mae"])),
        }
    return data


def fmt(value, n=2):
    return f"{float(value):.{n}f}"


def main_document(summary):
    d = Document(PREVIOUS / "Manuscript_common_test_revised.docx")
    p = find(d, "The acquisition functions combine four normalised quantities")
    old = p.text
    new = (
        "The acquisition functions combine normalised quantities describing each unrevealed candidate. "
        "Molecular diversity, D, is the normalised structural novelty relative to substrates already revealed. "
        "Model disagreement, Q, is the normalised standard deviation across the Ridge, Elastic Net, and "
        "Tanimoto-kNN predictions. The operational uncertainty component is U=0.50D+0.50Q, so U is a "
        "composite of structural novelty and model disagreement rather than a pure model-uncertainty term. "
        "Chemical-family coverage, C, increases priority for incompletely represented substrate families. "
        "Predicted performance, P, is the model-estimated outcome and is included only in the performance-first "
        "comparator. Normalisation places the quantities on comparable scales before their weighted combination. "
        "The frozen acquisition scores are"
    )
    replacement(p, old, new)
    p = find(d, "SUD=0.40U+0.40D+0.20C,")
    insert_after(d, p, (
        "The 0.40/0.40/0.20 coefficients are a fixed heuristic: the written score assigns equal top-level "
        "coefficients to U and D and a smaller nonzero coefficient to C. Because U itself includes D, the "
        "implemented default expands to SUD=0.60D+0.20Q+0.20C. The coefficients were not selected by "
        "optimising held-out results and are not claimed to be optimal. Sensitivity across the 21-point weight "
        "simplex was assessed on shared held-out splits (SI Section S9)."
    ))
    p = find(d, "To compare predictions on common test substrates in both systems")
    insert_after(d, p, (
        "Weight sensitivity was assessed over every non-negative combination of the three top-level weights "
        "in increments of 0.20 that sums to 1.00 (21 combinations, including the default). Each setting used "
        "the same outer test splits and initial pairs as the common-test analysis; only the acquisition weights "
        "changed. All five Ridge held-out MAEs were averaged within each trajectory and then within each split. "
        "No setting was selected from this retrospective grid (SI Section S9)."
    ))
    p = find(d, "In the repeated common-test analysis, the mean paired source-order-minus-uncertainty")
    summary_text = (
        "In the 21-setting sensitivity grid, the default weights ranked "
        f"{summary['p7']['rank_label']} of 21 for Fe(P7)Cl "
        f"(mean split MAE {fmt(summary['p7']['default']['mean_split_mae'])} ee points) and "
        f"{summary['cmcpor']['rank_label']} of 21 for Fe(CMC-Por)Cl "
        f"({fmt(summary['cmcpor']['default']['mean_split_mae'])} ee points). Across the grid, mean split MAE "
        f"ranged from {fmt(summary['p7']['min'])} to {fmt(summary['p7']['max'])} ee points for Fe(P7)Cl and "
        f"{fmt(summary['cmcpor']['min'])} to {fmt(summary['cmcpor']['max'])} for Fe(CMC-Por)Cl. The default "
        "therefore gives a useful reference point but is not established as an optimum; all grid results and "
        "their split-level variation are reported in Table S19 and Fig. S11. These retrospective splits overlap "
        "and do not validate a universally preferred weighting."
    )
    insert_after(d, p, summary_text)
    p = find(d, "The present 0.40/0.40/0.20 weighting should therefore be regarded")
    old = p.text
    new = old.replace(
        "The present 0.40/0.40/0.20 weighting should therefore be regarded as a study-specific acquisition rule rather than a universally optimal policy.",
        "The present 0.40/0.40/0.20 weighting is a study-specific heuristic, not an empirically established optimum; the retrospective sensitivity grid does not establish a universally preferred policy."
    )
    assert old != new
    replacement(p, old, new)
    p = find(d, "For PULSE-Acquire, the analyses remain retrospective")
    old = p.text
    new = old.replace(
        "sensitivity to initial pairs and common test sets has been examined only within the two observed datasets using overlapping splits, and has not been exhaustively characterised for broader starting panels",
        "sensitivity to initial pairs, common test sets, and acquisition weights has been examined only within the two observed datasets using overlapping splits; it has not been exhaustively characterised for broader starting panels"
    )
    assert old != new
    replacement(p, old, new)
    keep_captions_with_content(d)
    d.save(HERE / "Manuscript_weight_sensitivity_revised.docx")


def add_table(doc, anchor, title, domain, rows):
    cap = before(doc, anchor, title, "Caption", 9.5, True)
    cap.paragraph_format.keep_with_next = True
    r = cap.add_run(
        f" Full 21-combination simplex for {domain}. MAE is in ee points. Difference is combination minus "
        "the default mean split MAE (negative favours that combination); 'default lower' counts splits in "
        "which the default had lower MAE."
    )
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    t = doc.add_table(rows=1, cols=6)
    t.style = "Table Grid"
    t.autofit = True
    anchor._p.addprevious(t._tbl)
    headers = ["D", "U", "C", "Mean MAE", "Δ vs default", "Default lower\n(splits/20)"]
    for cell, text in zip(t.rows[0].cells, headers):
        cell_text(cell, text, True)
        shade = OxmlElement("w:shd")
        shade.set(qn("w:fill"), "E8EDF2")
        cell._tc.get_or_add_tcPr().append(shade)
    header_pr = t.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    header_pr.append(repeat)
    for row in sorted(rows, key=lambda x: int(x["weight_id"])):
        cells = t.add_row().cells
        values = [row["w_diversity"], row["w_uncertainty"], row["w_family_coverage"],
                  fmt(row["mean_split_mae"]), fmt(row["mean_paired_delta_vs_default"]),
                  f"{row['splits_default_lower_mae']}/20"]
        for cell, text in zip(cells, values):
            cell_text(cell, text, row["is_default"].lower() == "true")
        trpr = t.rows[-1]._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trpr.append(cant)
    return t


def supporting_info(summary):
    d = Document(PREVIOUS / "Supporting_Information_common_test_revised.docx")
    p = find(d, "These weights were specified in the study;")
    old = p.text
    new = (
        "The fixed 0.40/0.40/0.20 coefficients assign equal top-level contributions to U and D and a smaller "
        "nonzero contribution to C; they are a simple study-specific heuristic, not values derived from a "
        "chemical mechanism or established as optimal. In the executable acquisition code, U=0.50D+0.50Q, "
        "where Q is min-max-normalised model disagreement across the Ridge, Elastic Net, and Tanimoto-kNN "
        "predictions. The default therefore expands to SUD=0.60D+0.20Q+0.20C, so the nominal U and D terms "
        "are not independent. The weights were not selected by optimising held-out results. A 21-combination "
        "simplex sensitivity analysis is reported in Section S9. Literature on active learning and reaction "
        "optimisation does not establish these exact values [34,35,36,37]. The reported-order route follows "
        "source presentation order, which is not verified as the original chronological experimental order. "
        "Diversity-first prioritises Morgan/Tanimoto distance and family coverage. Random routes sample whole "
        "substrates without replacement: 500 replicates are reported for Ridge and Tanimoto-kNN, no random "
        "Elastic Net summary is included in this comparison."
    )
    replacement(p, old, new)

    anchor = find(d, "Declaration of AI-assisted manuscript preparation")
    heading = before(d, anchor, "S9 Acquisition-weight sensitivity analysis", "Heading 1", 15, True)
    heading.paragraph_format.page_break_before = True
    before(d, anchor, (
        "The operational score is S=wD·D+wU·U+wC·C, where D is min-max-normalised structural novelty, "
        "C is normalised family coverage, Q is min-max-normalised standard deviation of the Ridge, Elastic "
        "Net, and Tanimoto-kNN predictions, and U=0.50D+0.50Q. The default (wD,wU,wC)=(0.40,0.40,0.20) "
        "therefore expands to 0.60D+0.20Q+0.20C. The coefficients are treated as a fixed heuristic; this "
        "analysis does not infer that they are optimal."
    ))
    before(d, anchor, (
        "For sensitivity analysis, all 21 non-negative weight triplets summing to one on a 0.20 grid were "
        "evaluated. The analysis reused the 20 outer test splits and three shared starting pairs per split "
        "from Section S8: six of 38 Fe(P7)Cl active records or five of 26 Fe(CMC-Por)Cl active aryl records "
        "were held out. The seven locked Fe(CMC-Por)Cl audit records are outside the active 26-record cohort "
        "and were not used. Within each split and starting pair, every weight triplet used identical candidate "
        "and held-out sets. Only the three top-level weights changed; representations, per-candidate component "
        "normalisation, model settings, training-only standardisation, prediction bounds, and source-order "
        "tie-breaking were kept fixed."
    ))
    before(d, anchor, (
        "Ridge MAE on the common held-out records was averaged over 2, 6, 10, 15, and 20 active labels, "
        "then over the three initial pairs within each split. Table S19 reports every grid setting by catalyst, "
        "including its mean split-level MAE, paired difference from the default, and the number of splits in "
        "which the default was lower. The default rank is descriptive and is calculated over this same grid. "
        "Selected-substrate set overlap at 20 labels is also recorded in the accompanying analysis files. "
        "The grid was not used to select a replacement weight."
    ))
    before(d, anchor, (
        f"For Fe(P7)Cl, the default ranked {summary['p7']['rank_label']} of 21 "
        f"with mean split MAE {fmt(summary['p7']['default']['mean_split_mae'])} ee points; across the grid, "
        f"the mean ranged from {fmt(summary['p7']['min'])} to {fmt(summary['p7']['max'])}. For Fe(CMC-Por)Cl, "
        f"the default ranked {summary['cmcpor']['rank_label']} of 21 with mean "
        f"split MAE {fmt(summary['cmcpor']['default']['mean_split_mae'])} ee points; across the grid, the "
        f"mean ranged from {fmt(summary['cmcpor']['min'])} to {fmt(summary['cmcpor']['max'])}. The complete "
        "grid is shown in Table S19 and Fig. S11."
    ))
    before(d, anchor, (
        "Because the 20 held-out splits overlap and all derive from the same observed small datasets, these "
        "summaries describe retrospective sensitivity under this split-generation scheme. The relative rank "
        "does not provide independent validation, a population-level confidence interval, or evidence that a "
        "grid point is a generally optimal policy. No significance test is claimed. A prospective acquisition "
        "study would be needed to select or calibrate weights for a new reaction context."
    ))

    p7_rows = load_summary("p7")
    cmc_rows = load_summary("cmcpor")
    add_table(d, anchor, "Table S19a.", "Fe(P7)Cl", p7_rows)
    add_table(d, anchor, "Table S19b.", "Fe(CMC-Por)Cl", cmc_rows)
    pic = d.add_paragraph()
    anchor._p.addprevious(pic._p)
    pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic.paragraph_format.keep_with_next = True
    pic.add_run().add_picture(str(RESULTS / "weight_sensitivity_simplex.png"), width=Inches(6.2))
    cap = before(d, anchor, "Figure S11.", "Caption", 9.5, True)
    r = cap.add_run(
        " Retrospective common-test Ridge MAE over the 21-point weight simplex for Fe(P7)Cl (left) and "
        "Fe(CMC-Por)Cl (right). Each point is one (D,U,C) combination; colours show the mean over the 20 "
        "overlapping split-level held-out MAEs. The star marks the default (0.40,0.40,0.20). Lower values "
        "indicate lower error. The display is descriptive and does not identify a general optimum."
    )
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    before(d, anchor, (
        "The revision-local analysis folder retains the full split-level and trajectory-level results, "
        "held-out predictions, selected-substrate sets, code, and validation/provenance records."
    ))
    keep_captions_with_content(d)
    d.save(HERE / "Supporting_Information_weight_sensitivity_revised.docx")


def main():
    summary = summarize()
    main_document(summary)
    supporting_info(summary)
    print("Created cumulative R1.2 DOCX copies")


if __name__ == "__main__":
    main()

from __future__ import annotations

import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

HERE = Path(__file__).resolve().parent


def ptext(doc, starts: str, replacement: str) -> None:
    found = [p for p in doc.paragraphs if p.text.startswith(starts)]
    if not found:
        raise ValueError(f"paragraph not found: {starts}")
    found[0].clear()
    found[0].add_run(replacement)


def table_after(doc, caption: str) -> Table:
    body = doc._body._body
    children = list(body)
    for i, child in enumerate(children):
        if child.tag == qn("w:p") and Paragraph(child, doc._body).text.startswith(caption):
            for later in children[i + 1 :]:
                if later.tag == qn("w:tbl"):
                    return Table(later, doc._body)
                if later.tag == qn("w:p") and Paragraph(later, doc._body).text.strip():
                    break
    raise ValueError(f"table not found after {caption}")


def fill(table: Table, rows: list[list[str]]) -> None:
    if len(table.rows) != len(rows):
        raise ValueError(f"row mismatch for table: {len(table.rows)} != {len(rows)}")
    if any(len(row) != len(table.columns) for row in rows):
        raise ValueError("column mismatch")
    for tr, values in zip(table.rows, rows):
        for cell, value in zip(tr.cells, values):
            cell.text = value


def has_drawing(p: Paragraph) -> bool:
    return bool(p._p.xpath(".//w:drawing"))


def replace_picture(p: Paragraph, path: Path, width_inches: float = 6.2) -> None:
    for child in list(p._p):
        if child.tag != qn("w:pPr"):
            p._p.remove(child)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=__import__("docx").shared.Inches(width_inches))


def extract_section_block(doc: Document, start: str, end: str) -> list:
    body = doc._body._element
    children = list(body)
    start_i = end_i = None
    for i, child in enumerate(children):
        if child.tag != qn("w:p"):
            continue
        value = Paragraph(child, doc._body).text.strip()
        if value.startswith(start):
            start_i = i
        elif start_i is not None and value.startswith(end):
            end_i = i
            break
    if start_i is None or end_i is None:
        raise ValueError(f"could not locate section block {start!r} to {end!r}")
    return children[start_i:end_i]


def archive_and_remove_unreproducible_section(si: Document) -> None:
    block = extract_section_block(si, "S6 Exploratory hierarchical Bayesian optimisation", "S7 Shared-start acquisition")
    lines = [
        "# Withdrawn historical SI section: exploratory hierarchical Bayesian optimisation",
        "",
        "This material was removed from the revised Supporting Information because the original configuration, input snapshots, and imported project modules needed to reproduce its 66-evaluation trace were unavailable. The search also consumed pose-derived Stage 2p features that were affected by the nitrene atom-mapping error. Its historical values are retained below for audit only; they are not corrected results and are not used to support any manuscript claim.",
        "",
        "Source: Supporting_Information_corrected_working.docx, former Section S6.",
        "",
    ]
    for child in block:
        if child.tag == qn("w:p"):
            text = Paragraph(child, si._body).text
            if text:
                lines.extend([text, ""])
        elif child.tag == qn("w:tbl"):
            tbl = Table(child, si._body)
            for row in tbl.rows:
                lines.append(" | ".join(cell.text.replace("\n", " / ") for cell in row.cells))
            lines.append("")
    archive_dir = HERE / "corrected_project" / "withdrawn_historical"
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "historical_section_S6.md").write_text("\n".join(lines), encoding="utf-8")
    body = si._body._element
    for child in block:
        body.remove(child)


def remove_empty_cube_caption(si: Document) -> None:
    for p in list(si.paragraphs):
        if p.text.startswith("Figure S4. Archived CUBE rendering removed"):
            p._p.getparent().remove(p._p)
            break


def move_final_section_before_references(si: Document) -> None:
    """Keep the illustrative substrate section before the bibliography."""
    body = si._body._element
    children = list(body)
    start = next(
        (child for child in children
         if child.tag == qn("w:p")
         and Paragraph(child, si._body).text.startswith("S15 Illustrative substrate structures")),
        None,
    )
    references = next(
        (child for child in children
         if child.tag == qn("w:p")
         and Paragraph(child, si._body).text.strip() == "Supporting references"),
        None,
    )
    if start is None or references is None:
        raise ValueError("Could not locate the S15 section and supporting references")
    children = list(body)
    start_i = children.index(start)
    end_i = next((i for i in range(start_i + 1, len(children)) if children[i].tag == qn("w:sectPr")), len(children))
    block = children[start_i:end_i]
    if start_i < children.index(references):
        return
    for child in block:
        body.remove(child)
    for child in block:
        references.addprevious(child)


def repair_early_figure_placements(si: Document) -> None:
    """Match the early corrected progression captions to their charts."""
    paragraphs = si.paragraphs
    captions = {}
    for i, paragraph in enumerate(paragraphs):
        if paragraph.text.startswith("Figure S4."):
            captions[4] = i
        elif paragraph.text.startswith("Figure S5."):
            captions[5] = i
    if 4 not in captions or 5 not in captions:
        raise ValueError("Could not locate final Figure S4/S5 captions")

    # S4 is the corrected CMC aryl yield AUC-MAE plot.
    s4_image = next(
        (paragraphs[j] for j in range(captions[4] - 1, max(-1, captions[4] - 5), -1)
         if has_drawing(paragraphs[j])),
        None,
    )
    if s4_image is None:
        raise ValueError("Could not locate the image paragraph for Figure S4")
    replace_picture(s4_image, HERE / "figures" / "figureS5_corrected_yield_auc.png")
    paragraphs[captions[4]].clear()
    paragraphs[captions[4]].add_run(
        "Figure S4. Corrected independent-progression yield AUC-MAE for the Fe(CMC-Por)Cl aryl cohort, "
        "comparing reported order with uncertainty–diversity using Elastic Net, Ridge, and Tanimoto-kNN. "
        "Lower values indicate lower integrated error across the retrospective reveal trajectory."
    )

    # Put the two-catalyst ee progression panel immediately before its caption.
    between = paragraphs[captions[4] + 1:captions[5]]
    s5_image = next((p for p in between if has_drawing(p)), None)
    if s5_image is None:
        s5_image = next((p for p in reversed(between) if not p.text.strip()), None)
    if s5_image is None:
        raise ValueError("Could not locate an image or blank paragraph for Figure S5")
    replace_picture(s5_image, HERE / "figures" / "figureS6_corrected_independent_acquisition.png")


SECTION_MAP = {n: n - 1 for n in range(7, 17)}
TABLE_MAP = {17: 13, 18: 14, 19: 15, 20: 16}
FIGURE_MAP = {5: 4, 6: 5, 8: 6, 9: 7, 10: 8, 11: 9}


def replace_ranges(text: str, prefix: str, mapping: dict[int, int]) -> str:
    pattern = re.compile(rf"\b({prefix})\s+S(\d+)([a-z]?)(?:\s*([–-])\s*S(\d+)([a-z]?))?", re.IGNORECASE)

    def sub(match: re.Match[str]) -> str:
        kind, first, suffix, dash, second, second_suffix = match.groups()
        number = int(first)
        value = f"{kind} S{mapping.get(number, number)}{suffix}"
        if dash and second:
            n2 = int(second)
            value += f"{dash}S{mapping.get(n2, n2)}{second_suffix or ''}"
        return value

    return pattern.sub(sub, text)


def renumber_si_references(doc: Document) -> None:
    mappings = [(r"Sections?", SECTION_MAP), (r"Tables?", TABLE_MAP), (r"Figures?|Figs?\.", FIGURE_MAP)]

    def apply(p) -> None:
        text = p.text
        for prefix, mapping in mappings:
            pattern = re.compile(rf"\b({prefix})\s+S(\d+)([a-z]?)(?:\s*([–-])\s*S(\d+)([a-z]?))?", re.IGNORECASE)

            def sub(match: re.Match[str]) -> str:
                kind, first, suffix, dash, second, second_suffix = match.groups()
                n = int(first)
                value = f"{kind} S{mapping.get(n, n)}{suffix}"
                if dash and second:
                    n2 = int(second)
                    value += f"{dash}S{mapping.get(n2, n2)}{second_suffix or ''}"
                return value

            text = pattern.sub(sub, text)
            list_pattern = re.compile(rf"\b((?:{prefix})\s+S\d+[a-z]?)((?:\s*(?:and|,|&)\s*S\d+[a-z]?)+)", re.IGNORECASE)

            def remap_tail(match: re.Match[str]) -> str:
                head, tail = match.groups()
                tail = re.sub(
                    r"S(\d+)([a-z]?)",
                    lambda m: f"S{mapping.get(int(m.group(1)), int(m.group(1)))}{m.group(2)}",
                    tail,
                    flags=re.IGNORECASE,
                )
                return head + tail

            text = list_pattern.sub(remap_tail, text)
        if re.match(r"^S\d+", text):
            m = re.match(r"^(S)(\d+)(.*)$", text)
            number = int(m.group(2))
            if number in SECTION_MAP:
                text = m.group(1) + str(SECTION_MAP[number]) + m.group(3)
        if text != p.text:
            p.clear()
            p.add_run(text)

    for p in doc.paragraphs:
        apply(p)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    apply(p)


def update_si(si: Document) -> None:
    # Withdraw unverified quantitative material before renumbering the SI.
    ptext(
        si,
        "The V4/V6 acquisition-weight study in Section S6",
        "An exploratory V4/V6 acquisition-weight search is excluded from this revised SI because its original configuration, input snapshots, and imported modules were unavailable for exact reanalysis. Its historical trace is retained for audit in corrected_project/withdrawn_historical/ and is not used as validation or evidence in the manuscript.",
    )
    ptext(
        si,
        "The original pose-feature code sometimes assumed that molecular atom index zero",
        "The original pose-feature code sometimes assumed that molecular atom index zero was the nitrene nitrogen. In affected suffix-style nitrene SMILES, atom zero is carbon. The corrected generator identifies the nitrene by molecular connectivity and propagated atom mapping, then uses that identity to construct nitrene-anchored geometry and select the transferable hydrogen. Source reaction outcomes and saved coordinates are unchanged; affected geometric features and dependent predictions were regenerated. Pre-correction outputs are retained in the correction archive only as historical records and are not reported as corrected results.",
    )
    ptext(
        si,
        "Corrected baseline, endpoint, and substrate-class findings:",
        "Corrected baseline, endpoint, and substrate-class findings: in the 20-split common-test ee analysis, QBC / expected-improvement / Thompson mean MAE was 13.078 / 13.896 / 14.418 for P7 and 13.400 / 16.408 / 15.331 for the CMC aryl cohort, compared with uncertainty–diversity means of 13.718 and 13.834. Corrected common-test yield MAE for source order / uncertainty–diversity / random was 25.36 / 18.38 / 20.93 for P7 and 25.48 / 23.49 / 24.53 for CMC; split-level results vary. Corrected sulfonyl-only source / uncertainty–diversity / random MAE was 17.98 / 19.22 / 19.63. These outcomes do not identify chemical mechanisms.",
    )
    ptext(
        si,
        "The corrected P7 Stage 2pp Elastic Net target-held-out MAE",
        "The corrected P7 Stage 2pp Elastic Net family-held-out MAE changed from 8.270 for fixed Stage 2p to 10.464 after adding 655 occupancy/flexibility fields (903 combined fields). The Stage 1-v2 selection and dependent Stage 2-v2/Stage 3a seed-pilot models have also been regenerated: 148/600 selected pose identities changed across four of 12 substrate sets, and the corrected 11-record ee model cohort gives MAEs of 6.775 (Stage 2 seed baseline), 15.201 (Stage 2-v2 selected poses), 6.886 (graph-only Stage 3a-alt), and 13.201 (Stage 3a reference/shell). The earlier 12-record shell comparison of 21.208 versus 22.019 is superseded.",
    )
    ptext(
        si,
        "The corrected independent progression tables S9–S12",
        "The corrected independent progression tables S9–S12 and figures S5–S6 replace the archived values below. Across all three estimators, uncertainty–diversity has lower AUC-MAE than reported order for Fe(P7)Cl and the Fe(CMC-Por)Cl aryl cohort on both ee and yield; diversity-first remains lower than uncertainty–diversity for CMC ee with Tanimoto-kNN. A corrected scan of all 13 shared aryl identities confirms that P7 1i / CMC 2r remains the largest-Jensen–Shannon-divergence pair (0.0310 bits; total variation 0.1719; Bhattacharyya overlap 0.9781). Corrected CREST/GFN2-xTB ablation estimates are shown in Tables S6–S7; their substrate-bootstrap intervals include zero. The unverified historical V4/V6 search is excluded from the revised SI and archived separately; retained quantitative analyses are identified with their corrected inputs and protocol limitations.",
    )
    ptext(
        si,
        "This Supporting Information provides the detailed datasets",
        "This Supporting Information provides the detailed datasets, representations, validation protocols, acquisition analyses, and computational records referenced in the main manuscript. Sections S1–S16 report the retained analyses; the unverified historical V4/V6 search is excluded from the revised SI and archived separately for audit.",
    )
    archive_and_remove_unreproducible_section(si)
    remove_empty_cube_caption(si)

    # Replace text that still described the pre-correction archive as the result.
    ptext(
        si,
        "The dedicated matched Ridge comparison underlying",
        "The dedicated matched Ridge comparison was replayed from the recorded route definitions using regenerated, corrected pose-derived features. Earlier mean-prefix values calculated from the invalid positional atom anchor are superseded; the revised table reports only the corrected replay. The corrected route curves, route summary, and replay script are retained in the revision analysis archive. Mean-prefix MAE is a route-specific trajectory summary, not a fixed-test-set estimate.",
    )
    ptext(
        si,
        "For Fe(P7)Cl, the archived learning curves are located",
        "The original archived learning curves and selection events are retained as historical provenance, but their pose-dependent feature values are not used in the corrected metrics. The replay uses the corrected fixed-version Stage 2p records and the route-specific initial substrate pairs listed below; corrected row-level curves and the recomputation script are included in corrected_project/analysis_runs/corrected_dedicated_replay/.",
    )
    ptext(
        si,
        "The recorded initial substrate pairs are",
        "The replayed route-specific initial pairs are 1a/1b for Fe(P7)Cl reported order and 1a/1am for uncertainty–diversity; for Fe(CMC-Por)Cl they are 2aa/2ab and 2b/2ac, respectively. These route-specific starts are distinct from the pseudorandom seed. Recalculation with corrected Stage 2p features gives mean-prefix Ridge ee MAEs of 25.508 and 7.475 for Fe(P7)Cl, and 16.977 and 9.641 for the Fe(CMC-Por)Cl aryl cohort (reported order and uncertainty–diversity, respectively). The old archived means are superseded. These reductions combine starting-scope and subsequent-order effects and are not evidence of population-level significance.",
    )
    ptext(
        si,
        "The mean paired differences versus source-order continuation are",
        "Across 50 shared starting pairs, the corrected mean paired source-order-minus-uncertainty–diversity differences are 9.83 ee points for Fe(P7)Cl and 4.84 for Fe(CMC-Por)Cl. Against the mean of three random continuations, the differences are 1.38 and 3.07 points; uncertainty–diversity is lower than random in 39/50 and 46/50 pairs, respectively. The route-specific remaining pools differ, so this sensitivity analysis is conditional on the observed substrate pools and sampled starts rather than a common-test-set comparison.",
    )
    ptext(
        si,
        "For a prespecified secondary check, the same 50 Fe(CMC-Por)Cl starting pairs",
        "For a prespecified secondary check, the same 50 Fe(CMC-Por)Cl starting pairs were evaluated on the seven locked ee-labelled records 2y, 2z and 4a–4e, excluded from the active pool. Ridge audit MAE was averaged over budgets of 6, 13 and 20 labels. The corrected mean source-order-minus-uncertainty–diversity difference is 3.88 ee points (conditional pair-bootstrap 95% interval 2.69 to 5.05), with uncertainty–diversity lower in 43/50 pairs. This small fixed audit is conditional on seven records and is not an external validation on a new catalyst.",
    )
    ptext(
        si,
        "The archive supports reconstruction of the reported aggregate learning curves",
        "The original run archive does not contain a complete frozen prediction-level execution record for both catalyst domains. The corrected replay therefore preserves this limitation and identifies its corrected inputs and route outputs explicitly; the historical archive is not presented as an exact reproduction of the earlier derived features.",
    )
    ptext(
        si,
        "In the separate sulfonyl-only replay, source-order / uncertainty–diversity / random MAEs were",
        "In the corrected sulfonyl-only replay, source-order / uncertainty–diversity / random MAEs were 17.98 / 19.22 / 19.63; uncertainty–diversity had lower error than source order in 6/20 splits and random in 10/20. This replay uses different test sets and budgets from the mixed analysis. Candidate pool, training composition and acquisition path differ jointly; these small overlapping splits are retrospective and cannot identify isolated causal effects, population significance or prospective performance. Split definitions, selections, predictions, input hashes, source audit and validation checks are retained in the accompanying analysis records.",
    )
    ptext(
        si,
        "All routes were scored with the same 1,287-field Ridge predictor",
        "All routes were scored with the same 1,287-field Ridge predictor on held-out records. MAEs were averaged over five budgets, three starts and, for random and Thompson sampling, three continuations before averaging over 20 splits. Corrected mean ee MAEs for source / uncertainty–diversity / QBC / EI / TS / random were 20.71 / 13.72 / 13.08 / 13.90 / 14.42 / 15.17 for Fe(P7)Cl and 16.33 / 13.83 / 13.40 / 16.41 / 15.33 / 15.05 for the Fe(CMC-Por)Cl aryl cohort. QBC has lower mean error than uncertainty–diversity in both datasets; EI also has lower mean error for Fe(P7)Cl. These implementation-specific results do not establish a universal ranking.",
    )
    ptext(
        si,
        "After correction, the Fe(P7)Cl Elastic Net target-held-out",
        "After correction, the Fe(P7)Cl Elastic Net target-held-out and family-held-out MAEs are 7.979 and 8.538 for structure plus pose, versus 12.612 and 10.406 for structure-only models. The family-held-out improvement is modest and heterogeneous: pose error is lower for 11/17 families and 23/38 substrates, while the largest family favours structure-only. A separate corrected family-held-out comparison using the fixed 248-field Stage 2p representation gives MAE 8.270; adding 655 Stage 2pp occupancy/flexibility fields (903 fields total) gives MAE 10.464. Its RMSE and R² are listed in Table S5. The Stage 2p + Stage 3b-only arm produced extreme out-of-family predictions under the selected low-regularisation setting and is labelled unstable rather than assigned a performance estimate.",
    )
    ptext(
        si,
        "The corrected structure-only and structure-plus-pose Elastic Net ee predictions",
        "The corrected structure-only and structure-plus-pose Elastic Net ee predictions were paired by substrate and checked against the 17 family-held-out split definitions. Across the 38 records, pose error is lower for 23; it lowers family MAE in 11 of 17 groups. Equal-weight family MAE is 11.99 points for structure-only and 8.72 for structure plus pose. The largest group (n=12) favours structure-only, 5.25 versus 6.23 points. These are retrospective, imbalanced family summaries, not evidence of reliable extrapolation to unseen chemical families.",
    )
    ptext(
        si,
        "This common-test analysis is distinct from the seven-record Fe(CMC-Por)Cl audit",
        "This common-test analysis is distinct from the seven-record Fe(CMC-Por)Cl audit and from the dedicated mean-prefix route comparison. The previously reported 55.3% and 33.2% reductions are superseded by corrected replay estimates of 70.7% and 43.2%, respectively. Neither set of route-specific trajectory reductions is a fixed-test estimate or evidence of population-level significance.",
    )
    ptext(
        si,
        "The Fe(CMC-Por)Cl source-order mean is influenced by one split",
        "In the corrected common-test analysis, Fe(CMC-Por)Cl source-order-minus-uncertainty–diversity differences have a mean of 2.50 ee points, median 0.13, interquartile range −0.92 to 4.30, and range −5.52 to 21.07; 11/20 splits favour uncertainty–diversity. For Fe(P7)Cl, the corresponding mean is 6.99, median 5.64, interquartile range 3.99 to 7.75, and range −0.09 to 27.69; 19/20 splits favour uncertainty–diversity. These repeated splits show heterogeneity, not a uniform advantage.",
    )
    ptext(
        si,
        "For the average split-level source-order-minus-uncertainty–diversity difference",
        "Conditional 95% bootstrap intervals for the mean split-level source-order-minus-uncertainty–diversity differences are 4.65 to 9.95 ee points for Fe(P7)Cl and 0.09 to 5.37 for Fe(CMC-Por)Cl. Against random continuation, the intervals are −0.42 to 3.53 and −0.03 to 2.59. These intervals describe resampling of 20 overlapping splits conditional on the observed datasets and chosen protocol; they are not population-level inference.",
    )

    # Replace stale Stage 2pp rows with the corrected, traceable family-held-out ablation.
    table = table_after(si, "Table S5.")
    fill(
        table,
        [
            ["Protocol and representation", "MAE", "RMSE", "R²"],
            ["Target holdout: structure only", "12.612", "15.183", "0.064"],
            ["Target holdout: structure + pose", "7.979", "10.964", "0.512"],
            ["Family holdout: structure only", "10.406", "13.525", "0.257"],
            ["Family holdout: structure + pose", "8.538", "11.447", "0.468"],
            ["Separate family holdout: fixed Stage 2p, 248 fields", "8.270", "12.441", "0.371"],
            ["Separate family holdout: Stage 2p + Stage 2pp, 903 fields", "10.464", "13.646", "0.244"],
            ["Nested families: corrected Stage 2p geometry", "9.801", "14.150", "0.187"],
            ["Nested families: +Stage 3a-alt", "9.834", "13.998", "0.204"],
            ["Nested families: +Stage 3b only (unstable)", "Not reported", "Not reported", "Not reported"],
            ["Nested families: +Stage 3a-alt +Stage 3b", "9.653", "13.371", "0.274"],
        ],
    )
    ptext(
        si,
        "Table S5. Fe(P7)Cl ee development",
        "Table S5. Corrected Fe(P7)Cl ee model comparisons. Rows belong to distinct validation blocks and are not all paired ablations; the separate 248/903-field Stage 2p/Stage 2pp comparison is family-held-out.",
    )
    ptext(
        si,
        "Later Stage 3 and CREST comparisons use the same 38 substrates",
        "Later Stage 3 and CREST comparisons use the same 38 substrates from 17 families with outer and inner leave-one-family-out evaluation, but a different validation implementation and locked 248-column geometry reference. The corrected Stage 2p/Stage 2pp family-held-out comparison is also a separate protocol block. No row in Table S5 should be compared across protocol blocks as if it were a paired ablation.",
    )
    ptext(
        si,
        "The archived Cartesian CUBE volume visualisation",
        "The archived Cartesian CUBE volume visualisation was generated from pre-correction fields and is removed from the revised SI. The corrected cylindrical fields are shown in Figure S2. An updated atom-resolved volumetric rendering was not generated, so no CUBE surface is used to support this comparison.",
    )
    ptext(
        si,
        "The revised data package and supporting records",
        "The corrected computational files, regenerated pose-derived features, downstream analyses, scripts, and correction inventory are included in the accompanying revision archive. Archived pre-correction outputs are retained only as historical records and are identified as superseded; they are not used as corrected results.",
    ) if any(p.text.startswith("The revised data package and supporting records") for p in si.paragraphs) else None
    ptext(
        si,
        "DATA_AVAILABILITY_STATEMENT.md documents the computational package's distribution details.",
        "The corrected computational data and code are included in the accompanying revision archive, with file manifests and reproduction instructions. Any public repository deposit should use this corrected release; archived outputs calculated with the superseded atom-index assumption are retained only as historical records. This Supporting Information is supplied separately as a document.",
    )
    ptext(
        si,
        "Reproduction requires the actual data and coordinate files",
        "Reproduction requires the actual data and coordinate files, not only directory names or inaccessible links. The corrected revision archive supplies the inputs, coordinates, scripts, and output records needed to rerun the documented analyses. For each analysis, match the endpoint, population IDs, representation, split or reveal sequence, estimator settings, and evaluation convention before comparing results. Corrected route metrics can be recalculated from the included corrected learning curves and route summaries (Section S5.3); the original archived runs are incomplete and do not support exact bitwise regeneration of their earlier pose-derived feature calculations.",
    )
    ptext(
        si,
        "Experimental source data originate from the two cited reaction studies",
        "Experimental source data originate from the two cited reaction studies [1,2]. The accompanying correction archive contains curated records, corrected atom mappings, regenerated pose-derived features, downstream analyses, scripts, manifests, and a pre/post correction inventory. Archived matched-acquisition records are retained as historical provenance; corrected aggregate metrics come from the corrected replay files included with this revision. The original source archive remains incomplete for bitwise reconstruction of its earlier feature calculations.",
    )

    # Make all retained illustrations traceable to the corrected runs.
    caption_updates = {
        "Figure S9.": "Figure S9. Remaining-pool ee MAE at each nonempty prefix. Solid lines show medians across the 50 shared initial pairs and shaded bands show interquartile ranges; dashed lines show corrected dedicated route-specific trajectories. These bands describe variation across sampled starts and are not confidence intervals. Each route has its own evolving remaining evaluation pool.",
        "Figure S10.": "Figure S10. Corrected repeated common-test-set paired differences in mean ee MAE. Each point is one of 20 overlapping outer test splits; within each split, scores average three shared starting pairs and five label budgets. Blue and orange points show source-order and random comparator-minus-uncertainty–diversity differences; horizontal lines show their means and the grey line marks zero. Positive differences favour uncertainty–diversity. Splits are not independent datasets.",
        "Figure S11.": "Figure S11. Corrected retrospective common-test Ridge MAE over the 21-point weight simplex for Fe(P7)Cl (left) and Fe(CMC-Por)Cl aryl (right). Each point is one (D,U,C) combination; colour shows mean MAE over the 20 overlapping split-level held-out scores. The star marks the default (0.40,0.40,0.20). Lower values indicate lower error; the display does not identify a general optimum.",
    }
    for prefix, value in caption_updates.items():
        ptext(si, prefix, value)
    ptext(
        si,
        "Figure S8. Shared-start sensitivity",
        "Figure S8. Corrected shared-start sensitivity of remaining-pool mean-prefix ee MAE. Each point is one of 50 initial substrate pairs; the box shows the interquartile range and the median line. Positive comparator-minus-uncertainty–diversity values favour uncertainty–diversity. Random continuation averages three continuations per pair. Pair resampling is conditional on the fixed observed substrate pools.",
    )

    # Remove draft-only warnings and point to the corrected atom-mapping procedure.
    if si.paragraphs and si.paragraphs[0].text.startswith("WORKING REVISION"):
        si.paragraphs[0].clear()
    ptext(
        si,
        "The canonical Stage 1 pose generator starts from free-nitrene SMILES",
        "The canonical Stage 1 pose generator starts from free-nitrene SMILES with explicit hydrogens, unlike the azide input to B5 and CREST. It requests 5,000 ETKDGv3 conformers with seed 20260730 and performs UFF relaxation with a 500-iteration limit per call [11,12,13]. The nitrene nitrogen is identified by its molecular connectivity and propagated atom mapping, not by assuming a fixed positional atom index; its bonded neighbour is used for alignment into the catalyst reference frame. A prior feature-generation path used atom index 0 as the nitrene anchor, which is not invariant to SMILES atom ordering. We corrected the structural identification and regenerated all dependent pose-centred fields and analyses reported here. Experimental ee/yield labels and source coordinates were not changed. Catalyst-core coordinates are copied unchanged and the reference Fe–N distance is checked to 10⁻5 Å. This is rigid catalyst-referenced assembly and screening, not optimisation of a complete catalyst–substrate complex.",
    )
    ptext(
        si,
        "Reproducible coordinates, 2D structure files, feature values, checks and corrected predictions",
        "Reproducible coordinates, 2D structure files, feature values, checks and corrected predictions are retained in the accompanying correction archive. The 2D structures are starting azides; the 3D views are sampled catalyst-bound nitrene assemblies. The companion project includes corrected atom mappings and regenerated downstream files; archived results based on the superseded atom-index assumption are marked historical and are not used in the revised manuscript.",
    )
    ptext(
        si,
        "The mean substrate-heavy-atom centroid-to-Fe distances across 200 retained poses",
        "The mean substrate-heavy-atom centroid-to-Fe distances across 200 retained poses are 4.515124 Å (1a) and 3.869390 Å (1ah); corresponding mean nitrene-nitrogen-to-reported-reactive-carbon distances are 3.460454 and 3.581514 Å. The centroid depends on molecular size and composition. Independent recalculation from the 200 archived coordinates exposed an incorrect original atom-index assumption for suffix-style nitrene SMILES, which has been corrected. All pose-dependent analyses retained in the revised manuscript and SI were regenerated or checked against the corrected mapping; earlier outputs are retained as historical records and are not presented as corrected results.",
    )
    ptext(
        si,
        "In a post hoc check, the selected structure-plus-pose Elastic Net model overpredicted all four low-ee Fe(P7)Cl targets",
        "In a post hoc check of the corrected predictions, the selected structure-plus-pose Elastic Net model overpredicted all four low-ee Fe(P7)Cl targets. Mean prediction-minus-observation was +17.85 ee points in target holdout and +18.56 in family holdout. These four examples do not support a population-wide performance estimate. The published scopes and this retrospective curation cannot establish how many reactions were attempted but not reported. Cohort-level row audit, split memberships, source hashes, validation checks and analysis code are retained in the accompanying correction archive.",
    )

    # Remove old figure caption placeholder, then apply section/table/figure numbering.
    renumber_si_references(si)

    # New figures are computed solely from corrected run records.
    figure_assets = {
        "Figure S6.": HERE / "figures" / "figureS6_corrected_shared_start.png",
        "Figure S7.": HERE / "figures" / "figureS7_corrected_shared_curves.png",
        "Figure S8.": HERE / "figures" / "figureS8_corrected_common_test.png",
        "Figure S9.": HERE / "figures" / "figureS9_corrected_weight_sensitivity.png",
    }
    paragraphs = si.paragraphs
    for i, p in enumerate(paragraphs):
        for caption, asset in figure_assets.items():
            if p.text.startswith(caption):
                previous = next((paragraphs[j] for j in range(i - 1, max(-1, i - 8), -1) if has_drawing(paragraphs[j])), None)
                if previous is None:
                    raise ValueError(f"picture paragraph preceding {caption} not found")
                replace_picture(previous, asset)

    move_final_section_before_references(si)
    repair_early_figure_placements(si)


def update_manuscript(manuscript: Document) -> None:
    if manuscript.paragraphs and manuscript.paragraphs[0].text.startswith("WORKING REVISION"):
        manuscript.paragraphs[0].clear()
    # Describe the correction explicitly in the methods and preserve its scope.
    ptext(
        manuscript,
        "Pose construction begins from the corresponding free-nitrene structure",
        "Pose construction begins from the corresponding free-nitrene structure with explicit hydrogens. ETKDGv3 generates conformers, which are relaxed with UFF and aligned through the nitrene nitrogen and its bonded neighbour into a fixed catalyst reference frame.[30,31,32] The nitrene nitrogen is identified by molecular connectivity and propagated atom mapping, not by assuming a fixed atom index. An earlier feature-generation path used atom index 0 as the nitrene anchor; because atom order varies with SMILES ordering, this misidentified the geometric reference in affected records. We corrected the atom identification and regenerated all dependent pose-derived fields and analyses reported here. Experimental ee/yield labels and source coordinates were unchanged. Catalyst coordinates remain rigid. Candidates must preserve connectivity, complete optimisation, and pass a catalyst–substrate clash screen in which the intended Fe–N(nitrene) distance is exempted from the general clash criterion. Valid geometries are ranked by UFF score, and non-overlapping low- and high-ranked strata are retained. The high-ranked stratum is a geometric-contrast representation, not a thermodynamic population. No ee or yield is used during pose generation, alignment, screening, ranking, or retention. Full criteria, mapping checks, and regenerated outputs are documented in SI Section S2 and the accompanying correction archive.",
    )
    ptext(
        manuscript,
        "Substrate-scope construction is an information-acquisition problem",
        "Substrate-scope construction is an information-acquisition problem: the order in which substrates are examined determines how efficiently catalyst behaviour is learned. Here, catalyst-contextual representation and information-guided substrate ordering were retrospectively reevaluated in two small iron-porphyrin datasets for enantioselective intramolecular C(sp3)–H amination after correction of a nitrene atom-mapping error. In Fe(P7)Cl Elastic Net comparisons, adding pose descriptors reduced target-held-out MAE from 12.61 to 7.98 ee points and family-held-out MAE from 10.41 to 8.54; the family result remains heterogeneous across 17 small, imbalanced groups. In corrected common-test acquisition analyses, uncertainty–diversity reduced mean ee MAE relative to source order by 6.99 points for Fe(P7)Cl and 2.50 for the Fe(CMC-Por)Cl aryl cohort, but its advantage over random selection was smaller and varied across splits. Query by committee had lower mean ee error in both common-test datasets. Corrected yield comparisons differed between catalysts, and full-pose/acquisition combinations did not outperform structure-only baselines on average. All results are retrospective and conditional on the two published datasets; corrected atom mapping, sensitivity analyses, and remaining limits are documented in the Supporting Information.",
    )
    ptext(
        manuscript,
        "The corrected Stage 2pp ablation does not support",
        "A separate corrected 17-family held-out Stage 2pp comparison does not support adding occupancy/flexibility fields to the fixed Stage 2p representation: Elastic Net MAE increased from 8.270 with 248 Stage 2p fields to 10.464 with 903 combined fields (248 Stage 2p plus 655 Stage 2pp). This comparison uses a different family-held-out protocol from the matched target/family benchmark above and is not interpreted as a direct cross-protocol contrast. It provides no evidence that the richer representation improves prediction in this small dataset.",
    )
    ptext(
        manuscript,
        "Experimental outcomes originate from the cited reaction studies.",
        "Experimental outcomes originate from the cited reaction studies. The accompanying correction archive contains the curated records, corrected nitrene-to-atom mappings, regenerated pose-derived features, downstream model and acquisition analyses, source scripts, manifests, and pre/post correction inventory. Archived outputs calculated with the superseded positional atom assumption are retained only as historical records and are explicitly identified as superseded. Corrected analysis files and reproduction instructions are included with the revision materials; a public repository deposit should use this corrected release.",
    )
    # Cross-references in the manuscript follow the revised SI numbering.
    containers = list(manuscript.paragraphs)
    for table in manuscript.tables:
        for row in table.rows:
            for cell in row.cells:
                containers.extend(cell.paragraphs)
    for p in containers:
        ptext_value = p.text
        ptext_value = replace_ranges(ptext_value, r"Sections?", SECTION_MAP)
        ptext_value = replace_ranges(ptext_value, r"Tables?", TABLE_MAP)
        ptext_value = replace_ranges(ptext_value, r"Figures?|Figs?\.", FIGURE_MAP)
        if ptext_value != p.text:
            p.clear()
            p.add_run(ptext_value)


def main() -> None:
    # The input manuscripts are the corrected working documents produced by the preceding finalizer.
    si_path = HERE / "Supporting_Information_corrected_working.docx"
    main_path = HERE / "Manuscript_corrected_working.docx"
    si = Document(si_path)
    manuscript = Document(main_path)
    update_si(si)
    update_manuscript(manuscript)
    si.save(si_path)
    manuscript.save(main_path)

    shutil.copy2(main_path, HERE / "Manuscript_revised_corrected.docx")
    shutil.copy2(si_path, HERE / "Supporting_Information_revised_corrected.docx")
    print("Updated corrected manuscript and Supporting Information.")


if __name__ == "__main__":
    main()

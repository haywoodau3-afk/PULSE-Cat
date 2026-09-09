#!/usr/bin/env python3
"""Build SI-ready figures and compact tables from the frozen PPTL artifacts.

The script deliberately omits XYZ coordinate payloads.  It only consumes the
persisted learning-curve summaries, transfer matrices, curated reaction
records, and the compact Stage 2pp SVG density views.
"""

from __future__ import annotations

import base64
import csv
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
from typing import Iterable

from rdkit import Chem


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "supporting-information"
FIG = OUT / "figures"
TAB = OUT / "tables"

COLORS = {
    "historical_order": "#6b7280",
    "uncertainty_diversity": "#d95f02",
    "diversity_first": "#1b9e77",
    "performance_first": "#7570b3",
    "random": "#1f78b4",
    "ridge": "#d95f02",
    "elastic_net": "#1b9e77",
    "tanimoto_knn": "#7570b3",
    "B": "#2166ac",
    "P": "#b2182b",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def svg_header(width: int, height: int, title: str, description: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        f'<title id="title">{esc(title)}</title><desc id="desc">{esc(description)}</desc>'
        '<rect width="100%" height="100%" fill="#ffffff"/>'
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#1f2937} '
        '.grid{stroke:#e5e7eb;stroke-width:1}.frame{stroke:#374151;stroke-width:1;fill:none} '
        '.axis{stroke:#374151;stroke-width:1}.tick{font-size:12px}.label{font-size:13px} '
        '.title{font-size:18px;font-weight:700}.subtitle{font-size:12px;fill:#4b5563} '
        '.legend{font-size:12px}</style>'
    )


def ticks(lo: float, hi: float, count: int = 5) -> list[float]:
    if hi <= lo:
        return [lo]
    step = (hi - lo) / count
    values = [lo + step * index for index in range(count + 1)]
    return values


def line_path(points: list[tuple[float, float]], sx, sy) -> str:
    return " ".join(("M" if index == 0 else "L") + f" {sx(x):.2f},{sy(y):.2f}" for index, (x, y) in enumerate(points))


def draw_line_panel(
    x: int,
    y: int,
    width: int,
    height: int,
    title: str,
    series: dict[str, list[tuple[float, float]]],
    bands: dict[str, list[tuple[float, float, float]]],
    x_label: str = "Number of labelled substrates",
    y_label: str = "EE MAE (percentage points)",
) -> str:
    margin = {"left": 68, "right": 18, "top": 42, "bottom": 54}
    px0, py0 = x + margin["left"], y + margin["top"]
    px1, py1 = x + width - margin["right"], y + height - margin["bottom"]
    all_x = [point[0] for values in series.values() for point in values]
    all_y = [point[1] for values in series.values() for point in values]
    all_y += [value for values in bands.values() for _, low, high in values for value in (low, high)]
    xmin, xmax = min(all_x), max(all_x)
    ymin, ymax = 0.0, max(all_y) * 1.08
    if ymax <= 0:
        ymax = 1.0
    sx = lambda value: px0 + (value - xmin) / (xmax - xmin or 1) * (px1 - px0)
    sy = lambda value: py1 - (value - ymin) / (ymax - ymin or 1) * (py1 - py0)
    out = [f'<g aria-label="{esc(title)}">', f'<text class="title" x="{x}" y="{y + 22}">{esc(title)}</text>']
    for value in ticks(ymin, ymax, 5):
        yy = sy(value)
        out.append(f'<line class="grid" x1="{px0:.2f}" y1="{yy:.2f}" x2="{px1:.2f}" y2="{yy:.2f}"/>')
        out.append(f'<text class="tick" text-anchor="end" x="{px0 - 8}" y="{yy + 4:.2f}">{value:.0f}</text>')
    x_ticks = sorted(set([xmin, xmax] + [round(v) for v in ticks(xmin, xmax, 4)]))
    for value in x_ticks:
        xx = sx(value)
        out.append(f'<line class="grid" x1="{xx:.2f}" y1="{py0:.2f}" x2="{xx:.2f}" y2="{py1:.2f}"/>')
        out.append(f'<text class="tick" text-anchor="middle" x="{xx:.2f}" y="{py1 + 20}">{value:g}</text>')
    out.append(f'<rect class="frame" x="{px0}" y="{py0}" width="{px1-px0}" height="{py1-py0}"/>')
    for name, values in bands.items():
        if not values:
            continue
        upper = [(xx, high) for xx, _, high in values]
        lower = [(xx, low) for xx, low, _ in reversed(values)]
        path = line_path(upper + lower, sx, sy) + " Z"
        color = COLORS.get(name, "#1f78b4")
        out.append(f'<path d="{path}" fill="{color}" opacity="0.14" stroke="none"/>')
    for name, values in series.items():
        color = COLORS.get(name, "#374151")
        dash = ' stroke-dasharray="6 4"' if name == "random" else ""
        out.append(f'<path d="{line_path(values, sx, sy)}" fill="none" stroke="{color}" stroke-width="2.2"{dash}/>')
        for xx, yy in values:
            out.append(f'<circle cx="{sx(xx):.2f}" cy="{sy(yy):.2f}" r="2.2" fill="{color}"/>')
    out.append(f'<text class="label" text-anchor="middle" x="{(px0+px1)/2:.2f}" y="{y + height - 10}">{esc(x_label)}</text>')
    out.append(f'<text class="label" text-anchor="middle" transform="rotate(-90 {x + 16} {(py0+py1)/2:.2f})" x="{x + 16}" y="{(py0+py1)/2:.2f}">{esc(y_label)}</text>')
    out.append("</g>")
    return "".join(out)


def draw_legend(x: int, y: int, names: Iterable[str], labels: dict[str, str]) -> str:
    out = [f'<g transform="translate({x},{y})">']
    cursor = 0
    for name in names:
        color = COLORS.get(name, "#374151")
        dash = ' stroke-dasharray="6 4"' if name == "random" else ""
        label = labels.get(name, name)
        out.append(f'<line x1="{cursor}" y1="0" x2="{cursor + 22}" y2="0" stroke="{color}" stroke-width="2.5"{dash}/>')
        out.append(f'<text class="legend" x="{cursor + 28}" y="4">{esc(label)}</text>')
        cursor += 28 + len(label) * 6.2 + 22
    return "".join(out) + "</g>"


def make_independent_learning() -> Path:
    paths = {
        "P7": ROOT / "data/jacs_2025/scope_progression/learning-curve-summary.csv",
        "CMC-Por aryl": ROOT / "data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/learning-curve-summary.csv",
    }
    routes = ["historical_order", "uncertainty_diversity", "diversity_first", "performance_first", "random"]
    labels = {
        "historical_order": "historical order",
        "uncertainty_diversity": "uncertainty + diversity",
        "diversity_first": "diversity first",
        "performance_first": "performance first",
        "random": "random (500 replicates)",
    }
    body = [svg_header(1240, 680, "Independent progressive learning curves", "Ridge EE MAE as labelled substrates are added independently in the P7 and CMC-Por aryl domains.")]
    for index, (domain, path) in enumerate(paths.items()):
        rows = [row for row in read_csv(path) if row["model"] == "ridge" and row["target"] == "ee_percent"]
        series: dict[str, list[tuple[float, float]]] = {}
        bands: dict[str, list[tuple[float, float, float]]] = {}
        for route in routes:
            selected = sorted((row for row in rows if row["route"] == route), key=lambda row: int(row["n_labeled"]))
            series[route] = [(float(row["n_labeled"]), float(row["mae_mean"])) for row in selected]
            if route == "random":
                bands[route] = [(float(row["n_labeled"]), float(row["mae_q25"]), float(row["mae_q75"])) for row in selected]
        body.append(draw_line_panel(30 + (index % 2) * 610, 70, 580, 500, domain, series, bands))
    body.append(draw_legend(60, 610, routes, labels))
    body.append('<text class="subtitle" x="60" y="642">Shaded band: random-route interquartile range. Lower MAE is better; all points are retrospective label-masked replays.</text>')
    body.append("</svg>")
    path = FIG / "si_fig1_independent_learning_curves.svg"
    path.write_text("".join(body), encoding="utf-8")
    return path


def make_model_variants() -> Path:
    paths = {
        "P7": ROOT / "data/jacs_2025/scope_progression/learning-curve-summary.csv",
        "CMC-Por aryl": ROOT / "data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/learning-curve-summary.csv",
    }
    models = ["ridge", "elastic_net", "tanimoto_knn"]
    labels = {"ridge": "Ridge", "elastic_net": "Elastic Net", "tanimoto_knn": "Tanimoto kNN"}
    body = [svg_header(1240, 680, "Independent model variants", "Ridge, Elastic Net, and Tanimoto kNN learning curves under the uncertainty-diversity route.")]
    for index, (domain, path) in enumerate(paths.items()):
        rows = [row for row in read_csv(path) if row["route"] == "uncertainty_diversity" and row["target"] == "ee_percent"]
        series = {}
        for model in models:
            selected = sorted((row for row in rows if row["model"] == model), key=lambda row: int(row["n_labeled"]))
            series[model] = [(float(row["n_labeled"]), float(row["mae_mean"])) for row in selected]
        body.append(draw_line_panel(30 + (index % 2) * 610, 70, 580, 500, domain, series, {}))
    body.append(draw_legend(210, 610, models, labels))
    body.append('<text class="subtitle" x="60" y="642">Same route and target domain; model choice changes only the estimator. Curves are deterministic route summaries.</text>')
    body.append("</svg>")
    path = FIG / "si_fig2_model_variant_curves.svg"
    path.write_text("".join(body), encoding="utf-8")
    return path


def transfer_arms() -> dict[str, dict[str, dict[str, float]]]:
    matrices = [
        ROOT / "data/expansion/pptl/bidirectional-ee-2d-matrix.json",
        ROOT / "data/expansion/pptl/bidirectional-ee-pose-matrix.json",
        ROOT / "data/expansion/pptl/matrix-ee-b5-p3-p4.json",
    ]
    out: dict[str, dict[str, dict[str, float]]] = {}
    for path in matrices:
        data = json.loads(path.read_text(encoding="utf-8"))
        for arm, payload in data["arms"].items():
            out.setdefault(arm, {})
            for direction, values in payload["directions"].items():
                out[arm][direction] = float(values["guarded_ensemble"]["mae"])
    return out


def make_version_bars() -> Path:
    values = transfer_arms()
    arms = [f"B{i}" for i in range(1, 6)] + [f"P{i}" for i in range(5)]
    directions = ["cmcpor_to_p7_aryl", "p7_to_cmcpor_aryl"]
    direction_labels = {directions[0]: "CMC-Por → P7", directions[1]: "P7 → CMC-Por"}
    body = [svg_header(1240, 680, "Guarded transfer across representation versions", "Guarded reciprocal EE MAE for the frozen B1-B5 and P0-P4 representation ladder.")]
    for panel, direction in enumerate(directions):
        x, y, w, h = 55 + panel * 610, 70, 560, 500
        left, top, right, bottom = x + 60, y + 42, x + w - 18, y + h - 62
        ymax = max(values[arm][direction] for arm in arms) * 1.18
        sx = lambda i: left + i / (len(arms) - 1) * (right - left)
        sy = lambda val: bottom - val / ymax * (bottom - top)
        body.append(f'<g><text class="title" x="{x}" y="{y+22}">{esc(direction_labels[direction])}</text>')
        for tick in ticks(0, ymax, 5):
            yy = sy(tick)
            body.append(f'<line class="grid" x1="{left}" y1="{yy:.2f}" x2="{right}" y2="{yy:.2f}"/>')
            body.append(f'<text class="tick" text-anchor="end" x="{left-8}" y="{yy+4:.2f}">{tick:.0f}</text>')
        body.append(f'<rect class="frame" x="{left}" y="{top}" width="{right-left}" height="{bottom-top}"/>')
        bar_w = max(12, (right - left) / len(arms) * 0.62)
        for index, arm in enumerate(arms):
            xx = sx(index)
            color = COLORS["B" if arm.startswith("B") else "P"]
            yy = sy(values[arm][direction])
            body.append(f'<rect x="{xx-bar_w/2:.2f}" y="{yy:.2f}" width="{bar_w:.2f}" height="{bottom-yy:.2f}" fill="{color}" opacity="0.88"/>')
            body.append(f'<text class="tick" text-anchor="middle" x="{xx:.2f}" y="{bottom+19}">{arm}</text>')
            body.append(f'<text class="tick" text-anchor="middle" x="{xx:.2f}" y="{yy-6:.2f}">{values[arm][direction]:.1f}</text>')
        body.append(f'<text class="label" text-anchor="middle" x="{(left+right)/2:.2f}" y="{y+h-12}">Representation arm</text>')
        body.append(f'<text class="label" text-anchor="middle" transform="rotate(-90 {x+16} {(top+bottom)/2:.2f})" x="{x+16}" y="{(top+bottom)/2:.2f}">Guarded EE MAE (percentage points)</text></g>')
    body.append('<text class="legend" x="60" y="610" fill="#2166ac">B = 2D descriptor/fingerprint ladder</text>')
    body.append('<text class="legend" x="360" y="610" fill="#b2182b">P = pose-containing ladder</text>')
    body.append('<text class="subtitle" x="60" y="642">Lower is better. P3/P4 are the compact transfer-pose tiers; values are retrospective and label-masked.</text>')
    body.append("</svg>")
    path = FIG / "si_fig3_representation_version_bars.svg"
    path.write_text("".join(body), encoding="utf-8")
    return path


def make_transfer_curves() -> Path:
    data = json.loads((ROOT / "data/expansion/pptl/matrix-ee-b5-p3-p4.json").read_text(encoding="utf-8"))
    arms = ["B5", "P3", "P4"]
    labels = {arm: arm for arm in arms}
    body = [svg_header(1240, 680, "Progressive reciprocal transfer curves", "Guarded ensemble EE MAE at each labelled prefix for B5, P3, and P4.")]
    for panel, direction in enumerate(["cmcpor_to_p7_aryl", "p7_to_cmcpor_aryl"]):
        series = {}
        for arm in arms:
            rows = sorted(data["arms"][arm]["directions"][direction]["rows"], key=lambda row: row["prefix_size"])
            series[arm] = [(float(row["prefix_size"]), float(row["ensemble_absolute_error"])) for row in rows]
        title = "CMC-Por → P7" if panel == 0 else "P7 → CMC-Por"
        body.append(draw_line_panel(30 + panel * 610, 70, 580, 500, title, series, {}))
    body.append(draw_legend(470, 610, arms, labels))
    body.append('<text class="subtitle" x="60" y="642">Guarded ensemble only; each point is the held-out substrate at that prefix. Lower is better.</text>')
    body.append("</svg>")
    path = FIG / "si_fig4_progressive_transfer_curves.svg"
    path.write_text("".join(body), encoding="utf-8")
    return path


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical_smiles(value: str | None) -> str | None:
    if not value:
        return None
    molecule = Chem.MolFromSmiles(value)
    if molecule is None:
        return None
    for atom in molecule.GetAtoms():
        atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(molecule, isomericSmiles=True)


def make_smiles_table() -> Path:
    sources = [
        ("P7", "fe-p7-cl", ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"),
        ("CMC-Por", "cmcpor-fecl", ROOT / "data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl"),
    ]
    overlap = json.loads((ROOT / "data/expansion/pptl/canonical-overlap.json").read_text(encoding="utf-8"))["all_overlap"]
    groups = {left["left_id"]: (group, "P7", left["right_id"]) for group, left in overlap.items()}
    groups.update({right["right_id"]: (group, "P7", right["left_id"]) for group, right in overlap.items()})
    rows: list[dict[str, object]] = []
    for domain, catalyst, path in sources:
        for record in load_records(path):
            structure = record["structure"]
            product_recorded = structure.get("provided_product_smiles") or structure.get("atom_mapped_product_smiles")
            product_status = "recorded" if product_recorded else "missing_in_curated_record"
            row = {
                "domain": domain,
                "catalyst_id": catalyst,
                "pathway": record["family"].get("family_id"),
                "substrate_id": record["substrate_id"],
                "product_id": record["product_id"],
                "starting_azide_smiles": structure.get("azide_smiles"),
                "starting_azide_smiles_canonical": canonical_smiles(structure.get("azide_smiles")),
                "starting_nitrene_smiles": structure.get("nitrene_smiles"),
                "product_smiles_recorded": product_recorded,
                "product_smiles_canonical": canonical_smiles(product_recorded),
                "product_smiles_status": product_status,
                "ee_percent": record["outcome"].get("ee_percent"),
                "yield_percent": record["outcome"].get("isolated_yield_percent"),
                "reported_reactive_site": record["reaction_center"].get("reported_reactive_site", {}).get("site_id"),
                "source_location": record["source"].get("location"),
                "canonical_overlap_group": "",
                "paired_substrate_id": "",
            }
            if record["substrate_id"] in groups:
                group, _, paired = groups[record["substrate_id"]]
                row["canonical_overlap_group"] = group
                row["paired_substrate_id"] = paired
            rows.append(row)
    columns = list(rows[0].keys())
    path = TAB / "si_substrate_smiles.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


def make_overlay_index() -> Path:
    overlap = json.loads((ROOT / "data/expansion/pptl/canonical-overlap.json").read_text(encoding="utf-8"))["all_overlap"]
    rows = []
    for group, pair in overlap.items():
        p7 = ROOT / f"data/jacs_2025/stage2pp/svg/{pair['left_id']}.svg"
        cmc = ROOT / f"data/expansion/catalyst_rerun/cmcpor_uff_full/stage2pp/svg/{pair['right_id']}.svg"
        rows.append({
            "canonical_overlap_group": group,
            "p7_substrate_id": pair["left_id"],
            "cmcpor_substrate_id": pair["right_id"],
            "p7_overlay_svg": str(p7.relative_to(ROOT)),
            "cmcpor_overlay_svg": str(cmc.relative_to(ROOT)),
            "p7_overlay_sha256": sha256(p7),
            "cmcpor_overlay_sha256": sha256(cmc),
        })
    path = TAB / "si_pose_overlay_index.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def make_pose_montage() -> Path:
    overlap = json.loads((ROOT / "data/expansion/pptl/canonical-overlap.json").read_text(encoding="utf-8"))["all_overlap"]
    chosen_groups = [
        "CCCCc1ccccc1N=[N+]=[N-]",
        "COc1ccc(CCc2ccccc2N=[N+]=[N-])cc1",
        "[N-]=[N+]=Nc1ccccc1CCc1cc2ccccc2o1",
    ]
    width, height = 1600, 880
    body = [svg_header(width, height, "Representative Stage 2pp pose overlays", "Four matched P7 and CMC-Por substrate pairs shown as compact occupancy overlays.")]
    cell_w, cell_h = 760, 500
    for index, group in enumerate(chosen_groups):
        pair = overlap[group]
        col, row = index % 2, index // 2
        x, y = 30 + col * cell_w, 70 + row * cell_h
        body.append(f'<g><text class="title" x="{x}" y="{y+22}">Pair {index+1}: P7 {esc(pair["left_id"])} / CMC-Por {esc(pair["right_id"])}</text>')
        for j, (label, path) in enumerate([
            ("P7", ROOT / f"data/jacs_2025/stage2pp/svg/{pair['left_id']}.svg"),
            ("CMC-Por", ROOT / f"data/expansion/catalyst_rerun/cmcpor_uff_full/stage2pp/svg/{pair['right_id']}.svg"),
        ]):
            raw = base64.b64encode(path.read_bytes()).decode("ascii")
            ix = x + (j * 365)
            iy = y + 35
            body.append(f'<text class="label" x="{ix}" y="{iy+14}">{label}</text>')
            body.append(f'<image x="{ix}" y="{iy+22}" width="350" height="207" preserveAspectRatio="xMidYMid meet" href="data:image/svg+xml;base64,{raw}"/>')
        body.append("</g>")
    body.append('<text class="subtitle" x="30" y="1080">Blue = top-UFF stratum; red = bottom-UFF stratum; gray = top-minus-bottom. These are vdW-scaled occupancy fields, not electron density.</text>')
    body.append("</svg>")
    path = FIG / "si_fig5_pose_overlay_montage.svg"
    path.write_text("".join(body), encoding="utf-8")
    return path


def make_manifest(paths: list[Path]) -> Path:
    artifacts = [
        ("P7 curated reaction records", ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl", "41 JSONL records"),
        ("CMC-Por curated reaction records", ROOT / "data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl", "50 JSONL records"),
        ("P7 independent learning curves", ROOT / "data/jacs_2025/scope_progression/learning-curve-summary.csv", "per-prefix summary"),
        ("CMC-Por independent learning curves", ROOT / "data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/learning-curve-summary.csv", "per-prefix summary"),
        ("PPTL transfer matrices", ROOT / "data/expansion/pptl/matrix-ee-b5-p3-p4.json", "B5/P3/P4 reciprocal rows"),
        ("PPTL 2D ladder matrix", ROOT / "data/expansion/pptl/bidirectional-ee-2d-matrix.json", "B1-B5 guarded transfer"),
        ("PPTL pose ladder matrix", ROOT / "data/expansion/pptl/bidirectional-ee-pose-matrix.json", "P0-P2 guarded transfer"),
        ("PPTL route comparison", ROOT / "data/expansion/pptl/historical-vs-ai-progressive-comparison.json", "historical versus AI route summary"),
        ("PPTL freeze note", ROOT / "docs/checkpoint-1-9-manuscript-freeze.md", "scope and claim boundary"),
        ("PPTL final report", ROOT / "data/expansion/pptl/pptl-final-report.md", "consolidated computational report"),
        ("PPTL generator freeze", ROOT / "data/expansion/pptl/generator-freeze-config.json", "provenance and equal-budget comparison"),
        ("PPTL publication lock", ROOT / "data/expansion/pptl/publication-ledger-lock.json", "P7/CMC lock digest"),
        ("SI experiment inventory", TAB / "si_experiment_inventory.csv", "manuscript experiment inventory"),
        ("SI feature-arm definitions", TAB / "si_feature_arm_definitions.csv", "frozen representation definitions"),
        ("SI representation progression", TAB / "si_representation_progression_ee.csv", "reciprocal EE representation metrics"),
        ("SI independent progression metrics", TAB / "si_independent_progressive_model_metrics.csv", "independent estimator progression metrics"),
        ("SI held-out model comparison", TAB / "si_holdout_model_comparison_ee.csv", "independent P7 held-out EE comparison"),
        ("SI model progression tables", TAB / "si_model_progression_tables.md", "combined Markdown tables"),
        ("SI model progression table builder", ROOT / "scripts/pptl/build_model_progression_tables.py", "reproducible table extraction script"),
    ]
    entries = []
    for label, path, description in artifacts:
        entries.append({"label": label, "path": str(path.relative_to(ROOT)), "description": description, "sha256": sha256(path), "bytes": path.stat().st_size})
    for path in paths:
        entries.append({"label": path.stem, "path": str(path.relative_to(ROOT)), "description": "generated SI artifact", "sha256": sha256(path), "bytes": path.stat().st_size})
    overlay_dirs = {
        "P7 Stage 2pp SVG overlays": ROOT / "data/jacs_2025/stage2pp/svg",
        "CMC-Por Stage 2pp SVG overlays": ROOT / "data/expansion/catalyst_rerun/cmcpor_uff_full/stage2pp/svg",
    }
    directory_counts = {label: len(list(path.glob("*.svg"))) for label, path in overlay_dirs.items()}
    manifest = {
        "schema_version": "supporting-information-manifest-v1",
        "generated_at": dt.date.today().isoformat(),
        "xyz_included": False,
        "xyz_policy": "Large XYZ coordinate caches are intentionally excluded from this SI draft; compact pose-derived SVG/feature artifacts remain referenced.",
        "directory_counts": directory_counts,
        "artifacts": entries,
    }
    path = OUT / "si_data_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    generated = [make_independent_learning(), make_model_variants(), make_version_bars(), make_transfer_curves(), make_pose_montage(), make_smiles_table(), make_overlay_index()]
    make_manifest(generated)
    print("Generated SI artifacts:")
    for path in generated:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()

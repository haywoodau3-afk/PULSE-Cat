#!/usr/bin/env python3
"""Build an RSC-ready two-panel independent ee acquisition figure.

The figure is intentionally written as SVG so the primary deliverable remains
vector artwork.  A high-resolution PNG is generated separately from the SVG
using the bundled image runtime.
"""

from __future__ import annotations

import csv
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "supporting-information" / "figures"
WIDTH = 1800
HEIGHT = 1160

ROUTE_COLORS = {
    "historical_order": "#5B6770",
    "uncertainty_diversity": "#D55E00",
    "diversity_first": "#009E73",
    "performance_first": "#CC79A7",
    "random": "#0072B2",
}
ROUTE_LABELS = {
    "historical_order": "historical order",
    "uncertainty_diversity": "uncertainty + diversity",
    "diversity_first": "diversity first",
    "performance_first": "performance first",
    "random": "random (500 replicates)",
}
MODEL_COLORS = {
    "elastic_net": "#009E73",
    "ridge": "#D55E00",
    "tanimoto_knn": "#0072B2",
}
MODEL_LABELS = {
    "elastic_net": "Elastic Net",
    "ridge": "Ridge",
    "tanimoto_knn": "Tanimoto kNN",
}
MODEL_SYMBOLS = {"elastic_net": "circle", "ridge": "square", "tanimoto_knn": "triangle"}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def text(x: float, y: float, content: str, *, cls: str = "body", anchor: str = "start", fill: str | None = None) -> str:
    fill_attr = f' fill="{fill}"' if fill else ""
    return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}"{fill_attr}>{esc(content)}</text>'


def line(x1: float, y1: float, x2: float, y2: float, *, cls: str = "axis", stroke: str | None = None, dash: str | None = None) -> str:
    stroke_attr = f' stroke="{stroke}"' if stroke else ""
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"{stroke_attr}{dash_attr}/>'


def marker(cx: float, cy: float, kind: str, color: str, size: float = 7.0) -> str:
    if kind == "circle":
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{size:.1f}" fill="{color}" stroke="#ffffff" stroke-width="2"/>'
    if kind == "square":
        side = size * 1.75
        return f'<rect x="{cx-side/2:.1f}" y="{cy-side/2:.1f}" width="{side:.1f}" height="{side:.1f}" fill="{color}" stroke="#ffffff" stroke-width="2"/>'
    points = f"{cx:.1f},{cy-size:.1f} {cx-size*0.95:.1f},{cy+size*0.8:.1f} {cx+size*0.95:.1f},{cy+size*0.8:.1f}"
    return f'<polygon points="{points}" fill="{color}" stroke="#ffffff" stroke-width="2"/>'


def scale_x(value: float, lo: float, hi: float, left: float, right: float) -> float:
    return left + (value - lo) / (hi - lo) * (right - left)


def scale_y(value: float, lo: float, hi: float, top: float, bottom: float) -> float:
    return bottom - (value - lo) / (hi - lo) * (bottom - top)


def top_panel(rows: list[dict[str, str]]) -> str:
    left, right, top, bottom = 185, 1760, 170, 555
    xmin, xmax, ymin, ymax = 2.0, 37.0, 0.0, 45.0
    routes = ["historical_order", "uncertainty_diversity", "diversity_first", "performance_first", "random"]
    out: list[str] = []
    out.append(text(78, 80, "(a)", cls="panel-label"))
    out.append(text(145, 80, "Representative Fe(P7)Cl Ridge learning trajectories", cls="title"))
    out.append(text(145, 112, "Independent ee acquisition routes; lower MAE is better", cls="subtitle"))

    for tick in (0, 10, 20, 30, 40):
        y = scale_y(tick, ymin, ymax, top, bottom)
        out.append(line(left, y, right, y, cls="grid"))
        out.append(text(left - 18, y + 7, f"{tick}", cls="tick", anchor="end"))
    for tick in (2, 10, 20, 30, 37):
        x = scale_x(tick, xmin, xmax, left, right)
        out.append(line(x, top, x, bottom, cls="grid"))
        out.append(text(x, bottom + 34, f"{tick}", cls="tick", anchor="middle"))
    out.append(f'<rect class="frame" x="{left}" y="{top}" width="{right-left}" height="{bottom-top}"/>')

    for route in routes:
        selected = sorted((row for row in rows if row["route"] == route), key=lambda row: int(row["n_labeled"]))
        points = [
            (
                scale_x(float(row["n_labeled"]), xmin, xmax, left, right),
                scale_y(float(row["mae_mean"]), ymin, ymax, top, bottom),
            )
            for row in selected
        ]
        if not points:
            continue
        color = ROUTE_COLORS[route]
        point_string = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        dash_attr = ' stroke-dasharray="15 10"' if route == "random" else ""
        out.append(f'<polyline points="{point_string}" fill="none" stroke="{color}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"{dash_attr}/>')
        if route == "random":
            upper = [
                (
                    scale_x(float(row["n_labeled"]), xmin, xmax, left, right),
                    scale_y(float(row["mae_q75"]), ymin, ymax, top, bottom),
                )
                for row in selected
            ]
            lower = [
                (
                    scale_x(float(row["n_labeled"]), xmin, xmax, left, right),
                    scale_y(float(row["mae_q25"]), ymin, ymax, top, bottom),
                )
                for row in reversed(selected)
            ]
            band = " ".join(f"{x:.1f},{y:.1f}" for x, y in upper + lower)
            out.insert(-1, f'<polygon points="{band}" fill="{color}" opacity="0.16" stroke="none"/>')
        for x, y in points[::2]:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{color}" stroke="#ffffff" stroke-width="1.3"/>')

    out.append(text((left + right) / 2, 615, "Number of labelled substrates", cls="axis-label", anchor="middle"))
    out.append(f'<text class="axis-label" text-anchor="middle" transform="rotate(-90 65 {(top+bottom)/2:.1f})" x="65" y="{(top+bottom)/2:.1f}">EE MAE (percentage points)</text>')

    legend_x = 270
    legend_y = 142
    cursor_x = legend_x
    cursor_y = legend_y
    max_x = 1660
    for index, route in enumerate(routes):
        label = ROUTE_LABELS[route]
        item_width = 270 if route == "uncertainty_diversity" else 220
        if cursor_x + item_width > max_x:
            cursor_x = legend_x
            cursor_y += 30
        dash_attr = ' stroke-dasharray="15 10"' if route == "random" else ""
        color = ROUTE_COLORS[route]
        out.append(line(cursor_x, cursor_y - 5, cursor_x + 42, cursor_y - 5, cls="legend-line", stroke=color, dash="15 10" if route == "random" else None))
        out.append(text(cursor_x + 52, cursor_y, label, cls="legend"))
        cursor_x += item_width
    out.append(text(145, 655, "Shaded band: random-route interquartile range. Reported order is source presentation order, not verified laboratory chronology.", cls="note"))
    return "".join(out)


def bottom_panel(rows: list[dict[str, str]]) -> str:
    left, right, top, bottom = 185, 1760, 790, 1030
    ymin, ymax = 150.0, 360.0
    models = ["elastic_net", "ridge", "tanimoto_knn"]
    domains = [("CMC-Por aryl", "CMC-Por aryl", 560.0), ("P7", "Fe(P7)Cl", 1370.0)]
    out: list[str] = []
    out.append(text(78, 710, "(b)", cls="panel-label"))
    out.append(text(145, 710, "Integrated learning error across estimators and catalyst domains", cls="title"))
    out.append(text(145, 742, "Uncertainty + diversity route; ee target; lower AUC–MAE is better", cls="subtitle"))

    for tick in (150, 200, 250, 300, 350):
        y = scale_y(tick, ymin, ymax, top, bottom)
        out.append(line(left, y, right, y, cls="grid"))
        out.append(text(left - 18, y + 7, f"{tick}", cls="tick", anchor="end"))
    out.append(f'<rect class="frame" x="{left}" y="{top}" width="{right-left}" height="{bottom-top}"/>')

    lookup = {(row["domain"], row["model"]): float(row["auc_mae"]) for row in rows}
    offsets = {"elastic_net": -220.0, "ridge": 0.0, "tanimoto_knn": 220.0}
    for lookup_domain, display_domain, center in domains:
        for model in models:
            value = lookup[(lookup_domain, model)]
            x = center + offsets[model]
            y = scale_y(value, ymin, ymax, top, bottom)
            color = MODEL_COLORS[model]
            out.append(line(x, bottom, x, y, cls="stem", stroke=color))
            out.append(marker(x, y, MODEL_SYMBOLS[model], color, size=9.0))
            label_y = y - 20 if y > top + 32 else y + 30
            out.append(text(x, label_y, f"{value:.1f}", cls="value", anchor="middle"))
        out.append(text(center, bottom + 40, display_domain, cls="domain", anchor="middle"))

    out.append(text(65, (top + bottom) / 2, "AUC–MAE", cls="axis-label", anchor="middle"))
    out[-1] = f'<text class="axis-label" text-anchor="middle" transform="rotate(-90 65 {(top+bottom)/2:.1f})" x="65" y="{(top+bottom)/2:.1f}">AUC–MAE (integrated EE MAE)</text>'

    legend_x, legend_y = 1240.0, 752.0
    for index, model in enumerate(models):
        x = legend_x + index * 175
        out.append(marker(x, legend_y - 6, MODEL_SYMBOLS[model], MODEL_COLORS[model], size=7.5))
        out.append(text(x + 18, legend_y, MODEL_LABELS[model], cls="legend"))
    out.append(text(145, 1125, "AUC–MAE is the trapezoidal integral of the learning-curve MAE across the labelled-substrate progression.", cls="note"))
    return "".join(out)


def build_svg() -> Path:
    p7_path = ROOT / "data" / "jacs_2025" / "scope_progression" / "learning-curve-summary.csv"
    metrics_path = ROOT / "docs" / "supporting-information" / "tables" / "si_independent_progressive_model_metrics.csv"
    p7_rows = [row for row in read_csv(p7_path) if row["model"] == "ridge" and row["target"] == "ee_percent"]
    metric_rows = [
        row
        for row in read_csv(metrics_path)
        if row["target"] == "ee_percent" and row["route"] == "uncertainty_diversity"
    ]

    OUT.mkdir(parents=True, exist_ok=True)
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="180mm" height="116mm" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Independent ee acquisition robustness analyses</title>
  <desc id="desc">Representative Fe(P7)Cl Ridge learning trajectories and integrated learning error across estimators and catalyst domains.</desc>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <style>
    text {{ font-family: Arial, Helvetica, sans-serif; fill: #1f2933; }}
    .title {{ font-size: 31px; font-weight: 700; }}
    .subtitle {{ font-size: 23px; fill: #4b5563; }}
    .panel-label {{ font-size: 34px; font-weight: 700; }}
    .body {{ font-size: 24px; }}
    .tick {{ font-size: 22px; fill: #374151; }}
    .legend {{ font-size: 21px; }}
    .axis-label {{ font-size: 24px; }}
    .note {{ font-size: 19px; fill: #4b5563; }}
    .domain {{ font-size: 23px; font-weight: 600; }}
    .value {{ font-size: 20px; font-weight: 600; }}
    .grid {{ stroke: #d9dee3; stroke-width: 1.5; }}
    .frame {{ fill: none; stroke: #374151; stroke-width: 2; }}
    .axis {{ stroke: #374151; stroke-width: 2; }}
    .legend-line {{ stroke-width: 5; }}
    .stem {{ stroke-width: 3; opacity: 0.55; }}
  </style>
  {top_panel(p7_rows)}
  {bottom_panel(metric_rows)}
</svg>
'''
    path = OUT / "si_fig1_independent_ee_acquisition_rsc.svg"
    path.write_text(svg, encoding="utf-8")
    return path


if __name__ == "__main__":
    print(build_svg())

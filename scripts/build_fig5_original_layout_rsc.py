#!/usr/bin/env python3
"""Rebuild the original two-panel ee acquisition figure at RSC scale.

Panel A preserves the original seven-curve Fe(P7)Cl Ridge route plot. Panel B
preserves the original paired AUC-MAE bars comparing reported order with the
uncertainty–diversity route across estimators and catalyst domains.
"""

from __future__ import annotations

import csv
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "output" / "figures" / "figure3_data"
METRICS = ROOT / "docs" / "supporting-information" / "tables" / "si_independent_progressive_model_metrics.csv"
OUT = ROOT / "output" / "supporting-information" / "figures"
WIDTH = 1800
HEIGHT = 1800

COLORS = {
    "reported_order": "#7F879C",
    "diversity_first": "#7C5CFF",
    "performance_first": "#D97706",
    "random_mean": "#A4ABBA",
    "random_q25": "#B8BFCC",
    "random_q75": "#B8BFCC",
    "uncertainty_diversity": "#0F766E",
    "auc_reported": "#626A82",
    "auc_uncertainty": "#146B66",
}
LABELS = {
    "reported_order": "reported_order",
    "diversity_first": "diversity_first",
    "performance_first": "performance_first",
    "random_mean": "random_mean",
    "random_q25": "random_q25",
    "random_q75": "random_q75",
    "uncertainty_diversity": "uncertainty_diversity",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def tx(x: float, y: float, value: str, size: float, *, anchor: str = "start", fill: str = "#253041", weight: str = "400", italic: bool = False) -> str:
    style = f"font-size:{size}px;font-weight:{weight};" + ("font-style:italic;" if italic else "")
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="{fill}" style="{style}">{esc(value)}</text>'


def ln(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#98A2B3", width: float = 1.5, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width:.1f}"{dash_attr}/>'


def polyline(points: list[tuple[float, float]], *, stroke: str, width: float, dash: str | None = None) -> str:
    point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline points="{point_text}" fill="none" stroke="{stroke}" stroke-width="{width:.1f}" stroke-linecap="round" stroke-linejoin="round"{dash_attr}/>'


def sx(value: float, lo: float, hi: float, left: float, right: float) -> float:
    return left + (value - lo) / (hi - lo) * (right - left)


def sy(value: float, lo: float, hi: float, top: float, bottom: float) -> float:
    return bottom - (value - lo) / (hi - lo) * (bottom - top)


def legend_item(x: float, y: float, key: str, line_width: float, dash: str | None = None) -> str:
    out = [ln(x, y - 6, x + 40, y - 6, stroke=COLORS[key], width=line_width, dash=dash)]
    out.append(tx(x + 50, y, LABELS[key], 24, fill="#344054"))
    return "".join(out)


def panel_a(rows: list[dict[str, str]]) -> str:
    left, right, top, bottom = 248, 1740, 170, 870
    xlo, xhi, ylo, yhi = 2.0, 37.0, 0.0, 50.0
    out: list[str] = []
    out.append(tx(38, 62, "(A)", 34, weight="500"))

    # Keep the original two-row legend arrangement, but give it publication-safe type.
    out.append(legend_item(250, 48, "reported_order", 2.2))
    out.append(legend_item(535, 48, "diversity_first", 2.2))
    out.append(legend_item(800, 48, "performance_first", 2.2, "10 4 2 4"))
    out.append(legend_item(1085, 48, "random_mean", 2.2, "2 4"))
    out.append(legend_item(1380, 48, "uncertainty_diversity", 4.0))
    out.append(legend_item(250, 84, "random_q25", 2.0, "6 4"))
    out.append(legend_item(535, 84, "random_q75", 2.0, "1 4"))
    out.append(tx((left + right) / 2, 132, "Fe(P7)Cl route trajectories (Ridge)", 30, anchor="middle", weight="500"))

    for tick in (0, 12.5, 25, 37.5, 50):
        y = sy(tick, ylo, yhi, top, bottom)
        out.append(ln(left, y, right, y, stroke="#C9CED7", width=1.3))
        out.append(tx(left - 18, y + 8, f"{tick:g}", 24, anchor="end", fill="#344054"))
    for tick in range(2, 38):
        x = sx(tick, xlo, xhi, left, right)
        out.append(ln(x, bottom, x, bottom + 7, stroke="#98A2B3", width=1.0))
        out.append(tx(x, bottom + 29, str(tick), 20, anchor="middle", fill="#475467"))
    out.append(f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="none" stroke="#667085" stroke-width="1.8"/>')

    route_specs = [
        ("random_q25", 1.7, "6 4"),
        ("random_q75", 1.7, "1 4"),
        ("random_mean", 2.0, "2 4"),
        ("reported_order", 2.2, None),
        ("diversity_first", 2.2, None),
        ("performance_first", 2.2, "10 4 2 4"),
        ("uncertainty_diversity", 3.8, None),
    ]
    source_keys = {"reported_order": "historical_order"}
    for key, width, dash in route_specs:
        points = [
            (sx(float(row["n_labeled"]), xlo, xhi, left, right), sy(float(row[source_keys.get(key, key)]), ylo, yhi, top, bottom))
            for row in rows
        ]
        out.append(polyline(points, stroke=COLORS[key], width=width, dash=dash))

    out.append(tx((left + right) / 2, 940, "Revealed substrates", 26, anchor="middle", fill="#344054"))
    out.append(f'<text x="92" y="{(top+bottom)/2:.1f}" text-anchor="middle" fill="#344054" transform="rotate(-90 92 {(top+bottom)/2:.1f})" style="font-size:26px;font-weight:400">ee MAE (percentage points)</text>')
    return "".join(out)


def auc_rows() -> list[tuple[str, str, float, float]]:
    rows = [row for row in read_csv(METRICS) if row["target"] == "ee_percent" and row["route"] in {"historical_order", "uncertainty_diversity"}]
    lookup = {(row["domain"], row["model"], row["route"]): float(row["auc_mae"]) for row in rows}
    specs = [
        ("Fe(P7)Cl", "P7", "elastic_net"),
        ("Fe(P7)Cl", "P7", "ridge"),
        ("Fe(P7)Cl", "P7", "tanimoto_knn"),
        ("Fe(CMC-Por)Cl", "CMC-Por aryl", "elastic_net"),
        ("Fe(CMC-Por)Cl", "CMC-Por aryl", "ridge"),
        ("Fe(CMC-Por)Cl", "CMC-Por aryl", "tanimoto_knn"),
    ]
    return [
        (label, model, lookup[(domain, model, "historical_order")], lookup[(domain, model, "uncertainty_diversity")])
        for label, domain, model in specs
    ]


def panel_b(rows: list[tuple[str, str, float, float]]) -> str:
    left, right, top, bottom = 248, 1740, 1055, 1660
    ylo, yhi = 0.0, 800.0
    out: list[str] = []
    out.append(tx(38, 1024, "(B)", 34, weight="500"))

    # The original paired-bar legend sits above the right side of the chart.
    out.append(ln(1040, 1022, 1078, 1022, stroke=COLORS["auc_reported"], width=24))
    out.append(tx(1090, 1030, "Reported AUC-MAE", 24, fill="#344054"))
    out.append(ln(1380, 1022, 1418, 1022, stroke=COLORS["auc_uncertainty"], width=24))
    out.append(tx(1430, 1030, "Uncertainty–diversity AUC-MAE", 24, fill="#344054"))

    for tick in (0, 200, 400, 600, 800):
        y = sy(tick, ylo, yhi, top, bottom)
        out.append(ln(left, y, right, y, stroke="#C9CED7", width=1.3))
        out.append(tx(left - 18, y + 8, f"{tick:g}", 24, anchor="end", fill="#344054"))
    out.append(f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="none" stroke="#667085" stroke-width="1.8"/>')

    x_positions = [385, 625, 865, 1125, 1365, 1605]
    for x, (domain_label, model, reported, uncertainty) in zip(x_positions, rows):
        bar_w = 62
        gap = 9
        x_reported = x - bar_w - gap / 2
        x_uncertainty = x + gap / 2
        y_reported = sy(reported, ylo, yhi, top, bottom)
        y_uncertainty = sy(uncertainty, ylo, yhi, top, bottom)
        out.append(f'<rect x="{x_reported:.1f}" y="{y_reported:.1f}" width="{bar_w:.1f}" height="{bottom-y_reported:.1f}" fill="{COLORS["auc_reported"]}"/>')
        out.append(f'<rect x="{x_uncertainty:.1f}" y="{y_uncertainty:.1f}" width="{bar_w:.1f}" height="{bottom-y_uncertainty:.1f}" fill="{COLORS["auc_uncertainty"]}"/>')
        label = domain_label.replace("Fe(", "Fe(")
        out.append(tx(x, bottom + 35, label, 22, anchor="middle", fill="#344054"))
        model_label = model.replace("tanimoto_knn", "Tanimoto-kNN").replace("elastic_net", "Elastic Net").replace("ridge", "Ridge")
        out.append(tx(x, bottom + 64, model_label, 22, anchor="middle", fill="#344054"))

    out.append(f'<text x="92" y="{(top+bottom)/2:.1f}" text-anchor="middle" fill="#344054" transform="rotate(-90 92 {(top+bottom)/2:.1f})" style="font-size:26px;font-weight:400">AUC-MAE</text>')
    return "".join(out)


def build_svg() -> Path:
    route_rows = read_csv(DATA / "panel_a_p7_ridge_route_progression.csv")
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="180mm" height="180mm" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Independent ee acquisition robustness analyses</title>
  <desc id="desc">Original two-panel composition: Fe(P7)Cl Ridge route trajectories and paired reported-order versus uncertainty-diversity AUC-MAE bars across estimators and catalyst domains.</desc>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <style>
    text {{ font-family: Arial, Helvetica, sans-serif; }}
  </style>
  {panel_a(route_rows)}
  {panel_b(auc_rows())}
</svg>
'''
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "fig5_independent_ee_acquisition_original_layout_rsc.svg"
    path.write_text(svg, encoding="utf-8")
    return path


if __name__ == "__main__":
    print(build_svg())

#!/usr/bin/env python3
"""Build a compact square, single-column version of the original A/B figure."""

from __future__ import annotations

import csv
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "output" / "figures" / "figure3_data"
METRICS = ROOT / "docs" / "supporting-information" / "tables" / "si_independent_progressive_model_metrics.csv"
OUT = ROOT / "output" / "supporting-information" / "figures"
WIDTH = 900
HEIGHT = 900

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


def tx(x: float, y: float, value: str, size: float, *, anchor: str = "start", fill: str = "#253041", weight: str = "400") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="{fill}" style="font-size:{size}px;font-weight:{weight}">{esc(value)}</text>'


def ln(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#98A2B3", width: float = 1.2, dash: str | None = None) -> str:
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
    return ln(x, y - 5, x + 28, y - 5, stroke=COLORS[key], width=line_width, dash=dash) + tx(x + 36, y, LABELS[key], 22, fill="#344054")


def panel_a(rows: list[dict[str, str]]) -> str:
    left, right, top, bottom = 115, 875, 180, 465
    xlo, xhi, ylo, yhi = 2.0, 37.0, 0.0, 50.0
    out: list[str] = [tx(18, 33, "(A)", 28, weight="500")]

    # Three compact legend rows retain all seven original series.
    out.append(legend_item(115, 28, "reported_order", 1.8))
    out.append(legend_item(365, 28, "diversity_first", 1.8))
    out.append(legend_item(600, 28, "performance_first", 1.8, "8 3 2 3"))
    out.append(legend_item(115, 58, "random_mean", 1.8, "2 3"))
    out.append(legend_item(365, 58, "random_q25", 1.7, "5 3"))
    out.append(legend_item(600, 58, "random_q75", 1.7, "1 3"))
    out.append(legend_item(115, 88, "uncertainty_diversity", 3.0))
    out.append(tx((left + right) / 2, 132, "Fe(P7)Cl route trajectories (Ridge)", 25, anchor="middle", weight="500"))

    for tick in (0, 12.5, 25, 37.5, 50):
        y = sy(tick, ylo, yhi, top, bottom)
        out.append(ln(left, y, right, y, stroke="#C9CED7", width=1.0))
        out.append(tx(left - 12, y + 7, f"{tick:g}", 21, anchor="end", fill="#344054"))
    for tick in (2, 5, 10, 15, 20, 25, 30, 35, 37):
        x = sx(tick, xlo, xhi, left, right)
        out.append(ln(x, bottom, x, bottom + 5, stroke="#98A2B3", width=0.8))
        out.append(tx(x, bottom + 22, str(tick), 18, anchor="middle", fill="#475467"))
    out.append(f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="none" stroke="#667085" stroke-width="1.4"/>')

    route_specs = [
        ("random_q25", 1.3, "5 3"),
        ("random_q75", 1.3, "1 3"),
        ("random_mean", 1.5, "2 3"),
        ("reported_order", 1.7, None),
        ("diversity_first", 1.7, None),
        ("performance_first", 1.7, "8 3 2 3"),
        ("uncertainty_diversity", 2.9, None),
    ]
    source_keys = {"reported_order": "historical_order"}
    for key, width, dash in route_specs:
        points = [
            (sx(float(row["n_labeled"]), xlo, xhi, left, right), sy(float(row[source_keys.get(key, key)]), ylo, yhi, top, bottom))
            for row in rows
        ]
        out.append(polyline(points, stroke=COLORS[key], width=width, dash=dash))

    out.append(tx((left + right) / 2, 505, "Revealed substrates", 24, anchor="middle", fill="#344054"))
    out.append(f'<text x="48" y="{(top+bottom)/2:.1f}" text-anchor="middle" fill="#344054" transform="rotate(-90 48 {(top+bottom)/2:.1f})" style="font-size:23px;font-weight:400">ee MAE (percentage points)</text>')
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
    left, right, top, bottom = 115, 875, 580, 795
    ylo, yhi = 0.0, 800.0
    out: list[str] = [tx(18, 562, "(B)", 28, weight="500")]
    out.append(ln(150, 557, 178, 557, stroke=COLORS["auc_reported"], width=18))
    out.append(tx(188, 564, "Reported AUC-MAE", 21, fill="#344054"))
    out.append(ln(490, 557, 518, 557, stroke=COLORS["auc_uncertainty"], width=18))
    out.append(tx(528, 564, "Uncertainty–diversity AUC-MAE", 21, fill="#344054"))

    for tick in (0, 200, 400, 600, 800):
        y = sy(tick, ylo, yhi, top, bottom)
        out.append(ln(left, y, right, y, stroke="#C9CED7", width=1.0))
        out.append(tx(left - 12, y + 7, f"{tick:g}", 21, anchor="end", fill="#344054"))
    out.append(f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="none" stroke="#667085" stroke-width="1.4"/>')

    x_positions = [175, 300, 425, 565, 690, 815]
    for x, (domain_label, model, reported, uncertainty) in zip(x_positions, rows):
        bar_w = 29
        gap = 5
        x_reported = x - bar_w - gap / 2
        x_uncertainty = x + gap / 2
        y_reported = sy(reported, ylo, yhi, top, bottom)
        y_uncertainty = sy(uncertainty, ylo, yhi, top, bottom)
        out.append(f'<rect x="{x_reported:.1f}" y="{y_reported:.1f}" width="{bar_w:.1f}" height="{bottom-y_reported:.1f}" fill="{COLORS["auc_reported"]}"/>')
        out.append(f'<rect x="{x_uncertainty:.1f}" y="{y_uncertainty:.1f}" width="{bar_w:.1f}" height="{bottom-y_uncertainty:.1f}" fill="{COLORS["auc_uncertainty"]}"/>')
        model_label = model.replace("tanimoto_knn", "Tanimoto-kNN").replace("elastic_net", "Elastic Net").replace("ridge", "Ridge")
        if domain_label == "Fe(CMC-Por)Cl":
            out.append(tx(x, bottom + 21, "Fe(CMC-", 18, anchor="middle", fill="#344054"))
            out.append(tx(x, bottom + 41, "Por)Cl", 18, anchor="middle", fill="#344054"))
            out.append(tx(x, bottom + 62, model_label, 18, anchor="middle", fill="#344054"))
        else:
            out.append(tx(x, bottom + 25, domain_label, 18, anchor="middle", fill="#344054"))
            out.append(tx(x, bottom + 49, model_label, 18, anchor="middle", fill="#344054"))

    out.append(f'<text x="48" y="{(top+bottom)/2:.1f}" text-anchor="middle" fill="#344054" transform="rotate(-90 48 {(top+bottom)/2:.1f})" style="font-size:23px;font-weight:400">AUC-MAE</text>')
    return "".join(out)


def build_svg() -> Path:
    route_rows = read_csv(DATA / "panel_a_p7_ridge_route_progression.csv")
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="90mm" height="90mm" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Independent ee acquisition robustness analyses, single-column format</title>
  <desc id="desc">Square single-column rendering of the original Fe(P7)Cl Ridge route trajectories and paired AUC-MAE comparison.</desc>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <style>text {{ font-family: Arial, Helvetica, sans-serif; }}</style>
  {panel_a(route_rows)}
  {panel_b(auc_rows())}
</svg>
'''
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "fig5_independent_ee_acquisition_single_column_rsc.svg"
    path.write_text(svg, encoding="utf-8")
    return path


if __name__ == "__main__":
    print(build_svg())

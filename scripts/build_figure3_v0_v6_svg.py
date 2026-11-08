#!/usr/bin/env python3
"""Build the revised Figure 3 as a self-contained SVG/HTML figure."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "figures"
DATA = OUT / "figure3_data"

ROUTES = ["historical_order", "diversity_first", "performance_first", "random", "uncertainty_diversity"]
ROUTE_LABELS = {
    "historical_order": "Reported order",
    "diversity_first": "Diversity-first",
    "performance_first": "Performance-first",
    "random": "Random",
    "uncertainty_diversity": "Uncertainty–diversity",
}
ROUTE_COLORS = {
    "historical_order": "#667085",
    "diversity_first": "#7C5CFF",
    "performance_first": "#D97706",
    "random": "#98A2B3",
    "uncertainty_diversity": "#0F766E",
}
ROUTE_DASH = {
    "historical_order": "stroke-dasharray='7 4'",
    "diversity_first": "",
    "performance_first": "stroke-dasharray='10 4 2 4'",
    "random": "stroke-dasharray='2 4'",
    "uncertainty_diversity": "",
}
VERSIONS = ["V0", "V1", "V2", "V3", "V4", "V5", "V6"]
VERSION_COLORS = ["#98A2B3", "#7C9AC7", "#5C8FC4", "#3C82A6", "#177E89", "#0F766E", "#075985"]
VERSION_AUC = [14.5908, 13.3670, 13.9619, 14.8726, 12.2396, 13.3376, 12.3307]
VERSION_FLUCT = [1.1560, 2.0013, 1.3175, 1.3746, 0.8956, 2.1108, 0.8740]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def trajectory(path: Path) -> dict[str, list[tuple[float, float]] | list[float]]:
    rows = read_csv(path)
    out: dict[str, list[tuple[float, float]] | list[float]] = {
        route: [(float(row["n_labeled"]), float(row[route])) for row in rows]
        for route in ("historical_order", "diversity_first", "performance_first", "uncertainty_diversity")
    }
    out["random"] = [(float(row["n_labeled"]), float(row["random_mean"])) for row in rows]
    out["random_q25"] = [float(row["random_q25"]) for row in rows]
    out["random_q75"] = [float(row["random_q75"]) for row in rows]
    return out


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def txt(x: float, y: float, value: str, size: float = 12, fill: str = "#182230", anchor: str = "start", weight: str = "normal", italic: bool = False) -> str:
    style = f"font-size:{size}px;font-weight:{weight};" + ("font-style:italic;" if italic else "")
    return f"<text x='{x:.1f}' y='{y:.1f}' text-anchor='{anchor}' fill='{fill}' style='{style}'>{esc(value)}</text>"


def ln(x1: float, y1: float, x2: float, y2: float, stroke: str = "#98A2B3", width: float = 1, extra: str = "") -> str:
    return f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{stroke}' stroke-width='{width}' {extra}/>"


def circ(x: float, y: float, r: float, fill: str, stroke: str = "white", width: float = 1.2) -> str:
    return f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='{width}'/>"


def poly(points: list[tuple[float, float]], stroke: str, width: float, extra: str = "") -> str:
    point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f"<polyline points='{point_text}' fill='none' stroke='{stroke}' stroke-width='{width}' stroke-linecap='round' stroke-linejoin='round' {extra}/>"


def polygon(points: list[tuple[float, float]], fill: str, opacity: float) -> str:
    point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f"<polygon points='{point_text}' fill='{fill}' fill-opacity='{opacity}' stroke='none'/>"


def sx(value: float, lo: float, hi: float, left: float, width: float) -> float:
    return left + (value - lo) / (hi - lo) * width


def sy(value: float, lo: float, hi: float, top: float, height: float) -> float:
    return top + height - (value - lo) / (hi - lo) * height


def route_panel(data: dict[str, list[tuple[float, float]] | list[float]], title: str, left: float, top: float, width: float, xmax: int, show_y: bool, letter: str = "") -> str:
    pl, pt, pw, ph = left + 60, top + 35, width - 75, 225
    bottom = pt + ph
    out = [txt(left, top + 16, title, 11, weight="bold")]
    if letter:
        out.append(txt(left - 21, top + 16, letter, 14, weight="bold"))
    x0 = sx(2, 2, xmax, pl, pw)
    out.append(f"<rect x='{x0:.1f}' y='{pt:.1f}' width='{sx(min(10, xmax), 2, xmax, pl, pw)-x0:.1f}' height='{ph:.1f}' fill='#EAF4F2'/>")
    out.append(txt(sx(2.5, 2, xmax, pl, pw), pt + 18, "Low-data regime", 8.0, "#0F766E", weight="bold"))
    for tick in (0, 10, 20, 30, 40):
        yy = sy(tick, 0, 45, pt, ph)
        out += [ln(pl, yy, pl + pw, yy, "#E7EBF0", 0.8), txt(pl - 9, yy + 3, str(tick), 8.0, "#475467", "end")]
    out += [ln(pl, pt, pl, bottom), ln(pl, bottom, pl + pw, bottom)]
    ticks = [2, 10, 20, 30, xmax] if xmax > 30 else [2, 5, 10, 15, 20, xmax]
    for tick in ticks:
        xx = sx(tick, 2, xmax, pl, pw)
        out += [ln(xx, bottom, xx, bottom + 4, "#98A2B3", 0.8), txt(xx, bottom + 16, str(tick), 8.0, "#475467", "middle")]
    rand = data["random"]
    q25, q75 = data["random_q25"], data["random_q75"]
    band = [(sx(x, 2, xmax, pl, pw), sy(y, 0, 45, pt, ph)) for (x, _), y in zip(rand, q75)]
    band += [(sx(x, 2, xmax, pl, pw), sy(y, 0, 45, pt, ph)) for (x, _), y in zip(reversed(rand), reversed(q25))]
    out.append(polygon(band, ROUTE_COLORS["random"], 0.16))
    for route in ROUTES:
        pts = [(sx(x, 2, xmax, pl, pw), sy(y, 0, 45, pt, ph)) for x, y in data[route]]
        out.append(poly(pts, ROUTE_COLORS[route], 2.6 if route == "uncertainty_diversity" else 1.45, ROUTE_DASH[route]))
    if show_y:
        mid = pt + ph / 2
        out.append(f"<text x='{left-47:.1f}' y='{mid:.1f}' text-anchor='middle' fill='#344054' transform='rotate(-90 {left-47:.1f} {mid:.1f})' style='font-size:9.0px'>Retrospective ee MAE (percentage points)</text>")
    out += [txt(pl + pw / 2, bottom + 35, "Revealed substrates", 9.0, "#344054", "middle"), txt(pl + pw, bottom + 51, "Increasing experimental information →", 7.7, "#667085", "end")]
    return "".join(out)


def version_panel(left: float, top: float, width: float, height: float) -> str:
    out = [txt(left, top + 16, "V0–V6 feature-version benchmark", 11, weight="bold"), txt(left - 21, top + 16, "B", 14, weight="bold"), txt(left, top + 33, "Pooled P7 + CMC-Por; ee + isolated yield", 7.7, "#667085")]
    row_top, row_h = top + 70, 25
    auc_left, auc_width = left + 50, 125
    fl_left, fl_width = left + 230, 100
    out += [txt(auc_left + auc_width / 2, top + 51, "AUC-MAE", 8.0, "#344054", "middle"), txt(fl_left + fl_width / 2, top + 51, "Fluctuation", 8.0, "#344054", "middle")]
    for tick in (12, 13, 14, 15):
        xx = sx(tick, 11.4, 15.4, auc_left, auc_width)
        out += [ln(xx, row_top - 8, xx, row_top + row_h * 7 - 4, "#E7EBF0", 0.7), txt(xx, row_top - 13, str(tick), 7.0, "#667085", "middle")]
    for tick in (0.8, 1.2, 1.6, 2.0):
        xx = sx(tick, 0.7, 2.2, fl_left, fl_width)
        out += [ln(xx, row_top - 8, xx, row_top + row_h * 7 - 4, "#E7EBF0", 0.7), txt(xx, row_top - 13, f"{tick:.1f}", 7.0, "#667085", "middle")]
    for idx, (version, color) in enumerate(zip(VERSIONS, VERSION_COLORS)):
        y = row_top + idx * row_h
        out.append(txt(left + 4, y + 4, version, 8.4, "#344054", weight="bold" if version in ("V4", "V6") else "normal"))
        out.append(circ(sx(VERSION_AUC[idx], 11.4, 15.4, auc_left, auc_width), y, 4.2 if version not in ("V4", "V6") else 5.3, color))
        out.append(circ(sx(VERSION_FLUCT[idx], 0.7, 2.2, fl_left, fl_width), y, 4.2 if version not in ("V4", "V6") else 5.3, color))
        out.append(txt(auc_left + auc_width + 8, y + 4, f"{VERSION_AUC[idx]:.2f}", 7.2, color))
        out.append(txt(fl_left + fl_width + 8, y + 4, f"{VERSION_FLUCT[idx]:.2f}", 7.2, color))
    out += [txt(left, top + height - 18, "Lower values indicate lower accumulated error and more stable decay.", 7.5, "#667085"), txt(left + width, top + height - 18, "V4: lowest error · V6: lowest fluctuation", 7.5, "#075985", "end", weight="bold")]
    return "".join(out)


def pareto_panel(left: float, top: float, width: float, height: float) -> str:
    pl, pt, pw, ph = left + 62, top + 38, width - 85, height - 90
    out = [txt(left, top + 16, "Prediction versus stability", 11, weight="bold"), txt(left - 21, top + 16, "C", 14, weight="bold"), txt(left, top + 33, "Lower-left is preferable", 7.8, "#667085")]
    for tick in (12, 13, 14, 15):
        xx = sx(tick, 11.4, 15.4, pl, pw)
        out += [ln(xx, pt, xx, pt + ph, "#E7EBF0", 0.8), txt(xx, pt + ph + 16, str(tick), 8.0, "#475467", "middle")]
    for tick in (0.8, 1.2, 1.6, 2.0):
        yy = sy(tick, 0.7, 2.2, pt, ph)
        out += [ln(pl, yy, pl + pw, yy, "#E7EBF0", 0.8), txt(pl - 9, yy + 3, f"{tick:.1f}", 8.0, "#475467", "end")]
    out += [ln(pl, pt, pl, pt + ph), ln(pl, pt + ph, pl + pw, pt + ph)]
    for idx, (version, color) in enumerate(zip(VERSIONS, VERSION_COLORS)):
        x = sx(VERSION_AUC[idx], 11.4, 15.4, pl, pw)
        y = sy(VERSION_FLUCT[idx], 0.7, 2.2, pt, ph)
        r = 6.2 if version in ("V4", "V6") else 4.8
        out.append(circ(x, y, r, color))
        dx, dy = (6, 3)
        if version == "V4": dx, dy = (-7, -8)
        if version == "V6": dx, dy = (7, 13)
        out.append(txt(x + dx, y + dy, version, 8.6, color, "end" if dx < 0 else "start", weight="bold" if version in ("V4", "V6") else "normal"))
    out.append(f"<path d='M {sx(12.2,11.4,15.4,pl,pw):.1f} {sy(0.82,0.7,2.2,pt,ph):.1f} L {sx(13.2,11.4,15.4,pl,pw):.1f} {sy(0.82,0.7,2.2,pt,ph):.1f}' stroke='#0F766E' stroke-width='1.2' marker-end='url(#arrow)' fill='none'/>")
    out.append(txt(sx(12.65,11.4,15.4,pl,pw), sy(0.79,0.7,2.2,pt,ph), "better prediction and stability", 7.6, "#0F766E", "middle"))
    out += [txt(pl + pw / 2, pt + ph + 35, "Mean normalized AUC-MAE", 9.0, "#344054", "middle"), txt(left - 43, pt + ph / 2, "Mean fluctuation", 9.0, "#344054", "middle")]
    out.append(f"<text x='{left-43:.1f}' y='{pt+ph/2:.1f}' text-anchor='middle' fill='#344054' transform='rotate(-90 {left-43:.1f} {pt+ph/2:.1f})' style='font-size:9.0px'>Mean fluctuation</text>")
    out.append(txt(left, top + height - 18, "V4 minimizes pooled error; V6 gives the lowest pooled fluctuation.", 7.6, "#667085"))
    return "".join(out)


def robustness_data() -> list[tuple[str, str, float, float]]:
    rows = read_csv(DATA / "panel_d_independent_ee_estimator_metrics.csv")
    lookup = {(row["domain"], row["model"], row["route"]): row for row in rows}
    specs = [
        ("Fe(P7)Cl", "Elastic Net", "P7", "elastic_net"),
        ("Fe(P7)Cl", "Ridge", "P7", "ridge"),
        ("Fe(P7)Cl", "Tanimoto-kNN", "P7", "tanimoto_knn"),
        ("Fe(CMC-Por)Cl", "Elastic Net", "CMC-Por aryl", "elastic_net"),
        ("Fe(CMC-Por)Cl", "Ridge", "CMC-Por aryl", "ridge"),
        ("Fe(CMC-Por)Cl", "Tanimoto-kNN", "CMC-Por aryl", "tanimoto_knn"),
    ]
    return [
        (catalyst, model, float(lookup[(domain, estimator, "historical_order")]["auc_mae"]), float(lookup[(domain, estimator, "uncertainty_diversity")]["auc_mae"]))
        for catalyst, model, domain, estimator in specs
    ]


def robustness_panel(left: float, top: float, width: float, height: float, rows: list[tuple[str, str, float, float]]) -> str:
    pl, pt, pw, ph = left + 132, top + 52, width - 155, height - 108
    out = [txt(left, top + 16, "Estimator robustness and learning efficiency", 11, weight="bold"), txt(left - 21, top + 16, "D", 14, weight="bold"), txt(left, top + 33, "Fe(P7)Cl and Fe(CMC-Por)Cl; lower AUC-MAE is better", 7.7, "#667085")]
    ys = [pt + 12, pt + 42, pt + 72, pt + 116, pt + 146, pt + 176]
    for tick in (0, 200, 400, 600, 800):
        xx = sx(tick, 0, 800, pl, pw)
        out += [ln(xx, pt - 8, xx, pt + ph, "#E7EBF0", 0.8), txt(xx, pt + ph + 16, str(tick), 8.0, "#475467", "middle")]
    out.append(ln(pl, pt + ph, pl + pw, pt + ph))
    out.append(ln(left, pt + 98, left + width, pt + 98, "#D0D5DD", 0.8))
    for idx, (y, (domain, model, reported, ud)) in enumerate(zip(ys, rows)):
        label = f"{domain}  {model}"
        out.append(txt(left, y + 3, label, 7.7, "#344054"))
        xu = sx(ud, 0, 800, pl, pw)
        xr = sx(reported, 0, 800, pl, pw)
        out += [ln(xr, y, xu, y, "#CBD5E1", 2), ln(xr, y, xu - 4, y, "#0F766E", 1.4, "marker-end='url(#arrow)'")]
        out += [circ(xr, y, 4.5, "#667085"), txt(xr, y - 8, f"{reported:.0f}", 7.7, "#667085", "middle", weight="bold")]
        out += [circ(xu, y, 4.8, "#0F766E"), txt(xu, y + 14, f"{ud:.0f}", 7.7, "#0F766E", "middle", weight="bold")]
    out.append(txt(left, top + height - 18, "All six comparisons have numeric AUC-MAE values; uncertainty–diversity is lower in every comparison.", 7.4, "#667085"))
    return "".join(out)


def legend() -> str:
    out: list[str] = []
    xs = [95, 245, 390, 545, 680]
    for x, route in zip(xs, ROUTES):
        out += [ln(x, 82, x + 25, 82, ROUTE_COLORS[route], 2.6 if route == "uncertainty_diversity" else 1.7, ROUTE_DASH[route]), txt(x + 32, 86, ROUTE_LABELS[route], 8.0, "#344054")]
    out += [ln(870, 82, 895, 82, ROUTE_COLORS["random"], 7, "opacity='0.18'"), txt(902, 86, "Random IQR", 8.0, "#344054")]
    return "".join(out)


def build() -> str:
    p7 = trajectory(DATA / "panel_a_p7_ridge_route_progression.csv")
    cmc = trajectory(DATA / "panel_b_cmcpor_ridge_route_progression.csv")
    robustness = robustness_data()
    return "".join([
        "<svg xmlns='http://www.w3.org/2000/svg' width='1500' height='980' viewBox='0 0 1500 980'>",
        "<defs><marker id='arrow' markerWidth='7' markerHeight='7' refX='6' refY='3.5' orient='auto'><path d='M0,0 L7,3.5 L0,7 z' fill='#0F766E'/></marker></defs>",
        "<rect width='1500' height='980' fill='white'/>",
        txt(80, 35, "Acquisition order and feature design jointly determine learning efficiency", 16, weight="bold"),
        txt(80, 60, "Retrospective progressive acquisition of locked substrate outcomes", 9.3, "#667085"),
        legend(),
        route_panel(p7, "Fe(P7)Cl: route order", 80, 118, 450, 37, True, "A"),
        route_panel(cmc, "Fe(CMC-Por)Cl: route order", 555, 118, 450, 25, False),
        version_panel(1030, 118, 390, 300),
        pareto_panel(80, 500, 820, 360),
        robustness_panel(930, 500, 490, 360, robustness),
        txt(80, 928, "A: standard V0 route comparison. B–C: corrected V0–V6 feature-mixture benchmark pooled across P7/CMC-Por and ee/yield. D: independent estimator convergence audit.", 8.0, "#667085"),
        txt(80, 950, "All results are retrospective; lower error is better. V0–V6 metrics are feature-version ablations, not additional experimental outcomes or prospective savings claims.", 8.0, "#667085"),
        "</svg>",
    ])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    svg = build()
    svg_path = OUT / "figure3_v0_v6.svg"
    svg_path.write_text(svg, encoding="utf-8")
    html_path = OUT / "figure3_v0_v6.html"
    html_path.write_text("<!doctype html><html><head><meta charset='utf-8'><title>Revised Figure 3 V0–V6</title><style>@page{size:1500px 980px;margin:0}html,body{margin:0;background:white;width:1500px;height:980px}svg{display:block;width:1500px;height:980px}</style></head><body>" + svg + "</body></html>", encoding="utf-8")
    manifest = {
        "figure": "3A-D revised V0-V6",
        "title": "Acquisition order and feature design jointly determine learning efficiency",
        "outputs": [str(svg_path), str(html_path)],
        "source_files": [
            "output/figures/figure3_data/panel_a_p7_ridge_route_progression.csv",
            "output/figures/figure3_data/panel_b_cmcpor_ridge_route_progression.csv",
            "docs/rule-feature-mixture-results.md",
            "output/supporting-information/manuscript-results.md",
            "output/figures/figure3_data/panel_d_independent_ee_estimator_metrics.csv",
        ],
        "caveats": [
            "The V0-V6 benchmark is pooled across P7/CMC-Por and ee/isolated-yield cells.",
            "The route curves remain the exact Figure 3 P7 and CMC-Por aryl cohorts.",
            "The figure does not claim prospective experimental savings.",
        ],
    }
    (OUT / "figure3_v0_v6_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {svg_path}")


if __name__ == "__main__":
    main()

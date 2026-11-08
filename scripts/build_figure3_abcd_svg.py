#!/usr/bin/env python3
"""Build publication-style Figure 3A–D using the locked CSV summaries."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "figures"
PLOT_DATA = ROOT / "docs" / "supporting-information" / "latex" / "plot-data"
SUMMARY = ROOT / "data" / "expansion" / "pptl" / "historical-vs-ai-progressive-comparison.csv"

COLORS = {"historical_order":"#667085", "diversity_first":"#7C5CFF", "uncertainty_diversity":"#0F766E", "performance_first":"#D97706", "random":"#98A2B3"}
LABELS = {"historical_order":"Reported order", "diversity_first":"Diversity-first", "uncertainty_diversity":"Uncertainty–diversity", "performance_first":"Performance-first", "random":"Random"}
ROUTES = ["historical_order", "diversity_first", "performance_first", "random", "uncertainty_diversity"]
LINESTYLES = {"historical_order":"stroke-dasharray='7 4'", "diversity_first":"", "uncertainty_diversity":"", "performance_first":"stroke-dasharray='10 4 2 4'", "random":"stroke-dasharray='2 4'"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def trajectory(filename: str) -> dict[str, list[tuple[float, float]] | list[float]]:
    data = read_csv(PLOT_DATA / filename)
    out: dict[str, list[tuple[float, float]] | list[float]] = {route: [(float(r["n_labeled"]), float(r[route])) for r in data] for route in ("historical_order", "diversity_first", "uncertainty_diversity", "performance_first")}
    out["random"] = [(float(r["n_labeled"]), float(r["random_mean"])) for r in data]
    out["random_q25"] = [float(r["random_q25"]) for r in data]
    out["random_q75"] = [float(r["random_q75"]) for r in data]
    return out


def summary() -> dict[tuple[str, str], dict[str, float]]:
    return {(r["scope"], r["route"]): {"mean": float(r["mean_prefix_mae"]), "auc": float(r["auc_mae"])} for r in read_csv(SUMMARY)}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def txt(x: float, y: float, value: str, size: float = 12, fill: str = "#182230", anchor: str = "start", weight: str = "normal", italic: bool = False) -> str:
    style = f"font-size:{size}px;font-weight:{weight};" + ("font-style:italic;" if italic else "")
    return f"<text x='{x:.1f}' y='{y:.1f}' text-anchor='{anchor}' fill='{fill}' style='{style}'>{esc(value)}</text>"


def ln(x1: float, y1: float, x2: float, y2: float, stroke: str = "#98A2B3", width: float = 1, extra: str = "") -> str:
    return f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{stroke}' stroke-width='{width}' {extra}/>"


def rc(x: float, y: float, w: float, h: float, fill: str, opacity: float = 1) -> str:
    return f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' fill='{fill}' fill-opacity='{opacity}'/>"


def circ(x: float, y: float, r: float, fill: str) -> str:
    return f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r:.1f}' fill='{fill}' stroke='white' stroke-width='1.2'/>"


def poly(points: list[tuple[float, float]], stroke: str, width: float, extra: str = "") -> str:
    return f"<polyline points='{ ' '.join(f'{x:.1f},{y:.1f}' for x,y in points) }' fill='none' stroke='{stroke}' stroke-width='{width}' stroke-linecap='round' stroke-linejoin='round' {extra}/>"


def polygon(points: list[tuple[float, float]], fill: str, opacity: float) -> str:
    return f"<polygon points='{ ' '.join(f'{x:.1f},{y:.1f}' for x,y in points) }' fill='{fill}' fill-opacity='{opacity}' stroke='none'/>"


def sx(v: float, lo: float, hi: float, left: float, width: float) -> float:
    return left + (v - lo) / (hi - lo) * width


def sy(v: float, lo: float, hi: float, top: float, height: float) -> float:
    return top + height - (v - lo) / (hi - lo) * height


def learning_panel(data: dict[str, list[tuple[float, float]] | list[float]], title: str, letter: str, left: float, top: float, width: float, xmax: int, show_y: bool) -> str:
    pl, pt, pw, ph = left + 58, top + 32, width - 72, 270
    bottom = pt + ph
    out = [txt(left, top + 13, title, 11, weight="bold"), txt(left - 18, top + 13, letter, 13, weight="bold")]
    x2 = sx(2, 2, xmax, pl, pw)
    out.append(rc(x2, pt, sx(min(10, xmax), 2, xmax, pl, pw) - x2, ph, "#EAF4F2"))
    out.append(txt(sx(2.6, 2, xmax, pl, pw), pt + 18, "Low-data regime", 8.2, "#0F766E", weight="bold"))
    for tick in (0, 10, 20, 30, 40):
        yy = sy(tick, 0, 45, pt, ph)
        out += [ln(pl, yy, pl + pw, yy, "#E7EBF0", 0.8), txt(pl - 9, yy + 3.2, str(tick), 8.3, "#475467", "end")]
    out += [ln(pl, pt, pl, bottom), ln(pl, bottom, pl + pw, bottom)]
    ticks = [2, 10, 20, 30, xmax] if xmax > 30 else [2, 5, 10, 15, 20, xmax]
    for tick in ticks:
        xx = sx(tick, 2, xmax, pl, pw)
        out += [ln(xx, bottom, xx, bottom + 4, "#98A2B3", 0.8), txt(xx, bottom + 16, str(tick), 8.3, "#475467", "middle")]
    rand = data["random"]
    q25, q75 = data["random_q25"], data["random_q75"]
    band = [(sx(x, 2, xmax, pl, pw), sy(y, 0, 45, pt, ph)) for (x, _), y in zip(rand, q75)]
    band += [(sx(x, 2, xmax, pl, pw), sy(y, 0, 45, pt, ph)) for (x, _), y in zip(reversed(rand), reversed(q25))]
    out.append(polygon(band, COLORS["random"], 0.16))
    for route in ROUTES:
        pts = [(sx(x, 2, xmax, pl, pw), sy(y, 0, 45, pt, ph)) for x, y in data[route]]
        out.append(poly(pts, COLORS[route], 2.8 if route == "uncertainty_diversity" else 1.55, LINESTYLES[route]))
    if show_y:
        mid = pt + ph / 2
        out.append(f"<text x='{left-47:.1f}' y='{mid:.1f}' text-anchor='middle' fill='#344054' transform='rotate(-90 {left-47:.1f} {mid:.1f})' style='font-size:9.4px'>Retrospective ee MAE (percentage points)</text>")
    out += [txt(pl + pw / 2, bottom + 35, "Revealed substrates", 9.3, "#344054", "middle"), txt(pl + pw, bottom + 54, "Increasing experimental information →", 8.0, "#667085", "end")]
    return "".join(out)


def legend() -> str:
    out: list[str] = []
    for x, route in zip([105, 260, 390, 580, 735], ROUTES):
        out += [ln(x, 97, x + 27, 97, COLORS[route], 2.7 if route == "uncertainty_diversity" else 1.7, LINESTYLES[route]), txt(x + 34, 101, LABELS[route], 8.2, "#344054")]
    out += [ln(1065, 97, 1092, 97, COLORS["random"], 7, "opacity='0.18'"), txt(1099, 101, "Random IQR", 8.2, "#344054")]
    return "".join(out)


def efficiency_panel(s: dict[tuple[str, str], dict[str, float]]) -> str:
    left, top, width = 100, 528, 575
    pl, pt, pw, ph = left + 68, top + 38, width - 86, 220
    out = [txt(left, top + 13, "Matched learning-efficiency comparison", 11, weight="bold"), txt(left - 18, top + 13, "C", 13, weight="bold"), txt(left, top + 31, "Reported order", 8.1, COLORS["historical_order"]), txt(left + 88, top + 31, "→", 9, "#98A2B3"), txt(left + 108, top + 31, "Uncertainty–diversity", 8.1, COLORS["uncertainty_diversity"])]
    for tick in (0, 5, 10, 15, 20):
        xx = sx(tick, 0, 24.2, pl, pw)
        out += [ln(xx, pt, xx, pt + ph, "#E7EBF0", 0.8), txt(xx, pt + ph + 15, str(tick), 8.1, "#475467", "middle")]
    out += [ln(pl, pt + ph, pl + pw, pt + ph), txt(pl + pw / 2, pt + ph + 36, "Mean-prefix MAE (ee percentage points)", 9.2, "#344054", "middle")]
    ymap = {"P7": pt + 65, "CMC-Por aryl": pt + 166}
    names = {"P7":"Fe(P7)Cl", "CMC-Por aryl":"Fe(CMC-Por)Cl aryl"}
    for scope, y in ymap.items():
        reported = s[(scope, "historical_order")]["mean"]
        ud = s[(scope, "uncertainty_diversity")]["mean"]
        reduction = (reported - ud) / reported * 100
        xr, xu = sx(reported, 0, 24.2, pl, pw), sx(ud, 0, 24.2, pl, pw)
        out += [txt(left, y + 3, names[scope], 8.7, "#344054"), ln(xu, y, xr, y, "#CBD5E1", 2.2), ln(xr, y, xu + 5, y, COLORS["uncertainty_diversity"], 1.8, "marker-end='url(#arrow)'"), circ(xr, y, 5.3, COLORS["historical_order"]), circ(xu, y, 5.5, COLORS["uncertainty_diversity"]), txt(xr + 8, y - 10, f"{reported:.3f}", 8.4, COLORS["historical_order"], weight="bold"), txt(xu - 8, y + 17, f"{ud:.3f}", 8.4, COLORS["uncertainty_diversity"], "end", weight="bold"), txt(left + width - 2, y + 4, f"↓ {reduction:.1f}%", 10.5, COLORS["uncertainty_diversity"], "end", weight="bold")]
    out.append(txt(left, 850, "Dedicated matched Ridge comparison; mean-prefix error summarizes the full reveal trajectory.", 7.9, "#667085"))
    return "".join(out)


def convergence_panel() -> str:
    left, top, width = 715, 528, 575
    pl, pt, pw = left + 130, top + 56, width - 148
    out = [txt(left, top + 13, "Robustness and limits of early convergence", 11, weight="bold"), txt(left - 18, top + 13, "D", 13, weight="bold"), txt(pl, top + 32, "Independent multi-estimator experiment", 8.1, "#667085")]
    for tick in (0, 10, 20, 30, 40):
        xx = sx(tick, 0, 42, pl, pw)
        out += [ln(xx, pt - 12, xx, pt + 205, "#E7EBF0", 0.8), txt(xx, pt + 220, str(tick), 8.1, "#475467", "middle")]
    out += [ln(pl, pt + 205, pl + pw, pt + 205), txt(pl + pw / 2, pt + 241, "n₉₀: substrates needed to reach the 90% threshold (lower is earlier)", 8.7, "#344054", "middle"), ln(left, pt + 104, left + width, pt + 104, "#D0D5DD", 0.8)]
    data = [("Fe(P7)Cl", "Elastic Net", None, 16), ("", "Ridge", None, 16), ("", "Tanimoto-kNN", 37, 17), ("Fe(CMC-Por)Cl", "Elastic Net", 12, 6), ("", "Ridge", 16, 8), ("", "Tanimoto-kNN", 7, 14)]
    ys = [pt + 12, pt + 48, pt + 84, pt + 136, pt + 172, pt + 208]
    for (domain, model, reported, ud), y in zip(data, ys):
        label = f"{domain}  {model}" if domain else f"                 {model}"
        xu = sx(ud, 0, 42, pl, pw)
        out.append(txt(left, y + 3, label, 7.7, "#344054"))
        if reported is None:
            out.append(txt(sx(30.5, 0, 42, pl, pw), y + 3, "not reached", 7.7, COLORS["historical_order"], "center", italic=True))
        else:
            xr = sx(reported, 0, 42, pl, pw)
            out += [ln(xr, y, xu, y, "#CBD5E1", 2), ln(xr, y, xu - 4, y, COLORS["uncertainty_diversity"], 1.5, "marker-end='url(#arrow)'"), circ(xr, y, 4.2, COLORS["historical_order"]), txt(xr, y - 8, str(reported), 7.7, COLORS["historical_order"], "center", weight="bold")]
        out += [circ(xu, y, 4.5, COLORS["uncertainty_diversity"]), txt(xu, y + 14, str(ud), 7.7, COLORS["uncertainty_diversity"], "center", weight="bold")]
    out += [txt(left, 850, "Estimator-dependent exception: CMC-Por Tanimoto-kNN reaches n₉₀ earlier under reported order (7 vs 14), although U–D has lower integrated AUC-MAE.", 7.4, "#667085")]
    return "".join(out)


def build() -> str:
    return "".join([
        "<svg xmlns='http://www.w3.org/2000/svg' width='1340' height='920' viewBox='0 0 1340 920'>",
        "<defs><marker id='arrow' markerWidth='7' markerHeight='7' refX='6' refY='3.5' orient='auto'><path d='M0,0 L7,3.5 L0,7 z' fill='#0F766E'/></marker></defs>",
        "<rect width='1340' height='920' fill='white'/>",
        txt(100, 35, "Informative substrates accelerate learning of the ee landscape", 16, weight="bold"),
        txt(100, 61, "Retrospective progressive acquisition on locked observed substrate outcomes", 9.3, "#667085"),
        legend(),
        learning_panel(trajectory("p7_route_progression.csv"), "Fe(P7)Cl: acquisition order changes learning", "A", 100, 138, 575, 37, True),
        learning_panel(trajectory("cmcpor_route_progression.csv"), "Fe(CMC-Por)Cl: order effect generalizes", "B", 715, 138, 575, 25, False),
        efficiency_panel(summary()), convergence_panel(),
        txt(100, 885, "All comparisons are retrospective; lower MAE is better. Panel C uses the dedicated matched Ridge comparison; Panel D is the independent multi-estimator convergence audit.", 8.1, "#667085"),
        "</svg>",
    ])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    svg = build()
    (OUT / "figure3_progression_transfer.svg").write_text(svg, encoding="utf-8")
    html_doc = "<!doctype html><html><head><meta charset='utf-8'><title>Figure 3A–D</title><style>@page{size:1340px 920px;margin:0}html,body{margin:0;background:white;width:1340px;height:920px}svg{display:block;width:1340px;height:920px}</style></head><body>" + svg + "</body></html>"
    (OUT / "figure3_progression_transfer.html").write_text(html_doc, encoding="utf-8")
    manifest = {"figure":"3A-D", "title":"Informative substrates accelerate learning of the ee landscape", "source_files":["docs/supporting-information/latex/plot-data/p7_route_progression.csv", "docs/supporting-information/latex/plot-data/cmcpor_route_progression.csv", "data/expansion/pptl/historical-vs-ai-progressive-comparison.csv", "manuscript/supporting_information (1).tex"], "outputs":["output/figures/figure3_progression_transfer.svg", "output/figures/figure3_progression_transfer.html", "output/figures/figure3_progression_transfer.pdf", "output/figures/figure3_progression_transfer.png"], "notes":["Panels A–B use supplied Ridge route trajectories; random shows its mean with the supplied IQR band.", "Panel C uses dedicated matched Ridge mean-prefix values: 21.672→9.684 and 13.155→8.787.", "Panel D shows independent n90 summaries for Elastic Net, Ridge, and Tanimoto-kNN, preserving the CMC-Por Tanimoto-kNN exception.", "The figure does not make a prospective experimental-savings claim."]}
    (OUT / "figure3_progression_transfer_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote Figure 3A–D to {OUT}")


if __name__ == "__main__":
    main()

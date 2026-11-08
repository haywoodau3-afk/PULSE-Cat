from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
DATA = HERE / "corrected_project" / "analysis_runs"
OUT = HERE / "figures"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1800, 1100
INK = "#24313b"
MUTED = "#64727d"
GRID = "#dfe5e9"
BLUE = "#2c77a6"
ORANGE = "#d57934"
GREEN = "#4b8c68"
PALE_BLUE = "#dbeaf3"
PALE_ORANGE = "#f6e6d8"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Neue Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica Neue.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def q(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * pct
    low = int(math.floor(pos))
    high = int(math.ceil(pos))
    return ordered[low] + (ordered[high] - ordered[low]) * (pos - low)


def base(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((W // 2, 42), title, fill=INK, font=font(36, True), anchor="ma")
    return im, d


def panel_axes(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], ylo: float, yhi: float, ylabel: str, yticks: list[float]) -> tuple:
    x0, y0, x1, y1 = box
    for tick in yticks:
        y = y1 - (tick - ylo) / (yhi - ylo) * (y1 - y0)
        d.line((x0, y, x1, y), fill=GRID, width=2)
        d.text((x0 - 16, y), f"{tick:g}", fill=MUTED, font=font(22), anchor="rm")
    d.line((x0, y0, x0, y1), fill=INK, width=2)
    d.line((x0, y1, x1, y1), fill=INK, width=2)
    d.text(((x0 + x1) / 2, y0 - 28), ylabel, fill=INK, font=font(22, True), anchor="mm")

    def px(index: float) -> float:
        return x0 + index

    def py(value: float) -> float:
        return y1 - (value - ylo) / (yhi - ylo) * (y1 - y0)

    return px, py


def make_fig_s7() -> None:
    im, d = base("Shared-start sensitivity across 50 initial substrate pairs")
    for panel, domain, box in [
        ("Fe(P7)Cl", "p7", (190, 240, 830, 865)),
        ("Fe(CMC-Por)Cl", "cmcpor", (1000, 240, 1640, 865)),
    ]:
        rows = csv_rows(DATA / "corrected_shared_starts" / domain / "pair_results.csv")
        source = [float(r["reported_minus_ud"]) for r in rows]
        random = [float(r["random_minus_ud"]) for r in rows]
        x0, y0, x1, y1 = box
        px, py = panel_axes(d, box, -10, 20, "Comparator MAE − uncertainty–diversity MAE (ee points)", [-10, -5, 0, 5, 10, 15, 20])
        d.text(((x0 + x1) / 2, 135), panel, fill=INK, font=font(27, True), anchor="mm")
        yzero = py(0)
        d.line((x0, yzero, x1, yzero), fill="#8e9aa3", width=3)
        centers = [x0 + (x1 - x0) * .34, x0 + (x1 - x0) * .70]
        for values, cx, color, label in [(source, centers[0], BLUE, "Source order"), (random, centers[1], ORANGE, "Random")]:
            for i, v in enumerate(values):
                jitter = ((i * 37) % 31 - 15) * 1.7
                d.ellipse((cx + jitter - 5, py(v) - 5, cx + jitter + 5, py(v) + 5), fill=color, outline="white", width=1)
            lo, med, hi = q(values, .25), q(values, .5), q(values, .75)
            d.line((cx, py(min(values)), cx, py(max(values))), fill=color, width=3)
            d.rectangle((cx - 45, py(hi), cx + 45, py(lo)), fill="white", outline=color, width=4)
            d.line((cx - 45, py(med), cx + 45, py(med)), fill=color, width=5)
            d.text((cx, y1 + 30), label, fill=INK, font=font(22), anchor="ma")
        d.text(((x0 + x1) / 2, 974), "Initial-pair comparison", fill=MUTED, font=font(22), anchor="ma")
    im.save(OUT / "figureS6_corrected_shared_start.png", dpi=(300, 300))


def make_fig_s8() -> None:
    im, d = base("Remaining-pool ee MAE across shared starting pairs")
    for panel, domain, box in [
        ("Fe(P7)Cl", "p7", (190, 240, 830, 865)),
        ("Fe(CMC-Por)Cl aryl", "cmcpor", (1000, 240, 1640, 865)),
    ]:
        raw = csv_rows(DATA / "corrected_shared_starts" / domain / "learning_curves.csv")
        grouped: dict[tuple[str, int], list[float]] = defaultdict(list)
        for r in raw:
            route = r["route"]
            if route not in ("historical_order", "uncertainty_diversity"):
                continue
            grouped[(route, int(r["n_labeled"]))].append(float(r["mae"]))
        original = csv_rows(HERE / "corrected_project" / "analysis_runs" / "corrected_dedicated_replay" / "corrected_original_curves.csv")
        dedicated: dict[str, list[tuple[int, float]]] = defaultdict(list)
        for r in original:
            if r["domain"] == domain:
                dedicated[r["route"]].append((int(r["n_labeled"]), float(r["mae"])))
        ns = sorted({n for _, n in grouped})
        x0, y0, x1, y1 = box
        allv = [v for arr in grouped.values() for v in arr] + [v for arr in dedicated.values() for _, v in arr]
        yhi = max(25, math.ceil(max(allv) / 10) * 10)
        ticks = list(range(0, yhi + 1, 10))
        px, py = panel_axes(d, box, 0, yhi, "Remaining-pool MAE (ee points)", ticks)
        d.text(((x0 + x1) / 2, 135), panel, fill=INK, font=font(27, True), anchor="mm")
        xmin, xmax = min(ns), max(ns)

        def x_at(n: float) -> float:
            return x0 + (n - xmin) / max(1, xmax - xmin) * (x1 - x0)

        for route, color, band in [("historical_order", BLUE, PALE_BLUE), ("uncertainty_diversity", ORANGE, PALE_ORANGE)]:
            medpoints = []
            upper = []
            lower = []
            for n in ns:
                vals = grouped[(route, n)]
                medpoints.append((x_at(n), py(q(vals, .5))))
                upper.append((x_at(n), py(q(vals, .75))))
                lower.append((x_at(n), py(q(vals, .25))))
            d.polygon(upper + list(reversed(lower)), fill=band)
            d.line(medpoints, fill=color, width=5)
            for x, y in medpoints:
                d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)
        for route, color in [("historical_order", BLUE), ("uncertainty_diversity", ORANGE)]:
            pts = [(x_at(n), py(v)) for n, v in sorted(dedicated.get(route, []))]
            if pts:
                d.line(pts, fill=color, width=4)
                for x, y in pts:
                    d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)
        for n in ns:
            if n == xmin or n == xmax or n % 5 == 0:
                d.text((x_at(n), y1 + 20), str(n), fill=MUTED, font=font(18), anchor="ma")
        legend_y = 1000
        d.line((x0 + 10, legend_y, x0 + 70, legend_y), fill=BLUE, width=5)
        d.text((x0 + 82, legend_y), "Reported order", fill=INK, font=font(20), anchor="lm")
        d.line((x0 + 260, legend_y, x0 + 320, legend_y), fill=ORANGE, width=5)
        d.text((x0 + 332, legend_y), "Uncertainty–diversity", fill=INK, font=font(20), anchor="lm")
    im.save(OUT / "figureS7_corrected_shared_curves.png", dpi=(300, 300))


def make_fig_s9() -> None:
    im, d = base("Repeated common-test-set sensitivity")
    for panel, domain, box in [
        ("Fe(P7)Cl", "p7", (190, 240, 830, 865)),
        ("Fe(CMC-Por)Cl aryl", "cmcpor", (1000, 240, 1640, 865)),
    ]:
        rows = csv_rows(DATA / "corrected_common_test" / domain / "split_results.csv")
        source = [float(r["source_minus_ud"]) for r in rows]
        random = [float(r["random_minus_ud"]) for r in rows]
        x0, y0, x1, y1 = box
        all_values = source + random
        ylo = min(-4, math.floor(min(all_values) / 4) * 4)
        yhi = max(8, math.ceil(max(all_values) / 4) * 4)
        ticks = list(range(ylo, yhi + 1, 4))
        px, py = panel_axes(d, box, ylo, yhi, "Comparator MAE − uncertainty–diversity MAE (ee points)", ticks)
        d.text(((x0 + x1) / 2, 135), panel, fill=INK, font=font(27, True), anchor="mm")
        yzero = py(0)
        d.line((x0, yzero, x1, yzero), fill="#8e9aa3", width=3)
        for idx, (vals, color, marker) in enumerate([(source, BLUE, -7), (random, ORANGE, 7)]):
            for i, v in enumerate(vals):
                x = x0 + (i + .5) / len(vals) * (x1 - x0) + marker
                d.ellipse((x - 6, py(v) - 6, x + 6, py(v) + 6), fill=color, outline="white", width=1)
            mean = sum(vals) / len(vals)
            d.line((x0, py(mean), x1, py(mean)), fill=color, width=3)
        for i in [0, 4, 9, 14, 19]:
            x = x0 + (i + .5) / 20 * (x1 - x0)
            d.text((x, y1 + 20), str(i + 1), fill=MUTED, font=font(18), anchor="ma")
        ly = 975
        d.ellipse((x0 + 75, ly - 7, x0 + 89, ly + 7), fill=BLUE)
        d.text((x0 + 100, ly), "Source order", fill=INK, font=font(20), anchor="lm")
        d.ellipse((x0 + 275, ly - 7, x0 + 289, ly + 7), fill=ORANGE)
        d.text((x0 + 300, ly), "Random", fill=INK, font=font(20), anchor="lm")
    im.save(OUT / "figureS8_corrected_common_test.png", dpi=(300, 300))


def make_fig_s10() -> None:
    im, d = base("Retrospective common-test Ridge MAE over the weight simplex")
    summaries = {}
    for panel, domain in [("Fe(P7)Cl", "p7"), ("Fe(CMC-Por)Cl aryl", "cmcpor")]:
        rows = csv_rows(DATA / "corrected_weight_sensitivity" / domain / "weight_summary.csv")
        summaries[domain] = rows
    vals_all = [float(r["mean_split_mae"]) for rows in summaries.values() for r in rows]
    lo, hi = min(vals_all), max(vals_all)
    palette = ["#2c77a6", "#62a5bb", "#a3c4b5", "#f0c56b", "#e68745", "#b84b42"]

    def color_for(v: float) -> str:
        u = min(1, max(0, (v - lo) / (hi - lo if hi > lo else 1)))
        i = min(len(palette) - 1, int(u * (len(palette) - 1)))
        return palette[i]

    for title, domain, box in [
        ("Fe(P7)Cl", "p7", (180, 205, 820, 865)),
        ("Fe(CMC-Por)Cl aryl", "cmcpor", (980, 205, 1620, 865)),
    ]:
        x0, y0, x1, y1 = box
        d.text(((x0 + x1) / 2, 140), title, fill=INK, font=font(27, True), anchor="mm")
        tri = [(x0 + 40, y1 - 25), (x1 - 40, y1 - 25), ((x0 + x1) / 2, y0 + 25)]
        d.line((*tri[0], *tri[1]), fill=INK, width=3)
        d.line((*tri[1], *tri[2]), fill=INK, width=3)
        d.line((*tri[2], *tri[0]), fill=INK, width=3)
        d.text((tri[0][0] - 5, tri[0][1] + 34), "Diversity", fill=INK, font=font(21, True), anchor="la")
        d.text((tri[1][0] + 5, tri[1][1] + 34), "Uncertainty", fill=INK, font=font(21, True), anchor="ra")
        d.text((tri[2][0], tri[2][1] - 22), "Family coverage", fill=INK, font=font(21, True), anchor="ms")
        for row in summaries[domain]:
            wd, wu, wc = float(row["w_diversity"]), float(row["w_uncertainty"]), float(row["w_family_coverage"])
            x = tri[0][0] * wd + tri[1][0] * wu + tri[2][0] * wc
            y = tri[0][1] * wd + tri[1][1] * wu + tri[2][1] * wc
            rad = 15 if row["is_default"].lower() == "true" else 10
            col = color_for(float(row["mean_split_mae"]))
            d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=col, outline=INK if rad == 15 else "white", width=4 if rad == 15 else 2)
            if rad == 15:
                # Draw a crisp five-point star; it stays legible in print fonts.
                points = []
                for k in range(10):
                    angle = -math.pi / 2 + k * math.pi / 5
                    radius = 10 if k % 2 == 0 else 4
                    points.append((x + math.cos(angle) * radius, y + math.sin(angle) * radius))
                d.polygon(points, fill="black")
    # Compact color key.
    x0, x1, y = 510, 1290, 1010
    for i, color in enumerate(palette):
        xx0 = x0 + i * (x1 - x0) / len(palette)
        xx1 = x0 + (i + 1) * (x1 - x0) / len(palette)
        d.rectangle((xx0, y, xx1, y + 24), fill=color, outline="white")
    d.text((x0, y + 38), f"Lower MAE {lo:.1f}", fill=MUTED, font=font(18), anchor="la")
    d.text((x1, y + 38), f"Higher MAE {hi:.1f}", fill=MUTED, font=font(18), anchor="ra")
    im.save(OUT / "figureS9_corrected_weight_sensitivity.png", dpi=(300, 300))


def main() -> None:
    make_fig_s7()
    make_fig_s8()
    make_fig_s9()
    make_fig_s10()


if __name__ == "__main__":
    main()

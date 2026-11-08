#!/usr/bin/env python3
"""Build editable vector artwork for Figure 2A and Figure 2C.

The artwork is intentionally self-contained SVG so it can be edited or placed
in the manuscript without a rasterisation step. Numerical values are read from
the frozen representation-progression table; the panel-C geometry is a clear
schematic of the documented catalyst-referenced occupancy workflow.
"""

from __future__ import annotations

import csv
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "figures"
DATA = ROOT / "output" / "supporting-information" / "tables" / "si_representation_progression_ee.csv"

W = 1600
INK = "#17212b"
MUTED = "#52606d"
GRID = "#d9dee4"
P7 = "#007c91"
CMC = "#c45b2c"
PURPLE = "#7b62a8"
BAD = "#b33b2e"
GOOD = "#0a7a78"
PALE_TEAL = "#e3f1f2"
PALE_RUST = "#f7e9e4"
PALE_GOLD = "#fff4d5"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def txt(x: float, y: float, value: object, *, size: int = 16,
        weight: str = "400", fill: str = INK, anchor: str = "start",
        family: str = "Arial, Helvetica, sans-serif", italic: bool = False) -> str:
    style = " font-style:italic;" if italic else ""
    return (f'<text x="{x:g}" y="{y:g}" font-family="{family}" '
            f'font-size="{size}px" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" style="{style}">{esc(value)}</text>')


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = INK,
         width: float = 1.0, dash: str | None = None, opacity: float = 1.0) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
            f'stroke="{stroke}" stroke-width="{width:g}" opacity="{opacity:g}"{dash_attr}/>')


def rect(x: float, y: float, width: float, height: float, *, fill: str = "none",
         stroke: str = "none", sw: float = 0.0, rx: float = 0.0,
         opacity: float = 1.0) -> str:
    return (f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}" '
            f'rx="{rx:g}" opacity="{opacity:g}"/>')


def circle(cx: float, cy: float, r: float, *, fill: str, stroke: str = "none",
           sw: float = 0.0, opacity: float = 1.0) -> str:
    return (f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw:g}" opacity="{opacity:g}"/>')


def ellipse(cx: float, cy: float, rx: float, ry: float, *, fill: str,
            stroke: str = "none", sw: float = 0.0, opacity: float = 1.0,
            rotate: float | None = None) -> str:
    transform = f' transform="rotate({rotate:g} {cx:g} {cy:g})"' if rotate is not None else ""
    return (f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{rx:g}" ry="{ry:g}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}" '
            f'opacity="{opacity:g}"{transform}/>')


def path(d: str, *, stroke: str = INK, sw: float = 1.5, fill: str = "none",
         opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}" '
            f'opacity="{opacity:g}" stroke-linecap="round" stroke-linejoin="round"{dash_attr}/>')


def multiline(x: float, y: float, lines: list[str], *, size: int = 14,
              leading: int = 19, fill: str = MUTED, weight: str = "400") -> str:
    return "".join(txt(x, y + i * leading, value, size=size, fill=fill, weight=weight)
                   for i, value in enumerate(lines))


def svg_open(width: int, height: int, title: str, desc: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{esc(title)}</title>',
        f'<desc id="desc">{esc(desc)}</desc>',
        rect(0, 0, width, height, fill="white"),
    ]


def read_values() -> dict[str, dict[str, float]]:
    values: dict[str, dict[str, float]] = {"p7": {}, "cmc": {}}
    with DATA.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            target = "p7" if row["target_domain"] == "fe-p7-cl" else "cmc"
            values[target][row["feature_arm"]] = float(row["target_only_mae_ee_points"])
    return values


def draw_feature_icon(x: float, y: float, kind: str, color: str) -> str:
    out = [rect(x, y, 72, 58, fill="white", stroke=GRID, sw=1.2, rx=8)]
    if kind == "descriptor":
        for i, width in enumerate((42, 28, 50, 36)):
            yy = y + 14 + i * 9
            out.append(line(x + 11, yy, x + 11 + width, yy, stroke=color, width=3))
            out.append(circle(x + 16 + width, yy, 2.5, fill=color))
    elif kind == "fingerprint":
        for i in range(8):
            xx = x + 12 + i * 6.5
            height = 19 if i in (1, 4, 6) else 10
            out.append(rect(xx, y + 29 - height / 2, 3.5, height, fill=color, rx=1))
        out.append(line(x + 11, y + 42, x + 61, y + 42, stroke=GRID, width=1))
    else:
        # A small catalyst cavity with three translucent substrate traces.
        out.append(circle(x + 36, y + 29, 8, fill="#f0f2f4", stroke=color, sw=1.4))
        out.append(path(f"M {x+18} {y+20} Q {x+36} {y+5} {x+54} {y+20}", stroke=color, sw=2, opacity=.4))
        out.append(path(f"M {x+18} {y+38} Q {x+36} {y+53} {x+54} {y+38}", stroke=color, sw=2, opacity=.4))
        out.append(path(f"M {x+17} {y+31} Q {x+36} {y+19} {x+55} {y+31}", stroke=color, sw=2.5, opacity=.7))
    return "".join(out)


def panel_a() -> str:
    values = read_values()
    arms = ["B1", "B2", "B3", "B4", "B5", "P0", "P1", "P2", "P3", "P4"]
    out = svg_open(
        W, 840,
        "Figure 2A - Relevant geometry, not feature count",
        "Progressive feature ladder from molecular connectivity to compact catalyst-referenced pose descriptors. Target-only enantioselectivity MAE is shown for Fe(P7)Cl and Fe(CMC-Por)Cl.",
    )

    out.append(txt(46, 50, "A", size=30, weight="700", fill=INK))
    out.append(txt(92, 50, "Relevant geometry, not feature count", size=27, weight="700"))
    out.append(txt(92, 80, "Progressive representation ladder | target-only MAE, lower is better", size=15, fill=MUTED))

    # Plot occupies the left ~2/3; the right side is the explanatory feature ladder.
    left, top, bottom, right = 92, 134, 700, 1020
    plot_w, plot_h = right - left, bottom - top
    max_y = 22.0
    def y(value: float) -> float:
        return bottom - value / max_y * plot_h

    for tick in range(0, 25, 5):
        yy = y(tick)
        out.append(line(left, yy, right, yy, stroke=GRID, width=1))
        out.append(txt(left - 15, yy + 5, tick, size=13, fill=MUTED, anchor="end"))
    out.append(rect(left, top, plot_w, plot_h, fill="none", stroke="#334155", sw=1))
    out.append(f'<text x="32" y="{top + plot_h / 2:g}" font-family="Arial, Helvetica, sans-serif" font-size="14px" fill="{MUTED}" text-anchor="middle" transform="rotate(-90 32 {top + plot_h / 2:g})">MAE (ee percentage points)</text>')

    step = plot_w / len(arms)
    centers = [left + (i + .5) * step for i in range(len(arms))]
    divider = (centers[4] + centers[5]) / 2
    out.append(line(divider, top, divider, bottom, stroke=GRID, width=1.5, dash="7 6"))
    out.append(txt((centers[0] + centers[4]) / 2, top - 22, "Molecular connectivity", size=14, weight="700", fill=MUTED, anchor="middle"))
    out.append(txt((centers[5] + centers[9]) / 2, top - 22, "Catalyst-referenced pose", size=14, weight="700", fill=MUTED, anchor="middle"))

    p7_pts = [(centers[i], y(values["p7"][arm])) for i, arm in enumerate(arms)]
    cmc_pts = [(centers[i], y(values["cmc"][arm])) for i, arm in enumerate(arms)]
    out.append(path(" ".join([f"M {p7_pts[0][0]:g} {p7_pts[0][1]:g}"] + [f"L {x:g} {yy:g}" for x, yy in p7_pts[1:]]), stroke=P7, sw=3.3))
    out.append(path(" ".join([f"M {cmc_pts[0][0]:g} {cmc_pts[0][1]:g}"] + [f"L {x:g} {yy:g}" for x, yy in cmc_pts[1:]]), stroke=CMC, sw=3.3))

    for i, arm in enumerate(arms):
        for pts, key, color in ((p7_pts, "p7", P7), (cmc_pts, "cmc", CMC)):
            x, yy = pts[i]
            out.append(circle(x, yy, 6, fill=color, stroke="white", sw=2))
            label = f"{values[key][arm]:.3f}" if arm in {"B1", "B5", "P2", "P3", "P4"} else f"{values[key][arm]:.1f}"
            dy = -14 if yy < top + 40 else 24
            dx = -10 if key == "p7" else 10
            out.append(txt(x + dx, yy + dy, label, size=11, weight="700", fill=color, anchor="middle"))
        out.append(txt(centers[i], bottom + 29, arm, size=14, weight="700", anchor="middle"))

    # Legend and key outcome callouts.
    out.append(line(130, 755, 158, 755, stroke=P7, width=4))
    out.append(circle(144, 755, 5, fill=P7, stroke="white", sw=1.5))
    out.append(txt(168, 760, "Fe(P7)Cl target", size=13))
    out.append(line(335, 755, 363, 755, stroke=CMC, width=4))
    out.append(circle(349, 755, 5, fill=CMC, stroke="white", sw=1.5))
    out.append(txt(378, 760, "Fe(CMC-Por)Cl target", size=13))
    out.append(txt(650, 760, "P2: full 248-descriptor pose block", size=13, fill=BAD, weight="700", anchor="middle"))
    out.append(txt(650, 782, "higher-dimensional does not mean more predictive", size=12, fill=MUTED, anchor="middle"))

    # Right-hand feature ladder.
    x0, y0, box_w = 1090, 122, 460
    out.append(rect(x0, y0, box_w, 594, fill="#fafbfc", stroke=GRID, sw=1.2, rx=12))
    out.append(txt(x0 + 24, y0 + 34, "What is being added?", size=18, weight="700"))
    out.append(txt(x0 + 24, y0 + 57, "A compact chemical story behind B1-B5 and P0-P4", size=12, fill=MUTED))

    rows = [
        ("B1", "6 RDKit descriptors", "molecular size / polarity / topology", "descriptor", "#6f7d88", "baseline"),
        ("B2-B5", "15 RDKit + Morgan fingerprint", "128 -> 256 -> 1,024 bits; non-monotonic", "fingerprint", "#536f82", "connectivity"),
        ("P3", "44 compact pose descriptors", "selected substrate geometry around the catalyst", "pose", GOOD, "useful geometry"),
        ("P4", "+16 catalyst-interaction descriptors", "small catalyst-context block; P7 improves, CMC changes little", "pose", PURPLE, "context"),
        ("P2", "+248 raw pose descriptors", "all pose features; error rises to 16.953 / 17.659", "pose", BAD, "too much"),
    ]
    row_y = y0 + 78
    for code, title, detail, icon, color, tag in rows:
        out.append(draw_feature_icon(x0 + 20, row_y, icon, color))
        out.append(txt(x0 + 108, row_y + 21, code + "  " + title, size=15, weight="700", fill=color))
        out.append(txt(x0 + 108, row_y + 43, detail, size=12, fill=MUTED))
        out.append(txt(x0 + box_w - 18, row_y + 21, tag, size=11, weight="700", fill=color, anchor="end"))
        row_y += 94
    out.append(line(x0 + 20, y0 + 562, x0 + box_w - 20, y0 + 562, stroke=GRID, width=1))
    out.append(txt(x0 + 24, y0 + 585, "Headline: relevant geometry, not feature count", size=15, weight="700", fill=INK))

    out.append(txt(92, 823, "The compact PULSE-Pose block adds catalyst-referenced signal beyond the molecular baseline; indiscriminate feature expansion can increase error.", size=12, fill=MUTED))
    out.append("</svg>\n")
    return "".join(out)


def catalyst_cavity(x: float, y: float, w: float, h: float, color: str, label: str,
                    narrow: bool = False) -> str:
    """Draw a schematic porphyrin-like cavity and an ensemble of substrate traces."""
    out: list[str] = []
    cx, cy = x + w / 2, y + h / 2 + 6
    rx, ry = w * (0.30 if narrow else 0.36), h * 0.27
    # Backdrop and cavity wall.
    out.append(rect(x, y, w, h, fill="white", stroke=GRID, sw=1, rx=10))
    out.append(ellipse(cx, cy, rx, ry, fill="#f7fafb", stroke=color, sw=2.2, opacity=.92))
    out.append(ellipse(cx, cy, rx * .62, ry * .62, fill="white", stroke=GRID, sw=1.2))
    # Four nitrogens and the iron center.
    for dx, dy in ((-rx * .60, 0), (rx * .60, 0), (0, -ry * .60), (0, ry * .60)):
        out.append(circle(cx + dx, cy + dy, 7, fill="#f4f6f8", stroke=color, sw=1.5))
        out.append(txt(cx + dx, cy + dy + 4, "N", size=9, weight="700", fill=color, anchor="middle"))
    out.append(circle(cx, cy, 11, fill="#3b4650", stroke="white", sw=2))
    out.append(txt(cx, cy + 4, "Fe", size=10, weight="700", fill="white", anchor="middle"))
    # Six translucent substrate poses around the reactive region.
    pose_color = BAD
    offsets = [(-22, -20, -6), (-17, -12, 8), (-10, 2, -12), (5, 12, 5), (18, 8, 15), (24, -7, -4)]
    for i, (dx, dy, bend) in enumerate(offsets):
        sy = cy - ry * .78 + i * 5
        x1, y1 = cx + dx * .45, cy + dy * .24
        x2, y2 = cx + dx * .86 + bend, cy + dy * .68
        x3, y3 = cx + dx * 1.05 + bend * 1.4, cy + dy * 1.05
        out.append(path(f"M {x1:g} {y1:g} Q {x2:g} {y2:g} {x3:g} {y3:g}", stroke=pose_color, sw=2.1, opacity=.33))
        out.append(circle(x3, y3, 2.8, fill=pose_color, opacity=.45))
    # Reactive site cue.
    out.append(path(f"M {cx+rx*.05:g} {cy-ry*.98:g} l 8 8 l -8 8 l -8 -8 z", fill=BAD, stroke=BAD, sw=1, opacity=.82))
    out.append(txt(cx, y + h - 17, label, size=13, weight="700", fill=color, anchor="middle"))
    return "".join(out)


def density_map(x: float, y: float, w: float, h: float, color: str, title: str,
                rotate: float = 0.0, companion: str | None = None) -> str:
    out: list[str] = [rect(x, y, w, h, fill="white", stroke=GRID, sw=1, rx=10)]
    # Coordinate frame and soft spatial bins.
    for i in range(1, 5):
        xx = x + i * w / 5
        yy = y + i * h / 5
        out.append(line(xx, y + 20, xx, y + h - 28, stroke=GRID, width=.7, opacity=.75))
        out.append(line(x + 20, yy, x + w - 20, yy, stroke=GRID, width=.7, opacity=.75))
    out.append(txt(x + 17, y + 22, title, size=13, weight="700", fill=color))
    # Catalyst ring outline in the bottom layer.
    cx, cy = x + w * .49, y + h * .56
    out.append(ellipse(cx, cy, w * .25, h * .23, fill="none", stroke=color, sw=1.4, opacity=.55))
    out.append(ellipse(cx, cy, w * .14, h * .13, fill="none", stroke=GRID, sw=1))
    out.append(circle(cx, cy, 5, fill="#3b4650", opacity=.85))
    # Deterministic occupancy lobes: center + reactive-region bias.
    lobes = [
        (-.20, -.12, .24, .18, 0.24), (-.09, -.20, .23, .20, .28),
        (.05, -.15, .20, .16, .30), (.16, -.05, .18, .14, .26),
        (.12, .10, .23, .17, .17), (-.06, .15, .24, .19, .16),
        (-.18, .08, .18, .14, .12), (.01, -.02, .28, .22, .16),
    ]
    for dx, dy, rx, ry, opacity in lobes:
        out.append(ellipse(cx + dx * w, cy + dy * h, rx * w, ry * h,
                           fill=color, opacity=opacity, rotate=rotate))
    # A few contour strokes keep this as an occupancy field, not a molecular drawing.
    out.append(ellipse(cx + .03 * w, cy - .12 * h, .23 * w, .13 * h,
                       fill="none", stroke=color, sw=1.4, opacity=.5, rotate=rotate))
    out.append(ellipse(cx + .10 * w, cy + .02 * h, .16 * w, .10 * h,
                       fill="none", stroke=color, sw=1.2, opacity=.45, rotate=rotate))
    out.append(txt(x + w - 18, y + h - 16, "sampled occupancy", size=11, fill=MUTED, anchor="end"))
    if companion:
        out.append(txt(x + 18, y + h - 16, companion, size=11, fill=MUTED))
    return "".join(out)


def draw_shared_overlay(x: float, y: float, w: float, h: float) -> str:
    out: list[str] = [rect(x, y, w, h, fill="white", stroke=GRID, sw=1, rx=10)]
    out.append(txt(x + 17, y + 22, "shared substrate identity", size=13, weight="700", fill=INK))
    cx, cy = x + w * .50, y + h * .55
    # Same underlying substrate identity shown as two differently located catalyst-relative fields.
    for color, dx, dy, rot in ((P7, -.09, -.02, -12), (CMC, .09, .04, 18)):
        out.append(ellipse(cx + dx * w, cy + dy * h, .25 * w, .17 * h, fill=color, opacity=.18, rotate=rot))
        out.append(ellipse(cx + dx * w, cy + dy * h, .17 * w, .10 * h, fill="none", stroke=color, sw=2, opacity=.75, rotate=rot))
        out.append(ellipse(cx + dx * w, cy + dy * h, .08 * w, .05 * h, fill=color, opacity=.34, rotate=rot))
    out.append(circle(cx, cy, 5, fill="#3b4650", opacity=.9))
    # Identical substrate identity: central black motif, distinct contextual centroids.
    out.append(path(f"M {cx-37:g} {cy-58:g} l 18 -10 l 20 10 l 18 -10 l 18 10 l -18 10 l -20 -10 l -18 10 z", stroke=INK, sw=2.2, fill="white"))
    out.append(line(cx, y + 52, cx, y + h - 38, stroke=GRID, width=1, dash="4 5"))
    out.append(txt(x + 17, y + h - 17, "different catalyst-relative space", size=11, fill=MUTED))
    out.append(txt(x + w - 17, y + h - 17, "13 paired identities", size=11, fill=MUTED, anchor="end"))
    return "".join(out)


def panel_c() -> str:
    out = svg_open(
        W, 830,
        "Figure 2C - Same substrate, different catalyst-relative space",
        "Schematic of catalyst-referenced pose ensembles, spatial occupancy maps, and shared-substrate overlays. The maps summarize sampled occupancy and are not transition structures or Boltzmann populations.",
    )
    out.append(txt(46, 50, "C", size=30, weight="700"))
    out.append(txt(92, 50, "Same substrate, different catalyst-relative space", size=27, weight="700"))
    out.append(txt(92, 80, "What PULSE-Pose adds beyond an isolated molecular fingerprint", size=15, fill=MUTED))

    cols = [(92, 460), (570, 460), (1048, 460)]
    # Headings and connector arrows.
    headings = [
        ("1", "Pose ensemble", "sample the substrate in the catalyst environment"),
        ("2", "Occupancy map", "summarize where poses occupy space"),
        ("3", "Shared-substrate overlay", "compare the same identity across catalysts"),
    ]
    for i, (x, _) in enumerate(cols):
        number, title, detail = headings[i]
        out.append(circle(x + 15, 130, 14, fill=(P7 if i == 0 else GOOD if i == 1 else PURPLE)))
        out.append(txt(x + 15, 135, number, size=13, weight="700", fill="white", anchor="middle"))
        out.append(txt(x + 40, 136, title, size=18, weight="700"))
        out.append(txt(x + 40, 160, detail, size=12, fill=MUTED))
    out.append(path("M 530 274 C 545 274 551 274 566 274", stroke=GRID, sw=2))
    out.append(path("M 1008 274 C 1023 274 1029 274 1044 274", stroke=GRID, sw=2))
    out.append(path("M 558 268 l 8 6 l -8 6", stroke=GRID, sw=2))
    out.append(path("M 1036 268 l 8 6 l -8 6", stroke=GRID, sw=2))

    # First column: two catalyst cavities with pose traces.
    out.append(catalyst_cavity(92, 190, 208, 250, P7, "Fe(P7)Cl", narrow=True))
    out.append(catalyst_cavity(344, 190, 208, 250, CMC, "Fe(CMC-Por)Cl", narrow=False))
    out.append(txt(322, 228, "same substrate", size=12, fill=BAD, weight="700", anchor="middle"))
    out.append(path("M 308 312 C 318 300 326 300 338 312", stroke=BAD, sw=1.8, dash="4 4"))
    out.append(txt(92, 474, "Representative sampled poses around a frozen catalyst framework", size=13, fill=MUTED))
    out.append(txt(92, 499, "200 retained poses per substrate: 100 low-UFF + 100 high-UFF", size=12, fill=MUTED))
    out.append(txt(92, 521, "The red traces indicate an ensemble, not one optimized structure.", size=12, fill=BAD, weight="700"))

    # Second column: two separate occupancy maps.
    out.append(density_map(570, 190, 208, 250, P7, "Fe(P7)Cl", rotate=-12, companion="reaction-centered field"))
    out.append(density_map(822, 190, 208, 250, CMC, "Fe(CMC-Por)Cl", rotate=18, companion="reaction-centered field"))
    out.append(txt(570, 474, "Many conformations -> a compact spatial fingerprint", size=13, fill=MUTED))
    out.append(txt(570, 499, "density encodes sampled catalyst-relative occupancy", size=12, fill=MUTED))
    out.append(txt(570, 521, "not electron density and not a population model", size=12, fill=BAD, weight="700"))

    # Third column: overlay and legend.
    out.append(draw_shared_overlay(1048, 190, 460, 250))
    out.append(line(1080, 487, 1110, 487, stroke=P7, width=4))
    out.append(txt(1122, 492, "Fe(P7)Cl occupancy", size=12))
    out.append(line(1290, 487, 1320, 487, stroke=CMC, width=4))
    out.append(txt(1332, 492, "Fe(CMC-Por)Cl occupancy", size=12))
    out.append(txt(1048, 521, "same molecular fingerprint", size=12, fill=MUTED))
    out.append(txt(1508, 521, "different catalyst context", size=12, fill=PURPLE, weight="700", anchor="end"))

    # Bottom interpretation strip.
    out.append(rect(92, 578, 1416, 150, fill="#f8fafb", stroke=GRID, sw=1.2, rx=12))
    out.append(txt(118, 614, "PULSE-Pose turns a molecule from an isolated structural object into a catalyst-contextual spatial representation.", size=17, weight="700", fill=INK))
    out.append(txt(118, 646, "91 catalyst-domain records", size=13, weight="700", fill=P7))
    out.append(txt(118, 668, "41 Fe(P7)Cl + 50 Fe(CMC-Por)Cl", size=12, fill=MUTED))
    out.append(txt(420, 646, "13 shared canonical identities", size=13, weight="700", fill=PURPLE))
    out.append(txt(420, 668, "overlays compare identical substrate structures", size=12, fill=MUTED))
    out.append(txt(820, 646, "Interpretation guardrail", size=13, weight="700", fill=BAD))
    out.append(txt(820, 668, "sampled occupancy only - not transition states or Boltzmann populations", size=12, fill=MUTED))
    out.append(txt(820, 688, "or assigned selectivity-determining interactions", size=12, fill=MUTED))

    out.append(txt(92, 790, "The extra predictive value comes from selectively retained catalyst-referenced geometry, not from dimensionality alone.", size=12, fill=MUTED))
    out.append("</svg>\n")
    return "".join(out)


def composite(a: str, c: str) -> str:
    # Keep the two panels as separate source files as well; the composite uses
    # the same vector primitives but avoids external image references.
    a_inner = a[a.find(">", a.find("<svg")) + 1:a.rfind("</svg>")]
    c_inner = c[c.find(">", c.find("<svg")) + 1:c.rfind("</svg>")]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1710" viewBox="0 0 1600 1710" role="img" aria-labelledby="title desc">'
            '<title id="title">Figure 2A and 2C artwork</title>'
            '<desc id="desc">Progressive molecular representation ladder and catalyst-referenced pose-density schematic.</desc>'
            f'<g transform="translate(0 0)">{a_inner}</g>'
            f'<g transform="translate(0 850)">{c_inner}</g>'
            '</svg>\n')


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    a = panel_a()
    c = panel_c()
    paths = {
        OUT / "figure2a_representation_ladder.svg": a,
        OUT / "figure2c_pose_context_schematic.svg": c,
        OUT / "figure2_ac_schematic.svg": composite(a, c),
    }
    for path_out, content in paths.items():
        path_out.write_text(content, encoding="utf-8")
        print(path_out)


if __name__ == "__main__":
    main()

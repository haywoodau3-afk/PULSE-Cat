#!/usr/bin/env python3
"""Generate standalone SVG plots for molecular representation and PULSE-Pose results."""

from __future__ import annotations

import html
import json
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "plots"


COLORS = {
    "p7": "#007c91",
    "cmcpor": "#c45b2c",
    "structure": "#7a8793",
    "pose": "#007c91",
    "geometry": "#8a6bbd",
    "occupancy": "#b33b2e",
    "grid": "#d9dee4",
    "axis": "#334155",
    "text": "#1f2937",
    "muted": "#52606d",
    "accent": "#b33b2e",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(x: float, y: float, value: object, *, size: int = 14, weight: str = "400",
         fill: str = COLORS["text"], anchor: str = "start", rotate: float | None = None,
         family: str = "Arial, Helvetica, sans-serif") -> str:
    transform = f' transform="rotate({rotate:g} {x:g} {y:g})"' if rotate is not None else ""
    return (
        f'<text x="{x:g}" y="{y:g}" font-family="{family}" font-size="{size}px" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{transform}>'
        f'{esc(value)}</text>'
    )


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str,
         width: float = 1.0, dash: str | None = None) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{stroke}" stroke-width="{width:g}"{extra}/>'


def rect(x: float, y: float, width: float, height: float, *, fill: str = "none",
         stroke: str = "none", stroke_width: float = 0.0, rx: float = 0.0,
         opacity: float = 1.0) -> str:
    return (
        f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width:g}" '
        f'rx="{rx:g}" opacity="{opacity:g}"/>'
    )


def circle(cx: float, cy: float, radius: float, *, fill: str, stroke: str = "white",
           stroke_width: float = 2.0) -> str:
    return f'<circle cx="{cx:g}" cy="{cy:g}" r="{radius:g}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width:g}"/>'


def polyline(points: list[tuple[float, float]], *, stroke: str, width: float = 3.0) -> str:
    joined = " ".join(f"{x:g},{y:g}" for x, y in points)
    return f'<polyline points="{joined}" fill="none" stroke="{stroke}" stroke-width="{width:g}" stroke-linecap="round" stroke-linejoin="round"/>'


def svg_start(width: int, height: int, title: str, description: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="Arial, Helvetica, sans-serif" role="img" aria-labelledby="title desc">',
        f'<title id="title">{esc(title)}</title>',
        f'<desc id="desc">{esc(description)}</desc>',
        rect(0, 0, width, height, fill="white"),
    ]


def svg_end() -> str:
    return "</svg>\n"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def target_only_mae(matrix: dict, arm: str, direction: str) -> float:
    rows = matrix["arms"][arm]["directions"][direction]["rows"]
    return mean(abs(row["predictions"]["target_only"] - row["observed"]) for row in rows)


def extract_panel_a() -> tuple[list[str], dict[str, list[float]]]:
    """Return the fixed reciprocal replay feature ladder for both catalysts."""
    base = ROOT / "data" / "expansion" / "pptl"
    two_d = load_json(base / "bidirectional-ee-2d-matrix.json")
    pose_early = load_json(base / "bidirectional-ee-pose-matrix.json")
    pose_late = load_json(base / "matrix-ee-b5-p3-p4.json")

    arms = ["B1", "B2", "B3", "B4", "B5", "P0", "P1", "P2", "P3", "P4"]
    matrices = {
        **{arm: two_d for arm in two_d["arms"]},
        **{arm: pose_early for arm in pose_early["arms"]},
        "P3": pose_late,
        "P4": pose_late,
    }
    directions = {
        "p7": "cmcpor_to_p7_aryl",
        "cmcpor": "p7_to_cmcpor_aryl",
    }
    values = {
        key: [target_only_mae(matrices[arm], arm, direction) for arm in arms]
        for key, direction in directions.items()
    }
    return arms, values


def extract_panel_b() -> tuple[list[str], list[float], list[float], list[float]]:
    report_dir = ROOT / "data" / "jacs_2025" / "stage2" / "reports"
    target = load_json(report_dir / "full-scope-model-comparison.json")
    family = load_json(report_dir / "family-heldout-ee-model-comparison.json")

    def elastic_net(report: dict) -> tuple[float, float]:
        row = next(item for item in report["model_comparisons"] if item["model_name"] == "elastic_net")
        return row["structure_only_mae"], row["structure_pose_mae"]

    target_values = elastic_net(target)
    family_values = elastic_net(family)
    structure = [target_values[0], family_values[0]]
    pose = [target_values[1], family_values[1]]
    # Use the reported manuscript percentages for the annotation. The source
    # reports 31.9% and 10.3% (rather than recomputing and rounding them from
    # the higher-precision stored MAEs).
    reductions = [31.9, 10.3]
    return ["Target-held-out", "Family-held-out"], structure, pose, reductions


def render_panel_a() -> str:
    arms, values = extract_panel_a()
    width, height = 1240, 700
    left, right, top, bottom = 104, 60, 104, 116
    plot_w, plot_h = width - left - right, height - top - bottom
    max_y = 23.0
    group_step = plot_w / len(arms)
    centers = [left + group_step * (i + 0.5) for i in range(len(arms))]

    def y(v: float) -> float:
        return top + plot_h - v / max_y * plot_h

    out = svg_start(
        width,
        height,
        "Feature ladder for molecular representation and PULSE-Pose",
        "Target-only MAE across successive B1 to B5 molecular representations and P0 to P4 pose-augmented representations for Fe(P7)Cl and Fe(CMC-Por)Cl in the fixed reciprocal replay.",
    )

    # Legend.
    legend_x, legend_y = 790, 36
    for i, (key, label) in enumerate([
        ("p7", "Fe(P7)Cl system (n = 37)"),
        ("cmcpor", "Fe(CMC-Por)Cl system (n = 31)"),
    ]):
        yy = legend_y + i * 29
        out.append(line(legend_x, yy - 5, legend_x + 28, yy - 5, stroke=COLORS[key], width=4))
        out.append(circle(legend_x + 14, yy - 5, 5, fill=COLORS[key]))
        out.append(text(legend_x + 40, yy, label, size=13))

    # Grid and axes.
    for tick in range(0, 25, 5):
        yy = y(tick)
        out.append(line(left, yy, width - right, yy, stroke=COLORS["grid"], width=1))
        out.append(text(left - 14, yy + 5, tick, size=13, fill=COLORS["muted"], anchor="end"))
    out.append(rect(left, top, plot_w, plot_h, stroke=COLORS["axis"], stroke_width=1))
    out.append(text(30, top + plot_h / 2, "MAE (ee percentage points)", size=14, fill=COLORS["muted"], anchor="middle", rotate=-90))

    # Divider between molecular-representation and PULSE-Pose arms.
    divider = (centers[4] + centers[5]) / 2
    out.append(line(divider, top, divider, top + plot_h, stroke=COLORS["grid"], width=1.5, dash="6 6"))

    # Lines, markers, and directly labeled values.
    baseline = top + plot_h
    for key, color, dx, label_offset in [
        ("p7", COLORS["p7"], -9, 24),
        ("cmcpor", COLORS["cmcpor"], 9, -12),
    ]:
        points = [(center, y(value)) for center, value in zip(centers, values[key])]
        out.append(polyline(points, stroke=color, width=3.2))
        for arm, center, value in zip(arms, centers, values[key]):
            yy = y(value)
            out.append(circle(center, yy, 6, fill=color))
            out.append(text(center + dx, yy + label_offset, f"{value:.1f}", size=11, weight="700", fill=color, anchor="middle"))
            if key == "p7":
                out.append(text(center, baseline + 31, arm, size=14, weight="700", anchor="middle"))

    out.append(text(left + plot_w / 2, height - 28, "Representation arm", size=14, fill=COLORS["muted"], anchor="middle"))

    out.append(svg_end())
    return "".join(out)


def render_panel_b() -> str:
    labels, structure, pose, reductions = extract_panel_b()
    width, height = 1120, 700
    left, right, top, bottom = 112, 62, 100, 126
    plot_w, plot_h = width - left - right, height - top - bottom
    max_y = 18.0
    group_step = plot_w / len(labels)
    centers = [left + group_step * (i + 0.5) for i in range(len(labels))]
    bar_w, gap = 118, 16

    def y(v: float) -> float:
        return top + plot_h - v / max_y * plot_h

    out = svg_start(
        width,
        height,
        "Fe(P7)Cl structure-only and structure-plus-pose MAE comparison",
        "Independent matched 38-substrate Fe(P7)Cl enantioselectivity MAE comparison for structure-only and structure-plus-pose Elastic Net under target-held-out and family-held-out validation, with source-catalyst transfer excluded.",
    )
    # Legend.
    legend_x, legend_y = 620, 48
    for i, (color, label) in enumerate([
        (COLORS["structure"], "Structure-only (547 features)"),
        (COLORS["pose"], "Structure + PULSE-Pose (1,241 features)"),
    ]):
        xx = legend_x + i * 230
        out.append(rect(xx, legend_y - 15, 18, 18, fill=color, rx=2))
        out.append(text(xx + 28, legend_y, label, size=13))

    # Grid and axes.
    for tick in range(0, 20, 2):
        yy = y(tick)
        out.append(line(left, yy, width - right, yy, stroke=COLORS["grid"], width=1))
        out.append(text(left - 14, yy + 5, tick, size=13, fill=COLORS["muted"], anchor="end"))
    out.append(rect(left, top, plot_w, plot_h, stroke=COLORS["axis"], stroke_width=1))
    out.append(text(32, top + plot_h / 2, "MAE (ee percentage points)", size=14, fill=COLORS["muted"], anchor="middle", rotate=-90))
    out.append(text(left + plot_w / 2, height - 28, "Validation protocol", size=14, fill=COLORS["muted"], anchor="middle"))

    for i, center in enumerate(centers):
        sx = center - bar_w - gap / 2
        px = center + gap / 2
        sy, py = y(structure[i]), y(pose[i])
        out.append(rect(sx, sy, bar_w, top + plot_h - sy, fill=COLORS["structure"], rx=2))
        out.append(rect(px, py, bar_w, top + plot_h - py, fill=COLORS["pose"], rx=2))
        out.append(text(sx + bar_w / 2, sy - 12, f"{structure[i]:.3f}", size=15, weight="700", anchor="middle"))
        out.append(text(px + bar_w / 2, py - 12, f"{pose[i]:.3f}", size=15, weight="700", fill=COLORS["pose"], anchor="middle"))
        out.append(text(center, top + plot_h + 34, labels[i], size=15, weight="700", anchor="middle"))

        # Reduction bracket above each pair.
        bracket_y = min(sy, py) - 52
        bracket_left = sx + bar_w / 2
        bracket_right = px + bar_w / 2
        out.append(line(bracket_left, bracket_y + 13, bracket_left, bracket_y, stroke=COLORS["accent"], width=1.5))
        out.append(line(bracket_left, bracket_y, bracket_right, bracket_y, stroke=COLORS["accent"], width=1.5))
        out.append(line(bracket_right, bracket_y, bracket_right, bracket_y + 13, stroke=COLORS["accent"], width=1.5))
        out.append(text(center, bracket_y - 10, f"−{reductions[i]:.1f}%", size=17, weight="700", fill=COLORS["accent"], anchor="middle"))

    out.append(svg_end())
    return "".join(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "molecular-representation-a-independent.svg").write_text(render_panel_a(), encoding="utf-8")
    (OUT / "pulse-pose-b-independent.svg").write_text(render_panel_b(), encoding="utf-8")
    print(f"Wrote {OUT / 'molecular-representation-a-independent.svg'}")
    print(f"Wrote {OUT / 'pulse-pose-b-independent.svg'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build Figure 3A–D from the locked retrospective progression summaries.

Panels A and B use the supplied Ridge route trajectories. Panel C uses the
dedicated matched Ridge mean-prefix comparison. Panel D uses the independent
multi-estimator n90 summaries, including the documented Tanimoto-kNN exception.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "figures"
PLOT_DATA = ROOT / "docs" / "supporting-information" / "latex" / "plot-data"
SUMMARY = ROOT / "data" / "expansion" / "pptl" / "historical-vs-ai-progressive-comparison.csv"
SI_TEX = ROOT / "manuscript" / "supporting_information (1).tex"

COLORS = {
    "historical_order": "#667085",
    "diversity_first": "#7C5CFF",
    "uncertainty_diversity": "#0F766E",
    "performance_first": "#D97706",
    "random": "#98A2B3",
}
LABELS = {
    "historical_order": "Reported order",
    "diversity_first": "Diversity-first",
    "uncertainty_diversity": "Uncertainty–diversity",
    "performance_first": "Performance-first",
    "random": "Random",
}
ROUTES = [
    "historical_order",
    "diversity_first",
    "performance_first",
    "random",
    "uncertainty_diversity",
]
LINESTYLES = {
    "historical_order": (0, (4, 2)),
    "diversity_first": "-",
    "uncertainty_diversity": "-",
    "performance_first": (0, (6, 2, 1, 2)),
    "random": (0, (1, 2)),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_trajectory(filename: str) -> dict[str, dict[str, np.ndarray]]:
    rows = read_csv(PLOT_DATA / filename)
    x = np.asarray([int(row["n_labeled"]) for row in rows])
    series: dict[str, dict[str, np.ndarray]] = {}
    for route in ("historical_order", "diversity_first", "uncertainty_diversity", "performance_first"):
        series[route] = {"x": x, "y": np.asarray([float(row[route]) for row in rows])}
    series["random"] = {
        "x": x,
        "y": np.asarray([float(row["random_mean"]) for row in rows]),
        "q25": np.asarray([float(row["random_q25"]) for row in rows]),
        "q75": np.asarray([float(row["random_q75"]) for row in rows]),
    }
    return series


def read_dedicated_summary() -> dict[tuple[str, str], dict[str, float | str]]:
    rows = read_csv(SUMMARY)
    out: dict[tuple[str, str], dict[str, float | str]] = {}
    for row in rows:
        out[(row["scope"], row["route"])] = {
            "mean_prefix_mae": float(row["mean_prefix_mae"]),
            "auc_mae": float(row["auc_mae"]),
            "n90": row["n90"],
        }
    return out


def style_axes(ax: plt.Axes) -> None:
    ax.set_facecolor("white")
    ax.grid(axis="y", color="#E7EBF0", linewidth=0.8, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#98A2B3")
    ax.spines["bottom"].set_color("#98A2B3")
    ax.tick_params(colors="#475467", labelsize=8.5, length=3)
    ax.set_axisbelow(True)


def plot_learning_curve(
    ax: plt.Axes,
    series: dict[str, dict[str, np.ndarray]],
    title: str,
    x_max: int,
    show_y_label: bool,
    panel_letter: str,
) -> None:
    style_axes(ax)
    ax.add_patch(
        Rectangle(
            (2, 0),
            min(8, x_max - 2),
            45,
            facecolor="#EAF4F2",
            edgecolor="none",
            zorder=0,
        )
    )
    ax.text(2.5, 42.2, "Low-data regime", color="#0F766E", fontsize=8.2, weight="bold")
    for route in ROUTES:
        d = series[route]
        if route == "random":
            ax.fill_between(d["x"], d["q25"], d["q75"], color=COLORS[route], alpha=0.16, linewidth=0, zorder=1)
        ax.plot(
            d["x"],
            d["y"],
            color=COLORS[route],
            linestyle=LINESTYLES[route],
            linewidth=2.8 if route == "uncertainty_diversity" else 1.55,
            alpha=0.95 if route != "random" else 0.88,
            zorder=4 if route == "uncertainty_diversity" else 3,
            solid_capstyle="round",
        )
    ax.set_xlim(2, x_max)
    ax.set_ylim(0, 45)
    ax.set_xticks([2, 10, 20, 30, x_max] if x_max > 30 else [2, 5, 10, 15, 20, x_max])
    ax.set_yticks([0, 10, 20, 30, 40])
    ax.set_title(title, loc="left", fontsize=11, weight="bold", color="#182230", pad=8)
    ax.text(-0.095, 1.04, panel_letter, transform=ax.transAxes, fontsize=13, weight="bold", color="#182230")
    ax.set_xlabel("Revealed substrates", fontsize=9.5, color="#344054", labelpad=5)
    if show_y_label:
        ax.set_ylabel("Retrospective ee MAE (percentage points)", fontsize=9.5, color="#344054", labelpad=7)
    ax.text(
        0.98,
        -0.16,
        "Increasing experimental information →",
        transform=ax.transAxes,
        ha="right",
        fontsize=8.1,
        color="#667085",
    )


def add_shared_legend(fig: plt.Figure) -> None:
    handles = [
        Line2D([0], [0], color=COLORS[route], lw=2.8 if route == "uncertainty_diversity" else 1.8, linestyle=LINESTYLES[route], label=LABELS[route])
        for route in ROUTES
    ]
    handles.insert(3, Line2D([0], [0], color=COLORS["random"], lw=6, alpha=0.18, label="Random IQR"))
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=6,
        frameon=False,
        fontsize=8.4,
        handlelength=2.4,
        columnspacing=1.25,
        handletextpad=0.45,
    )


def plot_efficiency(ax: plt.Axes, summary: dict[tuple[str, str], dict[str, float | str]]) -> None:
    style_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.grid(axis="x", color="#E7EBF0", linewidth=0.8)
    ax.set_xlim(0, 24.2)
    ax.set_ylim(-0.65, 2.25)
    ax.set_yticks([1.35, 0.15])
    ax.set_yticklabels(["Fe(P7)Cl", "Fe(CMC-Por)Cl aryl"], fontsize=9.1, color="#344054")
    ax.set_xticks([0, 5, 10, 15, 20])
    ax.set_xlabel("Mean-prefix MAE (ee percentage points)", fontsize=9.5, color="#344054", labelpad=6)
    ax.set_title("Matched learning-efficiency comparison", loc="left", fontsize=11, weight="bold", color="#182230", pad=8)
    ax.text(-0.095, 1.04, "C", transform=ax.transAxes, fontsize=13, weight="bold", color="#182230")
    ax.text(0.00, 1.015, "Reported order", transform=ax.transAxes, fontsize=8.1, color=COLORS["historical_order"], ha="left")
    ax.text(0.26, 1.015, "→", transform=ax.transAxes, fontsize=9, color="#98A2B3", ha="center")
    ax.text(0.29, 1.015, "Uncertainty–diversity", transform=ax.transAxes, fontsize=8.1, color=COLORS["uncertainty_diversity"], ha="left")
    y_positions = {"P7": 1.35, "CMC-Por aryl": 0.15}
    for scope, y in y_positions.items():
        reported = float(summary[(scope, "historical_order")]["mean_prefix_mae"])
        ud = float(summary[(scope, "uncertainty_diversity")]["mean_prefix_mae"])
        reduction = (reported - ud) / reported * 100
        ax.plot([ud, reported], [y, y], color="#CBD5E1", lw=2.2, zorder=2)
        ax.add_patch(FancyArrowPatch((reported, y), (ud, y), arrowstyle="-|>", mutation_scale=11, color=COLORS["uncertainty_diversity"], lw=1.8, zorder=3))
        ax.scatter([reported], [y], s=70, color=COLORS["historical_order"], edgecolor="white", linewidth=1.2, zorder=5)
        ax.scatter([ud], [y], s=76, color=COLORS["uncertainty_diversity"], edgecolor="white", linewidth=1.2, zorder=5)
        ax.text(reported + 0.35, y + 0.17, f"{reported:.3f}", ha="left", va="bottom", fontsize=8.5, weight="bold", color=COLORS["historical_order"])
        ax.text(ud - 0.35, y - 0.17, f"{ud:.3f}", ha="right", va="top", fontsize=8.5, weight="bold", color=COLORS["uncertainty_diversity"])
        ax.text(23.85, y, f"↓ {reduction:.1f}%", ha="right", va="center", fontsize=11.2, weight="bold", color=COLORS["uncertainty_diversity"])
    ax.text(23.85, -0.42, "lower accumulated error", ha="right", fontsize=8.1, color="#667085")
    ax.text(0.0, -0.20, "Matched Ridge comparison; mean-prefix error summarizes the full reveal trajectory.", transform=ax.transAxes, fontsize=8.1, color="#667085")


def plot_convergence(ax: plt.Axes) -> None:
    style_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 42)
    rows = [
        ("Fe(P7)Cl", "Elastic Net", None, 16),
        ("", "Ridge", None, 16),
        ("", "Tanimoto-kNN", 37, 17),
        ("Fe(CMC-Por)Cl", "Elastic Net", 12, 6),
        ("", "Ridge", 16, 8),
        ("", "Tanimoto-kNN", 7, 14),
    ]
    ys = np.array([5.0, 4.0, 3.0, 1.55, 0.55, -0.45])
    ax.set_ylim(-1.08, 5.65)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{domain}  {model}" if domain else f"                 {model}" for domain, model, _, _ in rows], fontsize=7.8, color="#344054")
    ax.set_xticks([0, 10, 20, 30, 40])
    ax.set_xlabel("n₉₀: substrates needed to reach the 90% threshold (lower is earlier)", fontsize=9.2, color="#344054", labelpad=6)
    ax.set_title("Robustness and limits of early convergence", loc="left", fontsize=11, weight="bold", color="#182230", pad=8)
    ax.text(-0.095, 1.04, "D", transform=ax.transAxes, fontsize=13, weight="bold", color="#182230")
    ax.axhline(2.25, color="#D0D5DD", lw=0.8)
    ax.text(0.0, 5.48, "Independent multi-estimator experiment", fontsize=8.1, color="#667085")
    ax.axvspan(0, 10, color="#F8FAFC", zorder=0)
    for y, (domain, model, reported, ud) in zip(ys, rows):
        if reported is not None:
            ax.plot([reported, ud], [y, y], color="#CBD5E1", lw=2.0, zorder=2)
            ax.add_patch(FancyArrowPatch((reported, y), (ud, y), arrowstyle="-|>", mutation_scale=9, color=COLORS["uncertainty_diversity"], lw=1.5, zorder=3))
            ax.scatter(reported, y, s=49, color=COLORS["historical_order"], edgecolor="white", linewidth=1, zorder=5)
            ax.text(reported, y + 0.18, str(reported), ha="center", va="bottom", fontsize=7.9, color=COLORS["historical_order"], weight="bold")
        else:
            ax.text(30.5, y + 0.03, "not reached", ha="center", va="center", fontsize=7.8, color=COLORS["historical_order"], style="italic")
        ax.scatter(ud, y, s=55, color=COLORS["uncertainty_diversity"], edgecolor="white", linewidth=1, zorder=5)
        ax.text(ud, y - 0.18, str(ud), ha="center", va="top", fontsize=7.9, color=COLORS["uncertainty_diversity"], weight="bold")
    ax.text(0.0, 1.025, "Reported", transform=ax.transAxes, fontsize=8.1, color=COLORS["historical_order"], ha="left")
    ax.text(0.18, 1.025, "●", transform=ax.transAxes, fontsize=9, color=COLORS["uncertainty_diversity"], ha="center")
    ax.text(0.20, 1.025, "Uncertainty–diversity", transform=ax.transAxes, fontsize=8.1, color=COLORS["uncertainty_diversity"], ha="left")
    ax.text(0.0, -0.19, "Estimator-dependent exception: CMC-Por Tanimoto-kNN reaches n₉₀ earlier under reported order (7 vs 14), although U–D has lower integrated AUC-MAE.", transform=ax.transAxes, fontsize=7.65, color="#667085")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    p7 = read_trajectory("p7_route_progression.csv")
    cmc = read_trajectory("cmcpor_route_progression.csv")
    summary = read_dedicated_summary()

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.titleweight": "bold",
    })
    fig = plt.figure(figsize=(13.4, 9.15), constrained_layout=False)
    gs = fig.add_gridspec(2, 2, left=0.105, right=0.985, top=0.895, bottom=0.105, wspace=0.28, hspace=0.48, height_ratios=[1.05, 0.95])
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])
    plot_learning_curve(ax_a, p7, "Fe(P7)Cl: acquisition order changes learning", 37, True, "A")
    plot_learning_curve(ax_b, cmc, "Fe(CMC-Por)Cl: order effect generalizes", 25, False, "B")
    ax_b.set_yticklabels([])
    plot_efficiency(ax_c, summary)
    plot_convergence(ax_d)
    add_shared_legend(fig)
    fig.suptitle("Informative substrates accelerate learning of the ee landscape", x=0.105, y=0.946, ha="left", fontsize=15.5, weight="bold", color="#182230")
    fig.text(0.105, 0.918, "Retrospective progressive acquisition on locked observed substrate outcomes", fontsize=9.4, color="#667085", ha="left")
    fig.text(0.105, 0.055, "All comparisons are retrospective; lower MAE is better. Panel C uses the dedicated matched Ridge comparison; Panel D is the independent multi-estimator convergence audit.", fontsize=8.2, color="#667085", ha="left")

    for ext, dpi in (("svg", None), ("pdf", None), ("png", 320)):
        path = OUT / f"figure3_progression_transfer.{ext}"
        kwargs = {"bbox_inches": "tight", "pad_inches": 0.08}
        if dpi:
            kwargs["dpi"] = dpi
        fig.savefig(path, **kwargs)
    plt.close(fig)

    manifest = {
        "figure": "3A-D",
        "title": "Informative substrates accelerate learning of the ee landscape",
        "panels": {
            "A": "Fe(P7)Cl Ridge retrospective learning trajectories",
            "B": "Fe(CMC-Por)Cl aryl Ridge retrospective learning trajectories",
            "C": "Dedicated matched Ridge mean-prefix MAE comparison",
            "D": "Independent Elastic Net/Ridge/Tanimoto-kNN n90 convergence audit",
        },
        "source_files": [
            "docs/supporting-information/latex/plot-data/p7_route_progression.csv",
            "docs/supporting-information/latex/plot-data/cmcpor_route_progression.csv",
            "data/expansion/pptl/historical-vs-ai-progressive-comparison.csv",
            "manuscript/supporting_information (1).tex",
        ],
        "outputs": [
            "output/figures/figure3_progression_transfer.svg",
            "output/figures/figure3_progression_transfer.pdf",
            "output/figures/figure3_progression_transfer.png",
        ],
        "notes": [
            "Random lines show the supplied mean with the random-route IQR band.",
            "Panel C values are dedicated matched mean-prefix Ridge summaries, not the independent AUC audit.",
            "Panel D preserves the documented CMC-Por Tanimoto-kNN exception.",
            "No prospective experimental savings claim is made.",
        ],
    }
    (OUT / "figure3_progression_transfer_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote Figure 3A–D to {OUT}")


if __name__ == "__main__":
    main()

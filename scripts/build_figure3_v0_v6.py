#!/usr/bin/env python3
"""Build a revised Figure 3 separating route order from V0--V6 features."""
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
DATA = OUT / "figure3_data"

ROUTES = [
    "historical_order",
    "diversity_first",
    "performance_first",
    "random",
    "uncertainty_diversity",
]
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
ROUTE_STYLES = {
    "historical_order": (0, (4, 2)),
    "diversity_first": "-",
    "performance_first": (0, (6, 2, 1, 2)),
    "random": (0, (1, 2)),
    "uncertainty_diversity": "-",
}

VERSION_COLORS = ["#98A2B3", "#7C9AC7", "#5C8FC4", "#3C82A6", "#177E89", "#0F766E", "#075985"]
VERSIONS = ["V0", "V1", "V2", "V3", "V4", "V5", "V6"]
VERSION_AUC = [14.5908, 13.3670, 13.9619, 14.8726, 12.2396, 13.3376, 12.3307]
VERSION_FLUCT = [1.1560, 2.0013, 1.3175, 1.3746, 0.8956, 2.1108, 0.8740]
VERSION_JUMP = [12.081, 34.478, 21.193, 24.388, 7.851, 49.669, 7.925]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def trajectory(path: Path) -> dict[str, dict[str, np.ndarray]]:
    rows = read_csv(path)
    x = np.asarray([int(row["n_labeled"]) for row in rows])
    out: dict[str, dict[str, np.ndarray]] = {}
    for route in ROUTES[:-1]:
        out[route] = {"x": x, "y": np.asarray([float(row[route]) for row in rows])}
    out["random"] = {
        "x": x,
        "y": np.asarray([float(row["random_mean"]) for row in rows]),
        "q25": np.asarray([float(row["random_q25"]) for row in rows]),
        "q75": np.asarray([float(row["random_q75"]) for row in rows]),
    }
    return out


def style(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.set_facecolor("white")
    ax.grid(axis=grid_axis, color="#E7EBF0", linewidth=0.8, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#98A2B3")
    ax.spines["bottom"].set_color("#98A2B3")
    ax.tick_params(colors="#475467", labelsize=8.2, length=3)
    ax.set_axisbelow(True)


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.11, 1.04, label, transform=ax.transAxes, fontsize=13, weight="bold", color="#182230")


def plot_routes(ax: plt.Axes, data: dict[str, dict[str, np.ndarray]], title: str, x_max: int, show_y: bool, label: str) -> None:
    style(ax)
    ax.add_patch(Rectangle((2, 0), min(8, x_max - 2), 45, facecolor="#EAF4F2", edgecolor="none", zorder=0))
    ax.text(2.5, 42.1, "Low-data regime", color="#0F766E", fontsize=8.0, weight="bold")
    for route in ROUTES:
        d = data[route]
        if route == "random":
            ax.fill_between(d["x"], d["q25"], d["q75"], color=ROUTE_COLORS[route], alpha=0.16, linewidth=0, zorder=1)
        ax.plot(
            d["x"], d["y"], color=ROUTE_COLORS[route], linestyle=ROUTE_STYLES[route],
            linewidth=2.7 if route == "uncertainty_diversity" else 1.45,
            alpha=0.95 if route != "random" else 0.85, zorder=4 if route == "uncertainty_diversity" else 3,
            solid_capstyle="round",
        )
    ax.set_xlim(2, x_max)
    ax.set_ylim(0, 45)
    ax.set_xticks([2, 10, 20, 30, x_max] if x_max > 30 else [2, 5, 10, 15, 20, x_max])
    ax.set_yticks([0, 10, 20, 30, 40])
    ax.set_title(title, loc="left", fontsize=10.6, weight="bold", color="#182230", pad=8)
    panel_label(ax, label)
    ax.set_xlabel("Revealed substrates", fontsize=9.2, color="#344054", labelpad=5)
    if show_y:
        ax.set_ylabel("Retrospective ee MAE (percentage points)", fontsize=9.2, color="#344054", labelpad=7)
    ax.text(0.98, -0.17, "Increasing experimental information →", transform=ax.transAxes, ha="right", fontsize=7.8, color="#667085")


def plot_version_benchmark(ax: plt.Axes) -> None:
    style(ax, "x")
    panel_label(ax, "B")
    y = np.arange(len(VERSIONS))
    auc_base = VERSION_AUC[0]
    fluct_base = VERSION_FLUCT[0]
    for idx, (version, color) in enumerate(zip(VERSIONS, VERSION_COLORS)):
        ax.plot([auc_base, VERSION_AUC[idx]], [idx, idx], color="#D0D5DD", lw=1.5, zorder=1)
        ax.scatter(VERSION_AUC[idx], idx, s=55 if idx not in (4, 6) else 78, color=color, edgecolor="white", linewidth=1.0, zorder=3)
        if idx in (4, 6):
            ax.text(VERSION_AUC[idx] - 0.14, idx + 0.24, version, ha="right", va="bottom", fontsize=8.2, weight="bold", color=color)
    ax.set_yticks(y)
    ax.set_yticklabels(VERSIONS, fontsize=8.6, color="#344054")
    ax.invert_yaxis()
    ax.set_xlim(11.4, 15.4)
    ax.set_xticks([12, 13, 14, 15])
    ax.set_xlabel("Mean normalized AUC-MAE (lower is better)", fontsize=9.0, color="#344054", labelpad=6)
    ax.set_title("V0–V6 feature-version benchmark", loc="left", fontsize=10.6, weight="bold", color="#182230", pad=8)
    ax.text(0.0, 1.04, "Pooled P7 + CMC-Por; ee + isolated yield", transform=ax.transAxes, fontsize=7.8, color="#667085")
    ax.text(0.0, -0.19, "Each version drives its own uncertainty–diversity order; values are normalized across cells.", transform=ax.transAxes, fontsize=7.7, color="#667085")
    ax.text(VERSION_AUC[4] - 0.12, 4.65, "V4: lowest error", ha="right", va="top", fontsize=8.0, color="#075985", weight="bold")
    ax.text(VERSION_AUC[6] + 0.12, 6.1, "V6: most stable", ha="left", va="bottom", fontsize=8.0, color="#075985", weight="bold")
    ax2 = ax.twiny()
    ax2.set_xlim(0.72, 2.25)
    ax2.set_xticks([0.8, 1.2, 1.6, 2.0])
    ax2.set_xlabel("Mean fluctuation (lower is more stable)", fontsize=8.6, color="#667085", labelpad=5)
    ax2.tick_params(colors="#667085", labelsize=7.5, length=3)
    ax2.spines["top"].set_color("#CBD5E1")
    ax2.spines["bottom"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.plot(VERSION_FLUCT, y, color="#94A3B8", lw=1.0, alpha=0.7, marker="|", markersize=7, zorder=2)
    ax2.set_yticks([])


def plot_pareto(ax: plt.Axes) -> None:
    style(ax)
    panel_label(ax, "C")
    for idx, (version, color) in enumerate(zip(VERSIONS, VERSION_COLORS)):
        size = 90 if version in ("V4", "V6") else 52
        ax.scatter(VERSION_AUC[idx], VERSION_FLUCT[idx], s=size, color=color, edgecolor="white", linewidth=1.0, zorder=4)
        dx, dy = (0.04, 0.03)
        if version == "V0": dx, dy = (0.05, 0.03)
        if version == "V4": dx, dy = (-0.06, 0.055)
        if version == "V6": dx, dy = (0.05, -0.055)
        ax.text(VERSION_AUC[idx] + dx, VERSION_FLUCT[idx] + dy, version, fontsize=8.2, weight="bold" if version in ("V4", "V6") else "normal", color=color)
    ax.annotate("better prediction\nand stability", xy=(12.1, 0.80), xytext=(13.25, 0.82), arrowprops={"arrowstyle": "-|>", "color": "#0F766E", "lw": 1.2}, fontsize=8.0, color="#0F766E", ha="center")
    ax.set_xlim(11.4, 15.4)
    ax.set_ylim(0.72, 2.25)
    ax.set_xticks([12, 13, 14, 15])
    ax.set_yticks([0.8, 1.2, 1.6, 2.0])
    ax.set_xlabel("Mean normalized AUC-MAE", fontsize=9.0, color="#344054", labelpad=6)
    ax.set_ylabel("Mean trajectory fluctuation", fontsize=9.0, color="#344054", labelpad=6)
    ax.set_title("Prediction versus stability", loc="left", fontsize=10.6, weight="bold", color="#182230", pad=8)
    ax.text(0.0, 1.04, "Lower-left is preferable", transform=ax.transAxes, fontsize=7.8, color="#667085")
    ax.text(0.0, -0.19, "V4 minimizes pooled error; V6 gives the lowest pooled fluctuation.", transform=ax.transAxes, fontsize=7.7, color="#667085")


def plot_robustness(ax: plt.Axes) -> None:
    style(ax)
    panel_label(ax, "D")
    rows = [
        ("P7", "Elastic Net", None, 16), ("", "Ridge", None, 16), ("", "Tanimoto-kNN", 37, 17),
        ("CMC-Por", "Elastic Net", 12, 6), ("", "Ridge", 16, 8), ("", "Tanimoto-kNN", 7, 14),
    ]
    ys = np.array([5.0, 4.0, 3.0, 1.55, 0.55, -0.45])
    ax.axhline(2.25, color="#D0D5DD", lw=0.8)
    ax.axvspan(0, 10, color="#F8FAFC", zorder=0)
    for y, (domain, model, reported, ud) in zip(ys, rows):
        if reported is None:
            ax.text(30.5, y + 0.03, "not reached", ha="center", va="center", fontsize=7.8, color="#667085", style="italic")
        else:
            ax.plot([reported, ud], [y, y], color="#CBD5E1", lw=2.0, zorder=2)
            ax.add_patch(FancyArrowPatch((reported, y), (ud, y), arrowstyle="-|>", mutation_scale=9, color="#0F766E", lw=1.5, zorder=3))
            ax.scatter(reported, y, s=48, color="#667085", edgecolor="white", linewidth=1, zorder=5)
            ax.text(reported, y + 0.18, str(reported), ha="center", va="bottom", fontsize=7.7, color="#667085", weight="bold")
        ax.scatter(ud, y, s=54, color="#0F766E", edgecolor="white", linewidth=1, zorder=5)
        ax.text(ud, y - 0.18, str(ud), ha="center", va="top", fontsize=7.7, color="#0F766E", weight="bold")
    ax.set_xlim(0, 42)
    ax.set_ylim(-1.08, 5.65)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{domain}  {model}" if domain else f"              {model}" for domain, model, _, _ in rows], fontsize=7.7, color="#344054")
    ax.set_xticks([0, 10, 20, 30, 40])
    ax.set_xlabel("n₉₀: substrates needed to reach the 90% threshold", fontsize=8.9, color="#344054", labelpad=6)
    ax.set_title("Estimator robustness and limits", loc="left", fontsize=10.6, weight="bold", color="#182230", pad=8)
    ax.text(0.0, 1.04, "Independent multi-estimator experiment; lower is earlier", transform=ax.transAxes, fontsize=7.8, color="#667085")
    ax.text(0.0, -0.19, "CMC-Por Tanimoto-kNN is an estimator-dependent exception: reported order reaches n₉₀ earlier.", transform=ax.transAxes, fontsize=7.5, color="#667085")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    p7 = trajectory(DATA / "panel_a_p7_ridge_route_progression.csv")
    cmc = trajectory(DATA / "panel_b_cmcpor_ridge_route_progression.csv")
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": "white", "savefig.facecolor": "white"})
    fig = plt.figure(figsize=(15.0, 9.6), constrained_layout=False)
    gs = fig.add_gridspec(2, 3, left=0.065, right=0.985, top=0.87, bottom=0.12, wspace=0.34, hspace=0.55, height_ratios=[1.0, 1.0])
    ax_a1 = fig.add_subplot(gs[0, 0])
    ax_a2 = fig.add_subplot(gs[0, 1])
    ax_b = fig.add_subplot(gs[0, 2])
    ax_c = fig.add_subplot(gs[1, 0:2])
    ax_d = fig.add_subplot(gs[1, 2])
    plot_routes(ax_a1, p7, "Fe(P7)Cl: route order", 37, True, "A")
    plot_routes(ax_a2, cmc, "Fe(CMC-Por)Cl: route order", 25, False, "")
    ax_a2.set_yticklabels([])
    plot_version_benchmark(ax_b)
    plot_pareto(ax_c)
    plot_robustness(ax_d)
    fig.suptitle("Acquisition order and feature design jointly determine learning efficiency", x=0.065, y=0.94, ha="left", fontsize=15.5, weight="bold", color="#182230")
    fig.text(0.065, 0.912, "Retrospective progressive acquisition of locked substrate outcomes", fontsize=9.3, color="#667085", ha="left")
    handles = [Line2D([0], [0], color=ROUTE_COLORS[r], lw=2.7 if r == "uncertainty_diversity" else 1.7, linestyle=ROUTE_STYLES[r], label=ROUTE_LABELS[r]) for r in ROUTES]
    handles.insert(3, Line2D([0], [0], color=ROUTE_COLORS["random"], lw=6, alpha=0.18, label="Random IQR"))
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.065, 0.902), ncol=6, frameon=False, fontsize=8.1, handlelength=2.2, columnspacing=1.1, handletextpad=0.4)
    fig.text(0.065, 0.055, "A: standard V0 route comparison. B–C: corrected V0–V6 feature-mixture benchmark pooled across P7/CMC-Por and ee/yield. D: independent estimator convergence audit. Lower is better; all results are retrospective.", fontsize=8.0, color="#667085", ha="left")

    for ext, dpi in (("svg", None), ("pdf", None), ("png", 320)):
        path = OUT / f"figure3_v0_v6.{ext}"
        kwargs = {"bbox_inches": "tight", "pad_inches": 0.08}
        if dpi:
            kwargs["dpi"] = dpi
        fig.savefig(path, **kwargs)
    plt.close(fig)

    manifest = {
        "figure": "3A-D revised",
        "title": "Acquisition order and feature design jointly determine learning efficiency",
        "panels": {
            "A": "Five acquisition routes for P7 and CMC-Por aryl under the baseline representation",
            "B": "V0-V6 pooled feature-mixture benchmark with AUC-MAE and fluctuation",
            "C": "Prediction versus stability Pareto view for V0-V6",
            "D": "Independent Elastic Net/Ridge/Tanimoto-kNN n90 robustness audit",
        },
        "source_files": [
            "output/figures/figure3_data/panel_a_p7_ridge_route_progression.csv",
            "output/figures/figure3_data/panel_b_cmcpor_ridge_route_progression.csv",
            "docs/rule-feature-mixture-results.md",
            "output/supporting-information/manuscript-results.md",
            "output/figures/figure3_data/panel_d_independent_ee_estimator_metrics.csv",
        ],
        "caveats": [
            "The pooled V0-V6 benchmark combines P7/CMC-Por and ee/isolated-yield cells.",
            "The current CMC route curves are the Figure 3 aryl cohort; the persisted rule V0-V3 CMC replay uses a different full cohort.",
            "V4-V6 are shown as feature-mixture summary metrics, not as direct CMC aryl prefix curves.",
            "All results are retrospective and do not establish prospective experimental savings.",
        ],
        "outputs": [
            "output/figures/figure3_v0_v6.svg",
            "output/figures/figure3_v0_v6.pdf",
            "output/figures/figure3_v0_v6.png",
        ],
    }
    (OUT / "figure3_v0_v6_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT / 'figure3_v0_v6.png'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render the two-catalyst acquisition-weight simplex sensitivity plot."""
import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE / "results" / "weight_sensitivity"
OUT = BASE / "weight_sensitivity_simplex.png"
HEIGHT = np.sqrt(3.0) / 2.0


def rows(domain):
    with (BASE / domain / "weight_summary.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def xy(d, u, c):
    # Barycentric vertices: diversity bottom-left, uncertainty bottom-right,
    # coverage at the apex.
    return u + c * 0.5, c * HEIGHT


def draw_grid(ax):
    ax.plot([0, 1, 0.5, 0], [0, 0, HEIGHT, 0], color="#333333", lw=1.1)
    for i in range(1, 5):
        t = i / 5
        # Constant coverage (horizontal).
        ax.plot([0.5 * t, 1 - 0.5 * t], [HEIGHT * t, HEIGHT * t], color="#d6d6d6", lw=0.65)
        # Constant diversity and uncertainty lines.
        ax.plot([t, 0.5 * (1 - t)], [0, HEIGHT * (1 - t)], color="#d6d6d6", lw=0.65)
        ax.plot([1 - t, 0.5 * (1 - t)], [0, HEIGHT * (1 - t)], color="#d6d6d6", lw=0.65)
    ax.text(-0.035, -0.055, "Diversity (D)", ha="left", va="top", fontsize=9)
    ax.text(1.035, -0.055, "Uncertainty (U)", ha="right", va="top", fontsize=9)
    ax.text(0.5, HEIGHT + 0.035, "Family coverage (C)", ha="center", va="bottom", fontsize=9)
    ax.set_xlim(-0.10, 1.10)
    ax.set_ylim(-0.12, HEIGHT + 0.12)
    ax.set_aspect("equal")
    ax.axis("off")


def main():
    domains = [("p7", "Fe(P7)Cl"), ("cmcpor", "Fe(CMC-Por)Cl")]
    all_rows = {domain: rows(domain) for domain, _ in domains}
    vals = [float(r["mean_split_mae"]) for group in all_rows.values() for r in group]
    norm = Normalize(vmin=min(vals), vmax=max(vals))
    cmap = plt.get_cmap("viridis_r")
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.7), constrained_layout=True)
    for ax, (domain, title) in zip(axs, domains):
        draw_grid(ax)
        group = all_rows[domain]
        for r in group:
            d, u, c = (float(r[k]) for k in ("w_diversity", "w_uncertainty", "w_family_coverage"))
            x, y = xy(d, u, c)
            default = r["is_default"].lower() == "true"
            ax.scatter(x, y, c=[float(r["mean_split_mae"])], cmap=cmap, norm=norm,
                       s=105 if default else 70, marker="*" if default else "o",
                       edgecolors="black" if default else "white", linewidths=1.0 if default else 0.55,
                       zorder=5 if default else 3)
        default_row = next(r for r in group if r["is_default"].lower() == "true")
        x, y = xy(float(default_row["w_diversity"]), float(default_row["w_uncertainty"]), float(default_row["w_family_coverage"]))
        ax.annotate("0.40 / 0.40 / 0.20", (x, y), xytext=(8, 8), textcoords="offset points", fontsize=8,
                    bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#555555", "alpha": 0.9})
        ax.set_title(title, fontsize=12, pad=15)
    sm = ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array(np.asarray(vals))
    cbar = fig.colorbar(sm, ax=axs, shrink=0.83, pad=0.025)
    cbar.set_label("Mean held-out Ridge MAE (ee points)", fontsize=9)
    fig.suptitle("Retrospective acquisition-weight sensitivity", fontsize=13)
    fig.savefig(OUT, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(OUT)


if __name__ == "__main__":
    main()

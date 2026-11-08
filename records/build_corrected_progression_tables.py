"""Build compact corrected AUC tables and SI figures from rerun curves."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CORRECTED = HERE / "corrected_project/analysis_runs/independent_progression"
ORIGINALS = {
    "p7": ROOT / "data/jacs_2025/scope_progression/scope-progression-manifest.json",
    "cmcpor_aryl": ROOT / "data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression/scope-progression-manifest.json",
}
ALIASES = {
    "diversity_first": "D",
    "uncertainty_diversity": "U",
    "performance_first": "P",
    "random": "R",
    "historical_order": "H",
}
MODEL_ALIASES = {"elastic_net": "EN", "ridge": "R", "tanimoto_knn": "K"}
TABLES = {
    ("p7", "ee_percent"): "corrected_Table_S9_p7_ee.csv",
    ("p7", "isolated_yield_percent"): "corrected_Table_S10_p7_yield.csv",
    ("cmcpor_aryl", "ee_percent"): "corrected_Table_S11_cmc_ee.csv",
    ("cmcpor_aryl", "isolated_yield_percent"): "corrected_Table_S12_cmc_yield.csv",
}
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
NAVY = "#172B3A"
GRAY = "#8B98A5"
TEAL = "#277C8E"
ORANGE = "#D28D35"
PURPLE = "#7C6AA6"
RED = "#C85A54"
GRID = "#E7EBEF"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def chart_axes(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], ymax: float, ticks: int, y_label: str) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    draw.line((left, top, left, bottom), fill=NAVY, width=2)
    draw.line((left, bottom, right, bottom), fill=NAVY, width=2)
    for index in range(ticks + 1):
        value = ymax * index / ticks
        y = bottom - int((bottom - top) * index / ticks)
        draw.line((left, y, right, y), fill=GRID, width=1)
        draw.text((left - 70, y - 13), f"{value:.0f}", font=font(22), fill=NAVY)
    draw.text((left - 58, top - 58), y_label, font=font(23), fill=NAVY)
    return box


def line_chart(image: Image.Image, box: tuple[int, int, int, int], rows: list[dict], ymax: float) -> None:
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = box
    chart_axes(draw, box, ymax, 6, "MAE (ee points)")
    colors = {"historical_order": GRAY, "uncertainty_diversity": TEAL, "diversity_first": ORANGE, "performance_first": PURPLE, "random": RED}
    labels = {"historical_order": "Source order", "uncertainty_diversity": "Uncertainty–diversity", "diversity_first": "Diversity-first", "performance_first": "Performance-first", "random": "Random (500 replicates)"}
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["route"], []).append(row)
    x_min = min(int(row["n_labeled"]) for row in rows)
    x_max = max(int(row["n_labeled"]) for row in rows)

    def point(row: dict) -> tuple[int, int]:
        x = left + int((right - left) * (int(row["n_labeled"]) - x_min) / max(1, x_max - x_min))
        y = bottom - int((bottom - top) * float(row["mae_mean"]) / ymax)
        return x, y

    for route, route_rows in grouped.items():
        route_rows.sort(key=lambda row: int(row["n_labeled"]))
        color = colors[route]
        if route == "random":
            upper = [(point({**row, "mae_mean": row["mae_q75"]})[0], bottom - int((bottom - top) * float(row["mae_q75"]) / ymax)) for row in route_rows]
            lower = [(point({**row, "mae_mean": row["mae_q25"]})[0], bottom - int((bottom - top) * float(row["mae_q25"]) / ymax)) for row in reversed(route_rows)]
            layer = Image.new("RGBA", image.size, (255, 255, 255, 0)); ld = ImageDraw.Draw(layer)
            ld.polygon(upper + lower, fill=(200, 90, 84, 34))
            image.alpha_composite(layer)
            draw = ImageDraw.Draw(image)
        pts = [point(row) for row in route_rows]
        draw.line(pts, fill=color, width=4)
        for x, y in pts[::max(1, len(pts)//12)]:
            draw.ellipse((x-4, y-4, x+4, y+4), fill=color)
    for value in range(x_min, x_max + 1, max(1, (x_max - x_min) // 5)):
        x = left + int((right - left) * (value - x_min) / max(1, x_max - x_min))
        draw.text((x - 12, bottom + 14), str(value), font=font(20), fill=NAVY)
    draw.text(((left + right)//2 - 95, bottom + 55), "Labeled substrates", font=font(22), fill=NAVY)
    legend_y = top + 20
    for i, route in enumerate(["historical_order", "uncertainty_diversity", "diversity_first", "performance_first", "random"]):
        x = left + (i % 2) * 360
        y = legend_y + (i // 2) * 38
        draw.line((x, y+13, x+32, y+13), fill=colors[route], width=4)
        draw.text((x+42, y), labels[route], font=font(17), fill=NAVY)


def bar_chart(image: Image.Image, box: tuple[int, int, int, int], labels: list[str], left_values: list[float], right_values: list[float], ymax: float, y_label: str) -> None:
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = box
    chart_axes(draw, box, ymax, 5, y_label)
    groups = len(labels); group_w = (right - left) / groups; bar_w = min(52, int(group_w * 0.29))
    for i, label in enumerate(labels):
        cx = left + int(group_w * (i + 0.5))
        for val, dx, color in [(left_values[i], -bar_w//2, GRAY), (right_values[i], bar_w//2, TEAL)]:
            h = int((bottom - top) * val / ymax)
            draw.rectangle((cx+dx, bottom-h, cx+dx+bar_w-4, bottom), fill=color)
            draw.text((cx+dx-5, bottom-h-28), f"{val:.0f}", font=font(16), fill=NAVY)
        draw.multiline_text((cx-group_w*0.45, bottom+13), label, font=font(16), fill=NAVY, align="center", spacing=2)
    draw.rectangle((left+20, top+15, left+48, top+35), fill=GRAY); draw.text((left+58, top+12), "Source order", font=font(17), fill=NAVY)
    draw.rectangle((left+195, top+15, left+223, top+35), fill=TEAL); draw.text((left+233, top+12), "Uncertainty–diversity", font=font(17), fill=NAVY)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    summary_rows: list[dict] = []
    data_for_figures = {}
    for domain, target in [(d, t) for d in ORIGINALS for t in ("ee_percent", "isolated_yield_percent")]:
        folder = CORRECTED / domain
        manifest = json.loads((folder / "scope-progression-manifest.json").read_text(encoding="utf-8"))
        old_manifest = json.loads(ORIGINALS[domain].read_text(encoding="utf-8"))
        with (folder / "learning-curve-summary.csv").open(encoding="utf-8", newline="") as stream:
            curve_rows = list(csv.DictReader(stream))
        route_endpoints = {}
        for row in curve_rows:
            if row["target"] != target:
                continue
            key = (row["route"], row["model"])
            endpoint = route_endpoints.get(key)
            n = int(row["n_labeled"])
            if endpoint is None or n > endpoint[0]:
                route_endpoints[key] = (n, float(row["mae_mean"]))

        table_rows: list[dict] = []
        for route in ["diversity_first", "uncertainty_diversity", "performance_first", "random", "historical_order"]:
            for model in ["elastic_net", "ridge", "tanimoto_knn"]:
                key = f"{target}:{route}:{model}"
                convergence = manifest.get("convergence", {}).get(key)
                if not convergence:
                    continue
                final_n, final_mae = route_endpoints[(route, model)]
                reference_mae = manifest["reference_metrics"][target][f"{model}_loo_mae"]
                old = old_manifest.get("convergence", {}).get(key, {})
                row = {
                    "route": ALIASES[route],
                    "model": MODEL_ALIASES[model],
                    "final_n": final_n,
                    "final_mae": round(final_mae, 3),
                    "auc_mae": round(float(convergence["auc_mae"]), 3),
                    "n90": convergence.get("n90", "NA"),
                    "reference_loo_mae": round(float(reference_mae), 3),
                    "final_minus_reference": round(final_mae - float(reference_mae), 3),
                    "archived_auc_mae": round(float(old.get("auc_mae", float("nan"))), 3),
                }
                table_rows.append(row)
                summary_rows.append({"domain": domain, "target": target, **row})
        table_path = HERE / "corrected_project/independent_progression_tables" / TABLES[(domain, target)]
        write_csv(table_path, table_rows)
        data_for_figures[(domain, target)] = {"manifest": manifest, "curve_rows": curve_rows}

    write_csv(HERE / "corrected_project/analysis_runs/independent_progression/corrected_auc_summary.csv", summary_rows)

    metrics = data_for_figures[("cmcpor_aryl", "isolated_yield_percent")]["manifest"]["convergence"]
    models = ["elastic_net", "ridge", "tanimoto_knn"]
    labels = ["Elastic Net", "Ridge", "Tanimoto-kNN"]
    historical = [metrics[f"isolated_yield_percent:historical_order:{m}"]["auc_mae"] for m in models]
    ud = [metrics[f"isolated_yield_percent:uncertainty_diversity:{m}"]["auc_mae"] for m in models]
    image = Image.new("RGBA", (1800, 1050), "white")
    draw = ImageDraw.Draw(image)
    draw.text((110, 35), "Corrected Fe(CMC-Por)Cl aryl yield trajectories", font=font(37), fill=NAVY)
    bar_chart(image, (250, 190, 1650, 810), labels, historical, ud, max(historical + ud) * 1.14, "Yield AUC-MAE")
    draw.text((250, 900), "Lower values indicate lower integrated error across the retrospective reveal trajectory.", font=font(23), fill="#52616D")
    image.convert("RGB").save(HERE / "figures/figureS5_corrected_yield_auc.png", dpi=(300, 300))

    image = Image.new("RGBA", (3000, 1400), "white")
    draw = ImageDraw.Draw(image)
    draw.text((110, 35), "Corrected independent acquisition analyses", font=font(42), fill=NAVY)
    p7_curves = data_for_figures[("p7", "ee_percent")]["curve_rows"]
    curve_rows = [r for r in p7_curves if r["target"] == "ee_percent" and r["model"] == "ridge"]
    draw.text((100, 145), "A  Fe(P7)Cl Ridge ee learning curve", font=font(28), fill=NAVY)
    line_chart(image, (220, 250, 1390, 960), curve_rows, 60)
    ax_auc_data = []
    for domain, domain_label in [("p7", "Fe(P7)Cl"), ("cmcpor_aryl", "Fe(CMC-Por)Cl")]:
        conv = data_for_figures[(domain, "ee_percent")]["manifest"]["convergence"]
        for model, model_label in zip(models, labels):
            ax_auc_data.append((domain_label, model_label, conv[f"ee_percent:historical_order:{model}"]["auc_mae"], conv[f"ee_percent:uncertainty_diversity:{model}"]["auc_mae"]))
    draw.text((1540, 145), "B  Ee AUC-MAE by estimator", font=font(28), fill=NAVY)
    bar_chart(image, (1650, 250, 2890, 960), [f"{dom}\n{mod}" for dom, mod, *_ in ax_auc_data], [v[2] for v in ax_auc_data], [v[3] for v in ax_auc_data], max(v[2] for v in ax_auc_data) * 1.14, "Ee AUC-MAE")
    draw.text((1650, 1050), "AUC-MAE is a separate retrospective trajectory metric; it is not the mean-prefix MAE in the main dedicated comparison.", font=font(20), fill="#52616D")
    image.convert("RGB").save(HERE / "figures/figureS6_corrected_independent_acquisition.png", dpi=(300, 300))
    print(f"Wrote {len(summary_rows)} corrected route/model AUC rows and two figures")


if __name__ == "__main__":
    main()

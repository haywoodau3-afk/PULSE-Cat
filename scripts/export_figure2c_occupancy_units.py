#!/usr/bin/env python3
"""Export the three Figure 2C occupancy plots as standalone PNG/SVG figures."""

from __future__ import annotations

import html
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "output/figures/figure2c_data"
ANALYSIS = PACKAGE / "figure2c_selected_pair_analysis.json"
OUT = ROOT / "output/figures/figure2c_units/figure2c_04_occupancy_parts"

P7 = "#087f8c"
CMC = "#c45b35"
INK = "#17212b"
MUTED = "#56636d"
GRID = "#d8dde2"
PLOT_BG = "#fbfcfd"
FIELD = "nitrene__all_heavy__all_200"

WIDTH, HEIGHT = 600, 500
PLOT_X, PLOT_Y, PLOT_W, PLOT_H = 100, 125, 440, 300


def normalized(values: np.ndarray) -> np.ndarray:
    return values.astype(float) / float(values.sum())


def rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def fields(spec: dict, p7: np.ndarray, cmc: np.ndarray):
    if spec["kind"] == "p7":
        return [(p7, P7, 0.82)]
    if spec["kind"] == "cmc":
        return [(cmc, CMC, 0.82)]
    return [(p7, P7, 0.56), (cmc, CMC, 0.56)]


def svg_figure(spec: dict, metadata: dict, p7: np.ndarray, cmc: np.ndarray) -> str:
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img">',
        f'<title>{html.escape(spec["title"])}</title>',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="28" y="38" font-family="Arial, sans-serif" font-size="25" font-weight="700" fill="{spec["title_color"]}">{html.escape(spec["title"])}</text>',
        f'<text x="28" y="65" font-family="Arial, sans-serif" font-size="13" fill="{MUTED}">{html.escape(spec["detail"])}</text>',
        f'<text x="28" y="88" font-family="Arial, sans-serif" font-size="12" fill="{MUTED}">{html.escape(metadata["canonical_overlap_group"])}</text>',
        f'<rect x="{PLOT_X}" y="{PLOT_Y}" width="{PLOT_W}" height="{PLOT_H}" fill="{PLOT_BG}" stroke="{GRID}"/>',
    ]

    for array, color, opacity_scale in fields(spec, p7, cmc):
        probability = normalized(array)
        scaled = np.sqrt(probability / max(float(probability.max()), 1e-15))
        cell_w = PLOT_W / probability.shape[1]
        cell_h = PLOT_H / probability.shape[0]
        for iz in range(probability.shape[0]):
            for ir in range(probability.shape[1]):
                opacity = float(scaled[iz, ir]) * opacity_scale
                if opacity < 0.025:
                    continue
                x = PLOT_X + ir * cell_w
                y = PLOT_Y + (probability.shape[0] - 1 - iz) * cell_h
                out.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_w + .25:.2f}" height="{cell_h + .25:.2f}" fill="{color}" opacity="{opacity:.3f}"/>'
                )

    for rho_value in (0, 2, 4, 6, 8, 10):
        x = PLOT_X + rho_value / 10 * PLOT_W
        out.append(f'<line x1="{x:.1f}" y1="{PLOT_Y + PLOT_H}" x2="{x:.1f}" y2="{PLOT_Y + PLOT_H + 6}" stroke="{MUTED}"/>')
        out.append(f'<text x="{x:.1f}" y="{PLOT_Y + PLOT_H + 23}" font-family="Arial, sans-serif" font-size="11" text-anchor="middle" fill="{MUTED}">{rho_value}</text>')
    for z_value in (-8, -4, 0, 4, 8, 12):
        y = PLOT_Y + PLOT_H - (z_value + 8) / 20 * PLOT_H
        out.append(f'<line x1="{PLOT_X - 6}" y1="{y:.1f}" x2="{PLOT_X}" y2="{y:.1f}" stroke="{MUTED}"/>')
        out.append(f'<text x="{PLOT_X - 11}" y="{y + 4:.1f}" font-family="Arial, sans-serif" font-size="11" text-anchor="end" fill="{MUTED}">{z_value}</text>')
    out.append(f'<text x="{PLOT_X + PLOT_W / 2}" y="482" font-family="Arial, sans-serif" font-size="13" text-anchor="middle" fill="{MUTED}">radial ρ (Å)</text>')
    out.append(f'<text x="34" y="{PLOT_Y + PLOT_H / 2}" font-family="Arial, sans-serif" font-size="13" text-anchor="middle" fill="{MUTED}" transform="rotate(-90 34 {PLOT_Y + PLOT_H / 2})">axial z (Å)</text>')
    if spec["kind"] == "overlay":
        out.extend([
            f'<rect x="345" y="139" width="12" height="12" fill="{P7}" opacity=".72"/><text x="363" y="150" font-family="Arial, sans-serif" font-size="11" fill="{MUTED}">P7</text>',
            f'<rect x="407" y="139" width="12" height="12" fill="{CMC}" opacity=".72"/><text x="425" y="150" font-family="Arial, sans-serif" font-size="11" fill="{MUTED}">CMC-Por</text>',
        ])
    out.append("</svg>\n")
    return "".join(out)


def font(size: int, bold: bool = False):
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/SFNS.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def png_figure(spec: dict, metadata: dict, p7: np.ndarray, cmc: np.ndarray, path: Path) -> None:
    scale = 2
    image = Image.new("RGBA", (WIDTH * scale, HEIGHT * scale), "white")
    draw = ImageDraw.Draw(image)
    s = lambda value: int(round(value * scale))
    draw.text((s(28), s(14)), spec["title"], fill=rgb(spec["title_color"]), font=font(s(25), True))
    draw.text((s(28), s(48)), spec["detail"], fill=rgb(MUTED), font=font(s(13)))
    draw.text((s(28), s(72)), metadata["canonical_overlap_group"], fill=rgb(MUTED), font=font(s(12)))
    draw.rectangle((s(PLOT_X), s(PLOT_Y), s(PLOT_X + PLOT_W), s(PLOT_Y + PLOT_H)), fill=rgb(PLOT_BG), outline=rgb(GRID), width=s(1))

    for array, color, opacity_scale in fields(spec, p7, cmc):
        probability = normalized(array)
        scaled = np.sqrt(probability / max(float(probability.max()), 1e-15))
        cell_w = PLOT_W / probability.shape[1]
        cell_h = PLOT_H / probability.shape[0]
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        for iz in range(probability.shape[0]):
            for ir in range(probability.shape[1]):
                opacity = float(scaled[iz, ir]) * opacity_scale
                if opacity < 0.025:
                    continue
                x0 = s(PLOT_X + ir * cell_w)
                y0 = s(PLOT_Y + (probability.shape[0] - 1 - iz) * cell_h)
                x1 = s(PLOT_X + (ir + 1) * cell_w + 0.25)
                y1 = s(PLOT_Y + (probability.shape[0] - iz) * cell_h + 0.25)
                layer_draw.rectangle((x0, y0, x1, y1), fill=(*rgb(color), int(round(255 * opacity))))
        image = Image.alpha_composite(image, layer)
        draw = ImageDraw.Draw(image)

    for rho_value in (0, 2, 4, 6, 8, 10):
        x = PLOT_X + rho_value / 10 * PLOT_W
        draw.line((s(x), s(PLOT_Y + PLOT_H), s(x), s(PLOT_Y + PLOT_H + 6)), fill=rgb(MUTED), width=s(1))
        label = str(rho_value)
        box = draw.textbbox((0, 0), label, font=font(s(11)))
        draw.text((s(x) - (box[2] - box[0]) / 2, s(PLOT_Y + PLOT_H + 9)), label, fill=rgb(MUTED), font=font(s(11)))
    for z_value in (-8, -4, 0, 4, 8, 12):
        y = PLOT_Y + PLOT_H - (z_value + 8) / 20 * PLOT_H
        draw.line((s(PLOT_X - 6), s(y), s(PLOT_X), s(y)), fill=rgb(MUTED), width=s(1))
        label = str(z_value)
        box = draw.textbbox((0, 0), label, font=font(s(11)))
        draw.text((s(PLOT_X - 11) - (box[2] - box[0]), s(y - 6)), label, fill=rgb(MUTED), font=font(s(11)))
    x_label = "radial ρ (Å)"
    x_font = font(s(13))
    box = draw.textbbox((0, 0), x_label, font=x_font)
    draw.text((s(PLOT_X + PLOT_W / 2) - (box[2] - box[0]) / 2, s(462)), x_label, fill=rgb(MUTED), font=x_font)
    y_text = "axial z (Å)"
    y_font = font(s(13))
    y_box = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), y_text, font=y_font)
    y_label = Image.new("RGBA", (y_box[2] - y_box[0] + s(4), y_box[3] - y_box[1] + s(4)), (0, 0, 0, 0))
    ImageDraw.Draw(y_label).text((s(2) - y_box[0], s(2) - y_box[1]), y_text, fill=rgb(MUTED), font=y_font)
    y_label = y_label.rotate(90, expand=True)
    image.alpha_composite(y_label, (s(28), s(PLOT_Y + PLOT_H / 2) - y_label.height // 2))

    if spec["kind"] == "overlay":
        draw = ImageDraw.Draw(image)
        draw.rectangle((s(345), s(139), s(357), s(151)), fill=rgb(P7))
        draw.text((s(363), s(136)), "P7", fill=rgb(MUTED), font=font(s(11)))
        draw.rectangle((s(407), s(139), s(419), s(151)), fill=rgb(CMC))
        draw.text((s(425), s(136)), "CMC-Por", fill=rgb(MUTED), font=font(s(11)))

    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("Title", spec["title"])
    pnginfo.add_text("Canonical substrate", metadata["canonical_overlap_group"])
    pnginfo.add_text("Occupancy field", FIELD)
    image.convert("RGB").save(path, dpi=(300, 300), optimize=True, pnginfo=pnginfo)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    pair_folder = PACKAGE / metadata["pair_directory"]
    p7 = np.load(pair_folder / metadata["p7_npz"])[FIELD]
    cmc = np.load(pair_folder / metadata["cmcpor_npz"])[FIELD]
    specs = [
        {
            "kind": "p7",
            "stem": "figure2c_04a_fe_p7cl_occupancy",
            "title": "Fe(P7)Cl occupancy",
            "title_color": P7,
            "detail": "Record 1i · exact shared connectivity · 200-pose all-heavy field",
        },
        {
            "kind": "cmc",
            "stem": "figure2c_04b_fe_cmcporcl_occupancy",
            "title": "Fe(CMC-Por)Cl occupancy",
            "title_color": CMC,
            "detail": "Record 2r · exact shared connectivity · 200-pose all-heavy field",
        },
        {
            "kind": "overlay",
            "stem": "figure2c_04c_shared_identity_occupancy_overlay",
            "title": "Shared-identity occupancy overlay",
            "title_color": INK,
            "detail": f'JS {metadata["jensen_shannon_bits"]:.4f} bits · TV {metadata["total_variation_distance"]:.4f} · Bhattacharyya {metadata["bhattacharyya_overlap"]:.4f}',
        },
    ]
    manifest = {
        "source_analysis": str(ANALYSIS.relative_to(ROOT)),
        "identity_validation": "output/figures/figure2c_data/figure2c_substrate_identity_validation.json",
        "pair_relationship": "exact same substrate connectivity, verified across 200 frames per catalyst",
        "occupancy_field": FIELD,
        "units": [],
    }
    for spec in specs:
        svg_path = OUT / f'{spec["stem"]}.svg'
        png_path = OUT / f'{spec["stem"]}.png'
        svg_path.write_text(svg_figure(spec, metadata, p7, cmc), encoding="utf-8")
        png_figure(spec, metadata, p7, cmc, png_path)
        manifest["units"].append({**spec, "png": str(png_path.relative_to(ROOT)), "svg": str(svg_path.relative_to(ROOT)), "dimensions_px": [1200, 1000]})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

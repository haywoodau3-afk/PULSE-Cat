#!/usr/bin/env python3
"""Export the five data-derived Figure 2C units as standalone assets."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from PIL import Image, PngImagePlugin


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/figures/figure2c_pose_context.png"
OUT = ROOT / "output/figures/figure2c_units"

# Crop boxes are in pixels in the 3200 x 2160, 2x browser export. They follow
# the exact panel boundaries in figure2c-data-derived.html.
UNITS = [
    {
        "number": 1,
        "slug": "p7_pose_ensemble",
        "title": "Fe(P7)Cl catalyst-referenced pose ensemble",
        "box": (76, 284, 1112, 1112),
        "basis": "3Dmol.js rendering of the real multi-model XYZ pose ensemble",
    },
    {
        "number": 2,
        "slug": "cmcpor_pose_ensemble",
        "title": "Fe(CMC-Por)Cl catalyst-referenced pose ensemble",
        "box": (1144, 284, 2180, 1112),
        "basis": "3Dmol.js rendering of the real multi-model XYZ pose ensemble",
    },
    {
        "number": 3,
        "slug": "shared_identity_overlay",
        "title": "Same-canonical-substrate aligned overlay",
        "box": (2212, 284, 3124, 1112),
        "basis": "Paired real XYZ files aligned on Fe and four coordinating porphyrin N atoms, with nitrene N as a lower-weight pivot",
    },
    {
        "number": 4,
        "slug": "npz_occupancy_overlay",
        "title": "Numerical occupancy-density comparison",
        "box": (76, 1144, 2044, 1972),
        "basis": "Real NumPy NPZ occupancy fields and the prepared occupancy SVG",
    },
    {
        "number": 5,
        "slug": "cube_volumetric_map",
        "title": "3D volumetric occupancy map",
        "box": (2076, 1144, 3124, 1972),
        "basis": "3Dmol.js isosurfaces generated from real CUBE volumetric fields",
    },
]


def svg_wrapper(png_path: Path, width: int, height: int, title: str) -> str:
    encoded = base64.b64encode(png_path.read_bytes()).decode("ascii")
    safe_title = (
        title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
  <title id="title">{safe_title}</title>
  <image width="{width}" height="{height}" href="data:image/png;base64,{encoded}"/>
</svg>
'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGB")
    if source.size != (3200, 2160):
        raise ValueError(f"Expected a 3200 x 2160 source, received {source.size}")

    manifest = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_dimensions_px": list(source.size),
        "identity_validation": "output/figures/figure2c_data/figure2c_substrate_identity_validation.json",
        "selected_pair": {
            "canonical_substrate": "Cc1cccc(CCc2ccccc2)c1N=[N+]=[N-]",
            "fe_p7cl_record": "1i",
            "fe_cmcporcl_record": "2r",
            "relationship": "exact same substrate connectivity, not merely structural similarity",
            "frames_verified_per_catalyst": 200,
            "catalyst_stripped_element_counts": {"C": 15, "H": 15, "N": 1},
        },
        "units": [],
    }

    for unit in UNITS:
        left, top, right, bottom = unit["box"]
        cropped = source.crop(unit["box"])
        stem = f'figure2c_{unit["number"]:02d}_{unit["slug"]}'
        png_path = OUT / f"{stem}.png"
        svg_path = OUT / f"{stem}.svg"

        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Title", unit["title"])
        metadata.add_text("Source", str(SOURCE.relative_to(ROOT)))
        metadata.add_text("Data basis", unit["basis"])
        cropped.save(png_path, dpi=(300, 300), pnginfo=metadata, optimize=True)
        svg_path.write_text(
            svg_wrapper(png_path, cropped.width, cropped.height, unit["title"]),
            encoding="utf-8",
        )

        manifest["units"].append(
            {
                **unit,
                "box": [left, top, right, bottom],
                "dimensions_px": [cropped.width, cropped.height],
                "png": str(png_path.relative_to(ROOT)),
                "svg": str(svg_path.relative_to(ROOT)),
            }
        )

    (OUT / "figure2c_units_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    readme = """# Figure 2C — separate units

These five files are exact crops of the final data-derived Figure 2C browser render. Each unit is supplied as a high-resolution PNG and as a self-contained SVG wrapper. The 3D molecular and volumetric panels are WebGL renders and therefore remain raster content inside the SVG wrappers.

1. **Fe(P7)Cl pose ensemble** — real multi-model XYZ rendered in 3Dmol.js.
2. **Fe(CMC-Por)Cl pose ensemble** — real multi-model XYZ rendered in 3Dmol.js.
3. **Shared-substrate overlay** — records 1i and 2r have the exact same catalyst-stripped substrate connectivity (C₁₅H₁₅N after N₂ loss), not merely similar structures. They are aligned using Fe plus the four coordinating porphyrin nitrogens; nitrene nitrogen was used as a lower-weight orientation pivot.
4. **NPZ occupancy comparison** — numerical occupancy fields and the prepared two-dimensional occupancy overlay.
5. **CUBE volumetric map** — three-dimensional occupancy isosurfaces made from the converted volumetric fields.

The manifest records source dimensions, crop coordinates, file names, data basis, and the selected shared-substrate identity. An independent RDKit connectivity audit verified all 200 frames in each catalyst trajectory and all 13 shared pairs. These visualizations summarize sampled catalyst-relative occupancy; they are not transition-state assignments, Boltzmann populations, or experimentally established selectivity-determining conformations.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()

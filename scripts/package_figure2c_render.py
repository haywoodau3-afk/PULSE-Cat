#!/usr/bin/env python3
"""Package the browser-rendered Figure 2C PNG into portable SVG deliverables."""
from __future__ import annotations

import base64
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "output/figures"


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> None:
    png = FIGURES / "figure2c_pose_context.png"
    panel_a = FIGURES / "figure2a_representation_ladder.svg"
    png_uri = data_uri(png, "image/png")
    figure_c = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1080" viewBox="0 0 1600 1080" role="img">'
        '<title>Figure 2C — same substrate, different catalyst-relative space</title>'
        '<desc>Data-derived 3Dmol pose ensembles, catalyst-core overlay, NPZ occupancy maps, and CUBE isosurfaces for one exact shared canonical substrate identity.</desc>'
        f'<image width="1600" height="1080" href="{png_uri}"/>'
        '</svg>\n'
    )
    (FIGURES / "figure2c_pose_context.svg").write_text(figure_c, encoding="utf-8")

    if panel_a.exists():
        a_uri = data_uri(panel_a, "image/svg+xml")
        composite = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1940" viewBox="0 0 1600 1940" role="img">'
            '<title>Figure 2A and 2C</title>'
            '<desc>Representation ladder and data-derived catalyst-referenced pose comparison.</desc>'
            f'<image width="1600" height="840" href="{a_uri}"/>'
            f'<image y="860" width="1600" height="1080" href="{png_uri}"/>'
            '</svg>\n'
        )
        (FIGURES / "figure2_ac.svg").write_text(composite, encoding="utf-8")
    print(FIGURES / "figure2c_pose_context.svg")
    print(FIGURES / "figure2_ac.svg")


if __name__ == "__main__":
    main()

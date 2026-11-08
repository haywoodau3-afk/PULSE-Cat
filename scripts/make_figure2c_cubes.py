#!/usr/bin/env python3
"""Create small Gaussian-CUBE views of the Figure 2C cylindrical occupancy fields.

The package stores Stage 2pp occupancy as z/rho arrays in NPZ files.  This
script revolves the selected nitrene/all-heavy/top-100 field around the axial
coordinate to make a Cartesian volume that 3Dmol.js can render as an
isosurface.  It is a visualization transform, not a new chemical descriptor.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "output" / "figures" / "figure2c_data"


def write_cube(path: Path, values: np.ndarray) -> None:
    # Use a 0.5 A Cartesian grid.  The source fields span z=-8..12 A and
    # rho=0..10 A; revolving rho onto x/y gives a compact 20 A cube.
    spacing = 0.5
    axis = np.arange(-10.0, 10.0 + spacing / 2, spacing)
    z_axis = np.arange(-8.0, 12.0 + spacing / 2, spacing)
    z_centers = np.arange(-7.75, 12.0, 0.5)
    rho_centers = np.arange(0.25, 10.0, 0.5)

    # Source is (z-bin, rho-bin); interpolate along each axis, then rotate
    # rho into x/y.  Values outside the source range are zero.
    out = np.empty((axis.size, axis.size, z_axis.size), dtype=float)
    for ix, x in enumerate(axis):
        for iy, y in enumerate(axis):
            rho = float(np.hypot(x, y))
            z_rho = np.array([
                np.interp(rho, rho_centers, row, left=0.0, right=0.0)
                for row in values
            ])
            out[ix, iy, :] = np.interp(z_axis, z_centers, z_rho, left=0.0, right=0.0)

    with path.open("w", encoding="utf-8") as handle:
        handle.write("PULSE-Pose cylindrical occupancy revolved for visualization\n")
        handle.write("Not electron density; not a transition-state or population assignment\n")
        handle.write(f"    0 {axis[0]: .6f} {axis[0]: .6f} {-8.0: .6f}\n")
        handle.write(f"{axis.size:5d} {spacing: .6f} 0.000000 0.000000\n")
        handle.write(f"{axis.size:5d} 0.000000 {spacing: .6f} 0.000000\n")
        handle.write(f"{z_axis.size:5d} 0.000000 0.000000 {spacing: .6f}\n")
        flat = out.ravel(order="C")
        for start in range(0, flat.size, 6):
            handle.write(" ".join(f"{v: .6e}" for v in flat[start : start + 6]) + "\n")


def main() -> None:
    manifest = PACKAGE / "shared_overlay_manifest.csv"
    made = 0
    with manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pair_dir = PACKAGE / row["pair_directory"]
            for domain, npz_name, stem in (
                ("fe_p7cl", row["p7_npz"], "p7cl"),
                ("fe_cmcporcl", row["cmcpor_npz"], "cmcporcl"),
            ):
                npz_path = pair_dir / npz_name
                cube_name = npz_path.stem + "_nitrene_all_heavy_top100.cube"
                cube_path = pair_dir / cube_name
                data = np.load(npz_path)
                values = data["nitrene__all_heavy__top_100"]
                write_cube(cube_path, values)
                made += 1
    print(f"created {made} occupancy CUBE files")


if __name__ == "__main__":
    main()

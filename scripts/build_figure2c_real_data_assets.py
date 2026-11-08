#!/usr/bin/env python3
"""Select and prepare a real-data shared-substrate example for Figure 2C."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

import numpy as np

from make_figure2c_cubes import write_cube


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "output/figures/figure2c_data"
FIELD = "nitrene__all_heavy__all_200"
P7 = "#087f8c"
CMC = "#c45b35"
INK = "#17212b"
MUTED = "#56636d"
GRID = "#d8dde2"


def read_xyz(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    frames = []
    cursor = 0
    while cursor < len(lines):
        count = int(lines[cursor])
        symbols, coords = [], []
        for line in lines[cursor + 2:cursor + 2 + count]:
            fields = line.split()
            symbols.append(fields[0])
            coords.append([float(value) for value in fields[1:4]])
        frames.append((symbols, np.asarray(coords)))
        cursor += count + 2
    return frames


def normalized(values: np.ndarray) -> np.ndarray:
    total = float(values.sum())
    if total <= 0:
        raise ValueError("empty occupancy field")
    return values.astype(float) / total


def metrics(p: np.ndarray, q: np.ndarray) -> dict[str, float]:
    p, q = normalized(p).ravel(), normalized(q).ravel()
    midpoint = 0.5 * (p + q)
    def kl(left, right):
        mask = left > 0
        return float(np.sum(left[mask] * np.log2(left[mask] / right[mask])))
    return {
        "jensen_shannon_bits": 0.5 * kl(p, midpoint) + 0.5 * kl(q, midpoint),
        "total_variation_distance": 0.5 * float(np.abs(p - q).sum()),
        "bhattacharyya_overlap": float(np.sqrt(p * q).sum()),
    }


def cylindrical_moments(values: np.ndarray) -> dict[str, float]:
    probability = normalized(values)
    z = np.arange(-7.75, 12.0, 0.5)[:, None]
    rho = np.arange(0.25, 10.0, 0.5)[None, :]
    mean_z = float((probability * z).sum())
    mean_rho = float((probability * rho).sum())
    return {
        "mean_z_angstrom": mean_z,
        "mean_rho_angstrom": mean_rho,
        "sd_z_angstrom": float(np.sqrt((probability * (z - mean_z) ** 2).sum())),
        "sd_rho_angstrom": float(np.sqrt((probability * (rho - mean_rho) ** 2).sum())),
        "z_rho_covariance_angstrom2": float((probability * (z - mean_z) * (rho - mean_rho)).sum()),
    }


def field_svg(pair: dict[str, str], p7: np.ndarray, cmc: np.ndarray, values: dict[str, float]) -> str:
    width, height = 1200, 430
    plot_w, plot_h, top = 320, 292, 82
    origins = [54, 440, 826]
    panels = [("Fe(P7)Cl", p7, P7, None), ("Fe(CMC-Por)Cl", cmc, CMC, None), ("Shared-identity overlay", p7, P7, cmc)]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', f'<text x="32" y="31" font-family="Arial" font-size="22" font-weight="700" fill="{INK}">Same canonical substrate, different catalyst-relative occupancy</text>', f'<text x="32" y="55" font-family="Arial" font-size="12" fill="{MUTED}">{html.escape(pair["canonical_overlap_group"])}</text>']
    def draw_field(x0, array, color, opacity_scale=0.82):
        a = normalized(array)
        scaled = np.sqrt(a / max(float(a.max()), 1e-15))
        cell_w, cell_h = plot_w / a.shape[1], plot_h / a.shape[0]
        chunks = []
        for iz in range(a.shape[0]):
            for ir in range(a.shape[1]):
                opacity = float(scaled[iz, ir]) * opacity_scale
                if opacity < 0.025:
                    continue
                x = x0 + ir * cell_w
                y = top + (a.shape[0] - 1 - iz) * cell_h
                chunks.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_w + .25:.2f}" height="{cell_h + .25:.2f}" fill="{color}" opacity="{opacity:.3f}"/>')
        return "".join(chunks)
    for index, (title, array, color, companion) in enumerate(panels):
        x0 = origins[index]
        out.append(f'<text x="{x0}" y="75" font-family="Arial" font-size="14" font-weight="700" fill="{color if companion is None else INK}">{title}</text>')
        out.append(f'<rect x="{x0}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fbfcfd" stroke="{GRID}"/>')
        out.append(draw_field(x0, array, color, 0.82 if companion is None else 0.56))
        if companion is not None:
            out.append(draw_field(x0, companion, CMC, 0.56))
        for tick, rho in enumerate((0, 2, 4, 6, 8, 10)):
            x = x0 + rho / 10 * plot_w
            out.append(f'<line x1="{x:.1f}" y1="{top+plot_h}" x2="{x:.1f}" y2="{top+plot_h+5}" stroke="{MUTED}"/><text x="{x:.1f}" y="{top+plot_h+19}" font-family="Arial" font-size="10" text-anchor="middle" fill="{MUTED}">{rho}</text>')
        for z in (-8, -4, 0, 4, 8, 12):
            y = top + plot_h - (z + 8) / 20 * plot_h
            out.append(f'<line x1="{x0-5}" y1="{y:.1f}" x2="{x0}" y2="{y:.1f}" stroke="{MUTED}"/><text x="{x0-9}" y="{y+3:.1f}" font-family="Arial" font-size="10" text-anchor="end" fill="{MUTED}">{z}</text>')
        out.append(f'<text x="{x0+plot_w/2:.1f}" y="{height-13}" font-family="Arial" font-size="11" text-anchor="middle" fill="{MUTED}">radial ρ (Å)</text>')
        out.append(f'<text x="{x0-38}" y="{top+plot_h/2:.1f}" font-family="Arial" font-size="11" text-anchor="middle" fill="{MUTED}" transform="rotate(-90 {x0-38} {top+plot_h/2:.1f})">axial z (Å)</text>')
    out.append(f'<rect x="940" y="89" width="11" height="11" fill="{P7}" opacity=".72"/><text x="956" y="99" font-family="Arial" font-size="10" fill="{MUTED}">P7</text><rect x="1000" y="89" width="11" height="11" fill="{CMC}" opacity=".72"/><text x="1016" y="99" font-family="Arial" font-size="10" fill="{MUTED}">CMC-Por</text>')
    out.append(f'<text x="1180" y="55" font-family="Arial" font-size="11" text-anchor="end" fill="{MUTED}">JS divergence {values["jensen_shannon_bits"]:.4f} bits · TV distance {values["total_variation_distance"]:.4f}</text>')
    out.append('</svg>')
    return "".join(out)


def main() -> None:
    with (PACKAGE / "shared_overlay_manifest.csv").open(newline="") as handle:
        pairs = list(csv.DictReader(handle))
    ranked = []
    for pair in pairs:
        folder = PACKAGE / pair["pair_directory"]
        p7 = np.load(folder / pair["p7_npz"])[FIELD]
        cmc = np.load(folder / pair["cmcpor_npz"])[FIELD]
        row = {**pair, **metrics(p7, cmc)}
        ranked.append(row)
    ranked.sort(key=lambda row: row["jensen_shannon_bits"], reverse=True)
    selected = ranked[0]
    folder = PACKAGE / selected["pair_directory"]
    p7_npz = np.load(folder / selected["p7_npz"])
    cmc_npz = np.load(folder / selected["cmcpor_npz"])
    p7_aligned = folder / selected["p7_xyz"].replace("_all_200.xyz", "_all_200_aligned_catalyst_frame.xyz")
    cmc_aligned = folder / selected["cmcpor_xyz"].replace("_all_200.xyz", "_all_200_aligned_catalyst_frame.xyz")
    alignment = json.loads((folder / "alignment.json").read_text())
    # The catalyst-bound nitrene N is the first substrate atom in both
    # assemblies.  Use the recorded atom index rather than a motion threshold:
    # the nitrene N is an alignment pivot and is therefore nearly stationary.
    p7_substrate_start = int(alignment["p7_atom_indices_zero_based"]["nitrene_N"])
    cmc_substrate_start = int(alignment["cmcpor_atom_indices_zero_based"]["nitrene_N"])
    selected.update({
        "selection_rule": f"largest Jensen-Shannon divergence among the 13 shared canonical identities for {FIELD}",
        "occupancy_field": FIELD,
        "p7_aligned_xyz": str(p7_aligned.relative_to(PACKAGE)),
        "cmcpor_aligned_xyz": str(cmc_aligned.relative_to(PACKAGE)),
        "p7_catalyst_atom_count": p7_substrate_start,
        "cmcpor_catalyst_atom_count": cmc_substrate_start,
        "substrate_boundary_rule": "the recorded catalyst-bound nitrene N is the first substrate atom",
        "pose_count_per_environment": 200,
        "p7_cylindrical_moments": cylindrical_moments(p7_npz[FIELD]),
        "cmcpor_cylindrical_moments": cylindrical_moments(cmc_npz[FIELD]),
    })
    overlay_name = "shared_identity_occupancy_overlay.svg"
    (folder / overlay_name).write_text(field_svg(selected, p7_npz[FIELD], cmc_npz[FIELD], selected), encoding="utf-8")
    p7_cube = folder / f"{Path(selected['p7_npz']).stem}_nitrene_all_heavy_all200.cube"
    cmc_cube = folder / f"{Path(selected['cmcpor_npz']).stem}_nitrene_all_heavy_all200.cube"
    write_cube(p7_cube, p7_npz[FIELD])
    write_cube(cmc_cube, cmc_npz[FIELD])
    selected["prepared_overlay_svg"] = str((folder / overlay_name).relative_to(PACKAGE))
    selected["p7_all200_cube"] = str(p7_cube.relative_to(PACKAGE))
    selected["cmcpor_all200_cube"] = str(cmc_cube.relative_to(PACKAGE))
    (PACKAGE / "figure2c_selected_pair_analysis.json").write_text(json.dumps(selected, indent=2) + "\n")
    fields = ["rank", "overlay_index", "canonical_overlap_group", "p7_substrate_id", "cmcpor_substrate_id", "jensen_shannon_bits", "total_variation_distance", "bhattacharyya_overlap"]
    with (PACKAGE / "figure2c_shared_pair_ranking.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, row in enumerate(ranked, 1):
            writer.writerow({"rank": rank, **{field: row[field] for field in fields if field != "rank"}})
    print(json.dumps(selected, indent=2))


if __name__ == "__main__":
    main()

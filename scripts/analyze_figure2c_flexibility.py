#!/usr/bin/env python3
"""Compare catalyst-relative spread and internal flexibility for Figure 2C."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "output/figures/figure2c_data"
PAIR = PACKAGE / "shared_overlays/05_1i__2r"


def read_xyz_frames(path: Path) -> tuple[list[str], np.ndarray]:
    lines = path.read_text(encoding="utf-8").splitlines()
    frames: list[np.ndarray] = []
    symbols: list[str] | None = None
    cursor = 0
    while cursor < len(lines):
        count = int(lines[cursor])
        atom_lines = lines[cursor + 2 : cursor + 2 + count]
        current_symbols = [line.split()[0] for line in atom_lines]
        coordinates = np.asarray([[float(line.split()[i]) for i in (1, 2, 3)] for line in atom_lines], dtype=float)
        if symbols is None:
            symbols = current_symbols
        elif current_symbols != symbols:
            raise ValueError(f"Atom ordering changed in {path}")
        frames.append(coordinates)
        cursor += count + 2
    assert symbols is not None
    return symbols, np.stack(frames)


def kabsch_rmsd(left: np.ndarray, right: np.ndarray) -> float:
    left_centered = left - left.mean(axis=0)
    right_centered = right - right.mean(axis=0)
    u, _, vt = np.linalg.svd(left_centered.T @ right_centered)
    correction = np.eye(3)
    correction[-1, -1] = np.sign(np.linalg.det(u @ vt))
    rotation = u @ correction @ vt
    residual = left_centered @ rotation - right_centered
    return float(np.sqrt(np.mean(np.sum(residual * residual, axis=1))))


def summarize(values: np.ndarray) -> dict[str, float]:
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "sd": float(np.std(values)),
        "p95": float(np.percentile(values, 95)),
        "maximum": float(np.max(values)),
    }


def metrics(frames: np.ndarray, symbols: list[str], substrate_start: int) -> dict:
    substrate = frames[:, substrate_start:, :]
    substrate_symbols = symbols[substrate_start:]
    heavy_indices = [index for index, symbol in enumerate(substrate_symbols) if symbol != "H"]
    heavy = substrate[:, heavy_indices, :]

    pairwise_rmsd = []
    for left in range(len(heavy)):
        for right in range(left + 1, len(heavy)):
            pairwise_rmsd.append(kabsch_rmsd(heavy[left], heavy[right]))

    pair_indices = np.triu_indices(heavy.shape[1], 1)
    distance_vectors = []
    for frame in heavy:
        distances = np.linalg.norm(frame[:, None, :] - frame[None, :, :], axis=2)
        distance_vectors.append(distances[pair_indices])
    distance_vectors = np.asarray(distance_vectors)
    mean_distance_vector = distance_vectors.mean(axis=0)
    distance_matrix_rmsd = np.sqrt(np.mean((distance_vectors - mean_distance_vector) ** 2, axis=1))

    centered = heavy - heavy.mean(axis=1, keepdims=True)
    radius_gyration = np.sqrt(np.mean(np.sum(centered * centered, axis=2), axis=1))

    centers = heavy.mean(axis=1)
    center_covariance = np.cov(centers, rowvar=False, ddof=0)
    center_axis_sd = np.sqrt(np.maximum(np.linalg.eigvalsh(center_covariance), 0))[::-1]
    catalyst_relative_atom_rmsf = np.sqrt(np.mean(np.sum((heavy - heavy.mean(axis=0)) ** 2, axis=2), axis=0))

    return {
        "frames": int(heavy.shape[0]),
        "heavy_atoms": int(heavy.shape[1]),
        "pairwise_internal_heavy_atom_rmsd_angstrom": summarize(np.asarray(pairwise_rmsd)),
        "internal_pair_distance_rmsd_angstrom": summarize(distance_matrix_rmsd),
        "radius_of_gyration_angstrom": summarize(radius_gyration),
        "catalyst_relative_center_axis_sd_angstrom": [float(value) for value in center_axis_sd],
        "catalyst_relative_center_total_rms_angstrom": float(np.sqrt(np.trace(center_covariance))),
        "catalyst_relative_heavy_atom_rmsf_angstrom": summarize(catalyst_relative_atom_rmsf),
    }


def main() -> None:
    alignment = json.loads((PAIR / "alignment.json").read_text(encoding="utf-8"))
    p7_symbols, p7_frames = read_xyz_frames(PAIR / "fe_p7cl_1i_all_200_aligned_catalyst_frame.xyz")
    cmc_symbols, cmc_frames = read_xyz_frames(PAIR / "fe_cmcporcl_2r_all_200_aligned_catalyst_frame.xyz")
    p7 = metrics(p7_frames, p7_symbols, int(alignment["p7_atom_indices_zero_based"]["nitrene_N"]))
    cmc = metrics(cmc_frames, cmc_symbols, int(alignment["cmcpor_atom_indices_zero_based"]["nitrene_N"]))
    report = {
        "pair": {"fe_p7cl": "1i", "fe_cmcporcl": "2r"},
        "scope": "descriptive comparison of these two 200-pose ensembles only",
        "fe_p7cl": p7,
        "fe_cmcporcl": cmc,
        "cmc_to_p7_ratios": {
            "mean_pairwise_internal_rmsd": cmc["pairwise_internal_heavy_atom_rmsd_angstrom"]["mean"] / p7["pairwise_internal_heavy_atom_rmsd_angstrom"]["mean"],
            "mean_internal_pair_distance_rmsd": cmc["internal_pair_distance_rmsd_angstrom"]["mean"] / p7["internal_pair_distance_rmsd_angstrom"]["mean"],
            "radius_of_gyration_sd": cmc["radius_of_gyration_angstrom"]["sd"] / p7["radius_of_gyration_angstrom"]["sd"],
            "catalyst_relative_center_total_rms": cmc["catalyst_relative_center_total_rms_angstrom"] / p7["catalyst_relative_center_total_rms_angstrom"],
            "mean_catalyst_relative_atom_rmsf": cmc["catalyst_relative_heavy_atom_rmsf_angstrom"]["mean"] / p7["catalyst_relative_heavy_atom_rmsf_angstrom"]["mean"],
        },
    }
    output = PACKAGE / "figure2c_flexibility_analysis.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

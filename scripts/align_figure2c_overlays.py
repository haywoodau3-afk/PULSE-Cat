#!/usr/bin/env python3
"""Align shared Figure 2C pose ensembles in a common catalyst frame.

The four porphyrin N atoms and Fe define the primary rigid-body fit.  The
substrate nitrene N is included with a lower weight to resolve the otherwise
ambiguous in-plane orientation without allowing the substrate to override the
catalyst-core superposition.
"""

from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "output" / "figures" / "figure2c_data"
CATALYST_WEIGHT = 8.0
NITRENE_WEIGHT = 1.0


def read_xyz(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    frames = []
    cursor = 0
    while cursor < len(lines):
        count = int(lines[cursor].strip())
        comment = lines[cursor + 1]
        symbols = []
        coords = []
        for line in lines[cursor + 2 : cursor + 2 + count]:
            fields = line.split()
            symbols.append(fields[0])
            coords.append([float(value) for value in fields[1:4]])
        frames.append((symbols, np.asarray(coords, dtype=float), comment))
        cursor += count + 2
    if not frames:
        raise ValueError(f"no XYZ frames found in {path}")
    return frames


def catalyst_anchors(frame):
    symbols, coords, _ = frame
    fe_candidates = [i for i, symbol in enumerate(symbols) if symbol.lower() == "fe"]
    if len(fe_candidates) != 1:
        raise ValueError(f"expected one Fe atom, found {len(fe_candidates)}")
    fe = fe_candidates[0]
    nitrogen = [i for i, symbol in enumerate(symbols) if symbol == "N"]
    distances = sorted((np.linalg.norm(coords[i] - coords[fe]), i) for i in nitrogen)
    # The closest N is the substrate nitrene N; the next four are the
    # porphyrin N atoms coordinating Fe in these assemblies.
    nitrene = distances[0][1]
    porphyrin = [i for _, i in distances[1:5]]
    return fe, porphyrin, nitrene, [distances[j][0] for j in range(5)]


def fit_transform(source, target, weights):
    source_center = np.average(source, axis=0, weights=weights)
    target_center = np.average(target, axis=0, weights=weights)
    source_centered = source - source_center
    target_centered = target - target_center
    rotation, _ = Rotation.align_vectors(target_centered, source_centered, weights=weights)
    translation = target_center - rotation.apply(source_center)
    transformed = rotation.apply(source) + translation
    rmsd = float(np.sqrt(np.average(np.sum((transformed - target) ** 2, axis=1), weights=weights)))
    return rotation, translation, rmsd


def apply_transform(coords, rotation, translation):
    return rotation.apply(coords) + translation


def stabilize_frames(frames, anchor_indices):
    fe, porphyrin, nitrene, _ = anchor_indices
    indices = [fe, *porphyrin, nitrene]
    weights = np.asarray([CATALYST_WEIGHT] * 5 + [NITRENE_WEIGHT])
    reference = frames[0][1][indices]
    stabilized = []
    for symbols, coords, comment in frames:
        rotation, translation, _ = fit_transform(coords[indices], reference, weights)
        stabilized.append((symbols, apply_transform(coords, rotation, translation), comment))
    return stabilized


def cross_align(p7_frames, cmc_frames, p7_anchors, cmc_anchors):
    p7_fe, p7_por, p7_nitrene, _ = p7_anchors
    cmc_fe, cmc_por, cmc_nitrene, _ = cmc_anchors
    p7_indices = [p7_fe, *p7_por, p7_nitrene]
    weights = np.asarray([CATALYST_WEIGHT] * 5 + [NITRENE_WEIGHT])
    source = p7_frames[0][1][p7_indices]
    cmc_coords = cmc_frames[0][1]
    best = None
    for permutation in itertools.permutations(cmc_por):
        target = cmc_coords[[cmc_fe, *permutation, cmc_nitrene]]
        rotation, translation, rmsd = fit_transform(source, target, weights)
        if best is None or rmsd < best[0]:
            best = (rmsd, rotation, translation, permutation)
    rmsd, rotation, translation, permutation = best
    transformed = [
        (symbols, apply_transform(coords, rotation, translation), comment)
        for symbols, coords, comment in p7_frames
    ]
    return transformed, rmsd, permutation


def write_xyz(path: Path, frames, alignment_label):
    with path.open("w", encoding="utf-8") as handle:
        for symbols, coords, comment in frames:
            handle.write(f"{len(symbols)}\n")
            handle.write(f"{comment} alignment={alignment_label}\n")
            for symbol, xyz in zip(symbols, coords):
                handle.write(f"{symbol:<2s} {xyz[0]: .8f} {xyz[1]: .8f} {xyz[2]: .8f}\n")


def main():
    aligned_count = 0
    with (PACKAGE / "shared_overlay_manifest.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pair_dir = PACKAGE / row["pair_directory"]
            p7_path = pair_dir / row["p7_xyz"]
            cmc_path = pair_dir / row["cmcpor_xyz"]
            p7_frames = read_xyz(p7_path)
            cmc_frames = read_xyz(cmc_path)
            p7_anchors = catalyst_anchors(p7_frames[0])
            cmc_anchors = catalyst_anchors(cmc_frames[0])
            p7_stable = stabilize_frames(p7_frames, p7_anchors)
            cmc_stable = stabilize_frames(cmc_frames, cmc_anchors)
            p7_aligned, cross_rmsd, cmc_permutation = cross_align(
                p7_stable, cmc_stable, p7_anchors, cmc_anchors
            )

            p7_out = pair_dir / p7_path.name.replace("_all_200.xyz", "_all_200_aligned_catalyst_frame.xyz")
            cmc_out = pair_dir / cmc_path.name.replace("_all_200.xyz", "_all_200_aligned_catalyst_frame.xyz")
            write_xyz(p7_out, p7_aligned, "Fe+4porphyrin-N+nitrene-pivot")
            write_xyz(cmc_out, cmc_stable, "Fe+4porphyrin-N+nitrene-pivot")

            alignment = {
                "method": "weighted rigid-body Kabsch alignment",
                "primary_pivots": "Fe plus four porphyrin-coordinating N atoms",
                "secondary_pivot": "substrate nitrene N, lower weight to resolve in-plane orientation",
                "weights": {"Fe_and_por_N": CATALYST_WEIGHT, "nitrene_N": NITRENE_WEIGHT},
                "p7_atom_indices_zero_based": {"Fe": p7_anchors[0], "porphyrin_N": p7_anchors[1], "nitrene_N": p7_anchors[2]},
                "cmcpor_atom_indices_zero_based": {"Fe": cmc_anchors[0], "porphyrin_N": cmc_anchors[1], "nitrene_N": cmc_anchors[2]},
                "cmcpor_target_N_permutation_zero_based": list(cmc_permutation),
                "cross_system_weighted_rmsd_angstrom": cross_rmsd,
                "interpretation": "Catalyst cores are superposed; substrate differences are retained and must not be read as transition-state assignments.",
            }
            (pair_dir / "alignment.json").write_text(json.dumps(alignment, indent=2) + "\n", encoding="utf-8")
            aligned_count += 1
            print(row["pair_directory"], f"rmsd={cross_rmsd:.4f} A")
    print(f"aligned {aligned_count} shared pairs")


if __name__ == "__main__":
    main()

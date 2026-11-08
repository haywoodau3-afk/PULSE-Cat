#!/usr/bin/env python3
"""Validate that Figure 2C compares the same substrate in both catalysts."""

from __future__ import annotations

import collections
import csv
import json
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdDetermineBonds


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "output/figures/figure2c_data"


def read_xyz_frames(path: Path) -> list[list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    frames: list[list[str]] = []
    cursor = 0
    while cursor < len(lines):
        atom_count = int(lines[cursor])
        frames.append(lines[cursor + 2 : cursor + 2 + atom_count])
        cursor += atom_count + 2
    return frames


def topology_smiles(atom_lines: list[str]) -> str:
    xyz = "\n".join((str(len(atom_lines)), "substrate", *atom_lines)) + "\n"
    molecule = Chem.MolFromXYZBlock(xyz)
    if molecule is None:
        raise AssertionError("RDKit could not parse substrate XYZ block")
    rdDetermineBonds.DetermineConnectivity(molecule)
    return Chem.MolToSmiles(molecule, canonical=True)


def element_counts(atom_lines: list[str]) -> dict[str, int]:
    return dict(sorted(collections.Counter(line.split()[0] for line in atom_lines).items()))


def validate_pair(row: dict[str, str], *, all_frames: bool = False) -> dict:
    folder = PACKAGE / row["pair_directory"]
    alignment = json.loads((folder / "alignment.json").read_text(encoding="utf-8"))
    p7_start = int(alignment["p7_atom_indices_zero_based"]["nitrene_N"])
    cmc_start = int(alignment["cmcpor_atom_indices_zero_based"]["nitrene_N"])
    p7_name = row["p7_xyz"].replace("_all_200.xyz", "_all_200_aligned_catalyst_frame.xyz")
    cmc_name = row["cmcpor_xyz"].replace("_all_200.xyz", "_all_200_aligned_catalyst_frame.xyz")
    p7_frames = read_xyz_frames(folder / p7_name)
    cmc_frames = read_xyz_frames(folder / cmc_name)
    if len(p7_frames) != len(cmc_frames):
        raise AssertionError(f"{row['p7_substrate_id']}/{row['cmcpor_substrate_id']}: unequal frame counts")

    indices = range(len(p7_frames)) if all_frames else (0,)
    p7_reference = topology_smiles(p7_frames[0][p7_start:])
    cmc_reference = topology_smiles(cmc_frames[0][cmc_start:])
    p7_counts = element_counts(p7_frames[0][p7_start:])
    cmc_counts = element_counts(cmc_frames[0][cmc_start:])
    if p7_counts != cmc_counts:
        raise AssertionError(f"{row['p7_substrate_id']}/{row['cmcpor_substrate_id']}: formulas differ: {p7_counts} != {cmc_counts}")
    if p7_reference != cmc_reference:
        raise AssertionError(f"{row['p7_substrate_id']}/{row['cmcpor_substrate_id']}: connectivity differs: {p7_reference} != {cmc_reference}")

    for frame_index in indices:
        p7_atoms = p7_frames[frame_index][p7_start:]
        cmc_atoms = cmc_frames[frame_index][cmc_start:]
        if element_counts(p7_atoms) != p7_counts or topology_smiles(p7_atoms) != p7_reference:
            raise AssertionError(f"P7 {row['p7_substrate_id']} frame {frame_index + 1}: substrate identity changed")
        if element_counts(cmc_atoms) != cmc_counts or topology_smiles(cmc_atoms) != cmc_reference:
            raise AssertionError(f"CMC-Por {row['cmcpor_substrate_id']} frame {frame_index + 1}: substrate identity changed")

    return {
        "overlay_index": int(row["overlay_index"]),
        "p7_substrate_id": row["p7_substrate_id"],
        "cmcpor_substrate_id": row["cmcpor_substrate_id"],
        "canonical_substrate": row["canonical_overlap_group"],
        "substrate_element_counts_after_n2_loss": p7_counts,
        "connectivity_signature": p7_reference,
        "frames_checked_per_catalyst": len(p7_frames) if all_frames else 1,
        "exact_connectivity_match": True,
    }


def main() -> None:
    with (PACKAGE / "shared_overlay_manifest.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    results = []
    for row in rows:
        selected = row["p7_substrate_id"] == "1i" and row["cmcpor_substrate_id"] == "2r"
        results.append(validate_pair(row, all_frames=selected))
    report = {
        "validation_method": "RDKit distance-derived connectivity from catalyst-stripped XYZ; mutual comparison of canonical topology and explicit element counts",
        "all_shared_pairs_exact_connectivity_matches": all(item["exact_connectivity_match"] for item in results),
        "selected_pair": next(item for item in results if item["p7_substrate_id"] == "1i"),
        "pairs": results,
    }
    output = PACKAGE / "figure2c_substrate_identity_validation.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["selected_pair"], indent=2))
    print(f"PASS: {len(results)} shared pairs match; selected pair checked across 200 + 200 frames")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Extract local 3D shell descriptors around Stage 3a chemical centers."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import numpy


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CENTERS = ROOT / "data/jacs_2025/stage3/features/local-3d-shell-centers.jsonl"
DEFAULT_OUTPUT = ROOT / "data/jacs_2025/stage3/features/local-3d-shell-features.jsonl"
SHELLS = [
    ("0_3_angstrom", 0.0, 3.0),
    ("3_4_angstrom", 3.0, 4.0),
    ("4_5_angstrom", 4.0, 5.0),
    ("5_6_angstrom", 5.0, 6.0),
    ("6_8_angstrom", 6.0, 8.0),
]
EXPECTED_CENTERS = ["nitrene_center", "candidate_c_h_haa_center", "reactive_approach_midpoint"]
HETERO_ELEMENTS = {"B", "N", "O", "F", "P", "S", "Cl", "Br", "I"}


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def parse_xyz(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    expected_count = int(lines[0])
    atoms = []
    for line_number, line in enumerate(lines[2:], start=3):
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"{path}:{line_number}: expected XYZ row with element and three coordinates")
        element, x, y, z = parts
        atoms.append(
            {
                "index_one_based": len(atoms) + 1,
                "element": element,
                "xyz": numpy.array([float(x), float(y), float(z)], dtype=float),
            }
        )
    if len(atoms) != expected_count:
        raise ValueError(f"{path}: expected {expected_count} atoms, parsed {len(atoms)}")
    return atoms


def distance(left: numpy.ndarray, right: numpy.ndarray) -> float:
    return float(numpy.linalg.norm(left - right))


def quantile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    sorted_values = sorted(values)
    position = fraction * (len(sorted_values) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    lower = sorted_values[lower_index]
    upper = sorted_values[upper_index]
    return lower + (upper - lower) * (position - lower_index)


def center_xyz(center: dict[str, Any]) -> numpy.ndarray:
    xyz = center.get("xyz")
    if not (isinstance(xyz, list) and len(xyz) == 3):
        raise ValueError("Center must define xyz as a three-value list")
    return numpy.array([float(value) for value in xyz], dtype=float)


def atom_ownership_map(row: dict[str, Any]) -> dict[int, str]:
    ownership = {}
    for entry in row.get("atom_ownership", []):
        ownership[int(entry["index_one_based"])] = entry["owner"]
    return ownership


def shell_features(
    atoms: list[dict[str, Any]],
    origin: numpy.ndarray,
    lower: float,
    upper: float,
    ownership: dict[int, str],
    prefix: str,
) -> dict[str, Any]:
    members = []
    for atom in atoms:
        value = distance(origin, atom["xyz"])
        if lower <= value < upper:
            members.append((atom, value))

    distances = [value for _, value in members]
    features: dict[str, Any] = {
        f"{prefix}_atom_count": len(members),
        f"{prefix}_distance_min": min(distances) if distances else None,
        f"{prefix}_distance_mean": mean(distances) if distances else None,
        f"{prefix}_distance_q25": quantile(distances, 0.25),
        f"{prefix}_distance_median": quantile(distances, 0.50),
        f"{prefix}_distance_q75": quantile(distances, 0.75),
        f"{prefix}_distance_max": max(distances) if distances else None,
        f"{prefix}_hetero_atom_count": sum(1 for atom, _ in members if atom["element"] in HETERO_ELEMENTS),
        f"{prefix}_aromatic_proxy_atom_count": sum(1 for atom, _ in members if atom["element"] == "C"),
    }
    nearest = min(members, key=lambda item: item[1]) if members else None
    features[f"{prefix}_nearest_atom_index_one_based"] = nearest[0]["index_one_based"] if nearest else None
    features[f"{prefix}_nearest_atom_element"] = nearest[0]["element"] if nearest else None
    features[f"{prefix}_nearest_atom_owner"] = ownership.get(nearest[0]["index_one_based"], "unknown") if nearest else None

    for element in ["H", "C", "N", "O", "F", "P", "S", "Cl", "Fe"]:
        features[f"{prefix}_element_{element.lower()}_count"] = sum(1 for atom, _ in members if atom["element"] == element)
    for owner in ["core", "ligand", "substrate", "unknown"]:
        features[f"{prefix}_owner_{owner}_count"] = sum(
            1 for atom, _ in members if ownership.get(atom["index_one_based"], "unknown") == owner
        )
    return features


def extract_row(row: dict[str, Any]) -> dict[str, Any]:
    geometry_path = resolve_path(row["geometry_path"])
    atoms = parse_xyz(geometry_path)
    ownership = atom_ownership_map(row)
    centers = row.get("centers", {})
    missing = [center for center in EXPECTED_CENTERS if center not in centers]
    if missing:
        raise ValueError(f"{row.get('pose_id')}: missing shell centers: {', '.join(missing)}")

    features: dict[str, Any] = {}
    for center_id in EXPECTED_CENTERS:
        origin = center_xyz(centers[center_id])
        for shell_id, lower, upper in SHELLS:
            prefix = f"{center_id}.{shell_id}"
            features.update(shell_features(atoms, origin, lower, upper, ownership, prefix))

    return {
        "schema_version": "stage3a-local-3d-shell-features-v1",
        "substrate_id": row["substrate_id"],
        "pose_id": row["pose_id"],
        "candidate_site_id": row["candidate_site_id"],
        "feature_status": "computed_from_xyz_shell_centers",
        "feature_blocks": {"local_3d_shell_features": features},
        "provenance": {
            "geometry_path": display_path(geometry_path),
            "center_source": row.get("center_source", "provided_center_coordinates"),
            "shell_ids": [shell[0] for shell in SHELLS],
            "centers": EXPECTED_CENTERS,
        },
    }


def extract_features(center_rows_path: Path) -> list[dict[str, Any]]:
    return [extract_row(row) for row in read_jsonl(center_rows_path)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--centers", type=Path, default=DEFAULT_CENTERS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = extract_features(args.centers)
    write_jsonl(args.output, rows)
    print(f"Wrote Stage 3a local 3D shell features for {len(rows)} rows to {display_path(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

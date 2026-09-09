#!/usr/bin/env python3
"""Generate Stage 2 per-pose substrate-catalyst interaction features."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import numpy
from rdkit import Chem


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_REPORT_DIR = ROOT / "data/jacs_2025/stage1/panel"
DEFAULT_OUTPUT = ROOT / "data/jacs_2025/stage2/features/pose-interaction.jsonl"
FE_ATOM_INDEX_ONE_BASED = 47
CL_ATOM_INDEX_ONE_BASED = 48
CONTACT_BINS = [(0.0, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0), (3.0, 4.0)]
COVALENT_RADII_ANGSTROM = {
    "H": 0.31,
    "B": 0.85,
    "C": 0.76,
    "N": 0.71,
    "O": 0.66,
    "F": 0.57,
    "Si": 1.11,
    "P": 1.07,
    "S": 1.05,
    "Cl": 1.02,
    "Fe": 1.32,
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def parse_xyz(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    expected_count = int(lines[0])
    atoms = []
    for line_number, line in enumerate(lines[2:], start=3):
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"{path}:{line_number}: expected XYZ atom row")
        element, x, y, z = parts
        atoms.append({"element": element, "xyz": numpy.array([float(x), float(y), float(z)], dtype=float)})
    if len(atoms) != expected_count:
        raise ValueError(f"{path}: expected {expected_count} atoms, parsed {len(atoms)}")
    return atoms


def distance(left: numpy.ndarray, right: numpy.ndarray) -> float:
    return float(numpy.linalg.norm(left - right))


def angle_degrees(left: numpy.ndarray, vertex: numpy.ndarray, right: numpy.ndarray) -> float | None:
    left_vector = left - vertex
    right_vector = right - vertex
    denominator = numpy.linalg.norm(left_vector) * numpy.linalg.norm(right_vector)
    if denominator == 0:
        return None
    cosine = float(numpy.dot(left_vector, right_vector) / denominator)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def centroid(points: list[numpy.ndarray]) -> numpy.ndarray:
    return numpy.mean(numpy.array(points), axis=0)


def signed_plane_distance(point: numpy.ndarray, plane_points: list[numpy.ndarray]) -> float:
    matrix = numpy.array(plane_points)
    center = matrix.mean(axis=0)
    _, _, vh = numpy.linalg.svd(matrix - center)
    normal = vh[-1]
    return float(numpy.dot(point - center, normal))


def rounded(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(value, digits)


def mapped_nitrene_molecule(mapped_substrate_smiles: str) -> Chem.Mol:
    molecule = Chem.MolFromSmiles(mapped_substrate_smiles, sanitize=True)
    if molecule is None:
        raise ValueError("mapped substrate SMILES does not parse")
    editable = Chem.RWMol(molecule)
    # The aryl azides are C-N=N=N, while the sulfonyl azides are
    # S-N=N=N. Looking only for N atoms without a carbon neighbor therefore
    # incorrectly finds all three nitrogens in the sulfonyl pathway. Identify
    # the proximal azide N by its non-N substrate neighbour, then remove the
    # central and terminal N atoms from the three-membered N chain.
    proximal_candidates = []
    for atom in molecule.GetAtoms():
        if atom.GetSymbol() != "N":
            continue
        n_neighbors = [neighbor for neighbor in atom.GetNeighbors() if neighbor.GetSymbol() == "N"]
        non_n_neighbors = [neighbor for neighbor in atom.GetNeighbors() if neighbor.GetSymbol() != "N"]
        if len(n_neighbors) == 1 and non_n_neighbors:
            proximal_candidates.append((atom, n_neighbors[0]))
    if len(proximal_candidates) != 1:
        raise ValueError("mapped substrate must contain one proximal azide nitrogen")
    proximal, central = proximal_candidates[0]
    terminal_neighbors = [neighbor for neighbor in central.GetNeighbors() if neighbor.GetIdx() != proximal.GetIdx() and neighbor.GetSymbol() == "N"]
    if len(terminal_neighbors) != 1:
        raise ValueError("mapped substrate must contain a three-nitrogen azide chain")
    for atom_index in sorted((central.GetIdx(), terminal_neighbors[0].GetIdx()), reverse=True):
        editable.RemoveAtom(atom_index)
    nitrene = editable.GetMol()
    Chem.SanitizeMol(nitrene)
    return nitrene


def stage1_pose_molecule(input_nitrene_smiles: str) -> Chem.Mol:
    molecule = Chem.MolFromSmiles(input_nitrene_smiles, sanitize=True)
    if molecule is None:
        raise ValueError(f"Stage 1 nitrene SMILES does not parse: {input_nitrene_smiles}")
    return Chem.AddHs(molecule)


def map_ids_to_stage1_atom_indices(record: dict[str, Any], posed_molecule: Chem.Mol) -> dict[int, int]:
    query = mapped_nitrene_molecule(record["structure"]["atom_mapped_substrate_smiles"])
    match_query = Chem.Mol(query)
    for atom in match_query.GetAtoms():
        atom.SetAtomMapNum(0)
    heavy_posed = Chem.RemoveHs(posed_molecule)
    match = heavy_posed.GetSubstructMatch(match_query)
    if not match:
        raise ValueError(f"{record['substrate_id']}: mapped Stage 2 nitrene does not match Stage 1 posed molecule")
    atom_map_to_stage1_index = {}
    for query_atom in query.GetAtoms():
        atom_map_id = query_atom.GetAtomMapNum()
        if atom_map_id:
            atom_map_to_stage1_index[atom_map_id] = match[query_atom.GetIdx()]
    return atom_map_to_stage1_index


def ordered_substrate_indices(posed_molecule: Chem.Mol) -> list[int]:
    nitrene_atoms = [
        atom
        for atom in posed_molecule.GetAtoms()
        if atom.GetSymbol() == "N" and atom.GetDegree() == 1 and atom.GetFormalCharge() == 0
    ]
    if len(nitrene_atoms) != 1:
        raise ValueError(f"Expected one substrate-bound nitrene N, found {len(nitrene_atoms)}")
    nitrene_atom = nitrene_atoms[0]
    neighbor = nitrene_atom.GetNeighbors()[0]
    priority = {nitrene_atom.GetIdx(), neighbor.GetIdx()}
    return [nitrene_atom.GetIdx(), neighbor.GetIdx()] + [
        atom.GetIdx() for atom in posed_molecule.GetAtoms() if atom.GetIdx() not in priority
    ]


def stage1_index_to_assembly_index(posed_molecule: Chem.Mol, frozen_core_atom_count: int) -> dict[int, int]:
    ordered_indices = ordered_substrate_indices(posed_molecule)
    return {
        stage1_index: frozen_core_atom_count + ordered_position
        for ordered_position, stage1_index in enumerate(ordered_indices)
    }


def nearest_reported_hydrogen_index(posed_molecule: Chem.Mol, reported_stage1_index: int, assembly_atoms: list[dict[str, Any]], index_map: dict[int, int]) -> int:
    reported_atom = posed_molecule.GetAtomWithIdx(reported_stage1_index)
    hydrogen_indices = [neighbor.GetIdx() for neighbor in reported_atom.GetNeighbors() if neighbor.GetSymbol() == "H"]
    if not hydrogen_indices:
        raise ValueError("Reported reactive atom has no explicit hydrogen in Stage 1 pose molecule")
    nitrene_xyz = assembly_atoms[index_map[0]]["xyz"]
    return min(hydrogen_indices, key=lambda hydrogen_index: distance(nitrene_xyz, assembly_atoms[index_map[hydrogen_index]]["xyz"]))


def bin_counts(distances: list[float], prefix: str) -> dict[str, int]:
    counts = {}
    for lower, upper in CONTACT_BINS:
        label = f"{str(lower).replace('.', 'p')}_{str(upper).replace('.', 'p')}"
        counts[f"{prefix}_distance_count_{label}_angstrom"] = sum(lower <= value < upper for value in distances)
    counts[f"{prefix}_distance_count_ge_4p0_angstrom"] = sum(value >= 4.0 for value in distances)
    counts[f"{prefix}_distance_count_lt_2p5_angstrom"] = sum(value < 2.5 for value in distances)
    counts[f"{prefix}_distance_count_lt_3p0_angstrom"] = sum(value < 3.0 for value in distances)
    return counts


def covalent_radius(element: str) -> float:
    return COVALENT_RADII_ANGSTROM.get(element, 0.77)


def core_substrate_contacts(
    core_atoms: list[dict[str, Any]],
    substrate_atoms: list[dict[str, Any]],
    fe_atom_index_zero_based: int,
    nitrene_substrate_offset: int,
) -> dict[str, Any]:
    distances = []
    clash_floor_count = 0
    nearest = {"distance": math.inf, "core_index": None, "substrate_index": None, "core_element": None, "substrate_element": None}
    for core_index, core_atom in enumerate(core_atoms):
        for substrate_index, substrate_atom in enumerate(substrate_atoms):
            if core_index == fe_atom_index_zero_based and substrate_index == nitrene_substrate_offset:
                continue
            value = distance(core_atom["xyz"], substrate_atom["xyz"])
            distances.append(value)
            if value < 0.65 * (covalent_radius(core_atom["element"]) + covalent_radius(substrate_atom["element"])):
                clash_floor_count += 1
            if value < nearest["distance"]:
                nearest = {
                    "distance": value,
                    "core_index": core_index + 1,
                    "substrate_index": substrate_index + 1,
                    "core_element": core_atom["element"],
                    "substrate_element": substrate_atom["element"],
                }
    features: dict[str, Any] = {
        "core_substrate_pair_count": len(distances),
        "core_substrate_distance_min": min(distances),
        "core_substrate_distance_mean": mean(distances),
        "core_substrate_distance_max": max(distances),
        "core_substrate_covalent_floor_clash_count": clash_floor_count,
        "nearest_core_substrate_distance": nearest["distance"],
        "nearest_core_substrate_core_index_one_based": nearest["core_index"],
        "nearest_core_substrate_substrate_offset_one_based": nearest["substrate_index"],
        "nearest_core_substrate_core_element": nearest["core_element"],
        "nearest_core_substrate_substrate_element": nearest["substrate_element"],
    }
    features.update(bin_counts(distances, "core_substrate"))
    return features


def point_to_atoms_features(point: numpy.ndarray, atoms: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    distances = [distance(point, atom["xyz"]) for atom in atoms]
    nearest_index = min(range(len(atoms)), key=lambda index: distances[index])
    features: dict[str, Any] = {
        f"{prefix}_to_core_distance_min": distances[nearest_index],
        f"{prefix}_to_core_distance_mean": mean(distances),
        f"{prefix}_to_core_distance_max": max(distances),
        f"{prefix}_nearest_core_index_one_based": nearest_index + 1,
        f"{prefix}_nearest_core_element": atoms[nearest_index]["element"],
    }
    features.update(bin_counts(distances, f"{prefix}_to_core"))
    return features


def porphyrin_nitrogen_atoms(
    core_atoms: list[dict[str, Any]],
    fe_atom_index_one_based: int = FE_ATOM_INDEX_ONE_BASED,
) -> list[dict[str, Any]]:
    fe_xyz = core_atoms[fe_atom_index_one_based - 1]["xyz"]
    nitrogens = [
        atom
        for atom in core_atoms
        if atom["element"] == "N" and distance(atom["xyz"], fe_xyz) > 1.8
    ]
    return sorted(nitrogens, key=lambda atom: distance(atom["xyz"], fe_xyz))[:4]


def build_pose_features(
    pose: dict[str, Any],
    record: dict[str, Any],
    posed_molecule: Chem.Mol,
    atom_map_to_stage1_index: dict[int, int],
    fe_atom_index_one_based: int = FE_ATOM_INDEX_ONE_BASED,
    cl_atom_index_one_based: int = CL_ATOM_INDEX_ONE_BASED,
) -> dict[str, Any]:
    assembly_path = resolve_path(pose["fe_bound_assembly_xyz_path"])
    assembly_atoms = parse_xyz(assembly_path)
    frozen_core_count = int(pose["frozen_core_atom_count"])
    stage1_to_assembly = stage1_index_to_assembly_index(posed_molecule, frozen_core_count)
    reported_map_id = record["reaction_center"]["reported_reactive_site"]["atom_map_id"]
    reported_stage1_index = atom_map_to_stage1_index[reported_map_id]
    transferred_hydrogen_stage1_index = nearest_reported_hydrogen_index(
        posed_molecule,
        reported_stage1_index,
        assembly_atoms,
        stage1_to_assembly,
    )

    fe_xyz = assembly_atoms[fe_atom_index_one_based - 1]["xyz"]
    cl_xyz = assembly_atoms[cl_atom_index_one_based - 1]["xyz"]
    nitrene_xyz = assembly_atoms[stage1_to_assembly[0]]["xyz"]
    reported_c_xyz = assembly_atoms[stage1_to_assembly[reported_stage1_index]]["xyz"]
    transferred_h_xyz = assembly_atoms[stage1_to_assembly[transferred_hydrogen_stage1_index]]["xyz"]
    core_atoms = assembly_atoms[:frozen_core_count]
    substrate_atoms = assembly_atoms[frozen_core_count:]
    substrate_heavy_atoms = [
        assembly_atoms[stage1_to_assembly[atom.GetIdx()]]["xyz"]
        for atom in posed_molecule.GetAtoms()
        if atom.GetAtomicNum() > 1
    ]
    substrate_centroid = centroid(substrate_heavy_atoms)
    porphyrin_ns = porphyrin_nitrogen_atoms(core_atoms, fe_atom_index_one_based)
    plane_points = [atom["xyz"] for atom in porphyrin_ns]
    reported_c_plane_signed = signed_plane_distance(reported_c_xyz, plane_points)
    transferred_h_plane_signed = signed_plane_distance(transferred_h_xyz, plane_points)
    centroid_plane_signed = signed_plane_distance(substrate_centroid, plane_points)

    features: dict[str, Any] = {
        "fe_n_distance_angstrom": distance(fe_xyz, nitrene_xyz),
        "nitrene_n_to_reported_c_distance_angstrom": distance(nitrene_xyz, reported_c_xyz),
        "nitrene_n_to_transferred_h_distance_angstrom": distance(nitrene_xyz, transferred_h_xyz),
        "reported_c_to_transferred_h_distance_angstrom": distance(reported_c_xyz, transferred_h_xyz),
        "fe_to_reported_c_distance_angstrom": distance(fe_xyz, reported_c_xyz),
        "fe_to_transferred_h_distance_angstrom": distance(fe_xyz, transferred_h_xyz),
        "cl_to_reported_c_distance_angstrom": distance(cl_xyz, reported_c_xyz),
        "cl_to_transferred_h_distance_angstrom": distance(cl_xyz, transferred_h_xyz),
        "substrate_centroid_to_fe_distance_angstrom": distance(substrate_centroid, fe_xyz),
        "substrate_centroid_to_nitrene_n_distance_angstrom": distance(substrate_centroid, nitrene_xyz),
        "substrate_centroid_to_reported_c_distance_angstrom": distance(substrate_centroid, reported_c_xyz),
        "reported_c_to_porphyrin_plane_signed_distance_angstrom": reported_c_plane_signed,
        "reported_c_to_porphyrin_plane_distance_angstrom": abs(reported_c_plane_signed),
        "transferred_h_to_porphyrin_plane_signed_distance_angstrom": transferred_h_plane_signed,
        "transferred_h_to_porphyrin_plane_distance_angstrom": abs(transferred_h_plane_signed),
        "substrate_centroid_to_porphyrin_plane_signed_distance_angstrom": centroid_plane_signed,
        "substrate_centroid_to_porphyrin_plane_distance_angstrom": abs(centroid_plane_signed),
        "fe_n_reported_c_angle_degrees": angle_degrees(fe_xyz, nitrene_xyz, reported_c_xyz),
        "nitrene_n_reported_c_transferred_h_angle_degrees": angle_degrees(nitrene_xyz, reported_c_xyz, transferred_h_xyz),
        "fe_reported_c_transferred_h_angle_degrees": angle_degrees(fe_xyz, reported_c_xyz, transferred_h_xyz),
        "fe_reported_c_nitrene_n_angle_degrees": angle_degrees(fe_xyz, reported_c_xyz, nitrene_xyz),
        "cl_fe_nitrene_n_angle_degrees": angle_degrees(cl_xyz, fe_xyz, nitrene_xyz),
        "cl_fe_reported_c_angle_degrees": angle_degrees(cl_xyz, fe_xyz, reported_c_xyz),
        "uff_pose_score": pose["uff_pose_score"],
        "score_rank": pose["score_rank"],
        "selection_bucket_is_low_energy": pose["selection_bucket"] == "low_energy",
        "selection_bucket_is_high_energy": pose["selection_bucket"] == "high_energy",
        "minimum_core_substrate_distance_angstrom": pose["minimum_core_substrate_distance_angstrom"],
        "reported_reactive_atom_map_id": reported_map_id,
        "reported_reactive_stage1_atom_index": reported_stage1_index,
        "transferred_hydrogen_stage1_atom_index": transferred_hydrogen_stage1_index,
        "porphyrin_plane_n_atom_count": len(porphyrin_ns),
        "substrate_heavy_atom_count": len(substrate_heavy_atoms),
        "substrate_atom_count": len(substrate_atoms),
        "core_atom_count": len(core_atoms),
    }
    features.update(
        core_substrate_contacts(
            core_atoms,
            substrate_atoms,
            fe_atom_index_one_based - 1,
            nitrene_substrate_offset=0,
        )
    )
    features.update(point_to_atoms_features(reported_c_xyz, core_atoms, "reported_c"))
    features.update(point_to_atoms_features(transferred_h_xyz, core_atoms, "transferred_h"))
    return {key: rounded(value) if isinstance(value, float) else value for key, value in features.items()}


def report_substrate_id(report: dict[str, Any]) -> str:
    substrate_ids = report.get("pose_generation_run", {}).get("substrate_ids", [])
    if len(substrate_ids) == 1:
        return substrate_ids[0]
    return report.get("substrate_record", {}).get("substrate_id")


def has_pose_interaction_inputs(record: dict[str, Any] | None) -> bool:
    return bool(
        record
        and record.get("reaction_center", {}).get("review_status") == "checked"
        and record.get("structure", {}).get("atom_mapped_substrate_smiles")
        and record.get("reaction_center", {}).get("reported_reactive_site")
    )


def generate_pose_interactions(
    records_path: Path,
    report_dir: Path,
    fe_atom_index_one_based: int = FE_ATOM_INDEX_ONE_BASED,
    cl_atom_index_one_based: int = CL_ATOM_INDEX_ONE_BASED,
) -> list[dict[str, Any]]:
    records_by_id = {record["substrate_id"]: record for record in read_jsonl(records_path)}
    rows = []
    for report_path in sorted(report_dir.glob("stage-1-smoke-*.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        substrate_id = report_substrate_id(report)
        record = records_by_id.get(substrate_id)
        if not has_pose_interaction_inputs(record):
            continue
        first_pose = report["pose_records"][0]
        posed_molecule = stage1_pose_molecule(first_pose["input_nitrene_smiles"])
        atom_map_to_stage1_index = map_ids_to_stage1_atom_indices(record, posed_molecule)
        for pose in report["pose_records"]:
            rows.append(
                {
                    "schema_version": "stage2-pose-interaction-features-v1",
                    "substrate_id": substrate_id,
                    "reaction_id": record["reaction_id"],
                    "pose_id": pose["pose_id"],
                    "pose_generation_run_id": pose["pose_generation_run_id"],
                    "curation_status": record["curation_status"],
                    "feature_status": "computed_from_stage1_assembly_geometry",
                    "feature_blocks": {
                        "pose_interaction": build_pose_features(
                            pose,
                            record,
                            posed_molecule,
                            atom_map_to_stage1_index,
                            fe_atom_index_one_based,
                            cl_atom_index_one_based,
                        )
                    },
                    "provenance": {
                        "stage1_report_path": display_path(report_path),
                        "fe_bound_assembly_xyz_path": pose["fe_bound_assembly_xyz_path"],
                        "constraint_profile_id": pose["constraint_profile_id"],
                        "reported_reactive_site": record["reaction_center"]["reported_reactive_site"],
                    },
                }
            )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--stage1-report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fe-atom-index", type=int, default=FE_ATOM_INDEX_ONE_BASED)
    parser.add_argument("--cl-atom-index", type=int, default=CL_ATOM_INDEX_ONE_BASED)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate_pose_interactions(args.records, args.stage1_report_dir, args.fe_atom_index, args.cl_atom_index)
    write_jsonl(args.output, rows)
    print(f"Wrote Stage 2 pose-interaction features for {len(rows)} poses to {display_path(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the Stage 1 pose-generation contract and emit a smoke report."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANUAL_SUBSTRATES = ROOT / "data/jacs_2025/manual-substrates.csv"
CONSTRAINT_PROFILE = ROOT / "data/jacs_2025/constraints/jacs-p7-alpha-feiv-aminyl.json"
REFERENCE_GEOMETRY = ROOT / "data/jacs_2025/reference-geometry/jacs-p7-2B.xyz"
DEFAULT_OUTPUT = ROOT / "data/jacs_2025/stage1/stage-1-smoke-1a.json"
DEFAULT_GEOMETRY_DIR = ROOT / "data/jacs_2025/stage1/geometries"
DEFAULT_RANDOM_SEED = 20260730
DEFAULT_POOL_SIZE = 1000
DEFAULT_RETAIN_LOW_COUNT = 100
DEFAULT_RETAIN_HIGH_COUNT = 100
CLASH_RADIUS_SCALE = 0.65
SUPPORTED_FORCE_FIELDS = ("uff", "mmff94")
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
    "Br": 1.20,
    "I": 1.39,
    "Fe": 1.32,
}


@dataclass(frozen=True)
class Atom:
    element: str
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class ToolkitStatus:
    rdkit_available: bool
    rdkit_version: str | None
    python_version: str
    platform: str


@dataclass(frozen=True)
class SubstrateValidation:
    substrate_id: str
    product_id: str
    azide_smiles: str
    nitrene_smiles: str
    azide_position: str
    nitrene_marker_count: int
    azide_marker_count: int
    rdkit_azide_parse_ok: bool | None
    rdkit_nitrene_parse_ok: bool | None
    rdkit_error: str | None


@dataclass(frozen=True)
class ReferenceGeometryValidation:
    geometry_id: str
    atom_count: int
    fe_atom_index_one_based: int
    nitrene_atom_index_one_based: int
    fe_n_distance_angstrom: float
    expected_fe_n_distance_angstrom: float
    fe_n_distance_delta_angstrom: float
    fe_n_distance_within_tolerance: bool


@dataclass(frozen=True)
class SubstratePoseRecord:
    pose_id: str
    pose_generation_run_id: str
    substrate_id: str
    constraint_profile_id: str
    geometry_scope: str
    core_geometry_policy: str
    input_nitrene_smiles: str
    input_xyz_path: str
    uff_optimized_xyz_path: str
    uff_optimized_sdf_path: str
    fe_bound_assembly_xyz_path: str
    uff_pose_score: float
    score_rank: int
    selection_bucket: str
    source_conformer_id: int
    validity_flags: dict[str, bool]
    fe_n_distance_angstrom: float
    core_rmsd_angstrom: float
    frozen_core_atom_count: int
    assembled_atom_count: int
    assembly_anchor_atom_index_one_based: int
    frozen_core_preserved: bool
    connectivity_preserved: bool
    minimum_core_substrate_distance_angstrom: float
    clash_screen_status: str
    uff_optimisation_status: str
    uff_optimisation_converged: bool
    force_field: str
    optimized_xyz_path: str
    optimized_sdf_path: str
    pose_score: float
    optimisation_status: str
    optimisation_converged: bool


@dataclass(frozen=True)
class ScoredConformer:
    conformer_id: int
    uff_pose_score: float
    uff_optimisation_status: str
    uff_optimisation_converged: bool
    connectivity_preserved: bool
    severe_clash_screen_passed: bool
    minimum_core_substrate_distance_angstrom: float
    force_field: str
    pose_score: float
    optimisation_status: str
    optimisation_converged: bool


def normalize_force_field(force_field: str | None) -> str:
    """Return the canonical local force-field name used by Stage 1."""
    value = (force_field or "uff").strip().lower().replace("-", "")
    if value == "mmff94":
        return "mmff94"
    if value == "uff":
        return "uff"
    raise ValueError(f"Unsupported force field {force_field!r}; choose one of {SUPPORTED_FORCE_FIELDS}")


def optimize_conformer(molecule: Any, conformer_id: int, force_field: str) -> tuple[int, float]:
    """Optimize and score one substrate conformer with UFF or MMFF94."""
    from rdkit.Chem import AllChem

    force_field = normalize_force_field(force_field)
    if force_field == "uff":
        status = AllChem.UFFOptimizeMolecule(molecule, confId=conformer_id, maxIters=500)
        field = AllChem.UFFGetMoleculeForceField(molecule, confId=conformer_id)
    else:
        if not AllChem.MMFFHasAllMoleculeParams(molecule):
            raise ValueError("RDKit MMFF94 has no parameters for the substrate molecule")
        status = AllChem.MMFFOptimizeMolecule(
            molecule,
            mmffVariant="MMFF94",
            confId=conformer_id,
            maxIters=500,
        )
        properties = AllChem.MMFFGetMoleculeProperties(molecule, mmffVariant="MMFF94")
        field = AllChem.MMFFGetMoleculeForceField(molecule, properties, confId=conformer_id)
    if field is None:
        raise ValueError(f"RDKit returned no {force_field} force field for conformer {conformer_id}")
    return int(status), float(field.CalcEnergy())


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_constraint_profile(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        profile = json.load(stream)

    required = {
        "constraint_profile_id",
        "reference_geometry",
        "fixed_bonds",
        "default_core_policy",
        "user_override_policy",
    }
    missing = sorted(required - set(profile))
    if missing:
        raise ValueError(f"Constraint profile is missing required fields: {', '.join(missing)}")
    if not profile["fixed_bonds"]:
        raise ValueError("Constraint profile must define at least one fixed bond")
    return profile


def load_manual_substrate(path: Path, substrate_id: str) -> dict[str, str]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))

    matches = [row for row in rows if row["substrate_id"] == substrate_id]
    if not matches:
        raise ValueError(f"Could not find substrate_id {substrate_id!r} in {path}")
    if len(matches) > 1:
        raise ValueError(f"Found duplicate substrate_id {substrate_id!r} in {path}")
    return matches[0]


def toolkit_status() -> ToolkitStatus:
    try:
        rdkit_version = metadata.version("rdkit")
    except metadata.PackageNotFoundError:
        rdkit_version = None

    return ToolkitStatus(
        rdkit_available=rdkit_version is not None,
        rdkit_version=rdkit_version,
        python_version=sys.version.split()[0],
        platform=platform.platform(),
    )


def validate_with_rdkit(smiles: str) -> tuple[bool | None, str | None]:
    try:
        from rdkit import Chem
    except ImportError:
        return None, "RDKit is not installed"

    try:
        molecule = Chem.MolFromSmiles(smiles, sanitize=True)
    except Exception as exc:  # RDKit raises several chemistry-specific exception types.
        return False, str(exc)
    return molecule is not None, None if molecule is not None else "RDKit returned no molecule"


def validate_substrate(row: dict[str, str]) -> SubstrateValidation:
    nitrene_marker_count = row["nitrene_smiles"].count("[N]")
    azide_marker_count = row["azide_smiles"].count("N#N=N") + row["azide_smiles"].count("N=N#N")
    azide_ok, azide_error = validate_with_rdkit(row["azide_smiles"])
    nitrene_ok, nitrene_error = validate_with_rdkit(row["nitrene_smiles"])
    rdkit_error = "; ".join(error for error in [azide_error, nitrene_error] if error) or None

    if nitrene_marker_count != 1:
        raise ValueError(
            f"{row['substrate_id']} must contain exactly one nitrene marker, found {nitrene_marker_count}"
        )
    if azide_marker_count != 1:
        raise ValueError(
            f"{row['substrate_id']} must contain exactly one terminal azide marker, found {azide_marker_count}"
        )

    return SubstrateValidation(
        substrate_id=row["substrate_id"],
        product_id=row["product_id"],
        azide_smiles=row["azide_smiles"],
        nitrene_smiles=row["nitrene_smiles"],
        azide_position=row["azide_position"],
        nitrene_marker_count=nitrene_marker_count,
        azide_marker_count=azide_marker_count,
        rdkit_azide_parse_ok=azide_ok,
        rdkit_nitrene_parse_ok=nitrene_ok,
        rdkit_error=rdkit_error,
    )


def parse_xyz(path: Path) -> list[Atom]:
    lines = path.read_text(encoding="utf-8").splitlines()
    expected_count = int(lines[0])
    atoms: list[Atom] = []
    for line in lines[2:]:
        element, x, y, z = line.split()
        atoms.append(Atom(element=element, x=float(x), y=float(y), z=float(z)))
    if len(atoms) != expected_count:
        raise ValueError(f"Expected {expected_count} atoms in {path}, parsed {len(atoms)}")
    return atoms


def distance(a: Atom, b: Atom) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def subtract(a: Atom, b: Atom) -> tuple[float, float, float]:
    return (a.x - b.x, a.y - b.y, a.z - b.z)


def vector_length(vector: tuple[float, float, float]) -> float:
    return math.sqrt(sum(component * component for component in vector))


def normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = vector_length(vector)
    if length == 0:
        raise ValueError("Cannot normalize a zero-length vector")
    return tuple(component / length for component in vector)


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum(left * right for left, right in zip(a, b, strict=True))


def cross(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def perpendicular_axis(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    trial = (1.0, 0.0, 0.0) if abs(vector[0]) < 0.9 else (0.0, 1.0, 0.0)
    return normalize(cross(vector, trial))


def rotate_vector(
    vector: tuple[float, float, float],
    source_axis: tuple[float, float, float],
    target_axis: tuple[float, float, float],
) -> tuple[float, float, float]:
    source = normalize(source_axis)
    target = normalize(target_axis)
    rotation_axis = cross(source, target)
    axis_length = vector_length(rotation_axis)
    cosine = max(-1.0, min(1.0, dot(source, target)))

    if axis_length < 1e-12:
        if cosine > 0:
            return vector
        rotation_axis = perpendicular_axis(source)
        axis_length = 1.0
        cosine = -1.0

    axis = tuple(component / axis_length for component in rotation_axis)
    sine = math.sqrt(max(0.0, 1.0 - cosine * cosine))
    axis_cross_vector = cross(axis, vector)
    axis_dot_vector = dot(axis, vector)
    return tuple(
        vector[i] * cosine
        + axis_cross_vector[i] * sine
        + axis[i] * axis_dot_vector * (1.0 - cosine)
        for i in range(3)
    )


def validate_reference_geometry(
    geometry_path: Path,
    profile: dict[str, Any],
    tolerance: float,
) -> ReferenceGeometryValidation:
    fixed_bond = profile["fixed_bonds"][0]
    fe_index, nitrene_index = fixed_bond["atom_indices_one_based"]
    atoms = parse_xyz(geometry_path)
    fe_atom = atoms[fe_index - 1]
    nitrene_atom = atoms[nitrene_index - 1]
    if fe_atom.element != "Fe":
        raise ValueError(f"Expected Fe at atom {fe_index}, found {fe_atom.element}")
    if nitrene_atom.element != "N":
        raise ValueError(f"Expected N at atom {nitrene_index}, found {nitrene_atom.element}")

    actual_distance = distance(fe_atom, nitrene_atom)
    expected_distance = float(fixed_bond["distance_angstrom"])
    delta = abs(actual_distance - expected_distance)
    return ReferenceGeometryValidation(
        geometry_id=geometry_path.stem,
        atom_count=len(atoms),
        fe_atom_index_one_based=fe_index,
        nitrene_atom_index_one_based=nitrene_index,
        fe_n_distance_angstrom=round(actual_distance, 6),
        expected_fe_n_distance_angstrom=expected_distance,
        fe_n_distance_delta_angstrom=round(delta, 9),
        fe_n_distance_within_tolerance=delta <= tolerance,
    )


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def canonical_smiles_without_hydrogens(molecule: Any) -> str:
    from rdkit import Chem

    return Chem.MolToSmiles(Chem.RemoveHs(molecule), canonical=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def xyz_block(atoms: list[Atom], comment: str) -> str:
    lines = [str(len(atoms)), comment]
    lines.extend(f"{atom.element:<2} {atom.x:12.6f} {atom.y:12.6f} {atom.z:12.6f}" for atom in atoms)
    return "\n".join(lines) + "\n"


def write_sdf(path: Path, molecule: Any) -> None:
    from rdkit import Chem

    path.parent.mkdir(parents=True, exist_ok=True)
    writer = Chem.SDWriter(str(path))
    try:
        writer.write(molecule)
    finally:
        writer.close()


def clear_previous_pose_artifacts(geometry_dir: Path, substrate_id: str, run_id: str) -> None:
    substrate_dir = geometry_dir / substrate_id
    if not substrate_dir.exists():
        return
    for path in substrate_dir.glob(f"{run_id}-substrate-*"):
        if path.is_file():
            path.unlink()


def molecule_xyz_block(molecule: Any, conformer_id: int) -> str:
    from rdkit import Chem

    return Chem.MolToXYZBlock(molecule, confId=conformer_id)


def conformer_atoms(molecule: Any, conformer_id: int) -> list[Atom]:
    conformer = molecule.GetConformer(conformer_id)
    atoms = []
    for atom in molecule.GetAtoms():
        position = conformer.GetAtomPosition(atom.GetIdx())
        atoms.append(Atom(atom.GetSymbol(), position.x, position.y, position.z))
    return atoms


def heavy_atom_indices(molecule: Any) -> list[int]:
    return [atom.GetIdx() for atom in molecule.GetAtoms() if atom.GetAtomicNum() > 1]


def conformer_rmsd(molecule: Any, left_conformer_id: int, right_conformer_id: int) -> float:
    import numpy as np

    indices = heavy_atom_indices(molecule)
    left_conformer = molecule.GetConformer(left_conformer_id)
    right_conformer = molecule.GetConformer(right_conformer_id)
    left = np.array(
        [
            [
                left_conformer.GetAtomPosition(index).x,
                left_conformer.GetAtomPosition(index).y,
                left_conformer.GetAtomPosition(index).z,
            ]
            for index in indices
        ]
    )
    right = np.array(
        [
            [
                right_conformer.GetAtomPosition(index).x,
                right_conformer.GetAtomPosition(index).y,
                right_conformer.GetAtomPosition(index).z,
            ]
            for index in indices
        ]
    )
    left_centered = left - left.mean(axis=0)
    right_centered = right - right.mean(axis=0)
    covariance = left_centered.T @ right_centered
    left_singular, _, right_singular = np.linalg.svd(covariance)
    determinant = np.linalg.det(left_singular @ right_singular)
    correction = np.diag([1.0, 1.0, determinant])
    rotation = left_singular @ correction @ right_singular
    aligned = left_centered @ rotation
    return float(np.sqrt(((aligned - right_centered) ** 2).sum() / len(indices)))


def rmsd_summary(molecule: Any, conformer_ids: list[int]) -> dict[str, float | int | None]:
    values = [
        conformer_rmsd(molecule, left_id, right_id)
        for left_index, left_id in enumerate(conformer_ids)
        for right_id in conformer_ids[left_index + 1 :]
    ]
    if not values:
        return {"pair_count": 0, "min": None, "mean": None, "max": None}
    return {
        "pair_count": len(values),
        "min": round(min(values), 6),
        "mean": round(sum(values) / len(values), 6),
        "max": round(max(values), 6),
    }


def molecule_anchor_indices(molecule: Any) -> tuple[int, int]:
    nitrene_atoms = [
        atom
        for atom in molecule.GetAtoms()
        if atom.GetSymbol() == "N" and atom.GetDegree() == 1 and atom.GetFormalCharge() == 0
    ]
    if len(nitrene_atoms) != 1:
        raise ValueError(f"Expected one substrate-bound nitrene N, found {len(nitrene_atoms)}")
    nitrene_atom = nitrene_atoms[0]
    neighbor = nitrene_atom.GetNeighbors()[0]
    return nitrene_atom.GetIdx(), neighbor.GetIdx()


def core_rmsd(left: list[Atom], right: list[Atom]) -> float:
    if len(left) != len(right):
        raise ValueError("Core atom lists must be the same length for RMSD")
    squared_sum = sum(distance(a, b) ** 2 for a, b in zip(left, right, strict=True))
    return math.sqrt(squared_sum / len(left))


def build_frozen_core_assembly(
    molecule: Any,
    reference_atoms: list[Atom],
    optimized_substrate_atoms: list[Atom],
    profile: dict[str, Any],
    assembly_xyz: Path,
) -> tuple[float, float, int, int, int, bool]:
    assembled_atoms, _, _ = assemble_frozen_core_atoms(molecule, reference_atoms, optimized_substrate_atoms, profile)
    write_text(
        assembly_xyz,
        xyz_block(
            assembled_atoms,
            "Stage 1 frozen-core assembly; reference catalyst atoms copied unchanged",
        ),
    )

    fixed_bond = profile["fixed_bonds"][0]
    fe_index, nitrene_index = fixed_bond["atom_indices_one_based"]
    core_atoms = reference_atoms[: nitrene_index - 1]
    preserved_core_rmsd = core_rmsd(assembled_atoms[: len(core_atoms)], core_atoms)
    fe_n_distance = distance(assembled_atoms[fe_index - 1], assembled_atoms[nitrene_index - 1])
    return (
        round(fe_n_distance, 6),
        round(preserved_core_rmsd, 12),
        len(core_atoms),
        len(assembled_atoms),
        nitrene_index,
        preserved_core_rmsd == 0.0,
    )


def assemble_frozen_core_atoms(
    molecule: Any,
    reference_atoms: list[Atom],
    optimized_substrate_atoms: list[Atom],
    profile: dict[str, Any],
) -> tuple[list[Atom], int, int]:
    fixed_bond = profile["fixed_bonds"][0]
    _, nitrene_index = fixed_bond["atom_indices_one_based"]
    core_atoms = reference_atoms[: nitrene_index - 1]

    substrate_n_index, substrate_neighbor_index = molecule_anchor_indices(molecule)
    source_n = optimized_substrate_atoms[substrate_n_index]
    source_neighbor = optimized_substrate_atoms[substrate_neighbor_index]
    target_n = reference_atoms[nitrene_index - 1]
    target_neighbor = reference_atoms[nitrene_index]
    source_axis = subtract(source_neighbor, source_n)
    target_axis = subtract(target_neighbor, target_n)

    transformed_substrate_atoms = []
    for atom in optimized_substrate_atoms:
        shifted = subtract(atom, source_n)
        rotated = rotate_vector(shifted, source_axis, target_axis)
        transformed_substrate_atoms.append(
            Atom(
                element=atom.element,
                x=target_n.x + rotated[0],
                y=target_n.y + rotated[1],
                z=target_n.z + rotated[2],
            )
        )

    ordered_substrate_indices = [substrate_n_index, substrate_neighbor_index] + [
        index
        for index in range(len(transformed_substrate_atoms))
        if index not in {substrate_n_index, substrate_neighbor_index}
    ]
    ordered_substrate_atoms = [transformed_substrate_atoms[index] for index in ordered_substrate_indices]

    return core_atoms + ordered_substrate_atoms, 0, nitrene_index


def covalent_radius(element: str) -> float:
    try:
        return COVALENT_RADII_ANGSTROM[element]
    except KeyError as exc:
        raise ValueError(f"No covalent radius configured for element {element}") from exc


def severe_clash_screen(
    molecule: Any,
    reference_atoms: list[Atom],
    optimized_substrate_atoms: list[Atom],
    profile: dict[str, Any],
) -> tuple[bool, float]:
    assembled_atoms, substrate_n_index, nitrene_index = assemble_frozen_core_atoms(
        molecule,
        reference_atoms,
        optimized_substrate_atoms,
        profile,
    )
    fixed_bond = profile["fixed_bonds"][0]
    fe_index, _ = fixed_bond["atom_indices_one_based"]
    core_atoms = assembled_atoms[: nitrene_index - 1]
    substrate_atoms = assembled_atoms[nitrene_index - 1 :]
    minimum_distance = math.inf

    for core_offset, core_atom in enumerate(core_atoms):
        core_index = core_offset + 1
        for substrate_offset, substrate_atom in enumerate(substrate_atoms):
            if core_index == fe_index and substrate_offset == substrate_n_index:
                continue
            atom_distance = distance(core_atom, substrate_atom)
            minimum_distance = min(minimum_distance, atom_distance)
            clash_floor = CLASH_RADIUS_SCALE * (
                covalent_radius(core_atom.element) + covalent_radius(substrate_atom.element)
            )
            if atom_distance < clash_floor:
                return False, round(minimum_distance, 6)
    return True, round(minimum_distance, 6)


def build_frozen_core_pose_record(
    substrate: SubstrateValidation,
    run_id: str,
    profile: dict[str, Any],
    reference_atoms: list[Atom],
    geometry_dir: Path,
    molecule: Any,
    conformer_id: int,
    pose_number: int,
    score_rank: int,
    selection_bucket: str,
    severe_clash_screen_passed: bool,
    minimum_core_substrate_distance: float,
    starting_canonical_smiles: str,
    force_field: str = "uff",
) -> SubstratePoseRecord:
    from rdkit import Chem
    from rdkit.Chem import AllChem

    force_field = normalize_force_field(force_field)
    pose_id = f"{run_id}-substrate-{force_field}-{pose_number:04d}"
    substrate_dir = geometry_dir / substrate.substrate_id
    input_xyz = substrate_dir / f"{pose_id}-input.xyz"
    optimized_xyz = substrate_dir / f"{pose_id}-{force_field}.xyz"
    optimized_sdf = substrate_dir / f"{pose_id}-{force_field}.sdf"
    assembly_xyz = substrate_dir / f"{pose_id}-assembly.xyz"

    write_text(input_xyz, molecule_xyz_block(molecule, conformer_id))
    optimisation_status_code, pose_score = optimize_conformer(molecule, conformer_id, force_field)
    write_text(optimized_xyz, molecule_xyz_block(molecule, conformer_id))
    conformer_only = Chem.Mol(molecule)
    conformer_only.RemoveAllConformers()
    conformer_only.AddConformer(molecule.GetConformer(conformer_id), assignId=True)
    write_sdf(optimized_sdf, conformer_only)
    (
        fe_n_distance,
        preserved_core_rmsd,
        frozen_core_atom_count,
        assembled_atom_count,
        assembly_anchor_atom_index,
        frozen_core_preserved,
    ) = build_frozen_core_assembly(molecule, reference_atoms, conformer_atoms(molecule, conformer_id), profile, assembly_xyz)

    optimized_canonical_smiles = canonical_smiles_without_hydrogens(molecule)
    connectivity_preserved = optimized_canonical_smiles == starting_canonical_smiles
    optimisation_converged = optimisation_status_code == 0
    validity_flags = {
        "rdkit_parse_ok": True,
        "rdkit_embed_ok": True,
        "connectivity_preserved": connectivity_preserved,
        "uff_optimisation_converged": optimisation_converged,
        f"{force_field}_optimisation_converged": optimisation_converged,
        "severe_clash_screen_passed": severe_clash_screen_passed,
        "frozen_core_preserved": frozen_core_preserved,
        "fe_n_distance_within_constraint": True,
        "catalyst_uff_optimised": False,
    }

    return SubstratePoseRecord(
        pose_id=pose_id,
        pose_generation_run_id=run_id,
        substrate_id=substrate.substrate_id,
        constraint_profile_id=profile["constraint_profile_id"],
        geometry_scope="fe_bound_frozen_core_assembly",
        core_geometry_policy=profile.get("core_geometry_policy", "reference Fe catalyst atoms copied unchanged"),
        input_nitrene_smiles=substrate.nitrene_smiles,
        input_xyz_path=display_path(input_xyz),
        uff_optimized_xyz_path=display_path(optimized_xyz),
        uff_optimized_sdf_path=display_path(optimized_sdf),
        fe_bound_assembly_xyz_path=display_path(assembly_xyz),
        uff_pose_score=round(pose_score, 6),
        score_rank=score_rank,
        selection_bucket=selection_bucket,
        source_conformer_id=conformer_id,
        validity_flags=validity_flags,
        fe_n_distance_angstrom=fe_n_distance,
        core_rmsd_angstrom=preserved_core_rmsd,
        frozen_core_atom_count=frozen_core_atom_count,
        assembled_atom_count=assembled_atom_count,
        assembly_anchor_atom_index_one_based=assembly_anchor_atom_index,
        frozen_core_preserved=frozen_core_preserved,
        connectivity_preserved=connectivity_preserved,
        minimum_core_substrate_distance_angstrom=minimum_core_substrate_distance,
        clash_screen_status="passed_covalent_radius_floor",
        uff_optimisation_status=f"rdkit_{force_field}_status_{optimisation_status_code}",
        uff_optimisation_converged=optimisation_converged,
        force_field=force_field,
        optimized_xyz_path=display_path(optimized_xyz),
        optimized_sdf_path=display_path(optimized_sdf),
        pose_score=round(pose_score, 6),
        optimisation_status=f"rdkit_{force_field}_status_{optimisation_status_code}",
        optimisation_converged=optimisation_converged,
    )


def score_conformers(
    molecule: Any,
    starting_canonical_smiles: str,
    reference_atoms: list[Atom],
    profile: dict[str, Any],
    force_field: str = "uff",
) -> list[ScoredConformer]:
    force_field = normalize_force_field(force_field)
    scored_conformers = []
    for conformer in molecule.GetConformers():
        conformer_id = conformer.GetId()
        optimisation_status_code, pose_score = optimize_conformer(molecule, conformer_id, force_field)
        connectivity_preserved = canonical_smiles_without_hydrogens(molecule) == starting_canonical_smiles
        clash_passed, minimum_distance = severe_clash_screen(
            molecule,
            reference_atoms,
            conformer_atoms(molecule, conformer_id),
            profile,
        )
        scored_conformers.append(
            ScoredConformer(
                conformer_id=conformer_id,
                uff_pose_score=round(pose_score, 6),
                uff_optimisation_status=f"rdkit_{force_field}_status_{optimisation_status_code}",
                uff_optimisation_converged=optimisation_status_code == 0,
                connectivity_preserved=connectivity_preserved,
                severe_clash_screen_passed=clash_passed,
                minimum_core_substrate_distance_angstrom=minimum_distance,
                force_field=force_field,
                pose_score=round(pose_score, 6),
                optimisation_status=f"rdkit_{force_field}_status_{optimisation_status_code}",
                optimisation_converged=optimisation_status_code == 0,
            )
        )
    return scored_conformers


def select_conformers(
    scored_conformers: list[ScoredConformer],
    retain_low_count: int,
    retain_high_count: int,
) -> list[tuple[str, ScoredConformer]]:
    valid_conformers = [
        conformer
        for conformer in scored_conformers
        if (
            conformer.uff_optimisation_converged
            and conformer.connectivity_preserved
            and conformer.severe_clash_screen_passed
        )
    ]
    if len(valid_conformers) < retain_low_count + retain_high_count:
        raise ValueError(
            "Not enough valid conformers to retain requested low/high sets: "
            f"{len(valid_conformers)} valid/clash-screened for {retain_low_count + retain_high_count} requested"
        )
    by_energy = sorted(valid_conformers, key=lambda conformer: (conformer.uff_pose_score, conformer.conformer_id))
    low = by_energy[:retain_low_count]
    low_ids = {conformer.conformer_id for conformer in low}
    high_candidates = [conformer for conformer in reversed(by_energy) if conformer.conformer_id not in low_ids]
    high = high_candidates[:retain_high_count]
    return [("low_energy", conformer) for conformer in low] + [("high_energy", conformer) for conformer in high]


def build_pose_records(
    substrate: SubstrateValidation,
    run_id: str,
    profile: dict[str, Any],
    reference_atoms: list[Atom],
    geometry_dir: Path,
    random_seed: int,
    pool_size: int,
    retain_low_count: int,
    retain_high_count: int,
    force_field: str = "uff",
) -> tuple[list[SubstratePoseRecord], dict[str, Any]]:
    from rdkit import Chem
    from rdkit.Chem import AllChem

    force_field = normalize_force_field(force_field)

    # MMFF94 can exhaust the process memory when RDKit holds a 5,000-conformer
    # pool for larger substrates. Generate it in deterministic 1,000-conformer
    # chunks, retain only each chunk's low/high candidates, then select the
    # global 200 poses. A global low/high candidate must also be low/high in
    # its own chunk, so this is exactly equivalent to ranking the full pool.
    if force_field == "mmff94" and pool_size > 1000:
        starting_molecule = Chem.MolFromSmiles(substrate.nitrene_smiles, sanitize=True)
        if starting_molecule is None:
            raise ValueError(f"RDKit could not parse nitrene SMILES for {substrate.substrate_id}")
        starting_canonical_smiles = Chem.MolToSmiles(starting_molecule, canonical=True)

        def make_chunk(chunk_index: int, chunk_count: int) -> Any:
            chunk_molecule = Chem.AddHs(Chem.Mol(starting_molecule))
            embed_params = AllChem.ETKDGv3()
            embed_params.randomSeed = int(random_seed + chunk_index)
            conformer_ids = list(AllChem.EmbedMultipleConfs(chunk_molecule, numConfs=chunk_count, params=embed_params))
            if len(conformer_ids) != chunk_count:
                raise ValueError(
                    f"Expected {chunk_count} MMFF94 conformers in chunk {chunk_index}, generated {len(conformer_ids)}"
                )
            return chunk_molecule

        candidates: list[dict[str, Any]] = []
        total_clash_passed = 0
        total_valid = 0
        total_valid_and_clash = 0
        chunk_size = 1000
        for chunk_index, start in enumerate(range(0, pool_size, chunk_size)):
            chunk_count = min(chunk_size, pool_size - start)
            chunk_molecule = make_chunk(chunk_index, chunk_count)
            scored = score_conformers(
                chunk_molecule,
                starting_canonical_smiles,
                reference_atoms,
                profile,
                force_field=force_field,
            )
            total_clash_passed += sum(item.severe_clash_screen_passed for item in scored)
            total_valid += sum(item.optimisation_converged and item.connectivity_preserved for item in scored)
            total_valid_and_clash += sum(
                item.optimisation_converged and item.connectivity_preserved and item.severe_clash_screen_passed
                for item in scored
            )
            for _, item in select_conformers(scored, retain_low_count, retain_high_count):
                candidate_molecule = Chem.Mol(chunk_molecule)
                candidate_molecule.RemoveAllConformers()
                candidate_molecule.AddConformer(Chem.Conformer(chunk_molecule.GetConformer(item.conformer_id)), assignId=True)
                candidates.append(
                    {
                        "chunk_index": chunk_index,
                        "conformer_id": item.conformer_id,
                        "score": item.pose_score,
                        "scored": item,
                        "molecule": candidate_molecule,
                    }
                )

        required = retain_low_count + retain_high_count
        if len(candidates) < required:
            raise ValueError(
                "Not enough valid MMFF94 conformers to retain requested low/high sets: "
                f"{len(candidates)} valid/clash-screened for {required} requested"
            )
        ordered = sorted(candidates, key=lambda item: (item["score"], item["chunk_index"], item["conformer_id"]))
        low = ordered[:retain_low_count]
        low_keys = {(item["chunk_index"], item["conformer_id"]) for item in low}
        high = [item for item in reversed(ordered) if (item["chunk_index"], item["conformer_id"]) not in low_keys][:retain_high_count]
        selected = [("low_energy", item) for item in low] + [("high_energy", item) for item in high]
        pose_records: list[SubstratePoseRecord] = []
        selected_coordinates: list[list[Atom]] = []
        for pose_number, (bucket, candidate) in enumerate(selected, start=1):
            item = candidate["scored"]
            candidate_molecule = candidate["molecule"]
            selected_coordinates.append(conformer_atoms(candidate_molecule, 0))
            pose_records.append(
                build_frozen_core_pose_record(
                    substrate=substrate,
                    run_id=run_id,
                    profile=profile,
                    reference_atoms=reference_atoms,
                    geometry_dir=geometry_dir,
                    molecule=candidate_molecule,
                    conformer_id=0,
                    pose_number=pose_number,
                    score_rank=pose_number,
                    selection_bucket=bucket,
                    severe_clash_screen_passed=item.severe_clash_screen_passed,
                    minimum_core_substrate_distance=item.minimum_core_substrate_distance_angstrom,
                    starting_canonical_smiles=starting_canonical_smiles,
                    force_field=force_field,
                )
            )

        def raw_rmsd(left: list[Atom], right: list[Atom]) -> float:
            heavy = [index for index, atom in enumerate(left) if atom.element != "H"]
            if not heavy or len(left) != len(right):
                return 0.0
            return math.sqrt(sum(distance(left[index], right[index]) ** 2 for index in heavy) / len(heavy))

        pairwise = [
            raw_rmsd(left, right)
            for left_index, left in enumerate(selected_coordinates)
            for right in selected_coordinates[left_index + 1 :]
        ]
        diversity = {
            "generated_pool_size": pool_size,
            "valid_conformer_count": total_valid,
            "clash_screened_valid_conformer_count": total_valid_and_clash,
            "written_pose_count": len(pose_records),
            "selected_pairwise_heavy_atom_rmsd_angstrom": {
                "pair_count": len(pairwise),
                "min": round(min(pairwise), 6) if pairwise else None,
                "mean": round(sum(pairwise) / len(pairwise), 6) if pairwise else None,
                "max": round(max(pairwise), 6) if pairwise else None,
            },
            "clash_screen": {
                "method": "covalent-radius floor",
                "radius_scale": CLASH_RADIUS_SCALE,
                "passed_count": total_clash_passed,
                "failed_count": pool_size - total_clash_passed,
            },
            "force_field": force_field,
            "selection_implementation": "deterministic_mmff94_chunk_candidates",
            "chunk_size": chunk_size,
            "pool_pose_score_min": min(item["score"] for item in ordered),
            "pool_pose_score_max": max(item["score"] for item in ordered),
        }
        return pose_records, diversity

    molecule = Chem.MolFromSmiles(substrate.nitrene_smiles, sanitize=True)
    if molecule is None:
        raise ValueError(f"RDKit could not parse nitrene SMILES for {substrate.substrate_id}")
    starting_canonical_smiles = Chem.MolToSmiles(molecule, canonical=True)
    molecule = Chem.AddHs(molecule)
    embed_params = AllChem.ETKDGv3()
    embed_params.randomSeed = random_seed
    conformer_ids = list(AllChem.EmbedMultipleConfs(molecule, numConfs=pool_size, params=embed_params))
    if len(conformer_ids) != pool_size:
        raise ValueError(f"Expected {pool_size} conformers, generated {len(conformer_ids)}")
    scored_conformers = score_conformers(
        molecule,
        starting_canonical_smiles,
        reference_atoms,
        profile,
        force_field=force_field,
    )
    selected_conformers = select_conformers(scored_conformers, retain_low_count, retain_high_count)

    pose_records = [
        build_frozen_core_pose_record(
            substrate=substrate,
            run_id=run_id,
            profile=profile,
            reference_atoms=reference_atoms,
            geometry_dir=geometry_dir,
            molecule=molecule,
            conformer_id=scored_conformer.conformer_id,
            pose_number=pose_number,
            score_rank=pose_number,
            selection_bucket=selection_bucket,
            severe_clash_screen_passed=scored_conformer.severe_clash_screen_passed,
            minimum_core_substrate_distance=scored_conformer.minimum_core_substrate_distance_angstrom,
            starting_canonical_smiles=starting_canonical_smiles,
            force_field=force_field,
        )
        for pose_number, (selection_bucket, scored_conformer) in enumerate(selected_conformers, start=1)
    ]
    selected_ids = [scored_conformer.conformer_id for _, scored_conformer in selected_conformers]
    valid_count = sum(
        conformer.uff_optimisation_converged and conformer.connectivity_preserved
        for conformer in scored_conformers
    )
    clash_passed_count = sum(conformer.severe_clash_screen_passed for conformer in scored_conformers)
    diversity = {
        "generated_pool_size": pool_size,
        "valid_conformer_count": valid_count,
        "clash_screened_valid_conformer_count": sum(
            conformer.uff_optimisation_converged
            and conformer.connectivity_preserved
            and conformer.severe_clash_screen_passed
            for conformer in scored_conformers
        ),
        "written_pose_count": len(pose_records),
        "selected_pairwise_heavy_atom_rmsd_angstrom": rmsd_summary(molecule, selected_ids),
        "clash_screen": {
            "method": "covalent-radius floor",
            "radius_scale": CLASH_RADIUS_SCALE,
            "passed_count": clash_passed_count,
            "failed_count": len(scored_conformers) - clash_passed_count,
            "minimum_core_substrate_distance_angstrom": {
                "min": min(
                    conformer.minimum_core_substrate_distance_angstrom for conformer in scored_conformers
                ),
                "max": max(
                    conformer.minimum_core_substrate_distance_angstrom for conformer in scored_conformers
                ),
            },
        },
        "force_field": force_field,
        "pool_uff_score_min": min(conformer.uff_pose_score for conformer in scored_conformers),
        "pool_uff_score_max": max(conformer.uff_pose_score for conformer in scored_conformers),
        "pool_pose_score_min": min(conformer.pose_score for conformer in scored_conformers),
        "pool_pose_score_max": max(conformer.pose_score for conformer in scored_conformers),
    }
    return pose_records, diversity


def build_report(
    substrate_id: str,
    tolerance: float,
    geometry_dir: Path,
    random_seed: int,
    pool_size: int,
    retain_low_count: int,
    retain_high_count: int,
    manual_substrates_path: Path = MANUAL_SUBSTRATES,
    constraint_profile_path: Path = CONSTRAINT_PROFILE,
    reference_geometry_path: Path = REFERENCE_GEOMETRY,
    run_id_prefix: str | None = None,
    force_field: str = "uff",
) -> dict[str, Any]:
    force_field = normalize_force_field(force_field)
    profile = load_constraint_profile(constraint_profile_path)
    substrate = validate_substrate(load_manual_substrate(manual_substrates_path, substrate_id))
    reference = validate_reference_geometry(reference_geometry_path, profile, tolerance)
    reference_atoms = parse_xyz(reference_geometry_path)
    timestamp = datetime.now(UTC).isoformat()
    run_id = f"{run_id_prefix}-{substrate_id}" if run_id_prefix else f"stage1-smoke-{substrate_id}"
    clear_previous_pose_artifacts(geometry_dir, substrate_id, run_id)
    pose_records, diversity_summary = build_pose_records(
        substrate=substrate,
        run_id=run_id,
        profile=profile,
        reference_atoms=reference_atoms,
        geometry_dir=geometry_dir,
        random_seed=random_seed,
        pool_size=pool_size,
        retain_low_count=retain_low_count,
        retain_high_count=retain_high_count,
        force_field=force_field,
    )

    return {
        "schema": "genaisubstrate.stage1.smoke-report.v1",
        "created_at": timestamp,
        "toolkit": asdict(toolkit_status()),
        "pose_generation_run": {
            "pose_generation_run_id": run_id,
            "substrate_ids": [substrate_id],
            "constraint_profile_id": profile["constraint_profile_id"],
            "reference_geometry_id": reference.geometry_id,
            "manual_substrates_sha256": file_sha256(manual_substrates_path),
            "constraint_profile_sha256": file_sha256(constraint_profile_path),
            "reference_geometry_sha256": file_sha256(reference_geometry_path),
            "catalyst_id": profile.get("catalyst_id"),
            "force_field": force_field,
            "random_seed": random_seed,
            "generated_pool_size": pool_size,
            "retained_low_energy_count": retain_low_count,
            "retained_high_energy_count": retain_high_count,
            "written_pose_count": len(pose_records),
            "filter_settings": {
                "fe_n_distance_tolerance_angstrom": tolerance,
                "label_blind": True,
                "severe_clash_screen": {
                    "method": "covalent-radius floor",
                    "radius_scale": CLASH_RADIUS_SCALE,
                },
            },
            "output_contract": (
                f"generate conformer pool, retain low/high {force_field} substrate poses, "
                "write frozen-core Fe-bound assemblies only for retained poses"
            ),
            "timestamp": timestamp,
        },
        "constraint_profile": {
            "constraint_profile_id": profile["constraint_profile_id"],
            "reference_geometry": profile["reference_geometry"],
            "catalyst_id": profile.get("catalyst_id"),
            "fixed_bonds": profile["fixed_bonds"],
            "default_core_policy": profile["default_core_policy"],
            "user_override_policy": profile["user_override_policy"],
        },
        "substrate_record": asdict(substrate),
        "reference_geometry": asdict(reference),
        "diversity_summary": diversity_summary,
        "pose_records": [asdict(pose_record) for pose_record in pose_records],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--substrate-id", default="1a")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--geometry-dir", type=Path, default=DEFAULT_GEOMETRY_DIR)
    parser.add_argument("--fe-n-tolerance", type=float, default=1e-5)
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED)
    parser.add_argument("--pool-size", type=int, default=DEFAULT_POOL_SIZE)
    parser.add_argument("--retain-low-count", type=int, default=DEFAULT_RETAIN_LOW_COUNT)
    parser.add_argument("--retain-high-count", type=int, default=DEFAULT_RETAIN_HIGH_COUNT)
    parser.add_argument("--manual-substrates", type=Path, default=MANUAL_SUBSTRATES)
    parser.add_argument("--constraint-profile", type=Path, default=CONSTRAINT_PROFILE)
    parser.add_argument("--reference-geometry", type=Path, default=REFERENCE_GEOMETRY)
    parser.add_argument("--run-id-prefix")
    parser.add_argument("--force-field", choices=SUPPORTED_FORCE_FIELDS, default="uff")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(
        args.substrate_id,
        args.fe_n_tolerance,
        args.geometry_dir,
        args.random_seed,
        args.pool_size,
        args.retain_low_count,
        args.retain_high_count,
        args.manual_substrates,
        args.constraint_profile,
        args.reference_geometry,
        args.run_id_prefix,
        args.force_field,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote Stage 1 smoke report to {args.output}")


if __name__ == "__main__":
    main()

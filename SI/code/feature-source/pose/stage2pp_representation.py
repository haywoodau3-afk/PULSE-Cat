#!/usr/bin/env python3
"""Build persistent Stage 2″ occupancy/flexibility features and compare models.

Stage 2″ keeps the existing 200 retained Stage 1 poses per substrate, writes
numerical reaction-axis occupancy arrays plus derived SVG diagnostics, and
adds reaction-corridor flexibility to the existing Stage 2p representation.
The fields are geometric atom occupancies from XYZ coordinates, not electron
density.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy
from scipy.stats import energy_distance, spearmanr, wasserstein_distance
from rdkit import Chem
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
STAGE2P_SCRIPT = ROOT / "scripts/stage2p_representation.py"
STAGE2_FULL_SCOPE_SCRIPT = ROOT / "scripts/stage2_full_scope_benchmark.py"
STAGE2_FOLDING_SCRIPT = ROOT / "scripts/stage2_folding_feature_experiment.py"
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_REPORT_DIR = ROOT / "data/jacs_2025/stage1/panel"
DEFAULT_STAGE2P_FEATURES = ROOT / "data/jacs_2025/stage2/features/stage2p-features.jsonl"
DEFAULT_POSE_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"
DEFAULT_POSE_INTERACTION = ROOT / "data/jacs_2025/stage2/features/pose-interaction.jsonl"
DEFAULT_POSE_FOLDING = ROOT / "data/jacs_2025/stage2/features/pose-folding-features.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "data/jacs_2025/stage2pp"
DEFAULT_FEATURES = DEFAULT_OUTPUT_DIR / "features/stage2pp-features.jsonl"
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "features/stage2pp-manifest.json"
DEFAULT_METRICS = DEFAULT_OUTPUT_DIR / "modeling/stage2pp-model-comparison.json"
DEFAULT_PREDICTIONS = DEFAULT_OUTPUT_DIR / "modeling/stage2pp-predictions.csv"
DEFAULT_TRENDS = DEFAULT_OUTPUT_DIR / "modeling/stage2pp-trends.csv"
DEFAULT_DENSITY_DIR = DEFAULT_OUTPUT_DIR / "density"
DEFAULT_SVG_DIR = DEFAULT_OUTPUT_DIR / "svg"

STRATA = ("top_100", "bottom_100", "all_200")
VIEWS = ("nitrene", "activation", "n_to_h", "h_to_n")
CHANNELS = ("all_heavy", "carbon", "hetero", "halogen", "hydrogen", "reactive_c", "reactive_h")
EXCLUDED_EE = {"1an", "1ad", "1z"}

# Fixed, versioned hard-rule grid. Coordinates are in the local N↔H frame.
Z_EDGES = numpy.linspace(-8.0, 12.0, 41)
RHO_EDGES = numpy.linspace(0.0, 10.0, 21)
VDW_RADII = {
    "H": 1.20,
    "B": 1.92,
    "C": 1.70,
    "N": 1.55,
    "O": 1.52,
    "F": 1.47,
    "Si": 2.10,
    "P": 1.80,
    "S": 1.80,
    "Cl": 1.75,
    "Br": 1.85,
    "I": 1.98,
}
CLUSTER_QUANTIZATION = 0.35


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


stage2p = load_module("stage2p_for_stage2pp", STAGE2P_SCRIPT)
stage2_full_scope = load_module("stage2_full_scope_for_stage2pp", STAGE2_FULL_SCOPE_SCRIPT)
stage2_folding = load_module("stage2_folding_for_stage2pp", STAGE2_FOLDING_SCRIPT)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def finite(value: float | None) -> float:
    return float(value) if value is not None and math.isfinite(float(value)) else 0.0


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def weighted_mean(values: list[float], weights: list[float]) -> float:
    if not values or not weights or sum(weights) <= 0:
        return 0.0
    return float(numpy.average(numpy.asarray(values, dtype=float), weights=numpy.asarray(weights, dtype=float)))


def weighted_std(values: list[float], weights: list[float]) -> float:
    if not values or not weights or sum(weights) <= 0:
        return 0.0
    array = numpy.asarray(values, dtype=float)
    weight_array = numpy.asarray(weights, dtype=float)
    mean = numpy.average(array, weights=weight_array)
    return float(numpy.sqrt(numpy.average((array - mean) ** 2, weights=weight_array)))


def weighted_quantile(values: list[float], weights: list[float], fraction: float) -> float:
    if not values or not weights or sum(weights) <= 0:
        return 0.0
    order = numpy.argsort(numpy.asarray(values, dtype=float))
    sorted_values = numpy.asarray(values, dtype=float)[order]
    sorted_weights = numpy.asarray(weights, dtype=float)[order]
    cumulative = numpy.cumsum(sorted_weights) / sorted_weights.sum()
    return float(numpy.interp(fraction, cumulative, sorted_values))


def weighted_summary(values: list[float], weights: list[float]) -> dict[str, float]:
    return {
        "mean": weighted_mean(values, weights),
        "std": weighted_std(values, weights),
        "median": weighted_quantile(values, weights, 0.5),
        "q10": weighted_quantile(values, weights, 0.1),
        "q90": weighted_quantile(values, weights, 0.9),
    }


def unit(vector: numpy.ndarray) -> numpy.ndarray:
    length = float(numpy.linalg.norm(vector))
    if length <= 1e-12:
        return numpy.zeros(3, dtype=float)
    return vector / length


def angle_degrees(left: numpy.ndarray, vertex: numpy.ndarray, right: numpy.ndarray) -> float:
    left_vector = left - vertex
    right_vector = right - vertex
    denominator = numpy.linalg.norm(left_vector) * numpy.linalg.norm(right_vector)
    if denominator <= 1e-12:
        return 0.0
    cosine = float(numpy.dot(left_vector, right_vector) / denominator)
    return float(math.degrees(math.acos(max(-1.0, min(1.0, cosine)))))


def enrich_context(context: dict[str, Any], posed_molecule: Any) -> dict[str, Any]:
    atoms = []
    for atom in posed_molecule.GetAtoms():
        if atom.GetIdx() == 0:
            continue
        assembly_index = context["stage1_to_assembly"][atom.GetIdx()]
        atoms.append(
            {
                "index": atom.GetIdx(),
                "element": atom.GetSymbol(),
                "atomic_num": atom.GetAtomicNum(),
                "point": context["assembly_atoms"][assembly_index]["xyz"],
                "is_aromatic": atom.GetIsAromatic(),
            }
        )
    context["atom_records"] = atoms
    path = list(Chem.GetShortestPath(posed_molecule, 0, context["reported_stage1_index"]))
    point_by_index = {atom["index"]: atom["point"] for atom in atoms}
    point_by_index[0] = context["nitrene"]
    context["tether_path_points"] = [point_by_index[index] for index in path if index in point_by_index]
    context["reactive_hydrogen_points"] = [
        atom["point"]
        for atom in atoms
        if atom["index"] in {
            neighbor.GetIdx()
            for neighbor in posed_molecule.GetAtomWithIdx(context["reported_stage1_index"]).GetNeighbors()
            if neighbor.GetSymbol() == "H"
        }
    ]
    return context


def pose_context(pose: dict[str, Any], record: dict[str, Any], posed_molecule: Any, atom_map: dict[int, int]) -> dict[str, Any]:
    context = stage2p.pose_context(pose, record, posed_molecule, atom_map)
    assembly_atoms = stage2p.stage2_interaction.parse_xyz(stage2p.stage2_interaction.resolve_path(pose["fe_bound_assembly_xyz_path"]))
    frozen_core_count = int(pose["frozen_core_atom_count"])
    stage1_to_assembly = stage2p.stage2_interaction.stage1_index_to_assembly_index(posed_molecule, frozen_core_count)
    context["assembly_atoms"] = assembly_atoms
    context["stage1_to_assembly"] = stage1_to_assembly
    return enrich_context(context, posed_molecule)


def pose_signature(pose: dict[str, Any]) -> tuple[int, ...]:
    """Geometry-only fingerprint for duplicate balancing within a stratum."""
    point_rows = [atom["point"] for atom in pose["atom_records"] if atom["atomic_num"] > 1]
    points = numpy.asarray(point_rows, dtype=float).reshape((-1, 3))
    if len(points):
        centered = points - pose["nitrene"][None, :]
        distances = numpy.linalg.norm(centered[:, None, :] - centered[None, :, :], axis=2)
        upper = distances[numpy.triu_indices_from(distances, k=1)]
    else:
        upper = numpy.array([], dtype=float)
    vector = numpy.concatenate(
        [
            numpy.asarray([pose["segment_length"], numpy.linalg.norm(pose["carbon"] - pose["nitrene"]), angle_degrees(pose["nitrene"], pose["carbon"], pose["transferred_h"])], dtype=float),
            upper[:40],
        ]
    )
    return tuple(numpy.rint(vector / CLUSTER_QUANTIZATION).astype(int).tolist())


def assign_cluster_weights(poses: list[dict[str, Any]]) -> dict[str, float]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pose in poses:
        groups[pose["stratum"]].append(pose)
    weights: dict[str, float] = {}
    for stratum, group in groups.items():
        clusters: dict[tuple[int, ...], list[dict[str, Any]]] = defaultdict(list)
        for pose in group:
            clusters[pose_signature(pose)].append(pose)
        cluster_count = max(1, len(clusters))
        for members in clusters.values():
            member_weight = 1.0 / cluster_count / len(members)
            for pose in members:
                weights[pose["pose_id"]] = member_weight
    for pose in poses:
        pose["cluster_weight"] = weights[pose["pose_id"]]
        pose["cluster_id"] = f"{pose['stratum']}:{pose_signature(pose)}"
        pose["all_weight"] = 0.5 * pose["cluster_weight"]
    return weights


def channel_atoms(pose: dict[str, Any], channel: str) -> list[dict[str, Any]]:
    atoms = pose["atom_records"]
    if channel == "all_heavy":
        return [atom for atom in atoms if atom["atomic_num"] > 1]
    if channel == "carbon":
        return [atom for atom in atoms if atom["element"] == "C"]
    if channel == "hetero":
        return [atom for atom in atoms if atom["atomic_num"] > 1 and atom["element"] not in {"C", "H"}]
    if channel == "halogen":
        return [atom for atom in atoms if atom["element"] in {"F", "Cl", "Br", "I"}]
    if channel == "hydrogen":
        return [atom for atom in atoms if atom["element"] == "H"]
    if channel == "reactive_c":
        return [atom for atom in atoms if atom["index"] == pose["reported_stage1_index"]]
    if channel == "reactive_h":
        return [atom for atom in atoms if atom["index"] == pose["transferred_hydrogen_stage1_index"]]
    raise ValueError(f"Unknown Stage 2″ channel: {channel}")


def view_frame(pose: dict[str, Any], view: str) -> tuple[numpy.ndarray, numpy.ndarray]:
    if view == "nitrene":
        return pose["nitrene"], pose["axis_n_to_h"]
    if view == "activation":
        return pose["carbon"], pose["axis_n_to_h"]
    if view == "n_to_h":
        return pose["nitrene"], pose["axis_n_to_h"]
    if view == "h_to_n":
        return pose["transferred_h"], pose["axis_h_to_n"]
    raise ValueError(f"Unknown Stage 2″ view: {view}")


def cylindrical_coordinates(points: list[dict[str, Any]], origin: numpy.ndarray, axis: numpy.ndarray) -> tuple[numpy.ndarray, numpy.ndarray]:
    if not points:
        return numpy.array([], dtype=float), numpy.array([], dtype=float)
    coordinates = numpy.asarray([atom["point"] for atom in points], dtype=float)
    relative = coordinates - origin[None, :]
    z = relative @ axis
    perpendicular = relative - z[:, None] * axis[None, :]
    rho = numpy.linalg.norm(perpendicular, axis=1)
    return z, rho


def gaussian_field(points: list[dict[str, Any]], origin: numpy.ndarray, axis: numpy.ndarray) -> numpy.ndarray:
    field = numpy.zeros((len(Z_EDGES) - 1, len(RHO_EDGES) - 1), dtype=float)
    z_centers = 0.5 * (Z_EDGES[:-1] + Z_EDGES[1:])
    rho_centers = 0.5 * (RHO_EDGES[:-1] + RHO_EDGES[1:])
    z, rho = cylindrical_coordinates(points, origin, axis)
    for index, (z_value, rho_value) in enumerate(zip(z, rho)):
        element = points[index]["element"]
        radius = VDW_RADII.get(element, 1.70)
        sigma = max(0.22, radius * 0.30)
        z_mask = numpy.abs(z_centers - z_value) <= 3.0 * sigma
        rho_mask = numpy.abs(rho_centers - rho_value) <= 3.0 * sigma
        if not z_mask.any() or not rho_mask.any():
            continue
        zz, rr = numpy.meshgrid(z_centers[z_mask], rho_centers[rho_mask], indexing="ij")
        kernel = numpy.exp(-0.5 * (((zz - z_value) / sigma) ** 2 + ((rr - rho_value) / sigma) ** 2))
        field[numpy.ix_(z_mask, rho_mask)] += kernel
    return field


def dihedral_degrees(points: list[numpy.ndarray]) -> float:
    if len(points) < 4:
        return 0.0
    p0, p1, p2, p3 = [numpy.asarray(point, dtype=float) for point in points[-4:]]
    b0 = -(p1 - p0)
    b1 = unit(p2 - p1)
    b2 = p3 - p2
    v = b0 - numpy.dot(b0, b1) * b1
    w = b2 - numpy.dot(b2, b1) * b1
    if numpy.linalg.norm(v) <= 1e-12 or numpy.linalg.norm(w) <= 1e-12:
        return 0.0
    return float(math.degrees(math.atan2(numpy.dot(numpy.cross(b1, v), w), numpy.dot(v, w))))


def normalize_field(field: numpy.ndarray) -> numpy.ndarray:
    total = float(field.sum())
    return field / total if total > 0 else field


def field_entropy(field: numpy.ndarray) -> float:
    normalized = normalize_field(field).ravel()
    nonzero = normalized[normalized > 0]
    return float(-numpy.sum(nonzero * numpy.log(nonzero))) if len(nonzero) else 0.0


def field_relationship(left: numpy.ndarray, right: numpy.ndarray) -> dict[str, float]:
    left_probability = normalize_field(left)
    right_probability = normalize_field(right)
    midpoint = 0.5 * (left_probability + right_probability)
    left_nonzero = left_probability > 0
    right_nonzero = right_probability > 0
    js = 0.5 * numpy.sum(left_probability[left_nonzero] * numpy.log(left_probability[left_nonzero] / midpoint[left_nonzero]))
    js += 0.5 * numpy.sum(right_probability[right_nonzero] * numpy.log(right_probability[right_nonzero] / midpoint[right_nonzero]))
    difference = left_probability - right_probability
    cosine_denominator = numpy.linalg.norm(left_probability) * numpy.linalg.norm(right_probability)
    cosine = float(numpy.sum(left_probability * right_probability) / cosine_denominator) if cosine_denominator else 0.0
    return {"l1": float(numpy.sum(numpy.abs(difference))), "js": float(js), "cosine": cosine, "mean_abs": float(numpy.mean(numpy.abs(difference)))}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def flex_values(pose: dict[str, Any]) -> dict[str, float]:
    n_to_c = float(numpy.linalg.norm(pose["carbon"] - pose["nitrene"]))
    c_to_h = float(numpy.linalg.norm(pose["transferred_h"] - pose["carbon"]))
    n_to_h = float(pose["segment_length"])
    corridor = stage2p.directed_descriptor(pose["points"]["all_heavy"], pose["nitrene"], pose["axis_n_to_h"], pose["segment_length"])
    axis_z, axis_rho = cylindrical_coordinates(pose["atom_records"], pose["nitrene"], pose["axis_n_to_h"])
    reactive_h_distances = sorted(float(numpy.linalg.norm(point - pose["nitrene"])) for point in pose.get("reactive_hydrogen_points", [pose["transferred_h"]]))
    h_gap = reactive_h_distances[1] - reactive_h_distances[0] if len(reactive_h_distances) > 1 else 0.0
    return {
        "n_to_h_distance": n_to_h,
        "n_to_c_distance": n_to_c,
        "c_to_h_distance": c_to_h,
        "n_c_h_angle": angle_degrees(pose["nitrene"], pose["carbon"], pose["transferred_h"]),
        "tether_dihedral": dihedral_degrees(pose.get("tether_path_points", [])),
        "two_h_distance_gap": h_gap,
        "preferred_h_distance": reactive_h_distances[0] if reactive_h_distances else 0.0,
        "corridor_fraction": corridor["corridor_fraction"],
        "corridor_axial_mean": corridor["axial_mean"],
        "parallel_motion_std": float(numpy.std(axis_z)) if len(axis_z) else 0.0,
        "perpendicular_motion_std": float(numpy.std(axis_rho)) if len(axis_rho) else 0.0,
    }


def pose_weight(pose: dict[str, Any], stratum: str) -> float:
    if stratum == "all_200":
        return float(pose["all_weight"])
    return float(pose["cluster_weight"])


def aggregate_pose_values(poses: list[dict[str, Any]], values: list[float], stratum: str) -> dict[str, float]:
    weights = [pose_weight(pose, stratum) for pose in poses]
    return weighted_summary(values, weights)


def render_density_svg(substrate_id: str, arrays: dict[str, numpy.ndarray], path: Path) -> None:
    width, height = 1100, 650
    panels = [("nitrene", "Nitrene"), ("activation", "Activation C"), ("n_to_h", "N→H"), ("h_to_n", "H→N")]
    panel_w, panel_h = 260, 420
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#f7f4ed"/>',
        f'<text x="24" y="34" font-family="Arial" font-size="23" font-weight="700">Stage 2pp {substrate_id}</text>',
        '<text x="24" y="57" font-family="Arial" font-size="13">Numerical vdW-scaled occupancy; blue = top 100, red = bottom 100, gray = top-minus-bottom.</text>',
    ]
    for panel_index, (view, title) in enumerate(panels):
        x0 = 24 + panel_index * (panel_w + 10)
        y0 = 90
        parts.append(f'<rect x="{x0}" y="{y0}" width="{panel_w}" height="{panel_h}" fill="#fff" stroke="#b8b1a6"/>')
        parts.append(f'<text x="{x0 + 8}" y="{y0 + 20}" font-family="Arial" font-size="14" font-weight="700">{title}</text>')
        top = normalize_field(arrays[f"{view}__all_heavy__top_100"])
        bottom = normalize_field(arrays[f"{view}__all_heavy__bottom_100"])
        difference = arrays[f"{view}__all_heavy__top_minus_bottom"]
        maximum = max(float(top.max()), float(bottom.max()), 1e-12)
        rows, columns = top.shape
        cell_w = (panel_w - 20) / columns
        cell_h = (panel_h - 45) / rows
        for row_index in range(rows):
            for column_index in range(columns):
                top_value = float(top[row_index, column_index]) / maximum
                bottom_value = float(bottom[row_index, column_index]) / maximum
                diff_value = float(difference[row_index, column_index])
                if abs(diff_value) > 0.01:
                    fill = "#2166ac" if diff_value > 0 else "#b2182b"
                    opacity = min(0.85, 0.12 + 2.0 * abs(diff_value))
                elif top_value > 0 or bottom_value > 0:
                    fill = "#777777"
                    opacity = min(0.65, 0.08 + 0.7 * max(top_value, bottom_value))
                else:
                    continue
                x = x0 + 10 + column_index * cell_w
                y = y0 + 30 + (rows - row_index - 1) * cell_h
                parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_w + 0.3:.2f}" height="{cell_h + 0.3:.2f}" fill="{fill}" opacity="{opacity:.3f}"/>')
        parts.append(f'<text x="{x0 + 8}" y="{y0 + panel_h - 8}" font-family="Arial" font-size="10">axial z / radial ρ</text>')
    parts.append('</svg>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(parts), encoding="utf-8")


def build_feature_row(record: dict[str, Any], report: dict[str, Any], density_dir: Path, svg_dir: Path) -> dict[str, Any]:
    posed_molecule = stage2p.stage2_interaction.stage1_pose_molecule(record["structure"]["nitrene_smiles"])
    atom_map = stage2p.stage2_interaction.map_ids_to_stage1_atom_indices(record, posed_molecule)
    contexts = [pose_context(pose, record, posed_molecule, atom_map) for pose in report["pose_records"]]
    if len(contexts) != 200:
        raise ValueError(f"{record['substrate_id']}: expected 200 retained poses, found {len(contexts)}")
    poses = [stage2p.build_pose_features(context) for context in contexts]
    assign_cluster_weights(poses)
    for pose in poses:
        pose["flexibility"] = flex_values(pose)

    arrays: dict[str, numpy.ndarray] = {}
    stability: dict[str, float] = {}
    convergence: dict[str, float] = {}
    geometry: dict[str, float] = {}
    relational: dict[str, float] = {}
    flexibility: dict[str, float] = {}
    grouped = {stratum: [pose for pose in poses if pose["stratum"] == stratum] for stratum in ("top_100", "bottom_100")}
    grouped["all_200"] = poses

    for view in VIEWS:
        for channel in CHANNELS:
            field_by_stratum: dict[str, numpy.ndarray] = {}
            for stratum in STRATA:
                field = numpy.zeros((len(Z_EDGES) - 1, len(RHO_EDGES) - 1), dtype=float)
                second_moment = numpy.zeros_like(field)
                for pose in grouped[stratum]:
                    origin, axis = view_frame(pose, view)
                    pose_field = gaussian_field(channel_atoms(pose, channel), origin, axis)
                    if channel != "all_heavy":
                        pose_field = pose_field / max(float(pose["denominator"]), 1.0)
                    weight = pose_weight(pose, stratum)
                    field += weight * pose_field
                    second_moment += weight * pose_field * pose_field
                field_by_stratum[stratum] = field
                arrays[f"{view}__{channel}__{stratum}"] = field
                arrays[f"{view}__{channel}__{stratum}__variance"] = numpy.maximum(second_moment - field * field, 0.0)
                arrays[f"{view}__{channel}__{stratum}__axial_profile"] = field.sum(axis=1)
                arrays[f"{view}__{channel}__{stratum}__radial_profile"] = field.sum(axis=0)
                prefix = f"stage2pp:occupancy:{view}:{channel}:{stratum}"
                geometry[f"{prefix}:mass"] = float(field.sum())
                geometry[f"{prefix}:peak"] = float(field.max())
                geometry[f"{prefix}:entropy"] = field_entropy(field)
                geometry[f"{prefix}:variance_mean"] = float(arrays[f"{view}__{channel}__{stratum}__variance"].mean())
            difference = normalize_field(field_by_stratum["top_100"]) - normalize_field(field_by_stratum["bottom_100"])
            arrays[f"{view}__{channel}__top_minus_bottom"] = difference
            for relation_name, relation_value in field_relationship(field_by_stratum["top_100"], field_by_stratum["bottom_100"]).items():
                relational[f"stage2pp:occupancy_relation:{view}:{channel}:top_bottom:{relation_name}"] = relation_value

    for stratum in STRATA:
        members = grouped[stratum]
        for value_name in flex_values(members[0]):
            values = [pose["flexibility"][value_name] for pose in members]
            summary = aggregate_pose_values(members, values, stratum)
            for summary_name, summary_value in summary.items():
                flexibility[f"stage2pp:flexibility:{value_name}:{stratum}:{summary_name}"] = summary_value
    for value_name in flex_values(poses[0]):
        top_values = [pose["flexibility"][value_name] for pose in grouped["top_100"]]
        bottom_values = [pose["flexibility"][value_name] for pose in grouped["bottom_100"]]
        relational[f"stage2pp:flexibility_relation:{value_name}:top_bottom:wasserstein"] = float(wasserstein_distance(top_values, bottom_values))
        relational[f"stage2pp:flexibility_relation:{value_name}:top_bottom:energy_distance"] = float(energy_distance(top_values, bottom_values))
        all_scores = [pose["score_rank"] for pose in poses]
        all_values = [pose["flexibility"][value_name] for pose in poses]
        relational[f"stage2pp:flexibility_relation:{value_name}:uff_rank_spearman"] = stage2p.safe_spearman(all_scores, all_values)

    for view in ("nitrene", "activation", "n_to_h", "h_to_n"):
        top = grouped["top_100"]
        bottom = grouped["bottom_100"]
        top_radial = [pose[f"nitrene_features"]["all_heavy"]["radial_mean"] for pose in top]
        bottom_radial = [pose[f"nitrene_features"]["all_heavy"]["radial_mean"] for pose in bottom]
        relational[f"stage2pp:pose_relation:{view}:radial_mean:wasserstein"] = float(wasserstein_distance(top_radial, bottom_radial))
        relational[f"stage2pp:pose_relation:{view}:radial_mean:uff_rank_spearman"] = stage2p.safe_spearman([pose["score_rank"] for pose in poses], [pose["nitrene_features"]["all_heavy"]["radial_mean"] for pose in poses])

        for stratum in STRATA:
            members = grouped[stratum]
            midpoint = len(members) // 2
            if midpoint:
                first = numpy.mean([gaussian_field(channel_atoms(pose, "all_heavy"), *view_frame(pose, view)) for pose in members[:midpoint]], axis=0)
                second = numpy.mean([gaussian_field(channel_atoms(pose, "all_heavy"), *view_frame(pose, view)) for pose in members[midpoint:]], axis=0)
                stability[f"{view}:{stratum}:split_half_l1"] = field_relationship(first, second)["l1"]

    for stratum in ("top_100", "bottom_100"):
        members = grouped[stratum]
        full = numpy.mean([gaussian_field(channel_atoms(pose, "all_heavy"), *view_frame(pose, "nitrene")) for pose in members], axis=0)
        for count in (25, 50, 100):
            if len(members) >= count:
                partial = numpy.mean([gaussian_field(channel_atoms(pose, "all_heavy"), *view_frame(pose, "nitrene")) for pose in members[:count]], axis=0)
                convergence[f"{stratum}:first_{count}_vs_full_l1"] = field_relationship(partial, full)["l1"]

    density_dir.mkdir(parents=True, exist_ok=True)
    svg_dir.mkdir(parents=True, exist_ok=True)
    geometry["stage2pp:occupancy:heavy_atom_count"] = weighted_mean([float(pose["denominator"]) for pose in poses], [pose["all_weight"] for pose in poses])
    density_path = density_dir / f"{record['substrate_id']}.npz"
    numpy.savez_compressed(density_path, **arrays)
    svg_path = svg_dir / f"{record['substrate_id']}.svg"
    render_density_svg(record["substrate_id"], arrays, svg_path)

    target = record.get("outcome", {}).get("ee_percent")
    feature_blocks = {"stage2pp_geometry": geometry, "stage2pp_relational": relational, "stage2pp_flexibility": flexibility}
    return {
        "schema_version": "stage2pp-occupancy-flexibility-features-v1",
        "substrate_id": record["substrate_id"],
        "reaction_id": record["reaction_id"],
        "target_name": "ee_percent_magnitude",
        "target_value": None if target is None else float(target),
        "feature_blocks": feature_blocks,
        "feature_count": sum(len(block) for block in feature_blocks.values()),
        "artifacts": {"density_npz": display_path(density_path), "svg": display_path(svg_path), "density_sha256": file_sha256(density_path), "svg_sha256": file_sha256(svg_path)},
        "diagnostics": {"field_split_half_stability": stability, "field_convergence": convergence},
        "pose_audit": [
            {
                "pose_id": pose["pose_id"],
                "score": pose["score"],
                "score_rank": pose["score_rank"],
                "stratum": pose["stratum"],
                "cluster_id": pose["cluster_id"],
                "cluster_weight": pose["cluster_weight"],
                "all_weight": pose["all_weight"],
            }
            for pose in poses
        ],
        "provenance": {
            "pose_count": 200,
            "pose_strata": {"top_100": 100, "bottom_100": 100, "all_200": 200},
            "catalyst_atoms_in_density_fields": False,
            "activation_site_policy": "fixed_five_membered_ring_connectivity",
            "coordinate_convention": "azimuth_free_cylindrical_nitrene_transferred_h_axis",
            "occupancy_type": "vdw_scaled_gaussian_atom_occupancy",
            "vdw_radii_angstrom": VDW_RADII,
            "grid_z_edges_angstrom": Z_EDGES.tolist(),
            "grid_rho_edges_angstrom": RHO_EDGES.tolist(),
            "pose_weighting": "equal_total_weight_per_geometry_cluster_within_stratum",
            "cluster_quantization_angstrom": CLUSTER_QUANTIZATION,
            "cluster_count_by_stratum": {stratum: len({pose["cluster_id"] for pose in grouped[stratum]}) for stratum in ("top_100", "bottom_100")},
            "force_field": report.get("pose_generation_run", {}).get("force_field", "uff"),
        },
    }


def canonical_records(records_path: Path) -> list[dict[str, Any]]:
    return [
        row
        for row in read_jsonl(records_path)
        if row.get("reaction_center", {}).get("review_status") == "checked"
    ]


def report_map(report_dir: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for path in sorted(report_dir.glob("stage-1-smoke-*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        substrate_ids = report.get("pose_generation_run", {}).get("substrate_ids", [])
        substrate_id = substrate_ids[0] if len(substrate_ids) == 1 else report.get("substrate_record", {}).get("substrate_id")
        if substrate_id:
            result[substrate_id] = report
    return result


def generate_features(records_path: Path, report_dir: Path, density_dir: Path, svg_dir: Path) -> list[dict[str, Any]]:
    records = canonical_records(records_path)
    reports = report_map(report_dir)
    missing = sorted({row["substrate_id"] for row in records} - set(reports))
    if missing:
        raise ValueError(f"Missing Stage 1 reports: {', '.join(missing)}")
    return [build_feature_row(record, reports[record["substrate_id"]], density_dir, svg_dir) for record in sorted(records, key=lambda row: row["substrate_id"])]


def flatten_numeric(blocks: dict[str, dict[str, float]]) -> dict[str, float]:
    result = {}
    for block_name, block in blocks.items():
        for key, value in block.items():
            if math.isfinite(float(value)):
                result[f"{block_name}:{key}"] = float(value)
    return result


def feature_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    return {row["substrate_id"]: flatten_numeric(row["feature_blocks"]) for row in rows}


def write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    maps = feature_map(rows)
    feature_names = sorted(next(iter(maps.values()))) if maps else []
    write_json(path, {
        "schema_version": "stage2pp-feature-manifest-v1",
        "representation": "Stage 2″ persistent atomic occupancy and reaction-corridor flexibility",
        "target": "ee_percent_magnitude",
        "substrate_count": len(rows),
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "pose_strata": {"top_100": 100, "bottom_100": 100, "all_200": 200},
        "occupancy_artifacts_persisted": True,
        "svg_derived_from_numerical_arrays": True,
        "xyz_cache_expanded": False,
        "force_fields": sorted({row.get("provenance", {}).get("force_field", "uff") for row in rows}),
    })


def write_trends(path: Path, rows: list[dict[str, Any]]) -> None:
    model_rows = [row for row in rows if row.get("target_value") is not None and row["substrate_id"] not in EXCLUDED_EE]
    maps = feature_map(model_rows)
    ids = sorted(maps)
    target = numpy.asarray([next(row["target_value"] for row in model_rows if row["substrate_id"] == substrate_id) for substrate_id in ids], dtype=float)
    names = sorted(maps[ids[0]]) if ids else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["feature_name", "mean", "std", "spearman_ee", "pearson_ee"], lineterminator="\n")
        writer.writeheader()
        for name in names:
            values = numpy.asarray([maps[substrate_id][name] for substrate_id in ids], dtype=float)
            writer.writerow({"feature_name": name, "mean": float(values.mean()), "std": float(values.std()), "spearman_ee": finite(spearmanr(values, target).statistic) if len(set(values)) > 1 else 0.0, "pearson_ee": finite(numpy.corrcoef(values, target)[0, 1]) if len(set(values)) > 1 else 0.0})


def model_rows(
    records_path: Path,
    stage2p_path: Path,
    stage2pp_rows: list[dict[str, Any]],
    pose_summary_path: Path = DEFAULT_POSE_SUMMARY,
    pose_interaction_path: Path = DEFAULT_POSE_INTERACTION,
    pose_folding_path: Path = DEFAULT_POSE_FOLDING,
) -> dict[str, list[dict[str, Any]]]:
    records = {row["substrate_id"]: row for row in canonical_records(records_path) if row.get("outcome", {}).get("ee_percent") is not None and row["substrate_id"] not in EXCLUDED_EE}
    stage2pp_by_id = feature_map([row for row in stage2pp_rows if row["substrate_id"] in records])
    stage2p_by_id = {row["substrate_id"]: stage2p.flatten_numeric({**row["feature_blocks"]["stage2p_geometry"], **row["feature_blocks"]["stage2p_relational"]}) for row in read_jsonl(stage2p_path) if row["substrate_id"] in records}
    stage2_alt_rows, _, _, _ = stage2_folding.feature_rows_for_policy(
        records_path,
        pose_summary_path,
        pose_interaction_path,
        pose_folding_path,
        "summary_interaction_folding",
    )
    stage2_alt_by_id = {row["substrate_id"]: row["features"] for row in stage2_alt_rows if row["substrate_id"] in records}
    missing = sorted(set(records) - set(stage2p_by_id) - set(stage2pp_by_id))
    if missing:
        raise ValueError(f"Missing model feature rows: {', '.join(missing)}")
    result = {}
    combined = {sid: {**stage2p_by_id[sid], **stage2pp_by_id[sid]} for sid in records}
    alt_plus_stage2pp = {sid: {**stage2_alt_by_id[sid], **stage2pp_by_id[sid]} for sid in records}
    for name, features in (("stage2_alt", stage2_alt_by_id), ("stage2p", stage2p_by_id), ("stage2pp", stage2pp_by_id), ("stage2p_plus_stage2pp", combined), ("stage2_alt_plus_stage2pp", alt_plus_stage2pp)):
        result[name] = [
            {
                "substrate_id": sid,
                "family_id": records[sid]["family"]["family_id"],
                "target_name": "ee",
                "target_value": float(records[sid]["outcome"]["ee_percent"]),
                "features": features[sid],
                "fingerprint": stage2_full_scope.fingerprint(stage2_full_scope.molecule_from_record(records[sid])),
            }
            for sid in sorted(records)
        ]
    return result


def summarize_predictions(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {}
    for feature_set in sorted({row["feature_set"] for row in predictions}):
        rows = [row for row in predictions if row["feature_set"] == feature_set]
        by_model = {}
        for model_name in sorted({row["model_name"] for row in rows}):
            selected = [row for row in rows if row["model_name"] == model_name]
            observed = numpy.asarray([row["observed_target_value"] for row in selected], dtype=float)
            predicted = numpy.asarray([row["prediction"] for row in selected], dtype=float)
            by_model[model_name] = {"record_count": len(selected), "mae": float(numpy.mean(numpy.abs(observed - predicted))), "rmse": float(numpy.sqrt(numpy.mean((observed - predicted) ** 2))), "within_20_count": int(numpy.sum(numpy.abs(observed - predicted) <= 20.0))}
        summary[feature_set] = by_model
    return summary


def paired_bootstrap_report(predictions: list[dict[str, Any]], baseline_name: str, candidate_name: str, model_name: str = "elastic_net", seed: int = 20260806) -> dict[str, Any]:
    baseline = {row["target_substrate_id"]: float(row["prediction"]) for row in predictions if row["feature_set"] == baseline_name and row["model_name"] == model_name}
    candidate = {row["target_substrate_id"]: float(row["prediction"]) for row in predictions if row["feature_set"] == candidate_name and row["model_name"] == model_name}
    observed = {row["target_substrate_id"]: float(row["observed_target_value"]) for row in predictions if row["feature_set"] == baseline_name and row["model_name"] == model_name}
    ids = sorted(set(baseline) & set(candidate) & set(observed))
    if not ids:
        return {"baseline": baseline_name, "candidate": candidate_name, "model": model_name, "record_count": 0}
    delta = numpy.asarray([abs(candidate[sid] - observed[sid]) - abs(baseline[sid] - observed[sid]) for sid in ids], dtype=float)
    rng = numpy.random.default_rng(seed)
    bootstrap = numpy.asarray([delta[rng.integers(0, len(delta), len(delta))].mean() for _ in range(10000)], dtype=float)
    return {
        "baseline": baseline_name,
        "candidate": candidate_name,
        "model": model_name,
        "record_count": len(ids),
        "mean_delta_mae_candidate_minus_baseline": float(delta.mean()),
        "bootstrap_ci_95_low": float(numpy.quantile(bootstrap, 0.025)),
        "bootstrap_ci_95_high": float(numpy.quantile(bootstrap, 0.975)),
        "required_improvement_ee_points": -1.0,
        "passes_prespecified_gate": bool(delta.mean() <= -1.0 and numpy.quantile(bootstrap, 0.975) < 0.0),
    }


def stable_model_grid() -> dict[str, list[Any]]:
    """Regularized comparison grid suitable for 38 records and dense fields."""
    return {
        "ridge_regression": [
            make_pipeline(StandardScaler(), Ridge(alpha=alpha, solver="lsqr"))
            for alpha in (10.0, 100.0, 1000.0, 10000.0)
        ],
        "elastic_net": [
            make_pipeline(
                StandardScaler(),
                ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=50000, tol=1e-3, random_state=0, selection="cyclic"),
            )
            for alpha in (0.1, 1.0, 10.0, 100.0)
            for l1_ratio in (0.2, 0.5, 0.8, 1.0)
        ],
        "lightgbm": [
            stage2_full_scope.lightgbm.LGBMRegressor(
                n_estimators=n_estimators,
                learning_rate=learning_rate,
                num_leaves=num_leaves,
                min_child_samples=3,
                max_depth=3,
                reg_lambda=1.0,
                random_state=0,
                verbosity=-1,
            )
            for n_estimators in (25, 75)
            for learning_rate in (0.03, 0.1)
            for num_leaves in (3, 7)
        ],
        "gaussian_process": [
            make_pipeline(
                StandardScaler(),
                GaussianProcessRegressor(
                    kernel=ConstantKernel(1.0) * RBF(length_scale=length_scale) + WhiteKernel(noise_level=noise_level),
                    alpha=1e-5,
                    normalize_y=True,
                    random_state=0,
                    n_restarts_optimizer=0,
                ),
            )
            for length_scale in (0.5, 1.0, 2.0)
            for noise_level in (1.0, 10.0)
        ],
    }


def run_model_comparison(
    records_path: Path,
    stage2p_path: Path,
    stage2pp_rows: list[dict[str, Any]],
    pose_summary_path: Path = DEFAULT_POSE_SUMMARY,
    pose_interaction_path: Path = DEFAULT_POSE_INTERACTION,
    pose_folding_path: Path = DEFAULT_POSE_FOLDING,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    all_rows = model_rows(
        records_path,
        stage2p_path,
        stage2pp_rows,
        pose_summary_path,
        pose_interaction_path,
        pose_folding_path,
    )
    predictions: list[dict[str, Any]] = []
    requested_ids = {
        row["substrate_id"]
        for row in canonical_records(records_path)
        if row.get("outcome", {}).get("ee_percent") is not None and row["substrate_id"] not in EXCLUDED_EE
    }
    modeled_ids = {row["substrate_id"] for rows in all_rows.values() for row in rows}
    excluded_ids = sorted(requested_ids - modeled_ids)
    reports = {
        "schema_version": "stage2pp-model-comparison-v1",
        "target": "ee_percent_magnitude",
        "cohort": {"record_count": len(modeled_ids), "excluded": excluded_ids},
        "feature_sets": {},
    }
    original_grid = stage2_full_scope.model_grid
    original_fit_predict = stage2_full_scope.fit_predict

    def bounded_fit_predict(estimator: Any, x_train: numpy.ndarray, y_train: numpy.ndarray, x_pred: numpy.ndarray) -> tuple[numpy.ndarray, numpy.ndarray | None]:
        prediction, uncertainty = original_fit_predict(estimator, x_train, y_train, x_pred)
        return numpy.clip(prediction, 0.0, 100.0), uncertainty

    stage2_full_scope.model_grid = stable_model_grid
    stage2_full_scope.fit_predict = bounded_fit_predict
    try:
        for feature_set, rows in all_rows.items():
            feature_names = sorted({key for row in rows for key in row["features"]})
            family_predictions, splits = stage2_full_scope.benchmark(rows, feature_names, feature_set=feature_set, split_mode="family_holdout")
            predictions.extend(family_predictions)
            reports["feature_sets"][feature_set] = {"feature_count": len(feature_names), "family_split_count": len(splits)}
    finally:
        stage2_full_scope.model_grid = original_grid
        stage2_full_scope.fit_predict = original_fit_predict
    reports["metrics"] = summarize_predictions(predictions)
    reports["paired_uncertainty"] = {
        "stage2p_to_stage2pp": paired_bootstrap_report(predictions, "stage2p", "stage2p_plus_stage2pp"),
        "stage2_alt_to_stage2pp": paired_bootstrap_report(predictions, "stage2_alt", "stage2_alt_plus_stage2pp"),
    }
    reports["paired_gate"] = reports["paired_uncertainty"]["stage2p_to_stage2pp"]
    return reports, predictions


def write_predictions(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fields = sorted(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--stage1-report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--stage2p-features", type=Path, default=DEFAULT_STAGE2P_FEATURES)
    parser.add_argument("--pose-summary", type=Path, default=DEFAULT_POSE_SUMMARY)
    parser.add_argument("--pose-interaction", type=Path, default=DEFAULT_POSE_INTERACTION)
    parser.add_argument("--pose-folding", type=Path, default=DEFAULT_POSE_FOLDING)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--trends", type=Path, default=DEFAULT_TRENDS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    density_dir = args.output_dir / "density"
    svg_dir = args.output_dir / "svg"
    rows = generate_features(args.records, args.stage1_report_dir, density_dir, svg_dir)
    write_jsonl(args.features, rows)
    write_manifest(args.manifest, rows)
    write_trends(args.trends, rows)
    reports, predictions = run_model_comparison(
        args.records,
        args.stage2p_features,
        rows,
        args.pose_summary,
        args.pose_interaction,
        args.pose_folding,
    )
    write_json(args.metrics, reports)
    write_predictions(args.predictions, predictions)
    print(f"Wrote Stage 2″ features for {len(rows)} substrates")
    print(f"Wrote Stage 2″ model comparison to {args.metrics}")


if __name__ == "__main__":
    main()

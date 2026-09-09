#!/usr/bin/env python3
"""Build and benchmark the Stage 2p catalyst-stripped reaction-axis representation.

Stage 2p keeps only substrate atoms in its density fields, retains the Stage 1
nitrene N and selected transferred H as reaction-center anchors, and aggregates
200 retained poses into top-100, bottom-100, and all-pose summaries. Rendered
SVGs and per-pose field arrays are deliberately created inside a temporary
directory and are removed before the command returns.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import tempfile
import warnings
from pathlib import Path
from typing import Any, Iterable

import numpy
from rdkit import Chem
from scipy.stats import energy_distance, spearmanr, wasserstein_distance
from sklearn.linear_model import ElasticNet, ElasticNetCV
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
STAGE2_INTERACTION = ROOT / "scripts/stage2_pose_interaction.py"
STAGE2_FOLDING = ROOT / "scripts/stage2_folding_feature_experiment.py"
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_REPORT_DIR = ROOT / "data/jacs_2025/stage1/panel"
DEFAULT_POSE_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"
DEFAULT_POSE_INTERACTION = ROOT / "data/jacs_2025/stage2/features/pose-interaction.jsonl"
DEFAULT_POSE_FOLDING = ROOT / "data/jacs_2025/stage2/features/pose-folding-features.jsonl"
DEFAULT_FEATURES = ROOT / "data/jacs_2025/stage2/features/stage2p-features.jsonl"
DEFAULT_MANIFEST = ROOT / "data/jacs_2025/stage2/features/stage2p-manifest.json"
DEFAULT_METRICS = ROOT / "data/jacs_2025/stage2/modeling/stage2p-model-metrics.json"
DEFAULT_PREDICTIONS = ROOT / "data/jacs_2025/stage2/modeling/stage2p-predictions.csv"
DEFAULT_TRENDS = ROOT / "data/jacs_2025/stage2/modeling/stage2p-trends.csv"

STRATA = ("top_100", "bottom_100", "all_200")
FIELD_STD_KEYS = ()
RADIAL_CENTERS = numpy.array([1.0, 2.0, 3.0, 4.0, 5.5, 7.0, 9.0], dtype=float)
RADIAL_WIDTHS = numpy.array([0.70, 0.70, 0.75, 0.80, 0.95, 1.10, 1.30], dtype=float)
LEGENDRE_ORDERS = (1, 2, 3, 4)
MAX_NEW_FEATURES = 250


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


stage2_interaction = load_module("stage2_pose_interaction_for_stage2p", STAGE2_INTERACTION)
stage2_folding = load_module("stage2_folding_for_stage2p", STAGE2_FOLDING)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finite(value: float | None) -> float:
    return float(value) if value is not None and math.isfinite(float(value)) else 0.0


def quantile(values: list[float], fraction: float) -> float:
    return float(numpy.quantile(values, fraction)) if values else 0.0


def mean_or_zero(values: list[float]) -> float:
    return float(numpy.mean(values)) if values else 0.0


def std_or_zero(values: list[float]) -> float:
    return float(numpy.std(values)) if values else 0.0


def unit(vector: numpy.ndarray) -> numpy.ndarray:
    length = float(numpy.linalg.norm(vector))
    if length <= 1e-12:
        raise ValueError("Cannot construct a reaction axis from coincident anchors")
    return vector / length


def legendre(order: int, values: numpy.ndarray) -> numpy.ndarray:
    if order == 1:
        return values
    if order == 2:
        return 0.5 * (3.0 * values * values - 1.0)
    if order == 3:
        return 0.5 * (5.0 * values**3 - 3.0 * values)
    if order == 4:
        return (35.0 * values**4 - 30.0 * values**2 + 3.0) / 8.0
    raise ValueError(f"Unsupported Legendre order: {order}")


def radial_basis(values: numpy.ndarray) -> tuple[float, float]:
    if values.size == 0:
        return 0.0, 0.0
    responses = numpy.exp(-0.5 * ((values[:, None] - RADIAL_CENTERS[None, :]) / RADIAL_WIDTHS[None, :]) ** 2)
    near = float(responses[:, :3].mean())
    far = float(responses[:, 4:].mean())
    return near, far


def point_geometry(points: list[numpy.ndarray], origin: numpy.ndarray, axis: numpy.ndarray) -> dict[str, Any]:
    if not points:
        return {"r": numpy.array([], dtype=float), "rho": numpy.array([], dtype=float), "z": numpy.array([], dtype=float), "cos": numpy.array([], dtype=float)}
    coordinates = numpy.asarray(points, dtype=float)
    relative = coordinates - origin[None, :]
    z = relative @ axis
    perpendicular = relative - z[:, None] * axis[None, :]
    rho = numpy.linalg.norm(perpendicular, axis=1)
    r = numpy.linalg.norm(relative, axis=1)
    cosine = numpy.divide(z, r, out=numpy.zeros_like(z), where=r > 1e-12)
    return {"r": r, "rho": rho, "z": z, "cos": cosine}


def field_descriptor(points: list[numpy.ndarray], origin: numpy.ndarray, axis: numpy.ndarray, denominator: int) -> dict[str, float]:
    geometry = point_geometry(points, origin, axis)
    r = geometry["r"]
    cosine = geometry["cos"]
    if r.size == 0:
        return {"mass": 0.0, "radial_mean": 0.0, "radial_q90": 0.0, "near_response": 0.0, "angular_even_norm": 0.0, "angular_odd_norm": 0.0}
    even = numpy.array([numpy.mean(legendre(order, cosine)) for order in (2, 4)], dtype=float)
    odd = numpy.array([numpy.mean(legendre(order, cosine)) for order in (1, 3)], dtype=float)
    near, _ = radial_basis(r)
    return {
        "mass": float(r.size / max(denominator, 1)),
        "radial_mean": float(numpy.mean(r)),
        "radial_q90": quantile(r.tolist(), 0.90),
        "near_response": near,
        "angular_even_norm": float(numpy.linalg.norm(even)),
        "angular_odd_norm": float(numpy.linalg.norm(odd)),
    }


def directed_descriptor(
    points: list[numpy.ndarray],
    origin: numpy.ndarray,
    axis: numpy.ndarray,
    segment_length: float,
) -> dict[str, float]:
    geometry = point_geometry(points, origin, axis)
    z = geometry["z"]
    rho = geometry["rho"]
    if z.size == 0:
        return {"axial_mean": 0.0, "axial_std": 0.0, "axial_q90": 0.0, "corridor_fraction": 0.0}
    corridor = (z >= 0.0) & (z <= segment_length) & (rho <= 2.5)
    return {
        "axial_mean": float(numpy.mean(z)),
        "axial_std": float(numpy.std(z)),
        "axial_q90": quantile(z.tolist(), 0.90),
        "corridor_fraction": float(numpy.mean(corridor)),
    }


def pose_stratum(pose: dict[str, Any]) -> str:
    return "top_100" if pose["selection_bucket"] == "low_energy" else "bottom_100"


def report_substrate_id(report: dict[str, Any]) -> str | None:
    ids = report.get("pose_generation_run", {}).get("substrate_ids", [])
    if len(ids) == 1:
        return ids[0]
    return report.get("substrate_record", {}).get("substrate_id")


def pose_context(pose: dict[str, Any], record: dict[str, Any], posed_molecule: Chem.Mol, atom_map: dict[int, int]) -> dict[str, Any]:
    assembly_atoms = stage2_interaction.parse_xyz(stage2_interaction.resolve_path(pose["fe_bound_assembly_xyz_path"]))
    frozen_core_count = int(pose["frozen_core_atom_count"])
    stage1_to_assembly = stage2_interaction.stage1_index_to_assembly_index(posed_molecule, frozen_core_count)
    reported_map_id = record["reaction_center"]["reported_reactive_site"]["atom_map_id"]
    reported_index = atom_map[reported_map_id]
    transferred_h_index = stage2_interaction.nearest_reported_hydrogen_index(
        posed_molecule,
        reported_index,
        assembly_atoms,
        stage1_to_assembly,
    )
    nitrene = assembly_atoms[stage1_to_assembly[0]]["xyz"]
    carbon = assembly_atoms[stage1_to_assembly[reported_index]]["xyz"]
    transferred_h = assembly_atoms[stage1_to_assembly[transferred_h_index]]["xyz"]
    axis_n_to_h = unit(transferred_h - nitrene)
    axis_h_to_n = -axis_n_to_h
    substrate_points: dict[str, list[numpy.ndarray]] = {
        "all_heavy": [],
        "carbon": [],
        "hetero": [],
        "aromatic": [],
        "halogen": [],
        "reactive_h": [transferred_h],
    }
    atom_index_to_point = {}
    for atom in posed_molecule.GetAtoms():
        if atom.GetIdx() == 0:
            continue
        assembly_index = stage1_to_assembly[atom.GetIdx()]
        point = assembly_atoms[assembly_index]["xyz"]
        atom_index_to_point[atom.GetIdx()] = point
        if atom.GetAtomicNum() > 1:
            substrate_points["all_heavy"].append(point)
            if atom.GetSymbol() == "C":
                substrate_points["carbon"].append(point)
            if atom.GetSymbol() not in {"C", "H"}:
                substrate_points["hetero"].append(point)
            if atom.GetIsAromatic():
                substrate_points["aromatic"].append(point)
            if atom.GetSymbol() in {"F", "Cl", "Br", "I"}:
                substrate_points["halogen"].append(point)
    denominator = len(substrate_points["all_heavy"])
    return {
        "pose_id": pose["pose_id"],
        "score": float(pose["uff_pose_score"]),
        "score_rank": int(pose["score_rank"]),
        "stratum": pose_stratum(pose),
        "nitrene": nitrene,
        "carbon": carbon,
        "transferred_h": transferred_h,
        "axis_n_to_h": axis_n_to_h,
        "axis_h_to_n": axis_h_to_n,
        "segment_length": float(numpy.linalg.norm(transferred_h - nitrene)),
        "points": substrate_points,
        "denominator": denominator,
        "reported_stage1_index": reported_index,
        "transferred_hydrogen_stage1_index": transferred_h_index,
        "substrate_heavy_atom_count": denominator,
    }


def build_pose_features(context: dict[str, Any]) -> dict[str, Any]:
    points = context["points"]
    denominator = context["denominator"]
    nitrene_features = {
        channel: field_descriptor(points[channel], context["nitrene"], context["axis_n_to_h"], denominator)
        for channel in ("all_heavy", "carbon", "hetero", "aromatic", "halogen")
    }
    hydrogen_features = {
        channel: field_descriptor(points[channel], context["transferred_h"], context["axis_h_to_n"], denominator)
        for channel in ("all_heavy", "carbon", "hetero", "aromatic", "halogen", "reactive_h")
    }
    directed_features = {}
    for direction, origin, axis in (
        ("n_to_h", context["nitrene"], context["axis_n_to_h"]),
        ("h_to_n", context["transferred_h"], context["axis_h_to_n"]),
    ):
        directed_features[direction] = {
            channel: directed_descriptor(points[channel], origin, axis, context["segment_length"])
            for channel in ("all_heavy", "hetero")
        }
    return {
        **context,
        "nitrene_features": nitrene_features,
        "hydrogen_features": hydrogen_features,
        "directed_features": directed_features,
        "nitrene_cos_values": {
            channel: point_geometry(points[channel], context["nitrene"], context["axis_n_to_h"])["cos"].tolist()
            for channel in ("all_heavy", "hetero")
        },
        "hydrogen_cos_values": {
            channel: point_geometry(points[channel], context["transferred_h"], context["axis_h_to_n"])["cos"].tolist()
            for channel in ("all_heavy", "hetero")
        },
    }


def aggregate_descriptor(values: list[float]) -> dict[str, float]:
    return {
        "mean": mean_or_zero(values),
        "std": std_or_zero(values),
        "median": quantile(values, 0.50),
        "q10": quantile(values, 0.10),
        "q90": quantile(values, 0.90),
    }


def histogram_js(left: list[float], right: list[float], bins: int = 16) -> float:
    values = numpy.asarray(left + right, dtype=float)
    if values.size == 0:
        return 0.0
    edges = numpy.linspace(-1.0, 1.0, bins + 1)
    p, _ = numpy.histogram(left, bins=edges, density=False)
    q, _ = numpy.histogram(right, bins=edges, density=False)
    p = p.astype(float) + 1e-12
    q = q.astype(float) + 1e-12
    p /= p.sum()
    q /= q.sum()
    midpoint = 0.5 * (p + q)
    return float(0.5 * numpy.sum(p * numpy.log(p / midpoint)) + 0.5 * numpy.sum(q * numpy.log(q / midpoint)))


def safe_spearman(left: list[float], right: list[float]) -> float:
    if len(left) < 3 or len(set(left)) < 2 or len(set(right)) < 2:
        return 0.0
    value = spearmanr(left, right).statistic
    return finite(value)


def add_feature(target: dict[str, float], name: str, value: float) -> None:
    target[name] = finite(value)


def stability_summary(values: list[float], seed: int) -> dict[str, float]:
    if len(values) < 2:
        return {"bootstrap_mean_ci_width": 0.0, "split_half_wasserstein": 0.0}
    rng = numpy.random.default_rng(seed)
    array = numpy.asarray(values, dtype=float)
    bootstrap_means = numpy.array([array[rng.integers(0, len(array), len(array))].mean() for _ in range(1000)])
    permutation = rng.permutation(array)
    midpoint = len(permutation) // 2
    return {
        "bootstrap_mean_ci_width": float(numpy.quantile(bootstrap_means, 0.975) - numpy.quantile(bootstrap_means, 0.025)),
        "split_half_wasserstein": float(wasserstein_distance(permutation[:midpoint], permutation[midpoint:])),
    }


def generate_stability_diagnostics(pose_features: list[dict[str, Any]]) -> dict[str, float]:
    diagnostics: dict[str, float] = {}
    grouped: dict[str, list[dict[str, Any]]] = {stratum: [] for stratum in STRATA}
    for pose in pose_features:
        grouped[pose["stratum"]].append(pose)
    grouped["all_200"] = pose_features
    selectors = {
        "nitrene_all_heavy_radial_mean": lambda pose: pose["nitrene_features"]["all_heavy"]["radial_mean"],
        "hydrogen_all_heavy_radial_mean": lambda pose: pose["hydrogen_features"]["all_heavy"]["radial_mean"],
        "n_to_h_all_heavy_axial_mean": lambda pose: pose["directed_features"]["n_to_h"]["all_heavy"]["axial_mean"],
        "h_to_n_all_heavy_axial_mean": lambda pose: pose["directed_features"]["h_to_n"]["all_heavy"]["axial_mean"],
    }
    for selector_name, selector in selectors.items():
        for stratum in STRATA:
            values = [selector(pose) for pose in grouped[stratum]]
            seed_text = f"{selector_name}:{stratum}"
            seed = sum((index + 1) * ord(character) for index, character in enumerate(seed_text)) & 0xFFFF
            summary = stability_summary(values, seed=seed)
            for metric, value in summary.items():
                diagnostics[f"{selector_name}:{stratum}:{metric}"] = value
    return diagnostics


def generate_aggregate_features(pose_features: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    geometry: dict[str, float] = {}
    relational: dict[str, float] = {}
    grouped: dict[str, list[dict[str, Any]]] = {stratum: [] for stratum in STRATA}
    for pose in pose_features:
        grouped[pose["stratum"]].append(pose)
    grouped["all_200"] = pose_features

    for view_name, channels in (
        ("nitrene", ("all_heavy", "carbon", "hetero", "aromatic", "halogen")),
        ("hydrogen", ("all_heavy", "carbon", "hetero", "aromatic", "halogen", "reactive_h")),
    ):
        for channel in channels:
            descriptor_names = tuple(pose_features[0][f"{view_name}_features"][channel])
            for descriptor_name in descriptor_names:
                for stratum in STRATA:
                    values = [pose[f"{view_name}_features"][channel][descriptor_name] for pose in grouped[stratum]]
                    summary = aggregate_descriptor(values)
                    add_feature(geometry, f"stage2p:{view_name}:{channel}:{descriptor_name}:{stratum}:mean", summary["mean"])
                    if descriptor_name in FIELD_STD_KEYS:
                        add_feature(geometry, f"stage2p:{view_name}:{channel}:{descriptor_name}:{stratum}:std", summary["std"])

            if channel == "all_heavy":
                top = grouped["top_100"]
                bottom = grouped["bottom_100"]
                for metric_name in ("radial_mean", "radial_q90"):
                    add_feature(
                        relational,
                        f"stage2p:relation:{view_name}:{channel}:{metric_name}:wasserstein_top_bottom",
                        wasserstein_distance(
                            [pose[f"{view_name}_features"][channel][metric_name] for pose in top],
                            [pose[f"{view_name}_features"][channel][metric_name] for pose in bottom],
                        ),
                    )
                add_feature(
                    relational,
                    f"stage2p:relation:{view_name}:{channel}:angular_js_top_bottom",
                    histogram_js(
                        [value for pose in top for value in pose[f"{view_name}_cos_values"][channel]],
                        [value for pose in bottom for value in pose[f"{view_name}_cos_values"][channel]],
                    ),
                )

    for direction in ("n_to_h", "h_to_n"):
        for channel in ("all_heavy", "hetero"):
            for descriptor_name in ("axial_mean", "axial_q90", "corridor_fraction"):
                for stratum in STRATA:
                    values = [pose["directed_features"][direction][channel][descriptor_name] for pose in grouped[stratum]]
                    add_feature(
                        geometry,
                        f"stage2p:{direction}:{channel}:{descriptor_name}:{stratum}:mean",
                        mean_or_zero(values),
                    )

            if direction == "n_to_h":
                all_values = grouped["all_200"]
                left = mean_or_zero([pose["directed_features"]["n_to_h"][channel]["axial_mean"] for pose in all_values])
                right = mean_or_zero([pose["directed_features"]["h_to_n"][channel]["axial_mean"] for pose in all_values])
                add_feature(geometry, f"stage2p:directional_symmetry:{channel}:axial_mean:mean", 0.5 * (left + right))
                add_feature(geometry, f"stage2p:directional_antisymmetry:{channel}:axial_mean:mean", left - right)

    for view_name in ("nitrene", "hydrogen"):
        values_top = [pose[view_name + "_features"]["all_heavy"]["radial_mean"] for pose in grouped["top_100"]]
        values_bottom = [pose[view_name + "_features"]["all_heavy"]["radial_mean"] for pose in grouped["bottom_100"]]
        add_feature(relational, f"stage2p:relation:{view_name}:all_heavy:descriptor_energy_distance", energy_distance(values_top, values_bottom))
        scores = [pose["score_rank"] for pose in grouped["all_200"]]
        radial = [pose[view_name + "_features"]["all_heavy"]["radial_mean"] for pose in grouped["all_200"]]
        add_feature(relational, f"stage2p:relation:{view_name}:all_heavy:uff_rank_spearman_radial_mean", safe_spearman(scores, radial))

    features = {**geometry, **relational}
    if len(features) > MAX_NEW_FEATURES:
        raise ValueError(f"Stage 2p feature budget exceeded: {len(features)} > {MAX_NEW_FEATURES}")
    return {"stage2p_geometry": geometry, "stage2p_relational": relational}


def render_svg(substrate_id: str, pose_features: list[dict[str, Any]], path: Path) -> None:
    width, height = 1100, 720
    panels = [("nitrene", "Nitrene-centered field"), ("hydrogen", "Transferred-H field"), ("n_to_h", "N to H projection"), ("h_to_n", "H to N projection"), ("all", "Five-view pose map")]
    colors = {"top_100": "#2166ac", "bottom_100": "#b2182b"}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">', '<rect width="100%" height="100%" fill="#f7f4ed"/>', f'<text x="28" y="34" font-family="Arial" font-size="23" font-weight="700">Stage 2p {substrate_id}</text>', '<text x="28" y="58" font-family="Arial" font-size="13">Catalyst-stripped substrate fields; blue = top 100, red = bottom 100, gray = all-pose context.</text>']
    panel_w, panel_h = 205, 245
    for panel_index, (kind, title) in enumerate(panels):
        x0 = 24 + (panel_index % 5) * (panel_w + 10)
        y0 = 88
        parts.append(f'<rect x="{x0}" y="{y0}" width="{panel_w}" height="{panel_h}" fill="#fff" stroke="#b8b1a6"/>')
        parts.append(f'<text x="{x0 + 8}" y="{y0 + 20}" font-family="Arial" font-size="13" font-weight="700">{title}</text>')
        points = []
        for pose in pose_features:
            if kind in {"nitrene", "hydrogen"}:
                origin = pose[kind if kind == "nitrene" else "transferred_h"]
                axis = pose["axis_n_to_h"] if kind == "nitrene" else pose["axis_h_to_n"]
                for point in pose["points"]["all_heavy"]:
                    relative = point - origin
                    z = float(numpy.dot(relative, axis))
                    rho = float(numpy.linalg.norm(relative - z * axis))
                    points.append((z, rho, pose["stratum"]))
            elif kind in {"n_to_h", "h_to_n"}:
                direction = "n_to_h" if kind == "n_to_h" else "h_to_n"
                origin = pose["nitrene"] if direction == "n_to_h" else pose["transferred_h"]
                axis = pose["axis_n_to_h"] if direction == "n_to_h" else pose["axis_h_to_n"]
                for point in pose["points"]["all_heavy"]:
                    relative = point - origin
                    z = float(numpy.dot(relative, axis))
                    rho = float(numpy.linalg.norm(relative - z * axis))
                    points.append((z, rho, pose["stratum"]))
            else:
                for direction in ("n_to_h", "h_to_n"):
                    origin = pose["nitrene"] if direction == "n_to_h" else pose["transferred_h"]
                    axis = pose["axis_n_to_h"] if direction == "n_to_h" else pose["axis_h_to_n"]
                    for point in pose["points"]["all_heavy"]:
                        relative = point - origin
                        z = float(numpy.dot(relative, axis))
                        rho = float(numpy.linalg.norm(relative - z * axis))
                        points.append((z, rho, pose["stratum"]))
        if points:
            z_values = [point[0] for point in points]
            rho_values = [point[1] for point in points]
            z_min, z_max = min(z_values), max(z_values)
            rho_max = max(rho_values) or 1.0
            for z, rho, stratum in points[:: max(1, len(points) // 260)]:
                sx = x0 + 12 + (z - z_min) / (z_max - z_min or 1.0) * (panel_w - 24)
                sy = y0 + panel_h - 14 - rho / rho_max * (panel_h - 50)
                parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="1.4" fill="{colors.get(stratum, "#777777")}" opacity="0.34"/>')
        parts.append(f'<text x="{x0 + 8}" y="{y0 + panel_h - 8}" font-family="Arial" font-size="10">axis z / radial ρ</text>')
    parts.append('</svg>')
    path.write_text("".join(parts), encoding="utf-8")


def generate_substrate_feature_row(record: dict[str, Any], report: dict[str, Any], temporary_dir: Path) -> dict[str, Any]:
    posed_molecule = stage2_interaction.stage1_pose_molecule(record["structure"]["nitrene_smiles"])
    atom_map = stage2_interaction.map_ids_to_stage1_atom_indices(record, posed_molecule)
    contexts = [pose_context(pose, record, posed_molecule, atom_map) for pose in report["pose_records"]]
    if len(contexts) != 200:
        raise ValueError(f"{record['substrate_id']}: Stage 2p requires exactly 200 retained poses, found {len(contexts)}")
    pose_features = [build_pose_features(context) for context in contexts]
    graphic_path = temporary_dir / f"{record['substrate_id']}.svg"
    render_svg(record["substrate_id"], pose_features, graphic_path)
    blocks = generate_aggregate_features(pose_features)
    graphic_path.unlink()
    return {
        "schema_version": "stage2p-reaction-axis-features-v1",
        "substrate_id": record["substrate_id"],
        "reaction_id": record["reaction_id"],
        "target_name": "ee_percent_magnitude",
        "target_value": (float(record["outcome"]["ee_percent"]) if record.get("outcome", {}).get("ee_percent") is not None else None),
        "feature_blocks": blocks,
        "feature_count": sum(len(block) for block in blocks.values()),
        "diagnostics": {"pose_ensemble_stability": generate_stability_diagnostics(pose_features)},
        "provenance": {
            "pose_count": 200,
            "pose_strata": {"top_100": 100, "bottom_100": 100, "all_200": 200},
            "reported_reactive_atom_map_id": record["reaction_center"]["reported_reactive_site"]["atom_map_id"],
            "per_pose_transferred_hydrogen": True,
            "catalyst_atoms_in_density_fields": False,
            "nitrene_anchor_retained": True,
            "coordinate_convention": "azimuth_free_nitrene_transferred_h_axis",
            "radial_basis_centers_angstrom": RADIAL_CENTERS.tolist(),
            "radial_basis_widths_angstrom": RADIAL_WIDTHS.tolist(),
            "legendre_orders": list(LEGENDRE_ORDERS),
            "pose_weighting": "uniform_within_stratum",
            "temporary_graphics_generated": 1,
            "temporary_graphics_deleted_after_extraction": True,
            "temporary_graphic_path_not_persisted": True,
            "force_field": report.get("pose_generation_run", {}).get("force_field", "uff"),
        },
    }


def generate_stage2p_features(records_path: Path, report_dir: Path) -> list[dict[str, Any]]:
    records = {
        row["substrate_id"]: row
        for row in read_jsonl(records_path)
        if row.get("outcome", {}).get("ee_percent") is not None
        and row.get("reaction_center", {}).get("review_status") == "checked"
    }
    reports = {}
    for report_path in sorted(report_dir.glob("stage-1-smoke-*.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        substrate_id = report_substrate_id(report)
        if substrate_id in records:
            reports[substrate_id] = report
    missing = sorted(set(records) - set(reports))
    if missing:
        raise ValueError(f"Missing Stage 1 reports for modelable substrates: {', '.join(missing)}")
    rows = []
    with tempfile.TemporaryDirectory(prefix="stage2p-graphics-") as temporary:
        temporary_dir = Path(temporary)
        for substrate_id in sorted(records):
            rows.append(generate_substrate_feature_row(records[substrate_id], reports[substrate_id], temporary_dir))
        if any(temporary_dir.iterdir()):
            raise RuntimeError("Stage 2p temporary graphics were not deleted")
    return rows


def flatten_numeric(block: dict[str, Any], prefix: str = "") -> dict[str, float]:
    flattened: dict[str, float] = {}
    for key, value in block.items():
        name = f"{prefix}:{key}" if prefix else key
        if isinstance(value, bool):
            flattened[name] = float(value)
        elif isinstance(value, (int, float)) and math.isfinite(float(value)):
            flattened[name] = float(value)
    return flattened


def stage2p_feature_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    return {row["substrate_id"]: flatten_numeric({**row["feature_blocks"]["stage2p_geometry"], **row["feature_blocks"]["stage2p_relational"]}) for row in rows}


def write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    feature_names = sorted(stage2p_feature_map(rows)[rows[0]["substrate_id"]])
    write_json(
        path,
        {
            "schema_version": "stage2p-feature-manifest-v1",
            "representation": "Stage 2p catalyst-stripped nitrene-anchored reaction-axis representation",
            "target": "ee_percent_magnitude",
            "substrate_count": len(rows),
            "feature_count": len(feature_names),
            "feature_names": feature_names,
            "pose_strata": {"top_100": 100, "bottom_100": 100, "all_200": 200},
            "temporary_graphics": "generated_and_deleted_during_extraction",
            "stability_metrics_in_model": False,
            "comparison_tracks": ["compatibility", "rigorous_nested_loo"],
            "force_fields": sorted({row.get("provenance", {}).get("force_field", "uff") for row in rows}),
        },
    )


def write_trends(path: Path, rows: list[dict[str, Any]]) -> None:
    feature_by_id = stage2p_feature_map(rows)
    substrate_ids = sorted(feature_by_id)
    targets = numpy.array([next(row["target_value"] for row in rows if row["substrate_id"] == substrate_id) for substrate_id in substrate_ids], dtype=float)
    feature_names = sorted(feature_by_id[substrate_ids[0]])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["feature_name", "mean", "std", "spearman_ee", "pearson_ee"], lineterminator="\n")
        writer.writeheader()
        for feature_name in feature_names:
            values = numpy.array([feature_by_id[substrate_id][feature_name] for substrate_id in substrate_ids], dtype=float)
            spearman = 0.0 if len(set(values)) < 2 else finite(spearmanr(values, targets).statistic)
            pearson = 0.0 if len(set(values)) < 2 else finite(numpy.corrcoef(values, targets)[0, 1])
            writer.writerow({"feature_name": feature_name, "mean": float(values.mean()), "std": float(values.std()), "spearman_ee": spearman, "pearson_ee": pearson})


def model_feature_rows(
    records_path: Path,
    pose_summary_path: Path,
    pose_interaction_path: Path,
    pose_folding_path: Path,
    stage2p_rows: list[dict[str, Any]],
) -> dict[str, tuple[list[dict[str, Any]], list[str], numpy.ndarray, numpy.ndarray]]:
    stage2p_by_id = stage2p_feature_map(stage2p_rows)
    policies = {
        "stage2_pose_summary": "summary",
        "stage2_alt": "summary_interaction_folding",
    }
    result = {}
    for name, policy in policies.items():
        rows, _, _, _ = stage2_folding.feature_rows_for_policy(records_path, pose_summary_path, pose_interaction_path, pose_folding_path, policy)
        for row in rows:
            row["features"] = dict(row["features"])
        result[name] = build_matrix(rows)
    stage2p_rows_for_model = [
        {"substrate_id": row["substrate_id"], "actual_ee": row["target_value"], "features": stage2p_by_id[row["substrate_id"]]}
        for row in stage2p_rows
    ]
    result["stage2p_geometry"] = build_matrix(stage2p_rows_for_model)
    alt_rows = result["stage2_alt"][0]
    combined_rows = []
    for row in alt_rows:
        combined_rows.append({"substrate_id": row["substrate_id"], "actual_ee": row["actual_ee"], "features": {**row["features"], **stage2p_by_id[row["substrate_id"]]}})
    result["stage2_alt_stage2p"] = build_matrix(combined_rows)
    for component in ("nitrene", "hydrogen", "n_to_h", "h_to_n", "directional_symmetry", "directional_antisymmetry", "relation"):
        component_rows = []
        for row in alt_rows:
            component_features = {key: value for key, value in stage2p_by_id[row["substrate_id"]].items() if component in key}
            component_rows.append({"substrate_id": row["substrate_id"], "actual_ee": row["actual_ee"], "features": {**row["features"], **component_features}})
        result[f"stage2_alt_plus_{component}"] = build_matrix(component_rows)
    return result


def build_matrix(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str], numpy.ndarray, numpy.ndarray]:
    feature_names = sorted({key for row in rows for key in row["features"]})
    x = numpy.array([[row["features"].get(key, 0.0) for key in feature_names] for row in rows], dtype=float)
    y = numpy.array([row["actual_ee"] for row in rows], dtype=float)
    return rows, feature_names, x, y


def elastic_net_grid() -> list[tuple[float, float]]:
    return [(alpha, l1_ratio) for alpha in (0.01, 0.1, 1.0, 10.0, 100.0) for l1_ratio in (0.2, 0.5, 0.8, 1.0)]


def fit_model(x: numpy.ndarray, y: numpy.ndarray, alpha: float, l1_ratio: float) -> Any:
    return make_pipeline(
        StandardScaler(),
        ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=5000, tol=1e-3, random_state=0, selection="random"),
    )


def metrics(y: numpy.ndarray, prediction: numpy.ndarray) -> dict[str, Any]:
    absolute = numpy.abs(y - prediction)
    return {
        "record_count": int(len(y)),
        "mae": float(mean_absolute_error(y, prediction)),
        "rmse": float(mean_squared_error(y, prediction) ** 0.5),
        "r2": float(r2_score(y, prediction)),
        "median_abs_error": float(numpy.median(absolute)),
        "within_10_count": int(numpy.sum(absolute <= 10.0)),
        "within_15_count": int(numpy.sum(absolute <= 15.0)),
        "within_20_count": int(numpy.sum(absolute <= 20.0)),
    }


def compatibility_benchmark(x: numpy.ndarray, y: numpy.ndarray) -> dict[str, Any]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        selected = stage2_folding.select_loo_model(x, y)
    prediction = numpy.asarray(selected["loo_predictions"], dtype=float)
    return {
        "track": "compatibility",
        "protocol": "recorded_stage2_alt_full_loo_grid_selection",
        "selected_alpha": selected["selected_alpha"],
        "selected_l1_ratio": selected["selected_l1_ratio"],
        "predictions": prediction.tolist(),
        **metrics(y, prediction),
    }


def active_columns(x: numpy.ndarray) -> numpy.ndarray:
    return numpy.std(x, axis=0) > 0.0


def nested_benchmark(x: numpy.ndarray, y: numpy.ndarray) -> dict[str, Any]:
    """Run outer LOO with an inner LOO ElasticNetCV grid.

    Standardization and constant-feature filtering are fitted on each outer
    training fold. ElasticNetCV performs the inner leave-one-out selection over
    the exact Stage 2p alpha/l1-ratio grid, avoiding tens of thousands of
    repeated Python-level estimator fits.
    """
    predictions = numpy.zeros(len(y), dtype=float)
    selected_params: list[dict[str, float]] = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        for holdout in range(len(y)):
            outer_train = numpy.array([index for index in range(len(y)) if index != holdout], dtype=int)
            columns = active_columns(x[outer_train])
            scaler = StandardScaler()
            train_scaled = scaler.fit_transform(x[outer_train][:, columns])
            holdout_scaled = scaler.transform(x[[holdout]][:, columns])
            model = ElasticNetCV(
                alphas=[0.01, 0.1, 1.0, 10.0, 100.0],
                l1_ratio=[0.2, 0.5, 0.8, 1.0],
                cv=LeaveOneOut(),
                max_iter=5000,
                tol=1e-3,
                random_state=0,
                selection="random",
                n_jobs=-1,
            )
            model.fit(train_scaled, y[outer_train])
            predictions[holdout] = float(model.predict(holdout_scaled)[0])
            selected_params.append({"alpha": float(model.alpha_), "l1_ratio": float(model.l1_ratio_)})
    return {
        "track": "rigorous_nested_loo",
        "protocol": "nested_leave_one_out_with_fold_local_constant_filtering_and_scaling",
        "selected_params_by_holdout": selected_params,
        "predictions": predictions.tolist(),
        **metrics(y, predictions),
    }


def uncertainty_report(y: numpy.ndarray, baseline: numpy.ndarray, candidate: numpy.ndarray, seed: int = 0) -> dict[str, Any]:
    delta = numpy.abs(candidate - y) - numpy.abs(baseline - y)
    rng = numpy.random.default_rng(seed)
    bootstrap = numpy.array([numpy.mean(delta[rng.integers(0, len(delta), len(delta))]) for _ in range(10000)])
    signs = rng.choice(numpy.array([-1.0, 1.0]), size=(10000, len(delta)))
    permutation = numpy.mean(signs * delta[None, :], axis=1)
    mean_delta = float(numpy.mean(delta))
    upper = float(numpy.quantile(bootstrap, 0.975))
    p_value = float(numpy.mean(numpy.abs(permutation) >= abs(mean_delta)))
    return {
        "mean_delta_mae_candidate_minus_baseline": mean_delta,
        "bootstrap_ci_95_low": float(numpy.quantile(bootstrap, 0.025)),
        "bootstrap_ci_95_high": upper,
        "paired_sign_permutation_p_value": p_value,
        "practical_improvement_threshold_ee_points": -1.0,
        "passes_prespecified_gate": bool(mean_delta <= -1.0 and upper < 0.0),
    }


def run_benchmark(
    records_path: Path,
    pose_summary_path: Path,
    pose_interaction_path: Path,
    pose_folding_path: Path,
    stage2p_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    model_rows = model_feature_rows(records_path, pose_summary_path, pose_interaction_path, pose_folding_path, stage2p_rows)
    reports: dict[str, Any] = {"schema_version": "stage2p-model-comparison-v1", "target": "ee_percent_magnitude", "models": {}}
    prediction_rows: list[dict[str, Any]] = []
    compatibility_predictions: dict[str, numpy.ndarray] = {}
    rigorous_predictions: dict[str, numpy.ndarray] = {}
    primary_models = {"stage2_pose_summary", "stage2_alt", "stage2p_geometry", "stage2_alt_stage2p"}
    for model_name, (rows, feature_names, x, y) in model_rows.items():
        compatibility = compatibility_benchmark(x, y) if model_name in primary_models else None
        rigorous = nested_benchmark(x, y)
        reports["models"][model_name] = {
            "feature_count": len(feature_names),
            "comparison_scope": "primary_four_way" if model_name in primary_models else "rigorous_ablation_only",
            "compatibility": None if compatibility is None else {key: value for key, value in compatibility.items() if key != "predictions"},
            "rigorous": {key: value for key, value in rigorous.items() if key != "predictions"},
        }
        if compatibility is not None:
            compatibility_predictions[model_name] = numpy.asarray(compatibility["predictions"], dtype=float)
        rigorous_predictions[model_name] = numpy.asarray(rigorous["predictions"], dtype=float)
        for index, row in enumerate(rows):
            if compatibility is not None:
                prediction_rows.append({"track": "compatibility", "feature_set": model_name, "substrate_id": row["substrate_id"], "observed_ee": row["actual_ee"], "prediction": compatibility["predictions"][index], "abs_error": abs(compatibility["predictions"][index] - row["actual_ee"])})
            prediction_rows.append({"track": "rigorous_nested_loo", "feature_set": model_name, "substrate_id": row["substrate_id"], "observed_ee": row["actual_ee"], "prediction": rigorous["predictions"][index], "abs_error": abs(rigorous["predictions"][index] - row["actual_ee"])})
    for track_name, prediction_map in (("compatibility", compatibility_predictions), ("rigorous_nested_loo", rigorous_predictions)):
        if "stage2_alt" in prediction_map and "stage2_alt_stage2p" in prediction_map:
            reports.setdefault("paired_uncertainty", {})[track_name] = uncertainty_report(
                model_rows["stage2_alt"][3], prediction_map["stage2_alt"], prediction_map["stage2_alt_stage2p"]
            )
    substrate_count = len(model_rows["stage2_alt"][0])
    reports["cohort"] = {
        "substrate_count": substrate_count,
        "pose_cohort": f"{substrate_count} substrates x 200 retained Stage 1 poses",
    }
    reports["feature_policy"] = {"max_new_stage2p_features": MAX_NEW_FEATURES, "stability_metrics_in_model": False, "temporary_graphics_persisted": False}
    return reports, prediction_rows


def write_predictions(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["track", "feature_set", "substrate_id", "observed_ee", "prediction", "abs_error"]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--stage1-report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--pose-summary", type=Path, default=DEFAULT_POSE_SUMMARY)
    parser.add_argument("--pose-interaction", type=Path, default=DEFAULT_POSE_INTERACTION)
    parser.add_argument("--pose-folding", type=Path, default=DEFAULT_POSE_FOLDING)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--trends", type=Path, default=DEFAULT_TRENDS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stage2p_rows = generate_stage2p_features(args.records, args.stage1_report_dir)
    write_jsonl(args.features, stage2p_rows)
    write_manifest(args.manifest, stage2p_rows)
    write_trends(args.trends, stage2p_rows)
    reports, predictions = run_benchmark(args.records, args.pose_summary, args.pose_interaction, args.pose_folding, stage2p_rows)
    write_json(args.metrics, reports)
    write_predictions(args.predictions, predictions)
    print(f"Wrote Stage 2p features for {len(stage2p_rows)} substrates ({stage2p_rows[0]['feature_count']} features per substrate)")
    print(f"Wrote Stage 2p model comparison to {args.metrics}")


if __name__ == "__main__":
    main()

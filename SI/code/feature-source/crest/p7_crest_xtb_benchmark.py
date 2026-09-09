#!/usr/bin/env python3
"""Benchmark compact CREST/GFN2-xTB substrate features on the locked P7 cohort."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy


ROOT = Path(__file__).resolve().parents[3]
DATED_DIR = Path(__file__).resolve().parent
DEFAULT_ENSEMBLES = DATED_DIR / "crest-10-conformers" / "p7"
DEFAULT_OUTPUT = DATED_DIR / "p7-crest-xtb-model"
DEFAULT_XTB = ROOT / ".chem-env/bin/xtb"
RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
STAGE2P_FEATURES = ROOT / "data/jacs_2025/stage2/features/stage2p-features.jsonl"
# 1ad and 1z are non-modelable failure/no-product records; 1an is an achiral
# product whose ee is explicitly not applicable.
EXCLUDED_SUBSTRATES = {"1ad", "1an", "1z"}
MODEL_ELECTRONIC_FEATURES = [
    "crest_xtb.total_energy_per_atom_hartree",
    "crest_xtb.total_energy_per_electron_hartree",
    "crest_xtb.electronic_energy_per_electron_hartree",
    "crest_xtb.energy_minus_electronic_per_atom_hartree",
    "crest_xtb.homo_ev",
    "crest_xtb.lumo_ev",
    "crest_xtb.homo_lumo_gap_ev",
    "crest_xtb.dipole_norm_au",
    "crest_xtb.charge_std",
    "crest_xtb.charge_mean_absolute",
    "crest_xtb.charge_range",
    "crest_xtb.atomic_dipole_mean_norm_au",
    "crest_xtb.atomic_dipole_max_norm_au",
]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


stage2p = load_module("stage2p_representation_for_crest", ROOT / "scripts/stage2p_representation.py")
family_heldout = load_module("stage2p_family_heldout_for_crest", ROOT / "scripts/stage2p_family_heldout.py")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_first_xyz(path: Path) -> tuple[list[str], numpy.ndarray]:
    lines = path.read_text(encoding="utf-8").splitlines()
    count = int(lines[0])
    atom_lines = lines[2 : 2 + count]
    if len(atom_lines) != count:
        raise ValueError(f"{path}: truncated first XYZ structure")
    symbols, coordinates = [], []
    for line in atom_lines:
        fields = line.split()
        symbols.append(fields[0])
        coordinates.append([float(value) for value in fields[1:4]])
    return symbols, numpy.asarray(coordinates, dtype=float)


def geometry_features(symbols: list[str], coordinates: numpy.ndarray) -> dict[str, float]:
    heavy = numpy.asarray([symbol != "H" for symbol in symbols], dtype=bool)
    points = coordinates[heavy]
    centered = points - numpy.mean(points, axis=0)
    eigenvalues = numpy.sort(numpy.linalg.eigvalsh(centered.T @ centered / len(points)))
    distances = numpy.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)
    radius_gyration = float(numpy.sqrt(numpy.mean(numpy.sum(centered * centered, axis=1))))
    total = float(numpy.sum(eigenvalues))
    return {
        "crest_geom.atom_count": float(len(symbols)),
        "crest_geom.heavy_atom_count": float(numpy.sum(heavy)),
        "crest_geom.radius_gyration_angstrom": radius_gyration,
        "crest_geom.maximum_span_angstrom": float(numpy.max(distances)),
        "crest_geom.principal_variance_small": float(eigenvalues[0]),
        "crest_geom.principal_variance_middle": float(eigenvalues[1]),
        "crest_geom.principal_variance_large": float(eigenvalues[2]),
        "crest_geom.asphericity": float(eigenvalues[2] - 0.5 * (eigenvalues[0] + eigenvalues[1])),
        "crest_geom.planarity_fraction": float(eigenvalues[0] / total) if total else 0.0,
        "crest_geom.elongation_fraction": float(eigenvalues[2] / total) if total else 0.0,
    }


def electronic_features(payload: dict[str, Any], symbols: list[str]) -> dict[str, float]:
    charges = numpy.asarray(payload["partial charges"], dtype=float)
    occupations = numpy.asarray(payload["fractional occupation"], dtype=float)
    orbitals = numpy.asarray(payload["orbital energies / eV"], dtype=float)
    occupied = orbitals[occupations > 0.1]
    virtual = orbitals[occupations <= 0.1]
    dipole = numpy.asarray(payload["dipole / a.u."], dtype=float)
    atomic_dipoles = numpy.linalg.norm(numpy.asarray(payload["atomic dipole moments"], dtype=float), axis=1)
    electron_count = float(payload["number of electrons"])
    atom_count = float(len(symbols))
    features = {
        "crest_xtb.total_energy_per_atom_hartree": float(payload["total energy"]) / atom_count,
        "crest_xtb.total_energy_per_electron_hartree": float(payload["total energy"]) / electron_count,
        "crest_xtb.electronic_energy_per_electron_hartree": float(payload["electronic energy"]) / electron_count,
        "crest_xtb.energy_minus_electronic_per_atom_hartree": (
            float(payload["total energy"]) - float(payload["electronic energy"])
        ) / atom_count,
        "crest_xtb.homo_ev": float(numpy.max(occupied)),
        "crest_xtb.lumo_ev": float(numpy.min(virtual)),
        "crest_xtb.homo_lumo_gap_ev": float(payload["HOMO-LUMO gap / eV"]),
        "crest_xtb.dipole_norm_au": float(numpy.linalg.norm(dipole)),
        "crest_xtb.charge_std": float(numpy.std(charges)),
        "crest_xtb.charge_mean_absolute": float(numpy.mean(numpy.abs(charges))),
        "crest_xtb.charge_range": float(numpy.max(charges) - numpy.min(charges)),
        "crest_xtb.atomic_dipole_mean_norm_au": float(numpy.mean(atomic_dipoles)),
        "crest_xtb.atomic_dipole_max_norm_au": float(numpy.max(atomic_dipoles)),
    }
    for element in ("N", "O", "S", "F", "Cl", "Br", "I"):
        mask = numpy.asarray([symbol == element for symbol in symbols], dtype=bool)
        values = charges[mask]
        features[f"crest_xtb.{element}_count"] = float(len(values))
        features[f"crest_xtb.{element}_charge_mean"] = float(numpy.mean(values)) if len(values) else 0.0
        features[f"crest_xtb.{element}_charge_min"] = float(numpy.min(values)) if len(values) else 0.0
        features[f"crest_xtb.{element}_charge_max"] = float(numpy.max(values)) if len(values) else 0.0
    return features


def run_xtb(xyz_path: Path, destination: Path, xtb: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=True)
    output_json = destination / "xtbout.json"
    if output_json.exists():
        return read_json(output_json)
    with tempfile.TemporaryDirectory(prefix="p7-crest-xtb-") as temporary:
        work = Path(temporary)
        shutil.copy2(xyz_path, work / "conformer.xyz")
        completed = subprocess.run(
            [str(xtb), "conformer.xyz", "--gfn", "2", "--alpb", "ether", "--chrg", "0", "--uhf", "0", "--json"],
            cwd=work,
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
            env={**os.environ, "OMP_NUM_THREADS": "1"},
        )
        (destination / "xtb.stdout.log").write_text(completed.stdout, encoding="utf-8")
        (destination / "xtb.stderr.log").write_text(completed.stderr, encoding="utf-8")
        if completed.returncode != 0 or not (work / "xtbout.json").exists():
            raise RuntimeError(f"xTB failed for {xyz_path} with return code {completed.returncode}")
        shutil.copy2(work / "xtbout.json", output_json)
    return read_json(output_json)


def build_features(ensembles: Path, output: Path, xtb: Path) -> tuple[dict[str, dict[str, float]], list[str], list[str]]:
    by_id: dict[str, dict[str, float]] = {}
    geometry_names: set[str] = set()
    rows = []
    metadata_paths = sorted(ensembles.glob("*/metadata.json"))
    for index, metadata_path in enumerate(metadata_paths, start=1):
        metadata = read_json(metadata_path)
        substrate_id = metadata["substrate_id"]
        xyz_path = ROOT / metadata["conformers_xyz_path"]
        symbols, coordinates = parse_first_xyz(xyz_path)
        geometry = geometry_features(symbols, coordinates)
        xtb_payload = run_xtb(xyz_path, output / "xtb" / substrate_id, xtb)
        electronic = electronic_features(xtb_payload, symbols)
        population = metadata["population_model"]
        probability = {
            "crest_probability.retained_count": float(metadata["retained_conformer_count"]),
            "crest_probability.effective_conformer_count": float(population["effective_conformer_count"]),
            "crest_probability.maximum_probability": max(
                row["boltzmann_probability"] for row in population["conformers"]
            ),
        }
        features = {**geometry, **electronic, **probability}
        by_id[substrate_id] = features
        geometry_names.update(geometry)
        rows.append({"substrate_id": substrate_id, "features": features})
        print(f"[{index:02d}/{len(metadata_paths):02d}] xTB features {substrate_id}", flush=True)
    write_json(output / "features.json", rows)
    missing_model_features = sorted(set(MODEL_ELECTRONIC_FEATURES) - set(rows[0]["features"]))
    if missing_model_features:
        raise ValueError(f"Missing dense xTB model features: {missing_model_features}")
    return by_id, sorted(geometry_names), MODEL_ELECTRONIC_FEATURES


def bootstrap_delta(
    baseline: list[dict[str, Any]], candidate: list[dict[str, Any]], draws: int = 20000
) -> dict[str, float]:
    baseline_by_id = {row["substrate_id"]: row for row in baseline}
    candidate_by_id = {row["substrate_id"]: row for row in candidate}
    ids = sorted(baseline_by_id)
    base_errors = numpy.asarray([baseline_by_id[value]["abs_error"] for value in ids])
    candidate_errors = numpy.asarray([candidate_by_id[value]["abs_error"] for value in ids])
    rng = numpy.random.default_rng(20260907)
    indices = rng.integers(0, len(ids), size=(draws, len(ids)))
    deltas = numpy.mean(base_errors[indices] - candidate_errors[indices], axis=1)
    return {
        "mae_improvement_ee_points": float(numpy.mean(base_errors - candidate_errors)),
        "bootstrap_mean_improvement": float(numpy.mean(deltas)),
        "bootstrap_ci95_low": float(numpy.quantile(deltas, 0.025)),
        "bootstrap_ci95_high": float(numpy.quantile(deltas, 0.975)),
        "probability_improvement_gt_zero": float(numpy.mean(deltas > 0.0)),
    }


def write_predictions(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = ["feature_set", "substrate_id", "family_id", "family_label", "observed_ee", "prediction", "abs_error"]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def benchmark(ensembles: Path, output: Path, xtb: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    crest_by_id, geometry_names, electronic_names = build_features(ensembles, output, xtb)
    model_rows = stage2p.model_feature_rows(
        RECORDS,
        stage2p.DEFAULT_POSE_SUMMARY,
        stage2p.DEFAULT_POSE_INTERACTION,
        stage2p.DEFAULT_POSE_FOLDING,
        read_jsonl(STAGE2P_FEATURES),
    )["stage2p_geometry"]
    rows, base_names, base_x, y = model_rows
    keep = [index for index, row in enumerate(rows) if row["substrate_id"] not in EXCLUDED_SUBSTRATES]
    rows = [rows[index] for index in keep]
    base_x = base_x[keep]
    y = y[keep]
    ids = [row["substrate_id"] for row in rows]
    missing = sorted(set(ids) - set(crest_by_id))
    if missing:
        raise ValueError(f"Missing completed CREST/xTB features for {missing}")
    metadata = family_heldout.family_metadata(RECORDS)
    families = [metadata[value]["family_id"] for value in ids]
    family_labels = {value["family_id"]: value["family_label"] for value in metadata.values()}

    def matrix(names: list[str]) -> numpy.ndarray:
        return numpy.asarray([[crest_by_id[substrate_id][name] for name in names] for substrate_id in ids], dtype=float)

    arms = {
        "stage2p_geometry": (base_names, base_x),
        "stage2p_plus_crest_geometry": (base_names + geometry_names, numpy.column_stack([base_x, matrix(geometry_names)])),
        "stage2p_plus_crest_xtb_electronic": (
            base_names + electronic_names,
            numpy.column_stack([base_x, matrix(electronic_names)]),
        ),
        "stage2p_plus_crest_xtb_all": (
            base_names + geometry_names + electronic_names,
            numpy.column_stack([base_x, matrix(geometry_names + electronic_names)]),
        ),
    }
    reports, predictions_by_arm = {}, {}
    all_predictions = []
    for arm, (names, x) in arms.items():
        report, predictions = family_heldout.family_heldout_model(rows, names, x, y, families, family_labels)
        reports[arm] = report
        for prediction in predictions:
            prediction["feature_set"] = arm
        predictions_by_arm[arm] = predictions
        all_predictions.extend(predictions)
    comparisons = {
        arm: bootstrap_delta(predictions_by_arm["stage2p_geometry"], predictions)
        for arm, predictions in predictions_by_arm.items()
        if arm != "stage2p_geometry"
    }
    result = {
        "schema_version": "p7-crest-xtb-family-heldout-benchmark-v1",
        "target": "ee_percent_magnitude",
        "cohort": {"substrate_count": len(ids), "excluded_substrates": sorted(EXCLUDED_SUBSTRATES)},
        "protocol": "outer leave-one-family-out with inner leave-one-family-out ElasticNet selection",
        "primary_comparison": "stage2p_geometry versus stage2p_plus_crest_xtb_all",
        "probability_feature_status": "constant_and_excluded_from_model_arms_because_all_CREST_ensembles_contain_one_unique_minimum",
        "models": reports,
        "paired_bootstrap_comparisons": comparisons,
    }
    write_json(output / "metrics.json", result)
    write_predictions(output / "predictions.csv", all_predictions)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ensembles", type=Path, default=DEFAULT_ENSEMBLES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--xtb", type=Path, default=DEFAULT_XTB)
    args = parser.parse_args()
    result = benchmark(args.ensembles, args.output, args.xtb)
    for name, report in result["models"].items():
        metrics = report["pooled_metrics"]
        print(f"{name}: MAE={metrics['mae']:.3f}, R2={metrics['r2']:.3f}, RMSE={metrics['rmse']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

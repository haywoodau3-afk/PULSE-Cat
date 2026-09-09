#!/usr/bin/env python3
"""Resource benchmark and uncertainty-aware pose-population utilities.

This module is deliberately isolated from the production Stage 2/3 pipeline.
It selects diverse representatives from the existing low/high UFF strata,
runs constrained GFN-FF cleanup followed by a GFN2-xTB/ALPB(ether) single
point, and turns relative energies into uncertainty-aware population weights.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import math
import os
import re
import resource
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT = ROOT / "data/jacs_2025/stage1/panel/stage-1-smoke-1a.json"
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results/five-pose-benchmark"
DEFAULT_XTB = ROOT / ".chem-env/bin/xtb"
HARTREE_TO_KCAL_MOL = 627.509474
R_KCAL_MOL_K = 0.00198720425864083
ENERGY_RE = re.compile(r"TOTAL ENERGY\s+(-?\d+(?:\.\d+)?)", re.IGNORECASE)
GAP_RE = re.compile(r"HOMO-LUMO GAP\s+(-?\d+(?:\.\d+)?)\s+eV", re.IGNORECASE)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_xyz(path: Path) -> tuple[list[str], np.ndarray]:
    lines = path.read_text(encoding="utf-8").splitlines()
    count = int(lines[0].strip())
    rows = [line.split() for line in lines[2 : 2 + count]]
    if len(rows) != count:
        raise ValueError(f"{path}: expected {count} atoms, found {len(rows)}")
    return [row[0] for row in rows], np.asarray([[float(x) for x in row[1:4]] for row in rows], dtype=float)


def pose_vector(pose: dict[str, Any]) -> np.ndarray:
    """Flatten substrate coordinates; the shared frozen core fixes the frame."""
    path = ROOT / pose["fe_bound_assembly_xyz_path"]
    _, coordinates = parse_xyz(path)
    return coordinates[int(pose["frozen_core_atom_count"]) :].reshape(-1)


def farthest_point_representatives(poses: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    """Deterministic max-min representatives, seeded by the best score/rank."""
    if count <= 0:
        return []
    if count >= len(poses):
        return list(poses)
    ordered = sorted(poses, key=lambda row: (float(row["uff_pose_score"]), int(row["score_rank"])))
    vectors = np.asarray([pose_vector(pose) for pose in ordered])
    chosen = [0]
    nearest = np.linalg.norm(vectors - vectors[0], axis=1)
    while len(chosen) < count:
        index = max((i for i in range(len(ordered)) if i not in chosen), key=lambda i: (nearest[i], -i))
        chosen.append(index)
        nearest = np.minimum(nearest, np.linalg.norm(vectors - vectors[index], axis=1))
    return [ordered[index] for index in chosen]


def select_poses(report: dict[str, Any], count: int) -> list[dict[str, Any]]:
    """Select approximately half low and half strained representatives."""
    if count < 2:
        raise ValueError("At least two poses are required to represent both strata")
    low = [row for row in report["pose_records"] if row["selection_bucket"] == "low_energy"]
    high = [row for row in report["pose_records"] if row["selection_bucket"] == "high_energy"]
    low_count = (count + 1) // 2
    selected = farthest_point_representatives(low, low_count) + farthest_point_representatives(high, count - low_count)
    all_vectors = {row["pose_id"]: pose_vector(row) for row in low + high}
    for stratum in (low, high):
        medoids = [row for row in selected if row["selection_bucket"] == stratum[0]["selection_bucket"]]
        counts = {row["pose_id"]: 0 for row in medoids}
        for member in stratum:
            nearest = min(medoids, key=lambda row: float(np.linalg.norm(all_vectors[member["pose_id"]] - all_vectors[row["pose_id"]])))
            counts[nearest["pose_id"]] += 1
        for row in medoids:
            row["selection_cluster_size"] = counts[row["pose_id"]]
            row["sampling_prior"] = counts[row["pose_id"]] / len(report["pose_records"])
    return sorted(selected, key=lambda row: int(row["score_rank"]))


def write_xcontrol(path: Path, frozen_core_atom_count: int) -> None:
    atoms = ",".join(str(index) for index in range(1, frozen_core_atom_count + 1))
    path.write_text(f"$fix\n  atoms: {atoms}\n$end\n", encoding="utf-8")


def run_timed(
    command: list[str], cwd: Path, stdout_path: Path, stderr_path: Path, threads: int, timeout_seconds: int
) -> dict[str, Any]:
    started = time.perf_counter()
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                text=True,
                stdout=stdout,
                stderr=stderr,
                check=False,
                timeout=timeout_seconds,
                env={**os.environ, "OMP_NUM_THREADS": str(threads)},
            )
            returncode = completed.returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            returncode = 124
            timed_out = True
    wall = time.perf_counter() - started
    # On macOS ru_maxrss is bytes. It is the high-water mark across children of
    # this runner, so it is a conservative process-level bound, not a per-step trace.
    child_high_water_rss_bytes = int(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    return {
        "command": command,
        "returncode": returncode,
        "timed_out": timed_out,
        "wall_seconds": wall,
        "child_process_high_water_rss_bytes": child_high_water_rss_bytes,
        "memory_measurement_scope": "runner child-process high-water mark (macOS ru_maxrss)",
    }


def last_match(pattern: re.Pattern[str], text: str) -> float | None:
    matches = pattern.findall(text)
    return float(matches[-1]) if matches else None


def run_pose(
    pose: dict[str, Any],
    output_dir: Path,
    xtb_path: Path,
    threads: int,
    cleanup_method: str = "none",
    charge: int = 0,
    uhf: int = 1,
    timeout_seconds: int = 1800,
) -> dict[str, Any]:
    work = output_dir / pose["pose_id"]
    work.mkdir(parents=True, exist_ok=True)
    for name in (
        "xtbopt.xyz", "xtblast.xyz", "xtbopt.log", ".xtboptok", "charges", "wbo",
        "xtbrestart", "xtbtopo.mol", "gfnff-optimized.xyz",
    ):
        artifact = work / name
        if artifact.exists():
            artifact.unlink()
    source = ROOT / pose["fe_bound_assembly_xyz_path"]
    input_xyz = work / "input.xyz"
    shutil.copy2(source, input_xyz)
    xcontrol = work / "xcontrol"
    write_xcontrol(xcontrol, int(pose["frozen_core_atom_count"]))

    cleaned_xyz = work / "gfnff-optimized.xyz"
    if cleanup_method == "none":
        shutil.copy2(input_xyz, cleaned_xyz)
        cleanup = {"status": "skipped", "wall_seconds": 0.0, "reason": "direct GFN2 control benchmark on existing UFF-cleaned geometry"}
    else:
        cleanup_method_args = ["--gfnff"] if cleanup_method == "gfnff" else ["--gfn", "2"]
        cleanup = run_timed(
            [str(xtb_path), input_xyz.name, *cleanup_method_args, "--alpb", "ether", "--opt", "--input", xcontrol.name, "--chrg", str(charge), "--uhf", str(uhf)],
            work,
            work / "gfnff.stdout.log",
            work / "gfnff.stderr.log",
            threads,
            timeout_seconds,
        )
        optimized = work / "xtbopt.xyz"
        if cleanup["returncode"] != 0 or not optimized.exists():
            return {
                "pose_id": pose["pose_id"], "score_rank": pose["score_rank"],
                "selection_bucket": pose["selection_bucket"], "status": f"{cleanup_method}_failed", "cleanup": cleanup,
            }
        shutil.copy2(optimized, cleaned_xyz)

    single_point = run_timed(
        [str(xtb_path), cleaned_xyz.name, "--gfn", "2", "--alpb", "ether", "--chrg", str(charge), "--uhf", str(uhf)],
        work,
        work / "gfn2.stdout.log",
        work / "gfn2.stderr.log",
        threads,
        timeout_seconds,
    )
    text = (work / "gfn2.stdout.log").read_text(encoding="utf-8")
    energy = last_match(ENERGY_RE, text)
    gap = last_match(GAP_RE, text)
    charges_path = work / "charges"
    charges = [float(value) for value in charges_path.read_text(encoding="utf-8").split()] if charges_path.exists() else []
    return {
        "pose_id": pose["pose_id"],
        "score_rank": pose["score_rank"],
        "selection_bucket": pose["selection_bucket"],
        "uff_pose_score": pose["uff_pose_score"],
        "selection_cluster_size": pose["selection_cluster_size"],
        "sampling_prior": pose["sampling_prior"],
        "status": "success" if single_point["returncode"] == 0 and energy is not None else "gfn2_failed",
        "cleanup": cleanup,
        "single_point": single_point,
        "gfn2_total_energy_hartree": energy,
        "homo_lumo_gap_ev": gap,
        "charge_count": len(charges),
        "molecular_charge": charge,
        "unpaired_electrons": uhf,
        "charge_min": min(charges) if charges else None,
        "charge_max": max(charges) if charges else None,
        "artifacts": {
            "cleaned_xyz": str(cleaned_xyz.relative_to(ROOT)),
            "charges": str(charges_path.relative_to(ROOT)) if charges_path.exists() else None,
            "wbo": str((work / "wbo").relative_to(ROOT)) if (work / "wbo").exists() else None,
        },
    }


def boltzmann_weights(
    energies_hartree: Iterable[float],
    priors: Iterable[float],
    temperature_k: float,
) -> np.ndarray:
    energies = np.asarray(list(energies_hartree), dtype=float)
    prior = np.asarray(list(priors), dtype=float)
    if energies.size == 0 or energies.size != prior.size or np.any(prior < 0) or prior.sum() <= 0:
        raise ValueError("Energies and non-negative, non-zero priors must have equal non-zero length")
    delta = (energies - energies.min()) * HARTREE_TO_KCAL_MOL
    logits = -delta / (R_KCAL_MOL_K * temperature_k) + np.log(np.maximum(prior, 1e-300))
    logits -= logits.max()
    weights = np.exp(logits)
    return weights / weights.sum()


def uncertain_population_summary(
    energies_hartree: Iterable[float],
    priors: Iterable[float],
    temperature_k: float,
    sigma_kcal_mol: float = 1.0,
    draws: int = 2000,
    seed: int = 20260907,
) -> dict[str, Any]:
    energies = np.asarray(list(energies_hartree), dtype=float)
    prior = np.asarray(list(priors), dtype=float)
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(draws):
        perturbed = energies + rng.normal(0.0, sigma_kcal_mol / HARTREE_TO_KCAL_MOL, size=len(energies))
        samples.append(boltzmann_weights(perturbed, prior, temperature_k))
    matrix = np.asarray(samples)
    mean_weights = matrix.mean(axis=0)
    entropy = -float(np.sum(mean_weights * np.log(np.maximum(mean_weights, 1e-300))))
    return {
        "temperature_k": temperature_k,
        "energy_noise_sigma_kcal_mol": sigma_kcal_mol,
        "draw_count": draws,
        "mean_weights": mean_weights.tolist(),
        "weight_std": matrix.std(axis=0).tolist(),
        "entropy_nats": entropy,
        "effective_pose_count_entropy": math.exp(entropy),
        "effective_pose_count_kish": float(1.0 / np.sum(mean_weights**2)),
        "max_weight": float(mean_weights.max()),
    }


def angle_degrees(left: np.ndarray, vertex: np.ndarray, right: np.ndarray) -> float:
    a = left - vertex
    b = right - vertex
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator <= 1e-12:
        return 0.0
    return math.degrees(math.acos(float(np.clip(np.dot(a, b) / denominator, -1.0, 1.0))))


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, value))))


def load_stage2_interaction() -> Any:
    path = ROOT / "scripts/stage2_pose_interaction.py"
    spec = importlib.util.spec_from_file_location("pose_probability_stage2_interaction", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def parse_wbo(path: Path) -> dict[tuple[int, int], float]:
    values: dict[tuple[int, int], float] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) >= 3:
            left, right = int(fields[0]) - 1, int(fields[1]) - 1
            values[tuple(sorted((left, right)))] = float(fields[2])
    return values


def pose_site_descriptors(
    record: dict[str, Any], pose: dict[str, Any], result: dict[str, Any], output: Path
) -> list[dict[str, Any]]:
    """Build label-blind per-site steric/electronic descriptors for one pose."""
    stage2 = load_stage2_interaction()
    geometry_path = ROOT / result["artifacts"]["cleaned_xyz"]
    symbols, coordinates = parse_xyz(geometry_path)
    charge_path = ROOT / result["artifacts"]["charges"]
    charges = np.asarray([float(value) for value in charge_path.read_text(encoding="utf-8").split()])
    wbo = parse_wbo(output / result["pose_id"] / "wbo")
    molecule = stage2.stage1_pose_molecule(pose["input_nitrene_smiles"])
    atom_map = stage2.map_ids_to_stage1_atom_indices(record, molecule)
    stage1_to_assembly = stage2.stage1_index_to_assembly_index(molecule, int(pose["frozen_core_atom_count"]))
    nitrene_index = stage1_to_assembly[0]
    nitrene = coordinates[nitrene_index]
    core = coordinates[: int(pose["frozen_core_atom_count"])]
    rows = []
    for site in record["reaction_center"]["candidate_sites"]:
        stage1_carbon = atom_map.get(site["atom_map_id"])
        if stage1_carbon is None or stage1_carbon not in stage1_to_assembly:
            continue
        carbon_index = stage1_to_assembly[stage1_carbon]
        hydrogen_stage1 = [
            neighbor.GetIdx()
            for neighbor in molecule.GetAtomWithIdx(stage1_carbon).GetNeighbors()
            if neighbor.GetSymbol() == "H" and neighbor.GetIdx() in stage1_to_assembly
        ]
        if not hydrogen_stage1:
            continue
        hydrogen_index = min(
            (stage1_to_assembly[index] for index in hydrogen_stage1),
            key=lambda index: float(np.linalg.norm(coordinates[index] - nitrene)),
        )
        carbon, hydrogen = coordinates[carbon_index], coordinates[hydrogen_index]
        midpoint = 0.5 * (nitrene + hydrogen)
        n_h = float(np.linalg.norm(nitrene - hydrogen))
        n_h_c_angle = angle_degrees(nitrene, hydrogen, carbon)
        core_to_midpoint = np.linalg.norm(core - midpoint, axis=1)
        core_to_h = np.linalg.norm(core - hydrogen, axis=1)
        min_core_midpoint = float(core_to_midpoint.min())
        min_core_h = float(core_to_h.min())
        pocket_count_3a = int(np.count_nonzero(core_to_midpoint <= 3.0))
        distance_score = sigmoid((3.0 - n_h) / 0.30)
        angle_score = sigmoid((n_h_c_angle - 145.0) / 8.0)
        clearance_score = sigmoid((min_core_h - 1.25) / 0.15)
        ready_score = distance_score * angle_score * clearance_score
        rows.append(
            {
                "candidate_site_id": site["site_id"],
                "candidate_atom_map_id": site["atom_map_id"],
                "site_type": site["site_type"],
                "n_h_distance_angstrom": n_h,
                "n_h_c_angle_degrees": n_h_c_angle,
                "minimum_core_midpoint_distance_angstrom": min_core_midpoint,
                "minimum_core_h_distance_angstrom": min_core_h,
                "core_atom_count_within_3a_of_midpoint": pocket_count_3a,
                "nitrene_charge": float(charges[nitrene_index]),
                "candidate_carbon_charge": float(charges[carbon_index]),
                "transferred_h_charge": float(charges[hydrogen_index]),
                "candidate_c_h_wiberg_bond_order": wbo.get(tuple(sorted((carbon_index, hydrogen_index))), 0.0),
                "reaction_ready_score": ready_score,
            }
        )
    return rows


def weighted_mean_std(values: list[float], weights: np.ndarray) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    mean = float(np.sum(weights * array))
    return mean, float(math.sqrt(max(0.0, np.sum(weights * (array - mean) ** 2))))


def representation_demo(
    report: dict[str, Any], record: dict[str, Any], successes: list[dict[str, Any]], population: dict[str, Any], output: Path
) -> dict[str, Any]:
    poses = {row["pose_id"]: row for row in report["pose_records"]}
    weights = np.asarray(population["mean_weights"], dtype=float)
    per_pose = []
    site_mass: dict[str, float] = {}
    for result, weight in zip(successes, weights, strict=True):
        sites = pose_site_descriptors(record, poses[result["pose_id"]], result, output)
        for site in sites:
            site_mass[site["candidate_site_id"]] = site_mass.get(site["candidate_site_id"], 0.0) + weight * site["reaction_ready_score"]
        per_pose.append({"pose_id": result["pose_id"], "pose_weight": float(weight), "candidate_sites": sites})
    total_site_mass = sum(site_mass.values())
    site_probabilities = {
        key: value / total_site_mass if total_site_mass > 0 else 0.0 for key, value in sorted(site_mass.items())
    }
    sorted_probabilities = sorted(site_probabilities.values(), reverse=True)
    pose_max_ready = [max((site["reaction_ready_score"] for site in row["candidate_sites"]), default=0.0) for row in per_pose]
    pose_best_clearance = [max((site["minimum_core_h_distance_angstrom"] for site in row["candidate_sites"]), default=0.0) for row in per_pose]
    gaps = [float(row["homo_lumo_gap_ev"] or 0.0) for row in successes]
    ready_mean, ready_std = weighted_mean_std(pose_max_ready, weights)
    clearance_mean, clearance_std = weighted_mean_std(pose_best_clearance, weights)
    gap_mean, gap_std = weighted_mean_std(gaps, weights)
    site_entropy = -sum(value * math.log(max(value, 1e-300)) for value in site_probabilities.values())
    return {
        "schema_version": "bw-rpse-representation-demo-v1",
        "status": "five_pose_plumbing_demo_not_model_result",
        "substrate_id": record["substrate_id"],
        "candidate_site_policy": "all_candidate_c_h_sites_label_blind",
        "per_pose": per_pose,
        "site_probabilities": site_probabilities,
        "feature_blocks": {
            "population": {
                "entropy_nats": population["entropy_nats"],
                "effective_pose_count_entropy": population["effective_pose_count_entropy"],
                "maximum_pose_weight": population["max_weight"],
            },
            "steric_reaction_ready": {
                "best_site_ready_score_weighted_mean": ready_mean,
                "best_site_ready_score_weighted_std": ready_std,
                "best_site_clearance_weighted_mean": clearance_mean,
                "best_site_clearance_weighted_std": clearance_std,
            },
            "electronic": {
                "homo_lumo_gap_ev_weighted_mean": gap_mean,
                "homo_lumo_gap_ev_weighted_std": gap_std,
            },
            "site_competition": {
                "leading_site_probability": sorted_probabilities[0] if sorted_probabilities else 0.0,
                "leading_minus_second_probability": (
                    sorted_probabilities[0] - sorted_probabilities[1] if len(sorted_probabilities) > 1 else 0.0
                ),
                "site_probability_entropy_nats": site_entropy,
            },
        },
        "warning": "Collapsed pose weights make this demonstration unsuitable for model fitting; an ensemble-energy repair is required.",
    }


def resource_estimates(successes: list[dict[str, Any]], pose_count: int = 100, substrate_count: int = 38) -> dict[str, Any]:
    per_pose = [row["cleanup"]["wall_seconds"] + row["single_point"]["wall_seconds"] for row in successes]
    mean_seconds = float(np.mean(per_pose))
    p90_seconds = float(np.quantile(per_pose, 0.9))
    return {
        "observed_success_count": len(successes),
        "mean_seconds_per_pose": mean_seconds,
        "p90_seconds_per_pose": p90_seconds,
        "estimated_100_pose_serial_hours_mean": mean_seconds * pose_count / 3600.0,
        "estimated_100_pose_serial_hours_p90": p90_seconds * pose_count / 3600.0,
        "estimated_38_substrate_serial_hours_mean": mean_seconds * pose_count * substrate_count / 3600.0,
        "estimated_38_substrate_serial_hours_p90": p90_seconds * pose_count * substrate_count / 3600.0,
        "parallel_estimates_are_idealized": True,
        "estimated_38_substrate_hours_at_4_workers_mean": mean_seconds * pose_count * substrate_count / 3600.0 / 4.0,
    }


def benchmark(args: argparse.Namespace) -> dict[str, Any]:
    report = read_json(args.report)
    selected = select_poses(report, args.count)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    cleanup_method = "none" if args.skip_cleanup else args.cleanup_method
    def execute(pose: dict[str, Any]) -> dict[str, Any]:
        return run_pose(
            pose, output, args.xtb, args.threads, cleanup_method, args.charge, args.uhf, args.timeout_seconds
        )
    if args.workers == 1:
        rows = [execute(pose) for pose in selected]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            rows = list(executor.map(execute, selected))
    successes = [row for row in rows if row["status"] == "success"]
    record = next(row for row in read_jsonl(args.records) if row["substrate_id"] == "1a")
    temperature_k = float(record["condition"]["temperature_c"]) + 273.15
    population = None
    if len(successes) >= 2:
        population = uncertain_population_summary(
            [row["gfn2_total_energy_hartree"] for row in successes],
            [row["sampling_prior"] for row in successes],
            temperature_k,
        )
        for row, weight, weight_std in zip(successes, population["mean_weights"], population["weight_std"], strict=True):
            row["uncertain_boltzmann_weight_mean"] = weight
            row["uncertain_boltzmann_weight_std"] = weight_std
        demo = representation_demo(report, record, successes, population, output)
        write_json(output / "representation-demo.json", demo)
    result = {
        "schema_version": "pose-probability-five-pose-benchmark-v1",
        "method": (
            "direct GFN2-xTB/ALPB(ether) single point on existing UFF-cleaned frozen-core assembly"
            if cleanup_method == "none" else
            f"frozen-core {cleanup_method.upper()} optimization then GFN2-xTB/ALPB(ether) single point"
        ),
        "substrate_id": "1a",
        "requested_pose_count": args.count,
        "success_count": len(successes),
        "failed_count": len(rows) - len(successes),
        "threads_per_process": args.threads,
        "parallel_workers": args.workers,
        "cleanup_method": cleanup_method,
        "molecular_charge": args.charge,
        "unpaired_electrons": args.uhf,
        "pose_results": rows,
        "uncertain_population": population,
        "representation_demo_path": str((output / "representation-demo.json").relative_to(ROOT)) if population else None,
        "resource_estimates": resource_estimates(successes) if successes else None,
        "warnings": [
            "The five-pose population is a plumbing demonstration, not a converged ensemble or predictive result.",
            "Charge and UHF settings remain a scientific calibration variable; alternate defensible states require an explicit sensitivity ablation.",
            "Wall-time extrapolation is hardware- and concurrency-dependent.",
        ],
    }
    write_json(output / "benchmark.json", result)
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    result.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--xtb", type=Path, default=DEFAULT_XTB)
    result.add_argument("--count", type=int, default=5)
    result.add_argument("--threads", type=int, default=1)
    result.add_argument("--skip-cleanup", action="store_true")
    result.add_argument("--cleanup-method", choices=("gfnff", "gfn2"), default="gfnff")
    result.add_argument("--workers", type=int, default=1)
    result.add_argument("--timeout-seconds", type=int, default=1800)
    result.add_argument("--charge", type=int, default=0)
    result.add_argument("--uhf", type=int, default=1, help="Number of unpaired electrons; one encodes the defined doublet intermediate")
    return result


if __name__ == "__main__":
    payload = benchmark(parser().parse_args())
    print(json.dumps({"success_count": payload["success_count"], "resource_estimates": payload["resource_estimates"]}, indent=2))

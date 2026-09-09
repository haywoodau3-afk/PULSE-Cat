#!/usr/bin/env python3
"""Run full-scope ee benchmarks with 7:2:1 target-holdout splits."""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
from pathlib import Path
from typing import Any

import lightgbm
import numpy
import scipy
import sklearn
from rdkit import Chem, DataStructs
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdFingerprintGenerator, rdMolDescriptors
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import warnings


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_POSE_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"
DEFAULT_POSE_INTERACTION = ROOT / "data/jacs_2025/stage2/features/pose-interaction.jsonl"
DEFAULT_MATRIX = ROOT / "data/jacs_2025/stage2/features/full-scope-structure-ee-matrix.csv"
DEFAULT_REPORT = ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-model-benchmark.json"
DEFAULT_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-model-predictions.csv"
DEFAULT_SPLITS = ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-splits.json"
DEFAULT_POSE_MATRIX = ROOT / "data/jacs_2025/stage2/features/full-scope-structure-pose-ee-matrix.csv"
DEFAULT_POSE_REPORT = ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-pose-model-benchmark.json"
DEFAULT_POSE_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-pose-model-predictions.csv"
DEFAULT_COMPARISON_REPORT = ROOT / "data/jacs_2025/stage2/reports/full-scope-model-comparison.json"
DEFAULT_COMPARISON_TABLE = ROOT / "data/jacs_2025/stage2/reports/full-scope-model-comparison.csv"
DEFAULT_YIELD_MATRIX = ROOT / "data/jacs_2025/stage2/features/full-scope-structure-yield-matrix.csv"
DEFAULT_YIELD_REPORT = ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-yield-model-benchmark.json"
DEFAULT_YIELD_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-yield-model-predictions.csv"
DEFAULT_YIELD_POSE_MATRIX = ROOT / "data/jacs_2025/stage2/features/full-scope-structure-pose-yield-matrix.csv"
DEFAULT_YIELD_POSE_REPORT = ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-pose-yield-model-benchmark.json"
DEFAULT_YIELD_POSE_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/full-scope-structure-pose-yield-model-predictions.csv"
DEFAULT_YIELD_COMPARISON_REPORT = ROOT / "data/jacs_2025/stage2/reports/full-scope-yield-model-comparison.json"
DEFAULT_YIELD_COMPARISON_TABLE = ROOT / "data/jacs_2025/stage2/reports/full-scope-yield-model-comparison.csv"
DEFAULT_FAMILY_EE_STRUCTURE_REPORT = ROOT / "data/jacs_2025/stage2/reports/family-heldout-structure-ee-model-benchmark.json"
DEFAULT_FAMILY_EE_STRUCTURE_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/family-heldout-structure-ee-model-predictions.csv"
DEFAULT_FAMILY_EE_POSE_REPORT = ROOT / "data/jacs_2025/stage2/reports/family-heldout-structure-pose-ee-model-benchmark.json"
DEFAULT_FAMILY_EE_POSE_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/family-heldout-structure-pose-ee-model-predictions.csv"
DEFAULT_FAMILY_EE_COMPARISON_REPORT = ROOT / "data/jacs_2025/stage2/reports/family-heldout-ee-model-comparison.json"
DEFAULT_FAMILY_EE_COMPARISON_TABLE = ROOT / "data/jacs_2025/stage2/reports/family-heldout-ee-model-comparison.csv"
DEFAULT_FAMILY_YIELD_STRUCTURE_REPORT = ROOT / "data/jacs_2025/stage2/reports/family-heldout-structure-yield-model-benchmark.json"
DEFAULT_FAMILY_YIELD_STRUCTURE_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/family-heldout-structure-yield-model-predictions.csv"
DEFAULT_FAMILY_YIELD_POSE_REPORT = ROOT / "data/jacs_2025/stage2/reports/family-heldout-structure-pose-yield-model-benchmark.json"
DEFAULT_FAMILY_YIELD_POSE_PREDICTIONS = ROOT / "data/jacs_2025/stage2/reports/family-heldout-structure-pose-yield-model-predictions.csv"
DEFAULT_FAMILY_YIELD_COMPARISON_REPORT = ROOT / "data/jacs_2025/stage2/reports/family-heldout-yield-model-comparison.json"
DEFAULT_FAMILY_YIELD_COMPARISON_TABLE = ROOT / "data/jacs_2025/stage2/reports/family-heldout-yield-model-comparison.csv"
DEFAULT_FINAL_STAGE2_REPORT = ROOT / "data/jacs_2025/stage2/reports/stage-2-final-report.md"
MORGAN_RADIUS = 2
MORGAN_BITS = 512
BAYESIAN_BOOTSTRAP_DRAWS = 20000
BAYESIAN_BOOTSTRAP_SEED = 20260731
AGGREGATIONS = ["count", "min", "q05", "median", "mean", "q95", "max", "std"]
EXCLUDED_EE_RECORDS = {
    "1an": "not_applicable_achiral ee",
    "1ad": "excluded_after_review because 0% ee is likely undetermined by separation problem",
    "1z": "excluded_from_matched_cohort because the zero_curated ee record is not retained by the later 38-substrate protocols",
}
TARGET_LABELS = {"ee": "ee_percent", "yield": "isolated_yield_percent"}


PHYS_DESCRIPTORS = {
    "molecular_weight": Descriptors.MolWt,
    "exact_molecular_weight": Descriptors.ExactMolWt,
    "heavy_atom_molecular_weight": Descriptors.HeavyAtomMolWt,
    "num_valence_electrons": Descriptors.NumValenceElectrons,
    "bertz_ct": Descriptors.BertzCT,
    "mol_logp": Crippen.MolLogP,
    "tpsa": rdMolDescriptors.CalcTPSA,
    "labute_asa": rdMolDescriptors.CalcLabuteASA,
    "fraction_csp3": rdMolDescriptors.CalcFractionCSP3,
    "rotatable_bond_count": Lipinski.NumRotatableBonds,
    "h_donor_count": Lipinski.NumHDonors,
    "h_acceptor_count": Lipinski.NumHAcceptors,
    "ring_count": rdMolDescriptors.CalcNumRings,
    "aromatic_ring_count": rdMolDescriptors.CalcNumAromaticRings,
    "aliphatic_ring_count": rdMolDescriptors.CalcNumAliphaticRings,
    "saturated_ring_count": rdMolDescriptors.CalcNumSaturatedRings,
    "heteroatom_count": rdMolDescriptors.CalcNumHeteroatoms,
    "amide_bond_count": rdMolDescriptors.CalcNumAmideBonds,
    "bridgehead_atom_count": rdMolDescriptors.CalcNumBridgeheadAtoms,
    "spiro_atom_count": rdMolDescriptors.CalcNumSpiroAtoms,
    "atom_stereo_center_count": rdMolDescriptors.CalcNumAtomStereoCenters,
    "unspecified_atom_stereo_center_count": rdMolDescriptors.CalcNumUnspecifiedAtomStereoCenters,
}
ELEMENTS = ["C", "H", "N", "O", "F", "Si", "P", "S", "Cl"]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def molecule_from_record(record: dict[str, Any]) -> Chem.Mol:
    smiles = record["structure"]["azide_smiles"]
    molecule = Chem.MolFromSmiles(smiles, sanitize=True)
    if molecule is None:
        raise ValueError(f"{record['substrate_id']}: azide SMILES does not parse")
    return molecule


def fingerprint(molecule: Chem.Mol, n_bits: int = MORGAN_BITS) -> list[int]:
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=MORGAN_RADIUS, fpSize=n_bits, includeChirality=True)
    bit_vector = generator.GetFingerprint(molecule)
    array = numpy.zeros((n_bits,), dtype=int)
    DataStructs.ConvertToNumpyArray(bit_vector, array)
    return array.astype(int).tolist()


def tanimoto(left: list[int], right: list[int]) -> float:
    left_array = numpy.array(left, dtype=bool)
    right_array = numpy.array(right, dtype=bool)
    intersection = numpy.logical_and(left_array, right_array).sum()
    union = numpy.logical_or(left_array, right_array).sum()
    return float(intersection / union) if union else 0.0


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def add_numeric_features(target: dict[str, float], prefix: str, values: dict[str, Any]) -> None:
    for key, value in values.items():
        if is_number(value):
            target[f"{prefix}.{key}"] = float(value)
        elif isinstance(value, bool):
            target[f"{prefix}.{key}"] = float(value)


def add_one_hot(target: dict[str, float], prefix: str, key: str, value: Any) -> None:
    if value is not None:
        target[f"{prefix}.{key}={value}"] = 1.0


def quantile(values: list[float], fraction: float) -> float:
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = fraction * (len(sorted_values) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    lower = sorted_values[lower_index]
    upper = sorted_values[upper_index]
    return lower + (upper - lower) * (position - lower_index)


def aggregate_values(values: list[float]) -> dict[str, float]:
    array = numpy.array(values, dtype=float)
    return {
        "count": float(len(values)),
        "min": float(array.min()),
        "q05": quantile(values, 0.05),
        "median": float(numpy.median(array)),
        "mean": float(array.mean()),
        "q95": quantile(values, 0.95),
        "max": float(array.max()),
        "std": float(array.std()),
    }


def aggregate_pose_interactions(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    values_by_substrate: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        substrate_id = row["substrate_id"]
        values_by_substrate.setdefault(substrate_id, {})
        features = row["feature_blocks"]["pose_interaction"]
        for key, value in features.items():
            if is_number(value) or isinstance(value, bool):
                values_by_substrate[substrate_id].setdefault(key, []).append(float(value))

    aggregated: dict[str, dict[str, float]] = {}
    for substrate_id, feature_values in values_by_substrate.items():
        substrate_features = {}
        for key, values in feature_values.items():
            for agg_key, agg_value in aggregate_values(values).items():
                substrate_features[f"{key}.{agg_key}"] = agg_value
        aggregated[substrate_id] = substrate_features
    return aggregated


def element_counts(molecule: Chem.Mol) -> dict[str, float]:
    with_hydrogens = Chem.AddHs(molecule)
    counts = {f"element_count_{element}": 0.0 for element in ELEMENTS}
    counts["element_count_other"] = 0.0
    for atom in with_hydrogens.GetAtoms():
        key = f"element_count_{atom.GetSymbol()}"
        if key in counts:
            counts[key] += 1.0
        else:
            counts["element_count_other"] += 1.0
    return counts


def featurize_record(record: dict[str, Any]) -> tuple[dict[str, float], list[int]]:
    molecule = molecule_from_record(record)
    features = {name: float(fn(molecule)) for name, fn in PHYS_DESCRIPTORS.items()}
    features.update(element_counts(molecule))
    features["atom_count"] = float(Chem.AddHs(molecule).GetNumAtoms())
    features["heavy_atom_count"] = float(molecule.GetNumHeavyAtoms())
    features["formal_charge"] = float(Chem.GetFormalCharge(molecule))
    bit_vector = fingerprint(molecule)
    for index, value in enumerate(bit_vector):
        features[f"morgan_{MORGAN_RADIUS}_{MORGAN_BITS}_bit_{index}"] = float(value)
    return features, bit_vector


def reaction_center_features(record: dict[str, Any]) -> dict[str, float]:
    features: dict[str, float] = {}
    reaction_center = record["reaction_center"]
    reported_site = reaction_center["reported_reactive_site"]
    candidate_sites = reaction_center["candidate_sites"]
    add_numeric_features(features, "reaction_center.reported_site", reported_site)
    add_one_hot(features, "reaction_center.reported_site", "site_type", reported_site.get("site_type"))
    add_one_hot(features, "reaction_center", "assignment_method", reaction_center.get("assignment_method"))
    features["reaction_center.candidate_site_count"] = float(len(candidate_sites))
    for site in candidate_sites:
        site_type = site.get("site_type")
        if site_type:
            features[f"reaction_center.candidate_site_type_count.{site_type}"] = (
                features.get(f"reaction_center.candidate_site_type_count.{site_type}", 0.0) + 1.0
            )
    return features


def add_pose_aware_features(
    row_features: dict[str, float],
    record: dict[str, Any],
    pose_summary_by_id: dict[str, dict[str, Any]],
    pose_interaction_by_id: dict[str, dict[str, float]],
) -> None:
    substrate_id = record["substrate_id"]
    if substrate_id not in pose_summary_by_id:
        raise ValueError(f"{substrate_id}: missing pose-summary features")
    if substrate_id not in pose_interaction_by_id:
        raise ValueError(f"{substrate_id}: missing pose-interaction features")
    row_features.update(reaction_center_features(record))
    add_numeric_features(
        row_features,
        "pose_summary",
        pose_summary_by_id[substrate_id]["feature_blocks"]["pose_summary"],
    )
    add_numeric_features(row_features, "pose_interaction", pose_interaction_by_id[substrate_id])


def target_value(record: dict[str, Any], target: str) -> float | None:
    if target == "ee":
        if record["substrate_id"] in EXCLUDED_EE_RECORDS:
            return None
        outcome = record["outcome"]
        ee_percent = outcome.get("ee_percent")
        if isinstance(ee_percent, int | float) and outcome.get("ee_status") in {"reported", "zero_curated"}:
            return float(ee_percent)
        return None
    if target == "yield":
        value = record["outcome"].get("isolated_yield_percent")
        return float(value) if isinstance(value, int | float) else None
    raise ValueError(f"Unknown target: {target}")


def excluded_records_for_target(records_path: Path, target: str) -> list[dict[str, str]]:
    if target == "ee":
        return [
            {"substrate_id": substrate_id, "reason": reason}
            for substrate_id, reason in sorted(EXCLUDED_EE_RECORDS.items())
        ]
    return [
        {"substrate_id": record["substrate_id"], "reason": f"missing numeric {TARGET_LABELS[target]}"}
        for record in read_jsonl(records_path)
        if target_value(record, target) is None
    ]


def modelable_records(records_path: Path, target: str = "ee") -> list[dict[str, Any]]:
    records = []
    for record in read_jsonl(records_path):
        if target_value(record, target) is not None:
            records.append(record)
    return sorted(records, key=lambda row: row["substrate_id"])


def build_feature_rows(
    records_path: Path,
    feature_set: str = "structure_only",
    pose_summary_path: Path = DEFAULT_POSE_SUMMARY,
    pose_interaction_path: Path = DEFAULT_POSE_INTERACTION,
    target: str = "ee",
) -> tuple[list[dict[str, Any]], list[str]]:
    if feature_set not in {"structure_only", "structure_pose"}:
        raise ValueError(f"Unknown feature set: {feature_set}")
    pose_summary_by_id = {}
    pose_interaction_by_id = {}
    if feature_set == "structure_pose":
        pose_summary_by_id = {row["substrate_id"]: row for row in read_jsonl(pose_summary_path)}
        pose_interaction_by_id = aggregate_pose_interactions(read_jsonl(pose_interaction_path))

    rows = []
    target_column = TARGET_LABELS[target]
    for record in modelable_records(records_path, target):
        features, fp = featurize_record(record)
        if feature_set == "structure_pose":
            add_pose_aware_features(features, record, pose_summary_by_id, pose_interaction_by_id)
        rows.append(
            {
                "substrate_id": record["substrate_id"],
                "reaction_id": record["reaction_id"],
                "family_id": record["family"]["family_id"],
                "catalyst_id": record["catalyst_id"],
                "temperature_c": record["condition"]["temperature_c"],
                target_column: float(target_value(record, target)),
                "target_name": target,
                "target_value": float(target_value(record, target)),
                "yield_qualifier": record["outcome"].get("yield_qualifier"),
                "ee_status": record["outcome"]["ee_status"],
                "azide_smiles": record["structure"]["azide_smiles"],
                "feature_set": feature_set,
                "features": features,
                "fingerprint": fp,
            }
        )
    feature_names = sorted({name for row in rows for name in row["features"]})
    return rows, feature_names


def write_matrix(path: Path, rows: list[dict[str, Any]], feature_names: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "substrate_id",
        "reaction_id",
        "family_id",
        "catalyst_id",
        "temperature_c",
        "target_name",
        "target_value",
        "ee_percent",
        "isolated_yield_percent",
        "yield_qualifier",
        "ee_status",
        "azide_smiles",
        "feature_set",
    ] + feature_names
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            output = {key: row.get(key, "") for key in columns[:13]}
            output.update({name: row["features"].get(name, 0.0) for name in feature_names})
            writer.writerow(output)


def distance_from_similarity(left: list[int], right: list[int]) -> float:
    return 1.0 - tanimoto(left, right)


def maxmin_diverse_indices(candidate_indices: list[int], rows: list[dict[str, Any]], count: int, target_index: int) -> list[int]:
    if count >= len(candidate_indices):
        return list(candidate_indices)
    selected = [
        max(
            candidate_indices,
            key=lambda index: (
                distance_from_similarity(rows[index]["fingerprint"], rows[target_index]["fingerprint"]),
                rows[index]["substrate_id"],
            ),
        )
    ]
    remaining = [index for index in candidate_indices if index not in selected]
    while len(selected) < count:
        next_index = max(
            remaining,
            key=lambda index: (
                min(distance_from_similarity(rows[index]["fingerprint"], rows[selected_index]["fingerprint"]) for selected_index in selected),
                distance_from_similarity(rows[index]["fingerprint"], rows[target_index]["fingerprint"]),
                rows[index]["substrate_id"],
            ),
        )
        selected.append(next_index)
        remaining.remove(next_index)
    return selected


def build_splits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    train_count = round((7 / 9) * (len(rows) - 1))
    splits = []
    for target_index, row in enumerate(rows):
        candidates = [index for index in range(len(rows)) if index != target_index]
        train_indices = maxmin_diverse_indices(candidates, rows, train_count, target_index)
        validation_indices = [index for index in candidates if index not in train_indices]
        splits.append(
            {
                "target_index": target_index,
                "target_indices": [target_index],
                "split_id": row["substrate_id"],
                "heldout_family_id": None,
                "target_substrate_id": row["substrate_id"],
                "train_indices": train_indices,
                "validation_indices": validation_indices,
                "train_substrate_ids": [rows[index]["substrate_id"] for index in train_indices],
                "validation_substrate_ids": [rows[index]["substrate_id"] for index in validation_indices],
            }
        )
    return splits


def build_family_splits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    family_ids = sorted({row["family_id"] for row in rows})
    splits = []
    for family_id in family_ids:
        target_indices = [index for index, row in enumerate(rows) if row["family_id"] == family_id]
        candidate_indices = [index for index in range(len(rows)) if index not in target_indices]
        if len(candidate_indices) < 4:
            continue
        validation_count = max(1, round(0.2 * len(candidate_indices)))
        train_count = len(candidate_indices) - validation_count
        seed_target = target_indices[0]
        train_indices = maxmin_diverse_indices(candidate_indices, rows, train_count, seed_target)
        validation_indices = [index for index in candidate_indices if index not in train_indices]
        splits.append(
            {
                "target_index": target_indices[0],
                "target_indices": target_indices,
                "split_id": family_id,
                "heldout_family_id": family_id,
                "target_substrate_id": "|".join(rows[index]["substrate_id"] for index in target_indices),
                "target_substrate_ids": [rows[index]["substrate_id"] for index in target_indices],
                "train_indices": train_indices,
                "validation_indices": validation_indices,
                "train_substrate_ids": [rows[index]["substrate_id"] for index in train_indices],
                "validation_substrate_ids": [rows[index]["substrate_id"] for index in validation_indices],
            }
        )
    return splits


def matrix_arrays(rows: list[dict[str, Any]], feature_names: list[str]) -> tuple[numpy.ndarray, numpy.ndarray]:
    x = numpy.array([[row["features"].get(name, 0.0) for name in feature_names] for row in rows], dtype=float)
    y = numpy.array([row["target_value"] for row in rows], dtype=float)
    active = x.std(axis=0) > 0
    return x[:, active], y


def model_grid() -> dict[str, list[Any]]:
    return {
        "ridge_regression": [
            make_pipeline(StandardScaler(), Ridge(alpha=alpha))
            for alpha in [0.1, 1.0, 10.0, 100.0]
        ],
        "elastic_net": [
            make_pipeline(StandardScaler(), ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=20000, random_state=0))
            for alpha in [0.01, 0.1, 1.0, 10.0]
            for l1_ratio in [0.2, 0.5, 0.8]
        ],
        "lightgbm": [
            lightgbm.LGBMRegressor(
                n_estimators=n_estimators,
                learning_rate=learning_rate,
                num_leaves=num_leaves,
                min_child_samples=2,
                random_state=0,
                verbosity=-1,
            )
            for n_estimators in [25, 75]
            for learning_rate in [0.03, 0.1]
            for num_leaves in [3, 7]
        ],
        "gaussian_process": [
            make_pipeline(
                StandardScaler(),
                GaussianProcessRegressor(
                    kernel=ConstantKernel(1.0) * RBF(length_scale=length_scale) + WhiteKernel(noise_level=noise_level),
                    alpha=1e-6,
                    normalize_y=True,
                    random_state=0,
                    n_restarts_optimizer=0,
                ),
            )
            for length_scale in [0.5, 1.0, 2.0]
            for noise_level in [1.0, 10.0]
        ],
    }


def estimator_label(estimator: Any) -> str:
    final = estimator.steps[-1][1] if hasattr(estimator, "steps") else estimator
    params = final.get_params()
    interesting = {
        key: params[key]
        for key in ["alpha", "l1_ratio", "n_estimators", "learning_rate", "num_leaves"]
        if key in params
    }
    if isinstance(final, GaussianProcessRegressor):
        interesting["kernel"] = str(final.kernel)
    return json.dumps(interesting, sort_keys=True)


def fit_predict(estimator: Any, x_train: numpy.ndarray, y_train: numpy.ndarray, x_pred: numpy.ndarray) -> tuple[numpy.ndarray, numpy.ndarray | None]:
    model = clone(estimator)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(x_train, y_train)
    final = model.steps[-1][1] if hasattr(model, "steps") else model
    if isinstance(final, GaussianProcessRegressor):
        pred, std = model.predict(x_pred, return_std=True)
        return numpy.asarray(pred, dtype=float), numpy.asarray(std, dtype=float)
    return numpy.asarray(model.predict(x_pred), dtype=float), None


def choose_model(model_name: str, estimators: list[Any], split: dict[str, Any], x: numpy.ndarray, y: numpy.ndarray) -> dict[str, Any]:
    train = split["train_indices"]
    validation = split["validation_indices"]
    best: dict[str, Any] | None = None
    for estimator in estimators:
        pred, _ = fit_predict(estimator, x[train], y[train], x[validation])
        mae = float(mean_absolute_error(y[validation], pred))
        if best is None or mae < best["validation_mae"]:
            best = {
                "model_name": model_name,
                "estimator": estimator,
                "estimator_params": estimator_label(estimator),
                "validation_mae": mae,
            }
    assert best is not None
    return best


def empirical_interval(prediction: float, validation_residuals: numpy.ndarray, gp_std: float | None) -> dict[str, float | None]:
    if len(validation_residuals):
        low80 = float(prediction + numpy.quantile(validation_residuals, 0.10))
        high80 = float(prediction + numpy.quantile(validation_residuals, 0.90))
        low95 = float(prediction + numpy.quantile(validation_residuals, 0.025))
        high95 = float(prediction + numpy.quantile(validation_residuals, 0.975))
    else:
        low80 = high80 = low95 = high95 = prediction
    result: dict[str, float | None] = {
        "prediction_interval_80_low": low80,
        "prediction_interval_80_high": high80,
        "prediction_interval_95_low": low95,
        "prediction_interval_95_high": high95,
        "gp_predictive_std": gp_std,
    }
    if gp_std is not None:
        result["bayesian_normal_interval_95_low"] = float(prediction - 1.96 * gp_std)
        result["bayesian_normal_interval_95_high"] = float(prediction + 1.96 * gp_std)
    else:
        result["bayesian_normal_interval_95_low"] = None
        result["bayesian_normal_interval_95_high"] = None
    return result


def benchmark(
    rows: list[dict[str, Any]],
    feature_names: list[str],
    feature_set: str = "structure_only",
    split_mode: str = "target_holdout",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    x, y = matrix_arrays(rows, feature_names)
    splits = build_family_splits(rows) if split_mode == "family_holdout" else build_splits(rows)
    grids = model_grid()
    predictions = []
    for split in splits:
        target_indices = split.get("target_indices", [split["target_index"]])
        for model_name, estimators in grids.items():
            selected = choose_model(model_name, estimators, split, x, y)
            train = split["train_indices"]
            validation = split["validation_indices"]
            validation_pred, _ = fit_predict(selected["estimator"], x[train], y[train], x[validation])
            validation_residuals = validation_pred - y[validation]
            target_pred, target_std = fit_predict(selected["estimator"], x[train], y[train], x[target_indices])
            for target_position, target in enumerate(target_indices):
                prediction = float(target_pred[target_position])
                gp_std = float(target_std[target_position]) if target_std is not None else None
                intervals = empirical_interval(prediction, validation_residuals, gp_std)
                predictions.append(
                    {
                        "split_mode": split_mode,
                        "split_id": split["split_id"],
                        "heldout_family_id": split.get("heldout_family_id"),
                        "target_substrate_id": rows[target]["substrate_id"],
                        "feature_set": feature_set,
                        "target_name": rows[target]["target_name"],
                        "family_id": rows[target]["family_id"],
                        "model_name": model_name,
                        "observed_target_value": float(y[target]),
                        "observed_ee_percent": float(y[target]) if rows[target]["target_name"] == "ee" else None,
                        "observed_yield_percent": float(y[target]) if rows[target]["target_name"] == "yield" else None,
                        "prediction": prediction,
                        "residual": prediction - float(y[target]),
                        "abs_error": abs(prediction - float(y[target])),
                        "validation_mae": selected["validation_mae"],
                        "selected_estimator_params": selected["estimator_params"],
                        "train_count": len(train),
                        "validation_count": len(validation),
                        "heldout_count": len(target_indices),
                        "train_substrate_ids": "|".join(split["train_substrate_ids"]),
                        "validation_substrate_ids": "|".join(split["validation_substrate_ids"]),
                        **intervals,
                    }
                )
    return predictions, splits


def metric_summary(values: numpy.ndarray) -> dict[str, float]:
    return {
        "mean": float(values.mean()),
        "median": float(numpy.median(values)),
        "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
        "q05": float(numpy.quantile(values, 0.05)),
        "q95": float(numpy.quantile(values, 0.95)),
    }


def model_metrics(predictions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_model: dict[str, list[dict[str, Any]]] = {}
    for row in predictions:
        by_model.setdefault(row["model_name"], []).append(row)
    output = {}
    for model_name, rows in by_model.items():
        y_true = numpy.array([row["observed_target_value"] for row in rows], dtype=float)
        y_pred = numpy.array([row["prediction"] for row in rows], dtype=float)
        residuals = y_pred - y_true
        output[model_name] = {
            "target_count": len(rows),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
            "r2": float(r2_score(y_true, y_pred)),
            "mean_error": float(residuals.mean()),
            "residual_summary": metric_summary(residuals),
            "abs_error_summary": metric_summary(numpy.abs(residuals)),
            "within_10_ee_fraction": float(numpy.mean(numpy.abs(residuals) <= 10.0)),
            "within_20_ee_fraction": float(numpy.mean(numpy.abs(residuals) <= 20.0)),
            "bayesian_bootstrap": bayesian_bootstrap(y_true, y_pred),
        }
    return output


def bayesian_bootstrap(y_true: numpy.ndarray, y_pred: numpy.ndarray) -> dict[str, Any]:
    rng = numpy.random.default_rng(BAYESIAN_BOOTSTRAP_SEED)
    mae_values = []
    rmse_values = []
    for _ in range(BAYESIAN_BOOTSTRAP_DRAWS):
        weights = rng.dirichlet(numpy.ones(len(y_true)))
        residuals = y_pred - y_true
        mae_values.append(float(numpy.sum(weights * numpy.abs(residuals))))
        rmse_values.append(float(numpy.sqrt(numpy.sum(weights * residuals * residuals))))
    mae = numpy.array(mae_values)
    rmse = numpy.array(rmse_values)
    return {
        "method": "bayesian_bootstrap_over_target_holdout_residuals",
        "draw_count": BAYESIAN_BOOTSTRAP_DRAWS,
        "mae": {
            "median": float(numpy.median(mae)),
            "ci95_low": float(numpy.quantile(mae, 0.025)),
            "ci95_high": float(numpy.quantile(mae, 0.975)),
        },
        "rmse": {
            "median": float(numpy.median(rmse)),
            "ci95_low": float(numpy.quantile(rmse, 0.025)),
            "ci95_high": float(numpy.quantile(rmse, 0.975)),
        },
    }


def write_predictions(path: Path, predictions: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in predictions for key in row})
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(predictions)


def run_benchmark(
    records_path: Path,
    matrix_path: Path,
    report_path: Path,
    predictions_path: Path,
    splits_path: Path,
    feature_set: str = "structure_only",
    pose_summary_path: Path = DEFAULT_POSE_SUMMARY,
    pose_interaction_path: Path = DEFAULT_POSE_INTERACTION,
    target: str = "ee",
    split_mode: str = "target_holdout",
) -> dict[str, Any]:
    rows, feature_names = build_feature_rows(records_path, feature_set, pose_summary_path, pose_interaction_path, target)
    write_matrix(matrix_path, rows, feature_names)
    predictions, splits = benchmark(rows, feature_names, feature_set, split_mode)
    write_predictions(predictions_path, predictions)
    splits_path.parent.mkdir(parents=True, exist_ok=True)
    splits_path.write_text(json.dumps({"splits": splits}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metrics = model_metrics(predictions)
    best_model = min(metrics, key=lambda name: metrics[name]["mae"])
    train_count = len(splits[0]["train_indices"]) if splits else 0
    validation_count = len(splits[0]["validation_indices"]) if splits else 0
    report = {
        "schema_version": "stage2-full-scope-benchmark-v1",
        "status": f"{feature_set}_full_scope_smoke_test",
        "feature_set": feature_set,
        "target": target,
        "target_label": TARGET_LABELS[target],
        "split_mode": split_mode,
        "modelable_record_count": len(rows),
        "excluded_records": excluded_records_for_target(records_path, target),
        "feature_count": len(feature_names),
        "feature_policy": (
            "RDKit physchem plus 512-bit Morgan fingerprint from unmapped azide substrate SMILES"
            if feature_set == "structure_only"
            else "RDKit physchem plus 512-bit Morgan fingerprint, checked reaction-center metadata, pose-summary features, and aggregated per-pose substrate-catalyst interaction features"
        ),
        "split_policy": (
            (
                f"For each target molecule, hold out the target, choose {train_count} structurally diverse training "
                f"molecules from the remaining {len(rows) - 1} by MaxMin Morgan/Tanimoto distance, and use the "
                f"remaining {validation_count} as validation."
            )
            if split_mode == "target_holdout"
            else (
                f"For each family, hold out all records in that family, choose {train_count} structurally diverse "
                f"training molecules from the remaining records by MaxMin Morgan/Tanimoto distance, and use the "
                f"remaining {validation_count} as validation."
            )
        ),
        "split_counts": {
            "train": train_count,
            "validation": validation_count,
            "target_prediction": 1 if split_mode == "target_holdout" else None,
        },
        "split_count": len(splits),
        "matrix_path": display_path(matrix_path),
        "report_path": display_path(report_path),
        "predictions_path": display_path(predictions_path),
        "splits_path": display_path(splits_path),
        "models": metrics,
        "best_model_by_mae": best_model,
        "environment": {
            "python_version": platform.python_version(),
            "sklearn_version": sklearn.__version__,
            "scipy_version": scipy.__version__,
            "lightgbm_version": lightgbm.__version__,
        },
        "caveats": [
            "This uses all modelable substrate-scope records for the selected target except explicitly excluded labels.",
            "The target-holdout protocol uses a 7:2:1-inspired split; family-held-out validation holds out whole family groups.",
            "Validation sets are the structurally non-selected remainder after MaxMin training selection, not random draws.",
            "Gaussian Process intervals are model-native normal intervals; other intervals are validation-residual empirical intervals.",
            "Pose-aware features use inferred reaction centers for 29 atom_mapped records; product atom maps remain manually reviewed only for the 12 feature_ready seed records.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def comparison_rows(structure_report: dict[str, Any], pose_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for model_name in sorted(structure_report["models"]):
        structure_metrics = structure_report["models"][model_name]
        pose_metrics = pose_report["models"][model_name]
        rows.append(
            {
                "model_name": model_name,
                "structure_only_mae": structure_metrics["mae"],
                "structure_pose_mae": pose_metrics["mae"],
                "mae_delta_structure_minus_pose": structure_metrics["mae"] - pose_metrics["mae"],
                "structure_only_rmse": structure_metrics["rmse"],
                "structure_pose_rmse": pose_metrics["rmse"],
                "rmse_delta_structure_minus_pose": structure_metrics["rmse"] - pose_metrics["rmse"],
                "structure_only_r2": structure_metrics["r2"],
                "structure_pose_r2": pose_metrics["r2"],
                "r2_delta_pose_minus_structure": pose_metrics["r2"] - structure_metrics["r2"],
                "structure_only_within_10_ee_fraction": structure_metrics["within_10_ee_fraction"],
                "structure_pose_within_10_ee_fraction": pose_metrics["within_10_ee_fraction"],
                "structure_only_mae_ci95_low": structure_metrics["bayesian_bootstrap"]["mae"]["ci95_low"],
                "structure_only_mae_ci95_high": structure_metrics["bayesian_bootstrap"]["mae"]["ci95_high"],
                "structure_pose_mae_ci95_low": pose_metrics["bayesian_bootstrap"]["mae"]["ci95_low"],
                "structure_pose_mae_ci95_high": pose_metrics["bayesian_bootstrap"]["mae"]["ci95_high"],
            }
        )
    return rows


def write_comparison_table(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_comparison_report(
    path: Path,
    table_path: Path,
    structure_report: dict[str, Any],
    pose_report: dict[str, Any],
) -> dict[str, Any]:
    rows = comparison_rows(structure_report, pose_report)
    write_comparison_table(table_path, rows)
    best_overall = min(
        [
            {"feature_set": "structure_only", "model_name": model_name, "mae": metrics["mae"]}
            for model_name, metrics in structure_report["models"].items()
        ]
        + [
            {"feature_set": "structure_pose", "model_name": model_name, "mae": metrics["mae"]}
            for model_name, metrics in pose_report["models"].items()
        ],
        key=lambda row: row["mae"],
    )
    pose_best = pose_report["best_model_by_mae"]
    structure_best = structure_report["best_model_by_mae"]
    report = {
        "schema_version": "stage2-full-scope-model-comparison-v1",
        "status": "structure_only_vs_structure_pose_comparison",
        "target": structure_report["target"],
        "split_mode": structure_report["split_mode"],
        "modelable_record_count": structure_report["modelable_record_count"],
        "split_policy": structure_report["split_policy"],
        "structure_only": {
            "report_path": structure_report["report_path"] if "report_path" in structure_report else display_path(DEFAULT_REPORT),
            "feature_count": structure_report["feature_count"],
            "best_model_by_mae": structure_best,
            "best_mae": structure_report["models"][structure_best]["mae"],
        },
        "structure_pose": {
            "report_path": pose_report["report_path"] if "report_path" in pose_report else display_path(DEFAULT_POSE_REPORT),
            "feature_count": pose_report["feature_count"],
            "best_model_by_mae": pose_best,
            "best_mae": pose_report["models"][pose_best]["mae"],
        },
        "comparison_table_path": display_path(table_path),
        "model_comparisons": rows,
        "best_overall_by_mae": best_overall,
        "analysis": [
            "Positive MAE/RMSE deltas mean the pose-aware feature set improved over structure-only for that model.",
            "The comparison is still a small-data diagnostic; use family-held-out validation before making chemical generalization claims.",
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def run_comparison(
    records_path: Path,
    structure_matrix: Path,
    structure_report_path: Path,
    structure_predictions: Path,
    splits_path: Path,
    pose_matrix: Path,
    pose_report_path: Path,
    pose_predictions: Path,
    comparison_report_path: Path,
    comparison_table_path: Path,
    pose_summary_path: Path,
    pose_interaction_path: Path,
    target: str,
    split_mode: str,
) -> dict[str, Any]:
    structure_report = run_benchmark(
        records_path,
        structure_matrix,
        structure_report_path,
        structure_predictions,
        splits_path,
        feature_set="structure_only",
        pose_summary_path=pose_summary_path,
        pose_interaction_path=pose_interaction_path,
        target=target,
        split_mode=split_mode,
    )
    pose_report = run_benchmark(
        records_path,
        pose_matrix,
        pose_report_path,
        pose_predictions,
        splits_path,
        feature_set="structure_pose",
        pose_summary_path=pose_summary_path,
        pose_interaction_path=pose_interaction_path,
        target=target,
        split_mode=split_mode,
    )
    return write_comparison_report(comparison_report_path, comparison_table_path, structure_report, pose_report)


def best_summary_line(label: str, comparison: dict[str, Any]) -> str:
    overall = comparison["best_overall_by_mae"]
    return f"{label}: best={overall['feature_set']}/{overall['model_name']}, MAE={overall['mae']:.3f}"


def metric_row(label: str, comparison: dict[str, Any]) -> str:
    overall = comparison["best_overall_by_mae"]
    structure = comparison["structure_only"]
    pose = comparison["structure_pose"]
    return (
        f"| {label} | {comparison['modelable_record_count']} | {comparison['split_mode']} | "
        f"{structure['best_model_by_mae']} / {structure['best_mae']:.3f} | "
        f"{pose['best_model_by_mae']} / {pose['best_mae']:.3f} | "
        f"{overall['feature_set']} / {overall['model_name']} / {overall['mae']:.3f} |"
    )


def write_final_stage2_report(
    path: Path,
    ee_target: dict[str, Any],
    yield_target: dict[str, Any],
    ee_family: dict[str, Any],
    yield_family: dict[str, Any],
) -> None:
    lines = [
        "# Stage 2 Final Report",
        "",
        "## Scope",
        "",
        "Stage 2 produced model-facing features and baseline diagnostics for the JACS 2025 substrate scope.",
        "",
        "- Reaction ledger: 41 records.",
        "- Reaction-center coverage: 41 checked records.",
        "- Feature-ready product-map coverage: 12 seed records.",
        "- Atom-mapped non-seed coverage: 29 records with inferred checked reaction centers and deferred product maps.",
        "- Pose-summary coverage: 41 records.",
        "- Pose-interaction coverage: 8,200 retained poses.",
        "- xTB/BDE features: deferred to Stage 3.",
        "",
        "## Label Policy",
        "",
        "- `1an` is excluded from ee modelling because the product is achiral.",
        "- `1ad` remains in the ledger but is excluded from ee modelling because the 0% ee label is likely undetermined by a separation problem.",
        "- `1z` remains in the ledger but is excluded from the matched 38-substrate ee cohort so the early benchmarks use the same cohort as the later protocols.",
        "- Yield modelling uses all records with numeric isolated yield.",
        "",
        "## Model Summary",
        "",
        "| Target | Records | Split | Structure-only best / MAE | Pose-aware best / MAE | Overall best / MAE |",
        "| --- | ---: | --- | --- | --- | --- |",
        metric_row("ee", ee_target),
        metric_row("yield", yield_target),
        metric_row("ee", ee_family),
        metric_row("yield", yield_family),
        "",
        "## Interpretation",
        "",
        "The target-holdout ee benchmark currently favors pose-aware Elastic Net. After excluding `1ad` and aligning the cohort by excluding `1z`, the result should be treated as a provisional Stage 2 baseline rather than a broad chemical generalization claim.",
        "",
        "Family-held-out validation is the stricter test. Its metrics should be used to decide how much trust to place in predictions for genuinely new substrate families.",
        "",
        "Yield modelling is now available as a parallel baseline, but yield and ee should not be assumed to prefer the same model or feature set.",
        "",
        "## Recommended Baselines Going Into Stage 3",
        "",
        f"- ee target-holdout baseline: {ee_target['best_overall_by_mae']['feature_set']} / {ee_target['best_overall_by_mae']['model_name']}.",
        f"- yield target-holdout baseline: {yield_target['best_overall_by_mae']['feature_set']} / {yield_target['best_overall_by_mae']['model_name']}.",
        "- Treat family-held-out performance as the main risk signal for prospective substrate selection.",
        "- Keep xTB/BDE out of Stage 2; add it in Stage 3 only after deciding which families and residual failures need deeper energetics.",
        "",
        "## Remaining Stage 3 Hand-Off",
        "",
        "- Complete manual product atom maps for the 29 non-seed records if publication-grade `feature_ready` status is required.",
        "- Add xTB/BDE candidate-site features and calibration.",
        "- Use family-held-out residuals to choose prospective experiments or higher-level calculations.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--pose-summary", type=Path, default=DEFAULT_POSE_SUMMARY)
    parser.add_argument("--pose-interaction", type=Path, default=DEFAULT_POSE_INTERACTION)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--pose-matrix", type=Path, default=DEFAULT_POSE_MATRIX)
    parser.add_argument("--pose-report", type=Path, default=DEFAULT_POSE_REPORT)
    parser.add_argument("--pose-predictions", type=Path, default=DEFAULT_POSE_PREDICTIONS)
    parser.add_argument("--comparison-report", type=Path, default=DEFAULT_COMPARISON_REPORT)
    parser.add_argument("--comparison-table", type=Path, default=DEFAULT_COMPARISON_TABLE)
    parser.add_argument("--yield-matrix", type=Path, default=DEFAULT_YIELD_MATRIX)
    parser.add_argument("--yield-report", type=Path, default=DEFAULT_YIELD_REPORT)
    parser.add_argument("--yield-predictions", type=Path, default=DEFAULT_YIELD_PREDICTIONS)
    parser.add_argument("--yield-pose-matrix", type=Path, default=DEFAULT_YIELD_POSE_MATRIX)
    parser.add_argument("--yield-pose-report", type=Path, default=DEFAULT_YIELD_POSE_REPORT)
    parser.add_argument("--yield-pose-predictions", type=Path, default=DEFAULT_YIELD_POSE_PREDICTIONS)
    parser.add_argument("--yield-comparison-report", type=Path, default=DEFAULT_YIELD_COMPARISON_REPORT)
    parser.add_argument("--yield-comparison-table", type=Path, default=DEFAULT_YIELD_COMPARISON_TABLE)
    parser.add_argument("--family-ee-structure-report", type=Path, default=DEFAULT_FAMILY_EE_STRUCTURE_REPORT)
    parser.add_argument("--family-ee-structure-predictions", type=Path, default=DEFAULT_FAMILY_EE_STRUCTURE_PREDICTIONS)
    parser.add_argument("--family-ee-pose-report", type=Path, default=DEFAULT_FAMILY_EE_POSE_REPORT)
    parser.add_argument("--family-ee-pose-predictions", type=Path, default=DEFAULT_FAMILY_EE_POSE_PREDICTIONS)
    parser.add_argument("--family-ee-comparison-report", type=Path, default=DEFAULT_FAMILY_EE_COMPARISON_REPORT)
    parser.add_argument("--family-ee-comparison-table", type=Path, default=DEFAULT_FAMILY_EE_COMPARISON_TABLE)
    parser.add_argument("--family-yield-structure-report", type=Path, default=DEFAULT_FAMILY_YIELD_STRUCTURE_REPORT)
    parser.add_argument("--family-yield-structure-predictions", type=Path, default=DEFAULT_FAMILY_YIELD_STRUCTURE_PREDICTIONS)
    parser.add_argument("--family-yield-pose-report", type=Path, default=DEFAULT_FAMILY_YIELD_POSE_REPORT)
    parser.add_argument("--family-yield-pose-predictions", type=Path, default=DEFAULT_FAMILY_YIELD_POSE_PREDICTIONS)
    parser.add_argument("--family-yield-comparison-report", type=Path, default=DEFAULT_FAMILY_YIELD_COMPARISON_REPORT)
    parser.add_argument("--family-yield-comparison-table", type=Path, default=DEFAULT_FAMILY_YIELD_COMPARISON_TABLE)
    parser.add_argument("--final-stage2-report", type=Path, default=DEFAULT_FINAL_STAGE2_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ee_target = run_comparison(
        args.records,
        args.matrix,
        args.report,
        args.predictions,
        args.splits,
        args.pose_matrix,
        args.pose_report,
        args.pose_predictions,
        args.comparison_report,
        args.comparison_table,
        args.pose_summary,
        args.pose_interaction,
        "ee",
        "target_holdout",
    )
    yield_target = run_comparison(
        args.records,
        args.yield_matrix,
        args.yield_report,
        args.yield_predictions,
        args.splits.with_name("full-scope-structure-yield-splits.json"),
        args.yield_pose_matrix,
        args.yield_pose_report,
        args.yield_pose_predictions,
        args.yield_comparison_report,
        args.yield_comparison_table,
        args.pose_summary,
        args.pose_interaction,
        "yield",
        "target_holdout",
    )
    ee_family = run_comparison(
        args.records,
        args.matrix,
        args.family_ee_structure_report,
        args.family_ee_structure_predictions,
        args.splits.with_name("family-heldout-ee-splits.json"),
        args.pose_matrix,
        args.family_ee_pose_report,
        args.family_ee_pose_predictions,
        args.family_ee_comparison_report,
        args.family_ee_comparison_table,
        args.pose_summary,
        args.pose_interaction,
        "ee",
        "family_holdout",
    )
    yield_family = run_comparison(
        args.records,
        args.yield_matrix,
        args.family_yield_structure_report,
        args.family_yield_structure_predictions,
        args.splits.with_name("family-heldout-yield-splits.json"),
        args.yield_pose_matrix,
        args.family_yield_pose_report,
        args.family_yield_pose_predictions,
        args.family_yield_comparison_report,
        args.family_yield_comparison_table,
        args.pose_summary,
        args.pose_interaction,
        "yield",
        "family_holdout",
    )
    write_final_stage2_report(args.final_stage2_report, ee_target, yield_target, ee_family, yield_family)
    print(best_summary_line("ee target-holdout", ee_target))
    print(best_summary_line("yield target-holdout", yield_target))
    print(best_summary_line("ee family-held-out", ee_family))
    print(best_summary_line("yield family-held-out", yield_family))
    print(f"Wrote final Stage 2 report to {display_path(args.final_stage2_report)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

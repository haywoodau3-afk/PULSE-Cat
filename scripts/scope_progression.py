#!/usr/bin/env python3
"""Simulate substrate-scope progression with RDKit and Stage 2p features.

The unit of acquisition is always a whole substrate.  This module deliberately
keeps the experimental label attached to the substrate while using Morgan
fingerprints for structural distance and fixed low-capacity models for the
retrospective learning-curve experiment.

The same contract can be used for a historical labelled scope or for a future
paper's unlabelled candidate pool.  Unlabelled candidates are never used to fit
models and are never assigned a synthetic negative label.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "scope-progression-v1"
DEFAULT_REPLICATES = 500
DEFAULT_SEED = 20260824
DEFAULT_AUDIT_FRACTION = 0.20
DEFAULT_MORGAN_BITS = 1024
DEFAULT_MORGAN_RADIUS = 2
MILESTONE_FRACTION = (0.10, 0.25, 0.50, 0.75, 1.0)
PERCENT_TARGET_BOUNDS = (0.0, 100.0)


@dataclass(frozen=True)
class ScopeRow:
    substrate_id: str
    smiles: str
    family_id: str
    source_order: int
    record: dict[str, Any]


@dataclass
class FeatureTable:
    rows: list[ScopeRow]
    descriptor_names: list[str]
    descriptor_matrix: np.ndarray
    fingerprint_matrix: np.ndarray
    stage2p_names: list[str]
    stage2p_matrix: np.ndarray
    scaffolds: list[str]
    similarity_matrix: np.ndarray

    @property
    def ids(self) -> list[str]:
        return [row.substrate_id for row in self.rows]

    @property
    def families(self) -> list[str]:
        return [row.family_id for row in self.rows]

    def matrix(self, feature_set: str) -> np.ndarray:
        if feature_set == "rdkit_morgan":
            return np.column_stack([self.descriptor_matrix, self.fingerprint_matrix])
        if feature_set == "rdkit_morgan_stage2p":
            return np.column_stack([self.descriptor_matrix, self.fingerprint_matrix, self.stage2p_matrix])
        raise ValueError(f"unknown feature set: {feature_set}")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def first_present(mapping: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        value: Any = mapping
        for key in path:
            if not isinstance(value, dict) or key not in value:
                value = None
                break
            value = value[key]
        if value not in (None, ""):
            return value
    return None


def record_id(record: dict[str, Any]) -> str:
    value = first_present(record, ("substrate_id",), ("paper_substrate_id",), ("substrate", "paper_substrate_id"))
    if value is None:
        raise ValueError("record is missing substrate_id/paper_substrate_id")
    return str(value)


def substrate_smiles(record: dict[str, Any]) -> str:
    value = first_present(
        record,
        ("structure", "atom_mapped_substrate_smiles"),
        ("substrate", "atom_mapped_substrate_smiles"),
        ("substrate", "smiles"),
        ("structure", "azide_smiles"),
        ("substrate", "azide_smiles"),
        ("azide_smiles",),
    )
    if value is None:
        raise ValueError(f"{record_id(record)}: missing substrate SMILES")
    return str(value)


def family_id(record: dict[str, Any]) -> str:
    value = first_present(record, ("family", "family_id"), ("family_id",), ("family", "family_label"))
    return str(value) if value is not None else "unknown-family"


def outcome_value(record: dict[str, Any], target: str) -> float | None:
    key = "ee_percent" if target == "ee_percent" else "isolated_yield_percent"
    value = first_present(record, ("outcome", key), (key,))
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def outcome_status(record: dict[str, Any], target: str) -> str | None:
    if target == "ee_percent":
        return first_present(record, ("outcome", "ee_status"), ("ee_status",))
    return first_present(record, ("outcome", "yield_status"), ("yield_status",))


def catalyst_id(record: dict[str, Any]) -> str | None:
    value = first_present(record, ("catalyst_id",), ("catalyst", "catalyst_id"))
    return str(value) if value is not None else None


def load_scope_rows_from_records(records: Sequence[dict[str, Any]], catalyst: str | None = None) -> list[ScopeRow]:
    rows: list[ScopeRow] = []
    seen: set[str] = set()
    for order, record in enumerate(records):
        if catalyst is not None and catalyst_id(record) not in {None, catalyst}:
            continue
        substrate_id = record_id(record)
        if substrate_id in seen:
            raise ValueError(f"duplicate substrate_id in scope input: {substrate_id}")
        seen.add(substrate_id)
        smiles = substrate_smiles(record)
        if Chem.MolFromSmiles(smiles) is None:
            raise ValueError(f"{substrate_id}: invalid substrate SMILES")
        rows.append(ScopeRow(substrate_id, smiles, family_id(record), order, record))
    if not rows:
        raise ValueError("no scope records loaded")
    return rows


def load_scope_rows(path: Path, catalyst: str | None = None) -> list[ScopeRow]:
    rows = load_scope_rows_from_records(read_jsonl(path), catalyst)
    if not rows:
        raise ValueError(f"no scope records loaded from {path}")
    return rows


def numeric_features(mol: Chem.Mol) -> dict[str, float]:
    return {
        "heavy_atom_count": float(mol.GetNumHeavyAtoms()),
        "molecular_weight": float(Descriptors.MolWt(mol)),
        "logp": float(Crippen.MolLogP(mol)),
        "tpsa": float(rdMolDescriptors.CalcTPSA(mol)),
        "formal_charge": float(Chem.GetFormalCharge(mol)),
        "fraction_csp3": float(rdMolDescriptors.CalcFractionCSP3(mol)),
        "rotatable_bonds": float(Lipinski.NumRotatableBonds(mol)),
        "rings": float(rdMolDescriptors.CalcNumRings(mol)),
        "aromatic_rings": float(rdMolDescriptors.CalcNumAromaticRings(mol)),
        "h_bond_acceptors": float(Lipinski.NumHAcceptors(mol)),
        "h_bond_donors": float(Lipinski.NumHDonors(mol)),
        "hetero_atoms": float(rdMolDescriptors.CalcNumHeteroatoms(mol)),
        "aliphatic_rings": float(rdMolDescriptors.CalcNumAliphaticRings(mol)),
        "spiro_atoms": float(rdMolDescriptors.CalcNumSpiroAtoms(mol)),
        "chiral_centers": float(len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))),
    }


def morgan_bits(mol: Chem.Mol, radius: int, bits: int) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=bits)
    fingerprint = generator.GetFingerprint(mol)
    values = np.zeros((bits,), dtype=np.float64)
    DataStructs.ConvertToNumpyArray(fingerprint, values)
    return values


def flatten_numeric(value: Any, prefix: str = "") -> dict[str, float]:
    flattened: dict[str, float] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(flatten_numeric(child, child_prefix))
    elif isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
        flattened[prefix] = float(value)
    return flattened


def load_stage2p_features(path: Path | None) -> dict[str, dict[str, float]]:
    if path is None:
        return {}
    output: dict[str, dict[str, float]] = {}
    for row in read_jsonl(path):
        substrate_id = record_id(row)
        block = row.get("feature_blocks", row)
        output[substrate_id] = flatten_numeric(block, "stage2p")
    return output


def build_feature_table(
    rows: list[ScopeRow],
    stage2p_path: Path | None,
    morgan_radius: int = DEFAULT_MORGAN_RADIUS,
    morgan_bits_count: int = DEFAULT_MORGAN_BITS,
) -> FeatureTable:
    stage2p_by_id = load_stage2p_features(stage2p_path)
    descriptors: list[dict[str, float]] = []
    fingerprints: list[np.ndarray] = []
    scaffolds: list[str] = []
    for row in rows:
        mol = Chem.MolFromSmiles(row.smiles)
        if mol is None:
            raise ValueError(f"{row.substrate_id}: invalid substrate SMILES")
        descriptors.append(numeric_features(mol))
        fingerprints.append(morgan_bits(mol, morgan_radius, morgan_bits_count))
        scaffolds.append(MurckoScaffold.MurckoScaffoldSmiles(mol=mol) or "acyclic")
    descriptor_names = sorted({name for values in descriptors for name in values})
    descriptor_matrix = np.asarray([[values[name] for name in descriptor_names] for values in descriptors], dtype=float)
    fingerprint_matrix = np.asarray(fingerprints, dtype=float)
    stage2p_names = sorted({name for values in stage2p_by_id.values() for name in values})
    stage2p_matrix = np.asarray(
        [[stage2p_by_id.get(row.substrate_id, {}).get(name, 0.0) for name in stage2p_names] for row in rows],
        dtype=float,
    )
    similarity_matrix = tanimoto_matrix(fingerprint_matrix)
    return FeatureTable(
        rows=rows,
        descriptor_names=descriptor_names,
        descriptor_matrix=descriptor_matrix,
        fingerprint_matrix=fingerprint_matrix,
        stage2p_names=stage2p_names,
        stage2p_matrix=stage2p_matrix,
        scaffolds=scaffolds,
        similarity_matrix=similarity_matrix,
    )


def tanimoto_matrix(fingerprint_matrix: np.ndarray) -> np.ndarray:
    fingerprints: list[Any] = []
    for values in fingerprint_matrix:
        bit_vector = DataStructs.CreateFromBitString("".join("1" if value else "0" for value in values.astype(int)))
        fingerprints.append(bit_vector)
    matrix = np.eye(len(fingerprints), dtype=float)
    for index, fingerprint in enumerate(fingerprints):
        similarities = DataStructs.BulkTanimotoSimilarity(fingerprint, fingerprints)
        matrix[index, :] = np.asarray(similarities, dtype=float)
    return matrix


def minmax(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return values
    low = float(np.nanmin(values))
    high = float(np.nanmax(values))
    if not math.isfinite(low) or not math.isfinite(high) or high <= low:
        return np.full(values.shape, 0.5, dtype=float)
    return (values - low) / (high - low)


def rank_correlation(observed: np.ndarray, predicted: np.ndarray) -> float | None:
    if len(observed) < 2 or len(np.unique(observed)) < 2 or len(np.unique(predicted)) < 2:
        return None
    observed_rank = np.argsort(np.argsort(observed)).astype(float)
    predicted_rank = np.argsort(np.argsort(predicted)).astype(float)
    observed_rank -= observed_rank.mean()
    predicted_rank -= predicted_rank.mean()
    denominator = float(np.linalg.norm(observed_rank) * np.linalg.norm(predicted_rank))
    return float(np.dot(observed_rank, predicted_rank) / denominator) if denominator else None


def family_coverage(table: FeatureTable, candidates: Sequence[int], selected: Sequence[int]) -> np.ndarray:
    counts: dict[str, int] = {}
    for index in selected:
        counts[table.families[index]] = counts.get(table.families[index], 0) + 1
    values = []
    for index in candidates:
        count = counts.get(table.families[index], 0)
        values.append(1.0 if count == 0 else 1.0 / (1.0 + count))
    return minmax(np.asarray(values, dtype=float))


def novelty_scores(table: FeatureTable, candidates: Sequence[int], selected: Sequence[int]) -> np.ndarray:
    if not selected:
        return np.ones((len(candidates),), dtype=float)
    return np.asarray([1.0 - float(np.max(table.similarity_matrix[index, list(selected)])) for index in candidates])


def fit_ridge(X: np.ndarray, y: np.ndarray) -> Any:
    return make_pipeline(StandardScaler(), Ridge(alpha=10.0, solver="lsqr"))


def fit_elastic_net(X: np.ndarray, y: np.ndarray) -> Any:
    return make_pipeline(StandardScaler(), ElasticNet(alpha=0.1, l1_ratio=0.15, max_iter=10000, random_state=0))


def fit_predict_models(
    X: np.ndarray,
    fingerprints: np.ndarray,
    train: Sequence[int],
    test: Sequence[int],
    y: np.ndarray,
    include_elastic_net: bool = True,
) -> dict[str, np.ndarray]:
    if not train or not test:
        return {}
    train_array = np.asarray(train, dtype=int)
    test_array = np.asarray(test, dtype=int)
    predictions: dict[str, np.ndarray] = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        ridge = fit_ridge(X[train_array], y[train_array])
        ridge.fit(X[train_array], y[train_array])
        predictions["ridge"] = np.clip(
            np.asarray(ridge.predict(X[test_array]), dtype=float), *PERCENT_TARGET_BOUNDS
        )
        if include_elastic_net:
            elastic = fit_elastic_net(X[train_array], y[train_array])
            elastic.fit(X[train_array], y[train_array])
            predictions["elastic_net"] = np.clip(
                np.asarray(elastic.predict(X[test_array]), dtype=float), *PERCENT_TARGET_BOUNDS
            )
    predictions["tanimoto_knn"] = tanimoto_predictions(fingerprints, train, test, y)
    return predictions


def tanimoto_predictions(fingerprints: np.ndarray, train: Sequence[int], test: Sequence[int], y: np.ndarray) -> np.ndarray:
    return tanimoto_predictions_cross(fingerprints, fingerprints, train, test, y)


def tanimoto_predictions_cross(
    train_fingerprints: np.ndarray,
    test_fingerprints: np.ndarray,
    train: Sequence[int],
    test: Sequence[int],
    y: np.ndarray,
) -> np.ndarray:
    predictions = []
    train_array = np.asarray(train, dtype=int)
    for index in test:
        similarities = np.asarray(
            [tanimoto_similarity(test_fingerprints[index], train_fingerprints[j]) for j in train_array]
        )
        order = np.argsort(-similarities)[: min(5, len(similarities))]
        weights = similarities[order] + 1e-6
        predictions.append(float(np.average(y[train_array[order]], weights=weights)))
    return np.asarray(predictions, dtype=float)


def tanimoto_similarity(first: np.ndarray, second: np.ndarray) -> float:
    numerator = float(np.dot(first, second))
    denominator = float(np.sum(first) + np.sum(second) - numerator)
    return numerator / denominator if denominator else 1.0


def uncertainty_scores(
    predictions: dict[str, np.ndarray],
    novelty: np.ndarray,
) -> np.ndarray:
    if not predictions:
        return minmax(novelty)
    values = [prediction for name, prediction in predictions.items() if name in {"ridge", "elastic_net", "tanimoto_knn"}]
    disagreement = np.std(np.vstack(values), axis=0) if len(values) > 1 else np.zeros_like(novelty)
    return 0.5 * minmax(novelty) + 0.5 * minmax(disagreement)


def seed_indices(table: FeatureTable, pool: Sequence[int], route: str, rng: random.Random) -> list[int]:
    if len(pool) < 2:
        raise ValueError("at least two active substrates are required")
    if route == "historical_order":
        return sorted(pool, key=lambda index: table.rows[index].source_order)[:2]
    if route == "random":
        return rng.sample(list(pool), 2)
    pool_list = list(pool)
    mean_distance = np.asarray(
        [np.mean([1.0 - table.similarity_matrix[index, other] for other in pool_list if other != index]) for index in pool_list]
    )
    central = pool_list[int(np.argmin(mean_distance))]
    second = max((index for index in pool_list if index != central), key=lambda index: (1.0 - table.similarity_matrix[central, index], -index))
    return [central, second]


def selection_components(
    table: FeatureTable,
    X: np.ndarray,
    target_values: np.ndarray,
    selected: Sequence[int],
    candidates: Sequence[int],
    route: str,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    novelty = minmax(novelty_scores(table, candidates, selected))
    coverage = family_coverage(table, candidates, selected)
    predictions = fit_predict_models(X, table.fingerprint_matrix, selected, candidates, target_values)
    uncertainty = uncertainty_scores(predictions, novelty)
    predicted_performance = minmax(predictions.get("ridge", np.zeros(len(candidates), dtype=float)))
    if route == "diversity_first":
        score = 0.8 * novelty + 0.2 * coverage
    elif route == "uncertainty_diversity":
        score = 0.4 * novelty + 0.4 * uncertainty + 0.2 * coverage
    elif route == "performance_first":
        score = 0.5 * predicted_performance + 0.3 * uncertainty + 0.2 * novelty
    else:
        score = np.zeros(len(candidates), dtype=float)
    return score, {
        "diversity_score": novelty,
        "uncertainty_score": uncertainty,
        "family_coverage_score": coverage,
        "predicted_performance_score": predicted_performance,
    }


def metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, Any]:
    if len(observed) == 0:
        return {"n_evaluated": 0, "mae": None, "rmse": None, "spearman": None}
    return {
        "n_evaluated": int(len(observed)),
        "mae": float(mean_absolute_error(observed, predicted)),
        "rmse": float(math.sqrt(mean_squared_error(observed, predicted))),
        "spearman": rank_correlation(observed, predicted),
    }


def evaluate_prefix(
    table: FeatureTable,
    X: np.ndarray,
    target_values: np.ndarray,
    selected: Sequence[int],
    evaluation_pool: Sequence[int],
    route: str,
    replicate: int,
    n_labeled: int,
    target: str,
    evaluation_name: str,
    include_elastic_net: bool = True,
) -> list[dict[str, Any]]:
    test = [index for index in evaluation_pool if index not in selected and not np.isnan(target_values[index])]
    if not test:
        return []
    train = [index for index in selected if target_values[index] is not None]
    if len(train) < 2:
        return []
    y = target_values.astype(float)
    predictions = fit_predict_models(X, table.fingerprint_matrix, train, test, y, include_elastic_net)
    observed = y[np.asarray(test, dtype=int)]
    rows: list[dict[str, Any]] = []
    for model_name, predicted in predictions.items():
        row = {
            "schema_version": SCHEMA_VERSION,
            "route": route,
            "replicate": replicate,
            "target": target,
            "n_labeled": n_labeled,
            "evaluation_pool": evaluation_name,
            "model": model_name,
        }
        row.update(metrics(observed, predicted))
        rows.append(row)
    return rows


def simulate_route(
    table: FeatureTable,
    target: str,
    feature_set: str,
    active_indices: Sequence[int],
    audit_indices: Sequence[int],
    route: str,
    replicate: int,
    rng: random.Random,
    audit_milestones: set[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    X = table.matrix(feature_set)
    numeric_values = np.asarray(
        [outcome_value(row.record, target) if outcome_value(row.record, target) is not None else np.nan for row in table.rows],
        dtype=float,
    )
    pool = list(active_indices)
    selected = seed_indices(table, pool, route, rng)
    include_elastic_net = route != "random"
    events: list[dict[str, Any]] = []
    for seed_rank, index in enumerate(selected, start=1):
        events.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route": route,
                "replicate": replicate,
                "target": target,
                "step": seed_rank,
                "selection_phase": "initial_seed",
                "selected_substrate_id": table.rows[index].substrate_id,
                "family_id": table.rows[index].family_id,
                "selection_score": None,
                "diversity_score": None,
                "uncertainty_score": None,
                "family_coverage_score": None,
                "predicted_performance_score": None,
            }
        )
    learning_rows = evaluate_prefix(
        table, X, numeric_values, selected, pool, route, replicate, 2, target, "remaining_active", include_elastic_net
    )
    audit_metric_rows = evaluate_prefix(
        table, X, numeric_values, selected, audit_indices, route, replicate, 2, target, "locked_audit", include_elastic_net
    )
    audit_prediction_rows_output: list[dict[str, Any]] = []
    if 2 in audit_milestones:
        audit_prediction_rows_output.extend(audit_prediction_rows(table, X, numeric_values, selected, audit_indices, route, replicate, target, 2))
    for step in range(3, len(pool) + 1):
        candidates = [index for index in pool if index not in selected]
        if route == "random":
            chosen_position = rng.randrange(len(candidates))
            chosen = candidates[chosen_position]
            score = 0.0
            components = {
                "diversity_score": None,
                "uncertainty_score": None,
                "family_coverage_score": None,
                "predicted_performance_score": None,
            }
        elif route == "historical_order":
            chosen = min(candidates, key=lambda index: table.rows[index].source_order)
            score, component_values = selection_components(table, X, numeric_values, selected, candidates, "diversity_first")
            chosen_position = max(range(len(candidates)), key=lambda position: score[position] if candidates[position] == chosen else -1.0)
            components = {name: float(values[chosen_position]) for name, values in component_values.items()}
            score = float(score[chosen_position])
        else:
            scores, component_values = selection_components(table, X, numeric_values, selected, candidates, route)
            chosen_position = max(range(len(candidates)), key=lambda position: (scores[position], -table.rows[candidates[position]].source_order))
            chosen = candidates[chosen_position]
            score = float(scores[chosen_position])
            components = {name: float(values[chosen_position]) for name, values in component_values.items()}
        selected.append(chosen)
        events.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route": route,
                "replicate": replicate,
                "target": target,
                "step": step,
                "selection_phase": "sequential",
                "selected_substrate_id": table.rows[chosen].substrate_id,
                "family_id": table.rows[chosen].family_id,
                "selection_score": score,
                **components,
            }
        )
        learning_rows.extend(
            evaluate_prefix(
                table,
                X,
                numeric_values,
                selected,
                pool,
                route,
                replicate,
                step,
                target,
                "remaining_active",
                include_elastic_net,
            )
        )
        if step in audit_milestones:
            audit_metric_rows.extend(
                evaluate_prefix(
                    table, X, numeric_values, selected, audit_indices, route, replicate, step, target, "locked_audit", include_elastic_net
                )
            )
            audit_prediction_rows_output.extend(
                audit_prediction_rows(table, X, numeric_values, selected, audit_indices, route, replicate, target, step)
            )
    return learning_rows, audit_metric_rows, audit_prediction_rows_output, events


def audit_prediction_rows(
    table: FeatureTable,
    X: np.ndarray,
    target_values: np.ndarray,
    selected: Sequence[int],
    audit_indices: Sequence[int],
    route: str,
    replicate: int,
    target: str,
    n_labeled: int,
) -> list[dict[str, Any]]:
    test = [index for index in audit_indices if index not in selected]
    train = [index for index in selected if not np.isnan(target_values[index])]
    if len(train) < 2 or not test:
        return []
    predictions = fit_predict_models(
        X,
        table.fingerprint_matrix,
        train,
        test,
        target_values,
        include_elastic_net=route != "random",
    )
    output = []
    for model_name, predicted in predictions.items():
        for index, value in zip(test, predicted):
            output.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "route": route,
                    "replicate": replicate,
                    "target": target,
                    "n_labeled": n_labeled,
                    "model": model_name,
                    "substrate_id": table.rows[index].substrate_id,
                    "family_id": table.rows[index].family_id,
                    "observed_value": None if np.isnan(target_values[index]) else float(target_values[index]),
                    "predicted_value": float(value),
                }
            )
    return output


def choose_auto_audit(rows: Sequence[ScopeRow], fraction: float) -> list[str]:
    if fraction <= 0:
        return []
    grouped: dict[str, list[ScopeRow]] = {}
    for row in rows:
        grouped.setdefault(row.family_id, []).append(row)
    selected: list[str] = []
    for family_rows in grouped.values():
        count = max(1, math.ceil(len(family_rows) * fraction))
        selected.extend(row.substrate_id for row in family_rows[-count:])
    return selected


def milestone_counts(n: int) -> set[int]:
    values = {2, 3, 4, n}
    values.update(max(2, min(n, math.ceil(n * fraction))) for fraction in MILESTONE_FRACTION)
    return values


def reference_metrics(table: FeatureTable, feature_set: str, target: str, active_indices: Sequence[int]) -> dict[str, Any]:
    X = table.matrix(feature_set)
    values = np.asarray([outcome_value(table.rows[index].record, target) for index in active_indices], dtype=object)
    numeric = np.asarray([value if value is not None else np.nan for value in values], dtype=float)
    valid = [position for position, value in enumerate(numeric) if not np.isnan(value)]
    if len(valid) < 3:
        return {"baseline_mae": None, "ridge_loo_mae": None, "elastic_net_loo_mae": None}
    baseline_prediction = float(np.mean(numeric[valid]))
    baseline_mae = float(np.mean(np.abs(numeric[valid] - baseline_prediction)))
    loo_predictions: dict[str, list[float]] = {"ridge": [], "elastic_net": [], "tanimoto_knn": []}
    observed: list[float] = []
    for position in valid:
        train_positions = [other for other in valid if other != position]
        test_position = [position]
        all_values = np.asarray(
            [outcome_value(row.record, target) if outcome_value(row.record, target) is not None else np.nan for row in table.rows],
            dtype=float,
        )
        predictions = fit_predict_models(
            X,
            table.fingerprint_matrix,
            [active_indices[item] for item in train_positions],
            [active_indices[position]],
            all_values,
        )
        if not predictions:
            continue
        observed.append(float(numeric[position]))
        for model_name in loo_predictions:
            loo_predictions[model_name].append(float(predictions[model_name][0]))
    result = {"baseline_mae": baseline_mae}
    for model_name, predicted in loo_predictions.items():
        result[f"{model_name}_loo_mae"] = float(mean_absolute_error(observed, predicted)) if observed else None
    return result


def summarize_learning(rows: list[dict[str, Any]], reference: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["route"], row["model"], int(row["n_labeled"]))
        grouped.setdefault(key, []).append(row)
    summaries: list[dict[str, Any]] = []
    for (route, model, n_labeled), values in sorted(grouped.items()):
        maes = np.asarray([row["mae"] for row in values if row["mae"] is not None], dtype=float)
        if not len(maes):
            continue
        target = values[0]["target"]
        full_mae = reference.get(f"{model}_loo_mae")
        baseline = reference.get("baseline_mae")
        threshold = None if baseline is None or full_mae is None else baseline - 0.9 * (baseline - full_mae)
        summaries.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route": route,
                "model": model,
                "target": target,
                "n_labeled": n_labeled,
                "replicates": len(values),
                "mae_mean": float(np.mean(maes)),
                "mae_std": float(np.std(maes, ddof=1)) if len(maes) > 1 else 0.0,
                "mae_median": float(np.median(maes)),
                "mae_q25": float(np.quantile(maes, 0.25)),
                "mae_q75": float(np.quantile(maes, 0.75)),
                "threshold_90_percent_error_reduction": threshold,
                "threshold_reached": bool(threshold is not None and np.median(maes) <= threshold),
                "aggregation": "mean_across_random_replicates" if route == "random" else "single_deterministic_route",
            }
        )
    return summaries


def summarize_convergence(summary_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Return compact convergence diagnostics for each route/model/target curve.

    ``n90`` is the first labelled-scope size at which the median learning-curve
    MAE reaches the 90%-of-reference-error-reduction threshold.  ``auc_mae``
    is the trapezoidal area under the median MAE curve; lower is better.
    Missing thresholds remain null rather than being silently treated as a
    failure or success.
    """
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in summary_rows:
        key = (str(row["target"]), str(row["route"]), str(row["model"]))
        grouped.setdefault(key, []).append(row)
    output: dict[str, Any] = {}
    for (target, route, model), values in sorted(grouped.items()):
        ordered = sorted(values, key=lambda row: int(row["n_labeled"]))
        reached = [row for row in ordered if row.get("threshold_reached")]
        x = np.asarray([float(row["n_labeled"]) for row in ordered], dtype=float)
        y = np.asarray([float(row["mae_median"]) for row in ordered], dtype=float)
        auc = float(np.trapezoid(y, x)) if len(ordered) > 1 else None
        output[f"{target}:{route}:{model}"] = {
            "target": target,
            "route": route,
            "model": model,
            "n90": int(reached[0]["n_labeled"]) if reached else None,
            "auc_mae": auc,
            "observed_n_labeled": [int(row["n_labeled"]) for row in ordered],
        }
    return output


def run_analysis(
    records_path: Path,
    stage2p_path: Path | None,
    output_dir: Path,
    catalyst: str | None,
    targets: Sequence[str],
    feature_set: str,
    audit_ids: Sequence[str],
    audit_fraction: float,
    replicates: int,
    seed: int,
    late_stage_path: Path | None = None,
    exclude_ids: Sequence[str] = (),
    family_ids: Sequence[str] = (),
) -> dict[str, Any]:
    rows = load_scope_rows(records_path, catalyst)
    excluded = set(exclude_ids)
    rows = [row for row in rows if row.substrate_id not in excluded]
    allowed_families = set(family_ids)
    if allowed_families:
        rows = [row for row in rows if row.family_id in allowed_families]
    if not rows:
        raise ValueError("no scope records remain after exclusions and family filtering")
    table = build_feature_table(rows, stage2p_path)
    all_ids = table.ids
    requested_audit = set(audit_ids) | set(choose_auto_audit(rows, audit_fraction))
    missing_audit = sorted(requested_audit - set(all_ids))
    if missing_audit:
        raise ValueError(f"audit IDs not found in records: {', '.join(missing_audit)}")
    audit_indices = [index for index, substrate_id in enumerate(all_ids) if substrate_id in requested_audit]
    active_indices = [index for index in range(len(rows)) if index not in audit_indices]
    if len(active_indices) < 4:
        raise ValueError("at least four active substrates are required for progression analysis")
    routes = ["diversity_first", "uncertainty_diversity", "performance_first", "random", "historical_order"]
    learning_rows: list[dict[str, Any]] = []
    audit_metric_rows: list[dict[str, Any]] = []
    audit_prediction_rows_output: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    references: dict[str, Any] = {}
    target_active_counts: dict[str, int] = {}
    for target in targets:
        target_active_indices = [index for index in active_indices if outcome_value(rows[index].record, target) is not None]
        target_active_counts[target] = len(target_active_indices)
        if len(target_active_indices) < 4:
            continue
        references[target] = reference_metrics(table, feature_set, target, target_active_indices)
        for route in routes:
            route_replicates = replicates if route == "random" else 1
            for replicate in range(route_replicates):
                route_seed = routes.index(route) * 100_003
                target_seed = targets.index(target) * 1_000_003
                rng = random.Random(seed + replicate * 1009 + route_seed + target_seed)
                result_learning, result_audit_metrics, result_audit_predictions, result_events = simulate_route(
                    table,
                    target,
                    feature_set,
                    target_active_indices,
                    audit_indices,
                    route,
                    replicate,
                    rng,
                    milestone_counts(len(target_active_indices)),
                )
                learning_rows.extend(result_learning)
                audit_metric_rows.extend(result_audit_metrics)
                audit_prediction_rows_output.extend(result_audit_predictions)
                events.extend(result_events)
    late_stage_rows: list[dict[str, Any]] = []
    if late_stage_path is not None:
        late_stage_rows = load_scope_rows(late_stage_path, catalyst)
    output_dir.mkdir(parents=True, exist_ok=True)
    stage2p_ids = set(load_stage2p_features(stage2p_path))
    feature_rows = [
        {
            "substrate_id": row.substrate_id,
            "family_id": row.family_id,
            "source_order": row.source_order,
            "scaffold_smiles": table.scaffolds[index],
            "is_locked_audit": row.substrate_id in requested_audit,
            "stage2p_features_available": row.substrate_id in stage2p_ids,
        }
        for index, row in enumerate(rows)
    ]
    write_csv(output_dir / "scope-features.csv", feature_rows, list(feature_rows[0].keys()))
    if learning_rows:
        write_csv(output_dir / "learning-curve.csv", learning_rows, list(learning_rows[0].keys()))
    if audit_metric_rows:
        write_csv(output_dir / "audit-metrics.csv", audit_metric_rows, list(audit_metric_rows[0].keys()))
    if audit_prediction_rows_output:
        write_csv(output_dir / "audit-predictions.csv", audit_prediction_rows_output, list(audit_prediction_rows_output[0].keys()))
    if events:
        write_csv(output_dir / "selection-events.csv", events, list(events[0].keys()))
    random_seed_rows = [
        {
            "schema_version": event["schema_version"],
            "route": event["route"],
            "replicate": event["replicate"],
            "target": event["target"],
            "seed_rank": event["step"],
            "substrate_id": event["selected_substrate_id"],
            "family_id": event["family_id"],
        }
        for event in events
        if event.get("route") == "random" and event.get("selection_phase") == "initial_seed"
    ]
    if random_seed_rows:
        write_csv(output_dir / "random-seed-pairs.csv", random_seed_rows, list(random_seed_rows[0].keys()))
    summary_rows: list[dict[str, Any]] = []
    for target, reference in references.items():
        target_learning = [row for row in learning_rows if row["target"] == target]
        summary_rows.extend(summarize_learning(target_learning, reference))
    if summary_rows:
        write_csv(output_dir / "learning-curve-summary.csv", summary_rows, list(summary_rows[0].keys()))
    convergence = summarize_convergence(summary_rows)
    unseen_predictions: list[dict[str, Any]] = []
    if late_stage_rows:
        late_table = build_feature_table(late_stage_rows, None)
        late_X = late_table.matrix("rdkit_morgan")
        active_table_X = table.matrix("rdkit_morgan")
        for target in targets:
            active_y = np.asarray(
                [outcome_value(row.record, target) if outcome_value(row.record, target) is not None else np.nan for row in rows],
                dtype=float,
            )
            train = [index for index in active_indices if not np.isnan(active_y[index])]
            if len(train) < 2:
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ConvergenceWarning)
                ridge = fit_ridge(active_table_X[train], active_y[train])
                ridge.fit(active_table_X[train], active_y[train])
                elastic = fit_elastic_net(active_table_X[train], active_y[train])
                elastic.fit(active_table_X[train], active_y[train])
            ridge_values = np.clip(ridge.predict(late_X), *PERCENT_TARGET_BOUNDS)
            elastic_values = np.clip(elastic.predict(late_X), *PERCENT_TARGET_BOUNDS)
            knn_values = tanimoto_predictions_cross(
                table.fingerprint_matrix,
                late_table.fingerprint_matrix,
                train,
                list(range(len(late_stage_rows))),
                active_y,
            )
            for row, ridge_value, elastic_value in zip(late_stage_rows, ridge_values, elastic_values):
                unseen_predictions.extend(
                    [
                        {"schema_version": SCHEMA_VERSION, "substrate_id": row.substrate_id, "target": target, "feature_set": "rdkit_morgan", "model": "ridge", "predicted_value": float(ridge_value), "status": "prediction_only"},
                        {"schema_version": SCHEMA_VERSION, "substrate_id": row.substrate_id, "target": target, "feature_set": "rdkit_morgan", "model": "elastic_net", "predicted_value": float(elastic_value), "status": "prediction_only"},
                    ]
                )
            for row, knn_value in zip(late_stage_rows, knn_values):
                unseen_predictions.append(
                    {"schema_version": SCHEMA_VERSION, "substrate_id": row.substrate_id, "target": target, "feature_set": "rdkit_morgan", "model": "tanimoto_knn", "predicted_value": float(knn_value), "status": "prediction_only"}
                )
    if unseen_predictions:
        write_csv(output_dir / "late-stage-predictions.csv", unseen_predictions, list(unseen_predictions[0].keys()))
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "records_path": str(records_path),
        "stage2p_features_path": str(stage2p_path) if stage2p_path else None,
        "catalyst_id": catalyst,
        "target_names": list(targets),
        "feature_set": feature_set,
        "model_policy": {
            "primary_model": "ridge",
            "challengers": ["elastic_net", "tanimoto_knn"],
            "ridge_alpha": 10.0,
            "elastic_net_alpha": 0.1,
            "elastic_net_l1_ratio": 0.15,
            "prediction_bounds": {"lower": PERCENT_TARGET_BOUNDS[0], "upper": PERCENT_TARGET_BOUNDS[1]},
        },
        "acquisition_policy": {
            "unit": "whole_substrate",
            "routes": routes,
            "uncertainty_diversity_weights": {"diversity": 0.4, "uncertainty": 0.4, "family_coverage": 0.2},
            "performance_first_weights": {"predicted_performance": 0.5, "uncertainty": 0.3, "diversity": 0.2},
            "random_route_replicates": replicates,
            "random_route_prefix_evaluation": "every_labelled_prefix",
            "random_route_initial_seed_sampling": "uniform_without_replacement_two_substrates_per_replicate",
            "random_route_aggregation": "mean_mae_across_independent_replicates_with_q25_q75_band",
            "random_route_challenger_models": ["ridge", "tanimoto_knn"],
            "random_route_challenger_note": "Elastic Net is omitted from randomized replicate curves to keep the 500-replicate stress test tractable; it remains in deterministic route and reference comparisons.",
        },
        "scope_counts": {
            "input_records": len(rows),
            "active_records": len(active_indices),
            "active_records_with_target": target_active_counts,
            "locked_audit_records": len(audit_indices),
            "late_stage_locked_audit_records": len(late_stage_rows),
            "late_stage_prediction_records": len(late_stage_rows),
        },
        "locked_audit_ids": [table.rows[index].substrate_id for index in audit_indices],
        "locked_late_stage_audit_ids": [row.substrate_id for row in late_stage_rows],
        "excluded_ids": sorted(excluded),
        "family_filter": sorted(allowed_families),
        "reference_metrics": references,
        "convergence": convergence,
        "outputs": {
            "scope_features": "scope-features.csv",
            "learning_curve": "learning-curve.csv",
            "learning_curve_summary": "learning-curve-summary.csv",
            "selection_events": "selection-events.csv",
            "random_seed_pairs": "random-seed-pairs.csv",
            "audit_predictions": "audit-predictions.csv",
            "audit_metrics": "audit-metrics.csv",
            "late_stage_predictions": "late-stage-predictions.csv",
        },
    }
    write_json(output_dir / "scope-progression-manifest.json", manifest)
    return manifest


def parse_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--stage2p-features", type=Path)
    parser.add_argument("--late-stage-records", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--catalyst-id")
    parser.add_argument("--target", action="append", choices=["ee_percent", "isolated_yield_percent"])
    parser.add_argument("--feature-set", choices=["rdkit_morgan", "rdkit_morgan_stage2p"], default="rdkit_morgan_stage2p")
    parser.add_argument("--audit-ids", default="")
    parser.add_argument("--audit-fraction", type=float, default=0.0)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--exclude-ids", default="")
    parser.add_argument("--family-id", action="append", default=[])
    args = parser.parse_args()
    manifest = run_analysis(
        records_path=args.records,
        stage2p_path=args.stage2p_features,
        output_dir=args.output_dir,
        catalyst=args.catalyst_id,
        targets=args.target or ["ee_percent", "isolated_yield_percent"],
        feature_set=args.feature_set,
        audit_ids=parse_ids(args.audit_ids),
        audit_fraction=args.audit_fraction,
        replicates=args.replicates,
        seed=args.seed,
        late_stage_path=args.late_stage_records,
        exclude_ids=parse_ids(args.exclude_ids),
        family_ids=args.family_id,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

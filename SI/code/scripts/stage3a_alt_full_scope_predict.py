#!/usr/bin/env python3
"""Train full-scope ee models and predict latest unseen manual substrates."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import platform
import warnings
from pathlib import Path
from typing import Any

import numpy
from numbers_parser import Document
from rdkit import Chem
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
STAGE2_FULL_SCOPE = ROOT / "scripts/stage2_full_scope_benchmark.py"
STAGE2_CONTRACT = ROOT / "scripts/stage2_contract.py"
STAGE3A_COMPARISON = ROOT / "scripts/stage3a_seed_model_comparison.py"
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_WORKBOOK = ROOT / "substrate_manual_1_Latestage.numbers"
DEFAULT_OUTPUT = ROOT / "data/jacs_2025/stage3/model-comparison/stage3a-alt-full-scope-unseen-predictions.csv"
DEFAULT_REPORT = ROOT / "data/jacs_2025/stage3/model-comparison/stage3a-alt-full-scope-unseen-report.json"
DEFAULT_MATRIX = ROOT / "data/jacs_2025/stage3/model-comparison/stage3a-alt-full-scope-training-matrix.csv"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


stage2_full_scope = load_module("stage2_full_scope_benchmark", STAGE2_FULL_SCOPE)
stage2_contract = load_module("stage2_contract", STAGE2_CONTRACT)
stage3a_comparison = load_module("stage3a_seed_model_comparison", STAGE3A_COMPARISON)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def atom_mapped_smiles(smiles: str) -> str:
    molecule = Chem.MolFromSmiles(smiles, sanitize=True)
    if molecule is None:
        raise ValueError(f"Could not parse SMILES: {smiles}")
    for atom_index, atom in enumerate(molecule.GetAtoms(), start=1):
        atom.SetAtomMapNum(atom_index)
    return Chem.MolToSmiles(molecule, canonical=False)


def proximal_azide_nitrogen(molecule: Chem.Mol) -> Chem.Atom:
    matches = []
    for atom in molecule.GetAtoms():
        if not stage3a_comparison.is_azide_nitrogen(atom):
            continue
        has_carbon_neighbor = any(neighbor.GetSymbol() == "C" for neighbor in atom.GetNeighbors())
        has_nitrogen_neighbor = any(neighbor.GetSymbol() == "N" for neighbor in atom.GetNeighbors())
        if has_carbon_neighbor and has_nitrogen_neighbor:
            matches.append(atom)
    if len(matches) != 1:
        raise ValueError(f"Expected one proximal azide nitrogen, found {len(matches)}")
    return matches[0]


def inferred_reported_site(candidate_sites: list[dict[str, Any]], molecule: Chem.Mol) -> dict[str, Any]:
    proximal_n = proximal_azide_nitrogen(molecule)
    distance_matrix = Chem.GetDistanceMatrix(molecule)
    candidate_atoms = [
        (site, stage3a_comparison.atom_by_map_id(molecule, site["atom_map_id"]))
        for site in candidate_sites
    ]
    nonaryl = [
        (site, atom)
        for site, atom in candidate_atoms
        if site.get("site_type") != "aryl" and not atom.GetIsAromatic()
    ]
    pool = nonaryl or candidate_atoms
    target_distance_pool = [
        (site, atom)
        for site, atom in pool
        if int(distance_matrix[proximal_n.GetIdx(), atom.GetIdx()]) == 4
    ]
    if not target_distance_pool:
        target_distance_pool = sorted(
            pool,
            key=lambda item: (
                abs(float(distance_matrix[proximal_n.GetIdx(), item[1].GetIdx()]) - 4.0),
                -int(item[1].GetTotalNumHs()),
                item[0]["atom_map_id"],
            ),
        )[:1]
    reported = dict(target_distance_pool[0][0])
    reported["role"] = "inferred_product_forming_c_h_for_unseen_prediction"
    return reported


def manual_rows(workbook_path: Path) -> list[dict[str, str]]:
    workbook = Document(workbook_path)
    table = workbook.sheets[0].tables[0]
    rows = []
    for index, values in enumerate(table.rows(values_only=True)):
        if index == 0:
            continue
        entry = values[0] if len(values) > 0 else None
        smiles = values[1] if len(values) > 1 else None
        if not entry or not smiles:
            continue
        if not isinstance(smiles, str):
            raise ValueError(f"Workbook row {index + 1}: expected SMILES string")
        entry_text = str(entry)
        substrate_id = f"1{entry_text.lower()}"
        rows.append({"entry": entry_text, "substrate_id": substrate_id, "azide_smiles": smiles})
    return rows


def prediction_record(row: dict[str, str]) -> dict[str, Any]:
    mapped_smiles = atom_mapped_smiles(row["azide_smiles"])
    molecule = Chem.MolFromSmiles(mapped_smiles, sanitize=True)
    assert molecule is not None
    candidate_sites = stage2_contract.candidate_sites_from_mapped_smiles(row["substrate_id"], mapped_smiles)
    reported_site = inferred_reported_site(candidate_sites, molecule)
    return {
        "substrate_id": row["substrate_id"],
        "reaction_id": f"jacs-2025-{row['substrate_id']}",
        "family": {"family_id": "latestage-unseen"},
        "catalyst_id": "fe-p7-cl",
        "condition": {"temperature_c": 80},
        "outcome": {"ee_percent": None, "ee_status": "prediction_target"},
        "structure": {
            "azide_smiles": row["azide_smiles"],
            "atom_mapped_substrate_smiles": mapped_smiles,
        },
        "reaction_center": {
            "assignment_method": "graph_distance_4_from_proximal_azide_n",
            "reported_reactive_site": reported_site,
            "candidate_sites": candidate_sites,
            "reported_site_in_candidates": True,
        },
    }


def training_records(records_path: Path, include_zero_curated: bool) -> list[dict[str, Any]]:
    records = []
    for record in read_jsonl(records_path):
        ee = record.get("outcome", {}).get("ee_percent")
        ee_status = record.get("outcome", {}).get("ee_status")
        if not is_number(ee):
            continue
        if ee_status == "zero_curated" and not include_zero_curated:
            continue
        records.append(record)
    return sorted(records, key=lambda item: item["substrate_id"])


def base_features(record: dict[str, Any]) -> tuple[dict[str, float], list[int]]:
    features, fingerprint = stage2_full_scope.featurize_record(record)
    features.update(stage2_full_scope.reaction_center_features(record))
    return features, fingerprint


def alt_features(record: dict[str, Any]) -> dict[str, float]:
    molecule = stage3a_comparison.molecule_from_record(record)
    site_rules = [
        stage3a_comparison.stage3a_alt_site_rule(record, molecule, site)
        for site in record["reaction_center"]["candidate_sites"]
    ]
    feature_block = stage3a_comparison.aggregate_stage3a_alt_rules(site_rules)
    features: dict[str, float] = {}
    stage2_full_scope.add_numeric_features(features, "stage3a_alt_hetero_site", feature_block)
    return features


def featurize_records(records: list[dict[str, Any]], feature_set: str) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        features, fingerprint = base_features(record)
        if feature_set == "stage3a_alt":
            features.update(alt_features(record))
        rows.append(
            {
                "substrate_id": record["substrate_id"],
                "family_id": record["family"]["family_id"],
                "target_value": record["outcome"].get("ee_percent"),
                "features": features,
                "fingerprint": fingerprint,
                "azide_smiles": record["structure"]["azide_smiles"],
            }
        )
    return rows


def matrix(rows: list[dict[str, Any]], feature_names: list[str]) -> numpy.ndarray:
    return numpy.array([[row["features"].get(name, 0.0) for name in feature_names] for row in rows], dtype=float)


def estimator_grid() -> list[dict[str, Any]]:
    return [
        {
            "alpha": alpha,
            "l1_ratio": l1_ratio,
            "estimator": make_pipeline(
                StandardScaler(),
                ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=20000, random_state=0),
            ),
        }
        for alpha in [0.01, 0.1, 1.0, 10.0]
        for l1_ratio in [0.2, 0.5, 0.8]
    ]


def fit_predict(estimator: Any, x_train: numpy.ndarray, y_train: numpy.ndarray, x_pred: numpy.ndarray) -> numpy.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        estimator.fit(x_train, y_train)
    return numpy.asarray(estimator.predict(x_pred), dtype=float)


def select_elastic_net(x: numpy.ndarray, y: numpy.ndarray) -> dict[str, Any]:
    best = None
    for candidate in estimator_grid():
        predictions = []
        for holdout in range(len(y)):
            train = [index for index in range(len(y)) if index != holdout]
            pred = fit_predict(candidate["estimator"], x[train], y[train], x[[holdout]])[0]
            predictions.append(pred)
        y_pred = numpy.array(predictions, dtype=float)
        mae = float(mean_absolute_error(y, y_pred))
        if best is None or mae < best["loo_mae"]:
            best = {**candidate, "loo_mae": mae, "loo_predictions": y_pred}
    assert best is not None
    return best


def model_metrics(y: numpy.ndarray, y_pred: numpy.ndarray) -> dict[str, float]:
    return {
        "loo_mae": float(mean_absolute_error(y, y_pred)),
        "loo_rmse": float(mean_squared_error(y, y_pred) ** 0.5),
        "loo_r2": float(r2_score(y, y_pred)),
        "within_15_ee_count": int(numpy.sum(numpy.abs(y_pred - y) < 15.0)),
        "record_count": int(len(y)),
    }


def clipped_ee(value: float) -> float:
    return min(100.0, max(0.0, value))


def write_training_matrix(path: Path, rows: list[dict[str, Any]], feature_names: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["substrate_id", "target_value"] + feature_names)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "substrate_id": row["substrate_id"],
                    "target_value": row["target_value"],
                    **{name: row["features"].get(name, 0.0) for name in feature_names},
                }
            )


def run(args: argparse.Namespace) -> dict[str, Any]:
    train_records = training_records(args.records, include_zero_curated=args.include_zero_curated)
    known_ids = {record["substrate_id"] for record in read_jsonl(args.records)}
    unseen_records = [
        prediction_record(row)
        for row in manual_rows(args.workbook)
        if row["substrate_id"] not in known_ids
    ]
    if not unseen_records:
        raise ValueError(f"{display_path(args.workbook)} did not contain unseen substrates")

    model_outputs = {}
    prediction_rows = []
    all_training_rows_for_matrix = []
    all_feature_names_for_matrix = []
    for feature_set in ["stage2_base", "stage3a_alt"]:
        train_rows = featurize_records(train_records, "base" if feature_set == "stage2_base" else "stage3a_alt")
        pred_rows = featurize_records(unseen_records, "base" if feature_set == "stage2_base" else "stage3a_alt")
        feature_names = sorted({name for row in train_rows + pred_rows for name in row["features"]})
        x_train = matrix(train_rows, feature_names)
        y_train = numpy.array([row["target_value"] for row in train_rows], dtype=float)
        x_pred = matrix(pred_rows, feature_names)
        selected = select_elastic_net(x_train, y_train)
        final_estimator = selected["estimator"]
        predictions = fit_predict(final_estimator, x_train, y_train, x_pred)
        model_outputs[feature_set] = {
            "feature_count": len(feature_names),
            "selected_alpha": selected["alpha"],
            "selected_l1_ratio": selected["l1_ratio"],
            **model_metrics(y_train, selected["loo_predictions"]),
        }
        if feature_set == "stage3a_alt":
            all_training_rows_for_matrix = train_rows
            all_feature_names_for_matrix = feature_names
        for row, prediction in zip(pred_rows, predictions, strict=True):
            existing = next((item for item in prediction_rows if item["substrate_id"] == row["substrate_id"]), None)
            if existing is None:
                existing = {
                    "substrate_id": row["substrate_id"],
                    "entry": row["substrate_id"].removeprefix("1"),
                    "azide_smiles": row["azide_smiles"],
                }
                prediction_rows.append(existing)
            existing[f"{feature_set}_prediction"] = float(prediction)
            existing[f"{feature_set}_prediction_clipped_0_100"] = clipped_ee(float(prediction))

    for row in prediction_rows:
        row["stage3a_alt_minus_stage2_base"] = row["stage3a_alt_prediction"] - row["stage2_base_prediction"]
        row["stage3a_alt_minus_stage2_base_clipped_0_100"] = (
            row["stage3a_alt_prediction_clipped_0_100"] - row["stage2_base_prediction_clipped_0_100"]
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        fieldnames = [
            "substrate_id",
            "entry",
            "stage2_base_prediction",
            "stage2_base_prediction_clipped_0_100",
            "stage3a_alt_prediction",
            "stage3a_alt_prediction_clipped_0_100",
            "stage3a_alt_minus_stage2_base",
            "stage3a_alt_minus_stage2_base_clipped_0_100",
            "azide_smiles",
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(prediction_rows)

    write_training_matrix(args.matrix, all_training_rows_for_matrix, all_feature_names_for_matrix)
    report = {
        "schema_version": "stage3a-alt-full-scope-unseen-prediction-report-v1",
        "status": "full_fit_unseen_prediction_not_validated_without_unseen_ee_labels",
        "training_record_count": len(train_records),
        "training_policy": "all numeric ee records including zero_curated; excludes structurally not-applicable achiral ee",
        "workbook_path": display_path(args.workbook),
        "unseen_prediction_count": len(prediction_rows),
        "raw_unseen_predictions_outside_0_100_count": sum(
            1
            for row in prediction_rows
            for key in ["stage2_base_prediction", "stage3a_alt_prediction"]
            if row[key] < 0.0 or row[key] > 100.0
        ),
        "prediction_path": display_path(args.output),
        "training_matrix_path": display_path(args.matrix),
        "model_class": "standard_scaled_elastic_net_selected_by_training_leave_one_out_mae",
        "models": model_outputs,
        "environment": {
            "python_version": platform.python_version(),
            "sklearn_version": __import__("sklearn").__version__,
            "numpy_version": numpy.__version__,
            "rdkit_version": Chem.rdBase.rdkitVersion,
        },
        "caveats": [
            "Unseen rows have no experimental ee labels in the workbook, so performance means training-set LOO diagnostics plus prediction comparison, not external validation.",
            "Unseen reaction centers are inferred as non-aromatic candidate C-H sites at graph distance four from the proximal azide nitrogen.",
            "This is a graph/structure-only comparison because the unseen substrates do not yet have generated pose-summary or pose-interaction features.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--include-zero-curated", action="store_true", default=True)
    return parser.parse_args()


def main() -> None:
    report = run(parse_args())
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run full Stage 1/2 and Stage 3a-alt predictions for latestage unseen substrates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
import shutil
import subprocess
import sys
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
STAGE1_CONTRACT = ROOT / "scripts/stage1_contract.py"
STAGE2_POSE_SUMMARY = ROOT / "scripts/stage2_pose_summary.py"
STAGE2_POSE_INTERACTION = ROOT / "scripts/stage2_pose_interaction.py"
STAGE2_FULL_SCOPE = ROOT / "scripts/stage2_full_scope_benchmark.py"
STAGE2_CONTRACT = ROOT / "scripts/stage2_contract.py"
STAGE3A_COMPARISON = ROOT / "scripts/stage3a_seed_model_comparison.py"
DEFAULT_WORKBOOK = ROOT / "substrate_manual_1_Latestage.numbers"
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_TRAIN_POSE_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"
DEFAULT_TRAIN_POSE_INTERACTION = ROOT / "data/jacs_2025/stage2/features/pose-interaction.jsonl"
DEFAULT_WORK_DIR = ROOT / "data/jacs_2025/stage3/latestage"
DEFAULT_STAGE2_PREDICTIONS = ROOT / "data/jacs_2025/stage3/model-comparison/stage2-base-full-workflow-unseen-predictions.csv"
DEFAULT_STAGE3A_ALT_PREDICTIONS = ROOT / "data/jacs_2025/stage3/model-comparison/stage3a-alt-full-workflow-unseen-predictions.csv"
DEFAULT_COMPARISON = ROOT / "data/jacs_2025/stage3/model-comparison/stage3a-alt-full-workflow-unseen-comparison.csv"
DEFAULT_REPORT = ROOT / "data/jacs_2025/stage3/model-comparison/stage3a-alt-full-workflow-unseen-report.json"


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def to_nitrene(smiles: str) -> tuple[str, str]:
    prefix = "N#N=N"
    suffix = "N=N#N"
    prefix_count = smiles.count(prefix)
    suffix_count = smiles.count(suffix)
    if prefix_count + suffix_count != 1:
        raise ValueError(f"Expected one terminal azide in {smiles}")
    if prefix_count:
        return smiles.replace(prefix, "[N]", 1), "prefix"
    return smiles.replace(suffix, "[N]", 1), "suffix"


def latestage_manual_rows(workbook_path: Path) -> list[dict[str, str]]:
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
        entry_text = str(entry)
        substrate_id = f"1{entry_text.lower()}"
        nitrene_smiles, azide_position = to_nitrene(smiles)
        rows.append(
            {
                "manual_row": str(index),
                "source_entry_raw": entry_text,
                "substrate_id": substrate_id,
                "product_id": f"2{entry_text.lower()}",
                "azide_smiles": smiles,
                "nitrene_smiles": nitrene_smiles,
                "azide_position": azide_position,
                "removed_species": "N2",
                "retained_atom": "aryl-bound proximal azide N",
                "intermediate_scope": "free nitrene representation; Fe coordination is added in the constrained pose pipeline",
                "validation_status": "terminal-azide pattern validated for latestage unseen prediction",
            }
        )
    return rows


def write_manual_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


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
        if any(neighbor.GetSymbol() == "C" for neighbor in atom.GetNeighbors()):
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
    nonaryl = [(site, atom) for site, atom in candidate_atoms if site.get("site_type") != "aryl" and not atom.GetIsAromatic()]
    pool = nonaryl or candidate_atoms
    distance_four = [(site, atom) for site, atom in pool if int(distance_matrix[proximal_n.GetIdx(), atom.GetIdx()]) == 4]
    if not distance_four:
        distance_four = sorted(
            pool,
            key=lambda item: (
                abs(float(distance_matrix[proximal_n.GetIdx(), item[1].GetIdx()]) - 4.0),
                -int(item[1].GetTotalNumHs()),
                item[0]["atom_map_id"],
            ),
        )[:1]
    reported = dict(distance_four[0][0])
    reported["role"] = "inferred_product_forming_c_h_for_unseen_prediction"
    return reported


def latestage_records(manual_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    records = []
    for row in manual_rows:
        mapped = atom_mapped_smiles(row["azide_smiles"])
        molecule = Chem.MolFromSmiles(mapped, sanitize=True)
        assert molecule is not None
        candidate_sites = stage2_contract.candidate_sites_from_mapped_smiles(row["substrate_id"], mapped)
        reported_site = inferred_reported_site(candidate_sites, molecule)
        records.append(
            {
                "schema_version": "stage2-reaction-record-v1",
                "substrate_id": row["substrate_id"],
                "reaction_id": f"jacs-2025-{row['substrate_id']}",
                "curation_status": "atom_mapped",
                "review_status": "prediction_only",
                "catalyst_id": "fe-p7-cl",
                "family": {"family_id": "latestage-unseen"},
                "condition": {"temperature_c": 80},
                "outcome": {"ee_percent": None, "ee_status": "prediction_target"},
                "structure": {
                    "azide_smiles": row["azide_smiles"],
                    "atom_mapped_substrate_smiles": mapped,
                },
                "reaction_center": {
                    "assignment_method": "graph_distance_4_from_proximal_azide_n",
                    "review_status": "checked",
                    "reported_reactive_site": reported_site,
                    "candidate_sites": candidate_sites,
                    "reported_site_in_candidates": True,
                },
            }
        )
    return records


def run_command(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, text=True, check=True)


def replace_text_values(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        for source, target in replacements.items():
            value = value.replace(source, target)
        return value
    if isinstance(value, list):
        return [replace_text_values(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: replace_text_values(item, replacements) for key, item in value.items()}
    return value


def rename_copied_geometry_files(target_dir: Path, replacements: dict[str, str]) -> None:
    for path in sorted(target_dir.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        new_name = path.name
        for source, target in replacements.items():
            new_name = new_name.replace(source, target)
        if new_name != path.name:
            path.rename(path.with_name(new_name))


def reuse_duplicate_stage1_report(
    source_id: str,
    target_row: dict[str, str],
    manual_csv: Path,
    report_dir: Path,
    geometry_dir: Path,
    force: bool,
) -> bool:
    target_id = target_row["substrate_id"]
    source_report_path = report_dir / f"stage-1-smoke-{source_id}.json"
    target_report_path = report_dir / f"stage-1-smoke-{target_id}.json"
    if target_report_path.exists() and not force:
        return True
    if not source_report_path.exists():
        return False

    source_geometry_dir = geometry_dir / source_id
    target_geometry_dir = geometry_dir / target_id
    if source_geometry_dir.exists():
        if target_geometry_dir.exists():
            shutil.rmtree(target_geometry_dir)
        shutil.copytree(source_geometry_dir, target_geometry_dir)

    replacements = {
        source_id: target_id,
        f"2{source_id[1:]}": target_row["product_id"],
        f"stage1-smoke-{source_id}": f"stage1-smoke-{target_id}",
        f"/{source_id}/": f"/{target_id}/",
    }
    if target_geometry_dir.exists():
        rename_copied_geometry_files(target_geometry_dir, replacements)

    report = json.loads(source_report_path.read_text(encoding="utf-8"))
    report = replace_text_values(report, replacements)
    report["substrate_record"].update(
        {
            "substrate_id": target_id,
            "product_id": target_row["product_id"],
            "azide_smiles": target_row["azide_smiles"],
            "nitrene_smiles": target_row["nitrene_smiles"],
            "azide_position": target_row["azide_position"],
        }
    )
    report["pose_generation_run"]["substrate_ids"] = [target_id]
    report["pose_generation_run"]["manual_substrates_sha256"] = file_sha256(manual_csv)
    report["pose_generation_run"]["duplicate_pose_reuse"] = {
        "source_substrate_id": source_id,
        "reason": "identical azide_smiles in latestage unseen workbook",
    }
    target_report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def ensure_stage1_reports(
    manual_csv: Path,
    manual_rows: list[dict[str, str]],
    report_dir: Path,
    geometry_dir: Path,
    substrate_ids: list[str],
    pool_size: int,
    retain_low_count: int,
    retain_high_count: int,
    force: bool,
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    geometry_dir.mkdir(parents=True, exist_ok=True)
    first_id_by_smiles: dict[str, str] = {}
    row_by_id = {row["substrate_id"]: row for row in manual_rows}
    for substrate_id in substrate_ids:
        output = report_dir / f"stage-1-smoke-{substrate_id}.json"
        if output.exists() and not force:
            first_id_by_smiles.setdefault(row_by_id[substrate_id]["azide_smiles"], substrate_id)
            continue
        azide_smiles = row_by_id[substrate_id]["azide_smiles"]
        duplicate_source_id = first_id_by_smiles.get(azide_smiles)
        if duplicate_source_id and reuse_duplicate_stage1_report(
            duplicate_source_id,
            row_by_id[substrate_id],
            manual_csv,
            report_dir,
            geometry_dir,
            force,
        ):
            first_id_by_smiles.setdefault(azide_smiles, substrate_id)
            continue
        run_command(
            [
                sys.executable,
                str(STAGE1_CONTRACT),
                "--substrate-id",
                substrate_id,
                "--manual-substrates",
                str(manual_csv),
                "--output",
                str(output),
                "--geometry-dir",
                str(geometry_dir),
                "--pool-size",
                str(pool_size),
                "--retain-low-count",
                str(retain_low_count),
                "--retain-high-count",
                str(retain_high_count),
            ],
            ROOT,
        )
        first_id_by_smiles.setdefault(azide_smiles, substrate_id)


def training_records(records_path: Path) -> list[dict[str, Any]]:
    records = []
    for record in read_jsonl(records_path):
        ee = record.get("outcome", {}).get("ee_percent")
        if isinstance(ee, int | float) and not isinstance(ee, bool) and math.isfinite(ee):
            records.append(record)
    return sorted(records, key=lambda item: item["substrate_id"])


def add_numeric_features(target: dict[str, float], prefix: str, values: dict[str, Any]) -> None:
    for key, value in values.items():
        if isinstance(value, bool):
            target[f"{prefix}.{key}"] = float(value)
        elif isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value):
            target[f"{prefix}.{key}"] = float(value)


def pose_features_by_id(pose_summary_path: Path, pose_interaction_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    summary = {row["substrate_id"]: row for row in read_jsonl(pose_summary_path)}
    interaction = stage2_full_scope.aggregate_pose_interactions(read_jsonl(pose_interaction_path))
    return summary, interaction


def base_features(record: dict[str, Any], pose_summary: dict[str, Any], pose_interaction: dict[str, Any]) -> tuple[dict[str, float], list[int]]:
    features, fingerprint = stage2_full_scope.featurize_record(record)
    features.update(stage2_full_scope.reaction_center_features(record))
    add_numeric_features(features, "pose_summary", pose_summary[record["substrate_id"]]["feature_blocks"]["pose_summary"])
    add_numeric_features(features, "pose_interaction", pose_interaction[record["substrate_id"]])
    return features, fingerprint


def alt_features(record: dict[str, Any]) -> dict[str, float]:
    molecule = stage3a_comparison.molecule_from_record(record)
    site_rules = [stage3a_comparison.stage3a_alt_site_rule(record, molecule, site) for site in record["reaction_center"]["candidate_sites"]]
    block = stage3a_comparison.aggregate_stage3a_alt_rules(site_rules)
    features: dict[str, float] = {}
    add_numeric_features(features, "stage3a_alt_hetero_site", block)
    return features


def featurize(
    records: list[dict[str, Any]],
    pose_summary_path: Path,
    pose_interaction_path: Path,
    include_stage3a_alt: bool,
) -> list[dict[str, Any]]:
    pose_summary, pose_interaction = pose_features_by_id(pose_summary_path, pose_interaction_path)
    rows = []
    for record in records:
        features, fingerprint = base_features(record, pose_summary, pose_interaction)
        if include_stage3a_alt:
            features.update(alt_features(record))
        rows.append(
            {
                "substrate_id": record["substrate_id"],
                "family_id": record["family"]["family_id"],
                "target_value": record["outcome"].get("ee_percent"),
                "azide_smiles": record["structure"]["azide_smiles"],
                "features": features,
                "fingerprint": fingerprint,
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
            "estimator": make_pipeline(StandardScaler(), ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=20000, random_state=0)),
        }
        for alpha in [0.01, 0.1, 1.0, 10.0]
        for l1_ratio in [0.2, 0.5, 0.8]
    ]


def fit_predict(estimator: Any, x_train: numpy.ndarray, y_train: numpy.ndarray, x_pred: numpy.ndarray) -> numpy.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        estimator.fit(x_train, y_train)
    return numpy.asarray(estimator.predict(x_pred), dtype=float)


def select_model(x: numpy.ndarray, y: numpy.ndarray) -> dict[str, Any]:
    best = None
    for candidate in estimator_grid():
        predictions = []
        for holdout in range(len(y)):
            train = [index for index in range(len(y)) if index != holdout]
            predictions.append(fit_predict(candidate["estimator"], x[train], y[train], x[[holdout]])[0])
        y_pred = numpy.array(predictions)
        mae = float(mean_absolute_error(y, y_pred))
        if best is None or mae < best["loo_mae"]:
            best = {**candidate, "loo_predictions": y_pred, "loo_mae": mae}
    assert best is not None
    return best


def metrics(y: numpy.ndarray, y_pred: numpy.ndarray) -> dict[str, Any]:
    return {
        "loo_mae": float(mean_absolute_error(y, y_pred)),
        "loo_rmse": float(mean_squared_error(y, y_pred) ** 0.5),
        "loo_r2": float(r2_score(y, y_pred)),
        "within_15_ee_count": int(numpy.sum(numpy.abs(y_pred - y) < 15.0)),
        "record_count": int(len(y)),
    }


def clipped(value: float) -> float:
    return min(100.0, max(0.0, value))


def write_prediction_table(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        fieldnames = ["substrate_id", "prediction_raw", "prediction_clipped_0_100", "azide_smiles"]
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def train_and_predict(
    train_records: list[dict[str, Any]],
    pred_records: list[dict[str, Any]],
    train_pose_summary: Path,
    train_pose_interaction: Path,
    pred_pose_summary: Path,
    pred_pose_interaction: Path,
    include_stage3a_alt: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    train_rows = featurize(train_records, train_pose_summary, train_pose_interaction, include_stage3a_alt)
    pred_rows = featurize(pred_records, pred_pose_summary, pred_pose_interaction, include_stage3a_alt)
    feature_names = sorted({name for row in train_rows + pred_rows for name in row["features"]})
    x_train = matrix(train_rows, feature_names)
    y_train = numpy.array([row["target_value"] for row in train_rows], dtype=float)
    x_pred = matrix(pred_rows, feature_names)
    selected = select_model(x_train, y_train)
    pred_values = fit_predict(selected["estimator"], x_train, y_train, x_pred)
    model_report = {
        "feature_count": len(feature_names),
        "selected_alpha": selected["alpha"],
        "selected_l1_ratio": selected["l1_ratio"],
        **metrics(y_train, selected["loo_predictions"]),
    }
    prediction_rows = [
        {
            "substrate_id": row["substrate_id"],
            "prediction_raw": float(prediction),
            "prediction_clipped_0_100": clipped(float(prediction)),
            "azide_smiles": row["azide_smiles"],
        }
        for row, prediction in zip(pred_rows, pred_values, strict=True)
    ]
    return model_report, prediction_rows


def write_comparison(path: Path, stage2_rows: list[dict[str, Any]], stage3_rows: list[dict[str, Any]]) -> None:
    by_id = {row["substrate_id"]: row for row in stage3_rows}
    rows = []
    for row in stage2_rows:
        stage3 = by_id[row["substrate_id"]]
        rows.append(
            {
                "substrate_id": row["substrate_id"],
                "stage2_base_prediction_raw": row["prediction_raw"],
                "stage2_base_prediction_clipped_0_100": row["prediction_clipped_0_100"],
                "stage3a_alt_prediction_raw": stage3["prediction_raw"],
                "stage3a_alt_prediction_clipped_0_100": stage3["prediction_clipped_0_100"],
                "stage3a_alt_minus_stage2_base_raw": stage3["prediction_raw"] - row["prediction_raw"],
                "stage3a_alt_minus_stage2_base_clipped_0_100": stage3["prediction_clipped_0_100"] - row["prediction_clipped_0_100"],
                "azide_smiles": row["azide_smiles"],
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stage1_settings_by_substrate(report_dir: Path, substrate_ids: list[str]) -> dict[str, dict[str, Any]]:
    settings = {}
    for substrate_id in substrate_ids:
        report = json.loads((report_dir / f"stage-1-smoke-{substrate_id}.json").read_text(encoding="utf-8"))
        run_info = report["pose_generation_run"]
        settings[substrate_id] = {
            "generated_pool_size": run_info["generated_pool_size"],
            "retained_low_energy_count": run_info["retained_low_energy_count"],
            "retained_high_energy_count": run_info["retained_high_energy_count"],
            "written_pose_count": run_info["written_pose_count"],
            "duplicate_pose_reuse": run_info.get("duplicate_pose_reuse"),
        }
    return settings


def run(args: argparse.Namespace) -> dict[str, Any]:
    manual_csv = args.work_dir / "manual-substrates-latestage.csv"
    records_path = args.work_dir / "latestage-prediction-records.jsonl"
    report_dir = args.work_dir / "stage1-panel"
    geometry_dir = args.work_dir / "stage1-geometries"
    pose_summary_path = args.work_dir / "stage2-pose-summary.jsonl"
    pose_interaction_path = args.work_dir / "stage2-pose-interaction.jsonl"

    skip_substrate_ids = {substrate_id.strip() for substrate_id in args.skip_substrate if substrate_id.strip()}
    manual_rows = [
        row for row in latestage_manual_rows(args.workbook)
        if row["substrate_id"] not in skip_substrate_ids
    ]
    if not manual_rows:
        raise ValueError("No latestage substrates remain after applying --skip-substrate")
    write_manual_csv(manual_csv, manual_rows)
    pred_records = latestage_records(manual_rows)
    write_jsonl(records_path, pred_records)
    substrate_ids = [record["substrate_id"] for record in pred_records]

    ensure_stage1_reports(
        manual_csv,
        manual_rows,
        report_dir,
        geometry_dir,
        substrate_ids,
        args.pool_size,
        args.retain_low_count,
        args.retain_high_count,
        args.force_stage1,
    )
    run_command([sys.executable, str(STAGE2_POSE_SUMMARY), "--records", str(records_path), "--stage1-report-dir", str(report_dir), "--output", str(pose_summary_path)], ROOT)
    run_command([sys.executable, str(STAGE2_POSE_INTERACTION), "--records", str(records_path), "--stage1-report-dir", str(report_dir), "--output", str(pose_interaction_path)], ROOT)

    train_records = training_records(args.records)
    stage2_report, stage2_rows = train_and_predict(
        train_records,
        pred_records,
        args.train_pose_summary,
        args.train_pose_interaction,
        pose_summary_path,
        pose_interaction_path,
        include_stage3a_alt=False,
    )
    write_prediction_table(args.stage2_predictions, stage2_rows)

    stage3_report, stage3_rows = train_and_predict(
        train_records,
        pred_records,
        args.train_pose_summary,
        args.train_pose_interaction,
        pose_summary_path,
        pose_interaction_path,
        include_stage3a_alt=True,
    )
    write_prediction_table(args.stage3a_alt_predictions, stage3_rows)
    write_comparison(args.comparison, stage2_rows, stage3_rows)

    report = {
        "schema_version": "stage3a-alt-full-workflow-unseen-report-v1",
        "status": "full_workflow_checkpoints_complete",
        "training_record_count": len(train_records),
        "unseen_prediction_count": len(pred_records),
        "skipped_substrate_ids": sorted(skip_substrate_ids),
        "workbook_path": display_path(args.workbook),
        "manual_substrates_path": display_path(manual_csv),
        "prediction_records_path": display_path(records_path),
        "stage1_report_dir": display_path(report_dir),
        "stage1_geometry_dir": display_path(geometry_dir),
        "stage2_pose_summary_path": display_path(pose_summary_path),
        "stage2_pose_interaction_path": display_path(pose_interaction_path),
        "checkpoint_1_stage2_base_prediction_table": display_path(args.stage2_predictions),
        "checkpoint_2_stage3a_alt_prediction_table": display_path(args.stage3a_alt_predictions),
        "comparison_table": display_path(args.comparison),
        "models": {"stage2_base": stage2_report, "stage3a_alt": stage3_report},
        "stage1_requested_settings_for_missing_reports": {
            "pool_size": args.pool_size,
            "retain_low_count": args.retain_low_count,
            "retain_high_count": args.retain_high_count,
        },
        "stage1_actual_settings_by_substrate": stage1_settings_by_substrate(report_dir, substrate_ids),
        "environment": {
            "python_version": platform.python_version(),
            "numpy_version": numpy.__version__,
            "rdkit_version": Chem.rdBase.rdkitVersion,
        },
        "caveats": [
            "The latestage substrates do not have experimental ee labels in the workbook, so unseen performance cannot be measured yet.",
            "Reported reactive C-H sites for unseen substrates are inferred by graph distance from the proximal azide nitrogen.",
            "Stage 3a-alt here means Stage 0/1/2 pose-aware features plus the graph-only heteroatom site-competition block.",
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--train-pose-summary", type=Path, default=DEFAULT_TRAIN_POSE_SUMMARY)
    parser.add_argument("--train-pose-interaction", type=Path, default=DEFAULT_TRAIN_POSE_INTERACTION)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--stage2-predictions", type=Path, default=DEFAULT_STAGE2_PREDICTIONS)
    parser.add_argument("--stage3a-alt-predictions", type=Path, default=DEFAULT_STAGE3A_ALT_PREDICTIONS)
    parser.add_argument("--comparison", type=Path, default=DEFAULT_COMPARISON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--pool-size", type=int, default=5000)
    parser.add_argument("--retain-low-count", type=int, default=100)
    parser.add_argument("--retain-high-count", type=int, default=100)
    parser.add_argument("--force-stage1", action="store_true")
    parser.add_argument("--skip-substrate", action="append", default=[])
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

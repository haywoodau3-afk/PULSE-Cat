#!/usr/bin/env python3
"""Compare seed-pilot ee models after Stage 1-v2 and Stage 3a feature additions."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy


ROOT = Path(__file__).resolve().parents[1]
STAGE2_ELASTIC_NET = ROOT / "scripts/stage2_elastic_net.py"
STAGE2_POSE_SUMMARY = ROOT / "scripts/stage2_pose_summary.py"
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_TIER1 = ROOT / "data/jacs_2025/stage2/features/tier1.jsonl"
DEFAULT_POSE_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"
DEFAULT_STAGE2_POSE_INTERACTION = ROOT / "data/jacs_2025/stage2/features/pose-interaction.jsonl"
DEFAULT_V2_SELECTION = ROOT / "data/jacs_2025/stage3/v2-pose/stage1-v2-pose-selection.jsonl"
DEFAULT_V2_POSE_SUMMARY = ROOT / "data/jacs_2025/stage3/v2-pose/stage2-v2-pose-summary.jsonl"
DEFAULT_V2_POSE_INTERACTION = ROOT / "data/jacs_2025/stage3/v2-pose/stage1-v2-pose-interaction.jsonl"
DEFAULT_REFERENCE_SUMMARY = ROOT / "data/jacs_2025/stage3/features/stage3a-lite-reference-summary.jsonl"
DEFAULT_SHELL_FEATURES = ROOT / "data/jacs_2025/stage3/features/local-3d-shell-features.jsonl"
DEFAULT_STAGE3A_ALT_RULES = ROOT / "data/jacs_2025/stage3/features/stage3a-alt-hetero-site-rules.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "data/jacs_2025/stage3/model-comparison"
DEFAULT_COMPARISON_REPORT = DEFAULT_OUTPUT_DIR / "stage3a-seed-model-comparison.json"
DEFAULT_COMPARISON_TABLE = DEFAULT_OUTPUT_DIR / "stage3a-seed-model-comparison.csv"
DEFAULT_PREDICTION_COMPARISON = DEFAULT_OUTPUT_DIR / "stage3a-alt-prediction-comparison.csv"


spec = importlib.util.spec_from_file_location("stage2_elastic_net", STAGE2_ELASTIC_NET)
stage2_elastic_net = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage2_elastic_net)

pose_summary_spec = importlib.util.spec_from_file_location("stage2_pose_summary", STAGE2_POSE_SUMMARY)
stage2_pose_summary = importlib.util.module_from_spec(pose_summary_spec)
assert pose_summary_spec.loader is not None
pose_summary_spec.loader.exec_module(stage2_pose_summary)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def selected_pose_ids(selection_path: Path) -> dict[str, set[str]]:
    selected: dict[str, set[str]] = {}
    for row in read_jsonl(selection_path):
        selected.setdefault(row["substrate_id"], set()).add(row["pose_id"])
    return selected


def write_v2_pose_interaction(stage2_pose_interaction_path: Path, selection_path: Path, output_path: Path) -> dict[str, Any]:
    selected = selected_pose_ids(selection_path)
    rows = [
        row
        for row in read_jsonl(stage2_pose_interaction_path)
        if row["substrate_id"] in selected and row["pose_id"] in selected[row["substrate_id"]]
    ]
    write_jsonl(output_path, rows)
    return {
        "schema_version": "stage1-v2-pose-interaction-filter-report-v1",
        "selected_substrate_count": len(selected),
        "pose_interaction_row_count": len(rows),
        "output_path": display_path(output_path),
    }


def source_pose_records_by_substrate(selection_path: Path) -> dict[str, list[dict[str, Any]]]:
    selected_rows = read_jsonl(selection_path)
    selected_by_report: dict[str, set[str]] = {}
    for row in selected_rows:
        selected_by_report.setdefault(row["provenance"]["source_stage1_report_path"], set()).add(row["pose_id"])

    poses_by_substrate: dict[str, list[dict[str, Any]]] = {}
    for report_path_text, pose_ids in selected_by_report.items():
        report_path = ROOT / report_path_text
        report = json.loads(report_path.read_text(encoding="utf-8"))
        poses = [pose for pose in report["pose_records"] if pose["pose_id"] in pose_ids]
        if len(poses) != len(pose_ids):
            missing = sorted(pose_ids - {pose["pose_id"] for pose in poses})
            raise ValueError(f"{report_path_text}: missing selected pose ids {missing}")
        substrate_id = stage2_pose_summary.report_substrate_id(report)
        poses_by_substrate[substrate_id] = poses
    return poses_by_substrate


def write_v2_pose_summary(records_path: Path, stage2_pose_summary_path: Path, selection_path: Path, output_path: Path) -> dict[str, Any]:
    records_by_id = {record["substrate_id"]: record for record in read_jsonl(records_path)}
    stage2_summary_by_id = {row["substrate_id"]: row for row in read_jsonl(stage2_pose_summary_path)}
    poses_by_substrate = source_pose_records_by_substrate(selection_path)
    rows = []
    for substrate_id in sorted(poses_by_substrate):
        poses = poses_by_substrate[substrate_id]
        source_summary = stage2_summary_by_id[substrate_id]
        source_features = source_summary["feature_blocks"]["pose_summary"]
        bucket_counts = {
            "low_energy_pose_count": sum(1 for pose in poses if pose.get("selection_bucket") == "low_energy"),
            "high_energy_pose_count": sum(1 for pose in poses if pose.get("selection_bucket") == "high_energy"),
        }
        features = {
            "generated_pool_size": source_features.get("generated_pool_size"),
            "valid_conformer_count": source_features.get("valid_conformer_count"),
            "clash_screened_valid_conformer_count": source_features.get("clash_screened_valid_conformer_count"),
            "clash_screen_passed_count": source_features.get("clash_screen_passed_count"),
            "clash_screen_failed_count": source_features.get("clash_screen_failed_count"),
            "written_pose_count": len(poses),
            "retained_low_energy_count": bucket_counts["low_energy_pose_count"],
            "retained_high_energy_count": bucket_counts["high_energy_pose_count"],
            "selected_pairwise_heavy_atom_rmsd_pair_count": None,
            "selected_pairwise_heavy_atom_rmsd_min": None,
            "selected_pairwise_heavy_atom_rmsd_mean": None,
            "selected_pairwise_heavy_atom_rmsd_max": None,
            "pool_uff_score_min": source_features.get("pool_uff_score_min"),
            "pool_uff_score_max": source_features.get("pool_uff_score_max"),
            "clash_screen_minimum_core_substrate_distance_min": source_features.get("clash_screen_minimum_core_substrate_distance_min"),
            "clash_screen_minimum_core_substrate_distance_max": source_features.get("clash_screen_minimum_core_substrate_distance_max"),
            "connectivity_preserved_count": stage2_pose_summary.boolean_count(poses, "connectivity_preserved"),
            "uff_optimisation_converged_count": stage2_pose_summary.boolean_count(poses, "uff_optimisation_converged"),
            "severe_clash_screen_passed_count": stage2_pose_summary.boolean_count(poses, "severe_clash_screen_passed"),
            "frozen_core_preserved_count": stage2_pose_summary.boolean_count(poses, "frozen_core_preserved"),
            "fe_n_distance_within_constraint_count": stage2_pose_summary.boolean_count(poses, "fe_n_distance_within_constraint"),
            "catalyst_uff_optimised_count": stage2_pose_summary.boolean_count(poses, "catalyst_uff_optimised"),
            "frozen_core_atom_count_min": min(stage2_pose_summary.numeric_pose_values(poses, "frozen_core_atom_count")),
            "frozen_core_atom_count_max": max(stage2_pose_summary.numeric_pose_values(poses, "frozen_core_atom_count")),
            "assembled_atom_count_min": min(stage2_pose_summary.numeric_pose_values(poses, "assembled_atom_count")),
            "assembled_atom_count_max": max(stage2_pose_summary.numeric_pose_values(poses, "assembled_atom_count")),
        }
        features.update(bucket_counts)
        features.update(stage2_pose_summary.numeric_summary(stage2_pose_summary.numeric_pose_values(poses, "uff_pose_score"), "uff_pose_score"))
        features.update(stage2_pose_summary.bucket_score_summary(poses, "low_energy"))
        features.update(stage2_pose_summary.bucket_score_summary(poses, "high_energy"))
        features.update(stage2_pose_summary.numeric_summary(stage2_pose_summary.numeric_pose_values(poses, "fe_n_distance_angstrom"), "fe_n_distance_angstrom"))
        features.update(stage2_pose_summary.numeric_summary(stage2_pose_summary.numeric_pose_values(poses, "core_rmsd_angstrom"), "core_rmsd_angstrom"))
        features.update(
            stage2_pose_summary.numeric_summary(
                stage2_pose_summary.numeric_pose_values(poses, "minimum_core_substrate_distance_angstrom"),
                "minimum_core_substrate_distance_angstrom",
            )
        )
        record = records_by_id[substrate_id]
        rows.append(
            {
                "schema_version": "stage2-v2-pose-summary-features-v1",
                "substrate_id": substrate_id,
                "reaction_id": record["reaction_id"],
                "curation_status": record["curation_status"],
                "feature_status": "computed_from_stage1_v2_selected_poses",
                "feature_blocks": {"pose_summary": features},
                "provenance": {
                    "source_stage2_pose_summary_path": display_path(stage2_pose_summary_path),
                    "stage1_v2_selection_path": display_path(selection_path),
                    "selected_pose_count": len(poses),
                },
            }
        )
    write_jsonl(output_path, rows)
    return {
        "schema_version": "stage2-v2-pose-summary-report-v1",
        "selected_substrate_count": len(rows),
        "pose_summary_row_count": len(rows),
        "output_path": display_path(output_path),
    }


def aggregate_numeric_feature_block(rows: list[dict[str, Any]], block_name: str) -> dict[str, dict[str, float]]:
    values_by_substrate: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        substrate_id = row["substrate_id"]
        values_by_substrate.setdefault(substrate_id, {})
        features = row["feature_blocks"][block_name]
        for key, value in features.items():
            if stage2_elastic_net.is_number(value) or isinstance(value, bool):
                values_by_substrate[substrate_id].setdefault(key, []).append(float(value))

    aggregated = {}
    for substrate_id, feature_values in values_by_substrate.items():
        substrate_features = {}
        for key, values in feature_values.items():
            for agg_key, agg_value in stage2_elastic_net.aggregate_values(values).items():
                substrate_features[f"{key}.{agg_key}"] = agg_value
        aggregated[substrate_id] = substrate_features
    return aggregated


def reported_reference_features(reference_summary_path: Path) -> dict[str, dict[str, float]]:
    output = {}
    for row in read_jsonl(reference_summary_path):
        if row.get("is_reported_reactive_site"):
            features: dict[str, float] = {}
            stage2_elastic_net.add_numeric_features(features, "reference", row["feature_blocks"]["stage3a_lite_reference"])
            output[row["substrate_id"]] = features
    return output


def reported_shell_features(reference_summary_path: Path, shell_features_path: Path) -> dict[str, dict[str, float]]:
    reported_site_by_substrate = {
        row["substrate_id"]: row["candidate_site_id"]
        for row in read_jsonl(reference_summary_path)
        if row.get("is_reported_reactive_site")
    }
    output = {}
    for row in read_jsonl(shell_features_path):
        substrate_id = row["substrate_id"]
        if row["candidate_site_id"] != reported_site_by_substrate.get(substrate_id):
            continue
        features: dict[str, float] = {}
        stage2_elastic_net.add_numeric_features(features, "reported_shell", row["feature_blocks"]["local_3d_shell_features"])
        output[substrate_id] = features
    return output


def molecule_from_record(record: dict[str, Any]) -> Any:
    try:
        from rdkit import Chem
    except ImportError as exc:
        raise RuntimeError("RDKit is required for Stage 3a-alt graph heteroatom rules") from exc

    molecule = Chem.MolFromSmiles(record["structure"]["atom_mapped_substrate_smiles"], sanitize=True)
    if molecule is None:
        raise ValueError(f"{record['substrate_id']}: atom-mapped substrate SMILES does not parse")
    return molecule


def atom_by_map_id(molecule: Any, atom_map_id: int) -> Any:
    matches = [atom for atom in molecule.GetAtoms() if atom.GetAtomMapNum() == atom_map_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one atom with map id {atom_map_id}, found {len(matches)}")
    return matches[0]


def graph_distance_matrix(molecule: Any) -> Any:
    from rdkit import Chem

    return Chem.GetDistanceMatrix(molecule)


def is_azide_nitrogen(atom: Any) -> bool:
    if atom.GetSymbol() != "N":
        return False
    stack = [atom]
    visited = set()
    while stack:
        current = stack.pop()
        if current.GetIdx() in visited:
            continue
        visited.add(current.GetIdx())
        for neighbor in current.GetNeighbors():
            if neighbor.GetSymbol() == "N":
                stack.append(neighbor)
    return len(visited) >= 3


def is_substrate_heteroatom(atom: Any) -> bool:
    symbol = atom.GetSymbol()
    return symbol not in {"C", "H"} and not is_azide_nitrogen(atom)


def is_binding_capable_heteroatom(atom: Any) -> bool:
    symbol = atom.GetSymbol()
    return symbol in {"N", "O", "S", "P", "Se"} and atom.GetFormalCharge() <= 0


def hetero_role_counts_by_distance(molecule: Any, atom: Any) -> dict[str, Any]:
    distance_matrix = graph_distance_matrix(molecule)
    counts = {
        "alpha_heteroatom_count": 0.0,
        "alpha_N_count": 0.0,
        "alpha_O_count": 0.0,
        "alpha_S_count": 0.0,
        "alpha_halogen_count": 0.0,
        "beta_gamma_heteroatom_count": 0.0,
        "beta_gamma_acceptor_count": 0.0,
        "remote_binding_heteroatom_count": 0.0,
        "remote_binding_acceptor_count": 0.0,
        "soft_donor_count": 0.0,
        "halogen_count": 0.0,
        "nearest_heteroatom_graph_distance": 99.0,
        "nearest_acceptor_graph_distance": 99.0,
        "nearest_soft_donor_graph_distance": 99.0,
    }
    for other in molecule.GetAtoms():
        if not is_substrate_heteroatom(other):
            continue
        symbol = other.GetSymbol()
        distance = float(distance_matrix[atom.GetIdx(), other.GetIdx()])
        if distance <= 0:
            continue
        counts["nearest_heteroatom_graph_distance"] = min(counts["nearest_heteroatom_graph_distance"], distance)
        is_acceptor = symbol in {"N", "O", "S"} and other.GetFormalCharge() <= 0
        is_soft_donor = symbol in {"S", "P", "Se"}
        is_halogen = symbol in {"F", "Cl", "Br", "I"}
        is_remote_binding_capable = is_binding_capable_heteroatom(other)
        if is_acceptor:
            counts["nearest_acceptor_graph_distance"] = min(counts["nearest_acceptor_graph_distance"], distance)
        if is_soft_donor:
            counts["nearest_soft_donor_graph_distance"] = min(counts["nearest_soft_donor_graph_distance"], distance)
            counts["soft_donor_count"] += 1.0
        if is_halogen:
            counts["halogen_count"] += 1.0
        if distance == 1:
            counts["alpha_heteroatom_count"] += 1.0
            if symbol in {"N", "O", "S"}:
                counts[f"alpha_{symbol}_count"] += 1.0
            if is_halogen:
                counts["alpha_halogen_count"] += 1.0
        elif distance in {2.0, 3.0}:
            counts["beta_gamma_heteroatom_count"] += 1.0
            if is_acceptor:
                counts["beta_gamma_acceptor_count"] += 1.0
        else:
            if is_remote_binding_capable:
                counts["remote_binding_heteroatom_count"] += 1.0
            if is_acceptor and is_remote_binding_capable:
                counts["remote_binding_acceptor_count"] += 1.0
    return counts


def carbonyl_alpha_flag(atom: Any) -> float:
    for neighbor in atom.GetNeighbors():
        if neighbor.GetSymbol() != "C":
            continue
        for bond in neighbor.GetBonds():
            other = bond.GetOtherAtom(neighbor)
            if other.GetSymbol() == "O" and bond.GetBondTypeAsDouble() == 2.0:
                return 1.0
    return 0.0


def heteroaryl_adjacent_flag(atom: Any) -> float:
    molecule = atom.GetOwningMol()
    ring_info = molecule.GetRingInfo()
    for neighbor in atom.GetNeighbors():
        if not neighbor.GetIsAromatic():
            continue
        for ring in ring_info.AtomRings():
            if neighbor.GetIdx() not in ring:
                continue
            if any(is_substrate_heteroatom(molecule.GetAtomWithIdx(index)) for index in ring):
                return 1.0
    return 0.0


def site_type_for_rule(record: dict[str, Any], site: dict[str, Any]) -> str:
    reported_site = record["reaction_center"]["reported_reactive_site"]
    if site["atom_map_id"] == reported_site["atom_map_id"]:
        return reported_site.get("site_type") or site.get("site_type") or "unknown"
    return site.get("site_type") or "unknown"


def stage3a_alt_site_rule(record: dict[str, Any], molecule: Any, site: dict[str, Any]) -> dict[str, Any]:
    atom = atom_by_map_id(molecule, site["atom_map_id"])
    site_type = site_type_for_rule(record, site)
    counts = hetero_role_counts_by_distance(molecule, atom)
    carbonyl_alpha = carbonyl_alpha_flag(atom)
    heteroaryl_adjacent = heteroaryl_adjacent_flag(atom)
    is_reported = site["atom_map_id"] == record["reaction_center"]["reported_reactive_site"]["atom_map_id"]
    is_noncanonical_site = site_type not in {"benzylic", "aryl"}
    alpha_soft_donor = 1.0 if counts["alpha_S_count"] > 0 or counts["nearest_soft_donor_graph_distance"] == 1.0 else 0.0
    alpha_hetero = 1.0 if counts["alpha_heteroatom_count"] > 0 else 0.0
    beta_gamma_hetero = 1.0 if counts["beta_gamma_heteroatom_count"] > 0 else 0.0
    remote_binding = 1.0 if counts["remote_binding_heteroatom_count"] > 0 else 0.0
    electronic_score = (
        3.0 * alpha_soft_donor
        + 2.0 * alpha_hetero
        + 2.0 * carbonyl_alpha
        + 1.25 * heteroaryl_adjacent
        + 0.5 * counts["beta_gamma_heteroatom_count"]
    )
    binding_score = (
        1.5 * alpha_soft_donor
        + 1.0 * beta_gamma_hetero
        + 0.5 * remote_binding
        + 0.5 * counts["remote_binding_acceptor_count"]
        + 0.25 * counts["halogen_count"]
    )
    mechanism_risk_score = (
        electronic_score
        + binding_score
        + 1.0 * float(is_noncanonical_site)
        + 1.0 * float(site_type in {"thioether_benzylic", "carbonyl_alpha", "heteroaryl_adjacent"})
    )
    return {
        "candidate_site_id": site["site_id"],
        "candidate_atom_map_id": site["atom_map_id"],
        "candidate_site_type": site_type,
        "is_reported_reactive_site": is_reported,
        "is_noncanonical_site": is_noncanonical_site,
        "alpha_soft_donor_site": alpha_soft_donor,
        "alpha_heteroatom_site": alpha_hetero,
        "beta_gamma_heteroatom_site": beta_gamma_hetero,
        "carbonyl_alpha_site": carbonyl_alpha,
        "heteroaryl_adjacent_site": heteroaryl_adjacent,
        "remote_binding_heteroatom_available": remote_binding,
        "electronic_site_score": electronic_score,
        "binding_site_score": binding_score,
        "mechanism_risk_score": mechanism_risk_score,
        **counts,
    }


def aggregate_stage3a_alt_rules(site_rules: list[dict[str, Any]]) -> dict[str, float]:
    reported = [site for site in site_rules if site["is_reported_reactive_site"]]
    if len(reported) != 1:
        raise ValueError("Expected exactly one reported site rule row")
    reported_site = reported[0]
    competitors = [site for site in site_rules if not site["is_reported_reactive_site"]]
    aggregates: dict[str, float] = {
        "candidate_site_count": float(len(site_rules)),
        "mechanism_risk_site_count": float(sum(site["mechanism_risk_score"] > 0 for site in site_rules)),
        "heteroactivated_site_count": float(sum(site["alpha_heteroatom_site"] or site["beta_gamma_heteroatom_site"] for site in site_rules)),
        "reported_is_noncanonical_site": float(reported_site["is_noncanonical_site"]),
        "reported_alpha_soft_donor_site": float(reported_site["alpha_soft_donor_site"]),
        "reported_alpha_heteroatom_site": float(reported_site["alpha_heteroatom_site"]),
        "reported_beta_gamma_heteroatom_site": float(reported_site["beta_gamma_heteroatom_site"]),
        "reported_carbonyl_alpha_site": float(reported_site["carbonyl_alpha_site"]),
        "reported_heteroaryl_adjacent_site": float(reported_site["heteroaryl_adjacent_site"]),
        "reported_remote_binding_heteroatom_available": float(reported_site["remote_binding_heteroatom_available"]),
        "reported_nearest_heteroatom_graph_distance": float(reported_site["nearest_heteroatom_graph_distance"]),
        "reported_nearest_acceptor_graph_distance": float(reported_site["nearest_acceptor_graph_distance"]),
        "reported_electronic_site_score": float(reported_site["electronic_site_score"]),
        "reported_binding_site_score": float(reported_site["binding_site_score"]),
        "reported_mechanism_risk_score": float(reported_site["mechanism_risk_score"]),
    }
    for score_name in ["electronic_site_score", "binding_site_score", "mechanism_risk_score"]:
        competitor_values = [float(site[score_name]) for site in competitors] or [0.0]
        max_competitor = max(competitor_values)
        aggregates[f"max_competitor_{score_name}"] = max_competitor
        aggregates[f"reported_minus_max_competitor_{score_name}"] = float(reported_site[score_name]) - max_competitor
    return aggregates


def stage3a_alt_rule_rows(records_path: Path) -> list[dict[str, Any]]:
    rows = []
    for record in read_jsonl(records_path):
        if record["curation_status"] != "feature_ready" or not stage2_elastic_net.is_number(record["outcome"].get("ee_percent")):
            continue
        molecule = molecule_from_record(record)
        site_rules = [
            stage3a_alt_site_rule(record, molecule, site)
            for site in record["reaction_center"]["candidate_sites"]
        ]
        rows.append(
            {
                "schema_version": "stage3a-alt-hetero-site-rules-v1",
                "substrate_id": record["substrate_id"],
                "reaction_id": record["reaction_id"],
                "feature_status": "computed_from_mapped_substrate_graph",
                "feature_blocks": {
                    "stage3a_alt_hetero_site_competition": aggregate_stage3a_alt_rules(site_rules),
                },
                "site_rules": site_rules,
                "provenance": {
                    "records_path": display_path(records_path),
                    "candidate_site_policy": "all_stage2_candidate_haa_sites",
                    "pose_policy": "graph_only_no_pose_or_xtb_features",
                },
            }
        )
    return rows


def write_stage3a_alt_rules(records_path: Path, output_path: Path) -> dict[str, Any]:
    rows = stage3a_alt_rule_rows(records_path)
    write_jsonl(output_path, rows)
    return {
        "schema_version": "stage3a-alt-hetero-site-rules-report-v1",
        "selected_substrate_count": len(rows),
        "site_rule_count": sum(len(row["site_rules"]) for row in rows),
        "output_path": display_path(output_path),
        "feature_policy": "graph_only_chemically_signed_reported_vs_competitor_heteroatom_site_rules",
    }


def augment_rows_with_stage3a_alt(rows: list[dict[str, Any]], rules_path: Path) -> list[dict[str, Any]]:
    rules_by_substrate = {row["substrate_id"]: row for row in read_jsonl(rules_path)}
    for row in rows:
        substrate_id = row["substrate_id"]
        feature_block = rules_by_substrate[substrate_id]["feature_blocks"]["stage3a_alt_hetero_site_competition"]
        stage2_elastic_net.add_numeric_features(row["features"], "stage3a_alt_hetero_site", feature_block)
    return rows


def augment_rows_with_stage3a(
    rows: list[dict[str, Any]],
    selection_path: Path,
    reference_summary_path: Path,
    shell_features_path: Path,
) -> list[dict[str, Any]]:
    selection_features = aggregate_numeric_feature_block(read_jsonl(selection_path), "stage1_v2_pose_selection")
    reference_features = reported_reference_features(reference_summary_path)
    shell_features = reported_shell_features(reference_summary_path, shell_features_path)
    for row in rows:
        substrate_id = row["substrate_id"]
        stage2_elastic_net.add_numeric_features(row["features"], "stage1_v2_selection", selection_features[substrate_id])
        stage2_elastic_net.add_numeric_features(row["features"], "stage3a_reference", reference_features[substrate_id])
        stage2_elastic_net.add_numeric_features(row["features"], "stage3a_shell", shell_features[substrate_id])
    return rows


def run_seed_elastic_net(
    rows: list[dict[str, Any]],
    matrix_path: Path,
    report_path: Path,
    predictions_path: Path,
    feature_policy: str,
) -> dict[str, Any]:
    feature_names = stage2_elastic_net.write_matrix(matrix_path, rows)
    x, y = stage2_elastic_net.matrix_arrays(rows, feature_names)
    active_feature_mask = x.std(axis=0) > 0
    x_model = x[:, active_feature_mask]
    model_feature_names = [name for name, active in zip(feature_names, active_feature_mask, strict=True) if active]
    selected_params = stage2_elastic_net.select_hyperparameters(x_model, y)
    predictions = stage2_elastic_net.leave_one_out_predictions(
        x_model,
        y,
        alpha=selected_params["alpha"],
        l1_ratio=selected_params["l1_ratio"],
    )
    mean_predictions = numpy.array([
        y[[index for index in range(len(y)) if index != holdout_index]].mean()
        for holdout_index in range(len(y))
    ])
    model = stage2_elastic_net.ElasticNetModel(
        alpha=selected_params["alpha"],
        l1_ratio=selected_params["l1_ratio"],
    ).fit(x_model, y)
    residuals = predictions - y
    mean_residuals = mean_predictions - y

    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    with predictions_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "fold_index",
                "substrate_id",
                "family_id",
                "ee_percent",
                "elastic_net_loo_prediction",
                "elastic_net_residual",
                "elastic_net_abs_error",
                "mean_loo_prediction",
                "mean_abs_error",
            ],
        )
        writer.writeheader()
        for index, row in enumerate(rows):
            writer.writerow(
                {
                    "fold_index": index + 1,
                    "substrate_id": row["substrate_id"],
                    "family_id": row["family_id"],
                    "ee_percent": y[index],
                    "elastic_net_loo_prediction": predictions[index],
                    "elastic_net_residual": residuals[index],
                    "elastic_net_abs_error": abs(residuals[index]),
                    "mean_loo_prediction": mean_predictions[index],
                    "mean_abs_error": abs(mean_residuals[index]),
                }
            )

    report = {
        "schema_version": "stage3a-seed-ee-elastic-net-report-v1",
        "status": "seed_pilot_model_comparison_not_predictive_claim",
        "target": "ee_percent",
        "record_count": len(rows),
        "feature_count": len(feature_names),
        "nonconstant_feature_count": len(model_feature_names),
        "feature_policy": feature_policy,
        "matrix_path": display_path(matrix_path),
        "report_path": display_path(report_path),
        "predictions_path": display_path(predictions_path),
        "validation": "leave_one_out_cv_with_seed_level_hyperparameter_selection",
        "elastic_net": {
            "implementation": "local_coordinate_descent",
            "selected_hyperparameters": {
                "alpha": selected_params["alpha"],
                "l1_ratio": selected_params["l1_ratio"],
                "selection_loo_mae": selected_params["mae"],
            },
            "loo_metrics": stage2_elastic_net.metrics(y, predictions),
            "residual_summary": stage2_elastic_net.residual_distribution_summary(residuals),
            "calibration_summary": stage2_elastic_net.calibration_summary(y, predictions),
            "bayesian_bootstrap_metric_intervals": stage2_elastic_net.bayesian_bootstrap_metric_intervals(y, predictions),
            "nonzero_coefficient_count": int(numpy.sum(numpy.abs(model.coefficients) > 1e-12)),
            "top_coefficients": stage2_elastic_net.top_coefficients(model, model_feature_names),
        },
        "mean_baseline": {
            "loo_metrics": stage2_elastic_net.metrics(y, mean_predictions),
            "residual_summary": stage2_elastic_net.residual_distribution_summary(mean_residuals),
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def read_prediction_rows(path: Path) -> dict[str, dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return {row["substrate_id"]: row for row in csv.DictReader(stream)}


def write_prediction_comparison(
    reports: list[dict[str, Any]],
    output_path: Path,
) -> dict[str, Any]:
    prediction_tables = {}
    for item in reports:
        predictions_path = Path(item["report"]["predictions_path"])
        if not predictions_path.is_absolute():
            predictions_path = ROOT / predictions_path
        prediction_tables[item["run_id"]] = read_prediction_rows(predictions_path)
    run_ids = [item["run_id"] for item in reports]
    substrate_ids = sorted(prediction_tables[run_ids[0]])
    fieldnames = ["substrate_id", "family_id", "ee_percent"]
    for run_id in run_ids:
        fieldnames.extend([f"{run_id}_prediction", f"{run_id}_abs_error"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for substrate_id in substrate_ids:
            base_row = prediction_tables[run_ids[0]][substrate_id]
            row = {
                "substrate_id": substrate_id,
                "family_id": base_row["family_id"],
                "ee_percent": base_row["ee_percent"],
            }
            for run_id in run_ids:
                prediction_row = prediction_tables[run_id][substrate_id]
                row[f"{run_id}_prediction"] = prediction_row["elastic_net_loo_prediction"]
                row[f"{run_id}_abs_error"] = prediction_row["elastic_net_abs_error"]
            writer.writerow(row)
    return {
        "schema_version": "stage3a-alt-prediction-comparison-report-v1",
        "output_path": display_path(output_path),
        "run_ids": run_ids,
        "record_count": len(substrate_ids),
    }


def build_rows(records: Path, tier1: Path, pose_summary: Path, pose_interaction: Path) -> list[dict[str, Any]]:
    return stage2_elastic_net.build_feature_rows(records, tier1, pose_summary, pose_interaction)


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    filter_report = write_v2_pose_interaction(args.stage2_pose_interaction, args.v2_selection, args.v2_pose_interaction)
    v2_summary_report = write_v2_pose_summary(args.records, args.pose_summary, args.v2_selection, args.v2_pose_summary)
    stage3a_alt_report = write_stage3a_alt_rules(args.records, args.stage3a_alt_rules)
    runs = [
        {
            "run_id": "stage2_seed_baseline",
            "feature_policy": "stage2_seed_tier1_pose_summary_all_200_stage1_pose_interactions",
            "rows": build_rows(args.records, args.tier1, args.pose_summary, args.stage2_pose_interaction),
        },
        {
            "run_id": "stage2_v2_selected_pose",
            "feature_policy": "stage2_v2_seed_tier1_stage1_v2_pose_summary_top_50_stage1_v2_pose_interactions",
            "rows": build_rows(args.records, args.tier1, args.v2_pose_summary, args.v2_pose_interaction),
        },
        {
            "run_id": "stage3a_alt_hetero_site_competition",
            "feature_policy": "stage2_seed_baseline_plus_graph_only_heteroatom_reported_vs_competitor_site_rules",
            "rows": augment_rows_with_stage3a_alt(
                build_rows(args.records, args.tier1, args.pose_summary, args.stage2_pose_interaction),
                args.stage3a_alt_rules,
            ),
        },
        {
            "run_id": "stage3a_reference_shell",
            "feature_policy": "stage2_v2_selected_pose_plus_stage3a_xtb_reference_and_reported_site_shell_features",
            "rows": augment_rows_with_stage3a(
                build_rows(args.records, args.tier1, args.v2_pose_summary, args.v2_pose_interaction),
                args.v2_selection,
                args.reference_summary,
                args.shell_features,
            ),
        },
    ]

    reports = []
    for run in runs:
        run_id = run["run_id"]
        reports.append(
            {
                "run_id": run_id,
                "report": run_seed_elastic_net(
                    run["rows"],
                    args.output_dir / f"{run_id}-matrix.csv",
                    args.output_dir / f"{run_id}-report.json",
                    args.output_dir / f"{run_id}-predictions.csv",
                    run["feature_policy"],
                ),
            }
        )

    baseline_mae = reports[0]["report"]["elastic_net"]["loo_metrics"]["mae"]
    comparison_rows = []
    for item in reports:
        report = item["report"]
        metrics = report["elastic_net"]["loo_metrics"]
        comparison_rows.append(
            {
                "run_id": item["run_id"],
                "feature_policy": report["feature_policy"],
                "record_count": report["record_count"],
                "feature_count": report["feature_count"],
                "nonconstant_feature_count": report["nonconstant_feature_count"],
                "elastic_net_mae": metrics["mae"],
                "elastic_net_rmse": metrics["rmse"],
                "elastic_net_r2": metrics["r2"],
                "mae_delta_vs_stage2": metrics["mae"] - baseline_mae,
                "selected_alpha": report["elastic_net"]["selected_hyperparameters"]["alpha"],
                "selected_l1_ratio": report["elastic_net"]["selected_hyperparameters"]["l1_ratio"],
            }
        )

    args.comparison_table.parent.mkdir(parents=True, exist_ok=True)
    with args.comparison_table.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparison_rows[0]))
        writer.writeheader()
        writer.writerows(comparison_rows)

    prediction_comparison_report = write_prediction_comparison(reports, args.prediction_comparison)

    comparison_report = {
        "schema_version": "stage3a-seed-model-comparison-v1",
        "status": "seed_pilot_model_comparison_not_predictive_claim",
        "filter_report": filter_report,
        "stage2_v2_pose_summary_report": v2_summary_report,
        "stage3a_alt_hetero_site_rules_report": stage3a_alt_report,
        "comparison_table_path": display_path(args.comparison_table),
        "prediction_comparison_report": prediction_comparison_report,
        "comparison_rows": comparison_rows,
        "caveats": [
            "Stage 3a coverage is currently limited to the 12 seed substrates with constrained xTB references.",
            "Stage 2-v2 is the fair v2 comparator: Tier 1 plus pose-summary and pose-interaction features recomputed from the Stage 1-v2 selected top-50 pose set.",
            "Stage 3a-alt is Stage 2 seed baseline plus graph-only, chemically signed, reported-vs-competitor heteroatom site-competition features.",
            "Stage 3a is Stage 2-v2 plus xTB reference geometry, Stage 1-v2 selection-score aggregates, and reported-site local shell features.",
            "The Stage 3a reported-site shell block uses the manually curated product-forming site and is not a label-free full-panel feature yet.",
            "Stage 3b BDE features are not included in this comparison.",
        ],
    }
    args.comparison_report.write_text(json.dumps(comparison_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return comparison_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--tier1", type=Path, default=DEFAULT_TIER1)
    parser.add_argument("--pose-summary", type=Path, default=DEFAULT_POSE_SUMMARY)
    parser.add_argument("--stage2-pose-interaction", type=Path, default=DEFAULT_STAGE2_POSE_INTERACTION)
    parser.add_argument("--v2-selection", type=Path, default=DEFAULT_V2_SELECTION)
    parser.add_argument("--v2-pose-summary", type=Path, default=DEFAULT_V2_POSE_SUMMARY)
    parser.add_argument("--v2-pose-interaction", type=Path, default=DEFAULT_V2_POSE_INTERACTION)
    parser.add_argument("--reference-summary", type=Path, default=DEFAULT_REFERENCE_SUMMARY)
    parser.add_argument("--shell-features", type=Path, default=DEFAULT_SHELL_FEATURES)
    parser.add_argument("--stage3a-alt-rules", type=Path, default=DEFAULT_STAGE3A_ALT_RULES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--comparison-report", type=Path, default=DEFAULT_COMPARISON_REPORT)
    parser.add_argument("--comparison-table", type=Path, default=DEFAULT_COMPARISON_TABLE)
    parser.add_argument("--prediction-comparison", type=Path, default=DEFAULT_PREDICTION_COMPARISON)
    return parser.parse_args()


def main() -> None:
    report = run_comparison(parse_args())
    print(json.dumps(report["comparison_rows"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

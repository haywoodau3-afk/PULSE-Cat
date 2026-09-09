#!/usr/bin/env python3
"""Bootstrap and validate the Stage 3 mechanism-enriched feature contract."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/jacs_2025"
STAGE2_DIR = DATA_DIR / "stage2"
STAGE3_DIR = DATA_DIR / "stage3"
DEFAULT_STAGE2_RECORDS = STAGE2_DIR / "curated-reaction-records.jsonl"
DEFAULT_STAGE2_FEATURE_MANIFEST = STAGE2_DIR / "feature-manifest.json"
DEFAULT_STAGE3_CONTRACT = STAGE3_DIR / "stage3-contract.json"
DEFAULT_STAGE3_FEATURE_MANIFEST = STAGE3_DIR / "stage3-feature-manifest.json"
DEFAULT_STAGE3_ENVIRONMENT = STAGE3_DIR / "stage3-environment.json"

CHEM_ENV = ROOT / ".chem-env"
PYTHON_ENV = ROOT / ".venv"
MAMBA_ROOT_PREFIX = ROOT / ".mamba-root"

STAGE3_SUBSTAGE_IDS = {"stage3a_nci_guided_pose_v2", "stage3b_intrinsic_bde"}
SHELL_IDS = ["0_3_angstrom", "3_4_angstrom", "4_5_angstrom", "5_6_angstrom", "6_8_angstrom"]
SHELL_CENTERS = ["nitrene_center", "candidate_c_h_haa_center", "reactive_approach_midpoint"]
NCI_RULE_TIERS = {"consensus", "motif_specific"}
NCI_INTERACTION_CLASSES = {
    "hydrogen_bond",
    "aryl_pi_contact",
    "c_h_pi_contact",
    "agostic_like_c_h_contact",
    "close_ligand_substrate_atom_pair",
    "donor_acceptor_proximity",
    "reactive_c_h_approach_geometry",
}
COMPOSITE_SCORE_COMPONENTS = {
    "xtb_relative_energy",
    "nci_rule_satisfaction_score",
    "reactive_geometry_score",
    "clash_penalty",
    "core_deviation_penalty",
}
MODEL_FEATURE_SETS = {
    "structure_only",
    "structure_plus_v1_pose",
    "structure_plus_v2_nci_pose",
    "structure_plus_v2_shell_features",
    "structure_plus_bde",
    "structure_plus_v2_nci_pose_plus_bde",
    "pose_score_only",
    "pose_geometry_rich",
}


class ContractError(Exception):
    """Raised when a Stage 3 contract artifact is internally inconsistent."""


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise ContractError(f"{display_path(path)} already exists; pass --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_environment_manifest() -> dict[str, Any]:
    return {
        "schema_version": "stage3-environment-v1",
        "environment_policy": "separate_python_ml_env_and_command_line_chemistry_env",
        "python_ml_environment": {
            "env_id": "repo_venv",
            "path": str(PYTHON_ENV),
            "python_executable": str(PYTHON_ENV / "bin/python"),
            "required_imports": ["rdkit", "sklearn", "scipy", "lightgbm"],
            "usage": [
                "feature extraction",
                "artifact validation",
                "model matrix generation",
                "Stage 2 to Stage 3 model-delta reports",
            ],
        },
        "chemistry_environment": {
            "env_id": "stage3_chem_env",
            "path": str(CHEM_ENV),
            "micromamba": str(Path("/opt/homebrew/bin/micromamba")),
            "mamba_root_prefix": str(MAMBA_ROOT_PREFIX),
            "tools": {
                "xtb": {
                    "path": str(CHEM_ENV / "bin/xtb"),
                    "verified_version": "6.7.1",
                    "stage3_roles": [
                        "constrained GFN2-xTB reference-complex optimization",
                        "intrinsic C-H BDE calculation",
                    ],
                },
                "crest": {
                    "path": str(CHEM_ENV / "bin/crest"),
                    "verified_version": "3.0.2",
                    "stage3_roles": ["optional conformer and motif checks"],
                },
                "obabel": {
                    "path": str(CHEM_ENV / "bin/obabel"),
                    "verified_version": "3.1.0",
                    "stage3_roles": ["geometry and format conversion"],
                },
            },
        },
    }


def default_stage3_contract() -> dict[str, Any]:
    return {
        "schema_version": "stage3-contract-v1",
        "stage_id": "stage3",
        "stage_name": "Data-Efficiency Study",
        "purpose": (
            "Test whether mechanism-enriched synthetic 3D scaffold analysis improves ee and yield "
            "prediction beyond the Stage 2 baseline."
        ),
        "substrate_scope": {
            "source_records_path": "data/jacs_2025/stage2/curated-reaction-records.jsonl",
            "expected_record_count": 41,
            "candidate_site_policy": "all_candidate_haa_sites_for_all_substrates",
        },
        "substages": [
            {
                "substage_id": "stage3a_nci_guided_pose_v2",
                "label": "Stage 3a: NCI-Guided Pose v2",
                "status": "contract_declared",
                "reference_optimization": {
                    "unit": "per_substrate_optimized_reference_complex_ensemble",
                    "method": "GFN2-xTB",
                    "solvent_model": "ALPB ether where practical",
                    "starting_pose_count_range": [20, 50],
                    "optimized_reference_count_range": [3, 5],
                    "default_reference_motif_count": 3,
                    "dft_required_for_gate": False,
                },
                "scaffold_constraint_policy": {
                    "frozen_atom_groups": [
                        "Fe",
                        "porphyrin_macrocycle",
                        "axial_chloride_when_present",
                        "nitrene_N_Fe_N_anchor_geometry",
                        "core_atoms_required_to_preserve_selectivity_intermediate",
                    ],
                    "restrained_atom_groups": ["chiral_ligand_or_scaffold_substituents_forming_substrate_pocket"],
                    "mobile_atom_groups": ["substrate_atoms"],
                    "required_provenance": [
                        "frozen_atom_set",
                        "restrained_atom_set",
                        "restraint_force_constants",
                        "xtb_method",
                        "solvent_model",
                        "starting_pose_id",
                        "optimization_status",
                        "final_relative_energy",
                    ],
                },
                "nci_rule_contract": {
                    "rule_tiers": sorted(NCI_RULE_TIERS),
                    "interaction_classes": sorted(NCI_INTERACTION_CLASSES),
                    "rule_packet_unit": "motif",
                    "rule_packet_policy": "generate_poses_per_motif_then_merge_with_motif_provenance",
                },
                "pose_generation": {
                    "candidate_pose_count_per_substrate": 5000,
                    "retained_pose_count_per_substrate": 50,
                    "retention_policy": "hybrid_motif_retention",
                    "max_retained_per_viable_motif": 10,
                    "underfilled_flag": "v2_pose_underfilled",
                    "validity_requirements": [
                        "connectivity_preserved",
                        "clash_screen_passed",
                        "frozen_core_preserved",
                        "nci_rule_satisfaction_recorded",
                    ],
                },
                "composite_pose_score": {
                    "score_id": "stage3a_pose_centered_composite_score_v1",
                    "components": sorted(COMPOSITE_SCORE_COMPONENTS),
                    "raw_component_storage_required": True,
                    "motif_diversity_handled_by_retention_policy": True,
                    "ranking_policy": [
                        "filter_validity_and_core_constraints",
                        "apply_motif_retention_quotas",
                        "rank_remaining_candidates_by_composite_pose_score",
                    ],
                },
                "local_3d_shell_contract": {
                    "candidate_site_term": "candidate_c_h_haa_center",
                    "site_scope": "every_candidate_haa_site",
                    "centers": SHELL_CENTERS,
                    "shells": [
                        {"shell_id": "0_3_angstrom", "lower_angstrom": 0.0, "upper_angstrom": 3.0},
                        {"shell_id": "3_4_angstrom", "lower_angstrom": 3.0, "upper_angstrom": 4.0},
                        {"shell_id": "4_5_angstrom", "lower_angstrom": 4.0, "upper_angstrom": 5.0},
                        {"shell_id": "5_6_angstrom", "lower_angstrom": 5.0, "upper_angstrom": 6.0},
                        {"shell_id": "6_8_angstrom", "lower_angstrom": 6.0, "upper_angstrom": 8.0},
                    ],
                    "feature_families": [
                        "atom_counts_by_element",
                        "atom_counts_by_ownership",
                        "heteroatom_counts",
                        "aromatic_atom_counts",
                        "nearest_atom_identity_and_distance",
                        "donor_acceptor_contact_counts",
                        "aryl_centroid_proximity",
                        "shell_distance_quantiles",
                        "partial_charge_summaries_if_available",
                        "c_h_bond_orientation_relative_to_fe_n_and_porphyrin_plane",
                    ],
                },
            },
            {
                "substage_id": "stage3b_intrinsic_bde",
                "label": "Stage 3b: Intrinsic BDE Feature Set",
                "status": "contract_declared",
                "site_scope": "all_candidate_haa_sites_on_all_41_substrates",
                "method": {
                    "definition": "substrate radical + H atom - substrate",
                    "substrate_state": "isolated_closed_shell_substrate",
                    "radical_state": "corresponding_doublet_carbon_radical",
                    "level": "GFN2-xTB",
                    "solvent_model": "ALPB ether where practical",
                    "hydrogen_reference_policy": "one_consistent_hydrogen_atom_reference",
                },
                "feature_contract": {
                    "granularity": "candidate_site",
                    "features": [
                        "absolute_intrinsic_c_h_bde",
                        "within_substrate_bde_rank",
                        "bde_competition_gap",
                        "candidate_site_identity",
                        "atom_map_provenance",
                        "equivalence_class_provenance",
                        "method_and_solvent_provenance",
                        "substrate_optimization_status",
                        "radical_optimization_status",
                        "calibration_status",
                    ],
                    "initial_calibration_status": "uncalibrated_xtb",
                    "higher_level_calibration_required_for_first_model_delta": False,
                },
            },
        ],
        "model_delta_contract": {
            "primary_validation": "family_held_out",
            "diagnostic_validation": "target_holdout",
            "feature_sets": sorted(MODEL_FEATURE_SETS),
            "required_deltas": [
                "stage2_baseline_to_stage3a",
                "stage3a_to_stage3a_plus_stage3b",
                "stage2_baseline_to_stage3a_plus_stage3b",
            ],
            "metrics": ["MAE", "RMSE", "R2_where_meaningful", "prediction_interval_calibration", "residual_distribution"],
            "claim_requirements": [
                "survives_family_held_out_validation",
                "has_chemically_meaningful_residual_interpretation",
                "preserves_or_improves_uncertainty_calibration",
                "avoids_product_known_only_feature_leakage",
                "has_interpretable_feature_provenance",
            ],
        },
        "implementation_slices": [
            "stage3a_contract_and_pilot",
            "stage3a_full_scope_generation",
            "stage3a_model_delta",
            "stage3b_bde_pipeline",
            "stage3a_plus_stage3b_model_delta",
        ],
        "non_goals": [
            "DFT-quality complex energetics",
            "calibrated BDE accuracy before calibration milestone",
            "UFF, xTB, or composite pose scores as reaction barriers",
            "poses as independently labelled experimental training examples",
            "universal catalyst-scope model",
        ],
    }


def default_feature_manifest() -> dict[str, Any]:
    return {
        "schema_version": "stage3-feature-manifest-v1",
        "feature_policy": "mechanism_enriched_candidate_site_and_pose_features_with_model_delta_reporting",
        "feature_blocks": [
            {
                "block_id": "stage3a_xtb_reference_optimization",
                "status": "declared_not_yet_computed",
                "granularity": "substrate_reference_motif",
                "expected_feature_count_range": [10, 50],
                "dependencies": ["Stage 1 v1 retained poses", "xTB 6.7.1", "Stage 3 scaffold constraint policy"],
                "feature_families": ["xtb_relative_energy", "optimization_status", "motif_identity", "scaffold_deviation"],
                "output_path": "data/jacs_2025/stage3/reference-optimizations/xtb-reference-complexes.jsonl",
            },
            {
                "block_id": "stage3a_nci_rule_packets",
                "status": "declared_not_yet_computed",
                "granularity": "substrate_motif",
                "expected_feature_count_range": [20, 200],
                "dependencies": ["stage3a_xtb_reference_optimization"],
                "feature_families": sorted(NCI_INTERACTION_CLASSES),
                "output_path": "data/jacs_2025/stage3/nci-rules/nci-rule-packets.jsonl",
            },
            {
                "block_id": "stage3a_v2_pose_interaction",
                "status": "declared_not_yet_computed",
                "granularity": "pose_and_candidate_site",
                "expected_feature_count_range": [50, 300],
                "dependencies": ["stage3a_nci_rule_packets", "Stage 1/2 candidate-site atom maps"],
                "feature_families": [
                    "composite_pose_score_components",
                    "nci_rule_satisfaction",
                    "reactive_approach_geometry",
                    "motif_provenance",
                    "core_deviation",
                ],
                "output_path": "data/jacs_2025/stage3/features/v2-pose-interaction.jsonl",
            },
            {
                "block_id": "stage3a_local_3d_shell_features",
                "status": "declared_not_yet_computed",
                "granularity": "pose_candidate_site_shell",
                "expected_feature_count_range": [100, 500],
                "dependencies": ["stage3a_v2_pose_interaction", "retained v2 XYZ geometry"],
                "feature_families": [
                    "radial_shell_atom_counts",
                    "ownership_counts",
                    "nearest_atom_distances",
                    "donor_acceptor_counts",
                    "aryl_centroid_proximity",
                    "c_h_orientation_features",
                ],
                "parameters": {"shell_ids": SHELL_IDS, "centers": SHELL_CENTERS},
                "output_path": "data/jacs_2025/stage3/features/local-3d-shell-features.jsonl",
            },
            {
                "block_id": "stage3b_bde_features",
                "status": "declared_not_yet_computed",
                "granularity": "candidate_site",
                "expected_feature_count_range": [5, 30],
                "dependencies": ["Stage 2 candidate_site_features", "xTB 6.7.1", "consistent hydrogen atom reference"],
                "feature_families": [
                    "absolute_intrinsic_c_h_bde",
                    "within_substrate_bde_rank",
                    "bde_competition_gap",
                    "calibration_status",
                    "optimization_status",
                ],
                "parameters": {"initial_calibration_status": "uncalibrated_xtb"},
                "output_path": "data/jacs_2025/stage3/features/bde.jsonl",
            },
            {
                "block_id": "stage3_model_delta_reports",
                "status": "declared_not_yet_computed",
                "granularity": "model_report",
                "expected_feature_count_range": [1, 100],
                "dependencies": ["Stage 2 benchmark artifacts", "Stage 3a features", "Stage 3b BDE features"],
                "feature_families": ["stage2_to_stage3a_delta", "stage3a_to_stage3a_plus_stage3b_delta", "family_held_out_residuals"],
                "output_path": "data/jacs_2025/stage3/reports/stage3-model-delta-report.json",
            },
        ],
        "reporting_requirements": [
            "stage2_baseline_to_stage3a_delta",
            "stage3a_to_stage3a_plus_stage3b_delta",
            "family_held_out_primary_validation",
            "target_holdout_diagnostic_validation",
            "feature_provenance",
            "BDE_calibration_status",
        ],
    }


def bootstrap(contract_path: Path, manifest_path: Path, environment_path: Path, force: bool) -> dict[str, str]:
    write_json(contract_path, default_stage3_contract(), force)
    write_json(manifest_path, default_feature_manifest(), force)
    write_json(environment_path, default_environment_manifest(), force)
    return {
        "contract_path": display_path(contract_path),
        "manifest_path": display_path(manifest_path),
        "environment_path": display_path(environment_path),
    }


def validate_environment(environment: dict[str, Any], check_tools: bool) -> None:
    require(environment.get("schema_version") == "stage3-environment-v1", "Invalid Stage 3 environment schema")
    python_env = environment.get("python_ml_environment", {})
    chem_env = environment.get("chemistry_environment", {})
    require(Path(python_env.get("python_executable", "")).exists(), "Python env executable is missing")
    require(Path(chem_env.get("path", "")).exists(), "Chemistry env path is missing")
    require(Path(chem_env.get("micromamba", "")).exists(), "micromamba executable is missing")
    tools = chem_env.get("tools", {})
    for tool_name in ["xtb", "crest", "obabel"]:
        tool = tools.get(tool_name, {})
        tool_path = Path(tool.get("path", ""))
        require(tool_path.exists(), f"{tool_name}: executable is missing at {tool_path}")
        require(os.access(tool_path, os.X_OK), f"{tool_name}: executable is not runnable at {tool_path}")
        require(tool.get("verified_version"), f"{tool_name}: missing verified version")
        if check_tools:
            command = [str(tool_path), "-V"] if tool_name == "obabel" else [str(tool_path), "--version"]
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            require(result.returncode == 0, f"{tool_name}: version command failed: {result.stderr or result.stdout}")


def validate_feature_manifest(manifest: dict[str, Any]) -> None:
    require(manifest.get("schema_version") == "stage3-feature-manifest-v1", "Invalid Stage 3 feature manifest schema")
    blocks = manifest.get("feature_blocks")
    require(isinstance(blocks, list) and blocks, "Stage 3 manifest must define feature blocks")
    by_id = {block.get("block_id"): block for block in blocks if isinstance(block, dict)}
    required_blocks = {
        "stage3a_xtb_reference_optimization",
        "stage3a_nci_rule_packets",
        "stage3a_v2_pose_interaction",
        "stage3a_local_3d_shell_features",
        "stage3b_bde_features",
        "stage3_model_delta_reports",
    }
    require(required_blocks <= set(by_id), "Stage 3 feature manifest is missing required blocks")
    for block_id, block in by_id.items():
        require(block.get("status") in {"declared_not_yet_computed", "implemented", "implemented_partial"}, f"{block_id}: invalid status")
        require(
            block.get("granularity")
            in {"candidate_site", "pose_and_candidate_site", "pose_candidate_site_shell", "substrate_motif", "substrate_reference_motif", "model_report"},
            f"{block_id}: invalid granularity",
        )
        count_range = block.get("expected_feature_count_range")
        require(
            isinstance(count_range, list)
            and len(count_range) == 2
            and all(isinstance(value, int) and value > 0 for value in count_range)
            and count_range[0] <= count_range[1],
            f"{block_id}: invalid expected feature-count range",
        )
        require(isinstance(block.get("dependencies"), list) and block["dependencies"], f"{block_id}: missing dependencies")
        require(isinstance(block.get("feature_families"), list) and block["feature_families"], f"{block_id}: missing feature families")
        require(block.get("output_path", "").startswith("data/jacs_2025/stage3/"), f"{block_id}: output path must live under Stage 3")
    shell_params = by_id["stage3a_local_3d_shell_features"].get("parameters", {})
    require(shell_params.get("shell_ids") == SHELL_IDS, "Local 3D shell parameters must use the agreed shell ids")
    require(shell_params.get("centers") == SHELL_CENTERS, "Local 3D shell parameters must use the agreed centers")
    require(by_id["stage3b_bde_features"].get("parameters", {}).get("initial_calibration_status") == "uncalibrated_xtb", "BDE initial calibration status must be uncalibrated_xtb")
    reporting = set(manifest.get("reporting_requirements", []))
    require(
        {
            "stage2_baseline_to_stage3a_delta",
            "stage3a_to_stage3a_plus_stage3b_delta",
            "family_held_out_primary_validation",
            "BDE_calibration_status",
        }
        <= reporting,
        "Stage 3 manifest is missing model-delta reporting requirements",
    )


def validate_stage3_contract(contract: dict[str, Any], stage2_records: list[dict[str, Any]], stage2_manifest: dict[str, Any]) -> None:
    require(contract.get("schema_version") == "stage3-contract-v1", "Invalid Stage 3 contract schema")
    require(contract.get("stage_id") == "stage3", "Stage contract must identify stage3")
    scope = contract.get("substrate_scope", {})
    require(scope.get("expected_record_count") == 41, "Stage 3 must preserve the all-41 substrate scope")
    require(len(stage2_records) == scope["expected_record_count"], "Stage 2 records do not match Stage 3 expected scope")
    require(scope.get("candidate_site_policy") == "all_candidate_haa_sites_for_all_substrates", "Stage 3 must use all candidate HAA sites")

    stage2_blocks = {block.get("block_id"): block for block in stage2_manifest.get("feature_blocks", [])}
    require(stage2_blocks.get("pose_interaction", {}).get("status") == "implemented", "Stage 3 requires implemented Stage 2 pose_interaction")
    require("bde_features" in stage2_blocks, "Stage 3 requires the deferred Stage 2 BDE block as handoff")

    substages = contract.get("substages")
    require(isinstance(substages, list) and len(substages) == 2, "Stage 3 must define Stage 3a and Stage 3b")
    by_id = {substage.get("substage_id"): substage for substage in substages if isinstance(substage, dict)}
    require(set(by_id) == STAGE3_SUBSTAGE_IDS, "Stage 3 substages must be Stage 3a and Stage 3b")

    stage3a = by_id["stage3a_nci_guided_pose_v2"]
    reference = stage3a.get("reference_optimization", {})
    require(reference.get("method") == "GFN2-xTB", "Stage 3a reference optimization must use GFN2-xTB")
    require(reference.get("dft_required_for_gate") is False, "DFT must not be required for the Stage 3a gate")
    require(reference.get("starting_pose_count_range") == [20, 50], "Stage 3a starting pose range drifted")
    require(reference.get("optimized_reference_count_range") == [3, 5], "Stage 3a reference ensemble range drifted")
    scaffold = stage3a.get("scaffold_constraint_policy", {})
    require(scaffold.get("frozen_atom_groups"), "Stage 3a must define frozen atom groups")
    require(scaffold.get("restrained_atom_groups"), "Stage 3a must define restrained atom groups")
    require(scaffold.get("mobile_atom_groups") == ["substrate_atoms"], "Stage 3a substrate atoms must remain mobile")
    rules = stage3a.get("nci_rule_contract", {})
    require(set(rules.get("rule_tiers", [])) == NCI_RULE_TIERS, "Stage 3a must preserve consensus and motif-specific rule tiers")
    require(set(rules.get("interaction_classes", [])) == NCI_INTERACTION_CLASSES, "Stage 3a NCI interaction classes drifted")
    pose_generation = stage3a.get("pose_generation", {})
    require(pose_generation.get("candidate_pose_count_per_substrate") == 5000, "Stage 3a must generate 5000 v2 candidates per substrate")
    require(pose_generation.get("retained_pose_count_per_substrate") == 50, "Stage 3a must retain 50 final poses per substrate")
    require(pose_generation.get("retention_policy") == "hybrid_motif_retention", "Stage 3a must use hybrid retention")
    score = stage3a.get("composite_pose_score", {})
    require(set(score.get("components", [])) == COMPOSITE_SCORE_COMPONENTS, "Stage 3a composite score components drifted")
    shells = stage3a.get("local_3d_shell_contract", {})
    require(shells.get("candidate_site_term") == "candidate_c_h_haa_center", "Stage 3a must use candidate C-H HAA center")
    require(shells.get("site_scope") == "every_candidate_haa_site", "Stage 3a shell features must cover every candidate site")
    require(shells.get("centers") == SHELL_CENTERS, "Stage 3a shell centers drifted")
    require([shell["shell_id"] for shell in shells.get("shells", [])] == SHELL_IDS, "Stage 3a radial shells drifted")

    stage3b = by_id["stage3b_intrinsic_bde"]
    require(stage3b.get("site_scope") == "all_candidate_haa_sites_on_all_41_substrates", "Stage 3b must cover all candidate sites on all 41 substrates")
    method = stage3b.get("method", {})
    require(method.get("level") == "GFN2-xTB", "Stage 3b BDE level must be GFN2-xTB")
    require(method.get("definition") == "substrate radical + H atom - substrate", "Stage 3b BDE definition drifted")
    bde_features = stage3b.get("feature_contract", {})
    require(bde_features.get("initial_calibration_status") == "uncalibrated_xtb", "Stage 3b must enter first comparison as uncalibrated xTB")
    require(bde_features.get("higher_level_calibration_required_for_first_model_delta") is False, "Stage 3b must not require higher-level calibration before first model delta")

    model_delta = contract.get("model_delta_contract", {})
    require(model_delta.get("primary_validation") == "family_held_out", "Stage 3 primary validation must be family-held-out")
    require(set(model_delta.get("feature_sets", [])) == MODEL_FEATURE_SETS, "Stage 3 model feature-set comparison drifted")
    require(
        {
            "stage2_baseline_to_stage3a",
            "stage3a_to_stage3a_plus_stage3b",
            "stage2_baseline_to_stage3a_plus_stage3b",
        }
        <= set(model_delta.get("required_deltas", [])),
        "Stage 3 is missing required model deltas",
    )


def validate_contract(
    contract_path: Path,
    manifest_path: Path,
    environment_path: Path,
    stage2_records_path: Path,
    stage2_manifest_path: Path,
    check_tools: bool,
) -> dict[str, Any]:
    contract = read_json(contract_path)
    manifest = read_json(manifest_path)
    environment = read_json(environment_path)
    stage2_records = read_jsonl(stage2_records_path)
    stage2_manifest = read_json(stage2_manifest_path)

    validate_stage3_contract(contract, stage2_records, stage2_manifest)
    validate_feature_manifest(manifest)
    validate_environment(environment, check_tools)

    feature_blocks = manifest["feature_blocks"]
    substages = contract["substages"]
    tools = environment["chemistry_environment"]["tools"]
    return {
        "contract_path": display_path(contract_path),
        "manifest_path": display_path(manifest_path),
        "environment_path": display_path(environment_path),
        "stage2_record_count": len(stage2_records),
        "substage_count": len(substages),
        "feature_block_count": len(feature_blocks),
        "local_3d_shell_count": len(SHELL_IDS),
        "shell_center_count": len(SHELL_CENTERS),
        "nci_interaction_class_count": len(NCI_INTERACTION_CLASSES),
        "model_feature_set_count": len(MODEL_FEATURE_SETS),
        "tool_count": len(tools),
        "tool_check": "executed" if check_tools else "path_only",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_STAGE3_CONTRACT)
    parser.add_argument("--feature-manifest", type=Path, default=DEFAULT_STAGE3_FEATURE_MANIFEST)
    parser.add_argument("--environment", type=Path, default=DEFAULT_STAGE3_ENVIRONMENT)
    parser.add_argument("--stage2-records", type=Path, default=DEFAULT_STAGE2_RECORDS)
    parser.add_argument("--stage2-feature-manifest", type=Path, default=DEFAULT_STAGE2_FEATURE_MANIFEST)
    parser.add_argument("--bootstrap", action="store_true", help="Write the default Stage 3 contract artifacts.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing Stage 3 contract artifacts when bootstrapping.")
    parser.add_argument("--check-tools", action="store_true", help="Run version commands for xTB, CREST, and Open Babel.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.bootstrap:
            report = bootstrap(args.contract, args.feature_manifest, args.environment, args.force)
            print(
                "Wrote Stage 3 contract artifacts to "
                f"{report['contract_path']}, {report['manifest_path']}, and {report['environment_path']}"
            )
        report = validate_contract(
            args.contract,
            args.feature_manifest,
            args.environment,
            args.stage2_records,
            args.stage2_feature_manifest,
            args.check_tools,
        )
    except ContractError as exc:
        print(f"Stage 3 contract validation failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

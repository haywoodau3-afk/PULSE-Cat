#!/usr/bin/env python3
"""Bootstrap and validate the Stage 2 feature-readiness contract."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/jacs_2025"
STAGE2_DIR = DATA_DIR / "stage2"
SCOPE_OUTCOMES = DATA_DIR / "scope-outcomes.csv"
MANUAL_SUBSTRATES = DATA_DIR / "manual-substrates.csv"
DEFAULT_RECORDS = STAGE2_DIR / "curated-reaction-records.jsonl"
DEFAULT_SEED_SET = STAGE2_DIR / "feature-ready-seed-set.json"
DEFAULT_FEATURE_MANIFEST = STAGE2_DIR / "feature-manifest.json"
DEFAULT_CURATION_PACKETS = STAGE2_DIR / "seed-curation-packets.json"
FEATURES_DIR = STAGE2_DIR / "features"
REPORTS_DIR = STAGE2_DIR / "reports"

CURATION_STATUSES = {"source_indexed", "structure_curated", "atom_mapped", "feature_ready"}
EE_STATUSES = {"reported", "zero_curated", "not_applicable_achiral", "unknown"}
REVIEW_STATUSES = {"pending", "checked", "needs_review"}
BACKBONE_SUBSTRATES = ["1a", "1e", "1o", "1v", "1ae", "1ac"]
SELECTED_SEED_SUBSTRATES = ["1a", "1e", "1o", "1v", "1ae", "1ac", "1j", "1p", "1aa", "1ad", "1ah", "1am"]
POSE_INTERACTION_FEATURE_CONTRACT = {
    "schema_version": "stage2-pose-interaction-feature-contract-v1",
    "status": "implemented",
    "source_pose_scope": "Stage 1 retained frozen-core Fe-bound assemblies",
    "per_pose_geometry_features": [
        "fe_n_distance_angstrom",
        "nitrene_n_to_reported_c_distance_angstrom",
        "nitrene_n_to_transferred_h_distance_angstrom",
        "fe_n_reported_c_angle_degrees",
        "nitrene_n_reported_c_transferred_h_angle_degrees",
        "reported_c_to_porphyrin_plane_distance_angstrom",
        "substrate_centroid_to_fe_distance_angstrom",
        "minimum_core_substrate_distance_angstrom",
        "core_substrate_contact_count_by_distance_bin",
    ],
    "aggregation_statistics": ["count", "min", "q05", "median", "mean", "q95", "max", "std"],
    "provenance_requirements": [
        "pose_generation_run_id",
        "pose_id",
        "substrate_id",
        "constraint_profile_id",
        "geometry_path",
        "reported_reactive_site",
        "candidate_site_id",
    ],
}
FEATURE_MANIFEST = {
    "schema_version": "stage2-feature-manifest-v1",
    "feature_policy": "provenance_tracked_blocks_with_separate_granularity",
    "feature_blocks": [
        {
            "block_id": "tier1_physchem",
            "status": "implemented",
            "granularity": "record",
            "expected_feature_count_range": [20, 50],
            "dependencies": ["feature_ready reaction records", "RDKit"],
            "feature_families": [
                "molecular_size",
                "element_counts",
                "heteroatom_counts",
                "ring_aromaticity",
                "rotatable_bonds",
                "formal_charge",
                "logp_tpsa",
                "candidate_site_type_counts",
            ],
            "output_path": "data/jacs_2025/stage2/features/tier1.jsonl",
        },
        {
            "block_id": "tier1_fingerprint",
            "status": "implemented",
            "granularity": "record",
            "expected_feature_count_range": [1024, 2048],
            "dependencies": ["feature_ready reaction records", "RDKit"],
            "feature_families": ["Morgan/ECFP bit vector"],
            "parameters": {"radius": 2, "n_bits": 2048, "use_chirality": True},
            "output_path": "data/jacs_2025/stage2/features/tier1.jsonl",
        },
        {
            "block_id": "candidate_site_features",
            "status": "implemented",
            "granularity": "candidate_site",
            "expected_feature_count_range": [20, 100],
            "dependencies": ["feature_ready reaction records", "reported/candidate C-H site curation", "RDKit"],
            "feature_families": [
                "atom_identity",
                "hybridization",
                "aromaticity",
                "ring_membership",
                "hydrogen_count",
                "neighbor_atom_environment",
                "topological_distance_from_nitrene_n",
                "benzylic_allylic_heteroaryl_tags",
                "local_substituent_environment",
            ],
            "output_path": "data/jacs_2025/stage2/features/tier1.jsonl",
        },
        {
            "block_id": "pose_summary",
            "status": "implemented",
            "granularity": "pose_aggregate",
            "expected_feature_count_range": [50, 100],
            "dependencies": ["Stage 1 smoke/panel reports"],
            "feature_families": [
                "retained_pose_count",
                "UFF_score_distribution",
                "clash_screen_counts",
                "core_RMSD_summary",
                "Fe_N_distance_summary",
                "pose_selection_bucket_counts",
            ],
            "output_path": "data/jacs_2025/stage2/features/pose-summary.jsonl",
        },
        {
            "block_id": "pose_interaction",
            "status": "implemented",
            "granularity": "pose_and_pose_aggregate",
            "expected_feature_count_range": [50, 200],
            "dependencies": [
                "feature_ready reaction records",
                "Stage 1 retained frozen-core assemblies",
                "reported/candidate C-H site atom maps",
            ],
            "feature_families": POSE_INTERACTION_FEATURE_CONTRACT["per_pose_geometry_features"],
            "aggregation_statistics": POSE_INTERACTION_FEATURE_CONTRACT["aggregation_statistics"],
            "output_path": "data/jacs_2025/stage2/features/pose-interaction.jsonl",
        },
        {
            "block_id": "bde_features",
            "status": "deferred",
            "granularity": "candidate_site",
            "expected_feature_count_range": [5, 20],
            "dependencies": ["candidate_site_features", "GFN2-xTB/ALPB(ether)", "BDE calibration panel"],
            "feature_families": [
                "absolute_BDE",
                "within_substrate_BDE_rank",
                "BDE_competition_gap",
                "calibration_status",
                "calibration_residual_or_uncertainty",
            ],
            "output_path": "data/jacs_2025/stage2/features/bde.jsonl",
        },
    ],
    "reporting_requirements": [
        "substrate_count",
        "pose_count",
        "family_split",
        "feature_provenance",
        "uncertainty_method",
        "BDE_calibration_status",
    ],
}
SEED_SLOT_DEFINITIONS = [
    {
        "slot_id": "aryl-position-substituent",
        "label": "Aryl-position/substituent",
        "candidate_substrate_ids": ["1j", "1k"],
        "selection_status": "locked",
        "selected_substrate_id": "1j",
        "selection_rationale": "Keeps the first seed pass on the Fe(P7)Cl scope while covering aryl-position variation.",
    },
    {
        "slot_id": "fused-o-heteroaryl",
        "label": "Fused O heteroaryl",
        "candidate_substrate_ids": ["1p", "1q"],
        "selection_status": "locked",
        "selected_substrate_id": "1p",
        "selection_rationale": "Covers fused oxygen heteroaryl chemistry with a lower-ee stress case.",
    },
    {
        "slot_id": "n-heteroaryl",
        "label": "N heteroaryl",
        "candidate_substrate_ids": ["1z", "1aa"],
        "selection_status": "locked",
        "selected_substrate_id": "1aa",
        "selection_rationale": "Uses the Fe(P7)Cl N-heteroaryl record for the first ee baseline; 1z remains in the all-41 ledger as zero_curated.",
    },
    {
        "slot_id": "thioether-linker",
        "label": "Thioether linker",
        "candidate_substrate_ids": ["1ad"],
        "selection_status": "locked",
        "selected_substrate_id": "1ad",
        "selection_rationale": "Single-slot thioether linker representative, manually confirmed as 0% ee.",
    },
    {
        "slot_id": "lower-selectivity-alkyl-aryl-chain",
        "label": "Lower-selectivity alkyl/aryl chain",
        "candidate_substrate_ids": ["1ah", "1ai"],
        "selection_status": "locked",
        "selected_substrate_id": "1ah",
        "selection_rationale": "Covers nonactivated alkyl C-H amination with a lower-ee Fe(P7)Cl record.",
    },
    {
        "slot_id": "cycloalkyl-alkenyl",
        "label": "Cycloalkyl/alkenyl",
        "candidate_substrate_ids": ["1am", "1an"],
        "selection_status": "locked",
        "selected_substrate_id": "1am",
        "selection_rationale": "Uses the chiral cycloalkyl product for the first ee baseline; 1an remains all-41 achiral-product coverage.",
    },
]

FAMILY_ASSIGNMENTS = {
    "1a": ("diaryl-ethyl-parent", "Parent diaryl ethyl aryl azide"),
    "1b": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1c": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1d": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1e": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1f": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1g": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1h": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1i": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1j": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1k": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1l": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1m": ("diaryl-ethyl-aryl-substituted", "Substituted diaryl ethyl aryl azide"),
    "1n": ("polycyclic-aryl", "Polycyclic aryl analogue"),
    "1o": ("oxygen-heteroaryl", "Oxygen heteroaryl analogue"),
    "1p": ("oxygen-heteroaryl-fused", "Fused oxygen heteroaryl analogue"),
    "1q": ("oxygen-heteroaryl-fused", "Fused oxygen heteroaryl analogue"),
    "1r": ("oxygen-heterocycle-fused", "Fused oxygen heterocycle analogue"),
    "1s": ("oxygen-heterocycle-fused", "Fused oxygen heterocycle analogue"),
    "1t": ("oxygen-heterocycle-fused", "Fused oxygen heterocycle analogue"),
    "1u": ("carbonyl-heterocycle-fused", "Fused carbonyl heterocycle analogue"),
    "1v": ("sulfur-heteroaryl", "Sulfur heteroaryl analogue"),
    "1w": ("sulfur-heteroaryl-fused", "Fused sulfur heteroaryl analogue"),
    "1x": ("sulfur-heteroaryl-fused", "Fused sulfur heteroaryl analogue"),
    "1y": ("sulfur-heterocycle-fused", "Fused sulfur heterocycle analogue"),
    "1z": ("nitrogen-heteroaryl", "Nitrogen heteroaryl analogue"),
    "1aa": ("nitrogen-heteroaryl", "Nitrogen heteroaryl analogue"),
    "1ab": ("nitrogen-heteroaryl", "Nitrogen heteroaryl analogue"),
    "1ac": ("silyl-alkyl-aryl", "Silyl alkyl aryl analogue"),
    "1ad": ("thioether-linker", "Thioether linker analogue"),
    "1ae": ("carbonyl-alkyl-aryl", "Carbonyl alkyl aryl analogue"),
    "1af": ("carbonyl-alkyl-aryl", "Carbonyl alkyl aryl analogue"),
    "1ag": ("carbonyl-alkyl-aryl", "Carbonyl alkyl aryl analogue"),
    "1ah": ("alkyl-aryl-chain", "Alkyl aryl-chain analogue"),
    "1ai": ("alkyl-aryl-chain", "Alkyl aryl-chain analogue"),
    "1aj": ("cycloalkyl-alkyl-aryl", "Cycloalkyl alkyl aryl analogue"),
    "1ak": ("cycloalkyl-alkyl-aryl", "Cycloalkyl alkyl aryl analogue"),
    "1al": ("cycloalkyl-alkyl-aryl", "Cycloalkyl alkyl aryl analogue"),
    "1am": ("cycloalkyl-aryl", "Cycloalkyl aryl analogue"),
    "1an": ("alkenyl-cycloalkyl-aryl", "Alkenyl cycloalkyl aryl analogue"),
    "1ao": ("branched-diaryl-alkyl", "Branched diaryl alkyl analogue"),
}

SEED_CURATION_PACKETS = {
    "schema_version": "stage2-seed-curation-packets-v1",
    "curation_policy": "compact_human_checked_reaction_centres_with_generated_candidate_sites",
    "feature_ready_entries": [
        {
            "substrate_id": "1a",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[N:1]#[N:2]=[N:3][c:4]1[cH:5][cH:6][cH:7][cH:8][c:9]1[CH2:10][CH2:11][c:12]1[cH:13][cH:14][cH:15][cH:16][cH:17]1",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[CH2:10][C@H:11]1[c:12]1[cH:13][cH:14][cH:15][cH:16][cH:17]1",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "benzylic",
            "reaction_center_source_note": "Table 1 entry 1 reports 2-phenylindoline 2a; atom map 11 is the benzylic C-H site that forms the new C-N bond in the indoline product.",
        },
        {
            "substrate_id": "1e",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[N:1]#[N:2]=[N:3][c:4]1[cH:5][cH:6][cH:7][cH:8][c:9]1[CH2:10][CH2:11][c:12]1[cH:13][cH:14][c:15]([C:18]([F:19])([F:20])[F:21])[cH:16][cH:17]1",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[CH2:10][C@H:11]1[c:12]1[cH:13][cH:14][c:15]([C:18]([F:19])([F:20])[F:21])[cH:16][cH:17]1",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "benzylic",
            "reaction_center_source_note": "Table 1 entry 5 reports 2e; atom map 11 follows the 1a indoline-forming benzylic C-H pattern with the distal para-CF3 aryl substituent retained.",
        },
        {
            "substrate_id": "1o",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[N:1]#[N:2]=[N:3][c:4]1[cH:5][cH:6][cH:7][cH:8][c:9]1[CH2:10][CH2:11][c:12]1[cH:13][cH:14][o:15][cH:16]1",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[CH2:10][C@H:11]1[c:12]1[cH:13][cH:14][o:15][cH:16]1",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "benzylic",
            "reaction_center_source_note": "Table 1 entry 15 reports 2o; atom map 11 follows the 1a indoline-forming benzylic C-H pattern with the distal furan retained.",
        },
        {
            "substrate_id": "1v",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[N:1]#[N:2]=[N:3][c:4]1[cH:5][cH:6][cH:7][cH:8][c:9]1[CH2:10][CH2:11][c:12]1[cH:13][cH:14][s:15][cH:16]1",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[CH2:10][C@H:11]1[c:12]1[cH:13][cH:14][s:15][cH:16]1",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "benzylic",
            "reaction_center_source_note": "Table 1 entry 22 reports 2v; atom map 11 follows the 1a indoline-forming benzylic C-H pattern with the distal thiophene retained.",
        },
        {
            "substrate_id": "1j",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[N:1]#[N:2]=[N:3][c:4]1[cH:5][cH:6][c:7]([CH3:18])[cH:8][c:9]1[CH2:10][CH2:11][c:12]1[cH:13][cH:14][cH:15][cH:16][cH:17]1",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][c:7]([CH3:18])[cH:8][c:9]2[CH2:10][C@H:11]1[c:12]1[cH:13][cH:14][cH:15][cH:16][cH:17]1",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "benzylic",
            "reaction_center_source_note": "Table 1 entry 10 reports 2j; atom map 11 follows the indoline-forming benzylic C-H pattern while retaining the methyl substituent on the azide-bearing aryl ring.",
        },
        {
            "substrate_id": "1p",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[N:1]#[N:2]=[N:3][c:4]1[cH:5][cH:6][cH:7][cH:8][c:9]1[CH2:10][CH2:11][c:12]1[cH:13][c:14]2[cH:15][cH:16][cH:17][cH:18][c:19]2[o:20]1",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[CH2:10][C@H:11]1[c:12]1[cH:13][c:14]2[cH:15][cH:16][cH:17][cH:18][c:19]2[o:20]1",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "benzylic",
            "reaction_center_source_note": "Table 1 entry 16 reports 2p; atom map 11 follows the 1a indoline-forming benzylic C-H pattern with the distal benzofuran retained.",
        },
        {
            "substrate_id": "1aa",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[N:1]#[N:2]=[N:3][c:4]1[cH:5][cH:6][cH:7][cH:8][c:9]1[CH2:10][CH2:11][c:12]1[cH:13][cH:14][n:15][c:16]([Cl:18])[cH:17]1",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[CH2:10][C@H:11]1[c:12]1[cH:13][cH:14][n:15][c:16]([Cl:18])[cH:17]1",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "benzylic",
            "reaction_center_source_note": "Table 1 entry 27 reports 2aa; atom map 11 follows the 1a indoline-forming benzylic C-H pattern with the distal chloropyridyl ring retained.",
        },
        {
            "substrate_id": "1ae",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[CH3:14][O:13][C:12](=[O:15])[CH2:11][CH2:10][c:9]1[cH:8][cH:7][cH:6][cH:5][c:4]1[N:3]=[N:2]#[N:1]",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[CH2:10][C@H:11]1[C:12](=[O:15])[O:13][CH3:14]",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "carbonyl_alpha",
            "reaction_center_source_note": "Table 1 entry 31 reports 2ae; atom map 11 is the ester alpha C-H that forms the new C-N bond in the indoline product.",
        },
        {
            "substrate_id": "1ah",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[CH3:13][CH2:12][CH2:11][CH2:10][c:9]1[cH:8][cH:7][cH:6][cH:5][c:4]1[N:3]=[N:2]#[N:1]",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[CH2:10][C@H:11]1[CH2:12][CH3:13]",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "aliphatic",
            "reaction_center_source_note": "Table 1 entry 34 reports 2ah; atom map 11 is the secondary aliphatic C-H that forms the new C-N bond, leaving an ethyl substituent at the indoline stereocentre.",
        },
        {
            "substrate_id": "1ac",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[N:1]#[N:2]=[N:3][c:4]1[cH:5][cH:6][cH:7][cH:8][c:9]1[CH2:10][CH2:11][CH2:12][Si:13]([CH3:14])([CH3:15])[CH3:16]",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[CH2:10][C@H:11]1[CH2:12][Si:13]([CH3:14])([CH3:15])[CH3:16]",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "silylalkyl_substituted",
            "reaction_center_source_note": "Table 1 entry 29 reports 2ac after Boc-protected derivatization; atom map 11 is curated as the indoline-forming C-H, leaving the CH2-SiMe3 substituent at the product stereocentre.",
        },
        {
            "substrate_id": "1ad",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[N:1]#[N:2]=[N:3][c:4]1[cH:5][cH:6][cH:7][cH:8][c:9]1[S:10][CH2:11][c:12]1[cH:13][cH:14][cH:15][cH:16][cH:17]1",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[S:10][C@H:11]1[c:12]1[cH:13][cH:14][cH:15][cH:16][cH:17]1",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "thioether_benzylic",
            "reaction_center_source_note": "Table 1 entry 30 reports 2ad; atom map 11 is the thioether benzylic C-H that closes to the aryl nitrene N in the sulfur-containing indoline analogue.",
        },
        {
            "substrate_id": "1am",
            "curation_status": "feature_ready",
            "review_status": "checked",
            "atom_mapped_substrate_smiles": "[N:1]#[N:2]=[N:3][c:4]1[cH:5][cH:6][cH:7][cH:8][c:9]1[CH:10]1[CH2:11][CH2:12][CH2:13][CH2:14]1",
            "atom_mapped_product_smiles": "[NH:3]1[c:4]2[cH:5][cH:6][cH:7][cH:8][c:9]2[CH:10]2[C@H:11]1[CH2:12][CH2:13][CH2:14]2",
            "reported_reactive_atom_map_id": 11,
            "reported_site_type": "cycloalkyl",
            "reaction_center_source_note": "Table 1 entry 39 reports cyclopentane-fused indoline 2am; atom map 11 is one desymmetrized cyclopentyl C-H forming the new C-N bond.",
        }
    ],
    "pending_seed_substrate_ids": [],
}


class ContractError(ValueError):
    """Raised when a Stage 2 contract validation fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ContractError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc
    return records


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.dumps(record, sort_keys=True) for record in records]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def optional_int(value: str) -> int | None:
    if value == "":
        return None
    return int(value)


def stage2_ee_status(scope_row: dict[str, str]) -> tuple[int | None, str, str, str]:
    substrate_id = scope_row["substrate_id"]
    if substrate_id in {"1z", "1ad"}:
        return (
            0,
            "zero_curated",
            "checked",
            "Curated as 0% ee/racemic rather than an unknown ee label.",
        )
    if substrate_id == "1an":
        return (
            None,
            "not_applicable_achiral",
            "checked",
            "Product curated as achiral, so ee is structurally not applicable.",
        )
    if scope_row["ee_status"] == "reported":
        return optional_int(scope_row["ee_percent"]), "reported", "checked", "Source table reports a numeric ee."
    return None, "unknown", "pending", "Stage 0 table does not provide a model-ready ee label."


def build_seed_curation_packets() -> dict[str, Any]:
    return SEED_CURATION_PACKETS


def atom_site_type(atom: Any) -> str:
    if atom.GetIsAromatic():
        return "aryl"
    neighbors = atom.GetNeighbors()
    if any(neighbor.GetIsAromatic() for neighbor in neighbors):
        return "benzylic"
    for neighbor in neighbors:
        if neighbor.GetSymbol() != "C":
            continue
        if any(
            bond.GetBondTypeAsDouble() == 2.0 and bond.GetOtherAtom(neighbor).GetSymbol() == "O"
            for bond in neighbor.GetBonds()
        ):
            return "carbonyl_alpha"
    if atom.IsInRing():
        return "cycloalkyl"
    for neighbor in neighbors:
        bond = atom.GetOwningMol().GetBondBetweenAtoms(atom.GetIdx(), neighbor.GetIdx())
        if bond is not None and bond.GetBondTypeAsDouble() == 2.0:
            return "allylic_or_vinylic"
        if any(second.GetIsAromatic() for second in neighbor.GetNeighbors() if second.GetIdx() != atom.GetIdx()):
            return "heteroaryl_adjacent" if neighbor.GetSymbol() not in {"C", "H"} else "benzylic_adjacent"
    return "aliphatic"


def candidate_sites_from_mapped_smiles(substrate_id: str, mapped_smiles: str) -> list[dict[str, Any]]:
    try:
        from rdkit import Chem
    except ImportError as exc:
        raise ContractError("RDKit is required to generate candidate C-H sites") from exc

    molecule = Chem.MolFromSmiles(mapped_smiles, sanitize=True)
    if molecule is None:
        raise ContractError(f"{substrate_id}: atom-mapped substrate SMILES does not parse")

    candidate_sites: list[dict[str, Any]] = []
    for atom in molecule.GetAtoms():
        if atom.GetSymbol() != "C":
            continue
        hydrogen_count = int(atom.GetTotalNumHs())
        atom_map_id = atom.GetAtomMapNum()
        if hydrogen_count <= 0 or atom_map_id <= 0:
            continue
        site_type = atom_site_type(atom)
        candidate_sites.append(
            {
                "site_id": f"{substrate_id}-c{atom_map_id}-{site_type}",
                "atom_map_id": atom_map_id,
                "site_type": site_type,
                "hydrogen_count": hydrogen_count,
            }
        )
    return sorted(candidate_sites, key=lambda site: site["atom_map_id"])


def curation_entries_by_substrate(curation_packets: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["substrate_id"]: entry for entry in curation_packets.get("feature_ready_entries", [])}


def atom_mapped_smiles(smiles: str) -> str:
    try:
        from rdkit import Chem
    except ImportError as exc:
        raise ContractError("RDKit is required to atom-map scope substrates") from exc

    molecule = Chem.MolFromSmiles(smiles, sanitize=True)
    if molecule is None:
        raise ContractError(f"Could not parse substrate SMILES for atom mapping: {smiles}")
    for atom_index, atom in enumerate(molecule.GetAtoms(), start=1):
        atom.SetAtomMapNum(atom_index)
    return Chem.MolToSmiles(molecule, canonical=False)


def nitrene_molecule_from_mapped_azide(mapped_smiles: str) -> Any:
    try:
        from rdkit import Chem
    except ImportError as exc:
        raise ContractError("RDKit is required to infer reaction centers") from exc

    molecule = Chem.MolFromSmiles(mapped_smiles, sanitize=True)
    if molecule is None:
        raise ContractError("Mapped azide SMILES does not parse")
    terminal_nitrogen_indices = [
        atom.GetIdx()
        for atom in molecule.GetAtoms()
        if atom.GetSymbol() == "N" and not any(neighbor.GetSymbol() == "C" for neighbor in atom.GetNeighbors())
    ]
    if len(terminal_nitrogen_indices) != 2:
        raise ContractError(f"Expected two non-proximal azide nitrogens, found {len(terminal_nitrogen_indices)}")
    editable = Chem.RWMol(molecule)
    for atom_index in sorted(terminal_nitrogen_indices, reverse=True):
        editable.RemoveAtom(atom_index)
    nitrene = editable.GetMol()
    Chem.SanitizeMol(nitrene)
    return nitrene


def infer_reported_reactive_atom_map_id(substrate_id: str, mapped_smiles: str) -> tuple[int, str]:
    try:
        from rdkit import Chem
    except ImportError as exc:
        raise ContractError("RDKit is required to infer reaction centers") from exc

    if substrate_id == "1ag":
        return 6, "manual_exception_amide_alpha_site"
    if substrate_id in {"1am", "1an"}:
        return 11, "manual_exception_symmetry_related_cycloalkyl_site"

    molecule = nitrene_molecule_from_mapped_azide(mapped_smiles)
    nitrene_atoms = [
        atom
        for atom in molecule.GetAtoms()
        if atom.GetSymbol() == "N" and atom.GetDegree() == 1 and any(neighbor.GetSymbol() == "C" for neighbor in atom.GetNeighbors())
    ]
    if len(nitrene_atoms) != 1:
        raise ContractError(f"{substrate_id}: expected one substrate-bound nitrene N, found {len(nitrene_atoms)}")
    distance_matrix = Chem.GetDistanceMatrix(molecule)
    nitrene_atom = nitrene_atoms[0]
    candidates = [
        atom
        for atom in molecule.GetAtoms()
        if (
            atom.GetSymbol() == "C"
            and int(atom.GetTotalNumHs()) > 0
            and not atom.GetIsAromatic()
            and int(distance_matrix[nitrene_atom.GetIdx(), atom.GetIdx()]) == 4
        )
    ]
    if len(candidates) != 1:
        raise ContractError(
            f"{substrate_id}: expected one non-aromatic C-H candidate four bonds from nitrene N, found {len(candidates)}"
        )
    return candidates[0].GetAtomMapNum(), "inferred_non_aromatic_c_h_four_bonds_from_nitrene"


def apply_inferred_scope_reaction_center(record: dict[str, Any]) -> None:
    substrate_id = record["substrate_id"]
    mapped_substrate = atom_mapped_smiles(record["structure"]["azide_smiles"])
    reported_atom_map_id, inference_rule = infer_reported_reactive_atom_map_id(substrate_id, mapped_substrate)
    candidate_sites = candidate_sites_from_mapped_smiles(substrate_id, mapped_substrate)
    matches = [site for site in candidate_sites if site["atom_map_id"] == reported_atom_map_id]
    if not matches:
        raise ContractError(f"{substrate_id}: inferred reported atom {reported_atom_map_id} is absent from candidate sites")
    reported_site = dict(matches[0])
    reported_site["role"] = "reported_product_forming_c_h"
    record["curation_status"] = "atom_mapped"
    record["structure"]["atom_mapped_substrate_smiles"] = mapped_substrate
    record["reaction_center"] = {
        "reported_reactive_site": reported_site,
        "candidate_sites": candidate_sites,
        "reported_site_in_candidates": True,
        "source_note": (
            "Full-scope reaction center inferred from the conserved intramolecular C-H amination scope pattern; "
            f"rule={inference_rule}. Product atom map remains deferred until manual product-map review."
        ),
        "review_status": "checked",
        "assignment_method": inference_rule,
    }


def apply_feature_ready_curation(record: dict[str, Any], curation_entry: dict[str, Any]) -> None:
    substrate_id = record["substrate_id"]
    candidate_sites = candidate_sites_from_mapped_smiles(
        substrate_id,
        curation_entry["atom_mapped_substrate_smiles"],
    )
    reported_atom_map_id = curation_entry["reported_reactive_atom_map_id"]
    matches = [site for site in candidate_sites if site["atom_map_id"] == reported_atom_map_id]
    if not matches:
        raise ContractError(f"{substrate_id}: reported reactive atom {reported_atom_map_id} is not a candidate C-H site")
    reported_site = dict(matches[0])
    reported_site["site_type"] = curation_entry.get("reported_site_type", reported_site["site_type"])
    reported_site["role"] = "reported_product_forming_c_h"

    record["curation_status"] = curation_entry["curation_status"]
    record["structure"]["atom_mapped_substrate_smiles"] = curation_entry["atom_mapped_substrate_smiles"]
    record["structure"]["atom_mapped_product_smiles"] = curation_entry["atom_mapped_product_smiles"]
    record["reaction_center"] = {
        "reported_reactive_site": reported_site,
        "candidate_sites": candidate_sites,
        "reported_site_in_candidates": True,
        "source_note": curation_entry["reaction_center_source_note"],
        "review_status": curation_entry["review_status"],
    }


def build_record(
    scope_row: dict[str, str],
    manual_row: dict[str, str],
    curation_entries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    substrate_id = scope_row["substrate_id"]
    family_id, family_label = FAMILY_ASSIGNMENTS[substrate_id]
    ee_percent, ee_status, label_review_status, label_review_note = stage2_ee_status(scope_row)

    record = {
        "schema_version": "stage2-reaction-record-v1",
        "reaction_id": f"jacs-2025-{substrate_id}",
        "substrate_id": substrate_id,
        "product_id": scope_row["product_id"],
        "catalyst_id": scope_row["catalyst_id"],
        "condition": {
            "condition_set_id": f"jacs-2025-table1-{scope_row['temperature_c']}c",
            "temperature_c": optional_int(scope_row["temperature_c"]),
            "fixed_jacs_conditions": True,
        },
        "source": {
            "document_id": "jacs-2025-main-paper",
            "location": scope_row["source_location"],
            "confidence": "primary_table",
            "curation_status_stage0": scope_row["curation_status"],
        },
        "outcome": {
            "feasibility_status": "productive",
            "isolated_yield_percent": optional_int(scope_row["yield_percent"]),
            "yield_qualifier": "exact",
            "ee_percent": ee_percent,
            "ee_status": ee_status,
            "ee_status_stage0": scope_row["ee_status"],
            "optical_rotation_sign": scope_row["optical_rotation_sign"] or None,
            "major_product_configuration": None,
            "label_review_status": label_review_status,
            "label_review_note": label_review_note,
        },
        "structure": {
            "azide_smiles": manual_row["azide_smiles"],
            "nitrene_smiles": manual_row["nitrene_smiles"],
            "azide_position": manual_row["azide_position"],
            "atom_mapped_substrate_smiles": None,
            "atom_mapped_product_smiles": None,
            "azide_nitrene_precursor_linkage": manual_row["retained_atom"],
        },
        "reaction_center": {
            "reported_reactive_site": None,
            "candidate_sites": [],
            "reported_site_in_candidates": None,
            "source_note": None,
            "review_status": "pending",
        },
        "family": {
            "family_id": family_id,
            "family_label": family_label,
            "assignment_method": "manual_seed_contract",
            "structure_tags": [],
            "deterministic_tag_check_status": "pending",
        },
        "curation_status": "source_indexed",
    }
    if substrate_id in curation_entries:
        apply_feature_ready_curation(record, curation_entries[substrate_id])
    else:
        apply_inferred_scope_reaction_center(record)
    return record


def build_records(
    scope_path: Path,
    manual_path: Path,
    curation_packets: dict[str, Any],
) -> list[dict[str, Any]]:
    scope_rows = read_csv(scope_path)
    manual_by_id = {row["substrate_id"]: row for row in read_csv(manual_path)}
    curation_entries = curation_entries_by_substrate(curation_packets)
    records = []
    for scope_row in scope_rows:
        substrate_id = scope_row["substrate_id"]
        if substrate_id not in manual_by_id:
            raise ContractError(f"{substrate_id} is missing from {manual_path}")
        records.append(build_record(scope_row, manual_by_id[substrate_id], curation_entries))
    return records


def build_seed_set() -> dict[str, Any]:
    return {
        "schema_version": "stage2-seed-set-v1",
        "selection_policy": "chemical_family_coverage_first_label_diversity_second",
        "planned_seed_count": 12,
        "selected_seed_substrate_ids": SELECTED_SEED_SUBSTRATES,
        "locked_backbone_substrate_ids": BACKBONE_SUBSTRATES,
        "seed_slots": SEED_SLOT_DEFINITIONS,
        "pose_interaction_feature_contract": POSE_INTERACTION_FEATURE_CONTRACT,
        "notes": [
            "The seed set is an engineering and validation wedge, not the full 41-record chemical universe.",
            "Selected seed records must still pass atom-map and reaction-centre review before feature_ready extraction.",
        ],
    }


def build_feature_manifest() -> dict[str, Any]:
    return FEATURE_MANIFEST


def bootstrap(
    records_path: Path,
    seed_path: Path,
    manifest_path: Path,
    curation_path: Path,
    force: bool,
) -> dict[str, Any]:
    for output_path in [records_path, seed_path, manifest_path, curation_path]:
        if output_path.exists() and not force:
            raise ContractError(f"{output_path} already exists; pass --force to overwrite it")
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    curation_packets = build_seed_curation_packets()
    records = build_records(SCOPE_OUTCOMES, MANUAL_SUBSTRATES, curation_packets)
    seed_set = build_seed_set()
    feature_manifest = build_feature_manifest()
    write_jsonl(records_path, records)
    write_json(seed_path, seed_set)
    write_json(manifest_path, feature_manifest)
    write_json(curation_path, curation_packets)
    return {
        "records_path": str(records_path.relative_to(ROOT)),
        "seed_path": str(seed_path.relative_to(ROOT)),
        "manifest_path": str(manifest_path.relative_to(ROOT)),
        "curation_path": str(curation_path.relative_to(ROOT)),
        "record_count": len(records),
        "feature_ready_count": sum(record["curation_status"] == "feature_ready" for record in records),
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def validate_unique_ids(records: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for record in records:
        substrate_id = record.get("substrate_id")
        require(isinstance(substrate_id, str) and substrate_id, "Every record needs substrate_id")
        require(substrate_id not in seen, f"Duplicate substrate_id {substrate_id}")
        seen.add(substrate_id)


def validate_ledger_record(record: dict[str, Any], scope_by_id: dict[str, dict[str, str]]) -> None:
    substrate_id = record["substrate_id"]
    require(substrate_id in scope_by_id, f"{substrate_id}: missing scope-outcomes join")
    require(record.get("product_id") == scope_by_id[substrate_id]["product_id"], f"{substrate_id}: product_id mismatch")
    require(record.get("catalyst_id"), f"{substrate_id}: missing catalyst_id")
    require(record.get("condition", {}).get("condition_set_id"), f"{substrate_id}: missing condition_set_id")
    require(record.get("source", {}).get("location"), f"{substrate_id}: missing source location")
    require(record.get("curation_status") in CURATION_STATUSES, f"{substrate_id}: invalid curation_status")
    family = record.get("family", {})
    require(bool(family.get("family_id") or family.get("family_label")), f"{substrate_id}: missing family label")
    outcome = record.get("outcome", {})
    ee_status = outcome.get("ee_status")
    require(ee_status in EE_STATUSES, f"{substrate_id}: invalid ee_status {ee_status!r}")
    require(
        outcome.get("label_review_status") in REVIEW_STATUSES,
        f"{substrate_id}: invalid label_review_status",
    )
    if ee_status == "reported":
        require(isinstance(outcome.get("ee_percent"), int | float), f"{substrate_id}: reported ee needs numeric value")
    if ee_status == "zero_curated":
        require(outcome.get("ee_percent") == 0, f"{substrate_id}: zero_curated ee must be 0")
        require(
            outcome.get("label_review_status") == "checked",
            f"{substrate_id}: zero_curated ee requires checked label review",
        )
        require(bool(outcome.get("label_review_note")), f"{substrate_id}: zero_curated ee needs rationale")
    if ee_status == "not_applicable_achiral":
        require(outcome.get("ee_percent") is None, f"{substrate_id}: achiral ee must be null")
        require(
            outcome.get("label_review_status") == "checked",
            f"{substrate_id}: achiral ee requires checked label review",
        )


def site_key(site: dict[str, Any]) -> Any:
    if "atom_map_id" in site:
        return ("atom_map_id", site["atom_map_id"])
    if "atom_index" in site:
        return ("atom_index", site["atom_index"])
    if "site_id" in site:
        return ("site_id", site["site_id"])
    return None


def smiles_parse_ok(smiles: str) -> bool | None:
    try:
        from rdkit import Chem
    except ImportError:
        return None
    return Chem.MolFromSmiles(smiles, sanitize=True) is not None


def validate_feature_ready_record(record: dict[str, Any]) -> None:
    substrate_id = record["substrate_id"]
    structure = record.get("structure", {})
    require(structure.get("atom_mapped_substrate_smiles"), f"{substrate_id}: missing atom-mapped substrate SMILES")
    require(structure.get("atom_mapped_product_smiles"), f"{substrate_id}: missing atom-mapped product SMILES")
    require(structure.get("azide_nitrene_precursor_linkage"), f"{substrate_id}: missing azide/nitrene linkage")
    substrate_parse_ok = smiles_parse_ok(structure["atom_mapped_substrate_smiles"])
    product_parse_ok = smiles_parse_ok(structure["atom_mapped_product_smiles"])
    require(substrate_parse_ok is not False, f"{substrate_id}: atom-mapped substrate SMILES does not parse")
    require(product_parse_ok is not False, f"{substrate_id}: atom-mapped product SMILES does not parse")

    reaction_center = record.get("reaction_center", {})
    reported_site = reaction_center.get("reported_reactive_site")
    candidate_sites = reaction_center.get("candidate_sites")
    require(isinstance(reported_site, dict) and reported_site, f"{substrate_id}: missing reported reactive site")
    require(isinstance(candidate_sites, list) and candidate_sites, f"{substrate_id}: missing candidate sites")
    require(
        reaction_center.get("reported_site_in_candidates") is True,
        f"{substrate_id}: reported site must be confirmed in candidate set",
    )
    require(reaction_center.get("source_note"), f"{substrate_id}: missing reaction-centre source note")
    require(reaction_center.get("review_status") == "checked", f"{substrate_id}: reaction-centre review is not checked")

    reported_key = site_key(reported_site)
    candidate_keys = {site_key(site) for site in candidate_sites if isinstance(site, dict)}
    require(reported_key is not None, f"{substrate_id}: reported site needs a comparable id")
    require(reported_key in candidate_keys, f"{substrate_id}: reported site is absent from candidate sites")


def validate_atom_mapped_record(record: dict[str, Any]) -> None:
    substrate_id = record["substrate_id"]
    structure = record.get("structure", {})
    require(structure.get("atom_mapped_substrate_smiles"), f"{substrate_id}: missing atom-mapped substrate SMILES")
    substrate_parse_ok = smiles_parse_ok(structure["atom_mapped_substrate_smiles"])
    require(substrate_parse_ok is not False, f"{substrate_id}: atom-mapped substrate SMILES does not parse")

    reaction_center = record.get("reaction_center", {})
    reported_site = reaction_center.get("reported_reactive_site")
    candidate_sites = reaction_center.get("candidate_sites")
    require(isinstance(reported_site, dict) and reported_site, f"{substrate_id}: missing reported reactive site")
    require(isinstance(candidate_sites, list) and candidate_sites, f"{substrate_id}: missing candidate sites")
    require(
        reaction_center.get("reported_site_in_candidates") is True,
        f"{substrate_id}: reported site must be confirmed in candidate set",
    )
    require(reaction_center.get("source_note"), f"{substrate_id}: missing reaction-centre source note")
    require(reaction_center.get("review_status") == "checked", f"{substrate_id}: reaction-centre review is not checked")
    require(reaction_center.get("assignment_method"), f"{substrate_id}: missing reaction-centre assignment method")

    reported_key = site_key(reported_site)
    candidate_keys = {site_key(site) for site in candidate_sites if isinstance(site, dict)}
    require(reported_key is not None, f"{substrate_id}: reported site needs a comparable id")
    require(reported_key in candidate_keys, f"{substrate_id}: reported site is absent from candidate sites")


def validate_seed_set(seed_set: dict[str, Any], record_ids: set[str]) -> None:
    backbone = seed_set.get("locked_backbone_substrate_ids")
    selected_seed_ids = seed_set.get("selected_seed_substrate_ids")
    slots = seed_set.get("seed_slots")
    require(backbone == BACKBONE_SUBSTRATES, "Seed set backbone must match the Stage 1 backbone")
    require(selected_seed_ids == SELECTED_SEED_SUBSTRATES, "Seed set selected substrates must match the locked contract")
    require(len(set(selected_seed_ids)) == 12, "Seed set must contain 12 unique selected substrates")
    require(isinstance(slots, list) and len(slots) == 6, "Seed set must define six non-backbone slots")
    for substrate_id in backbone:
        require(substrate_id in record_ids, f"Seed backbone substrate {substrate_id} is missing from records")
    for substrate_id in selected_seed_ids:
        require(substrate_id in record_ids, f"Selected seed substrate {substrate_id} is missing from records")
    for slot in slots:
        candidates = slot.get("candidate_substrate_ids")
        require(isinstance(candidates, list) and candidates, f"{slot.get('slot_id')}: missing candidates")
        for substrate_id in candidates:
            require(substrate_id in record_ids, f"{slot.get('slot_id')}: candidate {substrate_id} missing from records")
        require(slot.get("selection_status") == "locked", f"{slot.get('slot_id')}: seed slot must be locked")
        require(slot.get("selected_substrate_id") in candidates, f"{slot.get('slot_id')}: locked slot needs selected candidate")
        require(bool(slot.get("selection_rationale")), f"{slot.get('slot_id')}: locked slot needs selection rationale")
    interaction_contract = seed_set.get("pose_interaction_feature_contract", {})
    require(
        interaction_contract.get("status") == "implemented",
        "Pose interaction feature contract must be implemented",
    )
    required_interactions = {
        "nitrene_n_to_reported_c_distance_angstrom",
        "fe_n_reported_c_angle_degrees",
        "nitrene_n_reported_c_transferred_h_angle_degrees",
    }
    require(
        required_interactions <= set(interaction_contract.get("per_pose_geometry_features", [])),
        "Pose interaction contract is missing required distance/angle features",
    )


def validate_feature_manifest(manifest: dict[str, Any]) -> None:
    require(manifest.get("schema_version") == "stage2-feature-manifest-v1", "Invalid feature manifest schema version")
    blocks = manifest.get("feature_blocks")
    require(isinstance(blocks, list) and blocks, "Feature manifest must define feature blocks")
    required_blocks = {
        "tier1_physchem",
        "tier1_fingerprint",
        "candidate_site_features",
        "pose_summary",
        "pose_interaction",
        "bde_features",
    }
    by_id = {block.get("block_id"): block for block in blocks if isinstance(block, dict)}
    require(required_blocks <= set(by_id), "Feature manifest is missing required Stage 2 blocks")
    for block_id, block in by_id.items():
        require(
            block.get("status") in {"declared_not_yet_computed", "implemented", "implemented_partial", "deferred"},
            f"{block_id}: invalid status",
        )
        require(block.get("granularity") in {"record", "candidate_site", "pose", "pose_aggregate", "pose_and_pose_aggregate"}, f"{block_id}: invalid granularity")
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
        require(block.get("output_path"), f"{block_id}: missing output path")
    require(by_id["tier1_fingerprint"].get("parameters", {}).get("n_bits") in {1024, 2048}, "tier1_fingerprint: unexpected bit count")
    require(by_id["pose_interaction"]["expected_feature_count_range"][1] >= 100, "pose_interaction: feature range is too small")
    require(by_id["bde_features"].get("status") == "deferred", "bde_features should remain deferred in this contract slice")
    reporting = set(manifest.get("reporting_requirements", []))
    require(
        {"substrate_count", "pose_count", "family_split", "feature_provenance", "uncertainty_method", "BDE_calibration_status"} <= reporting,
        "Feature manifest is missing Stage 2 report requirements",
    )


def validate_curation_packets(curation_packets: dict[str, Any], records: list[dict[str, Any]]) -> None:
    require(
        curation_packets.get("schema_version") == "stage2-seed-curation-packets-v1",
        "Invalid seed curation packet schema version",
    )
    entries = curation_packets.get("feature_ready_entries")
    require(isinstance(entries, list), "Seed curation packets must define feature_ready_entries")
    by_record_id = {record["substrate_id"]: record for record in records}
    selected_seed_set = set(SELECTED_SEED_SUBSTRATES)
    entry_ids = set()
    for entry in entries:
        substrate_id = entry.get("substrate_id")
        require(substrate_id in selected_seed_set, f"{substrate_id}: curation entry is not in selected seed set")
        require(substrate_id not in entry_ids, f"{substrate_id}: duplicate curation entry")
        entry_ids.add(substrate_id)
        require(entry.get("curation_status") == "feature_ready", f"{substrate_id}: curation entry must be feature_ready")
        require(entry.get("review_status") == "checked", f"{substrate_id}: curation entry must be checked")
        require(entry.get("atom_mapped_substrate_smiles"), f"{substrate_id}: curation entry missing mapped substrate")
        require(entry.get("atom_mapped_product_smiles"), f"{substrate_id}: curation entry missing mapped product")
        require(isinstance(entry.get("reported_reactive_atom_map_id"), int), f"{substrate_id}: curation entry missing reported atom map id")
        require(entry.get("reaction_center_source_note"), f"{substrate_id}: curation entry missing source note")
        require(
            by_record_id[substrate_id]["curation_status"] == "feature_ready",
            f"{substrate_id}: curation packet and ledger curation statuses disagree",
        )
    pending_ids = set(curation_packets.get("pending_seed_substrate_ids", []))
    require(entry_ids | pending_ids == selected_seed_set, "Curation packets must partition the selected seed set")
    require(not (entry_ids & pending_ids), "Curation packets cannot mark a seed record both ready and pending")


def validate_contract(
    records_path: Path,
    seed_path: Path,
    manifest_path: Path,
    curation_path: Path,
    scope_path: Path,
) -> dict[str, Any]:
    records = read_jsonl(records_path)
    scope_rows = read_csv(scope_path)
    scope_by_id = {row["substrate_id"]: row for row in scope_rows}
    require(len(records) == len(scope_rows), f"Expected {len(scope_rows)} records, found {len(records)}")
    validate_unique_ids(records)
    record_ids = {record["substrate_id"] for record in records}
    require(record_ids == set(scope_by_id), "Stage 2 ledger substrate ids must match scope-outcomes.csv exactly")

    feature_ready_count = 0
    atom_mapped_count = 0
    for record in records:
        validate_ledger_record(record, scope_by_id)
        if record["curation_status"] == "feature_ready":
            feature_ready_count += 1
            validate_feature_ready_record(record)
        elif record["curation_status"] == "atom_mapped":
            atom_mapped_count += 1
            validate_atom_mapped_record(record)

    seed_set = json.loads(seed_path.read_text(encoding="utf-8"))
    validate_seed_set(seed_set, record_ids)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_feature_manifest(manifest)
    curation_packets = json.loads(curation_path.read_text(encoding="utf-8"))
    validate_curation_packets(curation_packets, records)

    return {
        "records_path": str(records_path.relative_to(ROOT) if records_path.is_relative_to(ROOT) else records_path),
        "seed_path": str(seed_path.relative_to(ROOT) if seed_path.is_relative_to(ROOT) else seed_path),
        "manifest_path": str(manifest_path.relative_to(ROOT) if manifest_path.is_relative_to(ROOT) else manifest_path),
        "curation_path": str(curation_path.relative_to(ROOT) if curation_path.is_relative_to(ROOT) else curation_path),
        "record_count": len(records),
        "feature_ready_count": feature_ready_count,
        "atom_mapped_count": atom_mapped_count,
        "checked_reaction_center_count": feature_ready_count + atom_mapped_count,
        "seed_backbone_count": len(seed_set["locked_backbone_substrate_ids"]),
        "selected_seed_count": len(seed_set["selected_seed_substrate_ids"]),
        "seed_slot_count": len(seed_set["seed_slots"]),
        "feature_block_count": len(manifest["feature_blocks"]),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--seed-set", type=Path, default=DEFAULT_SEED_SET)
    parser.add_argument("--feature-manifest", type=Path, default=DEFAULT_FEATURE_MANIFEST)
    parser.add_argument("--curation-packets", type=Path, default=DEFAULT_CURATION_PACKETS)
    parser.add_argument("--scope-outcomes", type=Path, default=SCOPE_OUTCOMES)
    parser.add_argument("--bootstrap", action="store_true", help="Write the default Stage 2 ledger and seed files.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files when bootstrapping.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.bootstrap:
            report = bootstrap(args.records, args.seed_set, args.feature_manifest, args.curation_packets, args.force)
            print(
                "Wrote Stage 2 contract artifacts to "
                f"{report['records_path']}, {report['seed_path']}, {report['manifest_path']}, "
                f"and {report['curation_path']}"
            )
        report = validate_contract(
            args.records,
            args.seed_set,
            args.feature_manifest,
            args.curation_packets,
            args.scope_outcomes,
        )
    except ContractError as exc:
        print(f"Stage 2 contract validation failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

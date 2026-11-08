#!/usr/bin/env python3
"""Rule-based, reaction-centre-anchored substrate diversity features.

This module intentionally uses only RDKit graph information and frozen
chemical priors.  It does not run quantum chemistry, fit correction terms to
reaction labels, or use product/outcome information when a candidate is
unlabelled.  The resulting features are designed for transparent substrate
acquisition experiments, not as calibrated BDE or activation-energy claims.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold


SCHEMA_VERSION = "rule-based-diversity-v1"
RULE_VERSION = "v3"
SUPPORTED_VERSIONS = ("v0", "v1", "v2", "v3", "v4", "v5", "v6")
MIXABLE_VERSIONS = ("v1", "v2", "v3", "v4", "v5", "v6")
SHELL_DISTANCES = (1, 2, 3)
PATH_DISTANCE_PRIMARY = 4
PATH_DISTANCE_RELAXED = 5

# Pauling electronegativities.  The substrate domains currently contain
# organic main-group elements; unsupported elements remain explicit in the
# diagnostics rather than silently receiving a guessed value.
PAULING_EN = {
    "H": 2.20,
    "B": 2.04,
    "C": 2.55,
    "N": 3.04,
    "O": 3.44,
    "F": 3.98,
    "Si": 1.90,
    "P": 2.19,
    "S": 2.58,
    "Cl": 3.16,
    "Br": 2.96,
    "I": 2.66,
}
EN_ELEMENTS = ("B", "C", "N", "O", "F", "Si", "P", "S", "Cl", "Br", "I")

# These are deliberately coarse ordinal priors.  They are not presented as
# calculated bond dissociation energies and are frozen before any outcome
# comparison.  The relative ordering is the useful part of the acquisition
# representation; target-vs-competitor gaps are more robust than absolutes.
BDE_BASE = {
    "primary_aliphatic": 101.0,
    "secondary_aliphatic": 98.0,
    "tertiary_aliphatic": 96.0,
    "benzylic": 85.0,
    "allylic": 87.0,
    "alpha_hetero_O": 92.0,
    "alpha_hetero_N": 91.0,
    "alpha_hetero_S": 89.0,
    "alpha_hetero_other": 94.0,
    "carbonyl_alpha": 96.0,
    "aryl": 111.0,
    "unknown": 103.0,
}

BDE_CLASS_BINS = (
    (85.0, "very_low"),
    (92.0, "low"),
    (100.0, "moderate"),
    (108.0, "high"),
    (float("inf"), "very_high"),
)

VERSION_BLOCKS = {
    "v0": (),
    "v1": ("bde", "electronic"),
    "v2": ("bde", "electronic", "flexibility"),
    "v3": ("bde", "electronic", "flexibility", "steric_topology", "polarity", "site_ambiguity"),
    # V4 and V5 deliberately branch from V1 so the new blocks can be
    # diagnosed independently of the broad V2/V3 additions. V6 combines the
    # targeted V4/V5 blocks with a local reaction-centre regime block.
    "v4": ("bde", "electronic", "reaction_contrast"),
    "v5": ("bde", "electronic", "path_accessibility"),
    "v6": ("bde", "electronic", "reaction_contrast", "path_accessibility", "local_regime"),
}

ALL_BLOCKS = (
    "bde",
    "electronic",
    "flexibility",
    "steric_topology",
    "polarity",
    "site_ambiguity",
    "reaction_contrast",
    "path_accessibility",
    "local_regime",
)

BASE_COVERAGE_DIMENSIONS = (
    "pathway_id",
    "bde",
    "electronic",
    "flexibility",
    "steric_topology",
    "site_ambiguity",
)


@dataclass(frozen=True)
class SiteInfo:
    atom_map_id: int | None
    atom_index: int
    site_type: str
    hydrogen_count: int
    path_distance: int | None
    class_name: str
    estimated_bde: float | None
    bde_class: str
    bde_confidence: str
    bde_corrections: dict[str, float]


@dataclass
class RuleFeatureRow:
    substrate_id: str
    smiles: str
    pathway_id: str
    family_id: str
    target_atom_map_id: int | None
    target_atom_index: int | None
    numeric: dict[str, float]
    categorical: dict[str, str]
    blocks: dict[str, dict[str, float]]
    sites: list[dict[str, Any]]
    diagnostics: list[str] = field(default_factory=list)

    def vector(self, version: str) -> dict[str, float]:
        values: dict[str, float] = {}
        for block in blocks_for_version(version):
            values.update(self.blocks.get(block, {}))
        return values

    def as_json(self, version: str = RULE_VERSION) -> dict[str, Any]:
        if not is_valid_version_spec(version):
            raise ValueError(f"unsupported rule feature version: {version}")
        return {
            "schema_version": SCHEMA_VERSION,
            "rule_version": version,
            "substrate_id": self.substrate_id,
            "structure": {"atom_mapped_substrate_smiles": self.smiles},
            "pathway_id": self.pathway_id,
            "family_id": self.family_id,
            "target_atom_map_id": self.target_atom_map_id,
            "target_atom_index": self.target_atom_index,
            "feature_blocks": self.blocks,
            "numeric_features": self.numeric,
            "categorical_features": self.categorical,
            "candidate_site_records": self.sites,
            "diagnostics": self.diagnostics,
            "provenance": {
                "method": "frozen_2d_graph_rules",
                "quantum_calculation": False,
                "label_derived_parameters": False,
                "electronegativity": "Pauling",
                "bde_interpretation": "coarse ordinal prior, not calculated energy",
            },
        }


@dataclass
class RuleFeatureTable:
    rows: list[RuleFeatureRow]
    block_names: dict[str, list[str]]

    @property
    def ids(self) -> list[str]:
        return [row.substrate_id for row in self.rows]

    @property
    def families(self) -> list[str]:
        return [row.family_id for row in self.rows]

    @property
    def pathways(self) -> list[str]:
        return [row.pathway_id for row in self.rows]

    def matrix(self, version: str, scaled: bool = False) -> np.ndarray:
        names = sorted({name for row in self.rows for name in row.vector(version)})
        matrix = np.asarray([[row.vector(version).get(name, 0.0) for name in names] for row in self.rows], dtype=float)
        return scale_matrix(matrix, names) if scaled else matrix

    def names(self, version: str) -> list[str]:
        return sorted({name for row in self.rows for name in row.vector(version)})


def canonical_version_spec(version: str) -> str:
    """Return a stable version label for one named version or a feature union."""
    value = version.strip().lower()
    if value == "v0":
        return value
    tokens = tuple(token for token in value.split("+") if token)
    if not tokens or any(token not in MIXABLE_VERSIONS for token in tokens) or len(set(tokens)) != len(tokens):
        raise ValueError(f"unsupported rule feature version: {version}")
    ordered = sorted(set(tokens), key=MIXABLE_VERSIONS.index)
    return "+".join(ordered)


def is_valid_version_spec(version: str) -> bool:
    try:
        canonical_version_spec(version)
    except (AttributeError, ValueError):
        return False
    return True


def blocks_for_version(version: str) -> tuple[str, ...]:
    """Return the union of blocks for a named version or V1--V6 mixture."""
    canonical = canonical_version_spec(version)
    if canonical in VERSION_BLOCKS:
        return VERSION_BLOCKS[canonical]
    blocks: list[str] = []
    for token in canonical.split("+"):
        for block in VERSION_BLOCKS[token]:
            if block not in blocks:
                blocks.append(block)
    return tuple(blocks)


def feature_mixture_versions(mode: str = "all") -> list[str]:
    """Generate explicit V1--V6 unions for a prefix or exhaustive study."""
    if mode == "prefixes":
        return ["+".join(MIXABLE_VERSIONS[:index]) for index in range(1, len(MIXABLE_VERSIONS) + 1)]
    if mode != "all":
        raise ValueError(f"unknown feature mixture mode: {mode}")
    return [
        "+".join(combination)
        for size in range(1, len(MIXABLE_VERSIONS) + 1)
        for combination in itertools.combinations(MIXABLE_VERSIONS, size)
    ]


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


def pathway_id(record: dict[str, Any]) -> str:
    explicit = first_present(record, ("pathway_id",), ("pathway",), ("reaction_center", "pathway_id"))
    if explicit is not None:
        return str(explicit)
    linkage = str(first_present(record, ("structure", "azide_nitrene_precursor_linkage")) or "")
    family = family_id(record).lower()
    if "sulfonyl" in linkage.lower() or "sulfonyl" in family:
        return "sulfonyl"
    return "aryl"


def atom_map_index(molecule: Chem.Mol, atom_map_id: int | None) -> int | None:
    if atom_map_id is None:
        return None
    return next((atom.GetIdx() for atom in molecule.GetAtoms() if atom.GetAtomMapNum() == int(atom_map_id)), None)


def proximal_nitrene_index(molecule: Chem.Mol) -> int | None:
    candidates = []
    for atom in molecule.GetAtoms():
        if atom.GetAtomicNum() != 7:
            continue
        neighbours = list(atom.GetNeighbors())
        has_nitrogen_neighbour = any(neighbour.GetAtomicNum() == 7 for neighbour in neighbours)
        has_carbon_or_sulfur_neighbour = any(neighbour.GetAtomicNum() in {6, 16} for neighbour in neighbours)
        if has_nitrogen_neighbour and has_carbon_or_sulfur_neighbour:
            candidates.append(atom.GetIdx())
    return candidates[0] if len(candidates) == 1 else (candidates[0] if candidates else None)


def heavy_atom_indices(molecule: Chem.Mol) -> list[int]:
    return [atom.GetIdx() for atom in molecule.GetAtoms() if atom.GetAtomicNum() > 1]


def shortest_path(molecule: Chem.Mol, first: int | None, second: int | None) -> tuple[int, ...] | None:
    if first is None or second is None:
        return None
    try:
        path = tuple(int(index) for index in Chem.GetShortestPath(molecule, first, second))
    except (IndexError, ValueError):
        return None
    if any(molecule.GetAtomWithIdx(index).GetAtomicNum() == 1 for index in path):
        return None
    return path


def path_distance(molecule: Chem.Mol, first: int | None, second: int | None) -> int | None:
    if first is None or second is None:
        return None
    path = shortest_path(molecule, first, second)
    return len(path) - 1 if path else None


def atom_has_hydrogen(atom: Chem.Atom) -> bool:
    return atom.GetAtomicNum() == 6 and atom.GetTotalNumHs() > 0


def site_records(record: dict[str, Any], molecule: Chem.Mol) -> list[dict[str, Any]]:
    reaction_center = record.get("reaction_center", {})
    supplied = reaction_center.get("candidate_sites", [])
    if supplied:
        return [dict(site) for site in supplied]
    output = []
    for atom in molecule.GetAtoms():
        if atom_has_hydrogen(atom) and not atom.GetIsAromatic():
            output.append(
                {
                    "atom_map_id": atom.GetAtomMapNum() or None,
                    "atom_index": atom.GetIdx(),
                    "hydrogen_count": int(atom.GetTotalNumHs()),
                    "site_type": "inferred_non_aromatic",
                }
            )
    return output


def infer_site_class(molecule: Chem.Mol, atom_index: int) -> tuple[str, dict[str, Any]]:
    atom = molecule.GetAtomWithIdx(atom_index)
    if atom.GetIsAromatic():
        return "aryl", {}
    neighbours = [neighbour for neighbour in atom.GetNeighbors() if neighbour.GetAtomicNum() > 1]
    aromatic_neighbour = any(neighbour.GetIsAromatic() for neighbour in neighbours)
    carbonyl_neighbour = False
    carbonyl_element = None
    alpha_hetero = None
    unsaturated_neighbour = False
    for neighbour in neighbours:
        if neighbour.GetAtomicNum() in {7, 8, 16, 9, 17, 35, 53}:
            alpha_hetero = neighbour.GetSymbol()
        if neighbour.GetAtomicNum() == 6:
            for bond in neighbour.GetBonds():
                other = bond.GetOtherAtom(neighbour)
                if other.GetAtomicNum() == 8 and bond.GetBondType() == Chem.BondType.DOUBLE:
                    carbonyl_neighbour = True
                    carbonyl_element = "O"
            if any(bond.GetBondType() in {Chem.BondType.DOUBLE, Chem.BondType.TRIPLE} for bond in neighbour.GetBonds()):
                unsaturated_neighbour = True
    degree = len(neighbours)
    if carbonyl_neighbour:
        class_name = "carbonyl_alpha"
    elif alpha_hetero is not None:
        class_name = f"alpha_hetero_{alpha_hetero if alpha_hetero in {'N', 'O', 'S'} else 'other'}"
    elif aromatic_neighbour:
        class_name = "benzylic"
    elif unsaturated_neighbour:
        class_name = "allylic"
    elif degree <= 1:
        class_name = "primary_aliphatic"
    elif degree == 2:
        class_name = "secondary_aliphatic"
    else:
        class_name = "tertiary_aliphatic"
    ring_sizes = [len(ring) for ring in molecule.GetRingInfo().AtomRings() if atom_index in ring]
    return class_name, {
        "degree": degree,
        "aromatic_neighbour": aromatic_neighbour,
        "carbonyl_neighbour": carbonyl_neighbour,
        "carbonyl_element": carbonyl_element,
        "alpha_hetero": alpha_hetero,
        "ring_sizes": ring_sizes,
        "ring_member": bool(ring_sizes),
        "hydrogen_count": int(atom.GetTotalNumHs()),
    }


def bond_order(bond: Chem.Bond | None) -> float:
    if bond is None:
        return 1.0
    return float(bond.GetBondTypeAsDouble())


def bde_class(value: float) -> str:
    for upper, label in BDE_CLASS_BINS:
        if value <= upper:
            return label
    return "very_high"


def estimate_bde(
    molecule: Chem.Mol,
    atom_index: int,
    shells: dict[int, list[int]],
) -> tuple[float, str, str, dict[str, float], str]:
    class_name, context = infer_site_class(molecule, atom_index)
    corrections: dict[str, float] = {}
    estimate = BDE_BASE.get(class_name, BDE_BASE["unknown"])
    if context.get("ring_sizes"):
        smallest_ring = min(context["ring_sizes"])
        if smallest_ring <= 3:
            corrections["small_ring_strain"] = 4.0
        elif smallest_ring == 4:
            corrections["four_membered_ring_strain"] = 2.0
        if context.get("degree", 0) >= 3:
            corrections["ring_substitution"] = 1.0
    if context.get("carbonyl_neighbour"):
        corrections["carbonyl_context"] = -2.0
    if context.get("alpha_hetero") in {"O", "N", "S"}:
        corrections["alpha_hetero_context"] = -1.0
    direct = shells.get(1, [])
    direct_pull = sum(
        max(0.0, PAULING_EN.get(molecule.GetAtomWithIdx(index).GetSymbol(), PAULING_EN["C"]) - PAULING_EN["C"])
        for index in direct
    )
    if direct_pull > 0.8:
        corrections["direct_electronegativity_pull"] = -min(3.0, 0.75 * direct_pull)
    estimate += sum(corrections.values())
    confidence = "high" if class_name != "unknown" and PAULING_EN.get(molecule.GetAtomWithIdx(atom_index).GetSymbol()) else "medium"
    if class_name == "unknown":
        confidence = "low"
    bounded = float(np.clip(estimate, 70.0, 115.0))
    return bounded, bde_class(bounded), confidence, corrections, class_name


def shell_atoms(molecule: Chem.Mol, target_index: int) -> dict[int, list[int]]:
    heavy = set(heavy_atom_indices(molecule))
    output: dict[int, list[int]] = {}
    for index in heavy:
        if index == target_index:
            continue
        distance = path_distance(molecule, target_index, index)
        if distance in SHELL_DISTANCES:
            output.setdefault(int(distance), []).append(index)
    return output


def shell_feature_values(
    molecule: Chem.Mol,
    target_index: int,
    proximal_index: int | None,
) -> dict[str, float]:
    shells = shell_atoms(molecule, target_index)
    target_en = PAULING_EN.get(molecule.GetAtomWithIdx(target_index).GetSymbol(), PAULING_EN["C"])
    tether_path = set(shortest_path(molecule, target_index, proximal_index) or ())
    features: dict[str, float] = {}
    total_pull = 0.0
    for distance in SHELL_DISTANCES:
        indices = shells.get(distance, [])
        values = [PAULING_EN.get(molecule.GetAtomWithIdx(index).GetSymbol()) for index in indices]
        values = [value for value in values if value is not None]
        deltas = [value - target_en for value in values]
        prefix = f"shell_{distance}"
        features[f"{prefix}_atom_count"] = float(len(indices))
        features[f"{prefix}_mean_delta_en"] = float(np.mean(deltas)) if deltas else 0.0
        features[f"{prefix}_min_delta_en"] = float(np.min(deltas)) if deltas else 0.0
        features[f"{prefix}_max_delta_en"] = float(np.max(deltas)) if deltas else 0.0
        features[f"{prefix}_spread_delta_en"] = float(np.ptp(deltas)) if deltas else 0.0
        features[f"{prefix}_positive_pull"] = float(sum(max(0.0, delta) for delta in deltas))
        features[f"{prefix}_negative_pull"] = float(sum(min(0.0, delta) for delta in deltas))
        features[f"{prefix}_formal_charge_sum"] = float(sum(molecule.GetAtomWithIdx(index).GetFormalCharge() for index in indices))
        features[f"{prefix}_hetero_count"] = float(sum(molecule.GetAtomWithIdx(index).GetAtomicNum() not in {6, 1} for index in indices))
        features[f"{prefix}_aromatic_count"] = float(sum(molecule.GetAtomWithIdx(index).GetIsAromatic() for index in indices))
        features[f"{prefix}_ring_count"] = float(sum(molecule.GetAtomWithIdx(index).IsInRing() for index in indices))
        features[f"{prefix}_tether_count"] = float(sum(index in tether_path for index in indices))
        for element in EN_ELEMENTS:
            features[f"{prefix}_element_{element}"] = float(
                sum(molecule.GetAtomWithIdx(index).GetSymbol() == element for index in indices)
            )
        for index in indices:
            if distance == 1:
                local_bond = molecule.GetBondBetweenAtoms(target_index, index)
                local_weight = bond_order(local_bond)
            else:
                local_weight = 1.0
            total_pull += max(0.0, PAULING_EN.get(molecule.GetAtomWithIdx(index).GetSymbol(), target_en) - target_en) * local_weight / distance
    features["electronic_pull_total"] = float(total_pull)
    return features


def bond_flexibility(molecule: Chem.Mol, first: int, second: int) -> float:
    bond = molecule.GetBondBetweenAtoms(first, second)
    if bond is None or bond.IsInRing() or bond.GetIsAromatic() or bond.GetBondType() != Chem.BondType.SINGLE:
        return 0.0
    first_atom = molecule.GetAtomWithIdx(first)
    second_atom = molecule.GetAtomWithIdx(second)
    if first_atom.GetIsAromatic() or second_atom.GetIsAromatic():
        return 0.0
    if any(
        neighbour.GetAtomicNum() == 8
        and molecule.GetBondBetweenAtoms(atom.GetIdx(), neighbour.GetIdx()) is not None
        and molecule.GetBondBetweenAtoms(atom.GetIdx(), neighbour.GetIdx()).GetBondType() == Chem.BondType.DOUBLE
        for atom in (first_atom, second_atom)
        for neighbour in atom.GetNeighbors()
    ):
        return 0.0
    if any(
        any(neighbour.GetAtomicNum() == 6 and neighbour.GetIsAromatic() for neighbour in atom.GetNeighbors())
        for atom in (first_atom, second_atom)
    ):
        return 0.25
    if first_atom.GetDegree() >= 3 or second_atom.GetDegree() >= 3:
        return 0.5
    return 1.0


def flexibility_features(molecule: Chem.Mol, target_index: int, proximal_index: int | None) -> dict[str, float]:
    path = shortest_path(molecule, proximal_index, target_index) if proximal_index is not None else None
    path_values = [bond_flexibility(molecule, first, second) for first, second in zip(path or (), (path or ())[1:])]
    global_values = [
        bond_flexibility(molecule, bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
        for bond in molecule.GetBonds()
    ]
    rotatable = [value for value in global_values if value > 0.0]
    path_length = len(path) - 1 if path else 0
    return {
        "tether_path_length": float(path_length),
        "tether_rotatable_bond_count": float(sum(value >= 1.0 for value in path_values)),
        "tether_effective_rotors": float(sum(path_values)),
        "tether_flexibility_fraction": float(sum(path_values) / max(1, len(path_values))),
        "tether_bottleneck_flexibility": float(min(path_values)) if path_values else 0.0,
        "global_rotatable_bond_count": float(len(rotatable)),
        "global_effective_rotors": float(sum(global_values)),
    }


def graph_diameter(molecule: Chem.Mol) -> int:
    indices = heavy_atom_indices(molecule)
    distances = []
    for first in indices:
        for second in indices:
            if first < second:
                distance = path_distance(molecule, first, second)
                if distance is not None:
                    distances.append(distance)
    return max(distances, default=0)


def local_steric_features(molecule: Chem.Mol, target_index: int) -> dict[str, float]:
    shells = shell_atoms(molecule, target_index)
    shell_one = shells.get(1, [])
    shell_two = shells.get(2, [])
    return {
        "target_heavy_degree": float(sum(neighbour.GetAtomicNum() > 1 for neighbour in molecule.GetAtomWithIdx(target_index).GetNeighbors())),
        "target_ring_member": float(molecule.GetAtomWithIdx(target_index).IsInRing()),
        "shell_1_branch_count": float(sum(molecule.GetAtomWithIdx(index).GetDegree() >= 3 for index in shell_one)),
        "shell_2_branch_count": float(sum(molecule.GetAtomWithIdx(index).GetDegree() >= 3 for index in shell_two)),
        "shell_1_ring_count": float(sum(molecule.GetAtomWithIdx(index).IsInRing() for index in shell_one)),
        "steric_shielding_score": float(
            0.5 * molecule.GetAtomWithIdx(target_index).GetDegree()
            + 0.25 * sum(molecule.GetAtomWithIdx(index).GetDegree() >= 3 for index in shell_one)
            + 0.25 * sum(molecule.GetAtomWithIdx(index).IsInRing() for index in shell_one)
        ),
    }


def topology_features(molecule: Chem.Mol) -> dict[str, float]:
    heavy = len(heavy_atom_indices(molecule))
    bonds = sum(1 for bond in molecule.GetBonds() if bond.GetBeginAtom().GetAtomicNum() > 1 and bond.GetEndAtom().GetAtomicNum() > 1)
    components = len(Chem.GetMolFrags(molecule))
    ring_info = molecule.GetRingInfo().AtomRings()
    multi_ring_atoms = sum(
        sum(index in ring for ring in ring_info) > 1 for index in heavy_atom_indices(molecule)
    )
    return {
        "heavy_atom_count": float(heavy),
        "ring_count": float(rdMolDescriptors.CalcNumRings(molecule)),
        "aromatic_ring_count": float(rdMolDescriptors.CalcNumAromaticRings(molecule)),
        "aliphatic_ring_count": float(rdMolDescriptors.CalcNumAliphaticRings(molecule)),
        "spiro_atom_count": float(rdMolDescriptors.CalcNumSpiroAtoms(molecule)),
        "cycle_rank": float(max(0, bonds - heavy + components)),
        "fused_ring_atom_count": float(multi_ring_atoms),
        "graph_diameter": float(graph_diameter(molecule)),
        "fraction_csp3": float(rdMolDescriptors.CalcFractionCSP3(molecule)),
        "murcko_scaffold_present": float(bool(MurckoScaffold.MurckoScaffoldSmiles(mol=molecule))),
    }


def polarity_features(molecule: Chem.Mol, target_index: int) -> dict[str, float]:
    shells = shell_atoms(molecule, target_index)
    local = shells.get(1, []) + shells.get(2, [])
    return {
        "global_hbond_acceptors": float(Lipinski.NumHAcceptors(molecule)),
        "global_hbond_donors": float(Lipinski.NumHDonors(molecule)),
        "global_hetero_atoms": float(rdMolDescriptors.CalcNumHeteroatoms(molecule)),
        "global_formal_charge": float(Chem.GetFormalCharge(molecule)),
        "local_hbond_like_hetero_count": float(sum(molecule.GetAtomWithIdx(index).GetAtomicNum() not in {6, 1} for index in local)),
        "local_oxygen_count": float(sum(molecule.GetAtomWithIdx(index).GetAtomicNum() == 8 for index in local)),
        "local_nitrogen_count": float(sum(molecule.GetAtomWithIdx(index).GetAtomicNum() == 7 for index in local)),
        "local_sulfur_count": float(sum(molecule.GetAtomWithIdx(index).GetAtomicNum() == 16 for index in local)),
        "local_halogen_count": float(sum(molecule.GetAtomWithIdx(index).GetAtomicNum() in {9, 17, 35, 53} for index in local)),
    }


ROLE_FEATURES = (
    "hetero_count",
    "aromatic_count",
    "ring_count",
    "branch_count",
    "multiple_bond_count",
    "positive_charge_count",
    "negative_charge_count",
    "tether_count",
)


def shell_role_features(
    molecule: Chem.Mol,
    site_index: int,
    proximal_index: int | None,
) -> dict[str, float]:
    """Return atom-role counts around a site without depending on atom order."""

    shells = shell_atoms(molecule, site_index)
    tether_path = set(shortest_path(molecule, site_index, proximal_index) or ())
    features: dict[str, float] = {}
    for distance in SHELL_DISTANCES:
        indices = shells.get(distance, [])
        for role in ROLE_FEATURES:
            count = 0
            for index in indices:
                atom = molecule.GetAtomWithIdx(index)
                if role == "hetero_count":
                    count += atom.GetAtomicNum() not in {1, 6}
                elif role == "aromatic_count":
                    count += atom.GetIsAromatic()
                elif role == "ring_count":
                    count += atom.IsInRing()
                elif role == "branch_count":
                    count += atom.GetDegree() >= 3
                elif role == "multiple_bond_count":
                    count += any(bond.GetBondTypeAsDouble() > 1.0 for bond in atom.GetBonds())
                elif role == "positive_charge_count":
                    count += atom.GetFormalCharge() > 0
                elif role == "negative_charge_count":
                    count += atom.GetFormalCharge() < 0
                elif role == "tether_count":
                    count += index in tether_path
            features[f"shell_{distance}_{role}"] = float(count)
    return features


def reaction_contrast_features(
    molecule: Chem.Mol,
    target_index: int,
    proximal_index: int | None,
    sites: Sequence[SiteInfo],
    target_site: SiteInfo,
) -> dict[str, float]:
    """Compare the target site's local roles and BDE landscape with competitors."""

    usable = [site for site in sites if site.estimated_bde is not None and site.site_type != "aryl"]
    competitors = [site for site in usable if site.atom_index != target_site.atom_index]
    competitor_bdes = [float(site.estimated_bde) for site in competitors if site.estimated_bde is not None]
    target_bde = float(target_site.estimated_bde or 0.0)
    competitor_mean = float(np.mean(competitor_bdes)) if competitor_bdes else target_bde
    competitor_min = float(min(competitor_bdes)) if competitor_bdes else target_bde
    competitor_max = float(max(competitor_bdes)) if competitor_bdes else target_bde
    target_roles = shell_role_features(molecule, target_index, proximal_index)
    competitor_roles = [shell_role_features(molecule, site.atom_index, proximal_index) for site in competitors]
    features = {
        "contrast_competitor_count": float(len(competitors)),
        "contrast_competitor_bde_mean": competitor_mean,
        "contrast_competitor_bde_min": competitor_min,
        "contrast_competitor_bde_spread": competitor_max - competitor_min,
        "contrast_target_vs_competitor_bde_mean_delta": target_bde - competitor_mean,
        "contrast_target_vs_competitor_bde_min_delta": target_bde - competitor_min,
        "contrast_competitor_bde_within_3_count": float(sum(value <= target_bde + 3.0 for value in competitor_bdes)),
        "contrast_competitor_bde_within_5_count": float(sum(value <= target_bde + 5.0 for value in competitor_bdes)),
    }
    for name, value in target_roles.items():
        features[f"contrast_target_{name}"] = value
        competitor_values = [role_values.get(name, 0.0) for role_values in competitor_roles]
        competitor_value = float(np.mean(competitor_values)) if competitor_values else value
        features[f"contrast_competitor_{name}_mean"] = competitor_value
        features[f"contrast_target_vs_competitor_{name}_delta"] = value - competitor_value
    return features


def path_accessibility_summary(
    molecule: Chem.Mol,
    proximal_index: int | None,
    site_index: int,
) -> dict[str, float]:
    """Estimate local closure accessibility from fixed graph path rules."""

    path = shortest_path(molecule, proximal_index, site_index)
    if not path or len(path) < 2:
        return {
            "length": 0.0,
            "effective_rotors": 0.0,
            "flexibility_fraction": 0.0,
            "bottleneck_flexibility": 0.0,
            "ring_locked_bond_count": 0.0,
            "branch_count": 0.0,
            "conjugated_bond_count": 0.0,
            "accessibility_score": 0.0,
        }
    values = [bond_flexibility(molecule, first, second) for first, second in zip(path, path[1:])]
    length = len(values)
    bonds = [molecule.GetBondBetweenAtoms(first, second) for first, second in zip(path, path[1:])]
    ring_locked = sum(
        value == 0.0 and bond is not None and (bond.IsInRing() or bond.GetIsAromatic())
        for value, bond in zip(values, bonds)
    )
    branches = sum(molecule.GetAtomWithIdx(index).GetDegree() >= 3 for index in path[1:-1])
    conjugated = sum(value == 0.25 for value in values)
    flexibility_fraction = float(sum(values) / max(1, length))
    lock_fraction = float(ring_locked / max(1, length))
    branch_fraction = float(min(1.0, branches / max(1, len(path) - 2)))
    accessibility = float(np.clip(0.6 * flexibility_fraction + 0.2 * (1.0 - lock_fraction) + 0.2 * (1.0 - branch_fraction), 0.0, 1.0))
    return {
        "length": float(length),
        "effective_rotors": float(sum(values)),
        "flexibility_fraction": flexibility_fraction,
        "bottleneck_flexibility": float(min(values)),
        "ring_locked_bond_count": float(ring_locked),
        "branch_count": float(branches),
        "conjugated_bond_count": float(conjugated),
        "accessibility_score": accessibility,
    }


def path_accessibility_features(
    molecule: Chem.Mol,
    target_index: int,
    proximal_index: int | None,
    sites: Sequence[SiteInfo],
    target_site: SiteInfo,
) -> dict[str, float]:
    """Return target-path accessibility and target-versus-competitor contrasts."""

    usable = [site for site in sites if site.site_type != "aryl"]
    target_summary = path_accessibility_summary(molecule, proximal_index, target_index)
    competitor_summaries = [
        path_accessibility_summary(molecule, proximal_index, site.atom_index)
        for site in usable
        if site.atom_index != target_site.atom_index
    ]
    features = {
        f"path_target_{name}": value for name, value in target_summary.items()
    }
    features["path_competitor_count"] = float(len(competitor_summaries))
    for name in ("accessibility_score", "effective_rotors", "flexibility_fraction", "bottleneck_flexibility", "ring_locked_bond_count", "branch_count"):
        values = [summary[name] for summary in competitor_summaries]
        mean_value = float(np.mean(values)) if values else target_summary[name]
        features[f"path_competitor_{name}_mean"] = mean_value
        features[f"path_target_vs_competitor_{name}_delta"] = target_summary[name] - mean_value
    return features


def local_regime_features(
    molecule: Chem.Mol,
    target_index: int,
    proximal_index: int | None,
    sites: Sequence[SiteInfo],
    target_site: SiteInfo,
) -> dict[str, float]:
    """Summarize local steric and polarity contrasts without global descriptors."""

    def context(site_index: int) -> dict[str, float]:
        steric = local_steric_features(molecule, site_index)
        polarity = polarity_features(molecule, site_index)
        return {
            "steric_shielding": steric["steric_shielding_score"],
            "local_hetero_count": polarity["local_hbond_like_hetero_count"],
            "local_oxygen_count": polarity["local_oxygen_count"],
            "local_nitrogen_count": polarity["local_nitrogen_count"],
            "local_sulfur_count": polarity["local_sulfur_count"],
            "local_halogen_count": polarity["local_halogen_count"],
        }

    target_context = context(target_index)
    competitors = [
        context(site.atom_index)
        for site in sites
        if site.atom_index != target_site.atom_index and site.site_type != "aryl"
    ]
    features: dict[str, float] = {f"regime_target_{name}": value for name, value in target_context.items()}
    for name, value in target_context.items():
        competitor_values = [candidate.get(name, 0.0) for candidate in competitors]
        competitor_value = float(np.mean(competitor_values)) if competitor_values else value
        features[f"regime_competitor_{name}_mean"] = competitor_value
        features[f"regime_target_vs_competitor_{name}_delta"] = value - competitor_value
    features["regime_competitor_count"] = float(len(competitors))
    return features


def accessibility_class(score: float) -> str:
    return "locked" if score < 0.2 else "restricted" if score < 0.55 else "permissive"


def competition_class(gap: float, competitor_count: float) -> str:
    if competitor_count <= 0.0:
        return "no_competitor"
    return "near_tie" if gap <= 3.0 else "moderate_gap" if gap <= 7.0 else "clear_gap"


def pull_class(value: float) -> str:
    return "low_pull" if value < 0.5 else "medium_pull" if value < 1.5 else "high_pull"


def steric_class(value: float) -> str:
    return "open" if value < 1.0 else "moderate" if value < 2.0 else "shielded"


def nearest_competitor_summary(sites: Sequence[SiteInfo], target_map_id: int | None) -> dict[str, float | str]:
    usable = [site for site in sites if site.estimated_bde is not None and site.site_type != "aryl"]
    target = next((site for site in usable if site.atom_map_id == target_map_id), None)
    competitors = [site for site in usable if site.atom_map_id != target_map_id]
    if target is None:
        minimum = min((site.estimated_bde for site in usable), default=0.0)
        return {
            "target_bde": float(minimum),
            "target_bde_rank": 0.0,
            "bde_competition_gap": 0.0,
            "near_tie_competitor_count": float(sum(site.estimated_bde <= minimum + 5.0 for site in competitors)),
            "bde_confidence_code": 0.0,
        }
    ordered = sorted(usable, key=lambda site: (site.estimated_bde or float("inf"), site.atom_map_id or -1))
    competitor_values = [site.estimated_bde for site in competitors if site.estimated_bde is not None]
    confidence_code = {"low": 0.0, "medium": 0.5, "high": 1.0}[target.bde_confidence]
    return {
        "target_bde": float(target.estimated_bde or 0.0),
        "target_bde_rank": float(next((index for index, site in enumerate(ordered, start=1) if site.atom_map_id == target_map_id), 0)),
        "bde_competition_gap": float((target.estimated_bde or 0.0) - min(competitor_values)) if competitor_values else 0.0,
        "near_tie_competitor_count": float(sum(value <= (target.estimated_bde or 0.0) + 5.0 for value in competitor_values)),
        "bde_confidence_code": confidence_code,
    }


def scale_range(name: str) -> tuple[float, float]:
    if name.startswith("contrast_"):
        if "delta" in name:
            return -30.0, 30.0
        if "bde_mean" in name or "bde_min" in name:
            return 70.0, 115.0
        if "bde_spread" in name:
            return 0.0, 30.0
        return 0.0, 20.0
    if name.startswith("path_"):
        if "fraction" in name or "bottleneck" in name or "accessibility" in name:
            return 0.0, 1.0
        return 0.0, 20.0
    if name.startswith("regime_"):
        if "delta" in name:
            return -20.0, 20.0
        return 0.0, 20.0
    if "bde" in name and "class" not in name:
        if "gap" in name:
            return 0.0, 30.0
        if "rank" in name:
            return 1.0, 20.0
        return 70.0, 115.0
    if "delta_en" in name or "electronic_pull" in name or "formal_charge" in name:
        return -4.0, 4.0
    if "flexibility_fraction" in name or "confidence_code" in name:
        return 0.0, 1.0
    if "fraction" in name:
        return 0.0, 1.0
    if "degree" in name or "count" in name or "rotat" in name or "path_length" in name or "diameter" in name:
        return 0.0, 20.0
    if "score" in name:
        return 0.0, 20.0
    return 0.0, 20.0


def scale_matrix(matrix: np.ndarray, names: Sequence[str]) -> np.ndarray:
    if matrix.size == 0:
        return matrix.astype(float)
    scaled = np.zeros_like(matrix, dtype=float)
    for column, name in enumerate(names):
        low, high = scale_range(name)
        scaled[:, column] = np.clip((matrix[:, column] - low) / (high - low), 0.0, 1.0)
    return scaled


def make_rule_feature_row(record: dict[str, Any]) -> RuleFeatureRow:
    substrate_id = record_id(record)
    smiles = substrate_smiles(record)
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"{substrate_id}: invalid substrate SMILES")
    pathway = pathway_id(record)
    family = family_id(record)
    proximal = proximal_nitrene_index(molecule)
    diagnostics: list[str] = []
    if proximal is None:
        diagnostics.append("missing_unique_proximal_nitrene_atom")
    supplied_target = first_present(record, ("reaction_center", "reported_reactive_site", "atom_map_id"))
    target_map_id = int(supplied_target) if supplied_target is not None else None
    target_index = atom_map_index(molecule, target_map_id)
    candidates = site_records(record, molecule)
    if target_index is None:
        if target_map_id is not None:
            diagnostics.append("reported_target_atom_map_not_found")
        target_candidates = []
        for candidate in candidates:
            candidate_index = atom_map_index(molecule, candidate.get("atom_map_id"))
            if candidate_index is None:
                candidate_index = candidate.get("atom_index")
            if candidate_index is None or not atom_has_hydrogen(molecule.GetAtomWithIdx(candidate_index)):
                continue
            distance = path_distance(molecule, proximal, candidate_index)
            if distance in {PATH_DISTANCE_PRIMARY, PATH_DISTANCE_RELAXED}:
                target_candidates.append((abs((distance or 0) - PATH_DISTANCE_PRIMARY), candidate_index, candidate))
        if target_candidates:
            _, target_index, inferred = sorted(target_candidates, key=lambda value: (value[0], value[1]))[0]
            target_map_id = int(inferred.get("atom_map_id")) if inferred.get("atom_map_id") is not None else None
            diagnostics.append("target_inferred_from_pathway_template")
        else:
            diagnostics.append("no_reaction_template_target_site")
    if target_index is None:
        fallback = next(
            (atom.GetIdx() for atom in molecule.GetAtoms() if atom_has_hydrogen(atom) and not atom.GetIsAromatic()),
            None,
        )
        target_index = fallback
        if fallback is not None:
            diagnostics.append("target_fallback_used_for_descriptive_features")
    if target_index is None:
        raise ValueError(f"{substrate_id}: no carbon-hydrogen site is available")

    shell_map = shell_atoms(molecule, target_index)
    site_infos: list[SiteInfo] = []
    for candidate in candidates:
        candidate_map = candidate.get("atom_map_id")
        candidate_index = atom_map_index(molecule, candidate_map)
        if candidate_index is None:
            candidate_index = candidate.get("atom_index")
        if candidate_index is None:
            diagnostics.append(f"candidate_site_map_not_found:{candidate_map}")
            continue
        atom = molecule.GetAtomWithIdx(candidate_index)
        if atom.GetAtomicNum() != 6:
            continue
        class_name, _ = infer_site_class(molecule, candidate_index)
        estimate, estimate_class, confidence, corrections, inferred_class = estimate_bde(molecule, candidate_index, shell_atoms(molecule, candidate_index))
        site_infos.append(
            SiteInfo(
                atom_map_id=int(candidate_map) if candidate_map is not None else None,
                atom_index=candidate_index,
                site_type=str(candidate.get("site_type", inferred_class)),
                hydrogen_count=int(candidate.get("hydrogen_count", atom.GetTotalNumHs())),
                path_distance=path_distance(molecule, proximal, candidate_index),
                class_name=class_name,
                estimated_bde=estimate,
                bde_class=estimate_class,
                bde_confidence=confidence,
                bde_corrections=corrections,
            )
        )
    if not site_infos:
        diagnostics.append("no_candidate_site_records")
    target_site = next((site for site in site_infos if site.atom_index == target_index), None)
    if target_site is None:
        target_class, _ = infer_site_class(molecule, target_index)
        target_estimate, target_class_bin, target_confidence, target_corrections, target_class_name = estimate_bde(
            molecule, target_index, shell_atoms(molecule, target_index)
        )
        target_site = SiteInfo(
            atom_map_id=target_map_id,
            atom_index=target_index,
            site_type=target_class,
            hydrogen_count=int(molecule.GetAtomWithIdx(target_index).GetTotalNumHs()),
            path_distance=path_distance(molecule, proximal, target_index),
            class_name=target_class_name,
            estimated_bde=target_estimate,
            bde_class=target_class_bin,
            bde_confidence=target_confidence,
            bde_corrections=target_corrections,
        )
        site_infos.append(target_site)
    competitor = nearest_competitor_summary(site_infos, target_site.atom_map_id)
    electronic = shell_feature_values(molecule, target_index, proximal)
    bde_block = {
        "target_estimated_bde": float(target_site.estimated_bde or 0.0),
        "target_bde_rank": float(competitor["target_bde_rank"]),
        "bde_competition_gap": float(competitor["bde_competition_gap"]),
        "near_tie_competitor_count": float(competitor["near_tie_competitor_count"]),
        "bde_confidence_code": float(competitor["bde_confidence_code"]),
        "candidate_site_count": float(len(site_infos)),
        "non_aromatic_candidate_site_count": float(sum(site.site_type != "aryl" for site in site_infos)),
    }
    flexibility = flexibility_features(molecule, target_index, proximal)
    steric = local_steric_features(molecule, target_index)
    topology = topology_features(molecule)
    polarity = polarity_features(molecule, target_index)
    ambiguity = {
        "target_path_distance": float(path_distance(molecule, proximal, target_index) or 0),
        "primary_path_candidate_count": float(sum(site.path_distance == PATH_DISTANCE_PRIMARY for site in site_infos)),
        "relaxed_path_candidate_count": float(sum(site.path_distance == PATH_DISTANCE_RELAXED for site in site_infos)),
        "equivalent_target_hydrogen_count": float(target_site.hydrogen_count),
        "site_ambiguity_score": float(
            min(
                1.0,
                (max(0, len(site_infos) - 1) + float(competitor["near_tie_competitor_count"])) / 8.0,
            )
        ),
    }
    reaction_contrast = reaction_contrast_features(molecule, target_index, proximal, site_infos, target_site)
    path_accessibility = path_accessibility_features(molecule, target_index, proximal, site_infos, target_site)
    local_regime = local_regime_features(molecule, target_index, proximal, site_infos, target_site)
    numeric = {}
    for block in (
        bde_block,
        electronic,
        flexibility,
        steric,
        topology,
        polarity,
        ambiguity,
        reaction_contrast,
        path_accessibility,
        local_regime,
    ):
        numeric.update(block)
    target_accessibility = path_accessibility["path_target_accessibility_score"]
    target_pull = electronic["electronic_pull_total"]
    target_steric = local_regime["regime_target_steric_shielding"]
    categorical = {
        "pathway_id": pathway,
        "target_bde_class": target_site.bde_class,
        "target_bde_confidence": target_site.bde_confidence,
        "target_site_class": target_site.class_name,
        "tether_flexibility_class": (
            "locked" if flexibility["tether_effective_rotors"] == 0.0 else
            "restricted" if flexibility["tether_flexibility_fraction"] < 0.5 else
            "flexible"
        ),
        "topology_class": (
            "acyclic" if topology["ring_count"] == 0 else
            "fused_or_spiro" if topology["fused_ring_atom_count"] > 0 or topology["spiro_atom_count"] > 0 else
            "ring_containing"
        ),
        "reaction_competition_class": competition_class(
            bde_block["bde_competition_gap"],
            reaction_contrast["contrast_competitor_count"],
        ),
        "path_accessibility_class": accessibility_class(target_accessibility),
        "local_reactivity_regime": (
            f"{target_site.bde_class}|{pull_class(target_pull)}|"
            f"{accessibility_class(target_accessibility)}|{steric_class(target_steric)}"
        ),
    }
    serialized_sites = [
        {
            "atom_map_id": site.atom_map_id,
            "atom_index": site.atom_index,
            "site_type": site.site_type,
            "hydrogen_count": site.hydrogen_count,
            "path_distance": site.path_distance,
            "class_name": site.class_name,
            "estimated_bde": site.estimated_bde,
            "bde_class": site.bde_class,
            "bde_confidence": site.bde_confidence,
            "bde_corrections": site.bde_corrections,
        }
        for site in site_infos
    ]
    return RuleFeatureRow(
        substrate_id=substrate_id,
        smiles=smiles,
        pathway_id=pathway,
        family_id=family,
        target_atom_map_id=target_map_id,
        target_atom_index=target_index,
        numeric=numeric,
        categorical=categorical,
        blocks={
            "bde": bde_block,
            "electronic": electronic,
            "flexibility": flexibility,
            "steric_topology": {**steric, **topology},
            "polarity": polarity,
            "site_ambiguity": ambiguity,
            "reaction_contrast": reaction_contrast,
            "path_accessibility": path_accessibility,
            "local_regime": local_regime,
        },
        sites=serialized_sites,
        diagnostics=diagnostics,
    )


def build_rule_feature_table(records: Sequence[dict[str, Any]]) -> RuleFeatureTable:
    rows = [make_rule_feature_row(record) for record in records]
    names = {block: sorted({name for row in rows for name in row.blocks.get(block, {})}) for block in ALL_BLOCKS}
    return RuleFeatureTable(rows=rows, block_names=names)


def category_key(row: RuleFeatureRow, block: str) -> str:
    if block == "bde":
        return row.categorical.get("target_bde_class", "unknown")
    if block == "electronic":
        pull = row.numeric.get("electronic_pull_total", 0.0)
        return "low_pull" if pull < 0.5 else "medium_pull" if pull < 1.5 else "high_pull"
    if block == "flexibility":
        return row.categorical.get("tether_flexibility_class", "unknown")
    if block == "steric_topology":
        return row.categorical.get("topology_class", "unknown")
    if block == "site_ambiguity":
        score = row.numeric.get("site_ambiguity_score", 0.0)
        return "clear" if score < 0.25 else "ambiguous" if score < 0.6 else "highly_ambiguous"
    if block == "reaction_contrast":
        return row.categorical.get("reaction_competition_class", "unknown")
    if block == "path_accessibility":
        return row.categorical.get("path_accessibility_class", "unknown")
    if block == "local_regime":
        return row.categorical.get("local_reactivity_regime", "unknown")
    return row.pathway_id


def rule_novelty_scores(
    table: RuleFeatureTable,
    candidates: Sequence[int],
    selected: Sequence[int],
    version: str,
) -> np.ndarray:
    if not is_valid_version_spec(version):
        raise ValueError(f"unsupported rule feature version: {version}")
    if not candidates:
        return np.asarray([], dtype=float)
    if not selected:
        return np.ones(len(candidates), dtype=float)
    blocks = blocks_for_version(version)
    if not blocks:
        return np.zeros(len(candidates), dtype=float)
    distances = []
    for block in blocks:
        names = table.block_names.get(block, [])
        if not names:
            distances.append(np.zeros(len(candidates), dtype=float))
            continue
        matrix = np.asarray([[row.blocks.get(block, {}).get(name, 0.0) for name in names] for row in table.rows], dtype=float)
        scaled = scale_matrix(matrix, names)
        block_distances = []
        for candidate in candidates:
            nearest = min(float(np.mean(np.abs(scaled[candidate] - scaled[index]))) for index in selected)
            block_distances.append(nearest)
        distances.append(np.asarray(block_distances, dtype=float))
    return np.mean(np.vstack(distances), axis=0)


def rule_coverage_scores(
    table: RuleFeatureTable,
    candidates: Sequence[int],
    selected: Sequence[int],
    version: str | None = None,
) -> np.ndarray:
    if not candidates:
        return np.asarray([], dtype=float)
    if not selected:
        return np.ones(len(candidates), dtype=float)
    dimensions = coverage_dimensions_for_version(version)
    scores = []
    for candidate in candidates:
        values = []
        candidate_row = table.rows[candidate]
        for dimension in dimensions:
            if dimension == "pathway_id":
                candidate_key = candidate_row.pathway_id
                selected_keys = [table.rows[index].pathway_id for index in selected]
            else:
                candidate_key = category_key(candidate_row, dimension)
                selected_keys = [category_key(table.rows[index], dimension) for index in selected]
            count = selected_keys.count(candidate_key)
            values.append(1.0 if count == 0 else 1.0 / (1.0 + count))
        scores.append(float(np.mean(values)))
    return np.asarray(scores, dtype=float)


def coverage_dimensions_for_version(version: str | None) -> list[str]:
    """Return rule-category coverage dimensions without changing V0--V3."""
    if version is None:
        return list(BASE_COVERAGE_DIMENSIONS)
    dimensions = list(BASE_COVERAGE_DIMENSIONS)
    blocks = blocks_for_version(version)
    if "reaction_contrast" in blocks:
        dimensions.append("reaction_contrast")
    if "path_accessibility" in blocks:
        dimensions.append("path_accessibility")
    if "local_regime" in blocks:
        dimensions.append("local_regime")
    return dimensions


FATAL_DIAGNOSTICS = {
    "missing_unique_proximal_nitrene_atom",
    "reported_target_atom_map_not_found",
    "no_reaction_template_target_site",
    "no_candidate_site_records",
}


def rank_candidate_records(
    candidate_records: Sequence[dict[str, Any]],
    selected_records: Sequence[dict[str, Any]] = (),
    version: str = RULE_VERSION,
    pathway: str | None = None,
) -> list[dict[str, Any]]:
    """Rank unlabelled candidates and return an auditable explanation table."""

    if version not in SUPPORTED_VERSIONS or version == "v0":
        raise ValueError("library ranking requires v1 through v6 rule features")
    selected_table = build_rule_feature_table(selected_records) if selected_records else RuleFeatureTable([], {})
    candidate_table = build_rule_feature_table(candidate_records)
    combined = RuleFeatureTable(
        rows=[*selected_table.rows, *candidate_table.rows],
        block_names={
            block: sorted(
                {
                    name
                    for row in [*selected_table.rows, *candidate_table.rows]
                    for name in row.blocks.get(block, {})
                }
            )
            for block in ALL_BLOCKS
        },
    )
    selected_indices = list(range(len(selected_table.rows)))
    candidate_indices = list(range(len(selected_table.rows), len(combined.rows)))
    if pathway is not None:
        candidate_indices = [index for index in candidate_indices if combined.rows[index].pathway_id == pathway]
    novelty = rule_novelty_scores(combined, candidate_indices, selected_indices, version)
    coverage = rule_coverage_scores(combined, candidate_indices, selected_indices, version)
    rows = []
    for position, index in enumerate(candidate_indices):
        feature_row = combined.rows[index]
        fatal = sorted(set(feature_row.diagnostics) & FATAL_DIAGNOSTICS)
        rows.append(
            {
                "substrate_id": feature_row.substrate_id,
                "pathway_id": feature_row.pathway_id,
                "family_id": feature_row.family_id,
                "status": "unsupported" if fatal else "ranked",
                "diagnostics": ";".join(feature_row.diagnostics),
                "diversity_score": None if fatal else float(0.8 * novelty[position] + 0.2 * coverage[position]),
                "chemical_novelty_score": None if fatal else float(novelty[position]),
                "chemical_coverage_score": None if fatal else float(coverage[position]),
                "target_estimated_bde": feature_row.numeric.get("target_estimated_bde"),
                "target_bde_class": feature_row.categorical.get("target_bde_class"),
                "bde_competition_gap": feature_row.numeric.get("bde_competition_gap"),
                "tether_effective_rotors": feature_row.numeric.get("tether_effective_rotors"),
                "tether_flexibility_class": feature_row.categorical.get("tether_flexibility_class"),
                "site_ambiguity_score": feature_row.numeric.get("site_ambiguity_score"),
                "reaction_competition_class": feature_row.categorical.get("reaction_competition_class"),
                "path_accessibility_class": feature_row.categorical.get("path_accessibility_class"),
                "local_reactivity_regime": feature_row.categorical.get("local_reactivity_regime"),
                "contrast_target_vs_competitor_bde_mean_delta": feature_row.numeric.get("contrast_target_vs_competitor_bde_mean_delta"),
                "path_target_accessibility_score": feature_row.numeric.get("path_target_accessibility_score"),
                "regime_target_vs_competitor_steric_shielding_delta": feature_row.numeric.get("regime_target_vs_competitor_steric_shielding_delta"),
            }
        )
    return sorted(rows, key=lambda row: (row["status"] != "ranked", -(row["diversity_score"] or -1.0), row["substrate_id"]))


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_rule_features(records: Sequence[dict[str, Any]], output: Path, version: str = RULE_VERSION) -> RuleFeatureTable:
    table = build_rule_feature_table(records)
    write_jsonl(output, (row.as_json(version=version) for row in table.rows))
    return table


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", choices=SUPPORTED_VERSIONS, default=RULE_VERSION)
    parser.add_argument("--selected-records", type=Path)
    parser.add_argument("--ranking-output", type=Path)
    parser.add_argument("--pathway", choices=["aryl", "sulfonyl"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = [json.loads(line) for line in args.records.read_text(encoding="utf-8").splitlines() if line.strip()]
    table = write_rule_features(records, args.output, args.version)
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "rule_version": args.version,
        "record_count": len(table.rows),
        "output": str(args.output),
    }
    if args.ranking_output is not None:
        selected = []
        if args.selected_records is not None:
            selected = [json.loads(line) for line in args.selected_records.read_text(encoding="utf-8").splitlines() if line.strip()]
        ranking = rank_candidate_records(records, selected, args.version, args.pathway)
        args.ranking_output.parent.mkdir(parents=True, exist_ok=True)
        with args.ranking_output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(ranking[0]) if ranking else ["substrate_id", "status"])
            writer.writeheader()
            writer.writerows(ranking)
        report["ranking_output"] = str(args.ranking_output)
        report["ranked_count"] = sum(row["status"] == "ranked" for row in ranking)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

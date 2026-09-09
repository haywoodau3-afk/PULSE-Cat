"""Reusable, low-capacity primitives for the PPTL computational study.

This module intentionally keeps the experimental unit at one whole substrate.
It supports the generic nested reaction-record shapes used by the repository,
but does not fabricate missing chemistry, poses, or outcomes.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors
from rdkit.Chem import rdFingerprintGenerator
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler


DESCRIPTOR_NAMES = (
    "heavy_atom_count",
    "molecular_weight",
    "logp",
    "tpsa",
    "formal_charge",
    "fraction_csp3",
    "rotatable_bonds",
    "rings",
    "aromatic_rings",
    "h_bond_acceptors",
    "h_bond_donors",
    "hetero_atoms",
    "aliphatic_rings",
    "spiro_atoms",
    "chiral_centers",
)
MINIMAL_DESCRIPTOR_NAMES = (
    "molecular_weight",
    "logp",
    "tpsa",
    "fraction_csp3",
    "rotatable_bonds",
    "rings",
)
FEATURE_ARMS = {
    "B0",
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    "P0",
    "P1",
    "P2",
    "P3",
    "P4",
}
PERCENT_BOUNDS = (0.0, 100.0)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read object rows, failing closed on malformed JSONL."""

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"JSONL row at {path}:{line_number} must be an object")
        rows.append(value)
    return rows


def _first(record: Mapping[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        value: Any = record
        for key in path:
            if not isinstance(value, Mapping) or key not in value:
                value = None
                break
            value = value[key]
        if value not in (None, ""):
            return value
    return None


def record_id(record: Mapping[str, Any]) -> str:
    value = _first(
        record,
        ("substrate_id",),
        ("compound_id",),
        ("paper_substrate_id",),
        ("substrate", "paper_substrate_id"),
    )
    if value is None:
        raise ValueError("reaction record is missing a substrate/compound identifier")
    return str(value)


def catalyst_id(record: Mapping[str, Any]) -> str | None:
    value = _first(record, ("catalyst_id",), ("catalyst", "catalyst_id"))
    return str(value) if value is not None else None


def family_id(record: Mapping[str, Any]) -> str:
    value = _first(record, ("family_id",), ("family", "family_id"), ("family", "family_label"))
    return str(value) if value is not None else "unknown-family"


def split_group(record: Mapping[str, Any]) -> str:
    value = _first(record, ("split_group",), ("compound_id",), ("substrate_id",))
    return str(value) if value is not None else record_id(record)


def pathway_id(record: Mapping[str, Any]) -> str:
    value = _first(record, ("pathway_id",), ("reaction", "pathway_id"))
    return str(value) if value is not None else "unknown-pathway"


def canonical_smiles(value: str) -> str:
    molecule = Chem.MolFromSmiles(value)
    if molecule is None:
        raise ValueError(f"invalid SMILES: {value}")
    # Atom-map labels identify reaction bookkeeping, not compound identity.
    # Clear them before canonicalization so mapped records match across papers.
    for atom in molecule.GetAtoms():
        atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(molecule)


def smiles(record: Mapping[str, Any]) -> str:
    value = _first(
        record,
        ("structure", "atom_mapped_substrate_smiles"),
        ("substrate", "atom_mapped_substrate_smiles"),
        ("atom_mapped_substrate_smiles",),
        ("structure", "smiles"),
        ("substrate", "smiles"),
        ("substrate", "azide_smiles"),
        ("structure", "azide_smiles"),
        ("smiles",),
    )
    if value is None:
        raise ValueError(f"{record_id(record)}: missing substrate SMILES")
    value = str(value)
    if Chem.MolFromSmiles(value) is None:
        raise ValueError(f"{record_id(record)}: invalid substrate SMILES")
    return value


def outcome_value(record: Mapping[str, Any], target: str) -> float | None:
    key = "ee_percent" if target == "ee_percent" else "isolated_yield_percent"
    value = _first(record, ("outcome", key), (key,), ("target_value",))
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) and 0.0 <= value <= 100.0 else None


def outcome_status(record: Mapping[str, Any], target: str) -> str | None:
    key = "ee_status" if target == "ee_percent" else "yield_status"
    return _first(record, ("outcome", key), (key,))


def canonical_overlap(left: Sequence[ReactionRow], right: Sequence[ReactionRow]) -> dict[str, dict[str, str]]:
    """Map canonical compound identity to IDs in two catalyst domains."""

    left_map = {canonical_smiles(row.smiles): row.substrate_id for row in left}
    right_map = {canonical_smiles(row.smiles): row.substrate_id for row in right}
    return {
        key: {"left_id": left_map[key], "right_id": right_map[key]}
        for key in sorted(set(left_map) & set(right_map))
    }


def remove_canonical_overlap(source: Sequence[ReactionRow], target: Sequence[ReactionRow]) -> list[ReactionRow]:
    """Remove source chemistry that appears in the target domain."""

    target_keys = {canonical_smiles(row.smiles) for row in target}
    return [row for row in source if canonical_smiles(row.smiles) not in target_keys]


@dataclass(frozen=True)
class ReactionRow:
    """One substrate-level reaction observation or masked candidate."""

    substrate_id: str
    smiles: str
    family_id: str
    split_group: str
    pathway_id: str
    catalyst_id: str | None
    source_order: int
    record: dict[str, Any]

    def value(self, target: str) -> float | None:
        return outcome_value(self.record, target)


def load_reaction_rows(
    path: Path,
    *,
    catalyst: str | None = None,
    pathway: str | None = None,
    target: str | None = None,
    include_unlabelled: bool = True,
    pose_features_path: Path | None = None,
    catalyst_features_path: Path | None = None,
) -> list[ReactionRow]:
    """Load one row per substrate, preserving explicit missing outcomes."""

    pose_map = {record_id(row): row for row in read_jsonl(pose_features_path)} if pose_features_path else {}
    catalyst_map = _aggregate_feature_records(read_jsonl(catalyst_features_path)) if catalyst_features_path else {}
    rows: list[ReactionRow] = []
    seen: set[str] = set()
    for order, record in enumerate(read_jsonl(path)):
        row_catalyst = catalyst_id(record)
        if catalyst is not None and row_catalyst != catalyst:
            continue
        if pathway is not None and pathway_id(record) != pathway:
            continue
        if target is not None and not include_unlabelled and outcome_value(record, target) is None:
            continue
        substrate_id = record_id(record)
        if substrate_id in seen:
            raise ValueError(f"duplicate substrate-level record: {substrate_id}")
        seen.add(substrate_id)
        joined_record = dict(record)
        feature_blocks = dict(record.get("feature_blocks", {})) if isinstance(record.get("feature_blocks"), Mapping) else {}
        pose_record = pose_map.get(substrate_id)
        if pose_record is not None and isinstance(pose_record.get("feature_blocks"), Mapping):
            feature_blocks.update(pose_record["feature_blocks"])
        catalyst_record = catalyst_map.get(substrate_id)
        if catalyst_record is not None and isinstance(catalyst_record.get("feature_blocks"), Mapping):
            feature_blocks.update(catalyst_record["feature_blocks"])
        if feature_blocks:
            joined_record["feature_blocks"] = feature_blocks
        rows.append(
            ReactionRow(
                substrate_id=substrate_id,
                smiles=smiles(record),
                family_id=family_id(record),
                split_group=split_group(record),
                pathway_id=pathway_id(record),
                catalyst_id=row_catalyst,
                source_order=order,
                record=joined_record,
            )
        )
    if not rows:
        raise ValueError(f"no reaction rows loaded from {path}")
    return rows


def _aggregate_feature_records(records: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Aggregate repeated pose-interaction rows to one substrate-level record.

    Interaction files contain many ranked poses per substrate. Keeping the last
    pose would make the feature feed order-dependent. Numeric feature leaves
    are therefore averaged within substrate; labels and identifiers are never
    read from these records.
    """

    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record_id(record), []).append(record)
    output: dict[str, dict[str, Any]] = {}
    for substrate_id, group in grouped.items():
        merged = dict(group[0])
        block_names = sorted({str(name) for row in group if isinstance(row.get("feature_blocks"), Mapping) for name in row["feature_blocks"]})
        blocks: dict[str, Any] = {}
        for block_name in block_names:
            leaves: dict[str, list[float]] = {}
            for row in group:
                block = row.get("feature_blocks", {}).get(block_name) if isinstance(row.get("feature_blocks"), Mapping) else None
                for leaf, value in flatten_numeric(block).items():
                    leaves.setdefault(leaf, []).append(float(value))
            blocks[block_name] = {leaf: float(np.mean(values)) for leaf, values in leaves.items()}
        if blocks:
            merged["feature_blocks"] = blocks
        output[substrate_id] = merged
    return output


def flatten_numeric(value: Any, prefix: str = "") -> dict[str, float]:
    output: dict[str, float] = {}
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            output.update(flatten_numeric(child, child_prefix))
    elif isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
        output[prefix] = float(value)
    return output


def pose_features(record: Mapping[str, Any]) -> dict[str, float]:
    """Extract persisted Stage 2p features without treating pose rows as labels."""

    blocks = record.get("feature_blocks")
    if isinstance(blocks, Mapping):
        return flatten_numeric(
            {key: value for key, value in blocks.items() if str(key).startswith("stage2p")},
            "stage2p",
        )
    for key in ("stage2p_features", "features"):
        value = record.get(key)
        if isinstance(value, Mapping):
            return flatten_numeric(value, "stage2p")
    return {}


def catalyst_aware_features(record: Mapping[str, Any]) -> dict[str, float]:
    """Extract an explicitly catalyst-aware geometry block when persisted."""

    for key in ("catalyst_aware_features", "catalyst_aware_geometry", "interaction_features"):
        value = record.get(key)
        if isinstance(value, Mapping):
            return flatten_numeric(value, "catalyst_aware")
    blocks = record.get("feature_blocks")
    if isinstance(blocks, Mapping):
        for key, value in blocks.items():
            if "catalyst" in str(key).lower() or "interaction" in str(key).lower():
                return flatten_numeric(value, "catalyst_aware")
    return {}


def compact_catalyst_features(record: Mapping[str, Any]) -> dict[str, float]:
    """Select a small C2 catalyst-contact block from aggregated interactions."""

    values = catalyst_aware_features(record)
    selected_tokens = {
        "fe_n_distance_angstrom",
        "fe_n_reported_c_angle_degrees",
        "fe_reported_c_transferred_h_angle_degrees",
        "fe_to_reported_c_distance_angstrom",
        "fe_to_transferred_h_distance_angstrom",
        "minimum_core_substrate_distance_angstrom",
        "core_substrate_distance_count_lt_2p5_angstrom",
        "core_substrate_distance_count_lt_3p0_angstrom",
        "reported_c_to_core_distance_mean",
        "reported_c_to_core_distance_min",
        "transferred_h_to_core_distance_mean",
        "transferred_h_to_core_distance_min",
        "substrate_centroid_to_fe_distance_angstrom",
        "substrate_centroid_to_porphyrin_plane_signed_distance_angstrom",
        "uff_pose_score",
        "core_substrate_covalent_floor_clash_count",
    }
    return {name: value for name, value in values.items() if name.rsplit(".", 1)[-1] in selected_tokens}


def _descriptor_values(mol: Chem.Mol) -> dict[str, float]:
    values = {
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
    return values


def _morgan(mol: Chem.Mol, bits: int) -> np.ndarray:
    fingerprint = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=bits).GetFingerprint(mol)
    values = np.zeros(bits, dtype=float)
    DataStructs.ConvertToNumpyArray(fingerprint, values)
    return values


def _pose_matrix(rows: Sequence[ReactionRow]) -> tuple[list[str], np.ndarray]:
    maps = [pose_features(row.record) for row in rows]
    names = sorted({name for values in maps for name in values})
    if not names:
        return [], np.empty((len(rows), 0), dtype=float)
    return names, np.asarray([[values.get(name, 0.0) for name in names] for values in maps], dtype=float)


def compact_pose_features(record: Mapping[str, Any]) -> dict[str, float]:
    """Select a compact, interpretable Stage 2p C1 block.

    The raw 248-column block remains available for diagnostics. C1 retains
    reaction-corridor, directional-contrast, and low/high-pose distribution
    summaries while excluding redundant element-channel expansions.
    """

    values = pose_features(record)
    selected: dict[str, float] = {}
    for name, value in values.items():
        token = name.split("stage2p:", 1)[-1]
        keep = (
            token.startswith("directional_symmetry:")
            or token.startswith("directional_antisymmetry:")
            or (token.startswith(("n_to_h:", "h_to_n:")) and ":all_heavy:" in token and any(f":{field}:" in token for field in ("axial_mean", "axial_q90", "corridor_fraction")))
            or (token.startswith(("nitrene:all_heavy:", "hydrogen:all_heavy:")) and any(f":{field}:" in token for field in ("radial_mean", "radial_q90")))
            or token.startswith("relation:")
        )
        if keep:
            selected[name] = float(value)
    return selected


def _compact_pose_matrix(rows: Sequence[ReactionRow]) -> tuple[list[str], np.ndarray]:
    maps = [compact_pose_features(row.record) for row in rows]
    names = sorted({name for values in maps for name in values})
    if not names:
        return [], np.empty((len(rows), 0), dtype=float)
    return names, np.asarray([[values.get(name, 0.0) for name in names] for values in maps], dtype=float)


def _catalyst_matrix(rows: Sequence[ReactionRow]) -> tuple[list[str], np.ndarray]:
    maps = [compact_catalyst_features(row.record) for row in rows]
    names = sorted({name for values in maps for name in values})
    if not names:
        return [], np.empty((len(rows), 0), dtype=float)
    return names, np.asarray([[values.get(name, 0.0) for name in names] for values in maps], dtype=float)


def build_feature_matrix(rows: Sequence[ReactionRow], arm: str) -> tuple[np.ndarray, list[str]]:
    """Build a deterministic matrix for one frozen representation arm."""

    if arm not in FEATURE_ARMS:
        raise ValueError(f"unknown feature arm: {arm}")
    descriptors = [_descriptor_values(Chem.MolFromSmiles(row.smiles)) for row in rows]
    pose_names, pose_matrix = _pose_matrix(rows)
    compact_pose_names, compact_pose_matrix = _compact_pose_matrix(rows)
    catalyst_names, catalyst_matrix = _catalyst_matrix(rows)
    descriptor_names = MINIMAL_DESCRIPTOR_NAMES if arm in {"B1", "P1"} else DESCRIPTOR_NAMES
    descriptor_matrix = np.asarray([[values[name] for name in descriptor_names] for values in descriptors], dtype=float)
    bits = {"B3": 128, "B4": 256, "B5": 1024}.get(arm, 1024)
    morgan_matrix = np.asarray([_morgan(Chem.MolFromSmiles(row.smiles), bits) for row in rows], dtype=float)
    morgan_names = [f"morgan_{index:04d}" for index in range(bits)]
    if arm == "B0":
        return np.empty((len(rows), 0), dtype=float), []
    if arm in {"B1", "B2"}:
        return descriptor_matrix, list(descriptor_names)
    if arm in {"B3", "B4", "B5"}:
        return np.column_stack([descriptor_matrix, morgan_matrix]), list(descriptor_names) + morgan_names
    if arm == "P0":
        if not pose_names:
            raise ValueError("P0 requires persisted Stage 2p pose features")
        return pose_matrix, pose_names
    if arm == "P1":
        if not pose_names:
            raise ValueError("P1 requires persisted Stage 2p pose features")
        return np.column_stack([descriptor_matrix, pose_matrix]), list(descriptor_names) + pose_names
    if arm == "P2":
        if not pose_names:
            raise ValueError("P2 requires persisted Stage 2p pose features")
        full = np.column_stack([np.asarray([[values[name] for name in DESCRIPTOR_NAMES] for values in descriptors]), morgan_matrix])
        return np.column_stack([full, pose_matrix]), list(DESCRIPTOR_NAMES) + morgan_names + pose_names
    if arm == "P3":
        if not compact_pose_names:
            raise ValueError("P3 requires persisted Stage 2p pose features")
        full = np.column_stack([np.asarray([[values[name] for name in DESCRIPTOR_NAMES] for values in descriptors]), morgan_matrix])
        return np.column_stack([full, compact_pose_matrix]), list(DESCRIPTOR_NAMES) + morgan_names + compact_pose_names
    if arm == "P4":
        if not catalyst_names:
            raise ValueError(f"{arm} requires persisted catalyst-aware geometry features")
        if not compact_pose_names:
            raise ValueError("P4 requires persisted Stage 2p pose features")
        full = np.column_stack([np.asarray([[values[name] for name in DESCRIPTOR_NAMES] for values in descriptors]), morgan_matrix])
        columns = [full, compact_pose_matrix, catalyst_matrix]
        names = list(DESCRIPTOR_NAMES) + morgan_names + compact_pose_names + catalyst_names
        return np.column_stack(columns), names
    raise ValueError(f"feature arm {arm} needs a catalyst-aware feature provider")


def fit_ridge(X: np.ndarray, y: np.ndarray, alpha: float = 10.0) -> tuple[StandardScaler | None, Ridge]:
    if len(y) == 0:
        raise ValueError("cannot fit without labelled rows")
    if X.shape[1] == 0:
        return None, Ridge(alpha=alpha).fit(np.zeros((len(y), 1)), y)
    scaler = StandardScaler()
    model = Ridge(alpha=alpha, solver="lsqr")
    model.fit(scaler.fit_transform(X), y)
    return scaler, model


def predict_ridge(fitted: tuple[StandardScaler | None, Ridge], X: np.ndarray) -> np.ndarray:
    scaler, model = fitted
    transformed = np.zeros((len(X), 1), dtype=float) if scaler is None else scaler.transform(X)
    return np.clip(np.asarray(model.predict(transformed), dtype=float), *PERCENT_BOUNDS)


def _row_matrix(rows: Sequence[ReactionRow], arm: str) -> tuple[np.ndarray, list[str]]:
    return build_feature_matrix(rows, arm)


def _fit_target(rows: Sequence[ReactionRow], target: str, arm: str, alpha: float) -> tuple[tuple[StandardScaler | None, Ridge], list[str]]:
    labelled = [row for row in rows if row.value(target) is not None]
    if not labelled:
        raise ValueError(f"no labelled {target} rows")
    X, names = _row_matrix(labelled, arm)
    y = np.asarray([row.value(target) for row in labelled], dtype=float)
    return fit_ridge(X, y, alpha), names


def _feature_alignment(rows: Sequence[ReactionRow], names: Sequence[str], arm: str) -> np.ndarray:
    X, actual = _row_matrix(rows, arm)
    if list(actual) != list(names):
        positions = {name: index for index, name in enumerate(actual)}
        return np.column_stack([X[:, positions[name]] if name in positions else np.zeros(len(rows)) for name in names])
    return X


def _source_target_prediction(
    source: Sequence[ReactionRow], target_train: Sequence[ReactionRow], target_test: Sequence[ReactionRow], target_name: str, arm: str, alpha: float
) -> dict[str, np.ndarray]:
    labelled_target = [row for row in target_train if row.value(target_name) is not None]
    labelled_source = [row for row in source if row.value(target_name) is not None]
    if not labelled_source:
        raise ValueError("source expert needs labelled source rows")
    source_X, names = _row_matrix(labelled_source, arm)
    source_y = np.asarray([row.value(target_name) for row in labelled_source], dtype=float)
    source_model = fit_ridge(source_X, source_y, alpha)
    test_X = _feature_alignment(target_test, names, arm)
    predictions: dict[str, np.ndarray] = {"source_zero_shot": predict_ridge(source_model, test_X)}
    if labelled_target:
        target_X = _feature_alignment(labelled_target, names, arm)
        target_y = np.asarray([row.value(target_name) for row in labelled_target], dtype=float)
        pooled_X = np.vstack([source_X, target_X])
        pooled_y = np.concatenate([source_y, target_y])
        domain = np.concatenate([np.zeros(len(source_X)), np.ones(len(target_X))])[:, None]
        pooled_model = fit_ridge(np.column_stack([pooled_X, domain]), pooled_y, alpha)
        predictions["pooled_domain_indicator"] = predict_ridge(
            pooled_model,
            np.column_stack([test_X, np.ones(len(test_X))]),
        )
        target_model = fit_ridge(target_X, target_y, alpha)
        predictions["target_only"] = predict_ridge(target_model, _feature_alignment(target_test, names, arm))
        # Shrink the target coefficients toward the source coefficients in the
        # same standardized coordinate system.  This is a stable closed-form
        # ridge surrogate for the source-coefficient arm.
        source_scaler, source_estimator = source_model
        scaled_target = source_scaler.transform(target_X) if source_scaler is not None else np.zeros((len(target_X), 1))
        scaled_test = source_scaler.transform(test_X) if source_scaler is not None else np.zeros((len(test_X), 1))
        coefficient = source_estimator.coef_.copy()
        target_mean = float(target_y.mean())
        if scaled_target.shape[1] == coefficient.shape[0]:
            coefficient = (scaled_target.T @ scaled_target + 20.0 * np.eye(len(coefficient)))
            coefficient = np.linalg.solve(coefficient, scaled_target.T @ (target_y - target_mean) + 20.0 * source_estimator.coef_)
            predictions["source_coefficient_regularized"] = np.clip(target_mean + scaled_test @ coefficient, *PERCENT_BOUNDS)
        else:
            predictions["source_coefficient_regularized"] = predictions["target_only"]
        source_on_target = predict_ridge(source_model, _feature_alignment(target_train, names, arm))
        residual = target_y - source_on_target
        residual_model = fit_ridge(target_X, residual, alpha)
        predictions["source_prediction_residual"] = np.clip(
            predictions["source_zero_shot"] + predict_ridge(residual_model, test_X), *PERCENT_BOUNDS
        )
    return predictions


@dataclass
class GuardedEnsemble:
    """Online source trust with a target-only safety expert."""

    names: tuple[str, ...] = ("target_only", "p7", "cmcpor", "combined")
    initial_weights: np.ndarray | None = None
    cumulative_loss: np.ndarray | None = None
    scored: int = 0

    def __post_init__(self) -> None:
        if self.initial_weights is None:
            self.initial_weights = np.asarray([0.5, 1 / 6, 1 / 6, 1 / 6], dtype=float)
        if len(self.initial_weights) != len(self.names) or np.any(self.initial_weights < 0):
            raise ValueError("initial ensemble weights must match expert names and be non-negative")
        total = float(np.sum(self.initial_weights))
        if total <= 0:
            raise ValueError("initial ensemble weights must have positive mass")
        self.initial_weights = self.initial_weights / total
        if self.cumulative_loss is None:
            self.cumulative_loss = np.zeros(len(self.names), dtype=float)

    def weights(self) -> np.ndarray:
        assert self.initial_weights is not None and self.cumulative_loss is not None
        eta = math.sqrt(2.0 * math.log(len(self.names)) / max(1, self.scored + 1))
        raw = self.initial_weights * np.exp(-eta * self.cumulative_loss)
        if self.scored < 5:
            raw[1:] = np.minimum(raw[1:], 0.5 * raw[0] / max(1, len(raw) - 1))
        for index in range(1, len(raw)):
            if self.scored >= 5 and self.cumulative_loss[index] - self.cumulative_loss[0] > self.scored * 0.01:
                raw[index] = 0.0
        if float(raw.sum()) <= 0:
            raw[0] = 1.0
        return raw / raw.sum()

    def combine(self, predictions: Mapping[str, float]) -> tuple[float, dict[str, float]]:
        weights = self.weights()
        values = np.asarray([float(predictions[name]) for name in self.names], dtype=float)
        combined = float(np.dot(weights, values))
        return combined, {name: float(weight) for name, weight in zip(self.names, weights)}

    def update(self, predictions: Mapping[str, float], observed: float) -> dict[str, Any]:
        assert self.cumulative_loss is not None
        values = np.asarray([float(predictions[name]) for name in self.names], dtype=float)
        self.cumulative_loss += np.abs(values - float(observed)) / 100.0
        self.scored += 1
        combined, weights = self.combine(predictions)
        return {
            "observed": float(observed),
            "ensemble_prediction": combined,
            "weights": weights,
            "expert_absolute_errors": {name: abs(float(predictions[name]) - float(observed)) for name in self.names},
            "scored": self.scored,
        }


def run_fixed_prefix(
    source: Sequence[ReactionRow],
    target: Sequence[ReactionRow],
    *,
    target_name: str,
    arm: str = "B5",
    seed_size: int = 2,
    alpha: float = 10.0,
    source_domains: Mapping[str, Sequence[ReactionRow]] | None = None,
) -> list[dict[str, Any]]:
    """Evaluate target-only and explicitly named source experts on one route.

    ``source`` remains a backwards-compatible combined source pool. Reciprocal
    runs pass the active source under its canonical ``p7`` or ``cmcpor`` key;
    the inactive expert then falls back to the target-only prediction rather
    than implying that an unavailable domain was supplied.
    """

    active = [row for row in target if row.value(target_name) is not None]
    if len(active) <= seed_size:
        raise ValueError("fixed-prefix evaluation needs more active target rows than its seed")
    ordered = sorted(active, key=lambda row: row.source_order)
    domains = dict(source_domains or {"combined": list(source)})
    combined_source = list(source) if source else [row for values in domains.values() for row in values]
    p7_source = list(domains.get("p7", []))
    cmcpor_source = list(domains.get("cmcpor", []))
    ensemble = GuardedEnsemble()
    output: list[dict[str, Any]] = []
    for prefix_size in range(seed_size, len(ordered)):
        train = ordered[:prefix_size]
        test = [ordered[prefix_size]]
        target_fit, names = _fit_target(train, target_name, arm, alpha)
        test_X = _feature_alignment(test, names, arm)
        predictions: dict[str, float] = {"target_only": float(predict_ridge(target_fit, test_X)[0])}
        combined_predictions = _source_target_prediction(combined_source, train, test, target_name, arm, alpha) if combined_source else {}
        p7_predictions = _source_target_prediction(p7_source, train, test, target_name, arm, alpha) if p7_source else {}
        cmcpor_predictions = _source_target_prediction(cmcpor_source, train, test, target_name, arm, alpha) if cmcpor_source else {}
        predictions["source_zero_shot"] = float(combined_predictions.get("source_zero_shot", np.asarray([predictions["target_only"]]))[0])
        predictions["pooled_domain_indicator"] = float(combined_predictions.get("pooled_domain_indicator", np.asarray([predictions["target_only"]]))[0])
        predictions["source_coefficient_regularized"] = float(combined_predictions.get("source_coefficient_regularized", np.asarray([predictions["target_only"]]))[0])
        predictions["source_prediction_residual"] = float(combined_predictions.get("source_prediction_residual", np.asarray([predictions["target_only"]]))[0])
        predictions["p7_expert"] = float(p7_predictions.get("source_zero_shot", np.asarray([predictions["target_only"]]))[0])
        predictions["cmcpor_expert"] = float(cmcpor_predictions.get("source_zero_shot", np.asarray([predictions["target_only"]]))[0])
        expert_predictions = {
            "target_only": predictions["target_only"],
            "p7": predictions["p7_expert"],
            "cmcpor": predictions["cmcpor_expert"],
            "combined": predictions.get("pooled_domain_indicator", predictions["target_only"]),
        }
        combined, weights = ensemble.combine(expert_predictions)
        observed = float(test[0].value(target_name))
        update = ensemble.update(expert_predictions, observed)
        output.append(
            {
                "target": target_name,
                "feature_arm": arm,
                "prefix_size": prefix_size,
                "test_substrate_id": test[0].substrate_id,
                "observed": observed,
                "predictions": predictions,
                "ensemble_prediction_before_update": combined,
                "weights_before_update": weights,
                "weights_after_update": update["weights"],
                "ensemble_absolute_error": abs(combined - observed),
            }
        )
    return output


def curve_metrics(rows: Iterable[Mapping[str, Any]], prediction_key: str = "ensemble_prediction_before_update") -> dict[str, float | int | None]:
    values = list(rows)
    if not values:
        return {"count": 0, "mae": None, "auc_mae": None}
    errors = np.asarray([abs(float(row[prediction_key]) - float(row["observed"])) for row in values], dtype=float)
    return {
        "count": int(len(errors)),
        "mae": float(np.mean(errors)),
        "auc_mae": float(np.trapezoid(errors, np.asarray([row["prefix_size"] for row in values], dtype=float))),
    }


def prediction_metrics(rows: Iterable[Mapping[str, Any]], expert: str = "target_only") -> dict[str, float | int | None]:
    """Calculate prefix metrics for one expert stored in a replay row."""

    values = list(rows)
    if not values:
        return {"count": 0, "mae": None, "auc_mae": None}
    errors = np.asarray(
        [abs(float(row["predictions"][expert]) - float(row["observed"])) for row in values],
        dtype=float,
    )
    return {
        "count": int(len(errors)),
        "mae": float(np.mean(errors)),
        "auc_mae": float(np.trapezoid(errors, np.asarray([row["prefix_size"] for row in values], dtype=float))),
    }


__all__ = [
    "DESCRIPTOR_NAMES",
    "FEATURE_ARMS",
    "GuardedEnsemble",
    "MINIMAL_DESCRIPTOR_NAMES",
    "ReactionRow",
    "build_feature_matrix",
    "compact_pose_features",
    "compact_catalyst_features",
    "canonical_overlap",
    "canonical_smiles",
    "curve_metrics",
    "load_reaction_rows",
    "run_fixed_prefix",
    "prediction_metrics",
    "remove_canonical_overlap",
]

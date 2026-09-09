"""Auditable uncertainty-plus-diversity acquisition for PPTL candidates."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator


def _minmax(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return values
    low, high = float(np.min(values)), float(np.max(values))
    return np.zeros_like(values) if high <= low else (values - low) / (high - low)


def _fingerprints(smiles: Sequence[str], bits: int = 1024) -> list[Any]:
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=bits)
    output = []
    for value in smiles:
        molecule = Chem.MolFromSmiles(value)
        if molecule is None:
            raise ValueError(f"invalid candidate SMILES: {value}")
        output.append(generator.GetFingerprint(molecule))
    return output


def novelty_scores(candidate_smiles: Sequence[str], selected_smiles: Sequence[str], bits: int = 1024) -> np.ndarray:
    candidates = _fingerprints(candidate_smiles, bits)
    if not selected_smiles:
        return np.ones(len(candidates), dtype=float)
    selected = _fingerprints(selected_smiles, bits)
    return np.asarray([1.0 - max(DataStructs.TanimotoSimilarity(candidate, item) for item in selected) for candidate in candidates])


def family_coverage_scores(candidate_families: Sequence[str], selected_families: Sequence[str]) -> np.ndarray:
    counts: dict[str, int] = {}
    for family in selected_families:
        counts[family] = counts.get(family, 0) + 1
    raw = np.asarray([1.0 / (1.0 + counts.get(family, 0)) for family in candidate_families], dtype=float)
    return _minmax(raw)


def score_candidates(
    candidates: Sequence[Mapping[str, Any]],
    *,
    selected: Sequence[Mapping[str, Any]] = (),
    predictions: Mapping[str, Sequence[float]] | None = None,
    source_predictions: Mapping[str, Sequence[float]] | None = None,
) -> list[dict[str, Any]]:
    """Return decomposed PPTL acquisition scores, highest first."""

    if not candidates:
        return []
    novelty = novelty_scores(
        [str(row["smiles"]) for row in candidates],
        [str(row["smiles"]) for row in selected],
    )
    coverage = family_coverage_scores(
        [str(row.get("family_id", "unknown-family")) for row in candidates],
        [str(row.get("family_id", "unknown-family")) for row in selected],
    )
    prediction_values = [] if predictions is None else [np.asarray(values, dtype=float) for values in predictions.values()]
    source_values = [] if source_predictions is None else [np.asarray(values, dtype=float) for values in source_predictions.values()]
    model_disagreement = _minmax(np.std(np.vstack(prediction_values), axis=0)) if len(prediction_values) > 1 else np.zeros(len(candidates))
    source_disagreement = _minmax(np.std(np.vstack(source_values), axis=0)) if len(source_values) > 1 else np.zeros(len(candidates))
    disagreement = _minmax(0.5 * model_disagreement + 0.5 * source_disagreement)
    scores = 0.4 * disagreement + 0.4 * _minmax(novelty) + 0.2 * coverage
    output = []
    for index, candidate in enumerate(candidates):
        output.append(
            {
                "substrate_id": candidate.get("substrate_id") or candidate.get("compound_id"),
                "family_id": candidate.get("family_id", "unknown-family"),
                "score": float(scores[index]),
                "uncertainty_disagreement": float(disagreement[index]),
                "model_disagreement": float(model_disagreement[index]),
                "source_disagreement": float(source_disagreement[index]),
                "novelty": float(_minmax(novelty)[index]),
                "family_coverage": float(coverage[index]),
            }
        )
    return sorted(output, key=lambda row: (-row["score"], str(row["substrate_id"])))


__all__ = ["family_coverage_scores", "novelty_scores", "score_candidates"]

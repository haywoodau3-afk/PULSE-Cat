#!/usr/bin/env python3
"""Build high-level substrate-folding features from retained Stage 1 conformers."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import warnings
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

import numpy
from rdkit import Chem
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
STAGE2_FULL_SCOPE = ROOT / "scripts/stage2_full_scope_benchmark.py"
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_STAGE1_REPORT_DIR = ROOT / "data/jacs_2025/stage1/panel"
DEFAULT_POSE_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"
DEFAULT_POSE_INTERACTION = ROOT / "data/jacs_2025/stage2/features/pose-interaction.jsonl"
DEFAULT_FOLDING_FEATURES = ROOT / "data/jacs_2025/stage2/features/pose-folding-features.jsonl"
DEFAULT_AUGMENTED_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary-with-folding.jsonl"
DEFAULT_VIEW_DIR = ROOT / "data/jacs_2025/stage2/folding-views"
DEFAULT_METRICS = ROOT / "data/jacs_2025/stage2/modeling/pose-folding-feature-model-metrics.json"
DEFAULT_PREDICTIONS = ROOT / "data/jacs_2025/stage2/modeling/pose-folding-feature-loo-predictions.csv"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


stage2_full_scope = load_module("stage2_full_scope_benchmark", STAGE2_FULL_SCOPE)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def quantile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    sorted_values = sorted(values)
    position = fraction * (len(sorted_values) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    weight = position - lower_index
    return sorted_values[lower_index] * (1.0 - weight) + sorted_values[upper_index] * weight


def numeric_summary(values: list[float], prefix: str) -> dict[str, float | int | None]:
    if not values:
        return {
            f"{prefix}_count": 0,
            f"{prefix}_min": None,
            f"{prefix}_q05": None,
            f"{prefix}_median": None,
            f"{prefix}_mean": None,
            f"{prefix}_q95": None,
            f"{prefix}_max": None,
            f"{prefix}_std": None,
        }
    return {
        f"{prefix}_count": len(values),
        f"{prefix}_min": min(values),
        f"{prefix}_q05": quantile(values, 0.05),
        f"{prefix}_median": median(values),
        f"{prefix}_mean": mean(values),
        f"{prefix}_q95": quantile(values, 0.95),
        f"{prefix}_max": max(values),
        f"{prefix}_std": pstdev(values),
    }


def add_numeric_features(features: dict[str, float], prefix: str, block: dict[str, Any]) -> None:
    for key, value in block.items():
        if isinstance(value, bool):
            features[f"{prefix}:{key}"] = float(value)
        elif isinstance(value, int | float) and math.isfinite(float(value)):
            features[f"{prefix}:{key}"] = float(value)


def read_sdf(path: Path) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=False)
    molecule = next((mol for mol in supplier if mol is not None), None)
    if molecule is None:
        raise ValueError(f"Could not read pose SDF: {path}")
    Chem.SanitizeMol(molecule)
    return molecule


def heavy_atom_coordinates(molecule: Chem.Mol) -> tuple[list[int], numpy.ndarray]:
    conformer = molecule.GetConformer()
    indices = [atom.GetIdx() for atom in molecule.GetAtoms() if atom.GetAtomicNum() > 1]
    coords = numpy.array(
        [
            [
                conformer.GetAtomPosition(index).x,
                conformer.GetAtomPosition(index).y,
                conformer.GetAtomPosition(index).z,
            ]
            for index in indices
        ],
        dtype=float,
    )
    return indices, coords


def pairwise_distances(coords: numpy.ndarray) -> numpy.ndarray:
    delta = coords[:, None, :] - coords[None, :, :]
    return numpy.sqrt((delta * delta).sum(axis=2))


def upper_triangle_values(matrix: numpy.ndarray) -> numpy.ndarray:
    if matrix.shape[0] < 2:
        return numpy.array([], dtype=float)
    indices = numpy.triu_indices(matrix.shape[0], k=1)
    return matrix[indices]


def conformer_folding_features(molecule: Chem.Mol) -> dict[str, float]:
    heavy_indices, coords = heavy_atom_coordinates(molecule)
    centered = coords - coords.mean(axis=0)
    covariance = centered.T @ centered / max(len(coords), 1)
    eigvals = numpy.sort(numpy.linalg.eigvalsh(covariance))[::-1]
    eigvals = numpy.maximum(eigvals, 0.0)
    eigsum = float(eigvals.sum())
    rg = math.sqrt(eigsum)
    distances = pairwise_distances(coords)
    pair_distances = upper_triangle_values(distances)
    topological = Chem.GetDistanceMatrix(molecule)[numpy.ix_(heavy_indices, heavy_indices)]
    topological_pairs = upper_triangle_values(topological)
    long_range_mask = topological_pairs >= 6
    long_range_distances = pair_distances[long_range_mask]
    if long_range_distances.size:
        contact_4 = float((long_range_distances <= 4.0).sum() / long_range_distances.size)
        contact_5 = float((long_range_distances <= 5.0).sum() / long_range_distances.size)
        foldback_mean = float(long_range_distances.mean())
        foldback_q10 = float(numpy.quantile(long_range_distances, 0.10))
    else:
        contact_4 = 0.0
        contact_5 = 0.0
        foldback_mean = 0.0
        foldback_q10 = 0.0
    if pair_distances.size and topological_pairs.std() > 0 and pair_distances.std() > 0:
        graph_euclidean_corr = float(numpy.corrcoef(topological_pairs, pair_distances)[0, 1])
    else:
        graph_euclidean_corr = 0.0
    mean_eig = eigsum / 3.0 if eigsum else 0.0
    anisotropy = float(1.5 * numpy.square(eigvals - mean_eig).sum() / (eigsum * eigsum)) if eigsum else 0.0
    asphericity = float(eigvals[0] - 0.5 * (eigvals[1] + eigvals[2]))
    acylindricity = float(eigvals[1] - eigvals[2])
    axis_ratio_1_3 = float(math.sqrt(eigvals[0] / eigvals[2])) if eigvals[2] > 1e-12 else 0.0
    axis_ratio_2_3 = float(math.sqrt(eigvals[1] / eigvals[2])) if eigvals[2] > 1e-12 else 0.0
    max_distance = float(pair_distances.max()) if pair_distances.size else 0.0
    q90_distance = float(numpy.quantile(pair_distances, 0.90)) if pair_distances.size else 0.0
    mean_distance = float(pair_distances.mean()) if pair_distances.size else 0.0
    compactness = float(rg / max_distance) if max_distance else 0.0
    return {
        "radius_gyration": rg,
        "max_heavy_atom_distance": max_distance,
        "q90_heavy_atom_distance": q90_distance,
        "mean_heavy_atom_distance": mean_distance,
        "compactness_rg_over_max_distance": compactness,
        "shape_anisotropy": anisotropy,
        "shape_asphericity": asphericity,
        "shape_acylindricity": acylindricity,
        "principal_axis_ratio_1_3": axis_ratio_1_3,
        "principal_axis_ratio_2_3": axis_ratio_2_3,
        "long_range_contact_fraction_4a": contact_4,
        "long_range_contact_fraction_5a": contact_5,
        "long_range_foldback_distance_mean": foldback_mean,
        "long_range_foldback_distance_q10": foldback_q10,
        "graph_euclidean_distance_correlation": graph_euclidean_corr,
    }


def standardize(matrix: numpy.ndarray) -> tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    center = matrix.mean(axis=0)
    scale = matrix.std(axis=0)
    scale[scale == 0.0] = 1.0
    return (matrix - center) / scale, center, scale


def pca2(matrix: numpy.ndarray) -> tuple[numpy.ndarray, list[float]]:
    standardized, _, _ = standardize(matrix)
    _, singular_values, vt = numpy.linalg.svd(standardized, full_matrices=False)
    coords = standardized @ vt[:2].T
    variance = singular_values * singular_values
    total = float(variance.sum())
    fractions = [float(value / total) if total else 0.0 for value in variance[:2]]
    if coords.shape[1] == 1:
        coords = numpy.column_stack([coords[:, 0], numpy.zeros(coords.shape[0])])
        fractions.append(0.0)
    return coords[:, :2], fractions[:2]


def bucket_spread(matrix: numpy.ndarray) -> float:
    if len(matrix) <= 1:
        return 0.0
    standardized, _, _ = standardize(matrix)
    centroid = standardized.mean(axis=0)
    return float(numpy.sqrt(numpy.square(standardized - centroid).sum(axis=1)).mean())


def folding_feature_block(pose_feature_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], numpy.ndarray, list[str]]:
    keys = sorted(pose_feature_rows[0]["features"])
    matrix = numpy.array([[row["features"][key] for key in keys] for row in pose_feature_rows], dtype=float)
    pca_coords, pca_fraction = pca2(matrix)
    features: dict[str, Any] = {
        "folding_descriptor_pc1_variance_fraction": pca_fraction[0],
        "folding_descriptor_pc2_variance_fraction": pca_fraction[1],
    }
    all_standardized, _, _ = standardize(matrix)
    low_indices = [index for index, row in enumerate(pose_feature_rows) if row["bucket"] == "low_energy"]
    high_indices = [index for index, row in enumerate(pose_feature_rows) if row["bucket"] == "high_energy"]
    for bucket, indices in [("low_energy", low_indices), ("high_energy", high_indices), ("all", list(range(len(pose_feature_rows))))]:
        bucket_rows = [pose_feature_rows[index] for index in indices]
        bucket_matrix = matrix[indices]
        features[f"{bucket}_folding_pose_count"] = len(bucket_rows)
        features[f"{bucket}_folding_descriptor_spread"] = bucket_spread(bucket_matrix)
        for key in keys:
            values = [row["features"][key] for row in bucket_rows]
            features.update(numeric_summary(values, f"{bucket}_{key}"))
    if low_indices and high_indices:
        low_centroid = all_standardized[low_indices].mean(axis=0)
        high_centroid = all_standardized[high_indices].mean(axis=0)
        features["low_high_folding_centroid_distance"] = float(numpy.linalg.norm(low_centroid - high_centroid))
        for key_index, key in enumerate(keys):
            low_mean = float(matrix[low_indices, key_index].mean())
            high_mean = float(matrix[high_indices, key_index].mean())
            features[f"high_minus_low_{key}_mean"] = high_mean - low_mean
    else:
        features["low_high_folding_centroid_distance"] = 0.0
    return features, pca_coords, keys


def scale(values: list[float], low: float, high: float) -> list[float]:
    if not values:
        return []
    min_value = min(values)
    max_value = max(values)
    if max_value == min_value:
        return [(low + high) / 2.0 for _ in values]
    return [low + (value - min_value) * (high - low) / (max_value - min_value) for value in values]


def polyline(points: list[tuple[float, float]], color: str) -> str:
    if not points:
        return ""
    coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2" opacity="0.9" />'


def render_svg(
    substrate_id: str,
    pose_rows: list[dict[str, Any]],
    pca_coords: numpy.ndarray,
    view_path: Path,
) -> None:
    width = 900
    height = 560
    xs = scale([float(value) for value in pca_coords[:, 0]], 70, 520)
    ys = scale([float(value) for value in pca_coords[:, 1]], 430, 80)
    metrics = [
        ("radius_gyration", "Rg"),
        ("shape_anisotropy", "anisotropy"),
        ("long_range_contact_fraction_5a", "foldback"),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8f7f2" />',
        f'<text x="36" y="42" font-family="Arial" font-size="24" font-weight="700" fill="#25313b">{substrate_id} retained conformer folding view</text>',
        '<text x="36" y="68" font-family="Arial" font-size="13" fill="#52616b">PCA of high-level 3D shape and graph-foldback descriptors; blue = low-energy poses, red = high-energy poses.</text>',
        '<rect x="54" y="82" width="490" height="370" fill="#ffffff" stroke="#c9c3b6" />',
        '<line x1="70" y1="430" x2="520" y2="430" stroke="#89939b" stroke-width="1" />',
        '<line x1="70" y1="430" x2="70" y2="80" stroke="#89939b" stroke-width="1" />',
        '<text x="275" y="478" font-family="Arial" font-size="13" fill="#52616b">folding PC1</text>',
        '<text x="16" y="255" transform="rotate(-90 16 255)" font-family="Arial" font-size="13" fill="#52616b">folding PC2</text>',
    ]
    for row, x, y in zip(pose_rows, xs, ys, strict=True):
        color = "#2563eb" if row["bucket"] == "low_energy" else "#dc2626"
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}" opacity="0.68" />')
    parts.extend(
        [
            '<circle cx="610" cy="96" r="5" fill="#2563eb" opacity="0.75" />',
            '<text x="622" y="101" font-family="Arial" font-size="13" fill="#25313b">low-energy retained poses</text>',
            '<circle cx="610" cy="120" r="5" fill="#dc2626" opacity="0.75" />',
            '<text x="622" y="125" font-family="Arial" font-size="13" fill="#25313b">high-energy retained poses</text>',
            '<text x="590" y="166" font-family="Arial" font-size="17" font-weight="700" fill="#25313b">Bucket distributions</text>',
        ]
    )
    y_base = 210
    for metric_index, (metric_key, label) in enumerate(metrics):
        y0 = y_base + metric_index * 100
        parts.append(f'<text x="590" y="{y0 - 18}" font-family="Arial" font-size="13" font-weight="700" fill="#25313b">{label}</text>')
        values = [row["features"][metric_key] for row in pose_rows]
        scaled_values = scale(values, 620, 860)
        low_points = []
        high_points = []
        for index, (row, x_value) in enumerate(zip(pose_rows, scaled_values, strict=True)):
            point = (x_value, y0 + (index % 100) * 0.35)
            if row["bucket"] == "low_energy":
                low_points.append(point)
            else:
                high_points.append(point)
        parts.append(polyline(low_points, "#2563eb"))
        parts.append(polyline(high_points, "#dc2626"))
        parts.append(f'<line x1="620" y1="{y0 + 44}" x2="860" y2="{y0 + 44}" stroke="#c9c3b6" />')
    parts.append("</svg>")
    view_path.parent.mkdir(parents=True, exist_ok=True)
    view_path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def folding_row_for_report(report_path: Path, view_dir: Path) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    substrate_id = report["pose_generation_run"]["substrate_ids"][0]
    pose_feature_rows = []
    for pose in report["pose_records"]:
        sdf_path = ROOT / pose["uff_optimized_sdf_path"]
        molecule = read_sdf(sdf_path)
        pose_feature_rows.append(
            {
                "pose_id": pose["pose_id"],
                "bucket": pose["selection_bucket"],
                "features": conformer_folding_features(molecule),
            }
        )
    features, pca_coords, feature_keys = folding_feature_block(pose_feature_rows)
    view_path = view_dir / f"{substrate_id}-folding-view.svg"
    render_svg(substrate_id, pose_feature_rows, pca_coords, view_path)
    return {
        "schema_version": "stage2-pose-folding-features-v1",
        "substrate_id": substrate_id,
        "feature_status": "computed_from_retained_stage1_conformer_sdf",
        "feature_blocks": {"pose_folding": features},
        "provenance": {
            "stage1_report_path": display_path(report_path),
            "folding_view_path": display_path(view_path),
            "pose_count": len(pose_feature_rows),
            "per_conformer_descriptor_count": len(feature_keys),
            "bucket_policy": "low_energy and high_energy retained poses summarized separately",
        },
    }


def generate_folding_features(records_path: Path, report_dir: Path, view_dir: Path) -> list[dict[str, Any]]:
    records = {
        row["substrate_id"]: row
        for row in read_jsonl(records_path)
        if row.get("outcome", {}).get("ee_percent") is not None
        and row.get("reaction_center", {}).get("review_status") == "checked"
    }
    rows = []
    for report_path in sorted(report_dir.glob("stage-1-smoke-*.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        substrate_ids = report.get("pose_generation_run", {}).get("substrate_ids", [])
        if len(substrate_ids) != 1 or substrate_ids[0] not in records:
            continue
        rows.append(folding_row_for_report(report_path, view_dir))
    return sorted(rows, key=lambda row: row["substrate_id"])


def augment_pose_summary(pose_summary_path: Path, folding_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    folding_by_id = {row["substrate_id"]: row for row in folding_rows}
    augmented_rows = []
    for row in read_jsonl(pose_summary_path):
        substrate_id = row["substrate_id"]
        if substrate_id not in folding_by_id:
            continue
        augmented = json.loads(json.dumps(row))
        augmented["schema_version"] = "stage2-pose-summary-with-folding-features-v1"
        augmented["feature_blocks"]["pose_folding"] = folding_by_id[substrate_id]["feature_blocks"]["pose_folding"]
        augmented["provenance"]["pose_folding_features_path"] = folding_by_id[substrate_id]["provenance"]["folding_view_path"]
        augmented_rows.append(augmented)
    return sorted(augmented_rows, key=lambda row: row["substrate_id"])


def training_records(records_path: Path) -> list[dict[str, Any]]:
    return sorted(
        [
            record
            for record in read_jsonl(records_path)
            if record.get("outcome", {}).get("ee_percent") is not None
            and record.get("reaction_center", {}).get("review_status") == "checked"
        ],
        key=lambda record: record["substrate_id"],
    )


def feature_rows_for_policy(
    records_path: Path,
    pose_summary_path: Path,
    pose_interaction_path: Path,
    folding_path: Path,
    policy: str,
) -> tuple[list[dict[str, Any]], list[str], numpy.ndarray, numpy.ndarray]:
    records = training_records(records_path)
    summary = {row["substrate_id"]: row for row in read_jsonl(pose_summary_path)}
    interaction = stage2_full_scope.aggregate_pose_interactions(read_jsonl(pose_interaction_path))
    folding = {row["substrate_id"]: row for row in read_jsonl(folding_path)}
    rows = []
    for record in records:
        substrate_id = record["substrate_id"]
        features: dict[str, float] = {}
        if policy in {"summary", "summary_folding", "summary_interaction", "summary_interaction_folding"}:
            add_numeric_features(features, "pose_summary", summary[substrate_id]["feature_blocks"]["pose_summary"])
        if policy in {"folding", "summary_folding", "summary_interaction_folding"}:
            add_numeric_features(features, "pose_folding", folding[substrate_id]["feature_blocks"]["pose_folding"])
        if policy in {"summary_interaction", "summary_interaction_folding"}:
            add_numeric_features(features, "pose_interaction", interaction[substrate_id])
        rows.append(
            {
                "substrate_id": substrate_id,
                "actual_ee": float(record["outcome"]["ee_percent"]),
                "features": features,
            }
        )
    feature_names = sorted({key for row in rows for key in row["features"]})
    x = numpy.array([[row["features"].get(key, 0.0) for key in feature_names] for row in rows], dtype=float)
    y = numpy.array([row["actual_ee"] for row in rows], dtype=float)
    return rows, feature_names, x, y


def metrics(y: numpy.ndarray, predictions: list[float]) -> dict[str, Any]:
    pred = numpy.array(predictions, dtype=float)
    absolute_error = numpy.abs(y - pred)
    return {
        "record_count": int(len(y)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(mean_squared_error(y, pred) ** 0.5),
        "r2": float(r2_score(y, pred)),
        "median_abs_error": float(numpy.median(absolute_error)),
        "within_10_count": int((absolute_error <= 10.0).sum()),
        "within_15_count": int((absolute_error <= 15.0).sum()),
        "within_20_count": int((absolute_error <= 20.0).sum()),
    }


def select_loo_model(x: numpy.ndarray, y: numpy.ndarray) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for alpha in [0.01, 0.1, 1.0, 10.0, 100.0]:
        for l1_ratio in [0.2, 0.5, 0.8, 1.0]:
            predictions = []
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ConvergenceWarning)
                for holdout in range(len(y)):
                    mask = numpy.ones(len(y), dtype=bool)
                    mask[holdout] = False
                    model = make_pipeline(
                        StandardScaler(),
                        ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=50000, random_state=0),
                    )
                    model.fit(x[mask], y[mask])
                    predictions.append(float(model.predict(x[[holdout]])[0]))
            report = {
                "selected_alpha": alpha,
                "selected_l1_ratio": l1_ratio,
                "loo_predictions": predictions,
                **metrics(y, predictions),
            }
            if best is None or report["mae"] < best["mae"]:
                best = report
    assert best is not None
    return best


def write_prediction_table(path: Path, policies: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["substrate_id", "actual_ee"]
    for policy in policies:
        fieldnames.extend([f"{policy}_prediction", f"{policy}_abs_error"])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for index, row in enumerate(rows):
            output = {"substrate_id": row["substrate_id"], "actual_ee": row["actual_ee"]}
            for policy, report in policies.items():
                prediction = report["loo_predictions"][index]
                output[f"{policy}_prediction"] = prediction
                output[f"{policy}_abs_error"] = abs(row["actual_ee"] - prediction)
            writer.writerow(output)


def run(args: argparse.Namespace) -> dict[str, Any]:
    folding_rows = generate_folding_features(args.records, args.stage1_report_dir, args.view_dir)
    write_jsonl(args.folding_features, folding_rows)
    augmented_rows = augment_pose_summary(args.pose_summary, folding_rows)
    write_jsonl(args.augmented_pose_summary, augmented_rows)
    policies = {}
    prediction_rows: list[dict[str, Any]] | None = None
    for policy in ["summary", "folding", "summary_folding", "summary_interaction", "summary_interaction_folding"]:
        rows, feature_names, x, y = feature_rows_for_policy(
            args.records,
            args.pose_summary,
            args.pose_interaction,
            args.folding_features,
            policy,
        )
        selected = select_loo_model(x, y)
        policies[policy] = {
            key: value
            for key, value in selected.items()
            if key != "loo_predictions"
        }
        policies[policy]["feature_count"] = len(feature_names)
        policies[policy]["loo_predictions"] = selected["loo_predictions"]
        if prediction_rows is None:
            prediction_rows = rows
    assert prediction_rows is not None
    write_prediction_table(args.predictions, policies, prediction_rows)
    report = {
        "schema_version": "stage2-pose-folding-feature-experiment-v1",
        "status": "summary_point_complete",
        "folding_feature_rows": len(folding_rows),
        "augmented_pose_summary_rows": len(augmented_rows),
        "folding_feature_path": display_path(args.folding_features),
        "augmented_pose_summary_path": display_path(args.augmented_pose_summary),
        "folding_view_dir": display_path(args.view_dir),
        "prediction_table": display_path(args.predictions),
        "models": {
            policy: {key: value for key, value in policy_report.items() if key != "loo_predictions"}
            for policy, policy_report in policies.items()
        },
        "folding_feature_concept": [
            "3D heavy-atom cloud shape: radius of gyration, max distance, compactness, PCA anisotropy/asphericity/acylindricity.",
            "Graph-aware foldback: long topological-distance heavy-atom pairs that become close in 3D.",
            "Low-energy and high-energy retained pose buckets summarized separately, with high-minus-low deltas and centroid separation.",
        ],
    }
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--stage1-report-dir", type=Path, default=DEFAULT_STAGE1_REPORT_DIR)
    parser.add_argument("--pose-summary", type=Path, default=DEFAULT_POSE_SUMMARY)
    parser.add_argument("--pose-interaction", type=Path, default=DEFAULT_POSE_INTERACTION)
    parser.add_argument("--folding-features", type=Path, default=DEFAULT_FOLDING_FEATURES)
    parser.add_argument("--augmented-pose-summary", type=Path, default=DEFAULT_AUGMENTED_SUMMARY)
    parser.add_argument("--view-dir", type=Path, default=DEFAULT_VIEW_DIR)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

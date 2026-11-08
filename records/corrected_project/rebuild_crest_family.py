from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / "crest_family"
RECORDS = ROOT / "revision/reviewer2_comment1/results/p7_source_corrected_copy.jsonl"
STAGE2P = HERE / "features/p7/stage2p.jsonl"
POSE_INTERACTION = HERE / "features/p7/pose_interaction.jsonl"
POSE_SUMMARY = ROOT / "data/jacs_2025/stage2/features/pose-summary.jsonl"
POSE_FOLDING = ROOT / "data/jacs_2025/stage2/features/pose-folding-features.jsonl"
CREST = ROOT / "SI2/data/crest/benchmarks/p7-crest-xtb-model/features.json"

XTB_FEATURE_NAMES = {
    "crest_xtb.total_energy_per_atom_hartree",
    "crest_xtb.total_energy_per_electron_hartree",
    "crest_xtb.electronic_energy_per_electron_hartree",
    "crest_xtb.energy_minus_electronic_per_atom_hartree",
    "crest_xtb.homo_ev",
    "crest_xtb.lumo_ev",
    "crest_xtb.homo_lumo_gap_ev",
    "crest_xtb.dipole_norm_au",
    "crest_xtb.charge_std",
    "crest_xtb.charge_mean_absolute",
    "crest_xtb.charge_range",
    "crest_xtb.atomic_dipole_mean_norm_au",
    "crest_xtb.atomic_dipole_max_norm_au",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    family_model = load_module(
        "stage3a_alt_plus_stage2p_family_heldout_for_crest",
        ROOT / "scripts/stage3a_alt_plus_stage2p_family_heldout.py",
    )
    family_model.stage2p.DEFAULT_POSE_SUMMARY = POSE_SUMMARY
    family_model.stage2p.DEFAULT_POSE_INTERACTION = POSE_INTERACTION
    family_model.stage2p.DEFAULT_POSE_FOLDING = POSE_FOLDING
    family_model.EXCLUDED_SUBSTRATES = {"1ad", "1an", "1z"}

    stage2p_rows = family_model.read_jsonl(STAGE2P)
    model_rows = family_model.stage2p.model_feature_rows(
        RECORDS, POSE_SUMMARY, POSE_INTERACTION, POSE_FOLDING, stage2p_rows
    )
    base_rows, base_names, base_x, base_y = family_model.filter_model_rows(
        *model_rows["stage2p_geometry"]
    )
    ids = [row["substrate_id"] for row in base_rows]
    crest_records = json.loads(CREST.read_text(encoding="utf-8"))
    crest_by_id = {row["substrate_id"]: row["features"] for row in crest_records}
    missing = sorted(set(ids) - set(crest_by_id))
    if missing:
        raise ValueError(f"CREST matrix lacks corrected model IDs: {missing}")

    geometry_names = sorted(
        key for key in crest_by_id[ids[0]] if key.startswith("crest_geom.")
    )
    xtb_names = sorted(key for key in XTB_FEATURE_NAMES)
    if len(geometry_names) != 10 or len(xtb_names) != 13:
        raise ValueError("CREST feature blocks do not match the documented 10/13 fitted columns")
    geometry_x = numpy.asarray(
        [[crest_by_id[sid][name] for name in geometry_names] for sid in ids], dtype=float
    )
    xtb_x = numpy.asarray(
        [[crest_by_id[sid][name] for name in xtb_names] for sid in ids], dtype=float
    )

    metadata = family_model.family_heldout.family_metadata(RECORDS)
    family_ids = [metadata[sid]["family_id"] for sid in ids]
    family_labels = {
        value["family_id"]: value["family_label"] for value in metadata.values()
    }
    arms = [
        ("stage2p_geometry", base_names, base_x),
        ("stage2p_plus_crest_geometry", base_names + geometry_names, numpy.column_stack([base_x, geometry_x])),
        ("stage2p_plus_xtb_electronics", base_names + xtb_names, numpy.column_stack([base_x, xtb_x])),
        ("stage2p_plus_crest_and_xtb", base_names + geometry_names + xtb_names, numpy.column_stack([base_x, geometry_x, xtb_x])),
    ]

    report = {
        "schema_version": "corrected-p7-crest-stage2p-family-heldout-v1",
        "status": "corrected_base_features; retrospective family-held-out analysis",
        "target": "ee_percent_magnitude",
        "cohort": {
            "substrate_count": len(ids),
            "family_count": len(set(family_ids)),
            "family_sizes": {family: family_ids.count(family) for family in sorted(set(family_ids))},
        },
        "feature_sources": {
            "stage2p": str(STAGE2P.relative_to(ROOT)),
            "crest_geometry_and_xtb": str(CREST.relative_to(ROOT)),
            "crest_geometry_fitted_columns": geometry_names,
            "xtb_fitted_columns": xtb_names,
        },
        "models": {},
    }
    prediction_rows = []
    model_prediction_errors = {}
    for name, feature_names, x in arms:
        model_report, preds = family_model.family_heldout.family_heldout_model(
            base_rows, feature_names, x, base_y, family_ids, family_labels
        )
        report["models"][name] = model_report
        model_prediction_errors[name] = {
            row["substrate_id"]: float(row["abs_error"]) for row in preds
        }
        for row in preds:
            row["feature_set"] = name
            prediction_rows.append(row)

    # Preserve the SI's paired 20,000-draw substrate bootstrap, recalculated
    # from the corrected prediction pairs. This is descriptive and does not
    # resample chemical families as clusters.
    baseline_errors = model_prediction_errors["stage2p_geometry"]
    bootstrap_ids = sorted(baseline_errors)
    rng = numpy.random.default_rng(20260907)
    draw_indices = rng.integers(0, len(bootstrap_ids), size=(20000, len(bootstrap_ids)))
    report["paired_bootstrap_improvements"] = {}
    for name in model_prediction_errors:
        if name == "stage2p_geometry":
            continue
        delta = numpy.asarray(
            [baseline_errors[sid] - model_prediction_errors[name][sid] for sid in bootstrap_ids],
            dtype=float,
        )
        bootstrap = delta[draw_indices].mean(axis=1)
        report["paired_bootstrap_improvements"][name] = {
            "statistic": "baseline absolute error minus augmented absolute error; positive favors augmentation",
            "record_count": len(bootstrap_ids),
            "bootstrap_unit": "substrate; not family-clustered",
            "draw_count": int(len(bootstrap)),
            "seed": 20260907,
            "mean_improvement_ee_points": float(delta.mean()),
            "percentile_95_interval_ee_points": [
                float(value) for value in numpy.quantile(bootstrap, [0.025, 0.975])
            ],
            "bootstrap_fraction_above_zero": float(numpy.mean(bootstrap > 0.0)),
            "substrates_with_lower_absolute_error": int(numpy.sum(delta > 0.0)),
        }

    report["input_sha256"] = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in (RECORDS, STAGE2P, POSE_INTERACTION, POSE_SUMMARY, POSE_FOLDING, CREST)
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "corrected_metrics.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (OUT / "corrected_predictions.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["feature_set", "substrate_id", "family_id", "family_label", "observed_ee", "prediction", "abs_error"]
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(prediction_rows)
    for name, model in report["models"].items():
        pooled = model["pooled_metrics"]
        print(name, "MAE", pooled["mae"], "RMSE", pooled["rmse"], "R2", pooled["r2"], "macro", pooled["macro_family_mae"])
    print(f"Wrote corrected CREST family outputs under {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

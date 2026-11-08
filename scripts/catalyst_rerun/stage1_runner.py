#!/usr/bin/env python3
"""Run a catalyst-namespaced Stage 1 pilot without touching the P7 dataset."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CATALYST_SLUGS = {"cmcpor-fecl": "cmcpor", "d4-por-fecl": "d4_por"}
DEFAULT_CONFIGS = {
    catalyst_id: ROOT / "data" / "expansion" / "catalyst_rerun" / slug / "run-config.json"
    for catalyst_id, slug in CATALYST_SLUGS.items()
}


def namespace_paths(catalyst_id: str) -> dict[str, Path]:
    try:
        slug = CATALYST_SLUGS[catalyst_id]
    except KeyError as exc:
        raise ValueError(f"unsupported catalyst_id: {catalyst_id}") from exc
    root = ROOT / "data" / "expansion" / "catalyst_rerun" / slug
    return {
        "root": root,
        "stage0": root / "stage0",
        "stage1": root / "stage1",
        "stage1_reports": root / "stage1" / "reports",
        "stage1_geometry": root / "stage1" / "geometry",
        "stage2": root / "stage2",
        "stage2p": root / "stage2p",
        "stage2pp": root / "stage2pp",
        "models": root / "models",
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _resolve(config_path: Path, value: Any) -> Path | None:
    if value in (None, ""):
        return None
    path = Path(str(value))
    return path if path.is_absolute() else config_path.parent / path


def _contract_module():
    path = ROOT / "scripts" / "catalyst_rerun_contract.py"
    spec = importlib.util.spec_from_file_location("catalyst_rerun_contract_for_stage1", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def audit_catalyst_config(config_path: Path) -> dict[str, Any]:
    config = _load_json(config_path)
    if config.get("schema_version") != "catalyst-run-config-v1":
        raise ValueError("unsupported catalyst run config schema")
    catalyst_id = config.get("catalyst_id")
    if catalyst_id not in CATALYST_SLUGS:
        raise ValueError(f"unsupported catalyst_id: {catalyst_id}")
    contract = _contract_module()
    missing_inputs = []
    force_field = str(config.get("force_field", "uff")).lower().replace("-", "")
    if force_field not in {"uff", "mmff94"}:
        missing_inputs.append("supported_force_field")
    geometry_path = _resolve(config_path, config.get("reference_geometry_path"))
    profile_path = _resolve(config_path, config.get("constraint_profile_path"))
    substrates_path = _resolve(config_path, config.get("substrates_path"))
    outcomes_path = _resolve(config_path, config.get("outcomes_path"))
    for field, path in (
        ("reference_geometry_path", geometry_path),
        ("constraint_profile_path", profile_path),
        ("substrates_path", substrates_path),
        ("outcomes_path", outcomes_path),
    ):
        if path is None or not path.is_file():
            missing_inputs.append(field)

    substrates = _load_jsonl(substrates_path) if substrates_path and substrates_path.is_file() else []
    outcomes = _load_jsonl(outcomes_path) if outcomes_path and outcomes_path.is_file() else []
    if not substrates:
        missing_inputs.append("nonempty_substrates_path")
    if not outcomes:
        missing_inputs.append("nonempty_outcomes_path")
    invalid_records = []
    for record in substrates:
        try:
            contract.validate_substrate_record(record)
        except contract.ContractError as exc:
            invalid_records.append({"kind": "substrate", "compound_id": record.get("compound_id"), "error": str(exc)})
    for record in outcomes:
        try:
            contract.validate_outcome_record(record)
        except contract.ContractError as exc:
            invalid_records.append({"kind": "outcome", "compound_id": record.get("compound_id"), "error": str(exc)})
    substrate_ids = {record.get("compound_id") for record in substrates}
    catalyst_outcomes = {
        record.get("compound_id") for record in outcomes if record.get("catalyst_id") == catalyst_id
    }
    missing_outcomes = sorted(substrate_ids - catalyst_outcomes)
    if missing_outcomes:
        missing_inputs.append("catalyst_specific_outcomes")
    if invalid_records:
        missing_inputs.append("valid_substrate_or_outcome_records")
    return {
        "status": "blocked_missing_inputs" if missing_inputs else "ready_for_stage1_pilot",
        "catalyst_id": catalyst_id,
        "config_path": str(config_path),
        "missing_inputs": sorted(set(missing_inputs)),
        "invalid_records": invalid_records,
        "missing_outcomes": missing_outcomes,
        "substrate_count": len(substrates),
        "outcome_count": len([record for record in outcomes if record.get("catalyst_id") == catalyst_id]),
        "force_field": force_field,
        "paths": {
            "reference_geometry": str(geometry_path) if geometry_path else None,
            "constraint_profile": str(profile_path) if profile_path else None,
            "substrates": str(substrates_path) if substrates_path else None,
            "outcomes": str(outcomes_path) if outcomes_path else None,
            "output_root": config.get("output_root"),
        },
    }


def _load_stage1_module():
    path = ROOT / "scripts" / "stage1_contract.py"
    spec = importlib.util.spec_from_file_location("stage1_contract_for_catalyst_rerun", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Python 3.14's dataclasses inspect ``sys.modules`` while decorating
    # classes.  Register the dynamically loaded module before execution so
    # the namespaced runner works with the repository's Python environment.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_manual_substrates(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["substrate_id", "product_id", "azide_smiles", "nitrene_smiles", "azide_position"],
        )
        writer.writeheader()
        for row in rows:
            azide = row["azide_smiles"]
            writer.writerow(
                {
                    "substrate_id": row["paper_substrate_id"],
                    "product_id": row.get("product_id", ""),
                    "azide_smiles": azide,
                    "nitrene_smiles": row["nitrene_smiles"],
                    "azide_position": "prefix" if azide.startswith(("N#N=N", "N=N#N")) else "suffix",
                }
            )


def run_stage1(config_path: Path, pilot: bool = True, resume: bool = False) -> dict[str, Any]:
    audit = audit_catalyst_config(config_path)
    if audit["status"] != "ready_for_stage1_pilot":
        return audit
    config = _load_json(config_path)
    stage1 = _load_stage1_module()
    stage1_force_field = stage1.normalize_force_field(str(config.get("force_field", "uff")))
    paths = namespace_paths(config["catalyst_id"])
    output_root = _resolve(config_path, config.get("output_root")) or paths["root"]
    substrates = _load_jsonl(_resolve(config_path, config["substrates_path"]))
    if pilot:
        pilot_ids = set(config.get("pilot_substrate_ids", []))
        if pilot_ids:
            substrates = [row for row in substrates if row["paper_substrate_id"] in pilot_ids]
    manual_path = output_root / "stage0" / "manual-substrates.csv"
    _write_manual_substrates(manual_path, substrates)
    profile_path = _resolve(config_path, config["constraint_profile_path"])
    reference_path = _resolve(config_path, config["reference_geometry_path"])
    report_dir = output_root / "stage1" / "reports"
    geometry_dir = output_root / "stage1" / "geometry"
    report_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    prefix = f"stage-1-smoke-{CATALYST_SLUGS[config['catalyst_id']]}-{stage1_force_field}"
    for row in sorted(substrates, key=lambda value: value["paper_substrate_id"]):
        substrate_id = row["paper_substrate_id"]
        report_path = report_dir / f"{prefix}-{substrate_id}.json"
        if resume and report_path.is_file():
            try:
                existing = _load_json(report_path)
            except (OSError, json.JSONDecodeError):
                existing = None
            existing_ids = existing.get("pose_generation_run", {}).get("substrate_ids", []) if existing else []
            if existing and existing_ids == [substrate_id] and existing.get("pose_records"):
                reports.append(str(report_path))
                continue
        report = stage1.build_report(
            substrate_id,
            tolerance=float(config.get("fe_n_tolerance_angstrom", 1e-5)),
            geometry_dir=geometry_dir,
            random_seed=int(config.get("random_seed", 20260730)),
            pool_size=int(config.get("pool_size", 5000)),
            retain_low_count=int(config.get("retain_low_count", 100)),
            retain_high_count=int(config.get("retain_high_count", 100)),
            manual_substrates_path=manual_path,
            constraint_profile_path=profile_path,
            reference_geometry_path=reference_path,
            run_id_prefix=prefix,
            force_field=stage1_force_field,
        )
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        reports.append(str(report_path))
    return {
        "status": "stage1_pilot_complete",
        "catalyst_id": config["catalyst_id"],
        "substrate_count": len(reports),
        "report_dir": str(report_dir),
        "reports": reports,
    }


def parse_args(default_config: Path | None = None, expected_catalyst_id: str | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=default_config)
    parser.add_argument("--full", action="store_true", help="run all supplied substrates instead of the pilot subset")
    parser.add_argument("--resume", action="store_true", help="reuse existing nonempty Stage 1 reports with matching substrate ids")
    args = parser.parse_args()
    if args.config is None:
        raise SystemExit("--config is required")
    if expected_catalyst_id:
        config = _load_json(args.config)
        if config.get("catalyst_id") != expected_catalyst_id:
            raise SystemExit(f"config catalyst_id must be {expected_catalyst_id}")
    return args


def main(default_config: Path | None = None, expected_catalyst_id: str | None = None) -> int:
    args = parse_args(default_config, expected_catalyst_id)
    report = run_stage1(args.config, pilot=not args.full, resume=args.resume)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "stage1_pilot_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate isolated MMFF94 Stage 1 reports for the P7 scope."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "data/jacs_2025_mmff94/run-config.json"
OUTPUT_ROOT = CONFIG.parent


def load_stage1():
    path = ROOT / "scripts/stage1_contract.py"
    spec = importlib.util.spec_from_file_location("stage1_contract_for_p7_mmff94", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else CONFIG.parent / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="accepted for symmetry with catalyst runners")
    parser.add_argument("--resume", action="store_true", help="reuse matching completed MMFF94 reports")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    stage1 = load_stage1()
    force_field = stage1.normalize_force_field(config["force_field"])
    manual_substrates = resolve(config["manual_substrates_path"])
    profile = resolve(config["constraint_profile_path"])
    reference = resolve(config["reference_geometry_path"])
    report_dir = OUTPUT_ROOT / "stage1/reports"
    geometry_dir = OUTPUT_ROOT / "stage1/geometry"
    report_dir.mkdir(parents=True, exist_ok=True)
    with manual_substrates.open(encoding="utf-8", newline="") as stream:
        substrate_ids = sorted(row["substrate_id"] for row in csv.DictReader(stream))
    prefix = "stage-1-smoke-p7-mmff94"
    reports = []
    for substrate_id in substrate_ids:
        report_path = report_dir / f"{prefix}-{substrate_id}.json"
        if args.resume and report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            run = report.get("pose_generation_run", {})
            if run.get("substrate_ids") == [substrate_id] and run.get("force_field") == force_field:
                reports.append(str(report_path))
                continue
        report = stage1.build_report(
            substrate_id=substrate_id,
            tolerance=float(config["fe_n_tolerance_angstrom"]),
            geometry_dir=geometry_dir,
            random_seed=int(config["random_seed"]),
            pool_size=int(config["pool_size"]),
            retain_low_count=int(config["retain_low_count"]),
            retain_high_count=int(config["retain_high_count"]),
            manual_substrates_path=manual_substrates,
            constraint_profile_path=profile,
            reference_geometry_path=reference,
            run_id_prefix=prefix,
            force_field=force_field,
        )
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        reports.append(str(report_path))
    print(json.dumps({"status": "complete", "force_field": force_field, "report_count": len(reports), "report_dir": str(report_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

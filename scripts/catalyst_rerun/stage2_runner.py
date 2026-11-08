#!/usr/bin/env python3
"""Run namespaced Stage 2, Stage 2p, and Stage 2pp commands for one catalyst."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

_STAGE1_SPEC = importlib.util.spec_from_file_location(
    "catalyst_stage1_runner_for_stage2",
    Path(__file__).with_name("stage1_runner.py"),
)
assert _STAGE1_SPEC.loader is not None
_STAGE1 = importlib.util.module_from_spec(_STAGE1_SPEC)
_STAGE1_SPEC.loader.exec_module(_STAGE1)
CATALYST_SLUGS = _STAGE1.CATALYST_SLUGS
ROOT = _STAGE1.ROOT
_load_json = _STAGE1._load_json
_load_jsonl = _STAGE1._load_jsonl
_resolve = _STAGE1._resolve
audit_catalyst_config = _STAGE1.audit_catalyst_config
namespace_paths = _STAGE1.namespace_paths


def audit_stage2_config(config_path: Path) -> dict[str, Any]:
    stage1_audit = audit_catalyst_config(config_path)
    config = _load_json(config_path)
    missing = list(stage1_audit["missing_inputs"])
    stage2_records = _resolve(config_path, config.get("stage2_records_path"))
    if stage2_records is None or not stage2_records.is_file() or not stage2_records.read_text(encoding="utf-8").strip():
        missing.append("stage2_records_path")
    for field in ("fe_atom_index_one_based", "cl_atom_index_one_based"):
        if not isinstance(config.get(field), int) or config[field] < 1:
            missing.append(field)
    return {
        "status": "blocked_missing_inputs" if missing else "ready_for_stage2",
        "catalyst_id": config.get("catalyst_id"),
        "config_path": str(config_path),
        "missing_inputs": sorted(set(missing)),
        "stage1": stage1_audit,
        "stage2_records_path": str(stage2_records) if stage2_records else None,
    }


def _run(command: list[str]) -> None:
    local_python = ROOT / ".venv" / "bin" / "python"
    if not local_python.is_file():
        raise RuntimeError(f"repository-local Python environment is missing: {local_python}")
    subprocess.run([str(local_python), *command], cwd=ROOT, check=True)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _stage1_report_ids(report_dir: Path) -> set[str]:
    ids: set[str] = set()
    for report_path in report_dir.glob("stage-1-smoke-*.json"):
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        pose_run = report.get("pose_generation_run", {})
        substrate_ids = pose_run.get("substrate_ids", [])
        if len(substrate_ids) == 1 and isinstance(substrate_ids[0], str):
            ids.add(substrate_ids[0])
            continue
        substrate_id = report.get("substrate_record", {}).get("substrate_id")
        if isinstance(substrate_id, str) and substrate_id:
            ids.add(substrate_id)
    return ids


def run_stage2(config_path: Path) -> dict[str, Any]:
    audit = audit_stage2_config(config_path)
    if audit["status"] != "ready_for_stage2":
        return audit
    config = _load_json(config_path)
    catalyst_id = config["catalyst_id"]
    paths = namespace_paths(catalyst_id)
    output_root = _resolve(config_path, config.get("output_root")) or paths["root"]
    records = _resolve(config_path, config["stage2_records_path"])
    report_dir = output_root / "stage1" / "reports"
    stage2_dir = output_root / "stage2"
    stage2p_dir = output_root / "stage2p"
    stage2pp_dir = output_root / "stage2pp"
    summary_path = stage2_dir / "features" / "pose-summary.jsonl"
    interaction_path = stage2_dir / "features" / "pose-interaction.jsonl"
    folding_path = stage2_dir / "features" / "pose-folding-features.jsonl"
    augmented_path = stage2_dir / "features" / "pose-summary-with-folding.jsonl"
    all_records = _load_jsonl(records)
    report_ids = _stage1_report_ids(report_dir)
    run_records = [
        record
        for record in all_records
        if record.get("substrate_id") in report_ids and record.get("curation_status") == "feature_ready"
    ]
    if not run_records:
        raise RuntimeError(
            f"no feature-ready Stage 2 records have Stage 1 reports in {report_dir}; run Stage 1 first"
        )
    run_records_path = stage2_dir / "records-for-run.jsonl"
    _write_jsonl(run_records_path, run_records)
    _run([
        str(ROOT / "scripts/stage2_pose_summary.py"),
        "--records", str(run_records_path),
        "--stage1-report-dir", str(report_dir),
        "--output", str(summary_path),
    ])
    _run([
        str(ROOT / "scripts/stage2_pose_interaction.py"),
        "--records", str(run_records_path),
        "--stage1-report-dir", str(report_dir),
        "--output", str(interaction_path),
        "--fe-atom-index", str(config["fe_atom_index_one_based"]),
        "--cl-atom-index", str(config["cl_atom_index_one_based"]),
    ])
    _run([
        str(ROOT / "scripts/stage2_folding_feature_experiment.py"),
        "--records", str(run_records_path),
        "--stage1-report-dir", str(report_dir),
        "--pose-summary", str(summary_path),
        "--pose-interaction", str(interaction_path),
        "--folding-features", str(folding_path),
        "--augmented-pose-summary", str(augmented_path),
        "--view-dir", str(stage2_dir / "folding-views"),
        "--metrics", str(stage2_dir / "modeling/folding-metrics.json"),
        "--predictions", str(stage2_dir / "modeling/folding-predictions.csv"),
    ])
    _run([
        str(ROOT / "scripts/stage2p_representation.py"),
        "--records", str(run_records_path),
        "--stage1-report-dir", str(report_dir),
        "--pose-summary", str(summary_path),
        "--pose-interaction", str(interaction_path),
        "--pose-folding", str(folding_path),
        "--features", str(stage2p_dir / "features/stage2p-features.jsonl"),
        "--manifest", str(stage2p_dir / "features/stage2p-manifest.json"),
        "--metrics", str(stage2p_dir / "modeling/stage2p-model-metrics.json"),
        "--predictions", str(stage2p_dir / "modeling/stage2p-predictions.csv"),
        "--trends", str(stage2p_dir / "modeling/stage2p-trends.csv"),
    ])
    _run([
        str(ROOT / "scripts/stage2pp_representation.py"),
        "--records", str(run_records_path),
        "--stage1-report-dir", str(report_dir),
        "--stage2p-features", str(stage2p_dir / "features/stage2p-features.jsonl"),
        "--pose-summary", str(summary_path),
        "--pose-interaction", str(interaction_path),
        "--pose-folding", str(folding_path),
        "--output-dir", str(stage2pp_dir),
        "--features", str(stage2pp_dir / "features/stage2pp-features.jsonl"),
        "--manifest", str(stage2pp_dir / "features/stage2pp-manifest.json"),
        "--metrics", str(stage2pp_dir / "modeling/stage2pp-model-comparison.json"),
        "--predictions", str(stage2pp_dir / "modeling/stage2pp-predictions.csv"),
        "--trends", str(stage2pp_dir / "modeling/stage2pp-trends.csv"),
    ])
    return {
        "status": "stage2_to_stage2pp_complete",
        "catalyst_id": catalyst_id,
        "output_root": str(output_root),
        "record_count": len(run_records),
        "records_for_run": str(run_records_path),
        "stage2p_dir": str(stage2p_dir),
        "stage2pp_dir": str(stage2pp_dir),
    }


def main(default_config: Path | None = None, expected_catalyst_id: str | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=default_config)
    args = parser.parse_args()
    if args.config is None:
        raise SystemExit("--config is required")
    if expected_catalyst_id:
        config = _load_json(args.config)
        if config.get("catalyst_id") != expected_catalyst_id:
            raise SystemExit(f"config catalyst_id must be {expected_catalyst_id}")
    report = run_stage2(args.config)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "stage2_to_stage2pp_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())

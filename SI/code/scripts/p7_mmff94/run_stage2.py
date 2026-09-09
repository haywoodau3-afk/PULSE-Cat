#!/usr/bin/env python3
"""Run isolated P7 MMFF94 Stage 2, Stage 2p, and Stage 2pp."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "data/jacs_2025_mmff94/run-config.json"
OUTPUT_ROOT = CONFIG.parent


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else CONFIG.parent / path


def run(command: list[str]) -> None:
    python = ROOT / ".venv/bin/python"
    subprocess.run([str(python), *command], cwd=ROOT, check=True)


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    records = resolve(config["stage2_records_path"])
    report_dir = OUTPUT_ROOT / "stage1/reports"
    stage2 = OUTPUT_ROOT / "stage2"
    stage2p = OUTPUT_ROOT / "stage2p"
    stage2pp = OUTPUT_ROOT / "stage2pp"
    summary = stage2 / "features/pose-summary.jsonl"
    interaction = stage2 / "features/pose-interaction.jsonl"
    folding = stage2 / "features/pose-folding-features.jsonl"
    augmented = stage2 / "features/pose-summary-with-folding.jsonl"
    run([str(ROOT / "scripts/stage2_pose_summary.py"), "--records", str(records), "--stage1-report-dir", str(report_dir), "--output", str(summary)])
    run([str(ROOT / "scripts/stage2_pose_interaction.py"), "--records", str(records), "--stage1-report-dir", str(report_dir), "--output", str(interaction), "--fe-atom-index", str(config["fe_atom_index_one_based"]), "--cl-atom-index", str(config["cl_atom_index_one_based"])])
    run([str(ROOT / "scripts/stage2_folding_feature_experiment.py"), "--records", str(records), "--stage1-report-dir", str(report_dir), "--pose-summary", str(summary), "--pose-interaction", str(interaction), "--folding-features", str(folding), "--augmented-pose-summary", str(augmented), "--view-dir", str(stage2 / "folding-views"), "--metrics", str(stage2 / "modeling/folding-metrics.json"), "--predictions", str(stage2 / "modeling/folding-predictions.csv")])
    run([str(ROOT / "scripts/stage2p_representation.py"), "--records", str(records), "--stage1-report-dir", str(report_dir), "--pose-summary", str(summary), "--pose-interaction", str(interaction), "--pose-folding", str(folding), "--features", str(stage2p / "features/stage2p-features.jsonl"), "--manifest", str(stage2p / "features/stage2p-manifest.json"), "--metrics", str(stage2p / "modeling/stage2p-model-metrics.json"), "--predictions", str(stage2p / "modeling/stage2p-predictions.csv"), "--trends", str(stage2p / "modeling/stage2p-trends.csv")])
    run([str(ROOT / "scripts/stage2pp_representation.py"), "--records", str(records), "--stage1-report-dir", str(report_dir), "--stage2p-features", str(stage2p / "features/stage2p-features.jsonl"), "--pose-summary", str(summary), "--pose-interaction", str(interaction), "--pose-folding", str(folding), "--output-dir", str(stage2pp), "--features", str(stage2pp / "features/stage2pp-features.jsonl"), "--manifest", str(stage2pp / "features/stage2pp-manifest.json"), "--metrics", str(stage2pp / "modeling/stage2pp-model-comparison.json"), "--predictions", str(stage2pp / "modeling/stage2pp-predictions.csv"), "--trends", str(stage2pp / "modeling/stage2pp-trends.csv")])
    print(json.dumps({"status": "complete", "output_root": str(OUTPUT_ROOT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

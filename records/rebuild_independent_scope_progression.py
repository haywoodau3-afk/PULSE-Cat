"""Rerun the independent scope-progression analysis with corrected features."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts import scope_progression  # noqa: E402


HERE = Path(__file__).resolve().parent
OUT = HERE / "corrected_project/analysis_runs/independent_progression"
P7_STAGE2P = HERE / "corrected_project/features/p7/stage2p.jsonl"
CMC_STAGE2P = HERE / "corrected_project/features/cmc/stage2p.jsonl"


def run(name: str, **kwargs: object) -> dict:
    output = OUT / name
    result = scope_progression.run_analysis(output_dir=output, **kwargs)
    result["correction_status"] = "rerun with atom-mapped corrected Stage 2p features"
    result["independent_AUC_MAE_claims"] = "recomputed from regenerated learning curves"
    scope_progression.write_json(output / "scope-progression-manifest.json", result)
    print(name, json.dumps(result.get("convergence", {}), sort_keys=True), flush=True)
    return result


def main() -> None:
    p7 = run(
        "p7",
        records_path=ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl",
        stage2p_path=P7_STAGE2P,
        catalyst="fe-p7-cl",
        targets=["ee_percent", "isolated_yield_percent"],
        feature_set="rdkit_morgan_stage2p",
        audit_ids=[],
        audit_fraction=0.0,
        replicates=500,
        seed=20260824,
        late_stage_path=None,
        exclude_ids=["1ad"],
        family_ids=[],
    )
    cmc = run(
        "cmcpor_aryl",
        records_path=ROOT / "data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl",
        stage2p_path=CMC_STAGE2P,
        catalyst="cmcpor-fecl",
        targets=["ee_percent", "isolated_yield_percent"],
        feature_set="rdkit_morgan_stage2p",
        audit_ids=["2y", "2z", "4a", "4b", "4c", "4d", "4e"],
        audit_fraction=0.0,
        replicates=500,
        seed=20260824,
        late_stage_path=None,
        exclude_ids=[],
        family_ids=["angew-aryl-c-h-amination"],
    )
    comparison = {"p7": p7.get("convergence", {}), "cmcpor_aryl": cmc.get("convergence", {})}
    (OUT / "corrected_convergence_comparison.json").write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

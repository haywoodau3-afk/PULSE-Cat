#!/usr/bin/env python3
"""Run leakage-safe P7↔CMC-Por progressive transfer replays."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import (
    canonical_overlap,
    canonical_smiles,
    load_reaction_rows,
    prediction_metrics,
    remove_canonical_overlap,
    run_fixed_prefix,
)


def _filter_cmc_aryl(rows):
    return [row for row in rows if row.family_id == "angew-aryl-c-h-amination"]


def run_bidirectional(
    p7_records: Path,
    cmcpor_records: Path,
    *,
    p7_stage2p: Path | None = None,
    cmcpor_stage2p: Path | None = None,
    p7_catalyst_features: Path | None = None,
    cmcpor_catalyst_features: Path | None = None,
    target: str = "ee_percent",
    arm: str = "B5",
) -> dict:
    p7 = load_reaction_rows(p7_records, catalyst="fe-p7-cl", target=target, include_unlabelled=True, pose_features_path=p7_stage2p, catalyst_features_path=p7_catalyst_features)
    cmc = load_reaction_rows(cmcpor_records, catalyst="cmcpor-fecl", target=target, include_unlabelled=True, pose_features_path=cmcpor_stage2p, catalyst_features_path=cmcpor_catalyst_features)
    cmc_aryl = _filter_cmc_aryl(cmc)
    if len(cmc_aryl) < 4:
        raise ValueError("CMC-Por aryl cohort needs at least four substrates")
    p7_source = remove_canonical_overlap(p7, cmc_aryl)
    cmc_source = remove_canonical_overlap(cmc_aryl, p7)
    directions = {
        "p7_to_cmcpor_aryl": {
            "source": p7_source,
            "target": cmc_aryl,
            "source_domain": "fe-p7-cl",
            "target_domain": "cmcpor-fecl",
        },
        "cmcpor_to_p7_aryl": {
            "source": cmc_source,
            "target": p7,
            "source_domain": "cmcpor-fecl",
            "target_domain": "fe-p7-cl",
        },
    }
    all_shared = canonical_overlap(p7, cmc)
    aryl_shared = canonical_overlap(p7, cmc_aryl)
    report = {
        "schema_version": "pptl-bidirectional-report-v1",
        "target": target,
        "feature_arm": arm,
        "planned_paired_pose_count": 13,
        "shared_canonical_compounds": all_shared,
        "shared_canonical_count": len(all_shared),
        "primary_aryl_shared_canonical_compounds": aryl_shared,
        "primary_aryl_shared_canonical_count": len(aryl_shared),
        "directions": {},
    }
    for name, direction in directions.items():
        overlap_ids = {
            row.substrate_id
            for row in direction["target"]
            if canonical_smiles(row.smiles) in {canonical_smiles(source_row.smiles) for source_row in (p7 if name.startswith("p7_") else cmc_aryl)}
        }
        source_domains = {"combined": direction["source"]}
        source_domains["p7" if name.startswith("p7_") else "cmcpor"] = direction["source"]
        rows = run_fixed_prefix(
            direction["source"],
            direction["target"],
            target_name=target,
            arm=arm,
            source_domains=source_domains,
        )
        report["directions"][name] = {
            "source_domain": direction["source_domain"],
            "target_domain": direction["target_domain"],
            "source_count": len(direction["source"]),
            "target_count": len(direction["target"]),
            "excluded_canonical_overlap_count": len(overlap_ids),
            "excluded_canonical_substrate_ids": sorted(overlap_ids),
            "target_only": prediction_metrics(rows, "target_only"),
            "guarded_ensemble": {
                "count": len(rows),
                "mae": sum(float(row["ensemble_absolute_error"]) for row in rows) / len(rows),
            },
            "rows": rows,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p7-records", type=Path, required=True)
    parser.add_argument("--cmcpor-records", type=Path, required=True)
    parser.add_argument("--p7-stage2p", type=Path)
    parser.add_argument("--cmcpor-stage2p", type=Path)
    parser.add_argument("--p7-catalyst-features", type=Path)
    parser.add_argument("--cmcpor-catalyst-features", type=Path)
    parser.add_argument("--target", choices=("ee_percent", "isolated_yield_percent"), default="ee_percent")
    parser.add_argument("--feature-arm", default="B5")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_bidirectional(args.p7_records, args.cmcpor_records, p7_stage2p=args.p7_stage2p, cmcpor_stage2p=args.cmcpor_stage2p, p7_catalyst_features=args.p7_catalyst_features, cmcpor_catalyst_features=args.cmcpor_catalyst_features, target=args.target, arm=args.feature_arm)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"shared_canonical_count": report["shared_canonical_count"], "primary_aryl_shared_canonical_count": report["primary_aryl_shared_canonical_count"], "directions": {key: value["target_only"] for key, value in report["directions"].items()}}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

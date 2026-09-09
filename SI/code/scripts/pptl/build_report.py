#!/usr/bin/env python3
"""Assemble a compact Markdown report from PPTL machine-readable artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_report(fixed_prefix: Path | None = None, pose_ablation: Path | None = None, bidirectional: Path | None = None, matrix: Path | None = None, scaffold: list[Path] | None = None, bootstrap: list[Path] | None = None, routes: list[Path] | None = None, route_bootstrap: list[Path] | None = None, pose_controls: Path | None = None, resource: Path | None = None, pose_upgrade: Path | None = None, yield_matrix: Path | None = None, pose_upgrade_yield: Path | None = None, pose_incremental: list[Path] | None = None, route_incremental: list[Path] | None = None) -> str:
    lines = ["# PPTL computational report", "", "Status: generated from persisted artifacts", ""]
    if fixed_prefix and fixed_prefix.exists():
        rows = _read_jsonl(fixed_prefix)
        lines.extend(["## Fixed-prefix replay", "", f"- Prediction rows: {len(rows)}"])
        if rows:
            target_errors = [abs(float(row["predictions"]["target_only"]) - float(row["observed"])) for row in rows]
            ensemble_errors = [float(row["ensemble_absolute_error"]) for row in rows]
            lines.extend([f"- Target-only MAE: {sum(target_errors) / len(target_errors):.3f}", f"- Guarded-ensemble MAE: {sum(ensemble_errors) / len(ensemble_errors):.3f}"])
        lines.append("")
    if pose_ablation and pose_ablation.exists():
        report = json.loads(pose_ablation.read_text(encoding="utf-8"))
        lines.extend(["## Pose ablation", "", "| Arm | Target-only MAE | Guarded MAE |", "| --- | ---: | ---: |"])
        for arm, values in sorted(report.items()):
            target = values.get("target_only", {}).get("mae")
            guarded = values.get("guarded_ensemble", {}).get("mae")
            lines.append(f"| {arm} | {target if target is not None else 'blocked'} | {guarded if guarded is not None else 'blocked'} |")
        lines.append("")
    if bidirectional and bidirectional.exists():
        report = json.loads(bidirectional.read_text(encoding="utf-8"))
        lines.extend(["## Bidirectional aryl replay", "", f"- Planned paired pose panel: {report.get('planned_paired_pose_count', 'unspecified')}", f"- Canonical pairs in current ledger: {report.get('shared_canonical_count', 0)}", f"- Canonical aryl pairs: {report.get('primary_aryl_shared_canonical_count', 0)}", "", "| Direction | Target-only MAE | Guarded MAE | Excluded overlaps |", "| --- | ---: | ---: | ---: |"])
        for direction, values in sorted(report.get("directions", {}).items()):
            rows = values.get("rows", [])
            guarded = (sum(float(row["ensemble_absolute_error"]) for row in rows) / len(rows)) if rows else None
            target = values.get("target_only", {}).get("mae")
            lines.append(f"| {direction} | {target if target is not None else 'blocked'} | {guarded if guarded is not None else 'blocked'} | {values.get('excluded_canonical_overlap_count', 0)} |")
        lines.append("")
    if matrix and matrix.exists():
        report = json.loads(matrix.read_text(encoding="utf-8"))
        lines.extend(["## Feature-arm matrix", "", "| Arm | Direction | Target-only MAE | Guarded MAE | n |", "| --- | --- | ---: | ---: | ---: |"])
        for arm, arm_report in sorted(report.get("arms", {}).items()):
            for direction, values in sorted(arm_report.get("directions", {}).items()):
                rows = values.get("rows", [])
                guarded = (sum(float(row["ensemble_absolute_error"]) for row in rows) / len(rows)) if rows else None
                target = values.get("target_only", {}).get("mae")
                lines.append(f"| {arm} | {direction} | {target if target is not None else 'blocked'} | {guarded if guarded is not None else 'blocked'} | {len(rows)} |")
        lines.append("")
    if yield_matrix and yield_matrix.exists():
        report = json.loads(yield_matrix.read_text(encoding="utf-8"))
        lines.extend(["## Yield feature-arm matrix", "", "| Arm | Direction | Target-only MAE | Guarded MAE | n |", "| --- | --- | ---: | ---: | ---: |"])
        for arm, arm_report in sorted(report.get("arms", {}).items()):
            for direction, values in sorted(arm_report.get("directions", {}).items()):
                rows = values.get("rows", [])
                guarded = (sum(float(row["ensemble_absolute_error"]) for row in rows) / len(rows)) if rows else None
                lines.append(f"| {arm} | {direction} | {values.get('target_only', {}).get('mae')} | {guarded} | {len(rows)} |")
        lines.append("")
    if scaffold:
        lines.extend(["## Scaffold-held-out replay", "", "| Direction | Scaffold groups | Predictions | Target-only MAE | Combined MAE | Guarded MAE |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
        for path in scaffold:
            if not path.exists():
                continue
            report = json.loads(path.read_text(encoding="utf-8"))
            lines.append(f"| {report.get('source_domain')} → {report.get('target_domain')} | {report.get('scaffold_count')} | {report.get('row_count')} | {report.get('target_only', {}).get('mae')} | {report.get('combined', {}).get('mae')} | {report.get('guarded_mae')} |")
        lines.append("")
    if bootstrap:
        lines.extend(["## Scaffold-bootstrap intervals", "", "| Direction | Delta | Mean | 2.5% | 97.5% |", "| --- | --- | ---: | ---: | ---: |"])
        for path in bootstrap:
            if not path.exists():
                continue
            report = json.loads(path.read_text(encoding="utf-8"))
            direction = f"{report.get('source_domain')} → {report.get('target_domain')}"
            for name, interval in sorted(report.get("delta_intervals", {}).items()):
                lines.append(f"| {direction} | {name} | {interval.get('mean')} | {interval.get('lower_2.5')} | {interval.get('upper_97.5')} |")
        lines.append("")
    if routes:
        lines.extend(["## Random-route replicate summaries", "", "| Target | Arm | Direction | Routes | Mean MAE | Mean guarded AUC | Mean target AUC |", "| --- | --- | --- | ---: | ---: | ---: | ---: |"])
        for path in routes:
            if not path.exists():
                continue
            report = json.loads(path.read_text(encoding="utf-8"))
            for direction, value in sorted(report.get("directions", {}).items()):
                replicates = value.get("replicates", [])
                mean_mae = sum(item["guarded"]["mae"] for item in replicates) / len(replicates) if replicates else None
                mean_guarded_auc = sum(item["guarded"]["auc_mae"] for item in replicates) / len(replicates) if replicates else None
                mean_target_auc = sum(item["target_only"]["auc_mae"] for item in replicates) / len(replicates) if replicates else None
                lines.append(f"| {report.get('target')} | {report.get('feature_arm')} | {direction} | {len(replicates)} | {mean_mae} | {mean_guarded_auc} | {mean_target_auc} |")
        lines.append("")
    if route_bootstrap:
        lines.extend(["## Random-route bootstrap intervals", "", "| Target | Arm | Direction | Delta | Mean | 2.5% | 97.5% |", "| --- | --- | --- | --- | ---: | ---: | ---: |"])
        for path in route_bootstrap:
            if not path.exists():
                continue
            report = json.loads(path.read_text(encoding="utf-8"))
            for direction, value in sorted(report.get("directions", {}).items()):
                for metric in ("mae_delta_guarded_minus_target", "auc_delta_guarded_minus_target"):
                    interval = value["intervals"][metric]
                    lines.append(f"| {report.get('target')} | {report.get('feature_arm')} | {direction} | {metric} | {interval['mean']} | {interval['lower_2.5']} | {interval['upper_97.5']} |")
        lines.append("")
    if route_incremental:
        lines.extend(["## Matched-route incremental pose bootstrap", "", "| Pose arm | Direction | MAE delta vs B5 | AUC delta vs B5 |", "| --- | --- | ---: | ---: |"])
        for path in route_incremental:
            if not path.exists():
                continue
            report = json.loads(path.read_text(encoding="utf-8"))
            for direction, value in sorted(report.get("directions", {}).items()):
                intervals = value.get("intervals", {})
                lines.append(f"| {report.get('pose_arm')} | {direction} | {intervals.get('mae_delta_pose_minus_b5', {}).get('mean')} [{intervals.get('mae_delta_pose_minus_b5', {}).get('lower_2.5')}, {intervals.get('mae_delta_pose_minus_b5', {}).get('upper_97.5')}] | {intervals.get('auc_delta_pose_minus_b5', {}).get('mean')} [{intervals.get('auc_delta_pose_minus_b5', {}).get('lower_2.5')}, {intervals.get('auc_delta_pose_minus_b5', {}).get('upper_97.5')}] |")
        lines.append("")
    if pose_controls and pose_controls.exists():
        report = json.loads(pose_controls.read_text(encoding="utf-8"))
        lines.extend(["## Pose controls", "", "| Direction | Arm | Target-only MAE | Combined MAE | Guarded MAE |", "| --- | --- | ---: | ---: | ---: |"])
        for direction, arms in sorted(report.get("directions", {}).items()):
            for arm, values in sorted(arms.items()):
                lines.append(f"| {direction} | {arm} | {values.get('target_only_mae')} | {values.get('combined_mae')} | {values.get('guarded_mae')} |")
        lines.append("")
    if pose_upgrade and pose_upgrade.exists():
        report = json.loads(pose_upgrade.read_text(encoding="utf-8"))
        lines.extend(["## Compact pose residual upgrade", "", f"- Pose arm: {report.get('pose_arm')}; compact feature count: {report.get('pose_feature_count')}", "", "| Direction | B5 target MAE | Residual-pose target MAE | Direct compact-pose pooled MAE | Guarded residual-pose MAE |", "| --- | ---: | ---: | ---: | ---: |"])
        for direction, values in sorted(report.get("directions", {}).items()):
            metrics = values.get("metrics", {})
            lines.append(f"| {direction} | {metrics.get('target_b5', {}).get('mae')} | {metrics.get('target_residual_pose', {}).get('mae')} | {metrics.get('direct_p3_pooled', {}).get('mae')} | {metrics.get('guarded_residual_pose', {}).get('mae')} |")
        lines.extend(["", "Pose is evaluated as a cross-fitted residual correction and as a compact direct augmentation. The raw 248-column concatenation remains a diagnostic control.", ""])
    if pose_upgrade_yield and pose_upgrade_yield.exists():
        report = json.loads(pose_upgrade_yield.read_text(encoding="utf-8"))
        lines.extend(["## Yield compact pose residual upgrade", "", "| Direction | B5 target MAE | Residual-pose target MAE | Guarded residual-pose MAE |", "| --- | ---: | ---: | ---: |"])
        for direction, values in sorted(report.get("directions", {}).items()):
            metrics = values.get("metrics", {})
            lines.append(f"| {direction} | {metrics.get('target_b5', {}).get('mae')} | {metrics.get('target_residual_pose', {}).get('mae')} | {metrics.get('guarded_residual_pose', {}).get('mae')} |")
        lines.append("")
    if pose_incremental:
        lines.extend(["## Scaffold incremental pose bootstrap", "", "| Pose arm | Direction | Target MAE delta vs B5 | Guarded MAE delta vs B5 |", "| --- | --- | ---: | ---: |"])
        for path in pose_incremental:
            if not path.exists():
                continue
            report = json.loads(path.read_text(encoding="utf-8"))
            target = report.get("delta_intervals", {}).get("target_delta", {})
            guarded = report.get("delta_intervals", {}).get("guarded_delta", {})
            lines.append(f"| {report.get('pose_arm')} | {report.get('source_domain')} → {report.get('target_domain')} | {target.get('mean')} [{target.get('lower_2.5')}, {target.get('upper_97.5')}] | {guarded.get('mean')} [{guarded.get('lower_2.5')}, {guarded.get('upper_97.5')}] |")
        lines.append("")
    if resource and resource.exists():
        report = json.loads(resource.read_text(encoding="utf-8"))
        lines.extend(["## Resource ledger", "", "| Domain | Arm | Features | Feature seconds | Peak RSS (bytes) |", "| --- | --- | ---: | ---: | ---: |"])
        for domain, arms in sorted(report.get("domains", {}).items()):
            for arm, values in sorted(arms.items()):
                lines.append(f"| {domain} | {arm} | {values.get('features')} | {values.get('seconds')} | {values.get('peak_rss_bytes')} |")
        lines.append("")
    lines.extend(["## Evidence boundary", "", "This report represents a computational, label-masked replay. It is not prospective wet-lab validation and does not establish a GNN head-to-head result.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixed-prefix", type=Path)
    parser.add_argument("--pose-ablation", type=Path)
    parser.add_argument("--bidirectional", type=Path)
    parser.add_argument("--matrix", type=Path)
    parser.add_argument("--scaffold", type=Path, action="append")
    parser.add_argument("--bootstrap", type=Path, action="append")
    parser.add_argument("--routes", type=Path, action="append")
    parser.add_argument("--route-bootstrap", type=Path, action="append")
    parser.add_argument("--pose-controls", type=Path)
    parser.add_argument("--resource", type=Path)
    parser.add_argument("--pose-upgrade", type=Path)
    parser.add_argument("--yield-matrix", type=Path)
    parser.add_argument("--pose-upgrade-yield", type=Path)
    parser.add_argument("--pose-incremental", type=Path, action="append")
    parser.add_argument("--route-incremental", type=Path, action="append")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_report(args.fixed_prefix, args.pose_ablation, args.bidirectional, args.matrix, args.scaffold, args.bootstrap, args.routes, args.route_bootstrap, args.pose_controls, args.resource, args.pose_upgrade, args.yield_matrix, args.pose_upgrade_yield, args.pose_incremental, args.route_incremental), encoding="utf-8")
    print(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

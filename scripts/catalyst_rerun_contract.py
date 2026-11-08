#!/usr/bin/env python3
"""Audit the inputs required for catalyst-specific Stage 0--2p/2pp reruns."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data/expansion/catalyst_rerun/rerun-manifest.json"
DEFAULT_SUBSTRATES = ROOT / "data/expansion/catalyst_rerun/substrates.jsonl"
DEFAULT_OUTCOMES = ROOT / "data/expansion/catalyst_rerun/outcomes.jsonl"
EXPECTED_CATALYSTS = {"cmcpor-fecl", "d4-por-fecl"}
MODELABLE_EE_STATUSES = {"reported", "true_zero"}


class ContractError(ValueError):
    """Raised when an input bundle violates the rerun contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"expected JSON object in {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ContractError(f"JSONL row at {path}:{line_number} must be an object")
        rows.append(value)
    return rows


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _number(value: Any, field: str) -> None:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    _require(0 <= value <= 100, f"{field} must be between 0 and 100")


def validate_manifest(manifest: dict[str, Any]) -> None:
    _require(manifest.get("schema_version") == "catalyst-rerun-inputs-v1", "unsupported rerun manifest schema")
    scope = manifest.get("scope")
    _require(isinstance(scope, dict), "manifest is missing scope")
    _require(scope.get("aryl_entries") == "2a-2ac plus 4a-4e", "manifest must include both aryl tables")
    _require(scope.get("sulfonyl_entries") == "6a-6q", "manifest must include the full sulfonyl table")
    catalysts = manifest.get("catalysts")
    _require(isinstance(catalysts, list), "manifest is missing catalysts")
    catalyst_ids = {row.get("catalyst_id") for row in catalysts if isinstance(row, dict)}
    _require(catalyst_ids == EXPECTED_CATALYSTS, "manifest must declare exactly cmcpor-fecl and d4-por-fecl")
    for row in catalysts:
        _require(isinstance(row.get("paper_label"), str) and row["paper_label"], "catalyst paper_label is required")
        _require("reference_geometry_path" in row, f"{row.get('catalyst_id')}: reference_geometry_path is required")
        _require("constraint_profile_path" in row, f"{row.get('catalyst_id')}: constraint_profile_path is required")
    protocol = manifest.get("protocol")
    _require(isinstance(protocol, dict), "manifest is missing protocol")
    for field, expected in (("pool_size", 5000), ("retain_low_count", 100), ("retain_high_count", 100)):
        _require(protocol.get(field) == expected, f"protocol.{field} must remain {expected}")


def validate_substrate_record(record: dict[str, Any]) -> None:
    required = {
        "compound_id",
        "paper_substrate_id",
        "pathway_id",
        "family_id",
        "azide_smiles",
        "nitrene_smiles",
        "atom_mapped_substrate_smiles",
        "reported_reactive_site_atom_map_id",
        "candidate_site_atom_map_ids",
        "source",
    }
    missing = required - record.keys()
    _require(not missing, f"substrate is missing fields: {sorted(missing)}")
    for field in ("compound_id", "paper_substrate_id", "family_id", "azide_smiles", "nitrene_smiles", "atom_mapped_substrate_smiles"):
        _require(isinstance(record[field], str) and record[field], f"substrate.{field} must be non-empty")
    _require(record["pathway_id"] in {"aryl", "sulfonyl"}, "substrate.pathway_id must be aryl or sulfonyl")
    candidate_ids = record["candidate_site_atom_map_ids"]
    _require(isinstance(candidate_ids, list) and candidate_ids, "candidate_site_atom_map_ids must be a non-empty list")
    _require(all(isinstance(value, int) and value > 0 for value in candidate_ids), "candidate site ids must be positive integers")
    reported_id = record["reported_reactive_site_atom_map_id"]
    _require(isinstance(reported_id, int) and reported_id > 0, "reported_reactive_site_atom_map_id is required")
    _require(reported_id in candidate_ids, "reported reactive site must be in candidate_site_atom_map_ids")
    source = record["source"]
    _require(isinstance(source, dict), "substrate.source must be an object")
    for field in ("document_id", "location"):
        _require(isinstance(source.get(field), str) and source[field], f"substrate.source.{field} is required")


def validate_outcome_record(record: dict[str, Any]) -> None:
    required = {
        "compound_id",
        "paper_substrate_id",
        "catalyst_id",
        "condition_id",
        "record_role",
        "isolated_yield_percent",
        "yield_status",
        "ee_percent",
        "ee_status",
        "feasibility_status",
        "source",
    }
    missing = required - record.keys()
    _require(not missing, f"outcome is missing fields: {sorted(missing)}")
    _require(record["catalyst_id"] in EXPECTED_CATALYSTS, f"unknown catalyst_id: {record['catalyst_id']}")
    _require(record["record_role"] in {"primary_scope", "auxiliary_screen"}, "invalid outcome record_role")
    _require(record["yield_status"] in {"exact", "trace", "less_than", "not_reported", "not_applicable"}, "invalid yield_status")
    _require(record["ee_status"] in {"reported", "true_zero", "unresolved", "not_applicable"}, "invalid ee_status")
    _require(record["feasibility_status"] in {"productive", "nonproductive", "unknown"}, "invalid feasibility_status")
    if record["isolated_yield_percent"] is not None:
        _number(record["isolated_yield_percent"], "isolated_yield_percent")
    if record["ee_percent"] is not None:
        _number(record["ee_percent"], "ee_percent")
    if record["yield_status"] == "exact":
        _require(record["isolated_yield_percent"] is not None, "exact yield requires a numeric value")
    if record["ee_status"] in MODELABLE_EE_STATUSES:
        _require(record["ee_percent"] is not None, "modelable ee status requires a numeric value")
    if record["ee_status"] == "true_zero":
        _require(record["ee_percent"] == 0, "true_zero ee must have value 0")
    if record["ee_status"] in {"unresolved", "not_applicable"}:
        _require(record["ee_percent"] is None, "unresolved ee must be null")
    source = record["source"]
    _require(isinstance(source, dict), "outcome.source must be an object")
    for field in ("document_id", "location"):
        _require(isinstance(source.get(field), str) and source[field], f"outcome.source.{field} is required")


def _resolved_path(value: Any) -> Path | None:
    if value in (None, ""):
        return None
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def audit_inputs(manifest_path: Path, substrates_path: Path, outcomes_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    validate_manifest(manifest)
    substrates = load_jsonl(substrates_path)
    outcomes = load_jsonl(outcomes_path)
    for record in substrates:
        validate_substrate_record(record)
    for record in outcomes:
        validate_outcome_record(record)

    substrate_ids = {record["compound_id"] for record in substrates}
    outcome_pairs = {(record["compound_id"], record["catalyst_id"]) for record in outcomes}
    duplicate_substrates = len(substrate_ids) != len(substrates)
    duplicate_outcomes = len(outcome_pairs) != len(outcomes)
    missing_reference_geometry = []
    missing_constraint_profile = []
    for catalyst in manifest["catalysts"]:
        catalyst_id = catalyst["catalyst_id"]
        geometry_path = _resolved_path(catalyst.get("reference_geometry_path"))
        profile_path = _resolved_path(catalyst.get("constraint_profile_path"))
        if geometry_path is None or not geometry_path.is_file():
            missing_reference_geometry.append(catalyst_id)
        if profile_path is None or not profile_path.is_file():
            missing_constraint_profile.append(catalyst_id)

    required_pairs = {(compound_id, catalyst_id) for compound_id in substrate_ids for catalyst_id in EXPECTED_CATALYSTS}
    missing_outcome_pairs = sorted(required_pairs - outcome_pairs)
    blocked = bool(
        missing_reference_geometry
        or missing_constraint_profile
        or not substrates
        or not outcomes
        or duplicate_substrates
        or duplicate_outcomes
        or missing_outcome_pairs
    )
    return {
        "status": "blocked_missing_inputs" if blocked else "ready_for_stage1_pilot",
        "manifest_path": str(manifest_path),
        "substrates_path": str(substrates_path),
        "outcomes_path": str(outcomes_path),
        "substrate_count": len(substrates),
        "outcome_count": len(outcomes),
        "catalyst_ids": sorted(EXPECTED_CATALYSTS),
        "missing_reference_geometry": missing_reference_geometry,
        "missing_constraint_profile": missing_constraint_profile,
        "missing_outcome_pairs": [list(pair) for pair in missing_outcome_pairs],
        "duplicate_substrate_records": duplicate_substrates,
        "duplicate_outcome_records": duplicate_outcomes,
        "protocol": manifest["protocol"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--substrates", type=Path, default=DEFAULT_SUBSTRATES)
    parser.add_argument("--outcomes", type=Path, default=DEFAULT_OUTCOMES)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = audit_inputs(args.manifest, args.substrates, args.outcomes)
    except ContractError as exc:
        print(json.dumps({"status": "invalid_contract", "error": str(exc)}, indent=2))
        return 2
    output = json.dumps(report, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report["status"] == "ready_for_stage1_pilot" else 1


if __name__ == "__main__":
    raise SystemExit(main())

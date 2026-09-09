#!/usr/bin/env python3
"""Validate the bidirectional PPTL contract; D4 is an optional extension."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = Path(__file__).with_name("pptl-contract.json")


def _path(value: str | None) -> Path | None:
    if value in (None, ""):
        return None
    candidate = Path(value)
    return candidate if candidate.is_absolute() else ROOT / candidate


def validate_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if contract.get("schema_version") != "pptl-contract-v2":
        errors.append("unsupported schema_version")
    if contract.get("source_domains") != ["fe-p7-cl", "cmcpor-fecl"]:
        errors.append("source_domains must be P7 and CMC-Por in that order")
    if contract.get("primary_pathway") != "aryl":
        errors.append("primary_pathway must be aryl")
    directions = contract.get("primary_directions", [])
    expected = {
        ("fe-p7-cl", "cmcpor-fecl", "aryl"),
        ("cmcpor-fecl", "fe-p7-cl", "aryl"),
    }
    observed = {(item.get("source_domain"), item.get("target_domain"), item.get("pathway")) for item in directions}
    if observed != expected:
        errors.append("primary_directions must contain reciprocal P7/CMC-Por aryl directions")
    progression = contract.get("progression", {})
    if progression.get("unit") != "whole_substrate" or progression.get("seed_size") != 2:
        errors.append("progression must use a two-substrate whole-substrate seed")
    representations = contract.get("representations", {})
    expected_arms = {"B0", "B1", "B2", "B3", "B4", "B5", "P0", "P1", "P2", "P3", "P4", "PX"}
    if set(representations.get("arms", [])) != expected_arms:
        errors.append("representation arms do not match the frozen PPTL ladder")

    missing: list[str] = []
    for label, value in contract.get("records", {}).items():
        candidate = _path(value)
        if candidate is None or not candidate.is_file():
            missing.append(f"records.{label}")
    for label, value in contract.get("catalyst_feature_records", {}).items():
        if label == "aggregation":
            continue
        candidate = _path(value)
        if candidate is None or not candidate.is_file() or candidate.stat().st_size == 0:
            missing.append(f"catalyst_feature_records.{label}")
    d4 = contract.get("deferred_d4_extension", {})
    d4_missing: list[str] = []
    for label in ("substrates", "outcomes", "reference_geometry", "constraint_profile"):
        candidate = _path(d4.get(label))
        if candidate is None or not candidate.is_file() or (label in ("substrates", "outcomes") and candidate.stat().st_size == 0):
            d4_missing.append(f"deferred_d4_extension.{label}")
    status = "valid" if not errors and not missing else "invalid"
    return {
        "schema_version": "pptl-contract-validation-v1",
        "contract_path": str(path),
        "status": status,
        "errors": errors,
        "missing": missing,
        "deferred_d4_status": "ready" if not d4_missing else "deferred_missing_inputs",
        "deferred_d4_missing": d4_missing,
        "study_id": contract.get("study_id"),
        "source_domains": contract.get("source_domains"),
        "primary_directions": contract.get("primary_directions"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_contract(args.contract)
    destination = args.output or args.contract.parent / "contract-validation.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] != "invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())

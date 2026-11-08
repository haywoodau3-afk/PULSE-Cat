#!/usr/bin/env python3
"""Validate the cross-paper reaction-record and transfer-study contract."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "data" / "expansion" / "expansion-contract.json"
DEFAULT_SCHEMA = ROOT / "data" / "expansion" / "schema" / "reaction-record.schema.json"
DEFAULT_RECORDS = ROOT / "data" / "expansion" / "records.jsonl"

EXPECTED_DOMAINS = {
    "jacs_2025_aryl_p7_thermal",
    "angew_2023_aryl_photochemical",
    "angew_2023_sulfonyl_photochemical",
}
EXPECTED_TRANSFER_DIRECTIONS = {
    "jacs_aryl_to_angew_aryl",
    "angew_aryl_to_jacs_aryl",
    "jacs_aryl_to_angew_sulfonyl",
    "angew_sulfonyl_to_angew_aryl",
}
EXPECTED_RECORD_ROLES = {"primary_scope", "auxiliary_screen"}
MODELABLE_EE_STATUSES = {"reported", "true_zero"}
TOP_LEVEL_FIELDS = {
    "compound_id",
    "reaction_id",
    "paper_id",
    "domain_id",
    "pathway_id",
    "catalyst_id",
    "condition_id",
    "record_role",
    "split_group",
    "family",
    "substrate",
    "outcome",
    "conditions",
    "source",
}
SUBSTRATE_FIELDS = {"paper_substrate_id", "smiles", "product_smiles", "structure_status"}
OUTCOME_FIELDS = {
    "feasibility_status",
    "isolated_yield_percent",
    "yield_status",
    "ee_percent",
    "ee_status",
    "major_product_configuration",
    "configuration_status",
    "notes",
}
SOURCE_FIELDS = {"document_id", "location", "confidence"}
CONDITION_FIELDS = {"temperature_c", "solvent", "light", "atmosphere", "additives"}
FAMILY_FIELDS = {"family_id", "family_label"}


class ContractError(ValueError):
    """Raised when a contract or reaction record violates the public contract."""


def check_local_python_environment(root: Path = ROOT) -> dict[str, Any]:
    """Require the repository-local Python environment before validating data."""

    environment_dir = (root / ".venv").resolve()
    python_path = environment_dir / "bin" / "python"
    config_path = environment_dir / "pyvenv.cfg"
    if not environment_dir.is_dir() or not python_path.is_file() or not config_path.is_file():
        raise ContractError(
            "local virtual environment is missing; expected "
            f"{environment_dir}. Create it with: {sys.executable} scripts/environment_contract.py --create"
        )
    if not python_path.stat().st_mode & 0o111:
        raise ContractError(f"local virtual environment Python is not executable: {python_path}")
    return {
        "status": "present",
        "environment_dir": str(environment_dir),
        "python_executable": str(python_path),
        "running_python": str(Path(sys.executable).resolve()),
        "running_python_is_local": Path(sys.executable).resolve() == python_path.resolve(),
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"expected an object in {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ContractError(f"record at {path}:{line_number} must be an object")
        records.append(value)
    return records


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def validate_contract(contract: dict[str, Any]) -> None:
    _require(contract.get("schema_version") == "expansion-contract-v1", "unsupported contract schema_version")
    domains = contract.get("domains")
    _require(isinstance(domains, list) and len(domains) == 3, "contract must declare three coherent domains")
    domain_ids = {domain.get("domain_id") for domain in domains if isinstance(domain, dict)}
    _require(domain_ids == EXPECTED_DOMAINS, "contract domains do not match the three coherent domains")

    record_roles = set(contract.get("record_roles", []))
    _require(record_roles == EXPECTED_RECORD_ROLES, "contract record_roles must contain primary_scope and auxiliary_screen")

    transfer = contract.get("transfer_study")
    _require(isinstance(transfer, dict), "contract is missing transfer_study")
    directions = set(transfer.get("directions", []))
    _require(directions == EXPECTED_TRANSFER_DIRECTIONS, "contract must declare four transfer directions")
    _require(transfer.get("required_baselines"), "transfer study must declare required baselines")
    _require(transfer.get("feature_ablation_required") is True, "feature ablation is required for transfer")

    evaluation = contract.get("evaluation")
    _require(isinstance(evaluation, dict), "contract is missing evaluation")
    _require(evaluation.get("ee_primary_metric") == "mae", "ee primary metric must be mae")
    _require(
        evaluation.get("ee_mae_relative_improvement_gate") == 0.10,
        "ee transfer gate must be 10 percent",
    )
    _require(evaluation.get("paper_held_out_test_required") is True, "paper-held-out test is required")


def _domain_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {domain["domain_id"]: domain for domain in contract["domains"]}


def _validate_numeric_range(value: Any, field: str, record_id: str) -> None:
    if value is None:
        return
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric or null in {record_id}")
    _require(0 <= value <= 100, f"{field} must be between 0 and 100 in {record_id}")


def validate_record(record: dict[str, Any], contract: dict[str, Any], seen_reaction_ids: set[str] | None = None) -> None:
    required = {
        "compound_id",
        "reaction_id",
        "paper_id",
        "domain_id",
        "pathway_id",
        "catalyst_id",
        "condition_id",
        "record_role",
        "split_group",
        "substrate",
        "outcome",
        "source",
    }
    missing = required - record.keys()
    _require(not missing, f"record is missing required fields: {sorted(missing)}")
    _require(not (set(record) - TOP_LEVEL_FIELDS), f"unknown record fields in {record.get('reaction_id', '<unknown>')}: {sorted(set(record) - TOP_LEVEL_FIELDS)}")
    record_id = str(record.get("reaction_id"))
    _require(isinstance(record["compound_id"], str) and record["compound_id"], f"compound_id must be non-empty in {record_id}")
    _require(isinstance(record["reaction_id"], str) and record["reaction_id"], "reaction_id must be non-empty")
    if seen_reaction_ids is not None:
        _require(record_id not in seen_reaction_ids, f"duplicate reaction_id: {record_id}")
        seen_reaction_ids.add(record_id)

    domain_id = record["domain_id"]
    domains = _domain_map(contract)
    _require(domain_id in domains, f"unknown domain_id in {record_id}: {domain_id}")
    domain = domains[domain_id]
    _require(record["paper_id"] == domain["paper_id"], f"paper_id does not match domain in {record_id}")
    _require(record["pathway_id"] == domain["pathway_id"], f"pathway_id does not match domain in {record_id}")
    _require(record["catalyst_id"] in domain["catalyst_ids"], f"catalyst is not allowed in domain in {record_id}")
    _require(record["record_role"] in EXPECTED_RECORD_ROLES, f"invalid record_role in {record_id}")
    _require(isinstance(record["split_group"], str) and record["split_group"], f"split_group must be non-empty in {record_id}")
    if "family" in record:
        family = record["family"]
        _require(isinstance(family, dict), f"family must be an object in {record_id}")
        _require(not (set(family) - FAMILY_FIELDS), f"unknown family fields in {record_id}: {sorted(set(family) - FAMILY_FIELDS)}")
        for field in FAMILY_FIELDS:
            _require(isinstance(family.get(field), str) and family[field], f"family.{field} is required in {record_id}")

    substrate = record["substrate"]
    _require(isinstance(substrate, dict), f"substrate must be an object in {record_id}")
    _require(not (set(substrate) - SUBSTRATE_FIELDS), f"unknown substrate fields in {record_id}: {sorted(set(substrate) - SUBSTRATE_FIELDS)}")
    _require(isinstance(substrate.get("paper_substrate_id"), str) and substrate["paper_substrate_id"], f"paper_substrate_id is required in {record_id}")

    outcome = record["outcome"]
    _require(isinstance(outcome, dict), f"outcome must be an object in {record_id}")
    _require(not (set(outcome) - OUTCOME_FIELDS), f"unknown outcome fields in {record_id}: {sorted(set(outcome) - OUTCOME_FIELDS)}")
    _require(outcome.get("feasibility_status") in {"productive", "nonproductive", "unknown"}, f"invalid feasibility status in {record_id}")
    _require(outcome.get("yield_status") in {"exact", "trace", "less_than", "not_reported", "not_applicable"}, f"invalid yield status in {record_id}")
    _require(outcome.get("ee_status") in {"reported", "true_zero", "unresolved", "not_applicable"}, f"invalid ee status in {record_id}")
    _validate_numeric_range(outcome.get("isolated_yield_percent"), "isolated_yield_percent", record_id)
    _validate_numeric_range(outcome.get("ee_percent"), "ee_percent", record_id)

    yield_status = outcome["yield_status"]
    yield_value = outcome.get("isolated_yield_percent")
    if yield_status == "exact":
        _require(yield_value is not None, f"exact yield requires a numeric value in {record_id}")
    if yield_status in {"not_reported", "not_applicable"}:
        _require(yield_value is None, f"unreported yield must be null in {record_id}")

    ee_status = outcome["ee_status"]
    ee_value = outcome.get("ee_percent")
    if ee_status in MODELABLE_EE_STATUSES:
        _require(ee_value is not None, f"modelable ee status requires a numeric value in {record_id}")
    if ee_status == "true_zero":
        _require(ee_value == 0, f"true_zero ee must have value 0 in {record_id}")
    if ee_status in {"unresolved", "not_applicable"}:
        _require(ee_value is None, f"unresolved ee must be null in {record_id}")

    configuration = outcome.get("major_product_configuration")
    configuration_status = outcome.get("configuration_status")
    if configuration_status == "reported":
        _require(isinstance(configuration, str) and configuration, f"reported configuration is required in {record_id}")
    if configuration_status in {"unresolved", "not_applicable"}:
        _require(configuration is None, f"unresolved configuration must be null in {record_id}")

    source = record["source"]
    _require(isinstance(source, dict), f"source must be an object in {record_id}")
    _require(not (set(source) - SOURCE_FIELDS), f"unknown source fields in {record_id}: {sorted(set(source) - SOURCE_FIELDS)}")
    for field in ("document_id", "location", "confidence"):
        _require(isinstance(source.get(field), str) and source[field], f"source.{field} is required in {record_id}")
    _require(source["confidence"] in {"primary_table", "supporting_information", "new_experiment"}, f"invalid source confidence in {record_id}")

    if "conditions" in record:
        conditions = record["conditions"]
        _require(isinstance(conditions, dict), f"conditions must be an object in {record_id}")
        _require(not (set(conditions) - CONDITION_FIELDS), f"unknown condition fields in {record_id}: {sorted(set(conditions) - CONDITION_FIELDS)}")
        if "additives" in conditions:
            _require(
                isinstance(conditions["additives"], list)
                and all(isinstance(additive, str) for additive in conditions["additives"]),
                f"conditions.additives must be a string list in {record_id}",
            )


def validate_records(records: Iterable[dict[str, Any]], contract: dict[str, Any]) -> list[dict[str, Any]]:
    validate_contract(contract)
    materialized = list(records)
    seen_reaction_ids: set[str] = set()
    compound_to_split: dict[str, str] = {}
    for record in materialized:
        validate_record(record, contract, seen_reaction_ids)
        compound_id = record["compound_id"]
        split_group = record["split_group"]
        previous = compound_to_split.setdefault(compound_id, split_group)
        _require(previous == split_group, f"compound_id {compound_id} has inconsistent split_group")
    return materialized


def summarize_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    materialized = list(records)
    domain_counts = Counter(record["domain_id"] for record in materialized)
    role_counts = Counter(record["record_role"] for record in materialized)
    ee_modelable_count = sum(record["outcome"]["ee_status"] in MODELABLE_EE_STATUSES for record in materialized)
    configuration_modelable_count = sum(
        record["outcome"].get("configuration_status") == "reported" for record in materialized
    )
    return {
        "record_count": len(materialized),
        "primary_scope_count": role_counts.get("primary_scope", 0),
        "auxiliary_screen_count": role_counts.get("auxiliary_screen", 0),
        "domain_counts": dict(sorted(domain_counts.items())),
        "ee_modelable_count": ee_modelable_count,
        "configuration_modelable_count": configuration_modelable_count,
    }


def build_report(
    contract: dict[str, Any],
    records: list[dict[str, Any]],
    contract_path: Path,
    schema_path: Path,
    records_path: Path,
    environment_report: dict[str, Any],
) -> dict[str, Any]:
    summary = summarize_records(records)
    return {
        "status": "valid",
        "contract_schema_version": contract["schema_version"],
        "contract_path": str(contract_path),
        "schema_path": str(schema_path),
        "records_path": str(records_path),
        "environment": environment_report,
        **summary,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument(
        "--skip-environment-check",
        action="store_true",
        help="skip the repository-local .venv precondition for schema-only diagnostics",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        environment_report = (
            {"status": "skipped"}
            if args.skip_environment_check
            else check_local_python_environment()
        )
        contract = load_json(args.contract)
        schema = load_json(args.schema)
        _require(schema.get("$id", "").endswith("/expansion/reaction-record.schema.json"), "unexpected expansion schema id")
        records = load_jsonl(args.records)
        validate_records(records, contract)
        print(
            json.dumps(
                build_report(
                    contract,
                    records,
                    args.contract,
                    args.schema,
                    args.records,
                    environment_report,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except ContractError as exc:
        print(f"expansion contract validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

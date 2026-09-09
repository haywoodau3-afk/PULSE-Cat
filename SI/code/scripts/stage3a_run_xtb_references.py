#!/usr/bin/env python3
"""Run Stage 3a xTB reference optimizations from the pilot worklist."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE3_DIR = ROOT / "data/jacs_2025/stage3"
DEFAULT_WORKLIST = STAGE3_DIR / "pilot/stage3a-lite-reference-optimization-worklist.jsonl"
DEFAULT_OUTPUT = STAGE3_DIR / "pilot/stage3a-lite-constrained-reference-optimization-results.jsonl"
DEFAULT_ENVIRONMENT = STAGE3_DIR / "stage3-environment.json"
DEFAULT_CONSTRAINT_MODE = "constrain_frozen_core"
DEFAULT_CORE_FORCE_CONSTANT = 1.0
ENERGY_PATTERNS = [
    re.compile(r"TOTAL ENERGY\s+(-?\d+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"total energy\s+(-?\d+(?:\.\d+)?)", re.IGNORECASE),
]


class XtbRunError(Exception):
    """Raised when the xTB runner input or output contract is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise XtbRunError(message)


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")


def load_xtb_path(environment_path: Path, override: Path | None) -> Path:
    if override is not None:
        return override
    environment = read_json(environment_path)
    return Path(environment["chemistry_environment"]["tools"]["xtb"]["path"])


def selected_work_items(
    worklist: list[dict[str, Any]],
    substrate_id: str | None,
    work_item_id: str | None,
    limit: int | None,
    completed_ids: set[str],
    force: bool,
) -> list[dict[str, Any]]:
    rows = []
    for row in worklist:
        if substrate_id and row["substrate_id"] != substrate_id:
            continue
        if work_item_id and row["work_item_id"] != work_item_id:
            continue
        if not force and row["work_item_id"] in completed_ids:
            continue
        rows.append(row)
    if limit is not None:
        require(limit >= 0, "--limit must be non-negative")
        rows = rows[:limit]
    return rows


def completed_work_item_ids(results: list[dict[str, Any]]) -> set[str]:
    return {
        row["work_item_id"]
        for row in results
        if row.get("optimization_status") == "success" and row.get("work_item_id")
    }


def parse_final_energy_hartree(text: str) -> float | None:
    for line in reversed(text.splitlines()):
        for pattern in ENERGY_PATTERNS:
            match = pattern.search(line)
            if match:
                return float(match.group(1))
    return None


def atom_list(indices: list[int]) -> str:
    return ",".join(str(index) for index in indices)


def write_xcontrol(path: Path, frozen_core_atom_count: int, mode: str, force_constant: float) -> Path | None:
    if mode == "none":
        return None
    require(mode in {"fix_frozen_core", "constrain_frozen_core"}, f"Unsupported constraint mode: {mode}")
    require(frozen_core_atom_count >= 2, "xTB atom-position fixing requires at least two atoms")
    if mode == "fix_frozen_core":
        text = "$fix\n" f"  atoms: {atom_list(list(range(1, frozen_core_atom_count + 1)))}\n" "$end\n"
    else:
        require(force_constant > 0, "Core constraint force constant must be positive")
        text = (
            "$constrain\n"
            f"  force constant={force_constant}\n"
            f"  atoms: {atom_list(list(range(1, frozen_core_atom_count + 1)))}\n"
            "$end\n"
        )
    path.write_text(text, encoding="utf-8")
    return path


def run_one(
    work_item: dict[str, Any],
    xtb_path: Path,
    timeout_seconds: int,
    omp_threads: int,
    constraint_mode: str,
    core_force_constant: float,
) -> dict[str, Any]:
    work_item_id = work_item["work_item_id"]
    work_dir = resolve_path(work_item["work_dir"])
    input_path = resolve_path(work_item["input_assembly_xyz_path"])
    require(input_path.exists(), f"{work_item_id}: input geometry is missing at {display_path(input_path)}")
    require(xtb_path.exists(), f"xTB executable is missing at {xtb_path}")
    require(xtb_path.is_file(), f"xTB path is not a file: {xtb_path}")

    work_dir.mkdir(parents=True, exist_ok=True)
    for stale_name in [
        "xtbopt.xyz",
        "xtblast.xyz",
        "xtbopt.log",
        "xtb.stdout.log",
        "xtb.stderr.log",
        "charges",
        "wbo",
        "xtbrestart",
        "xtbtopo.mol",
        ".xtboptok",
    ]:
        stale_path = work_dir / stale_name
        if stale_path.exists():
            stale_path.unlink()
    local_input = work_dir / "input-assembly.xyz"
    shutil.copy2(input_path, local_input)

    frozen_core_atom_count = int(work_item["provenance"]["frozen_core_atom_count"])
    xcontrol_path = write_xcontrol(work_dir / "xcontrol", frozen_core_atom_count, constraint_mode, core_force_constant)
    command = [str(xtb_path), str(local_input), "--gfn", "2", "--alpb", "ether", "--opt"]
    if xcontrol_path is not None:
        command.extend(["--input", str(xcontrol_path)])
    stdout_path = work_dir / "xtb.stdout.log"
    stderr_path = work_dir / "xtb.stderr.log"
    started_at = datetime.now(UTC).isoformat()
    try:
        result = subprocess.run(
            command,
            cwd=work_dir,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            env={**os.environ, "OMP_NUM_THREADS": str(omp_threads)},
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout_text = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode(errors="replace")
        stderr_text = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode(errors="replace")
        result = None
        timed_out = True
    else:
        stdout_text = result.stdout
        stderr_text = result.stderr
    finished_at = datetime.now(UTC).isoformat()

    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")
    optimized_xyz = work_dir / "xtbopt.xyz"
    final_energy = parse_final_energy_hartree(stdout_text + "\n" + stderr_text)

    if timed_out:
        status = "timeout"
        returncode = None
    else:
        returncode = result.returncode if result is not None else None
        status = "success" if returncode == 0 and optimized_xyz.exists() else "failed"

    return {
        "schema_version": "stage3a-xtb-reference-optimization-result-v1",
        "work_item_id": work_item_id,
        "substrate_id": work_item["substrate_id"],
        "reaction_id": work_item["reaction_id"],
        "stage1_pose_id": work_item["stage1_pose_id"],
        "optimization_status": status,
        "returncode": returncode,
        "timed_out": timed_out,
        "started_at": started_at,
        "finished_at": finished_at,
        "work_dir": display_path(work_dir),
        "input_assembly_xyz_path": display_path(input_path),
        "local_input_xyz_path": display_path(local_input),
        "optimized_complex_xyz_path": display_path(optimized_xyz) if optimized_xyz.exists() else None,
        "xtb_stdout_log_path": display_path(stdout_path),
        "xtb_stderr_log_path": display_path(stderr_path),
        "final_energy_hartree": final_energy,
        "method": "GFN2-xTB",
        "solvent_model": "ALPB ether",
        "constraint_mode": constraint_mode,
        "core_force_constant": core_force_constant if constraint_mode == "constrain_frozen_core" else None,
        "xcontrol_path": display_path(xcontrol_path) if xcontrol_path is not None else None,
        "command": command,
        "provenance": {
            "stage1_pose_generation_run_id": work_item["stage1_pose_generation_run_id"],
            "stage1_score_rank": work_item["stage1_score_rank"],
            "stage1_selection_bucket": work_item["stage1_selection_bucket"],
            "scaffold_constraint_policy_id": work_item["scaffold_constraint_policy_id"],
            "candidate_site_count": work_item["provenance"]["candidate_site_count"],
            "frozen_core_atom_count": frozen_core_atom_count,
        },
    }


def validate_results(results_path: Path, worklist_path: Path) -> dict[str, Any]:
    results = read_jsonl(results_path)
    worklist = read_jsonl(worklist_path)
    work_ids = {row["work_item_id"] for row in worklist}
    seen = set()
    status_counts: dict[str, int] = {}
    for row in results:
        require(row.get("schema_version") == "stage3a-xtb-reference-optimization-result-v1", "Invalid result row schema")
        work_item_id = row.get("work_item_id")
        require(work_item_id in work_ids, f"{work_item_id}: result is absent from worklist")
        require(work_item_id not in seen, f"{work_item_id}: duplicate result row")
        seen.add(work_item_id)
        status = row.get("optimization_status")
        require(status in {"success", "failed", "timeout"}, f"{work_item_id}: invalid optimization status")
        status_counts[status] = status_counts.get(status, 0) + 1
        require(resolve_path(row["xtb_stdout_log_path"]).exists(), f"{work_item_id}: stdout log is missing")
        require(resolve_path(row["xtb_stderr_log_path"]).exists(), f"{work_item_id}: stderr log is missing")
        if row.get("constraint_mode") == "fix_frozen_core":
            require(row.get("xcontrol_path"), f"{work_item_id}: constrained row needs xcontrol path")
            require(resolve_path(row["xcontrol_path"]).exists(), f"{work_item_id}: xcontrol file is missing")
        if row.get("constraint_mode") == "constrain_frozen_core":
            require(row.get("xcontrol_path"), f"{work_item_id}: constrained row needs xcontrol path")
            require(resolve_path(row["xcontrol_path"]).exists(), f"{work_item_id}: xcontrol file is missing")
            require(row.get("core_force_constant", 0) > 0, f"{work_item_id}: constrained row needs force constant")
        if status == "success":
            require(row.get("optimized_complex_xyz_path"), f"{work_item_id}: success row needs optimized XYZ path")
            require(resolve_path(row["optimized_complex_xyz_path"]).exists(), f"{work_item_id}: optimized XYZ is missing")
            require(row.get("final_energy_hartree") is not None, f"{work_item_id}: success row needs parsed final energy")
    return {
        "results_path": display_path(results_path),
        "worklist_path": display_path(worklist_path),
        "result_count": len(results),
        "worklist_count": len(worklist),
        "status_counts": status_counts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worklist", type=Path, default=DEFAULT_WORKLIST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--environment", type=Path, default=DEFAULT_ENVIRONMENT)
    parser.add_argument("--xtb", type=Path, default=None, help="Override xTB executable path.")
    parser.add_argument("--substrate-id", default=None)
    parser.add_argument("--work-item-id", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--omp-threads", type=int, default=4)
    parser.add_argument("--constraint-mode", default=DEFAULT_CONSTRAINT_MODE, choices=["constrain_frozen_core", "fix_frozen_core", "none"])
    parser.add_argument("--core-force-constant", type=float, default=DEFAULT_CORE_FORCE_CONSTANT)
    parser.add_argument("--force", action="store_true", help="Rerun work items even if successful result rows already exist.")
    parser.add_argument("--run", action="store_true", help="Execute selected xTB work items. Without this, only validate existing results.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.run:
            worklist = read_jsonl(args.worklist)
            existing_results = read_jsonl(args.output)
            xtb_path = load_xtb_path(args.environment, args.xtb)
            selected = selected_work_items(
                worklist,
                args.substrate_id,
                args.work_item_id,
                args.limit,
                completed_work_item_ids(existing_results),
                args.force,
            )
            rows = [
                run_one(row, xtb_path, args.timeout_seconds, args.omp_threads, args.constraint_mode, args.core_force_constant)
                for row in selected
            ]
            if args.force:
                rerun_ids = {row["work_item_id"] for row in rows}
                existing_results = [row for row in existing_results if row["work_item_id"] not in rerun_ids]
                write_jsonl(args.output, existing_results + rows)
            else:
                append_jsonl(args.output, rows)
            print(f"Ran {len(rows)} Stage 3a xTB reference optimizations")
        report = validate_results(args.output, args.worklist)
    except XtbRunError as exc:
        print(f"Stage 3a xTB reference runner failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

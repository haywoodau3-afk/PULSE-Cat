#!/usr/bin/env python3
"""Check or create the repository-local Python virtual environment."""

from __future__ import annotations

import argparse
import json
import sys
import venv
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_DIR = ".venv"


class EnvironmentContractError(ValueError):
    """Raised when the repository-local Python environment is unavailable."""


def _environment_dir(repo_root: Path, environment_dir: str | Path | None = None) -> Path:
    root = repo_root.resolve()
    candidate = Path(environment_dir) if environment_dir is not None else Path(DEFAULT_ENV_DIR)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise EnvironmentContractError("environment directory must be inside the repository root") from exc
    return candidate


def check_local_environment(repo_root: Path = ROOT, environment_dir: str | Path | None = None) -> dict[str, Any]:
    """Return a report when a valid repository-local venv exists."""

    root = repo_root.resolve()
    env_dir = _environment_dir(root, environment_dir)
    python_path = env_dir / "bin" / "python"
    config_path = env_dir / "pyvenv.cfg"
    missing = [str(path) for path in (env_dir, python_path, config_path) if not path.exists()]
    if missing:
        raise EnvironmentContractError(
            "local virtual environment is missing; expected "
            f"{env_dir}. Create it with: {sys.executable} scripts/environment_contract.py --create"
        )
    if not python_path.is_file() or not python_path.stat().st_mode & 0o111:
        raise EnvironmentContractError(f"local virtual environment Python is not executable: {python_path}")
    return {
        "status": "present",
        "repository_root": str(root),
        "environment_dir": str(env_dir),
        "python_executable": str(python_path),
        "pyvenv_config": str(config_path),
        "running_python": str(Path(sys.executable).resolve()),
        "running_python_is_local": Path(sys.executable).resolve() == python_path.resolve(),
    }


def create_local_environment(repo_root: Path = ROOT, environment_dir: str | Path | None = None) -> dict[str, Any]:
    """Create a missing local venv, refusing to overwrite an existing path."""

    root = repo_root.resolve()
    env_dir = _environment_dir(root, environment_dir)
    if env_dir.exists():
        return check_local_environment(root, env_dir)
    env_dir.parent.mkdir(parents=True, exist_ok=True)
    builder = venv.EnvBuilder(with_pip=True, clear=False, symlinks=False)
    builder.create(env_dir)
    return check_local_environment(root, env_dir)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--environment-dir", type=Path, default=Path(DEFAULT_ENV_DIR))
    parser.add_argument("--create", action="store_true", help="create the venv only when the path is absent")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = create_local_environment(args.repo_root, args.environment_dir) if args.create else check_local_environment(args.repo_root, args.environment_dir)
    except EnvironmentContractError as exc:
        if args.json:
            print(json.dumps({"status": "invalid", "error": str(exc)}))
        else:
            print(f"environment contract validation failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"local virtual environment present: {report['environment_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

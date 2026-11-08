#!/usr/bin/env python3
"""Run the cmcpor-only Stage 1 namespace."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from catalyst_rerun.stage1_runner import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(
        main(
            ROOT / "data/expansion/catalyst_rerun/cmcpor/run-config.json",
            "cmcpor-fecl",
        )
    )

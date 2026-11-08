"""Fail-closed readiness check for the constrained non-LLM generator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "data/expansion/pptl/generator-freeze-config.json"


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    torch_present = importlib.util.find_spec("torch") is not None
    checkpoint_ready = config["primary_generator"]["checkpoint_sha256"] not in {
        "",
        "PENDING_CHECKPOINT_ACQUISITION",
    }
    report = {
        "config": str(CONFIG.relative_to(ROOT)),
        "torch_present": torch_present,
        "checkpoint_hash_recorded": checkpoint_ready,
        "status": "ready_for_generation" if torch_present and checkpoint_ready else "blocked",
        "blocking_reasons": [
            reason
            for reason, missing in (
                ("torch_not_installed", not torch_present),
                ("checkpoint_hash_pending", not checkpoint_ready),
            )
            if missing
        ],
    }
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "ready_for_generation" else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Score and rank one PPTL candidate pool with auditable components."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from acquisition import score_candidates
from core import read_jsonl


def _normalise(row: dict) -> dict:
    substrate = row.get("substrate") if isinstance(row.get("substrate"), dict) else {}
    return {
        "substrate_id": row.get("substrate_id") or row.get("compound_id") or substrate.get("paper_substrate_id"),
        "family_id": row.get("family_id") or (row.get("family") or {}).get("family_id", "unknown-family"),
        "smiles": row.get("smiles") or substrate.get("smiles") or substrate.get("azide_smiles"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, help="JSON object mapping expert names to prediction arrays")
    parser.add_argument("--source-predictions", type=Path, help="JSON object mapping source names to prediction arrays")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidates = [_normalise(row) for row in read_jsonl(args.candidates)]
    selected = [_normalise(row) for row in read_jsonl(args.selected)]
    predictions = json.loads(args.predictions.read_text(encoding="utf-8")) if args.predictions else None
    source_predictions = json.loads(args.source_predictions.read_text(encoding="utf-8")) if args.source_predictions else None
    if any(not row["smiles"] for row in candidates + selected):
        raise ValueError("candidate and selected rows require SMILES")
    ranking = score_candidates(candidates, selected=selected, predictions=predictions, source_predictions=source_predictions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(ranking, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(candidates), "selected_count": len(selected), "top": ranking[0] if ranking else None}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

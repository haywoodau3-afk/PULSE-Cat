#!/usr/bin/env python3
"""Freeze the exact P7/CMC-Por files used by the publication analysis."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from core import canonical_overlap, load_reaction_rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _summary(rows) -> dict[str, object]:
    return {
        "row_count": len(rows),
        "ee_label_count": sum(row.value("ee_percent") is not None for row in rows),
        "yield_label_count": sum(row.value("isolated_yield_percent") is not None for row in rows),
        "pathway_counts": dict(sorted(Counter(row.pathway_id for row in rows).items())),
        "family_counts": dict(sorted(Counter(row.family_id for row in rows).items())),
        "split_group_count": len({row.split_group for row in rows}),
    }


def freeze_ledger(p7_records: Path, cmcpor_records: Path, *, p7_stage2p: Path | None = None, cmcpor_stage2p: Path | None = None, contract: Path | None = None) -> dict:
    p7 = load_reaction_rows(p7_records, catalyst="fe-p7-cl", include_unlabelled=True)
    cmc = load_reaction_rows(cmcpor_records, catalyst="cmcpor-fecl", include_unlabelled=True)
    cmc_aryl = [row for row in cmc if row.family_id == "angew-aryl-c-h-amination"]
    overlap = canonical_overlap(p7, cmc_aryl)
    files = {"p7_records": p7_records, "cmcpor_records": cmcpor_records}
    if p7_stage2p is not None:
        files["p7_stage2p"] = p7_stage2p
    if cmcpor_stage2p is not None:
        files["cmcpor_stage2p"] = cmcpor_stage2p
    if contract is not None:
        files["pptl_contract"] = contract
    manifest = {
        "schema_version": "pptl-publication-ledger-lock-v1",
        "status": "locked",
        "locked_at_utc": datetime.now(timezone.utc).isoformat(),
        "study_id": "parallel-progressive-transfer-bidirectional-v1",
        "primary_pathway": "angew-aryl-c-h-amination",
        "domains": {
            "p7": {"catalyst_id": "fe-p7-cl", **_summary(p7)},
            "cmcpor": {"catalyst_id": "cmcpor-fecl", **_summary(cmc)},
            "cmcpor_aryl": {"catalyst_id": "cmcpor-fecl", **_summary(cmc_aryl)},
        },
        "canonical_overlap": {
            "count": len(overlap),
            "pairs": overlap,
            "atom_maps_removed_before_matching": True,
            "excluded_from_cold_start_source": True,
            "paired_diagnostic_only": True,
        },
        "files": {
            key: {"path": str(path), "sha256": _sha256(path), "bytes": path.stat().st_size}
            for key, path in files.items()
        },
        "policies": {
            "ee_primary": True,
            "yield_secondary": True,
            "whole_substrate_unit": True,
            "cmcpor_sulfonyl_separate_control": True,
            "d4_required_for_primary_study": False,
        },
    }
    # The digest identifies the inputs and policy, not the time at which the
    # manifest was regenerated. This makes the lock reproducible.
    digest_payload = dict(manifest)
    digest_payload.pop("locked_at_utc", None)
    lock_digest = hashlib.sha256(json.dumps(digest_payload, sort_keys=True).encode("utf-8")).hexdigest()
    manifest["lock_digest"] = lock_digest
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p7-records", type=Path, required=True)
    parser.add_argument("--cmcpor-records", type=Path, required=True)
    parser.add_argument("--p7-stage2p", type=Path)
    parser.add_argument("--cmcpor-stage2p", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = freeze_ledger(args.p7_records, args.cmcpor_records, p7_stage2p=args.p7_stage2p, cmcpor_stage2p=args.cmcpor_stage2p, contract=args.contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "lock_digest": report["lock_digest"], "overlap_count": report["canonical_overlap"]["count"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

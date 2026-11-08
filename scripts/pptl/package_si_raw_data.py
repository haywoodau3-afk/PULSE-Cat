#!/usr/bin/env python3
"""Build the manuscript SI raw-data deposit without copying XYZ caches.

The package preserves every source file's repository-relative path below a
numbered scientific category.  A SHA-256 manifest makes the deposit auditable
without requiring the working repository.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "supporting-information" / "raw-data"

SOURCE_GROUPS = [
    (
        "01_curated_records_and_source_provenance",
        [
            ROOT / "data/jacs_2025/README.md",
            ROOT / "data/jacs_2025/constraints",
            ROOT / "data/jacs_2025/manual-substrates.csv",
            ROOT / "data/jacs_2025/optimization-conditions.csv",
            ROOT / "data/jacs_2025/reference-geometry",
            ROOT / "data/jacs_2025/scope-outcomes.csv",
            ROOT / "data/jacs_2025/source-ledger.csv",
            ROOT / "data/jacs_2025/schema",
            ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl",
            ROOT / "data/jacs_2025/stage2/feature-ready-seed-set.json",
            ROOT / "data/jacs_2025/stage2/seed-curation-packets.json",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/README.md",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/constraints",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/derived-nitrene-sites.csv",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/outcomes.jsonl",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/remap-run-report.json",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/remap-validation.csv",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/remap-validation.json",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/reference-geometry",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/run-config.json",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/source-structures.jsonl",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/stage0",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/substrates.jsonl",
        ],
    ),
    (
        "02_independent_progressive_learning",
        [
            ROOT / "data/jacs_2025/scope_progression",
            ROOT / "data/jacs_2025/rule_diversity_scope_progression",
            ROOT / "data/expansion/catalyst_rerun/cmcpor_aryl_scope_progression",
            ROOT / "data/expansion/catalyst_rerun/cmcpor_uff_full/scope_progression",
            ROOT / "data/expansion/catalyst_rerun/cmcpor_uff_full/rule_diversity_scope_progression",
        ],
    ),
    (
        "03_structure_pose_features_and_model_benchmarks",
        [
            ROOT / "data/jacs_2025/stage2/features",
            ROOT / "data/jacs_2025/stage2/modeling",
            ROOT / "data/jacs_2025/stage2/reports",
            ROOT / "data/jacs_2025/stage2/folding-views",
            ROOT / "data/jacs_2025/stage1",
            ROOT / "data/jacs_2025/stage3",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/stage1",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/stage2",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/stage2p",
            ROOT / "data/expansion/catalyst_rerun/cmcpor_uff_full/stage2",
            ROOT / "data/expansion/catalyst_rerun/cmcpor_uff_full/stage2p",
            ROOT / "data/expansion/catalyst_rerun/cmcpor_uff_full/stage0",
            ROOT / "data/expansion/catalyst_rerun/cmcpor_uff_full/stage1",
        ],
    ),
    (
        "04_pose_density_arrays_and_overlays",
        [
            ROOT / "data/jacs_2025/stage2pp",
            ROOT / "data/expansion/catalyst_rerun/cmcpor/stage2pp",
            ROOT / "data/expansion/catalyst_rerun/cmcpor_uff_full/stage2pp",
        ],
    ),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scientific_level(path: Path) -> str:
    name = path.name.lower()
    if path.suffix.lower() in {".smi", ".jsonl"} and any(
        token in name for token in ("raw", "record", "outcome", "substrate", "structure")
    ):
        return "raw_or_record_level"
    if path.suffix.lower() == ".npz":
        return "numerical_pose_array"
    if any(token in name for token in ("feature", "matrix", "prediction", "curve", "metric")):
        return "analysis_ready_or_model_output"
    if path.suffix.lower() in {".svg", ".md"}:
        return "human_readable_or_visualization"
    if path.suffix.lower() == ".ckpt":
        return "model_checkpoint"
    return "supporting_metadata_or_analysis_output"


def pptl_category(path: Path) -> str:
    relative = path.relative_to(ROOT / "data/expansion/pptl")
    name = str(relative).lower()
    generation_tokens = (
        "raw-", "raw_", "funnel", "generator", "generation", "enumeration",
        "smiles-rnn", "promptsmiles", "grammar", "checkpoints/", "five-seed",
    )
    proposal_tokens = (
        "panel", "shortlist", "availability", "pubchem", "morphology",
        "synthetic-reliability", "safety", "ledger", "lock", "resource",
    )
    if any(token in name for token in generation_tokens):
        return "06_generative_substrate_search"
    if any(token in name for token in proposal_tokens):
        return "07_proposed_scope_and_frozen_ledgers"
    return "05_transfer_learning_and_progressive_routes"


def iter_files(source: Path):
    if source.is_file():
        yield source
    elif source.is_dir():
        yield from sorted(path for path in source.rglob("*") if path.is_file())
    else:
        raise FileNotFoundError(source)


def allowed(path: Path) -> bool:
    return path.suffix.lower() != ".xyz" and path.name not in {".DS_Store", ".gitkeep"}


def package_file(source: Path, category: str, rows: list[dict[str, object]]) -> None:
    relative = source.relative_to(ROOT)
    destination = OUT / category / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    rows.append(
        {
            "category": category,
            "package_path": destination.relative_to(OUT).as_posix(),
            "source_path": relative.as_posix(),
            "format": source.suffix.lower().lstrip(".") or "none",
            "scientific_level": scientific_level(source),
            "bytes": source.stat().st_size,
            "sha256": sha256(source),
        }
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    excluded_xyz: list[dict[str, object]] = []
    seen: set[Path] = set()

    for category, sources in SOURCE_GROUPS:
        for source_root in sources:
            for source in iter_files(source_root):
                resolved = source.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                if not allowed(source):
                    if source.suffix.lower() == ".xyz":
                        excluded_xyz.append(
                            {
                                "source_path": source.relative_to(ROOT).as_posix(),
                                "bytes": source.stat().st_size,
                                "reason": "deferred_by_user_for_current_SI_package",
                            }
                        )
                    continue
                package_file(source, category, rows)

    pptl_root = ROOT / "data/expansion/pptl"
    for source in iter_files(pptl_root):
        resolved = source.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if not allowed(source):
            if source.suffix.lower() == ".xyz":
                excluded_xyz.append(
                    {
                        "source_path": source.relative_to(ROOT).as_posix(),
                        "bytes": source.stat().st_size,
                        "reason": "deferred_by_user_for_current_SI_package",
                    }
                )
            continue
        package_file(source, pptl_category(source), rows)

    rows.sort(key=lambda row: (str(row["category"]), str(row["package_path"])))
    manifest_csv = OUT / "raw-data-manifest.csv"
    with manifest_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_category: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "bytes": 0})
    for row in rows:
        summary = by_category[str(row["category"])]
        summary["files"] += 1
        summary["bytes"] += int(row["bytes"])

    manifest = {
        "schema_version": "si-raw-data-deposit-v1",
        "package_root": "output/supporting-information/raw-data",
        "policy": {
            "xyz_included": False,
            "xyz_note": "XYZ coordinate files are the only intentionally excluded scientific data layer, following the user's earlier instruction.",
            "hidden_and_placeholder_files_included": False,
        },
        "summary": {
            "files": len(rows),
            "bytes": sum(int(row["bytes"]) for row in rows),
            "categories": dict(sorted(by_category.items())),
            "excluded_xyz_files": len(excluded_xyz),
            "excluded_xyz_bytes": sum(int(row["bytes"]) for row in excluded_xyz),
        },
        "excluded_xyz": excluded_xyz,
        "files": rows,
    }
    (OUT / "raw-data-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(manifest["summary"], indent=2))


if __name__ == "__main__":
    main()

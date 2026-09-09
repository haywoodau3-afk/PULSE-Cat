#!/usr/bin/env python3
"""Write a SHA-256 manifest for the SI2 package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


SI2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SI2_ROOT.parent
OUTPUT = SI2_ROOT / "manifest.json"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def source_for(relative: Path) -> str | None:
    text = relative.as_posix()
    direct = {
        "SI2/source/rdkit/build_feature_table.py": None,
        "SI2/source/rdkit/build_tier1_features.py": "scripts/stage2_features.py",
        "SI2/source/rdkit/build_rdkit_morgan_progression.py": "scripts/scope_progression.py",
    }
    if text in direct:
        return direct[text]
    if text.startswith("SI2/source/"):
        candidates = [text.removeprefix("SI2/source/")]
        if "/" in candidates[0]:
            candidates.append(candidates[0].split("/", 1)[1])
        for candidate in candidates:
            if (REPO_ROOT / "scripts" / candidate).exists():
                return (Path("scripts") / candidate).as_posix()
            if (REPO_ROOT / "docs/research/2026-09-07" / candidate).exists():
                return (Path("docs/research/2026-09-07") / candidate).as_posix()
    if text.startswith("SI2/procedure/"):
        name = Path(text).name
        for candidate in [Path("docs/research/2026-09-07") / name, Path("docs") / name, Path("output/supporting-information") / name]:
            if (REPO_ROOT / candidate).exists():
                return candidate.as_posix()
    if text.startswith("SI2/data/inputs/"):
        name = Path(text).name
        candidates = list((REPO_ROOT / "data/jacs_2025").rglob(name)) + list((REPO_ROOT / "data/expansion/catalyst_rerun/cmcpor").rglob(name))
        if candidates:
            return candidates[0].relative_to(REPO_ROOT).as_posix()
    mappings = [
        ("SI2/data/pose/p7/stage1-reports/", "data/jacs_2025/stage1/panel/"),
        ("SI2/data/pose/p7/geometries/", "data/jacs_2025/stage1/geometries/"),
        ("SI2/data/pose/p7/stage2/", "data/jacs_2025/stage2/"),
        ("SI2/data/pose/p7/stage2pp/", "data/jacs_2025/stage2pp/"),
        ("SI2/data/pose/cmcpor/stage1-reports/", "data/expansion/catalyst_rerun/cmcpor/stage1/reports/"),
        ("SI2/data/pose/cmcpor/geometries/", "data/expansion/catalyst_rerun/cmcpor/stage1/geometry/"),
        ("SI2/data/pose/cmcpor/stage2/", "data/expansion/catalyst_rerun/cmcpor/stage2/"),
        ("SI2/data/pose/cmcpor/stage2/", "data/expansion/catalyst_rerun/cmcpor/stage2p/"),
        ("SI2/data/pose/cmcpor/stage2pp/", "data/expansion/catalyst_rerun/cmcpor/stage2pp/"),
        ("SI2/data/xtb/bde-and-calibration/", "data/jacs_2025/stage3/calibration/"),
        ("SI2/data/xtb/stage3-features/", "data/jacs_2025/stage3/"),
        ("SI2/data/xtb/reference-optimizations/", "data/jacs_2025/stage3/pilot/reference-optimizations/"),
        ("SI2/data/crest/ensembles/", "docs/research/2026-09-07/crest-10-conformers/"),
        ("SI2/data/crest/benchmarks/p7-crest-xtb-model/", "docs/research/2026-09-07/p7-crest-xtb-model/"),
        ("SI2/data/crest/benchmarks/five-pose-results/", "docs/research/2026-09-07/results/"),
    ]
    for prefix, origin in mappings:
        if text.startswith(prefix):
            candidate = REPO_ROOT / origin / text.removeprefix(prefix)
            if candidate.exists():
                return candidate.relative_to(REPO_ROOT).as_posix()
    return None


def main() -> None:
    files = []
    for path in sorted(SI2_ROOT.rglob("*")):
        if not path.is_file() or path == OUTPUT:
            continue
        relative = path.relative_to(REPO_ROOT)
        files.append(
            {
                "path": relative.as_posix(),
                "source_path": source_for(relative),
                "size_bytes": path.stat().st_size,
                "sha256": digest(path),
            }
        )
    payload = {
        "schema_version": "si2-file-manifest-v1",
        "package": "SI2",
        "file_count": len(files),
        "notes": [
            "All listed files are physically present under SI2.",
            "source_path identifies the original repository artifact when it can be mapped unambiguously; null denotes a SI2-specific document or generated table.",
            "Partial CREST jobs are retained for audit but are not counted as completed ensembles.",
        ],
        "files": files,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(files)} file records to {OUTPUT}")


if __name__ == "__main__":
    main()

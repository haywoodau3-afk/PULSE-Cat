from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = HERE / "corrected_project"

SOURCE_SCRIPTS = [
    "scripts/stage1_contract.py",
    "scripts/stage1_v2_pose_selection.py",
    "scripts/stage2_contract.py",
    "scripts/stage2_features.py",
    "scripts/stage2_folding_feature_experiment.py",
    "scripts/stage2_full_scope_benchmark.py",
    "scripts/stage2_pose_interaction.py",
    "scripts/stage2_pose_summary.py",
    "scripts/stage2p_family_heldout.py",
    "scripts/stage2p_publication_benchmark.py",
    "scripts/stage2p_representation.py",
    "scripts/stage2pp_representation.py",
    "scripts/stage3a_alt_full_scope_predict.py",
    "scripts/stage3a_alt_full_workflow_unseen.py",
    "scripts/stage3a_alt_plus_stage2p_family_heldout.py",
    "scripts/stage3a_local_shell_features.py",
    "scripts/stage3a_pilot.py",
    "scripts/stage3a_reference_features.py",
    "scripts/stage3a_seed_model_comparison.py",
    "docs/research/2026-09-07/pose_probability.py",
]

INPUT_FILES = [
    "revision/reviewer2_comment1/results/p7_source_corrected_copy.jsonl",
    "revision/reviewer1_comment5/results/cmcpor_source_corrected_copy.jsonl",
    "revision/reviewer2_comment2/results/corrected_p7_stage2p.jsonl",
    "revision/reviewer2_comment2/results/corrected_cmcpor_stage2p.jsonl",
    "revision/reviewer2_comment2/results/corrected_p7_pose_interaction.jsonl",
    "data/jacs_2025/stage2/curated-reaction-records.jsonl",
    "data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl",
    "SI2/data/crest/benchmarks/p7-crest-xtb-model/features.json",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def entry(path: Path, relative_to: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(relative_to)),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def snapshot_source_scripts() -> list[dict[str, object]]:
    destination = PROJECT / "source_scripts"
    if destination.exists():
        shutil.rmtree(destination)
    copied = []
    for relative in SOURCE_SCRIPTS:
        source = ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append({"repository_path": relative, **entry(target, PROJECT)})
    readme = destination / "README.md"
    readme.write_text(
        "# Source script snapshots\n\n"
        "These byte-preserved repository scripts cover the atom-mapping contract, pose interaction and summaries, Stage 2/2p/2pp features, selection, family validation, Stage 3a, and CREST/xTB workflows. Original repository-relative paths and SHA-256 hashes are listed in the package manifest. Correction-specific analysis wrappers are retained alongside their outputs.\n",
        encoding="utf-8",
    )
    copied.append({"repository_path": "README.md", **entry(readme, PROJECT)})
    return copied


def snapshot_input_files() -> list[dict[str, object]]:
    destination = PROJECT / "input_snapshots"
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for relative in INPUT_FILES:
        source = ROOT / relative
        if not source.is_file():
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        records.append({"workspace_path": relative, **entry(target, PROJECT)})
    return records


def main() -> None:
    cache = PROJECT / "__pycache__"
    if cache.exists():
        shutil.rmtree(cache)

    source_scripts = snapshot_source_scripts()
    input_snapshots = snapshot_input_files()

    package_files = []
    for path in sorted(HERE.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.name in {"MANIFEST.json", "FULL_PACKAGE_MANIFEST.json"}:
            continue
        package_files.append(entry(path, HERE))

    external_inputs = []
    for relative in INPUT_FILES:
        path = ROOT / relative
        if path.is_file():
            external_inputs.append(entry(path, ROOT))
    for directory in [
        ROOT / "data/jacs_2025/stage1/panel",
        ROOT / "data/expansion/catalyst_rerun/cmcpor_uff_full/stage1/reports",
    ]:
        if directory.is_dir():
            for path in sorted(directory.glob("stage-1-smoke-*.json")):
                external_inputs.append(entry(path, ROOT))

    manifest = {
        "title": "Corrected PULSE-Cat revision archive",
        "manifest_version": 2,
        "status": "corrected outputs and revised documents reconciled; author review and public deposit remain separate steps",
        "created": date.today().isoformat(),
        "runtime": {"python": sys.version, "platform": platform.platform()},
        "source_scripts": source_scripts,
        "input_snapshots": input_snapshots,
        "external_source_inputs": external_inputs,
        "package_files": package_files,
        "notes": [
            "Experimental ee/yield labels and the source pose coordinates were not altered by the atom-mapping correction.",
            "Pose-centred Stage 2 interaction, Stage 2p/2pp, downstream prediction and acquisition analyses were regenerated or explicitly withdrawn where source dependencies could not be reconstructed.",
            "The non-reproducible historical V4/V6 hierarchical weight search was removed from the revised SI and preserved under corrected_project/withdrawn_historical/; it is not evidence in the revised manuscript.",
            "The corrected dedicated mean-prefix replay uses three random continuations; the separate independent AUC-MAE progression uses 500 continuations per endpoint.",
            "All retained tables, figures, captions, and SI cross-references are reconciled to the corrected outputs; historical values are identified as superseded where discussed.",
            "The archived original output tree remains historical and is not a substitute for the corrected release files included in this archive.",
            "The corrected release includes all 140 Stage 1 reports and 28,000 assembly XYZ inputs used for corrected pose-feature regeneration, with a per-file SHA-256 manifest.",
            "Frozen SI, SI2, SI3, and SI4 source snapshots retain pre-correction code for historical provenance; SOURCE_TREE_AUDIT.md identifies the corrected source of record.",
        ],
    }
    (HERE / "FULL_PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (PROJECT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest built: {len(package_files)} package files, {len(source_scripts)} source scripts, {len(input_snapshots)} input snapshots")


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import hashlib
import json
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = HERE / "corrected_project"
OUTPUT_DIR = PROJECT / "input_snapshots" / "pose_coordinates"
BUNDLE = OUTPUT_DIR / "pose_coordinate_inputs.tar.gz"
MANIFEST = OUTPUT_DIR / "pose_coordinate_inputs_manifest.csv"


def read_feature_ids(path: Path) -> list[str]:
    return [json.loads(line)["substrate_id"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def substrate_id(report: dict) -> str | None:
    ids = report.get("pose_generation_run", {}).get("substrate_ids", [])
    if len(ids) == 1:
        return ids[0]
    return report.get("substrate_record", {}).get("substrate_id")


def collect_inputs() -> list[tuple[str, str, Path]]:
    selected: list[tuple[str, str, Path]] = []

    p7_ids = set(read_feature_ids(PROJECT / "features" / "p7" / "stage2p.jsonl"))
    p7_reports = ROOT / "data" / "jacs_2025" / "stage1" / "panel"
    for sid in sorted(p7_ids):
        report_path = p7_reports / f"stage-1-smoke-{sid}.json"
        if not report_path.is_file():
            raise FileNotFoundError(report_path)
        selected.append(("stage1_report", sid, report_path))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        poses = report.get("pose_records", [])
        if len(poses) != 200:
            raise ValueError(f"P7 {sid}: expected 200 retained poses, found {len(poses)}")
        for pose in poses:
            value = pose.get("fe_bound_assembly_xyz_path")
            if not value:
                raise ValueError(f"P7 {sid}: retained pose lacks assembly XYZ path")
            coordinate_path = ROOT / value
            if not coordinate_path.is_file():
                raise FileNotFoundError(coordinate_path)
            selected.append(("assembly_xyz", sid, coordinate_path))

    cmc_ids = set(read_feature_ids(PROJECT / "features" / "cmc" / "stage2p.jsonl"))
    cmc_reports = ROOT / "data" / "expansion" / "catalyst_rerun" / "cmcpor_uff_full" / "stage1" / "reports"
    matched_reports: dict[str, list[Path]] = {sid: [] for sid in cmc_ids}
    for report_path in sorted(cmc_reports.glob("stage-1-smoke-*.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        sid = substrate_id(report)
        if sid in matched_reports:
            matched_reports[sid].append(report_path)
    for sid in sorted(cmc_ids):
        reports = matched_reports[sid]
        if len(reports) != 2:
            raise ValueError(f"CMC {sid}: expected the two recorded report variants, found {len(reports)}")
        for report_path in reports:
            selected.append(("stage1_report", sid, report_path))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            poses = report.get("pose_records", [])
            if len(poses) != 200:
                raise ValueError(f"CMC {sid} ({report_path.name}): expected 200 retained poses, found {len(poses)}")
            for pose in poses:
                value = pose.get("fe_bound_assembly_xyz_path")
                if not value:
                    raise ValueError(f"CMC {sid}: retained pose lacks assembly XYZ path")
                coordinate_path = ROOT / value
                if not coordinate_path.is_file():
                    raise FileNotFoundError(coordinate_path)
                selected.append(("assembly_xyz", sid, coordinate_path))

    return selected


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = collect_inputs()
    unique_paths = {path for _, _, path in rows}
    if len(unique_paths) != len(rows):
        raise ValueError("Duplicate source paths were collected; refusing to make an ambiguous bundle")

    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["kind", "substrate_id", "source_path", "archive_path", "size_bytes", "sha256"],
        )
        writer.writeheader()
        for kind, sid, path in rows:
            relative = path.relative_to(ROOT)
            writer.writerow(
                {
                    "kind": kind,
                    "substrate_id": sid,
                    "source_path": str(relative),
                    "archive_path": str(relative),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )

    with tarfile.open(BUNDLE, "w:gz", compresslevel=6) as archive:
        for _, _, path in rows:
            archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)

    report_count = sum(kind == "stage1_report" for kind, _, _ in rows)
    coordinate_count = sum(kind == "assembly_xyz" for kind, _, _ in rows)
    print(f"Bundled {report_count} Stage 1 reports and {coordinate_count} assembly XYZ files")
    print(f"Bundle: {BUNDLE} ({BUNDLE.stat().st_size:,} bytes)")
    print(f"Input manifest: {MANIFEST}")


if __name__ == "__main__":
    main()

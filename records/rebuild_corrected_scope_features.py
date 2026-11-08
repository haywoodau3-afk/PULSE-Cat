"""Complete corrected Stage 2p feature coverage for all Fe(P7)Cl records.

The Stage 2p feature generator historically emitted only records with a
numerical ee label.  That omitted geometry for two Fe(P7)Cl records that have
other usable outcomes (one ND ee, one achiral product with a reported yield).
This correction runner derives their features without inventing an ee label.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts import stage2p_representation as stage2p  # noqa: E402
from scripts.scope_progression import catalyst_id  # noqa: E402


HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "revision/reviewer2_comment1/results/p7_source_corrected_copy.jsonl"
REPORTS = ROOT / "data/jacs_2025/stage1/panel"
FEATURES = HERE / "corrected_project/features/p7/stage2p.jsonl"
REPORT = HERE / "corrected_project/features/p7/stage2p_coverage_report.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    records = [
        row
        for row in read_jsonl(SOURCE)
        if catalyst_id(row) == "fe-p7-cl"
        and row.get("reaction_center", {}).get("review_status") == "checked"
    ]
    if len(records) != 40:
        raise ValueError(f"Expected 40 source-checked Fe(P7)Cl records; found {len(records)}")

    existing = read_jsonl(FEATURES)
    by_id = {row["substrate_id"]: row for row in existing}
    if len(by_id) != len(existing):
        raise ValueError("Duplicate substrate IDs in corrected Stage 2p file")

    generated: list[str] = []
    with tempfile.TemporaryDirectory(prefix="corrected-stage2p-") as temp:
        tempdir = Path(temp)
        for record in records:
            substrate_id = record["substrate_id"]
            if substrate_id in by_id:
                continue
            report_path = REPORTS / f"stage-1-smoke-{substrate_id}.json"
            if not report_path.is_file():
                raise FileNotFoundError(f"Missing saved Stage 1 geometry: {report_path}")
            pose_report = json.loads(report_path.read_text(encoding="utf-8"))
            by_id[substrate_id] = stage2p.generate_substrate_feature_row(record, pose_report, tempdir)
            generated.append(substrate_id)

    expected_ids = sorted(row["substrate_id"] for row in records)
    if sorted(by_id) != expected_ids:
        missing = sorted(set(expected_ids) - set(by_id))
        extra = sorted(set(by_id) - set(expected_ids))
        raise ValueError(f"Corrected Stage 2p ID mismatch; missing={missing}, extra={extra}")

    ordered = [by_id[substrate_id] for substrate_id in expected_ids]
    stage2p.write_jsonl(FEATURES, ordered)
    REPORT.write_text(
        json.dumps(
            {
                "status": "corrected feature coverage complete",
                "source_records": str(SOURCE.relative_to(ROOT)),
                "geometry_source": str(REPORTS.relative_to(ROOT)),
                "feature_file": str(FEATURES.relative_to(HERE)),
                "fe_p7_source_checked_records": len(records),
                "corrected_feature_records": len(ordered),
                "newly_generated_records": generated,
                "records_with_ee_target": sum(row.get("target_value") is not None for row in ordered),
                "records_with_yield_but_no_ee": [
                    row["substrate_id"]
                    for row in records
                    if row.get("outcome", {}).get("isolated_yield_percent") is not None
                    and row.get("outcome", {}).get("ee_percent") is None
                ],
                "target_values_added_or_changed": False,
                "pose_count_required_per_record": 200,
                "all_records_pose_count": {
                    row["substrate_id"]: row.get("provenance", {}).get("pose_count")
                    for row in ordered
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"feature_records": len(ordered), "newly_generated": generated}, indent=2))


if __name__ == "__main__":
    main()

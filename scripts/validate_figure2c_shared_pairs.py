#!/usr/bin/env python3
"""Validate that Figure 2C overlays compare identical canonical substrates."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "output/figures/figure2c_data"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    records = read_csv(PACKAGE / "manifest.csv")
    by_key = {(row["domain"], row["substrate_id"]): row for row in records}
    pairs = read_csv(PACKAGE / "shared_overlay_manifest.csv")
    checks = []
    errors = []
    for pair in pairs:
        p7 = by_key.get(("fe_p7cl", pair["p7_substrate_id"]))
        cmc = by_key.get(("fe_cmcporcl", pair["cmcpor_substrate_id"]))
        canonical = pair["canonical_overlap_group"]
        row_errors = []
        if p7 is None:
            row_errors.append(f"missing Fe(P7)Cl record {pair['p7_substrate_id']}")
        if cmc is None:
            row_errors.append(f"missing Fe(CMC-Por)Cl record {pair['cmcpor_substrate_id']}")
        if p7 and p7["shared_overlay_group"] != canonical:
            row_errors.append("P7 manifest canonical identity differs")
        if cmc and cmc["shared_overlay_group"] != canonical:
            row_errors.append("CMC-Por manifest canonical identity differs")
        folder = PACKAGE / pair["pair_directory"]
        required = [
            folder / pair["p7_xyz"].replace("_all_200.xyz", "_all_200_aligned_catalyst_frame.xyz"),
            folder / pair["cmcpor_xyz"].replace("_all_200.xyz", "_all_200_aligned_catalyst_frame.xyz"),
            folder / pair["p7_npz"], folder / pair["cmcpor_npz"],
            folder / pair["p7_svg"], folder / pair["cmcpor_svg"],
            folder / "alignment.json",
        ]
        missing = [str(path.relative_to(PACKAGE)) for path in required if not path.exists()]
        if missing:
            row_errors.append("missing artifacts: " + ", ".join(missing))
        checks.append({
            "overlay_index": int(pair["overlay_index"]),
            "canonical_identity": canonical,
            "p7_substrate_id": pair["p7_substrate_id"],
            "cmcpor_substrate_id": pair["cmcpor_substrate_id"],
            "same_canonical_identity": not any("canonical identity" in error for error in row_errors),
            "catalyst_frame_aligned_files_present": not any(error.startswith("missing artifacts") for error in row_errors),
            "errors": row_errors,
        })
        errors.extend(row_errors)
    report = {
        "figure": "2C",
        "purpose": "Confirm that shared overlays compare the same canonical substrate identity across catalyst environments.",
        "pair_count": len(pairs),
        "valid": not errors,
        "alignment_rule": "Fe + four porphyrin-coordinating N atoms primary; substrate nitrene N lower-weight secondary pivot.",
        "pairs": checks,
    }
    (PACKAGE / "shared_overlay_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    if errors:
        raise SystemExit("Figure 2C shared-pair validation failed: " + " | ".join(errors))
    print(f"Validated {len(pairs)} canonical shared-substrate overlays")


if __name__ == "__main__":
    main()

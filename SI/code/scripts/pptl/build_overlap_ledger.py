#!/usr/bin/env python3
"""Build the frozen cross-catalyst canonical-compound ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

from core import canonical_overlap, canonical_smiles, load_reaction_rows, remove_canonical_overlap


def _row_payload(row) -> dict[str, object]:
    molecule = Chem.MolFromSmiles(row.smiles)
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=molecule, includeChirality=False) if molecule is not None else ""
    return {
        "substrate_id": row.substrate_id,
        "catalyst_id": row.catalyst_id,
        "pathway_id": row.pathway_id,
        "family_id": row.family_id,
        "split_group": row.split_group,
        "canonical_compound_group": canonical_smiles(row.smiles),
        "scaffold_group": canonical_smiles(scaffold) if scaffold else "acyclic",
        "source_order": row.source_order,
    }


def build_ledger(p7_records: Path, cmcpor_records: Path, *, target: str = "ee_percent") -> dict:
    p7 = load_reaction_rows(p7_records, catalyst="fe-p7-cl", target=target, include_unlabelled=True)
    cmc = load_reaction_rows(cmcpor_records, catalyst="cmcpor-fecl", target=target, include_unlabelled=True)
    cmc_aryl = [row for row in cmc if row.family_id == "angew-aryl-c-h-amination"]
    all_overlap = canonical_overlap(p7, cmc)
    aryl_overlap = canonical_overlap(p7, cmc_aryl)
    p7_cold = remove_canonical_overlap(p7, cmc_aryl)
    cmc_cold = remove_canonical_overlap(cmc_aryl, p7)
    return {
        "schema_version": "pptl-canonical-overlap-ledger-v1",
        "target": target,
        "planned_pair_count": 13,
        "domain_counts": {"p7": len(p7), "cmcpor": len(cmc), "cmcpor_aryl": len(cmc_aryl)},
        "all_overlap_count": len(all_overlap),
        "primary_aryl_overlap_count": len(aryl_overlap),
        "all_overlap": all_overlap,
        "primary_aryl_overlap": aryl_overlap,
        "directions": {
            "p7_to_cmcpor_aryl": {
                "source_domain": "fe-p7-cl",
                "target_domain": "cmcpor-fecl",
                "source_cold_count": len(p7_cold),
                "excluded_source_ids": sorted(set(row.substrate_id for row in p7) - set(row.substrate_id for row in p7_cold)),
            },
            "cmcpor_to_p7_aryl": {
                "source_domain": "cmcpor-fecl",
                "target_domain": "fe-p7-cl",
                "source_cold_count": len(cmc_cold),
                "excluded_source_ids": sorted(set(row.substrate_id for row in cmc_aryl) - set(row.substrate_id for row in cmc_cold)),
            },
        },
        "rows": {
            "p7": [_row_payload(row) for row in p7],
            "cmcpor_aryl": [_row_payload(row) for row in cmc_aryl],
        },
        "policy": {
            "atom_maps_removed_before_canonicalization": True,
            "cold_start_excludes_canonical_overlap": True,
            "paired_rows_are_diagnostic_only": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p7-records", type=Path, required=True)
    parser.add_argument("--cmcpor-records", type=Path, required=True)
    parser.add_argument("--target", choices=("ee_percent", "isolated_yield_percent"), default="ee_percent")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_ledger(args.p7_records, args.cmcpor_records, target=args.target)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_overlap_count": report["all_overlap_count"], "primary_aryl_overlap_count": report["primary_aryl_overlap_count"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

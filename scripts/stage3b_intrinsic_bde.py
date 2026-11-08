#!/usr/bin/env python3
"""Compute uncalibrated intrinsic C-H BDE features with GFN2-xTB."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from rdkit import Chem
from rdkit.Chem import AllChem


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_OUTPUT = ROOT / "data/jacs_2025/stage3/features/bde.jsonl"
DEFAULT_XTB = ROOT / ".chem-env/bin/xtb"
EXCLUDED_SUBSTRATES = {"1ad", "1z"}
HARTREE_TO_KCAL = 627.509474
ENERGY_RE = re.compile(r"TOTAL ENERGY\s+(-?\d+\.\d+)\s+Eh")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def mol_with_conformer(smiles: str) -> Chem.Mol:
    molecule = Chem.AddHs(Chem.MolFromSmiles(smiles))
    if molecule is None:
        raise ValueError(f"Could not parse substrate SMILES: {smiles}")
    status = AllChem.EmbedMolecule(molecule, randomSeed=20260801, useRandomCoords=True)
    if status != 0:
        raise ValueError("RDKit conformer embedding failed")
    AllChem.UFFOptimizeMolecule(molecule, maxIters=300)
    return molecule


def xyz_text(molecule: Chem.Mol, omit_index: int | None = None) -> str:
    conformer = molecule.GetConformer()
    atom_lines = []
    for index, atom in enumerate(molecule.GetAtoms()):
        if index == omit_index:
            continue
        point = conformer.GetAtomPosition(index)
        atom_lines.append(f"{atom.GetSymbol()} {point.x:.8f} {point.y:.8f} {point.z:.8f}")
    return f"{len(atom_lines)}\nGFN2-xTB BDE input\n" + "\n".join(atom_lines) + "\n"


def run_xtb(xtb: Path, xyz: str, uhf: int, timeout_seconds: int, optimize: bool = True) -> tuple[float | None, str]:
    with tempfile.TemporaryDirectory(prefix="stage3b-xtb-") as temporary:
        work = Path(temporary)
        input_path = work / "input.xyz"
        input_path.write_text(xyz, encoding="utf-8")
        command = [str(xtb), str(input_path), "--gfn", "2", "--alpb", "ether"]
        if optimize:
            command.append("--opt")
        if uhf:
            command.extend(["--uhf", str(uhf)])
        try:
            result = subprocess.run(command, cwd=work, text=True, capture_output=True, timeout=timeout_seconds, check=False)
        except subprocess.TimeoutExpired:
            return None, "timeout"
        output = result.stdout + "\n" + result.stderr
        match = ENERGY_RE.search(output)
        if result.returncode != 0 or match is None:
            return None, f"failed_returncode_{result.returncode}"
        return float(match.group(1)), "completed"


def hydrogen_reference(xtb: Path, timeout_seconds: int) -> tuple[float, str]:
    energy, status = run_xtb(xtb, "1\nH atom\nH 0 0 0\n", 1, timeout_seconds, optimize=False)
    if energy is None:
        raise RuntimeError(f"Hydrogen atom reference failed: {status}")
    return energy, status


def candidate_hydrogen_index(molecule: Chem.Mol, atom_map_id: int) -> tuple[int, int] | None:
    heavy_index = next((atom.GetIdx() for atom in molecule.GetAtoms() if atom.GetAtomMapNum() == atom_map_id), None)
    if heavy_index is None:
        return None
    hydrogen = next((neighbor.GetIdx() for neighbor in molecule.GetAtomWithIdx(heavy_index).GetNeighbors() if neighbor.GetAtomicNum() == 1), None)
    if hydrogen is None:
        return None
    return heavy_index, hydrogen


def build_feature_row(record: dict[str, Any], xtb: Path, timeout_seconds: int, hydrogen_energy: float) -> dict[str, Any]:
    substrate_smiles = record["structure"].get("atom_mapped_substrate_smiles")
    molecule = mol_with_conformer(substrate_smiles)
    neutral_energy, neutral_status = run_xtb(xtb, xyz_text(molecule), 0, timeout_seconds)
    sites = []
    for site in record["reaction_center"]["candidate_sites"]:
        site_type = str(site.get("site_type", ""))
        if "aryl" in site_type:
            continue
        mapping = candidate_hydrogen_index(molecule, int(site["atom_map_id"]))
        if mapping is None:
            sites.append({"site_id": site["site_id"], "status": "missing_explicit_hydrogen"})
            continue
        _, hydrogen_index = mapping
        radical_energy, radical_status = run_xtb(xtb, xyz_text(molecule, hydrogen_index), 1, timeout_seconds)
        row = {
            "site_id": site["site_id"],
            "atom_map_id": site["atom_map_id"],
            "site_type": site_type,
            "status": radical_status if radical_energy is not None and neutral_energy is not None else "failed",
            "neutral_optimization_status": neutral_status,
            "radical_optimization_status": radical_status,
        }
        if radical_energy is not None and neutral_energy is not None:
            row["absolute_intrinsic_c_h_bde"] = (radical_energy + hydrogen_energy - neutral_energy) * HARTREE_TO_KCAL
        sites.append(row)

    successful = [site for site in sites if isinstance(site.get("absolute_intrinsic_c_h_bde"), float)]
    successful.sort(key=lambda site: site["absolute_intrinsic_c_h_bde"])
    for rank, site in enumerate(successful, start=1):
        site["within_substrate_bde_rank"] = rank
    by_id = {site["site_id"]: site for site in successful}
    reported_id = record["reaction_center"]["reported_reactive_site"]["site_id"]
    reported = by_id.get(reported_id)
    competitors = [site["absolute_intrinsic_c_h_bde"] for site in successful if site["site_id"] != reported_id]
    block: dict[str, Any] = {
        "candidate_site_count": len(sites),
        "successful_site_count": len(successful),
        "failed_site_count": len(sites) - len(successful),
        "min_absolute_intrinsic_c_h_bde": min((site["absolute_intrinsic_c_h_bde"] for site in successful), default=None),
        "calibration_status": "uncalibrated_xtb",
    }
    if reported is not None:
        block.update(
            {
                "absolute_intrinsic_c_h_bde": reported["absolute_intrinsic_c_h_bde"],
                "within_substrate_bde_rank": reported["within_substrate_bde_rank"],
                "bde_competition_gap": reported["absolute_intrinsic_c_h_bde"] - min(competitors) if competitors else None,
            }
        )
    return {
        "schema_version": "stage3b-intrinsic-bde-features-v1",
        "substrate_id": record["substrate_id"],
        "feature_blocks": {"stage3b_bde_features": block},
        "candidate_site_records": sites,
        "provenance": {
            "method": "GFN2-xTB",
            "solvent": "ALPB(ether)",
            "definition": "substrate radical + H atom - substrate",
            "radical_state": "corresponding doublet carbon radical",
            "hydrogen_reference_energy_hartree": hydrogen_energy,
            "excluded_substrate": record["substrate_id"] in EXCLUDED_SUBSTRATES,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--xtb", type=Path, default=DEFAULT_XTB)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = [
        record
        for record in read_jsonl(args.records)
        if record["substrate_id"] not in EXCLUDED_SUBSTRATES
        and record.get("outcome", {}).get("ee_percent") is not None
    ]
    hydrogen_energy, _ = hydrogen_reference(args.xtb, args.timeout_seconds)
    rows = [build_feature_row(record, args.xtb, args.timeout_seconds, hydrogen_energy) for record in records]
    write_jsonl(args.output, rows)
    print(f"Wrote Stage 3b BDE features for {len(rows)} substrates to {args.output}")


if __name__ == "__main__":
    raise SystemExit(main())

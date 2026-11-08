#!/usr/bin/env python3
"""Generate Stage 2 Tier 1 feature blocks for feature-ready records."""

from __future__ import annotations

import argparse
import json
import platform
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy
from rdkit import Chem, DataStructs
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdFingerprintGenerator, rdMolDescriptors


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
DEFAULT_MANIFEST = ROOT / "data/jacs_2025/stage2/feature-manifest.json"
DEFAULT_OUTPUT = ROOT / "data/jacs_2025/stage2/features/tier1.jsonl"

ELEMENTS = ["C", "H", "N", "O", "F", "Si", "P", "S", "Cl"]
SITE_TYPES = [
    "aliphatic",
    "aryl",
    "benzylic",
    "benzylic_adjacent",
    "carbonyl_alpha",
    "cycloalkyl",
    "heteroaryl_adjacent",
    "silylalkyl_substituted",
    "thioether_benzylic",
]
BOND_TYPES = ["SINGLE", "DOUBLE", "TRIPLE", "AROMATIC"]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")


def rdkit_version() -> str:
    try:
        return metadata.version("rdkit")
    except metadata.PackageNotFoundError:
        return "unknown"


def molecule_from_record(record: dict[str, Any]) -> Chem.Mol:
    smiles = record["structure"]["atom_mapped_substrate_smiles"]
    molecule = Chem.MolFromSmiles(smiles, sanitize=True)
    if molecule is None:
        raise ValueError(f"{record['substrate_id']}: atom-mapped substrate SMILES does not parse")
    return molecule


def atom_by_map_id(molecule: Chem.Mol, atom_map_id: int) -> Chem.Atom:
    matches = [atom for atom in molecule.GetAtoms() if atom.GetAtomMapNum() == atom_map_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one atom with map id {atom_map_id}, found {len(matches)}")
    return matches[0]


def element_counts(molecule: Chem.Mol) -> dict[str, int]:
    with_hydrogens = Chem.AddHs(molecule)
    counts = {f"element_count_{element}": 0 for element in ELEMENTS}
    counts["element_count_other"] = 0
    for atom in with_hydrogens.GetAtoms():
        symbol = atom.GetSymbol()
        key = f"element_count_{symbol}"
        if key in counts:
            counts[key] += 1
        else:
            counts["element_count_other"] += 1
    return counts


def candidate_site_type_counts(record: dict[str, Any]) -> dict[str, int]:
    counts = {f"candidate_site_count_{site_type}": 0 for site_type in SITE_TYPES}
    counts["candidate_site_count_other"] = 0
    for site in record["reaction_center"]["candidate_sites"]:
        site_type = site["site_type"]
        key = f"candidate_site_count_{site_type}"
        if key in counts:
            counts[key] += 1
        else:
            counts["candidate_site_count_other"] += 1
    counts["candidate_site_count_total"] = len(record["reaction_center"]["candidate_sites"])
    return counts


def tier1_physchem(record: dict[str, Any], molecule: Chem.Mol) -> dict[str, float | int]:
    features: dict[str, float | int] = {
        "atom_count": Chem.AddHs(molecule).GetNumAtoms(),
        "heavy_atom_count": molecule.GetNumHeavyAtoms(),
        "molecular_weight": Descriptors.MolWt(molecule),
        "exact_molecular_weight": Descriptors.ExactMolWt(molecule),
        "heavy_atom_molecular_weight": Descriptors.HeavyAtomMolWt(molecule),
        "num_valence_electrons": Descriptors.NumValenceElectrons(molecule),
        "formal_charge": Chem.GetFormalCharge(molecule),
        "mol_logp": Crippen.MolLogP(molecule),
        "tpsa": rdMolDescriptors.CalcTPSA(molecule),
        "labute_asa": rdMolDescriptors.CalcLabuteASA(molecule),
        "bertz_ct": Descriptors.BertzCT(molecule),
        "fraction_csp3": rdMolDescriptors.CalcFractionCSP3(molecule),
        "rotatable_bond_count": Lipinski.NumRotatableBonds(molecule),
        "h_donor_count": Lipinski.NumHDonors(molecule),
        "h_acceptor_count": Lipinski.NumHAcceptors(molecule),
        "ring_count": rdMolDescriptors.CalcNumRings(molecule),
        "aromatic_ring_count": rdMolDescriptors.CalcNumAromaticRings(molecule),
        "aliphatic_ring_count": rdMolDescriptors.CalcNumAliphaticRings(molecule),
        "saturated_ring_count": rdMolDescriptors.CalcNumSaturatedRings(molecule),
        "heteroatom_count": rdMolDescriptors.CalcNumHeteroatoms(molecule),
        "amide_bond_count": rdMolDescriptors.CalcNumAmideBonds(molecule),
        "bridgehead_atom_count": rdMolDescriptors.CalcNumBridgeheadAtoms(molecule),
        "spiro_atom_count": rdMolDescriptors.CalcNumSpiroAtoms(molecule),
        "atom_stereo_center_count": rdMolDescriptors.CalcNumAtomStereoCenters(molecule),
        "unspecified_atom_stereo_center_count": rdMolDescriptors.CalcNumUnspecifiedAtomStereoCenters(molecule),
    }
    features.update(element_counts(molecule))
    features.update(candidate_site_type_counts(record))
    return features


def tier1_fingerprint(molecule: Chem.Mol, radius: int, n_bits: int, use_chirality: bool) -> dict[str, Any]:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=radius,
        fpSize=n_bits,
        includeChirality=use_chirality,
    )
    fingerprint = generator.GetFingerprint(molecule)
    bit_vector_array = numpy.zeros((n_bits,), dtype=int)
    DataStructs.ConvertToNumpyArray(fingerprint, bit_vector_array)
    bit_vector = bit_vector_array.tolist()
    on_bits = list(fingerprint.GetOnBits())
    return {
        "fingerprint_type": "Morgan",
        "radius": radius,
        "n_bits": n_bits,
        "use_chirality": use_chirality,
        "on_bit_count": len(on_bits),
        "on_bits": on_bits,
        "bit_vector": bit_vector,
    }


def min_ring_size(atom: Chem.Atom) -> int | None:
    ring_sizes = [len(ring) for ring in atom.GetOwningMol().GetRingInfo().AtomRings() if atom.GetIdx() in ring]
    return min(ring_sizes) if ring_sizes else None


def shortest_distance(molecule: Chem.Mol, source_atom: Chem.Atom, target_map_id: int) -> int | None:
    try:
        target_atom = atom_by_map_id(molecule, target_map_id)
    except ValueError:
        return None
    distance_matrix = Chem.GetDistanceMatrix(molecule)
    return int(distance_matrix[source_atom.GetIdx(), target_atom.GetIdx()])


def neighbor_symbol_counts(atom: Chem.Atom) -> dict[str, int]:
    counts = {f"neighbor_count_{element}": 0 for element in ELEMENTS}
    counts["neighbor_count_other"] = 0
    for neighbor in atom.GetNeighbors():
        key = f"neighbor_count_{neighbor.GetSymbol()}"
        if key in counts:
            counts[key] += 1
        else:
            counts["neighbor_count_other"] += 1
    return counts


def bond_type_counts(atom: Chem.Atom) -> dict[str, int]:
    counts = {f"bond_count_{bond_type.lower()}": 0 for bond_type in BOND_TYPES}
    for bond in atom.GetBonds():
        bond_type = str(bond.GetBondType())
        key = f"bond_count_{bond_type.lower()}"
        if key in counts:
            counts[key] += 1
    return counts


def candidate_site_features(record: dict[str, Any], molecule: Chem.Mol) -> list[dict[str, Any]]:
    reported_atom_map_id = record["reaction_center"]["reported_reactive_site"]["atom_map_id"]
    features = []
    for site in record["reaction_center"]["candidate_sites"]:
        atom = atom_by_map_id(molecule, site["atom_map_id"])
        site_features: dict[str, Any] = {
            "site_id": site["site_id"],
            "atom_map_id": site["atom_map_id"],
            "site_type": site["site_type"],
            "is_reported_reactive_site": site["atom_map_id"] == reported_atom_map_id,
            "atomic_num": atom.GetAtomicNum(),
            "degree": atom.GetDegree(),
            "total_degree": atom.GetTotalDegree(),
            "explicit_valence": atom.GetValence(Chem.ValenceType.EXPLICIT),
            "implicit_valence": atom.GetValence(Chem.ValenceType.IMPLICIT),
            "formal_charge": atom.GetFormalCharge(),
            "hybridization": str(atom.GetHybridization()),
            "is_aromatic": atom.GetIsAromatic(),
            "is_in_ring": atom.IsInRing(),
            "min_ring_size": min_ring_size(atom),
            "hydrogen_count": int(atom.GetTotalNumHs()),
            "implicit_hydrogen_count": atom.GetNumImplicitHs(),
            "explicit_hydrogen_count": atom.GetNumExplicitHs(),
            "carbon_neighbor_count": sum(1 for neighbor in atom.GetNeighbors() if neighbor.GetSymbol() == "C"),
            "hetero_neighbor_count": sum(1 for neighbor in atom.GetNeighbors() if neighbor.GetSymbol() not in {"C", "H"}),
            "aromatic_neighbor_count": sum(1 for neighbor in atom.GetNeighbors() if neighbor.GetIsAromatic()),
            "ring_neighbor_count": sum(1 for neighbor in atom.GetNeighbors() if neighbor.IsInRing()),
            "topological_distance_to_nitrene_n": shortest_distance(molecule, atom, 3),
            "topological_distance_to_azide_ipso_c": shortest_distance(molecule, atom, 4),
            "topological_distance_to_reported_site": shortest_distance(molecule, atom, reported_atom_map_id),
            "is_benzylic_like": site["site_type"] in {"benzylic", "benzylic_adjacent", "thioether_benzylic"},
            "is_heteroaryl_adjacent_like": site["site_type"] == "heteroaryl_adjacent",
            "is_carbonyl_alpha": site["site_type"] == "carbonyl_alpha",
            "is_cycloalkyl": site["site_type"] == "cycloalkyl",
        }
        site_features.update(neighbor_symbol_counts(atom))
        site_features.update(bond_type_counts(atom))
        features.append(site_features)
    return features


def manifest_block(manifest: dict[str, Any], block_id: str) -> dict[str, Any]:
    for block in manifest["feature_blocks"]:
        if block["block_id"] == block_id:
            return block
    raise ValueError(f"Feature manifest is missing {block_id}")


def generate_tier1(records_path: Path, manifest_path: Path) -> list[dict[str, Any]]:
    records = read_jsonl(records_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fingerprint_params = manifest_block(manifest, "tier1_fingerprint")["parameters"]
    feature_ready_records = [record for record in records if record["curation_status"] == "feature_ready"]
    outputs = []
    for record in feature_ready_records:
        molecule = molecule_from_record(record)
        outputs.append(
            {
                "schema_version": "stage2-tier1-features-v1",
                "substrate_id": record["substrate_id"],
                "reaction_id": record["reaction_id"],
                "curation_status": record["curation_status"],
                "feature_blocks": {
                    "tier1_physchem": tier1_physchem(record, molecule),
                    "tier1_fingerprint": tier1_fingerprint(
                        molecule,
                        radius=fingerprint_params["radius"],
                        n_bits=fingerprint_params["n_bits"],
                        use_chirality=fingerprint_params["use_chirality"],
                    ),
                    "candidate_site_features": candidate_site_features(record, molecule),
                },
                "provenance": {
                    "records_path": str(records_path.relative_to(ROOT) if records_path.is_relative_to(ROOT) else records_path),
                    "feature_manifest_path": str(
                        manifest_path.relative_to(ROOT) if manifest_path.is_relative_to(ROOT) else manifest_path
                    ),
                    "rdkit_version": rdkit_version(),
                    "python_version": platform.python_version(),
                    "source_atom_mapped_substrate_smiles": record["structure"]["atom_mapped_substrate_smiles"],
                },
            }
        )
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--feature-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def display_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def main() -> int:
    args = parse_args()
    outputs = generate_tier1(args.records, args.feature_manifest)
    write_jsonl(args.output, outputs)
    print(f"Wrote Stage 2 Tier 1 features for {len(outputs)} records to {display_path(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

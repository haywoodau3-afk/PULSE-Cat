#!/usr/bin/env python3
"""Screen ranked aryl-azide proposals against four precursor disconnections.

The four route labels are deliberately structural:

* A: 2-bromoaniline + terminal alkene
* B: 2-vinylaniline + aryl/alkyl bromide
* C: 2-ethynylaniline + aryl/alkyl bromide
* D: 2-iodoaniline + terminal alkyne

For a generated substrate to enter this screen it must contain the conservative
linear ``Ar-CH2-CH2-R`` morphology.  Fused, spiro, branched and heteroatom-
attached tethers are retained as proposals but are marked ``route_not_mapped``
rather than being forced into a disconnection.

PubChem compound presence is a database-registration check.  It is not a claim
of current supplier stock, price, lead time, synthetic success, or laboratory
permission.  Results are cached so the exact query set can be frozen and
replayed.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import deque
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from rdkit import Chem


FIXED_CORES = {
    "A": {"name": "2-bromoaniline", "smiles": "Nc1ccccc1Br", "cid": 11992, "partner_kind": "terminal_alkene"},
    "B": {"name": "2-vinylaniline", "smiles": "C=Cc1ccccc1N", "cid": 10351689, "partner_kind": "bromide"},
    "C": {"name": "2-ethynylaniline", "smiles": "C#Cc1ccccc1N", "cid": 4153905, "partner_kind": "bromide"},
    "D": {"name": "2-iodoaniline", "smiles": "Nc1ccccc1I", "cid": 11995, "partner_kind": "terminal_alkyne"},
}


def route_fragment(smiles: str) -> str | None:
    """Return an R-group fragment with one ``*`` attachment atom."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    for ar in mol.GetAtoms():
        if not (ar.GetIsAromatic() and ar.GetAtomicNum() == 6):
            continue
        proximal = [n for n in ar.GetNeighbors() if n.GetAtomicNum() == 7 and not n.GetIsAromatic()]
        if not proximal:
            continue
        for ortho in ar.GetNeighbors():
            if not (ortho.GetIsAromatic() and ortho.GetAtomicNum() == 6):
                continue
            for c1 in ortho.GetNeighbors():
                if c1.GetAtomicNum() != 6 or c1.GetIsAromatic() or c1.GetHybridization() != Chem.HybridizationType.SP3:
                    continue
                for c2 in c1.GetNeighbors():
                    if c2.GetIdx() == ortho.GetIdx() or c2.GetAtomicNum() != 6 or c2.GetIsAromatic() or c2.GetHybridization() != Chem.HybridizationType.SP3:
                        continue
                    if c1.GetTotalNumHs() != 2 or c2.GetTotalNumHs() != 2:
                        continue
                    extras = [n for n in c2.GetNeighbors() if n.GetIdx() != c1.GetIdx()]
                    if len(extras) != 1 or extras[0].GetAtomicNum() != 6:
                        continue
                    r_atom = extras[0]
                    # The R group must be a separate, acyclic component after
                    # removing the two-carbon tether; cycles/fused systems are
                    # not silently assigned a linear two-step route.
                    seen: set[int] = set()
                    queue: deque[int] = deque([r_atom.GetIdx()])
                    while queue:
                        index = queue.popleft()
                        if index in seen:
                            continue
                        seen.add(index)
                        for neighbor in mol.GetAtomWithIdx(index).GetNeighbors():
                            if neighbor.GetIdx() != c2.GetIdx() and neighbor.GetIdx() not in seen:
                                queue.append(neighbor.GetIdx())
                    scaffold = {ar.GetIdx(), ortho.GetIdx(), c1.GetIdx(), c2.GetIdx(), proximal[0].GetIdx()}
                    if seen & scaffold:
                        continue
                    rw = Chem.RWMol()
                    mapping: dict[int, int] = {}
                    for index in sorted(seen):
                        mapping[index] = rw.AddAtom(Chem.Atom(mol.GetAtomWithIdx(index)))
                    for bond in mol.GetBonds():
                        begin, end = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
                        if begin in seen and end in seen:
                            rw.AddBond(mapping[begin], mapping[end], bond.GetBondType())
                    dummy = rw.AddAtom(Chem.Atom(0))
                    rw.AddBond(dummy, mapping[r_atom.GetIdx()], Chem.BondType.SINGLE)
                    fragment = rw.GetMol()
                    Chem.SanitizeMol(fragment)
                    return Chem.MolToSmiles(fragment, canonical=True)
    return None


def make_partner(fragment: str, unit: str) -> str | None:
    if fragment.count("*") != 1:
        return None
    candidate = fragment.replace("*", unit)
    mol = Chem.MolFromSmiles(candidate)
    if mol is None:
        return None
    Chem.SanitizeMol(mol)
    return Chem.MolToSmiles(mol, canonical=True)


def bromide_is_carbon_bound(smiles: str) -> bool:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    for bromine in (atom for atom in mol.GetAtoms() if atom.GetAtomicNum() == 35):
        neighbors = bromine.GetNeighbors()
        if len(neighbors) != 1 or neighbors[0].GetAtomicNum() != 6:
            return False
        carbon = neighbors[0]
        if not (carbon.GetIsAromatic() or carbon.GetHybridization() == Chem.HybridizationType.SP3):
            return False
    return True


def query_pubchem(smiles: str, cache: dict[str, Any], timeout: float = 20.0) -> dict[str, Any]:
    if smiles in cache:
        return cache[smiles]
    endpoint = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/"
        f"{quote(smiles, safe='')}/property/IUPACName,CanonicalSMILES,InChIKey/JSON"
    )
    request = Request(endpoint, headers={"User-Agent": "genaisubstrate-route-screen/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        props = payload.get("PropertyTable", {}).get("Properties", [])
        if not props:
            result = {"status": "no_compound", "query_smiles": smiles, "endpoint": endpoint}
        else:
            item = props[0]
            result = {
                "status": "pubchem_compound_hit",
                "query_smiles": smiles,
                "endpoint": endpoint,
                "cid": item.get("CID"),
                "iupac_name": item.get("IUPACName"),
                "canonical_smiles": item.get("ConnectivitySMILES") or item.get("CanonicalSMILES"),
                "inchikey": item.get("InChIKey"),
            }
    except Exception as exc:  # network errors are explicit unknowns, never negatives
        result = {"status": "query_error", "query_smiles": smiles, "endpoint": endpoint, "error": str(exc)}
    cache[smiles] = result
    return result


def pubchem_endpoint(smiles: str) -> str:
    return (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/"
        f"{quote(smiles, safe='')}/property/IUPACName,CanonicalSMILES,InChIKey/JSON"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--max-candidates", type=int, default=16)
    parser.add_argument("--query-pubchem", action="store_true", help="query PubChem; otherwise emit query URLs only")
    args = parser.parse_args()

    cache: dict[str, Any] = {}
    if args.cache.is_file():
        cache = json.loads(args.cache.read_text(encoding="utf-8"))
    candidates = list(csv.DictReader(args.candidates.open(newline="", encoding="utf-8")))

    def predicted(row: dict[str, str]) -> float:
        for key in ("predicted_ee", "predicted_ee_percent", "ee_prediction_development"):
            try:
                return float(row.get(key, ""))
            except ValueError:
                pass
        return float("-inf")

    candidates.sort(key=lambda row: (-predicted(row), row.get("candidate_id", "")))
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rank, row in enumerate(candidates, start=1):
        canonical = row.get("canonical_smiles", "")
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        if len(output) >= args.max_candidates:
            break
        fragment = route_fragment(canonical)
        result: dict[str, Any] = {
            "candidate_id": row.get("candidate_id", ""),
            "candidate_rank": rank,
            "canonical_smiles": canonical,
            "predicted_ee": row.get("predicted_ee", row.get("predicted_ee_percent", row.get("ee_prediction_development", ""))),
            "ad_status": row.get("ad_status", ""),
            "r_fragment": fragment or "",
            "route_status": "route_mapped" if fragment else "route_not_mapped",
        }
        for method, core in FIXED_CORES.items():
            if fragment is None:
                result[f"{method}_partner_smiles"] = ""
                result[f"{method}_pubchem_status"] = "route_not_mapped"
                continue
            unit = {"A": "C=C", "B": "Br", "C": "Br", "D": "C#C"}[method]
            partner = make_partner(fragment, unit)
            if method in {"B", "C"} and partner is not None and not bromide_is_carbon_bound(partner):
                partner = None
            result[f"{method}_partner_smiles"] = partner or ""
            if partner is None:
                result[f"{method}_pubchem_status"] = "partner_structurally_infeasible"
                continue
            if args.query_pubchem:
                hit = query_pubchem(partner, cache)
                result[f"{method}_pubchem_status"] = hit["status"]
                result[f"{method}_pubchem_cid"] = hit.get("cid", "")
                result[f"{method}_pubchem_name"] = hit.get("iupac_name", "")
            else:
                result[f"{method}_pubchem_status"] = "query_pending"
                result[f"{method}_pubchem_url"] = pubchem_endpoint(partner)
        result["fixed_core_pubchem_status"] = "known_pubchem_core_records"
        output.append(result)

    args.cache.parent.mkdir(parents=True, exist_ok=True)
    args.cache.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(output[0]) if output else ["candidate_id", "route_status"]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)
    print(json.dumps({"candidate_count": len(output), "query_count": len(cache), "query_pubchem": args.query_pubchem, "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate a deterministic, scaffold-constrained comparator pool."""

from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

SUBSTITUENTS = ["C", "CC", "CCC", "CO", "OC", "F", "Cl", "Br", "C(F)(F)F", "C#N", "C(=O)C", "C(=O)OC", "c1ccccc1", "c1ccc(F)cc1", "c1ccc(Cl)cc1", "c1ccccc1C", "C1CCCCC1", "C1CC1", "C=C", "C#C", "CF", "CCl", "CBr", "COC", "CCO", "C(C)C", "C(C)(C)C", "C1CCCC1", "c1ccncc1", "c1ccoc1", "c1ccsc1", "C(=O)N", "C(C)O", "C(C)F", "C(C)Cl", "C(C)Br", "C(C)C#N", "C1CCOCC1"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=50000)
    args = parser.parse_args()
    rows = []
    i = 0
    # Fixed ordering and vocabulary make this comparator exactly reproducible.
    for nitrene, remote_a, remote_b in product(SUBSTITUENTS, SUBSTITUENTS, SUBSTITUENTS):
        smiles = f"[N-]=[N+]=Nc1cc({nitrene})ccc1CCc2cc({remote_a})cc({remote_b})c2"
        rows.append({"candidate_id": f"enum-{i:06d}", "smiles": smiles, "provenance": "deterministic-enumeration", "enumeration_index": i})
        i += 1
        if i >= args.budget:
            break
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({"budget": args.budget, "generated": len(rows), "vocabulary_size": len(SUBSTITUENTS)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

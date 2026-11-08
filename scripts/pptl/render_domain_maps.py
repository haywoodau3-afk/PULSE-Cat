#!/usr/bin/env python3
"""Compare persisted occupancy arrays from two catalyst namespaces.

The output is numerical and auditable. SVG rendering remains a derived view;
this command never converts a rendered image back into model features.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance


def _arrays(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as archive:
        return {key: np.asarray(archive[key], dtype=float) for key in archive.files}


def compare_arrays(left: Path, right: Path) -> dict:
    left_arrays, right_arrays = _arrays(left), _arrays(right)
    common = sorted(set(left_arrays) & set(right_arrays))
    comparisons = []
    for key in common:
        a, b = left_arrays[key].ravel(), right_arrays[key].ravel()
        if a.shape != b.shape:
            continue
        a_positive = np.clip(a, 0.0, None)
        b_positive = np.clip(b, 0.0, None)
        if float(a_positive.sum()) > 0:
            a_positive = a_positive / a_positive.sum()
        if float(b_positive.sum()) > 0:
            b_positive = b_positive / b_positive.sum()
        comparisons.append(
            {
                "field": key,
                "shape": list(a.shape),
                "l1": float(np.mean(np.abs(a - b))),
                "wasserstein": float(wasserstein_distance(a, b)),
                "jensen_shannon": float(jensenshannon(a_positive + 1e-12, b_positive + 1e-12)),
            }
        )
    return {
        "left": str(left),
        "right": str(right),
        "common_field_count": len(comparisons),
        "comparisons": comparisons,
        "status": "valid" if comparisons else "no_common_compatible_fields",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare_arrays(args.left, args.right)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Report interval coverage and applicability-domain diagnostics from CSV predictions."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def f(row: dict[str, str], key: str) -> float | None:
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--observed", default="observed")
    parser.add_argument("--prediction", default="prediction")
    parser.add_argument("--lower-80", default="lower_80")
    parser.add_argument("--upper-80", default="upper_80")
    parser.add_argument("--lower-95", default="lower_95")
    parser.add_argument("--upper-95", default="upper_95")
    parser.add_argument("--ad-distance", default="ad_distance")
    args = parser.parse_args()
    rows = list(csv.DictReader(args.input.open(encoding="utf-8")))
    usable = [r for r in rows if f(r, args.observed) is not None and f(r, args.prediction) is not None]
    result: dict[str, object] = {"input_count": len(rows), "scored_count": len(usable)}
    errors = [abs(f(r, args.observed) - f(r, args.prediction)) for r in usable]
    result["mae"] = sum(errors) / len(errors) if errors else None
    for label, lo_key, hi_key in (("80", args.lower_80, args.upper_80), ("95", args.lower_95, args.upper_95)):
        bounded = [(f(r, args.observed), f(r, lo_key), f(r, hi_key)) for r in usable]
        bounded = [x for x in bounded if None not in x]
        result[f"coverage_{label}"] = sum(lo <= y <= hi for y, lo, hi in bounded) / len(bounded) if bounded else None
        result[f"interval_count_{label}"] = len(bounded)
    distances = [f(r, args.ad_distance) for r in rows]
    distances = [x for x in distances if x is not None]
    result["ad_distance_count"] = len(distances)
    result["ad_distance_mean"] = sum(distances) / len(distances) if distances else None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Aggregate runtime coverage JSON into per-library/category tables
and merge with existing MR coverage metrics for RQ1 comparison.

Usage:
    python3 scripts/aggregate_runtime_coverage.py \
        --runtime output/coverage/runtime_coverage.json \
        --out output/coverage/runtime_coverage_summary.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGGREGATE_DIR = PROJECT_ROOT / "output" / "aggregate"


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _pct(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    return s[int(p * (len(s) - 1))]


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = _mean(xs), _mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return round(num / (dx * dy), 4) if dx and dy else None


def _dist(xs: list[float]) -> dict:
    return {
        "mean":   round(_mean(xs), 4),
        "median": round(_median(xs), 4),
        "p25":    round(_pct(xs, 0.25), 4),
        "p75":    round(_pct(xs, 0.75), 4),
        "min":    round(min(xs), 4) if xs else 0.0,
        "max":    round(max(xs), 4) if xs else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime", required=True)
    ap.add_argument("--out", default=str(PROJECT_ROOT / "output" / "coverage" / "runtime_coverage_summary.json"))
    args = ap.parse_args()

    records = json.loads(Path(args.runtime).read_text())

    # Load MR coverage from existing per-sample CSV
    mr_cov: dict[str, float] = {}
    csv_path = AGGREGATE_DIR / "coverage_baselines_combined.csv"
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                mr_cov[row["sample_id"]] = float(row.get("mr_coverage_rate") or 0)

    rows = []
    for r in records:
        cov = r.get("runtime_coverage") or {}
        if not cov:
            continue
        rows.append({
            "sample_id":   r["sample_id"],
            "library":     r["library"],
            "category":    r["category"],
            "stmt_cov":    float(cov.get("statement_coverage_rate") or 0),
            "branch_cov":  float(cov.get("branch_coverage_rate") or 0),
            "mr_cov":      mr_cov.get(r["sample_id"], 0.0),
        })

    stmt   = [r["stmt_cov"] for r in rows]
    branch = [r["branch_cov"] for r in rows]
    mr     = [r["mr_cov"] for r in rows]

    lib_agg: dict[str, list] = defaultdict(list)
    cat_agg: dict[str, list] = defaultdict(list)
    for r in rows:
        lib_agg[r["library"]].append(r)
        cat_agg[r["category"]].append(r)

    def _group_summary(group: list[dict]) -> dict:
        return {
            "n": len(group),
            "stmt":   _dist([r["stmt_cov"] for r in group]),
            "branch": _dist([r["branch_cov"] for r in group]),
            "mr":     _dist([r["mr_cov"] for r in group]),
        }

    summary = {
        "n_with_runtime_coverage": len(rows),
        "n_total_corpus": len(records),
        "overall": {
            "statement_coverage": _dist(stmt),
            "branch_coverage":    _dist(branch),
            "mr_coverage":        _dist(mr),
            "pearson_stmt_vs_mr":   _pearson(stmt, mr),
            "pearson_branch_vs_mr": _pearson(branch, mr),
        },
        "by_library":  {lib: _group_summary(g) for lib, g in sorted(lib_agg.items())},
        "by_category": {cat: _group_summary(g) for cat, g in sorted(cat_agg.items())},
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

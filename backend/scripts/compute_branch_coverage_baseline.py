#!/usr/bin/env python3
"""Compute branch-coverage baseline for all reports and output aggregates.

Adds branch_coverage static proxy alongside the existing statement_coverage
proxy.  Outputs:
  - output/aggregate/branch_coverage_baseline.json  (summary + per-library/category)
  - output/aggregate/coverage_baselines_combined.csv (all metrics per component)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mr_framework.baseline_branch_coverage import compute_branch_coverage_baseline
from mr_framework.pipeline import AGGREGATE_DIR, REPORTS_DIR


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
    idx = int(p * (len(s) - 1))
    return s[idx]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports-dir", default=str(REPORTS_DIR))
    ap.add_argument("--update-reports", action="store_true")
    args = ap.parse_args()

    reports_dir = Path(args.reports_dir)
    rows: list[dict] = []
    failures: list[dict] = []

    for report_path in sorted(reports_dir.glob("*.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        meta = report.get("meta") or {}
        source_path = Path(meta.get("source_path") or "")
        test_path = Path(meta.get("test_path") or "")

        if not source_path.exists() or not test_path.exists():
            failures.append({"sample_id": meta.get("sample_id"), "reason": "missing source/test"})
            continue

        branch = compute_branch_coverage_baseline(
            source_path.read_text(encoding="utf-8", errors="replace"),
            test_path.read_text(encoding="utf-8", errors="replace"),
        )

        if args.update_reports:
            report.setdefault("baselines", {})["branch_coverage"] = branch
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        # pull existing statement coverage if present
        stmt = (report.get("baselines") or {}).get("statement_coverage") or {}
        comp = report.get("completeness") or {}

        rows.append({
            "sample_id": meta.get("sample_id"),
            "library": meta.get("library"),
            "category": meta.get("category"),
            "component_name": meta.get("component_name"),
            # branch
            "branch_coverage_rate": branch.get("branch_coverage_rate", 0.0),
            "total_branches": branch.get("total_branches", 0),
            "covered_branches": branch.get("covered_branches", 0),
            # statement (existing)
            "statement_coverage_rate": stmt.get("statement_coverage_rate", 0.0),
            "total_statements": stmt.get("total_statements", 0),
            "covered_statements": stmt.get("covered_statements", 0),
            # MR
            "mr_coverage_rate": comp.get("coverage_rate", 0.0),
            "mr_touch_rate": comp.get("touch_rate", 0.0),
            "mr_strict_gap_rate": comp.get("strict_gap_rate", 0.0),
            "issue_pressure": report.get("issue_pressure", 0),
        })

    # ── write combined CSV ──────────────────────────────────────────────────
    AGGREGATE_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = AGGREGATE_DIR / "coverage_baselines_combined.csv"
    fieldnames = [
        "sample_id", "library", "category", "component_name",
        "branch_coverage_rate", "total_branches", "covered_branches",
        "statement_coverage_rate", "total_statements", "covered_statements",
        "mr_coverage_rate", "mr_touch_rate", "mr_strict_gap_rate", "issue_pressure",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # ── aggregate summary ───────────────────────────────────────────────────
    branch_rates = [r["branch_coverage_rate"] for r in rows]
    stmt_rates   = [r["statement_coverage_rate"] for r in rows]
    mr_rates     = [r["mr_coverage_rate"] for r in rows]

    def _dist(xs: list[float]) -> dict:
        return {
            "min":    round(min(xs), 6) if xs else 0.0,
            "p25":    round(_pct(xs, 0.25), 6),
            "median": round(_median(xs), 6),
            "p75":    round(_pct(xs, 0.75), 6),
            "max":    round(max(xs), 6) if xs else 0.0,
            "mean":   round(_mean(xs), 6),
        }

    # ── by library ──────────────────────────────────────────────────────────
    lib_rows: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        lib_rows[r["library"]].append(r)

    by_library = {}
    for lib, rs in sorted(lib_rows.items()):
        by_library[lib] = {
            "n": len(rs),
            "mean_branch_coverage":    round(_mean([r["branch_coverage_rate"] for r in rs]), 6),
            "mean_statement_coverage": round(_mean([r["statement_coverage_rate"] for r in rs]), 6),
            "mean_mr_coverage":        round(_mean([r["mr_coverage_rate"] for r in rs]), 6),
        }

    # ── by category ─────────────────────────────────────────────────────────
    cat_rows: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        cat_rows[r["category"]].append(r)

    by_category = {}
    for cat, rs in sorted(cat_rows.items()):
        by_category[cat] = {
            "n": len(rs),
            "mean_branch_coverage":    round(_mean([r["branch_coverage_rate"] for r in rs]), 6),
            "mean_statement_coverage": round(_mean([r["statement_coverage_rate"] for r in rs]), 6),
            "mean_mr_coverage":        round(_mean([r["mr_coverage_rate"] for r in rs]), 6),
        }

    # ── Pearson correlations ─────────────────────────────────────────────────
    import math

    def _pearson(xs: list[float], ys: list[float]) -> float | None:
        n = len(xs)
        if n < 3:
            return None
        mx, my = _mean(xs), _mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        dy = math.sqrt(sum((y - my) ** 2 for y in ys))
        return round(num / (dx * dy), 4) if dx and dy else None

    summary = {
        "n": len(rows),
        "failures": len(failures),
        "branch_coverage": {
            "distribution": _dist(branch_rates),
            "pearson_vs_mr_coverage": _pearson(branch_rates, mr_rates),
        },
        "statement_coverage": {
            "distribution": _dist(stmt_rates),
            "pearson_vs_mr_coverage": _pearson(stmt_rates, mr_rates),
        },
        "mr_coverage": {
            "distribution": _dist(mr_rates),
        },
        "by_library": by_library,
        "by_category": by_category,
        "csv": str(csv_path),
    }

    json_path = AGGREGATE_DIR / "branch_coverage_baseline.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

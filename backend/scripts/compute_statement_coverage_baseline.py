#!/usr/bin/env python3
"""Compute statement coverage baseline for existing reports.

This baseline is a static proxy because the extracted corpus does not include
the original runnable package/test harness for each component library.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mr_framework.baseline_coverage import compute_statement_coverage_baseline
from mr_framework.pipeline import AGGREGATE_DIR, REPORTS_DIR, _baseline_summary


def main() -> int:
    p = argparse.ArgumentParser(description="Compute static statement coverage baseline for output/reports")
    p.add_argument("--reports-dir", default=str(REPORTS_DIR))
    p.add_argument("--update-reports", action="store_true", help="Write baseline results into each report JSON")
    args = p.parse_args()

    rows = []
    failures = []
    for report_path in sorted(Path(args.reports_dir).glob("*.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        meta = report.get("meta") or {}
        source_path = Path(meta.get("source_path") or "")
        test_path = Path(meta.get("test_path") or "")
        if not source_path.exists() or not test_path.exists():
            failures.append({"sample_id": meta.get("sample_id"), "reason": "missing source/test path"})
            continue
        baseline = compute_statement_coverage_baseline(
            source_path.read_text(encoding="utf-8", errors="replace"),
            test_path.read_text(encoding="utf-8", errors="replace"),
        )
        report.setdefault("baselines", {})["statement_coverage"] = baseline
        rows.append(report)
        if args.update_reports:
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    AGGREGATE_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = AGGREGATE_DIR / "statement_coverage_baseline.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "sample_id",
            "library",
            "category",
            "component_name",
            "statement_coverage_rate",
            "total_statements",
            "covered_statements",
            "mr_coverage_rate",
            "touch_rate",
            "strict_gap_rate",
            "issue_pressure",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for report in rows:
            meta = report.get("meta") or {}
            comp = report.get("completeness") or {}
            stmt = ((report.get("baselines") or {}).get("statement_coverage") or {})
            w.writerow(
                {
                    "sample_id": meta.get("sample_id"),
                    "library": meta.get("library"),
                    "category": meta.get("category"),
                    "component_name": meta.get("component_name"),
                    "statement_coverage_rate": stmt.get("statement_coverage_rate"),
                    "total_statements": stmt.get("total_statements"),
                    "covered_statements": stmt.get("covered_statements"),
                    "mr_coverage_rate": comp.get("coverage_rate"),
                    "touch_rate": comp.get("touch_rate"),
                    "strict_gap_rate": comp.get("strict_gap_rate"),
                    "issue_pressure": report.get("issue_pressure"),
                }
            )

    summary = _baseline_summary(rows)
    summary["failures"] = failures
    summary["csv"] = str(csv_path)
    summary["reports_updated"] = bool(args.update_reports)
    json_path = AGGREGATE_DIR / "statement_coverage_baseline.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"summary": summary, "json": str(json_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

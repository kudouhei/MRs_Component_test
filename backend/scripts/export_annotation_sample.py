#!/usr/bin/env python3
"""Export MR/test alignment items for human annotation."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from mr_framework.taxonomy import normalize_type_category  # noqa: E402

REPORTS_DIR = PROJECT_ROOT / "output" / "reports"
OUT_DIR = PROJECT_ROOT / "output" / "validation"


def main() -> int:
    p = argparse.ArgumentParser(description="Export sampled MR coverage items for annotation")
    p.add_argument("--reports-dir", default=str(REPORTS_DIR))
    p.add_argument("--out", default=str(OUT_DIR / "annotation_sample.csv"))
    p.add_argument("--limit", type=int, default=300)
    p.add_argument("--seed", type=int, default=20260525)
    p.add_argument("--include-covered", action="store_true", help="Include covered MRs as well as gaps")
    args = p.parse_args()

    items = []
    for path in sorted(Path(args.reports_dir).glob("*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        meta = report.get("meta") or {}
        for row in report.get("mr_coverage") or []:
            if not args.include_covered and row.get("covered"):
                continue
            relation_type = row.get("relation_type")
            type_category = normalize_type_category(row.get("type_category"), relation_type)
            items.append(
                {
                    "sample_id": meta.get("sample_id"),
                    "library": meta.get("library"),
                    "category": meta.get("category"),
                    "component_name": meta.get("component_name"),
                    "mr_id": row.get("mr_id"),
                    "relation_type": relation_type,
                    "type_category": type_category,
                    "mr_description": row.get("mr_description"),
                    "expected_relation": row.get("expected_relation"),
                    "system_touched": int(bool(row.get("touched"))),
                    "system_covered": int(bool(row.get("covered"))),
                    "system_reason": row.get("reason") or "",
                    "evidence_touch_hits": ";".join(row.get("evidence_touch_hits") or []),
                    "related_tests": ";".join(row.get("related_tests") or []),
                    "human_valid_mr": "",
                    "human_touched": "",
                    "human_covered": "",
                    "human_notes": "",
                }
            )

    random.Random(args.seed).shuffle(items)
    if args.limit and args.limit > 0:
        items = items[: args.limit]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "library",
        "category",
        "component_name",
        "mr_id",
        "relation_type",
        "type_category",
        "mr_description",
        "expected_relation",
        "system_touched",
        "system_covered",
        "system_reason",
        "evidence_touch_hits",
        "related_tests",
        "human_valid_mr",
        "human_touched",
        "human_covered",
        "human_notes",
    ]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(items)

    print(json.dumps({"exported": len(items), "path": str(out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

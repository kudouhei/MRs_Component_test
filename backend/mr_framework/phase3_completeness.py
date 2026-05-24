"""Phase 3 — Completeness metrics and blind-spot diagnostics."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .models import BlindSpotStats, CompletenessMetrics


def _row_touched(row: dict[str, Any]) -> bool:
    return bool(
        row.get("evidence_touch")
        or row.get("hybrid_touched")
        or row.get("touched")
        or row.get("covered")
    )


def _row_covered(row: dict[str, Any]) -> bool:
    return bool(row.get("evidence_covered") or row.get("covered"))


def compute_completeness(mr_coverage: list[dict[str, Any]]) -> CompletenessMetrics:
    total = len(mr_coverage)
    if total == 0:
        return CompletenessMetrics()

    touched = sum(1 for r in mr_coverage if _row_touched(r))
    covered = sum(1 for r in mr_coverage if _row_covered(r))
    hybrid = sum(1 for r in mr_coverage if r.get("hybrid_touched"))
    uncovered = total - covered
    missed = sum(1 for r in mr_coverage if not _row_touched(r) and not _row_covered(r))
    touched_not_cov = sum(1 for r in mr_coverage if _row_touched(r) and not _row_covered(r))

    types_all = {r.get("relation_type") for r in mr_coverage if r.get("relation_type")}
    types_cov = {
        r.get("relation_type")
        for r in mr_coverage
        if r.get("relation_type") and _row_covered(r)
    }

    return CompletenessMetrics(
        total_mrs=total,
        touched_mrs=touched,
        covered_mrs=covered,
        touch_rate=round(touched / total, 6),
        coverage_rate=round(covered / total, 6),
        hybrid_touched_mrs=hybrid,
        hybrid_touch_rate=round(hybrid / total, 6),
        missed_touch_uncovered=missed,
        touched_not_covered=touched_not_cov,
        touched_not_covered_rate=round(touched_not_cov / total, 6),
        overlooked_uncovered_rate=round(missed / uncovered, 6) if uncovered else 0.0,
        distinct_relation_types=len(types_all),
        covered_relation_types=len(types_cov),
        relation_type_coverage_ratio=round(len(types_cov) / len(types_all), 6)
        if types_all
        else 0.0,
    )


def diagnose_blind_spots(mr_coverage: list[dict[str, Any]]) -> BlindSpotStats:
    miss_at_uncov = 0
    touched_not_covered = 0
    blind_counter: Counter[str] = Counter()

    for row in mr_coverage:
        rt = str(row.get("relation_type") or "unknown")
        touched = _row_touched(row)
        covered = _row_covered(row)
        if not covered and not touched:
            miss_at_uncov += 1
            blind_counter[rt] += 1
        elif touched and not covered:
            touched_not_covered += 1
            blind_counter[rt] += 1

    top_blind = [
        {"relation_type": rt, "blind_count": n, "kind": "untouched_or_touched_not_covered"}
        for rt, n in blind_counter.most_common(15)
    ]

    by_cat: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "untouched": 0, "touched_not_covered": 0}
    )
    for row in mr_coverage:
        cat = str(row.get("type_category") or "unknown")
        by_cat[cat]["total"] += 1
        if not _row_touched(row) and not _row_covered(row):
            by_cat[cat]["untouched"] += 1
        elif _row_touched(row) and not _row_covered(row):
            by_cat[cat]["touched_not_covered"] += 1

    return BlindSpotStats(
        miss_at_uncov=miss_at_uncov,
        touched_not_covered=touched_not_covered,
        top_blind_mr_types=top_blind,
        by_type_category=dict(by_cat),
    )

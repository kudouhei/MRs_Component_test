"""Phase 3: completeness metrics and blind spots."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .models import SampleMeta


def _touched(r: dict) -> bool:
    return bool(r.get("touched") or r.get("evidence_touch") or r.get("llm_touched"))


def _covered(r: dict) -> bool:
    return bool(r.get("covered") or r.get("evidence_covered") or r.get("llm_covered"))


def compute_completeness(mr_coverage: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(mr_coverage)
    if n == 0:
        return {"total_mrs": 0, "touch_rate": 0.0, "coverage_rate": 0.0}
    touched = sum(1 for r in mr_coverage if _touched(r))
    covered = sum(1 for r in mr_coverage if _covered(r))
    touched_not_cov = sum(1 for r in mr_coverage if _touched(r) and not _covered(r))
    miss = sum(1 for r in mr_coverage if not _touched(r) and not _covered(r))
    weights = [float(r.get("mr_confidence") or 1.0) for r in mr_coverage]
    w_total = sum(weights) or float(n)
    w_touch = sum(w for r, w in zip(mr_coverage, weights) if _touched(r))
    w_cov = sum(w for r, w in zip(mr_coverage, weights) if _covered(r))
    types_all = {r.get("relation_type") for r in mr_coverage if r.get("relation_type")}
    types_cov = {r.get("relation_type") for r in mr_coverage if r.get("relation_type") and _covered(r)}
    return {
        "total_mrs": n,
        "touched_mrs": touched,
        "covered_mrs": covered,
        "touch_rate": round(touched / n, 6),
        "coverage_rate": round(covered / n, 6),
        "weighted_touch_rate": round(w_touch / w_total, 6),
        "weighted_coverage_rate": round(w_cov / w_total, 6),
        "touched_not_covered": touched_not_cov,
        "touched_not_covered_rate": round(touched_not_cov / n, 6),
        "miss_at_uncov": miss,
        "miss_at_uncov_rate": round(miss / n, 6),
        "strict_gap": n - covered,
        "strict_gap_rate": round((n - covered) / n, 6),
        "distinct_relation_types": len(types_all),
        "covered_relation_types": len(types_cov),
        "uncovered_relation_types": sorted(types_all - types_cov),
        "relation_type_coverage_ratio": round(len(types_cov) / len(types_all), 6) if types_all else 0.0,
        "by_type_category": _by_category(mr_coverage),
        "by_relation_type": _by_relation_type(mr_coverage),
    }


def _by_category(mr_coverage: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in mr_coverage:
        buckets[str(r.get("type_category") or "unknown")].append(r)
    out = {}
    for cat, rows in buckets.items():
        n = len(rows)
        out[cat] = {
            "total": n,
            "touch_rate": round(sum(1 for r in rows if _touched(r)) / n, 6) if n else 0.0,
            "coverage_rate": round(sum(1 for r in rows if _covered(r)) / n, 6) if n else 0.0,
        }
    return out


def _by_relation_type(mr_coverage: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in mr_coverage:
        buckets[str(r.get("relation_type") or "unknown")].append(r)
    out = {}
    for rt, rows in buckets.items():
        n = len(rows)
        out[rt] = {
            "total": n,
            "touched": sum(1 for r in rows if _touched(r)),
            "covered": sum(1 for r in rows if _covered(r)),
            "touch_rate": round(sum(1 for r in rows if _touched(r)) / n, 6) if n else 0.0,
            "coverage_rate": round(sum(1 for r in rows if _covered(r)) / n, 6) if n else 0.0,
        }
    return out


def diagnose_blind_spots(mr_coverage: list[dict[str, Any]], meta: SampleMeta) -> dict[str, Any]:
    blind_counter: Counter[str] = Counter()
    untouched_counter: Counter[str] = Counter()
    weak_counter: Counter[str] = Counter()
    blind_items = []
    for r in mr_coverage:
        if not _covered(r):
            rt = str(r.get("relation_type") or "unknown")
            blind_counter[rt] += 1
            if _touched(r):
                weak_counter[rt] += 1
                severity = "weak_oracle"
            else:
                untouched_counter[rt] += 1
                severity = "untouched"
            blind_items.append(
                {
                    "mr_id": r.get("mr_id"),
                    "relation_type": rt,
                    "type_category": r.get("type_category"),
                    "severity": severity,
                    "evidence_touch_hits": r.get("evidence_touch_hits") or [],
                    "reason": r.get("reason") or "no strict coverage evidence",
                }
            )
    return {
        "miss_at_uncov": sum(1 for r in mr_coverage if not _touched(r) and not _covered(r)),
        "touched_not_covered": sum(1 for r in mr_coverage if _touched(r) and not _covered(r)),
        "untouched_by_type": [
            {"relation_type": rt, "blind_count": c} for rt, c in untouched_counter.most_common(15)
        ],
        "weak_oracle_by_type": [
            {"relation_type": rt, "blind_count": c} for rt, c in weak_counter.most_common(15)
        ],
        "top_blind_mr_types": [
            {"relation_type": rt, "blind_count": c} for rt, c in blind_counter.most_common(15)
        ],
        "blind_items": blind_items[:50],
        "category": meta.category,
        "library": meta.library,
    }

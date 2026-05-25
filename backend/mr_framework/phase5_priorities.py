"""Phase 5: priorities and improvement suggestions."""

from __future__ import annotations

from typing import Any

from .models import SampleMeta


def build_test_priorities(
    meta: SampleMeta,
    mr_coverage: list[dict[str, Any]],
    *,
    issue_pressure: int = 0,
) -> list[dict[str, Any]]:
    items = []
    for r in mr_coverage:
        touched = bool(r.get("touched"))
        covered = bool(r.get("covered"))
        if covered:
            continue
        reason = "touched_not_covered" if touched else "miss_at_uncov"
        score = (0.7 if touched else 1.0) + min(issue_pressure, 20) * 0.03
        items.append(
            {
                "library": meta.library,
                "category": meta.category,
                "component_name": meta.component_name,
                "relation_type": r.get("relation_type"),
                "type_category": r.get("type_category"),
                "reason": reason,
                "priority_score": round(score, 4),
            }
        )
    items.sort(key=lambda x: -x["priority_score"])
    return items[:25]


def build_improvement_suggestions(
    meta: SampleMeta,
    mr_coverage: list[dict[str, Any]],
    completeness: dict[str, Any],
) -> list[dict[str, Any]]:
    suggestions = []
    cat_rates = (completeness.get("by_type_category") or {}).items()
    weak_cats = sorted(cat_rates, key=lambda x: x[1].get("coverage_rate", 0))[:2]
    for cat, stats in weak_cats:
        suggestions.append(
            {
                "kind": "category_gap",
                "message": (
                    f"Category '{cat}' has low strict coverage "
                    f"({stats.get('coverage_rate', 0):.1%}) for {meta.component_name}; "
                    f"add tests targeting typical {meta.category} MRs (see taxonomy)."
                ),
            }
        )
    for r in mr_coverage:
        if r.get("covered"):
            continue
        suggestions.append(
            {
                "kind": "mr_gap",
                "relation_type": r.get("relation_type"),
                "message": (
                    f"Add test(s) for MR '{r.get('relation_type')}': "
                    f"{(r.get('reason') or 'no alignment evidence')[:200]}"
                ),
            }
        )
        if len(suggestions) >= 12:
            break
    return suggestions


def insufficient_attention_evidence(
    completeness: dict[str, Any],
    blind: dict[str, Any],
    *,
    issue_pressure: int,
) -> dict[str, Any]:
    return {
        "touch_rate": completeness.get("touch_rate"),
        "coverage_rate": completeness.get("coverage_rate"),
        "miss_at_uncov": blind.get("miss_at_uncov"),
        "open_bug_pressure": issue_pressure,
        "summary": (
            "Tests show gaps in metamorphic relation space; "
            "strict coverage below full indicates insufficient behavioral-relation testing."
        ),
    }

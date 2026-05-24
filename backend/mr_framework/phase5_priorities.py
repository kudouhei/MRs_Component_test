"""Phase 5 — Evidence and test supplementation priorities."""

from __future__ import annotations

from typing import Any

from .models import SampleMeta, TestPriority


def build_test_priorities(
    meta: SampleMeta,
    mr_coverage: list[dict[str, Any]],
    *,
    issue_pressure: int = 0,
) -> list[TestPriority]:
    priorities: list[TestPriority] = []
    for row in mr_coverage:
        touched = bool(
            row.get("evidence_touch")
            or row.get("hybrid_touched")
            or row.get("touched")
        )
        covered = bool(row.get("evidence_covered") or row.get("covered"))
        if covered:
            continue
        if touched and not covered:
            reason = "touched_but_not_strictly_covered"
            base = 0.7
        else:
            reason = "miss_at_uncov"
            base = 1.0
        score = base + min(issue_pressure, 20) * 0.03
        priorities.append(
            TestPriority(
                library=meta.library,
                component_name=meta.component_name,
                category=meta.category,
                relation_type=str(row.get("relation_type") or "unknown"),
                type_category=str(row.get("type_category") or "unknown"),
                reason=reason,
                priority_score=round(score, 4),
            )
        )
    priorities.sort(key=lambda p: -p.priority_score)
    return priorities[:20]


def insufficient_attention_evidence(
    completeness: dict[str, Any],
    blind_spots: dict[str, Any],
    *,
    issue_pressure: int,
) -> dict[str, Any]:
    return {
        "touch_rate": completeness.get("touch_rate"),
        "coverage_rate": completeness.get("coverage_rate"),
        "miss_at_uncov": blind_spots.get("miss_at_uncov"),
        "touched_not_covered": blind_spots.get("touched_not_covered"),
        "open_bug_pressure": issue_pressure,
        "interpretation": (
            "Low strict coverage with blind MR types indicates insufficient test "
            "attention to behavioral relations; optional alignment with open bug pressure."
        ),
    }

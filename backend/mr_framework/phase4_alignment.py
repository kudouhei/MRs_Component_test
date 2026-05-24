"""Phase 4 — External anchor: open issues alignment (RQ3)."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from .models import AlignmentReport, SampleMeta, utc_now_iso
from .samples import PROJECT_ROOT, component_name_variants

OPEN_ISSUES_DIR = PROJECT_ROOT / "analysis" / "open_issues"

ISSUE_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "keyboard_interaction": ["keyboard", "keydown", "arrow", "tab", "focus"],
    "focus_management": ["focus", "blur", "tabindex"],
    "aria_mapping": ["aria", "accessibility", "a11y", "screen reader"],
    "null_handling": ["null", "undefined", "empty", "crash"],
    "state_synchronization": ["controlled", "state", "sync", "stale"],
    "two_way_binding": ["binding", "value", "onchange"],
    "pagination_consistency": ["pagination", "page"],
    "responsive_sizing": ["responsive", "resize", "overflow"],
    "data_validation": ["validation", "invalid", "error"],
}


def load_issue_pressure() -> dict[tuple[str, str], int]:
    path = OPEN_ISSUES_DIR / "open_issue_pressure_by_component.json"
    if not path.exists():
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {
        (r["library"], r["component"]): int(r.get("open_bug_count") or 0)
        for r in rows
        if r.get("library") and r.get("component")
    }


def issue_pressure_for_sample(
    meta: SampleMeta,
    pressure_map: dict[tuple[str, str], int] | None = None,
) -> int:
    pressure_map = pressure_map or load_issue_pressure()
    return max(
        (pressure_map.get((meta.library, v), 0) for v in component_name_variants(meta.component_name)),
        default=0,
    )


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return round(num / (den_x * den_y), 4)


def run_exp1(sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = [
        (float(r.get("issue_pressure") or 0), float((r.get("completeness") or {}).get("touch_rate") or 0), r)
        for r in sample_rows
    ]
    pressures, touch_rates = [p for p, _, _ in pairs], [t for _, t, _ in pairs]
    subset = [
        {
            "sample_id": r["meta"]["sample_id"],
            "library": r["meta"]["library"],
            "component_name": r["meta"]["component_name"],
            "issue_pressure": p,
            "touch_rate": t,
            "coverage_rate": (r.get("completeness") or {}).get("coverage_rate"),
        }
        for p, t, r in pairs
        if p >= 3 and t < 0.35
    ]
    return {
        "n_samples": len(pairs),
        "pearson_pressure_vs_touch_rate": _pearson(pressures, touch_rates),
        "high_pressure_low_completeness_subset": sorted(subset, key=lambda x: (-x["issue_pressure"], x["touch_rate"]))[:25],
    }


def _issue_topics(title: str, labels: str) -> set[str]:
    blob = f"{title} {labels}".lower()
    return {rt for rt, kws in ISSUE_TOPIC_KEYWORDS.items() if any(kw in blob for kw in kws)}


def run_exp2(sample_rows: list[dict[str, Any]], issues_path: Path | None = None) -> dict[str, Any]:
    path = issues_path or (OPEN_ISSUES_DIR / "open_issues_five_repos.json")
    if not path.exists():
        return {"error": "open_issues_five_repos.json missing"}
    issues = json.loads(path.read_text(encoding="utf-8"))
    blind_by_comp: dict[tuple[str, str], Counter[str]] = {}
    for r in sample_rows:
        meta = r["meta"]
        c: Counter[str] = Counter()
        for b in (r.get("blind_spots") or {}).get("top_blind_mr_types") or []:
            c[str(b.get("relation_type") or "")] += int(b.get("blind_count") or 0)
        if c:
            blind_by_comp[(meta["library"], meta["component_name"])] = c
    overlap_rows: list[dict[str, Any]] = []
    topic_hits: Counter[str] = Counter()
    for issue in issues:
        comp, lib = issue.get("matched_component"), issue.get("library")
        if not comp or not lib:
            continue
        topics = _issue_topics(issue.get("title") or "", issue.get("labels") or "")
        if not topics:
            continue
        blind = None
        for (bl, bc), counter in blind_by_comp.items():
            if bl == lib and (comp.lower() in bc.lower() or bc.lower() in comp.lower()):
                blind = counter
                break
        if not blind:
            continue
        for topic in topics:
            if blind.get(topic, 0) > 0:
                topic_hits[topic] += 1
                overlap_rows.append(
                    {
                        "library": lib,
                        "component": comp,
                        "issue_number": issue.get("number"),
                        "mr_type": topic,
                        "blind_count": blind.get(topic, 0),
                    }
                )
    return {
        "topic_mr_overlap_rows": len(overlap_rows),
        "top_topic_mr_overlaps": [{"mr_type": rt, "co_occurrence_count": n} for rt, n in topic_hits.most_common(20)],
        "examples": overlap_rows[:30],
    }


def build_alignment_report(
    sample_rows: list[dict[str, Any]],
    *,
    version_snapshot: str | None = None,
) -> AlignmentReport:
    summary_path = OPEN_ISSUES_DIR / "open_issues_summary.json"
    v = version_snapshot
    if not v and summary_path.exists():
        s = json.loads(summary_path.read_text(encoding="utf-8"))
        v = f"open_issues_corpus_{s.get('total_valid_issues', '?')}_issues"
    v = v or utc_now_iso()
    exp1, exp2 = run_exp1(sample_rows), run_exp2(sample_rows)
    return AlignmentReport(
        version_snapshot=v,
        exp1=exp1,
        exp2=exp2,
        val_summary=(
            f"Cross-sectional alignment (V={v}): "
            f"Exp1 r={exp1.get('pearson_pressure_vs_touch_rate')}; "
            f"Exp2 overlaps={exp2.get('top_topic_mr_overlaps', [])[:3]}. "
            "Co-occurrence only, not prediction."
        ),
    )

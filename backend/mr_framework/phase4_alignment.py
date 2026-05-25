"""Phase 4: open issues external anchor (RQ3 alignment)."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from .models import AlignmentReport, SampleMeta, utc_now_iso
from .samples import PROJECT_ROOT, component_name_variants

OPEN_ISSUES_DIR = PROJECT_ROOT / "analysis" / "open_issues"
TOPIC_KW = {
    "keyboard_interaction": ["keyboard", "keydown", "keyup", "arrow", "enter", "escape", "tab"],
    "focus_management": ["focus", "blur", "activeelement", "focus trap"],
    "null_handling": ["null", "undefined", "empty", "crash", "cannot read", "blank"],
    "state_synchronization": ["state", "controlled", "uncontrolled", "sync", "value"],
    "aria_mapping": ["aria", "a11y", "accessibility", "screen reader", "role"],
    "interaction_feedback": ["click", "hover", "press", "disabled", "readonly"],
    "pagination_consistency": ["pagination", "page", "page size", "next page", "prev"],
    "data_validation": ["validate", "validation", "invalid", "required", "error"],
    "placement_consistency": ["placement", "position", "popper", "popover", "tooltip"],
    "responsive_sizing": ["responsive", "breakpoint", "resize", "width", "height"],
}


def load_issue_pressure() -> dict[tuple[str, str], int]:
    p = OPEN_ISSUES_DIR / "open_issue_pressure_by_component.json"
    if not p.exists():
        return {}
    return {
        (r["library"], r["component"]): int(r.get("open_bug_count") or 0)
        for r in json.loads(p.read_text(encoding="utf-8"))
        if r.get("library") and r.get("component")
    }


def issue_pressure_for_sample(meta: SampleMeta) -> int:
    m = load_issue_pressure()
    return max((m.get((meta.library, v), 0) for v in component_name_variants(meta.component_name)), default=0)


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return round(num / (dx * dy), 4) if dx and dy else None


def run_exp1(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ps = [float(r.get("issue_pressure") or 0) for r in rows]
    trs = [float((r.get("completeness") or {}).get("coverage_rate") or 0) for r in rows]
    gaps = [float((r.get("completeness") or {}).get("strict_gap_rate") or 0) for r in rows]
    return {
        "n": len(rows),
        "pearson_pressure_vs_coverage_rate": _pearson(ps, trs),
        "pearson_pressure_vs_strict_gap_rate": _pearson(ps, gaps),
        "pressure_bins": _pressure_bins(rows),
        "high_pressure_low_coverage": [
            {
                "sample_id": r["meta"]["sample_id"],
                "library": r["meta"]["library"],
                "category": r["meta"]["category"],
                "component_name": r["meta"]["component_name"],
                "issue_pressure": p,
                "coverage_rate": (r.get("completeness") or {}).get("coverage_rate"),
                "strict_gap_rate": (r.get("completeness") or {}).get("strict_gap_rate"),
            }
            for r, p, t in zip(rows, ps, trs)
            if p >= 3 and t < 0.3
        ][:20],
    }


def run_exp2(rows: list[dict[str, Any]]) -> dict[str, Any]:
    path = OPEN_ISSUES_DIR / "open_issues_five_repos.json"
    if not path.exists():
        return {"error": "missing open_issues corpus"}
    issues = json.loads(path.read_text(encoding="utf-8"))
    hits: Counter[str] = Counter()
    topic_total: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = {}
    for iss in issues:
        comp, lib = iss.get("matched_component"), iss.get("library")
        if not comp:
            continue
        blob = f"{iss.get('title','')} {iss.get('labels','')} {iss.get('body','')}".lower()
        topics = {t for t, kws in TOPIC_KW.items() if any(k in blob for k in kws)}
        for t in topics:
            topic_total[t] += 1
        for r in rows:
            m = r["meta"]
            if m["library"] != lib:
                continue
            if comp.lower() not in m["component_name"].lower() and m["component_name"].lower() not in comp.lower():
                continue
            blind = {b["relation_type"] for b in (r.get("blind_spots") or {}).get("top_blind_mr_types") or []}
            for t in topics & blind:
                hits[t] += 1
                examples.setdefault(t, [])
                if len(examples[t]) < 5:
                    examples[t].append(
                        {
                            "sample_id": m["sample_id"],
                            "issue": iss.get("html_url") or iss.get("url") or iss.get("number"),
                            "title": str(iss.get("title") or "")[:180],
                        }
                    )
    return {
        "topic_counts_in_issues": [{"mr_type": k, "count": v} for k, v in topic_total.most_common(20)],
        "top_topic_blind_overlaps": [
            {
                "mr_type": k,
                "overlap_count": v,
                "issue_topic_count": topic_total.get(k, 0),
                "overlap_ratio": round(v / topic_total[k], 6) if topic_total.get(k) else 0.0,
                "examples": examples.get(k, []),
            }
            for k, v in hits.most_common(15)
        ],
    }


def _pressure_bins(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bins = [
        ("none", lambda p: p == 0),
        ("low", lambda p: 1 <= p <= 2),
        ("medium", lambda p: 3 <= p <= 9),
        ("high", lambda p: p >= 10),
    ]
    out = []
    for name, pred in bins:
        bucket = [r for r in rows if pred(int(r.get("issue_pressure") or 0))]
        if not bucket:
            out.append({"bin": name, "n": 0})
            continue
        cov = [float((r.get("completeness") or {}).get("coverage_rate") or 0) for r in bucket]
        gap = [float((r.get("completeness") or {}).get("strict_gap_rate") or 0) for r in bucket]
        out.append(
            {
                "bin": name,
                "n": len(bucket),
                "mean_coverage_rate": round(sum(cov) / len(cov), 6),
                "mean_strict_gap_rate": round(sum(gap) / len(gap), 6),
                "zero_coverage_count": sum(1 for x in cov if x == 0),
            }
        )
    return out


def build_alignment_report(rows: list[dict[str, Any]], version_snapshot: str | None = None) -> AlignmentReport:
    v = version_snapshot or utc_now_iso()
    e1, e2 = run_exp1(rows), run_exp2(rows)
    return AlignmentReport(
        version_snapshot=v,
        exp1=e1,
        exp2=e2,
        val_summary=(
            f"Cross-sectional alignment at V={v}; "
            f"r(pressure,coverage)={e1.get('pearson_pressure_vs_coverage_rate')}; "
            "co-occurrence only, not causal prediction."
        ),
    )

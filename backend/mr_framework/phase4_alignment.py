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
    "keyboard_interaction": ["keyboard", "keydown", "focus", "tab"],
    "null_handling": ["null", "undefined", "empty", "crash"],
    "state_synchronization": ["state", "controlled", "sync"],
    "aria_mapping": ["aria", "a11y", "accessibility"],
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
    return {
        "n": len(rows),
        "pearson_pressure_vs_coverage_rate": _pearson(ps, trs),
        "high_pressure_low_coverage": [
            {
                "sample_id": r["meta"]["sample_id"],
                "issue_pressure": p,
                "coverage_rate": (r.get("completeness") or {}).get("coverage_rate"),
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
    for iss in issues:
        comp, lib = iss.get("matched_component"), iss.get("library")
        if not comp:
            continue
        blob = f"{iss.get('title','')} {iss.get('labels','')}".lower()
        topics = {t for t, kws in TOPIC_KW.items() if any(k in blob for k in kws)}
        for r in rows:
            m = r["meta"]
            if m["library"] != lib:
                continue
            if comp.lower() not in m["component_name"].lower() and m["component_name"].lower() not in comp.lower():
                continue
            blind = {b["relation_type"] for b in (r.get("blind_spots") or {}).get("top_blind_mr_types") or []}
            for t in topics & blind:
                hits[t] += 1
    return {"top_topic_blind_overlaps": [{"mr_type": k, "count": v} for k, v in hits.most_common(15)]}


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

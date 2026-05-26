"""Phase 4: open issues external anchor (RQ3 alignment)."""

from __future__ import annotations

import json
import math
import random
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


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _rank_avg(xs: list[float]) -> list[float]:
    indexed = sorted(enumerate(xs), key=lambda x: x[1])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        r = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = r
        i = j + 1
    return ranks


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    return _pearson(_rank_avg(xs), _rank_avg(ys))


def _cliffs_delta(a: list[float], b: list[float]) -> float | None:
    if not a or not b:
        return None
    gt = 0
    lt = 0
    for x in a:
        for y in b:
            if x > y:
                gt += 1
            elif x < y:
                lt += 1
    n = len(a) * len(b)
    return round((gt - lt) / n, 6) if n else None


def _permutation_pvalue_mean_diff(
    values: list[float], labels: list[bool], *, n_iter: int = 20000, seed: int = 42
) -> float | None:
    n = len(values)
    n_true = sum(1 for x in labels if x)
    if n < 4 or n_true == 0 or n_true == n:
        return None
    obs_true = [v for v, t in zip(values, labels) if t]
    obs_false = [v for v, t in zip(values, labels) if not t]
    obs = _mean(obs_true) - _mean(obs_false)

    rng = random.Random(seed)
    idx = list(range(n))
    exceed = 0
    for _ in range(n_iter):
        true_idx = set(rng.sample(idx, n_true))
        grp_true = [values[i] for i in true_idx]
        grp_false = [values[i] for i in idx if i not in true_idx]
        diff = _mean(grp_true) - _mean(grp_false)
        if abs(diff) >= abs(obs):
            exceed += 1
    p = (exceed + 1) / (n_iter + 1)
    return round(p, 6)


def _bootstrap_ci_mean_diff(
    a: list[float], b: list[float], *, n_iter: int = 3000, seed: int = 7
) -> tuple[float, float] | None:
    if not a or not b:
        return None
    rng = random.Random(seed)
    diffs = []
    for _ in range(n_iter):
        sa = [a[rng.randrange(len(a))] for _ in range(len(a))]
        sb = [b[rng.randrange(len(b))] for _ in range(len(b))]
        diffs.append(_mean(sa) - _mean(sb))
    diffs.sort()
    lo = diffs[int(0.025 * (len(diffs) - 1))]
    hi = diffs[int(0.975 * (len(diffs) - 1))]
    return (round(lo, 6), round(hi, 6))


def _logcomb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def _hypergeom_right_tail(n_total: int, n_success: int, n_draw: int, x_obs: int) -> float:
    if n_total <= 0:
        return 1.0
    max_x = min(n_success, n_draw)
    min_x = max(0, n_draw - (n_total - n_success))
    if x_obs <= min_x:
        return 1.0
    denom = _logcomb(n_total, n_draw)
    logs = []
    for x in range(x_obs, max_x + 1):
        logp = _logcomb(n_success, x) + _logcomb(n_total - n_success, n_draw - x) - denom
        logs.append(logp)
    if not logs:
        return 1.0
    m = max(logs)
    s = sum(math.exp(v - m) for v in logs)
    return float(min(1.0, math.exp(m) * s))


def _fdr_bh(rows: list[dict[str, Any]], p_key: str = "p_value") -> None:
    ps = [(i, float(r.get(p_key) or 1.0)) for i, r in enumerate(rows)]
    ps.sort(key=lambda x: x[1])
    m = len(ps)
    qvals = [1.0] * m
    prev = 1.0
    for rank in range(m, 0, -1):
        i, p = ps[rank - 1]
        q = min(prev, p * m / rank)
        prev = q
        qvals[rank - 1] = q
    for (ranked_idx, _), q in zip(ps, qvals):
        rows[ranked_idx]["q_value"] = round(float(q), 6)


def _high_pressure_gap_test(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ps = [float(r.get("issue_pressure") or 0) for r in rows]
    gaps = [float((r.get("completeness") or {}).get("strict_gap_rate") or 0) for r in rows]
    covs = [float((r.get("completeness") or {}).get("coverage_rate") or 0) for r in rows]
    labels = [p >= 10 for p in ps]
    high_gap = [g for g, h in zip(gaps, labels) if h]
    rest_gap = [g for g, h in zip(gaps, labels) if not h]
    high_cov = [c for c, h in zip(covs, labels) if h]
    rest_cov = [c for c, h in zip(covs, labels) if not h]
    ci = _bootstrap_ci_mean_diff(high_gap, rest_gap)
    return {
        "high_threshold": 10,
        "n_high": len(high_gap),
        "n_other": len(rest_gap),
        "mean_strict_gap_high": round(_mean(high_gap), 6),
        "mean_strict_gap_other": round(_mean(rest_gap), 6),
        "strict_gap_diff_high_minus_other": round(_mean(high_gap) - _mean(rest_gap), 6),
        "strict_gap_diff_bootstrap95ci": list(ci) if ci else None,
        "strict_gap_diff_permutation_pvalue": _permutation_pvalue_mean_diff(gaps, labels),
        "strict_gap_cliffs_delta": _cliffs_delta(high_gap, rest_gap),
        "mean_coverage_high": round(_mean(high_cov), 6),
        "mean_coverage_other": round(_mean(rest_cov), 6),
        "coverage_diff_high_minus_other": round(_mean(high_cov) - _mean(rest_cov), 6),
    }


def run_exp1(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ps = [float(r.get("issue_pressure") or 0) for r in rows]
    trs = [float((r.get("completeness") or {}).get("coverage_rate") or 0) for r in rows]
    gaps = [float((r.get("completeness") or {}).get("strict_gap_rate") or 0) for r in rows]
    return {
        "n": len(rows),
        "pearson_pressure_vs_coverage_rate": _pearson(ps, trs),
        "pearson_pressure_vs_strict_gap_rate": _pearson(ps, gaps),
        "spearman_pressure_vs_coverage_rate": _spearman(ps, trs),
        "spearman_pressure_vs_strict_gap_rate": _spearman(ps, gaps),
        "pressure_bins": _pressure_bins(rows),
        "high_pressure_vs_others_strict_gap_test": _high_pressure_gap_test(rows),
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
    matched_pairs: list[dict[str, Any]] = []

    sample_blind_types = {
        r["meta"]["sample_id"]: {b["relation_type"] for b in (r.get("blind_spots") or {}).get("top_blind_mr_types") or []}
        for r in rows
    }

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
            sample_id = m["sample_id"]
            blind = sample_blind_types.get(sample_id, set())
            matched_pairs.append(
                {
                    "sample_id": sample_id,
                    "library": lib,
                    "issue": iss.get("html_url") or iss.get("url") or iss.get("number"),
                    "title": str(iss.get("title") or "")[:180],
                    "topics": topics,
                    "blind_types": blind,
                }
            )
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

    significance_rows: list[dict[str, Any]] = []
    n_pairs = len(matched_pairs)
    for t in TOPIC_KW:
        if n_pairs == 0:
            break
        a = sum(1 for p in matched_pairs if t in p["topics"] and t in p["blind_types"])
        b = sum(1 for p in matched_pairs if t in p["topics"] and t not in p["blind_types"])
        c = sum(1 for p in matched_pairs if t not in p["topics"] and t in p["blind_types"])
        d = n_pairs - a - b - c
        n_topic = a + b
        n_blind = a + c
        if n_topic == 0:
            continue
        expected = (n_topic * n_blind / n_pairs) if n_pairs else 0.0
        p_val = _hypergeom_right_tail(n_pairs, n_blind, n_topic, a)
        odds_ratio = ((a + 0.5) * (d + 0.5)) / ((b + 0.5) * (c + 0.5))
        significance_rows.append(
            {
                "mr_type": t,
                "n_pairs": n_pairs,
                "topic_count": n_topic,
                "blind_count": n_blind,
                "overlap_count": a,
                "expected_overlap_under_null": round(expected, 6),
                "enrichment_ratio": round(a / expected, 6) if expected > 0 else None,
                "odds_ratio": round(odds_ratio, 6),
                "p_value": round(p_val, 6),
                "examples": examples.get(t, []),
            }
        )
    _fdr_bh(significance_rows, p_key="p_value")
    significance_rows.sort(key=lambda x: (x.get("q_value", 1.0), x.get("p_value", 1.0), -x.get("overlap_count", 0)))

    return {
        "n_matched_issue_component_pairs": n_pairs,
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
        "topic_blind_significance": significance_rows,
        "significant_topics_fdr_005": [
            row["mr_type"] for row in significance_rows if float(row.get("q_value") or 1.0) < 0.05
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

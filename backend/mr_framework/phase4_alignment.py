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
HIGH_PRESSURE_THRESHOLD = 9
PRESSURE_BIN_DEFS = {
    "none": "0",
    "low": "1-2",
    "medium": "3-8",
    "high": f">={HIGH_PRESSURE_THRESHOLD}",
}
RQ4_ENSEMBLE_MODEL_DIRS = ("deepseek", "gemini-2.5-flash", "gpt-5-mini")
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
    ps = [(i, float(1.0 if r.get(p_key) is None else r[p_key])) for i, r in enumerate(rows)]
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


def _load_open_issues_corpus() -> list[dict[str, Any]] | None:
    for name in ("open_issues_four_repos.json", "open_issues_five_repos.json"):
        path = OPEN_ISSUES_DIR / name
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def _completeness_rates(row: dict[str, Any]) -> tuple[float, float, float]:
    comp = row.get("completeness") or {}
    return (
        float(comp.get("coverage_rate") or 0),
        float(comp.get("strict_gap_rate") or 0),
        float(comp.get("touch_rate") or 0),
    )


def load_model_report_index(model_dir_name: str) -> dict[str, dict[str, Any]]:
    reports_dir = PROJECT_ROOT / "output" / "model_runs" / model_dir_name / "reports"
    if not reports_dir.is_dir():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for path in reports_dir.glob("*.json"):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            sid = (row.get("meta") or {}).get("sample_id")
            if sid:
                out[sid] = row
        except (json.JSONDecodeError, OSError):
            continue
    return out


def build_ensemble_exp1_rows(
    primary_rows: list[dict[str, Any]],
    *,
    model_dirs: tuple[str, ...] = RQ4_ENSEMBLE_MODEL_DIRS,
) -> list[dict[str, Any]]:
    """Per-component mean of coverage/touch/gap across LLM runs (macro input for RQ4 Exp1)."""
    indices = {m: load_model_report_index(m) for m in model_dirs}
    out: list[dict[str, Any]] = []
    for row in primary_rows:
        sid = (row.get("meta") or {}).get("sample_id")
        if not sid:
            continue
        covers: list[float] = []
        gaps: list[float] = []
        touches: list[float] = []
        for model in model_dirs:
            other = indices[model].get(sid)
            if not other:
                break
            c, g, t = _completeness_rates(other)
            covers.append(c)
            gaps.append(g)
            touches.append(t)
        if len(covers) != len(model_dirs):
            continue
        merged = dict(row)
        merged["completeness"] = {
            **(row.get("completeness") or {}),
            "coverage_rate": round(sum(covers) / len(covers), 6),
            "strict_gap_rate": round(sum(gaps) / len(gaps), 6),
            "touch_rate": round(sum(touches) / len(touches), 6),
        }
        out.append(merged)
    return out


def _high_pressure_gap_test(rows: list[dict[str, Any]], *, threshold: int = HIGH_PRESSURE_THRESHOLD) -> dict[str, Any]:
    ps = [float(r.get("issue_pressure") or 0) for r in rows]
    gaps = [float((r.get("completeness") or {}).get("strict_gap_rate") or 0) for r in rows]
    covs = [float((r.get("completeness") or {}).get("coverage_rate") or 0) for r in rows]
    labels = [p >= threshold for p in ps]
    high_gap = [g for g, h in zip(gaps, labels) if h]
    rest_gap = [g for g, h in zip(gaps, labels) if not h]
    high_cov = [c for c, h in zip(covs, labels) if h]
    rest_cov = [c for c, h in zip(covs, labels) if not h]
    ci = _bootstrap_ci_mean_diff(high_gap, rest_gap)
    return {
        "high_threshold": threshold,
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


def run_exp1(
    rows: list[dict[str, Any]],
    *,
    coverage_metric: str = "single_model",
    ensemble_models: list[str] | None = None,
) -> dict[str, Any]:
    ps = [float(r.get("issue_pressure") or 0) for r in rows]
    trs = [float((r.get("completeness") or {}).get("coverage_rate") or 0) for r in rows]
    gaps = [float((r.get("completeness") or {}).get("strict_gap_rate") or 0) for r in rows]
    touches = [float((r.get("completeness") or {}).get("touch_rate") or 0) for r in rows]
    return {
        "n": len(rows),
        "coverage_metric": coverage_metric,
        "ensemble_models": ensemble_models,
        "pressure_bin_definitions": dict(PRESSURE_BIN_DEFS),
        "mean_coverage_rate": round(_mean(trs), 6),
        "mean_touch_rate": round(_mean(touches), 6),
        "mean_strict_gap_rate": round(_mean(gaps), 6),
        "pearson_pressure_vs_coverage_rate": _pearson(ps, trs),
        "pearson_pressure_vs_touch_rate": _pearson(ps, touches),
        "pearson_pressure_vs_strict_gap_rate": _pearson(ps, gaps),
        "spearman_pressure_vs_coverage_rate": _spearman(ps, trs),
        "spearman_pressure_vs_touch_rate": _spearman(ps, touches),
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


def _by_relation_type_map(row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = (row.get("completeness") or {}).get("by_relation_type") or []
    if isinstance(raw, dict):
        return raw
    return {str(k): v for k, v in raw}


def _issue_topics(iss: dict[str, Any]) -> set[str]:
    blob = f"{iss.get('title','')} {iss.get('labels','')} {iss.get('body','')}".lower()
    return {t for t, kws in TOPIC_KW.items() if any(k in blob for k in kws)}


def _match_issue_to_sample_id(rows: list[dict[str, Any]], iss: dict[str, Any]) -> str | None:
    comp, lib = iss.get("matched_component"), iss.get("library")
    if not comp or not lib:
        return None
    comp_l = str(comp).lower()
    for r in rows:
        m = r["meta"]
        if m["library"] != lib:
            continue
        name_l = m["component_name"].lower()
        if comp_l in name_l or name_l in comp_l:
            return m["sample_id"]
    return None


def build_component_issue_topics(rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {r["meta"]["sample_id"]: set() for r in rows}
    for iss in issues:
        sid = _match_issue_to_sample_id(rows, iss)
        if not sid:
            continue
        out.setdefault(sid, set()).update(_issue_topics(iss))
    return out


def build_component_relation_types(
    primary_rows: list[dict[str, Any]],
    *,
    model_dirs: tuple[str, ...] = RQ4_ENSEMBLE_MODEL_DIRS,
) -> dict[str, set[str]]:
    """Union of inferred relation_type labels per component across LLM runs."""
    indices = {m: load_model_report_index(m) for m in model_dirs}
    out: dict[str, set[str]] = {}
    for row in primary_rows:
        sid = (row.get("meta") or {}).get("sample_id")
        if not sid:
            continue
        types: set[str] = set()
        for model in model_dirs:
            other = indices[model].get(sid)
            if not other:
                continue
            for mr in other.get("mr_coverage") or []:
                rel = mr.get("relation_type")
                if rel:
                    types.add(str(rel))
        out[sid] = types
    return out


def _binomial_right_tail(n: int, k: int, p: float) -> float:
    if n <= 0 or k <= 0:
        return 1.0
    if p <= 0:
        return 0.0 if k > 0 else 1.0
    if p >= 1:
        return 1.0
    tail = 0.0
    for x in range(k, n + 1):
        tail += math.comb(n, x) * (p**x) * ((1 - p) ** (n - x))
    return float(min(1.0, tail))


def _build_issue_component_pairs(rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for iss in issues:
        comp, lib = iss.get("matched_component"), iss.get("library")
        if not comp:
            continue
        topics = _issue_topics(iss)
        if not topics:
            continue
        comp_l = str(comp).lower()
        for r in rows:
            m = r["meta"]
            if m["library"] != lib:
                continue
            name_l = m["component_name"].lower()
            if comp_l not in name_l and name_l not in comp_l:
                continue
            pairs.append(
                {
                    "sample_id": m["sample_id"],
                    "library": lib,
                    "component_name": m["component_name"],
                    "issue": iss.get("html_url") or iss.get("url") or iss.get("number"),
                    "title": str(iss.get("title") or "")[:180],
                    "topics": topics,
                }
            )
    return pairs


def run_exp2(
    rows: list[dict[str, Any]],
    *,
    mapping_metric: str = "ensemble_union",
    ensemble_models: list[str] | None = None,
) -> dict[str, Any]:
    """Bug themes (keyword-tagged) vs. whether they land on inferred MR relation_types."""
    issues = _load_open_issues_corpus()
    if not issues:
        return {"error": "missing open_issues corpus"}

    comp_types = build_component_relation_types(rows)
    pairs = _build_issue_component_pairs(rows, issues)
    n_components = len(rows)

    topic_issue_counts: Counter[str] = Counter()
    for iss in issues:
        for t in _issue_topics(iss):
            topic_issue_counts[t] += 1

    type_prevalence = {
        t: sum(1 for sid, types in comp_types.items() if t in types) / n_components
        for t in TOPIC_KW
    }

    mapping_rows: list[dict[str, Any]] = []
    miss_examples: dict[str, list[dict[str, Any]]] = {t: [] for t in TOPIC_KW}

    for rel_type in TOPIC_KW:
        tagged_pairs = [p for p in pairs if rel_type in p["topics"]]
        if not tagged_pairs:
            continue
        lands = 0
        for p in tagged_pairs:
            sid = p["sample_id"]
            if rel_type in (comp_types.get(sid) or set()):
                lands += 1
            elif len(miss_examples[rel_type]) < 5:
                miss_examples[rel_type].append(
                    {
                        "sample_id": sid,
                        "library": p["library"],
                        "component_name": p["component_name"],
                        "issue": p["issue"],
                        "title": p["title"],
                    }
                )

        n_tagged = len(tagged_pairs)
        map_rate = lands / n_tagged
        baseline = type_prevalence.get(rel_type) or 0.0
        p_val = _binomial_right_tail(n_tagged, lands, baseline) if baseline > 0 else None
        mapping_rows.append(
            {
                "relation_type": rel_type,
                "n_tagged_issue_component_pairs": n_tagged,
                "n_lands_on_mr_type": lands,
                "n_not_in_inferred_mrs": n_tagged - lands,
                "mapping_rate": round(map_rate, 6),
                "corpus_type_prevalence": round(baseline, 6),
                "enrichment_vs_prevalence": round(map_rate / baseline, 6) if baseline > 0 else None,
                "p_value": round(p_val, 6) if p_val is not None else None,
                "issue_topic_count_in_corpus": topic_issue_counts.get(rel_type, 0),
                "miss_examples": miss_examples.get(rel_type, []),
            }
        )

    _fdr_bh(mapping_rows, p_key="p_value")
    mapping_rows.sort(
        key=lambda x: (
            x.get("q_value", 1.0),
            x.get("p_value", 1.0) if x.get("p_value") is not None else 1.0,
            -float(x.get("mapping_rate") or 0),
        )
    )

    total_tagged = sum(r["n_tagged_issue_component_pairs"] for r in mapping_rows)
    total_lands = sum(r["n_lands_on_mr_type"] for r in mapping_rows)
    return {
        "mapping_metric": mapping_metric,
        "ensemble_models": ensemble_models,
        "analysis_unit": "issue_component_pair_with_keyword_topic",
        "n_components": n_components,
        "n_matched_pairs_with_topic": len(pairs),
        "overall_mapping_rate": round(total_lands / total_tagged, 6) if total_tagged else None,
        "topic_counts_in_issues": [
            {"relation_type": k, "count": v} for k, v in topic_issue_counts.most_common(20)
        ],
        "topic_to_mr_type_mapping": mapping_rows,
        "significant_topics_fdr_005": [
            row["relation_type"]
            for row in mapping_rows
            if float(1.0 if row.get("q_value") is None else row["q_value"]) < 0.05
        ],
    }


def _pressure_bins(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bins = [
        ("none", lambda p: p == 0),
        ("low", lambda p: 1 <= p <= 2),
        ("medium", lambda p: 3 <= p <= 8),
        ("high", lambda p: p >= HIGH_PRESSURE_THRESHOLD),
    ]
    out = []
    for name, pred in bins:
        bucket = [r for r in rows if pred(int(r.get("issue_pressure") or 0))]
        if not bucket:
            out.append({"bin": name, "n": 0})
            continue
        cov = [float((r.get("completeness") or {}).get("coverage_rate") or 0) for r in bucket]
        touch = [float((r.get("completeness") or {}).get("touch_rate") or 0) for r in bucket]
        gap = [float((r.get("completeness") or {}).get("strict_gap_rate") or 0) for r in bucket]
        out.append(
            {
                "bin": name,
                "n": len(bucket),
                "mean_coverage_rate": round(sum(cov) / len(cov), 6),
                "mean_touch_rate": round(sum(touch) / len(touch), 6),
                "mean_strict_gap_rate": round(sum(gap) / len(gap), 6),
                "zero_coverage_count": sum(1 for x in cov if x == 0),
            }
        )
    return out


def build_alignment_report(
    rows: list[dict[str, Any]],
    version_snapshot: str | None = None,
    *,
    exp1_rows: list[dict[str, Any]] | None = None,
    exp1_coverage_metric: str = "single_model",
    exp1_ensemble_models: list[str] | None = None,
    exp2_mapping_metric: str = "ensemble_union",
    exp2_ensemble_models: list[str] | None = None,
) -> AlignmentReport:
    v = version_snapshot or utc_now_iso()
    e1_input = exp1_rows if exp1_rows is not None else rows
    e1 = run_exp1(
        e1_input,
        coverage_metric=exp1_coverage_metric,
        ensemble_models=exp1_ensemble_models,
    )
    e2 = run_exp2(
        rows,
        mapping_metric=exp2_mapping_metric,
        ensemble_models=exp2_ensemble_models,
    )
    sig = e2.get("significant_topics_fdr_005") or []
    return AlignmentReport(
        version_snapshot=v,
        exp1=e1,
        exp2=e2,
        val_summary=(
            f"Cross-sectional alignment at V={v}; "
            f"Exp1={exp1_coverage_metric} r(pressure,cover)={e1.get('pearson_pressure_vs_coverage_rate')}; "
            f"Exp2={exp2_mapping_metric} map={e2.get('overall_mapping_rate')}; "
            f"FDR-significant={sig}; not causal prediction."
        ),
    )

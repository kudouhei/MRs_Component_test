"""Five-phase pipeline: (C,D)→M(C); (T,M)→O; metrics; issues; priorities."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .llm_client import DEFAULT_LLM_MODEL
from .models import SampleReport, utc_now_iso
from .phase1_inference import infer_mrs, mrs_to_coverage_skeleton
from .phase2_alignment import align_tests_to_mrs
from .phase3_completeness import compute_completeness, diagnose_blind_spots
from .phase4_alignment import build_alignment_report, issue_pressure_for_sample
from .phase5_priorities import (
    build_improvement_suggestions,
    build_test_priorities,
    insufficient_attention_evidence,
)
from .samples import PROJECT_ROOT, SampleMeta, iter_samples, read_sample_files
from .versioning import FRAMEWORK_VERSION, build_run_provenance, write_run_config

OUTPUT_ROOT = PROJECT_ROOT / "output"
REPORTS_DIR = OUTPUT_ROOT / "reports"
AGGREGATE_DIR = OUTPUT_ROOT / "aggregate"
RUN_CONFIG = OUTPUT_ROOT / "run_config.json"


def analyze_sample(
    meta: SampleMeta,
    *,
    model: str | None = None,
    version_snapshot: str | None = None,
) -> SampleReport:
    code, tests, description = read_sample_files(meta)
    inf = infer_mrs(
        code,
        description,
        meta,
        model=model,
    )
    mr_coverage = mrs_to_coverage_skeleton(inf.mrs)
    align_tests_to_mrs(
        inf.mrs,
        mr_coverage,
        tests=tests,
        code=code,
        meta=meta,
        llm_model=model,
    )
    completeness = compute_completeness(mr_coverage)
    blind = diagnose_blind_spots(mr_coverage, meta)
    pressure = issue_pressure_for_sample(meta)
    priorities = build_test_priorities(meta, mr_coverage, issue_pressure=pressure)
    suggestions = build_improvement_suggestions(meta, mr_coverage, completeness)
    evidence = insufficient_attention_evidence(completeness, blind, issue_pressure=pressure)

    provenance = build_run_provenance(
        mr_inference_mode=inf.mode,
        alignment_mode="hybrid",
        llm_model=inf.llm_model,
        llm_temperature=inf.llm_temperature,
        prompt_version=inf.prompt_version,
        taxonomy_version=inf.taxonomy_version,
        taxonomy_fingerprint=inf.taxonomy_fingerprint,
        llm_fallback_reason=inf.fallback_reason,
        uses_description=bool(description.strip()),
        category=meta.category,
    )

    return SampleReport(
        meta=meta,
        version_snapshot=version_snapshot or utc_now_iso(),
        metamorphic_relations=[m.to_dict() for m in inf.mrs],
        mr_coverage=mr_coverage,
        completeness=completeness,
        blind_spots=blind,
        test_priorities=priorities,
        improvement_suggestions=suggestions,
        issue_pressure=pressure,
        alignment_notes={"insufficient_attention": evidence},
        provenance=provenance,
        generated_at=utc_now_iso(),
    )


def save_report(report: SampleReport) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{report.meta.sample_id}.json"
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_batch(
    *,
    library: str | None = None,
    category: str | None = None,
    limit: int | None = None,
    sample_id: str | None = None,
    model: str | None = None,
    version_snapshot: str | None = None,
) -> dict[str, Any]:
    v = version_snapshot or utc_now_iso()
    cfg = build_run_provenance(
        version_snapshot=v,
        mr_inference_mode="llm",
        alignment_mode="hybrid",
        llm_model=model or DEFAULT_LLM_MODEL,
    )
    write_run_config(RUN_CONFIG, cfg)

    rows: list[dict[str, Any]] = []
    saved: list[str] = []
    for meta in iter_samples(library=library, category=category, limit=limit, sample_id=sample_id):
        report = analyze_sample(
            meta,
            model=model,
            version_snapshot=v,
        )
        rows.append(report.to_dict())
        saved.append(str(save_report(report)))

    alignment = build_alignment_report(rows, version_snapshot=v)
    agg = _aggregate(rows, cfg)
    _export_csv(rows)
    _export_priorities_csv(rows)
    AGGREGATE_DIR.mkdir(parents=True, exist_ok=True)
    (AGGREGATE_DIR / "batch_summary.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8")
    (AGGREGATE_DIR / "alignment_val.json").write_text(
        json.dumps(alignment.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {
        "framework_version": FRAMEWORK_VERSION,
        "n_samples": len(rows),
        "version_snapshot": v,
        "run_config": str(RUN_CONFIG),
        "reports_saved": len(saved),
        "aggregate": agg,
        "alignment": alignment.to_dict(),
    }


def _aggregate(rows: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, Any]:
    if not rows:
        return {"n_samples": 0}
    def mean(field: str) -> float:
        vals = [float((r.get("completeness") or {}).get(field) or 0) for r in rows]
        return round(sum(vals) / len(vals), 6)

    by_lib: dict[str, list[float]] = {}
    by_cat: dict[str, list[float]] = {}
    total_mrs = 0
    total_touched_mrs = 0
    total_covered_mrs = 0
    total_weak_oracle = 0
    total_untouched = 0
    for r in rows:
        m = r["meta"]
        c = r.get("completeness") or {}
        cr = float(c.get("coverage_rate") or 0)
        by_lib.setdefault(m["library"], []).append(cr)
        by_cat.setdefault(m["category"], []).append(cr)
        total_mrs += int(c.get("total_mrs") or 0)
        total_touched_mrs += int(c.get("touched_mrs") or 0)
        total_covered_mrs += int(c.get("covered_mrs") or 0)
        total_weak_oracle += int(c.get("touched_not_covered") or 0)
        total_untouched += int(c.get("miss_at_uncov") or 0)

    blind_global: dict[str, int] = {}
    weak_global: dict[str, int] = {}
    untouched_global: dict[str, int] = {}
    for r in rows:
        for b in (r.get("blind_spots") or {}).get("top_blind_mr_types") or []:
            rt = str(b.get("relation_type"))
            blind_global[rt] = blind_global.get(rt, 0) + int(b.get("blind_count") or 0)
        for b in (r.get("blind_spots") or {}).get("weak_oracle_by_type") or []:
            rt = str(b.get("relation_type"))
            weak_global[rt] = weak_global.get(rt, 0) + int(b.get("blind_count") or 0)
        for b in (r.get("blind_spots") or {}).get("untouched_by_type") or []:
            rt = str(b.get("relation_type"))
            untouched_global[rt] = untouched_global.get(rt, 0) + int(b.get("blind_count") or 0)

    return {
        "n_samples": len(rows),
        "provenance": cfg,
        "rq1": {
            "total_mrs": total_mrs,
            "total_touched_mrs": total_touched_mrs,
            "total_covered_mrs": total_covered_mrs,
            "total_weak_oracle": total_weak_oracle,
            "total_untouched": total_untouched,
            "mean_touch_rate": mean("touch_rate"),
            "mean_coverage_rate": mean("coverage_rate"),
            "mean_weighted_touch_rate": mean("weighted_touch_rate"),
            "mean_weighted_coverage_rate": mean("weighted_coverage_rate"),
            "mean_strict_gap_rate": mean("strict_gap_rate"),
            "coverage_distribution": _distribution(
                [float((r.get("completeness") or {}).get("coverage_rate") or 0) for r in rows]
            ),
            "touch_distribution": _distribution(
                [float((r.get("completeness") or {}).get("touch_rate") or 0) for r in rows]
            ),
            "zero_coverage_samples": sum(
                1 for r in rows if float((r.get("completeness") or {}).get("coverage_rate") or 0) == 0
            ),
            "full_coverage_samples": sum(
                1 for r in rows if float((r.get("completeness") or {}).get("coverage_rate") or 0) == 1
            ),
            "by_library": {k: round(sum(v) / len(v), 6) for k, v in by_lib.items()},
            "by_category": {k: round(sum(v) / len(v), 6) for k, v in by_cat.items()},
        },
        "rq2": {
            "top_blind_mr_types": sorted(
                [{"relation_type": k, "count": n} for k, n in blind_global.items()],
                key=lambda x: -x["count"],
            )[:20],
            "top_weak_oracle_types": sorted(
                [{"relation_type": k, "count": n} for k, n in weak_global.items()],
                key=lambda x: -x["count"],
            )[:20],
            "top_untouched_types": sorted(
                [{"relation_type": k, "count": n} for k, n in untouched_global.items()],
                key=lambda x: -x["count"],
            )[:20],
        },
        "top_test_priorities": _aggregate_priorities(rows),
    }


def _distribution(vals: list[float]) -> dict[str, float]:
    if not vals:
        return {"min": 0.0, "p25": 0.0, "median": 0.0, "p75": 0.0, "max": 0.0}
    xs = sorted(vals)
    return {
        "min": round(xs[0], 6),
        "p25": round(_percentile(xs, 25), 6),
        "median": round(_percentile(xs, 50), 6),
        "p75": round(_percentile(xs, 75), 6),
        "max": round(xs[-1], 6),
    }


def _percentile(xs: list[float], pct: float) -> float:
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * pct / 100
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def _export_csv(rows: list[dict[str, Any]]) -> None:
    AGGREGATE_DIR.mkdir(parents=True, exist_ok=True)
    path = AGGREGATE_DIR / "per_sample_metrics.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "sample_id", "library", "category", "component_name",
                "total_mrs", "touch_rate", "coverage_rate", "issue_pressure",
                "weighted_touch_rate", "weighted_coverage_rate", "strict_gap_rate",
                "mr_inference_mode", "alignment_mode",
            ],
        )
        w.writeheader()
        for r in rows:
            c = r.get("completeness") or {}
            p = r.get("provenance") or {}
            m = r["meta"]
            w.writerow({
                "sample_id": m["sample_id"],
                "library": m["library"],
                "category": m["category"],
                "component_name": m["component_name"],
                "total_mrs": c.get("total_mrs"),
                "touch_rate": c.get("touch_rate"),
                "coverage_rate": c.get("coverage_rate"),
                "issue_pressure": r.get("issue_pressure"),
                "weighted_touch_rate": c.get("weighted_touch_rate"),
                "weighted_coverage_rate": c.get("weighted_coverage_rate"),
                "strict_gap_rate": c.get("strict_gap_rate"),
                "mr_inference_mode": p.get("mr_inference_mode"),
                "alignment_mode": p.get("alignment_mode"),
            })


def _aggregate_priorities(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for r in rows:
        for item in r.get("test_priorities") or []:
            items.append({"sample_id": r["meta"]["sample_id"], **item})
    items.sort(key=lambda x: -float(x.get("priority_score") or 0))
    return items[:50]


def _export_priorities_csv(rows: list[dict[str, Any]]) -> None:
    AGGREGATE_DIR.mkdir(parents=True, exist_ok=True)
    path = AGGREGATE_DIR / "test_priorities.csv"
    fieldnames = [
        "sample_id",
        "library",
        "category",
        "component_name",
        "relation_type",
        "type_category",
        "reason",
        "test_transformation",
        "expected_oracle",
        "priority_score",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for item in _aggregate_priorities(rows):
            w.writerow({k: item.get(k) for k in fieldnames})

"""Five-phase pipeline: (C,D)→M(C); (T,M)→O; metrics; issues; priorities."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .llm_client import DEFAULT_LLM_MODEL
from .models import SampleReport, utc_now_iso
from .baseline_coverage import compute_statement_coverage_baseline
from .phase1_inference import infer_mrs, mrs_to_coverage_skeleton
from .phase2_alignment import align_tests_to_mrs
from .phase3_completeness import compute_completeness, diagnose_blind_spots
from .phase4_alignment import build_alignment_report, issue_pressure_for_sample
from .phase5_priorities import (
    build_improvement_suggestions,
    build_test_priorities,
    insufficient_attention_evidence,
)
from .batch_progress import BatchProgressReporter, collect_sample_metas
from .samples import (
    PROJECT_ROOT,
    SampleMeta,
    describe_shards,
    list_sample_metas,
    read_sample_files,
    shard_bounds,
)
from .versioning import FRAMEWORK_VERSION, build_run_provenance, write_run_config

OUTPUT_ROOT = PROJECT_ROOT / "output"
REPORTS_DIR = OUTPUT_ROOT / "reports"
AGGREGATE_DIR = OUTPUT_ROOT / "aggregate"
RUN_CONFIG = OUTPUT_ROOT / "run_config.json"


def _sanitize_model_name(model: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in model.strip()) or "unknown-model"


def model_tag(model: str | None) -> str:
    return _sanitize_model_name(model or DEFAULT_LLM_MODEL)


def output_root_for_model(model: str | None, *, separate_by_model: bool) -> Path:
    if not separate_by_model:
        return OUTPUT_ROOT
    return OUTPUT_ROOT / "model_runs" / model_tag(model)


def _paths(output_root: Path) -> dict[str, Path]:
    return {
        "output_root": output_root,
        "reports_dir": output_root / "reports",
        "aggregate_dir": output_root / "aggregate",
        "run_config": output_root / "run_config.json",
        "progress_json": output_root / "batch_progress.json",
        "progress_txt": output_root / "batch_progress.txt",
    }


def _report_filename(sample_id: str, model: str | None) -> str:
    return f"{sample_id}__{model_tag(model)}.json"


def _report_matches_model(path: Path, model: str | None) -> bool:
    return path.stem.endswith(f"__{model_tag(model)}")


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
    baselines = {
        "statement_coverage": compute_statement_coverage_baseline(code, tests),
    }
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
        baselines=baselines,
        issue_pressure=pressure,
        alignment_notes={"insufficient_attention": evidence},
        provenance=provenance,
        generated_at=utc_now_iso(),
    )


def save_report(
    report: SampleReport,
    *,
    reports_dir: Path = REPORTS_DIR,
    model: str | None = None,
) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / _report_filename(report.meta.sample_id, model)
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_saved_report_rows(
    *,
    reports_dir: Path = REPORTS_DIR,
    model: str | None = None,
) -> list[dict[str, Any]]:
    if not reports_dir.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(reports_dir.glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            if model is not None:
                is_tagged = _report_matches_model(path, model)
                prov_model = str((row.get("provenance") or {}).get("llm_model") or "")
                # Backward-compatible: accept legacy filenames when provenance model matches.
                if not is_tagged and prov_model != (model or ""):
                    continue
            rows.append(row)
        except (json.JSONDecodeError, OSError):
            continue
    return rows


def merge_aggregate_from_reports(
    *,
    version_snapshot: str | None = None,
    model: str | None = None,
    separate_by_model: bool = False,
) -> dict[str, Any]:
    """Rebuild aggregate CSV/JSON from all per-sample reports on disk."""
    out_root = output_root_for_model(model, separate_by_model=separate_by_model)
    paths = _paths(out_root)
    rows = load_saved_report_rows(reports_dir=paths["reports_dir"], model=model)
    v = version_snapshot or utc_now_iso()
    cfg: dict[str, Any] = {}
    if paths["run_config"].exists():
        try:
            cfg = json.loads(paths["run_config"].read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cfg = {}
    if not cfg:
        cfg = build_run_provenance(
            version_snapshot=v,
            mr_inference_mode="llm",
            alignment_mode="hybrid",
            llm_model=model or DEFAULT_LLM_MODEL,
        )
    cfg["merge_from_reports"] = True
    cfg["n_reports_on_disk"] = len(rows)

    alignment = build_alignment_report(rows, version_snapshot=v)
    agg = _aggregate(rows, cfg)
    tag = model_tag(model)
    _export_csv(rows, aggregate_dir=paths["aggregate_dir"], model=model)
    _export_priorities_csv(rows, aggregate_dir=paths["aggregate_dir"], model=model)
    paths["aggregate_dir"].mkdir(parents=True, exist_ok=True)
    (paths["aggregate_dir"] / "batch_summary.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8")
    (paths["aggregate_dir"] / f"batch_summary__{tag}.json").write_text(
        json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (paths["aggregate_dir"] / "alignment_val.json").write_text(
        json.dumps(alignment.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (paths["aggregate_dir"] / f"alignment_val__{tag}.json").write_text(
        json.dumps(alignment.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {
        "framework_version": FRAMEWORK_VERSION,
        "n_samples": len(rows),
        "version_snapshot": v,
        "run_config": str(paths["run_config"]),
        "output_root": str(paths["output_root"]),
        "aggregate": agg,
        "alignment": alignment.to_dict(),
        "merged_from_reports": True,
    }


def run_batch(
    *,
    library: str | None = None,
    category: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    shard_index: int | None = None,
    num_shards: int | None = None,
    sample_id: str | None = None,
    model: str | None = None,
    version_snapshot: str | None = None,
    show_progress: bool = True,
    skip_aggregate: bool = False,
    merge_reports_after: bool = False,
    separate_by_model: bool = False,
) -> dict[str, Any]:
    v = version_snapshot or utc_now_iso()
    out_root = output_root_for_model(model, separate_by_model=separate_by_model)
    paths = _paths(out_root)
    cfg = build_run_provenance(
        version_snapshot=v,
        mr_inference_mode="llm",
        alignment_mode="hybrid",
        llm_model=model or DEFAULT_LLM_MODEL,
    )
    cfg["output_root"] = str(paths["output_root"])
    cfg["separate_by_model"] = separate_by_model
    if shard_index is not None and num_shards is not None:
        cfg["shard_index"] = shard_index
        cfg["num_shards"] = num_shards
    write_run_config(paths["run_config"], cfg)

    corpus = list_sample_metas(library=library, category=category, sample_id=sample_id)
    global_total = len(corpus)
    global_offset = 0
    shard_label = ""
    if shard_index is not None and num_shards is not None and not sample_id:
        global_offset, end = shard_bounds(global_total, shard_index, num_shards)
        shard_label = f"[shard {shard_index}/{num_shards}]"

    metas = collect_sample_metas(
        library=library,
        category=category,
        limit=limit,
        offset=offset,
        shard_index=shard_index,
        num_shards=num_shards,
        sample_id=sample_id,
    )
    progress = BatchProgressReporter(
        total=len(metas),
        enabled=show_progress,
        json_path=paths["progress_json"],
        txt_path=paths["progress_txt"],
        global_total=global_total if shard_label else len(metas),
        global_offset=global_offset,
        shard_label=shard_label,
    )
    progress.start()

    rows: list[dict[str, Any]] = []
    saved: list[str] = []
    failed_samples: list[dict[str, str]] = []
    for index, meta in enumerate(metas, start=1):
        progress.begin_sample(
            index,
            meta.sample_id,
            meta.library,
            meta.category,
            meta.component_name,
        )
        try:
            report = analyze_sample(
                meta,
                model=model,
                version_snapshot=v,
            )
        except Exception as exc:  # noqa: BLE001 — continue batch on single-sample failure
            progress.end_sample(index, failed=True, error_message=str(exc)[:200])
            failed_samples.append({"sample_id": meta.sample_id, "error": str(exc)[:500]})
            continue
        rows.append(report.to_dict())
        saved.append(str(save_report(report, reports_dir=paths["reports_dir"], model=model)))
        c = report.completeness
        progress.end_sample(
            index,
            touch_rate=float(c.get("touch_rate") or 0),
            coverage_rate=float(c.get("coverage_rate") or 0),
        )

    progress.finish(extra_message=f"Saved {len(saved)} reports → {paths['reports_dir']}")

    result: dict[str, Any] = {
        "framework_version": FRAMEWORK_VERSION,
        "n_samples": len(rows),
        "n_failed": len(failed_samples),
        "failed_samples": failed_samples,
        "version_snapshot": v,
        "run_config": str(paths["run_config"]),
        "output_root": str(paths["output_root"]),
        "reports_saved": len(saved),
        "shard_index": shard_index,
        "num_shards": num_shards,
        "shard_count": len(metas),
        "corpus_total": global_total,
    }

    if not skip_aggregate:
        alignment = build_alignment_report(rows, version_snapshot=v)
        agg = _aggregate(rows, cfg)
        tag = model_tag(model)
        _export_csv(rows, aggregate_dir=paths["aggregate_dir"], model=model)
        _export_priorities_csv(rows, aggregate_dir=paths["aggregate_dir"], model=model)
        paths["aggregate_dir"].mkdir(parents=True, exist_ok=True)
        (paths["aggregate_dir"] / "batch_summary.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8")
        (paths["aggregate_dir"] / f"batch_summary__{tag}.json").write_text(
            json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (paths["aggregate_dir"] / "alignment_val.json").write_text(
            json.dumps(alignment.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (paths["aggregate_dir"] / f"alignment_val__{tag}.json").write_text(
            json.dumps(alignment.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        result["aggregate"] = agg
        result["alignment"] = alignment.to_dict()

    if merge_reports_after:
        merged = merge_aggregate_from_reports(
            version_snapshot=v,
            model=model,
            separate_by_model=separate_by_model,
        )
        result["merged_aggregate"] = merged

    return result


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
    baseline_summary = _baseline_summary(rows)

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
        "baselines": baseline_summary,
        "top_test_priorities": _aggregate_priorities(rows),
    }


def _baseline_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = []
    for r in rows:
        stmt = ((r.get("baselines") or {}).get("statement_coverage") or {})
        if "statement_coverage_rate" not in stmt:
            continue
        mr_cov = float((r.get("completeness") or {}).get("coverage_rate") or 0)
        pairs.append(
            {
                "sample_id": (r.get("meta") or {}).get("sample_id"),
                "library": (r.get("meta") or {}).get("library"),
                "category": (r.get("meta") or {}).get("category"),
                "statement_coverage_rate": float(stmt.get("statement_coverage_rate") or 0),
                "mr_coverage_rate": mr_cov,
                "strict_gap_rate": float((r.get("completeness") or {}).get("strict_gap_rate") or 0),
            }
        )
    stmt_vals = [p["statement_coverage_rate"] for p in pairs]
    mr_vals = [p["mr_coverage_rate"] for p in pairs]
    gap_vals = [p["strict_gap_rate"] for p in pairs]
    high_stmt_low_mr = [
        p for p in sorted(pairs, key=lambda x: (-x["statement_coverage_rate"], x["mr_coverage_rate"]))
        if p["statement_coverage_rate"] >= 0.6 and p["mr_coverage_rate"] < 0.3
    ][:20]
    return {
        "statement_coverage": {
            "kind": "statement_coverage_static_proxy",
            "n": len(pairs),
            "distribution": _distribution(stmt_vals),
            "pearson_vs_mr_coverage": _pearson(stmt_vals, mr_vals),
            "pearson_vs_strict_gap": _pearson(stmt_vals, gap_vals),
            "high_statement_low_mr_components": high_stmt_low_mr,
        }
    }


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return round(num / (dx * dy), 6) if dx and dy else None


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


def _export_csv(
    rows: list[dict[str, Any]],
    *,
    aggregate_dir: Path = AGGREGATE_DIR,
    model: str | None = None,
) -> None:
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    path = aggregate_dir / "per_sample_metrics.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "sample_id", "library", "category", "component_name",
                "total_mrs", "touch_rate", "coverage_rate", "issue_pressure",
                "weighted_touch_rate", "weighted_coverage_rate", "strict_gap_rate",
                "statement_coverage_rate",
                "mr_inference_mode", "alignment_mode",
            ],
        )
        w.writeheader()
        for r in rows:
            c = r.get("completeness") or {}
            p = r.get("provenance") or {}
            m = r["meta"]
            stmt = ((r.get("baselines") or {}).get("statement_coverage") or {})
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
                "statement_coverage_rate": stmt.get("statement_coverage_rate"),
                "mr_inference_mode": p.get("mr_inference_mode"),
                "alignment_mode": p.get("alignment_mode"),
            })
    (aggregate_dir / f"per_sample_metrics__{model_tag(model)}.csv").write_text(
        path.read_text(encoding="utf-8"), encoding="utf-8"
    )


def _aggregate_priorities(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for r in rows:
        for item in r.get("test_priorities") or []:
            items.append({"sample_id": r["meta"]["sample_id"], **item})
    items.sort(key=lambda x: -float(x.get("priority_score") or 0))
    return items[:50]


def _export_priorities_csv(
    rows: list[dict[str, Any]],
    *,
    aggregate_dir: Path = AGGREGATE_DIR,
    model: str | None = None,
) -> None:
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    path = aggregate_dir / "test_priorities.csv"
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
    (aggregate_dir / f"test_priorities__{model_tag(model)}.csv").write_text(
        path.read_text(encoding="utf-8"), encoding="utf-8"
    )

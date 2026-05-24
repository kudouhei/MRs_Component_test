"""End-to-end five-phase pipeline for one sample or batch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import SampleReport, utc_now_iso
from .phase1_inference import MrInferenceMode, infer_mrs, mrs_to_coverage_skeleton
from .phase2_alignment import align_tests_to_mrs
from .phase3_completeness import compute_completeness, diagnose_blind_spots
from .phase4_alignment import build_alignment_report, issue_pressure_for_sample
from .phase5_priorities import build_test_priorities, insufficient_attention_evidence
from .samples import PROJECT_ROOT, SampleMeta, iter_samples, read_sample_files
from .versioning import (
    DEFAULT_LLM_MODEL,
    build_run_provenance,
    default_run_config,
    write_run_config,
)

OUTPUT_ROOT = PROJECT_ROOT / "output"
REPORTS_DIR = OUTPUT_ROOT / "reports"
AGGREGATE_DIR = OUTPUT_ROOT / "aggregate"
RUN_CONFIG_PATH = OUTPUT_ROOT / "run_config.json"


def analyze_sample(
    meta: SampleMeta,
    *,
    mr_inference_mode: MrInferenceMode = "llm",
    model: str | None = None,
    allow_heuristic_fallback: bool = False,
    version_snapshot: str | None = None,
) -> SampleReport:
    code, tests = read_sample_files(meta)
    llm_model = model or DEFAULT_LLM_MODEL
    inference = infer_mrs(
        code,
        meta,
        mode=mr_inference_mode,
        model=llm_model,
        allow_heuristic_fallback=allow_heuristic_fallback,
    )
    mrs = inference.mrs
    mr_coverage = mrs_to_coverage_skeleton(mrs)
    align_tests_to_mrs(mrs, mr_coverage, tests=tests, code=code, meta=meta)

    completeness = compute_completeness(mr_coverage)
    blind = diagnose_blind_spots(mr_coverage)
    pressure = issue_pressure_for_sample(meta)
    priorities = build_test_priorities(meta, mr_coverage, issue_pressure=pressure)
    evidence = insufficient_attention_evidence(
        completeness.to_dict(),
        blind.to_dict(),
        issue_pressure=pressure,
    )

    provenance = build_run_provenance(
        mr_inference_mode=inference.mode,
        llm_model=inference.llm_model,
        llm_temperature=inference.llm_temperature,
        prompt_version=inference.prompt_version,
        prompt_fingerprint=inference.prompt_fingerprint,
        taxonomy_version=inference.taxonomy_version,
        taxonomy_fingerprint=inference.taxonomy_fingerprint,
        llm_fallback_reason=inference.fallback_reason,
    )

    v = version_snapshot or utc_now_iso()
    report_model = inference.llm_model if inference.mode == "llm" else "heuristic_ablation"
    return SampleReport(
        meta=meta,
        version_snapshot=v,
        model=report_model,
        provenance=provenance,
        metamorphic_relations=[m.to_dict() for m in mrs],
        mr_coverage=mr_coverage,
        completeness=completeness.to_dict(),
        blind_spots=blind.to_dict(),
        test_priorities=[p.to_dict() for p in priorities],
        issue_pressure=pressure,
        alignment_notes={"insufficient_attention": evidence},
        generated_at=utc_now_iso(),
    )


def save_report(report: SampleReport, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{report.meta.sample_id}.json"
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_batch(
    *,
    library: str | None = None,
    limit: int | None = None,
    sample_id: str | None = None,
    mr_inference_mode: MrInferenceMode = "llm",
    model: str | None = None,
    allow_heuristic_fallback: bool = False,
    version_snapshot: str | None = None,
    write_reports: bool = True,
) -> dict[str, Any]:
    version_snapshot = version_snapshot or utc_now_iso()
    llm_model = model or DEFAULT_LLM_MODEL
    run_cfg = default_run_config(
        version_snapshot=version_snapshot,
        mr_inference_mode=mr_inference_mode,
        llm_model=llm_model,
        allow_heuristic_fallback=allow_heuristic_fallback,
    )
    write_run_config(RUN_CONFIG_PATH, run_cfg)

    rows: list[dict[str, Any]] = []
    saved: list[str] = []
    fallback_count = 0

    for meta in iter_samples(library=library, limit=limit, sample_id=sample_id):
        report = analyze_sample(
            meta,
            mr_inference_mode=mr_inference_mode,
            model=llm_model,
            allow_heuristic_fallback=allow_heuristic_fallback,
            version_snapshot=version_snapshot,
        )
        if report.provenance.get("llm_fallback_reason"):
            fallback_count += 1
        row = report.to_dict()
        rows.append(row)
        if write_reports:
            p = save_report(report)
            saved.append(str(p))

    alignment = build_alignment_report(rows, version_snapshot=version_snapshot)
    agg = aggregate_batch(rows, alignment)
    agg["provenance"] = run_cfg
    agg["llm_fallback_sample_count"] = fallback_count

    AGGREGATE_DIR.mkdir(parents=True, exist_ok=True)
    (AGGREGATE_DIR / "batch_summary.json").write_text(
        json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (AGGREGATE_DIR / "alignment_val.json").write_text(
        json.dumps(alignment.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    export_rq_tables(rows, agg, alignment)

    return {
        "n_samples": len(rows),
        "version_snapshot": version_snapshot,
        "run_config_path": str(RUN_CONFIG_PATH),
        "reports_saved": saved,
        "aggregate": agg,
        "alignment": alignment.to_dict(),
    }


def aggregate_batch(
    rows: list[dict[str, Any]],
    alignment: Any,
) -> dict[str, Any]:
    if not rows:
        return {"n_samples": 0}

    def mean(field: str) -> float:
        vals = [float((r.get("completeness") or {}).get(field) or 0) for r in rows]
        return round(sum(vals) / len(vals), 6) if vals else 0.0

    by_library: dict[str, list[float]] = {}
    by_category: dict[str, list[float]] = {}
    blind_type_counter: dict[str, int] = {}

    for r in rows:
        lib = r["meta"]["library"]
        cat = r["meta"]["category"]
        tr = float((r.get("completeness") or {}).get("touch_rate") or 0)
        by_library.setdefault(lib, []).append(tr)
        by_category.setdefault(cat, []).append(tr)
        for b in (r.get("blind_spots") or {}).get("top_blind_mr_types") or []:
            rt = str(b.get("relation_type") or "")
            blind_type_counter[rt] = blind_type_counter.get(rt, 0) + int(b.get("blind_count") or 0)

    rq1 = {
        "mean_touch_rate": mean("touch_rate"),
        "mean_coverage_rate": mean("coverage_rate"),
        "mean_hybrid_touch_rate": mean("hybrid_touch_rate"),
        "by_library": {
            lib: round(sum(v) / len(v), 6) for lib, v in sorted(by_library.items())
        },
        "by_category": {
            cat: round(sum(v) / len(v), 6) for cat, v in sorted(by_category.items())
        },
    }
    rq2 = {
        "top_blind_mr_types_global": sorted(
            [{"relation_type": k, "count": n} for k, n in blind_type_counter.items()],
            key=lambda x: -x["count"],
        )[:20],
    }
    return {
        "n_samples": len(rows),
        "rq1": rq1,
        "rq2": rq2,
        "rq3_alignment_ref": "see alignment_val.json",
    }


def export_rq_tables(
    rows: list[dict[str, Any]],
    agg: dict[str, Any],
    alignment: Any,
) -> None:
    import csv

    AGGREGATE_DIR.mkdir(parents=True, exist_ok=True)
    per_sample = AGGREGATE_DIR / "per_sample_metrics.csv"
    with per_sample.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "sample_id",
                "library",
                "category",
                "component_name",
                "mr_inference_mode",
                "total_mrs",
                "touched_mrs",
                "touch_rate",
                "covered_mrs",
                "coverage_rate",
                "issue_pressure",
            ],
        )
        w.writeheader()
        for r in rows:
            c = r.get("completeness") or {}
            m = r.get("meta") or {}
            prov = r.get("provenance") or {}
            w.writerow(
                {
                    "sample_id": m.get("sample_id"),
                    "library": m.get("library"),
                    "category": m.get("category"),
                    "component_name": m.get("component_name"),
                    "mr_inference_mode": prov.get("mr_inference_mode"),
                    "total_mrs": c.get("total_mrs"),
                    "touched_mrs": c.get("touched_mrs"),
                    "touch_rate": c.get("touch_rate"),
                    "covered_mrs": c.get("covered_mrs"),
                    "coverage_rate": c.get("coverage_rate"),
                    "issue_pressure": r.get("issue_pressure"),
                }
            )

    priorities_path = AGGREGATE_DIR / "test_priorities.csv"
    with priorities_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "library",
                "component_name",
                "category",
                "relation_type",
                "type_category",
                "reason",
                "priority_score",
            ],
        )
        w.writeheader()
        for r in rows:
            for p in r.get("test_priorities") or []:
                w.writerow(p)

#!/usr/bin/env python3
"""Regenerate RQ4 alignment artifacts (ensemble Exp1 + topic/type-gap Exp2)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mr_framework.models import utc_now_iso
from mr_framework.phase4_alignment import (
    RQ4_ENSEMBLE_MODEL_DIRS,
    build_alignment_report,
    build_ensemble_exp1_rows,
)
from mr_framework.pipeline import load_saved_report_rows

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
AGGREGATE_DIR = PROJECT_ROOT / "output" / "aggregate"
PRIMARY_MODEL_DIR = PROJECT_ROOT / "output" / "model_runs" / "deepseek"


def _pct(v: float | None, digits: int = 1) -> str:
    if v is None:
        return ""
    return f"{100 * v:.{digits}f}"


def _write_pressure_csv(path: Path, exp1: dict) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "pressure_bin",
                "bin_definition",
                "n",
                "mean_coverage_rate",
                "mean_coverage_pct",
                "mean_touch_rate",
                "mean_touch_pct",
                "zero_coverage_count",
            ]
        )
        defs = exp1.get("pressure_bin_definitions") or {}
        for row in exp1.get("pressure_bins") or []:
            cov = row.get("mean_coverage_rate")
            touch = row.get("mean_touch_rate")
            w.writerow(
                [
                    row.get("bin"),
                    defs.get(row.get("bin"), ""),
                    row.get("n"),
                    cov,
                    _pct(cov),
                    touch,
                    _pct(touch),
                    row.get("zero_coverage_count"),
                ]
            )


THEME_LABELS = {
    "keyboard_interaction": "Keyboard",
    "placement_consistency": "Placement",
    "focus_management": "Focus",
    "null_handling": "Null / empty",
    "state_synchronization": "State sync",
    "aria_mapping": "ARIA / a11y",
    "interaction_feedback": "Click / hover",
    "pagination_consistency": "Pagination",
    "data_validation": "Validation",
    "responsive_sizing": "Responsive layout",
}


def _write_topic_mapping_csv(path: Path, exp2: dict) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "theme_label",
                "relation_type",
                "n_tagged_pairs",
                "n_lands_on_mr_type",
                "n_not_in_inferred_mrs",
                "mapping_rate_pct",
                "corpus_type_prevalence_pct",
                "enrichment_vs_prevalence",
                "p_value",
                "q_value",
                "fdr_significant",
                "issue_topic_count_in_corpus",
            ]
        )
        for row in exp2.get("topic_to_mr_type_mapping") or []:
            q = row.get("q_value")
            rel = row.get("relation_type")
            w.writerow(
                [
                    THEME_LABELS.get(rel, rel),
                    rel,
                    row.get("n_tagged_issue_component_pairs"),
                    row.get("n_lands_on_mr_type"),
                    row.get("n_not_in_inferred_mrs"),
                    _pct(row.get("mapping_rate")),
                    _pct(row.get("corpus_type_prevalence")),
                    row.get("enrichment_vs_prevalence"),
                    row.get("p_value"),
                    q,
                    "yes" if q is not None and float(q) < 0.05 else "no",
                    row.get("issue_topic_count_in_corpus"),
                ]
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate RQ4 alignment artifacts")
    parser.add_argument(
        "--primary-reports",
        type=Path,
        default=PRIMARY_MODEL_DIR / "reports",
        help="Primary reports used for component/issue matching in Exp2",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=AGGREGATE_DIR / "alignment_val.json",
    )
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=ANALYSIS_DIR,
    )
    args = parser.parse_args()

    primary_rows = load_saved_report_rows(reports_dir=args.primary_reports)
    if not primary_rows:
        raise SystemExit(f"No reports found under {args.primary_reports}")

    ensemble_rows = build_ensemble_exp1_rows(primary_rows)
    if len(ensemble_rows) != len(primary_rows):
        raise SystemExit(
            f"Ensemble rows {len(ensemble_rows)} != primary rows {len(primary_rows)}; "
            "check all three model report directories."
        )

    issues_summary_path = PROJECT_ROOT / "analysis" / "open_issues" / "open_issues_summary.json"
    issues_summary = {}
    if issues_summary_path.exists():
        issues_summary = json.loads(issues_summary_path.read_text(encoding="utf-8"))

    alignment = build_alignment_report(
        primary_rows,
        version_snapshot=utc_now_iso(),
        exp1_rows=ensemble_rows,
        exp1_coverage_metric="ensemble_mean",
        exp1_ensemble_models=list(RQ4_ENSEMBLE_MODEL_DIRS),
        exp2_mapping_metric="ensemble_union",
        exp2_ensemble_models=list(RQ4_ENSEMBLE_MODEL_DIRS),
    )
    payload = alignment.to_dict()
    payload["rq4"] = {
        "open_issues": issues_summary,
        "exp1_note": "Issue pressure vs. ensemble macro Cover/Touch (three LLM per-component means).",
        "exp2_note": "Keyword-tagged bug themes vs. whether theme lands on inferred MR relation_type (ensemble union).",
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tagged = args.output_json.with_name("alignment_val__deepseek-chat.json")
    tagged.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    args.analysis_dir.mkdir(parents=True, exist_ok=True)
    _write_pressure_csv(args.analysis_dir / "rq4_pressure_bins.csv", payload["exp1"])
    _write_topic_mapping_csv(args.analysis_dir / "rq4_topic_mr_mapping.csv", payload["exp2"])
    (args.analysis_dir / "rq4_alignment.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    exp1 = payload["exp1"]
    exp2 = payload["exp2"]
    high = exp1.get("high_pressure_vs_others_strict_gap_test") or {}
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.analysis_dir / 'rq4_pressure_bins.csv'}")
    print(f"Wrote {args.analysis_dir / 'rq4_topic_mr_mapping.csv'}")
    print(
        f"Exp1 ensemble n={exp1.get('n')} "
        f"Cover={_pct(exp1.get('mean_coverage_rate'))}% "
        f"Touch={_pct(exp1.get('mean_touch_rate'))}% "
        f"r(p,Cover)={exp1.get('pearson_pressure_vs_coverage_rate')}"
    )
    print(
        f"High pressure (>=9): n={high.get('n_high')} "
        f"gap diff={_pct(high.get('strict_gap_diff_high_minus_other'))}pp "
        f"p={high.get('strict_gap_diff_permutation_pvalue')}"
    )
    sig = exp2.get("significant_topics_fdr_005") or []
    print(
        f"Exp2 overall mapping={_pct(exp2.get('overall_mapping_rate'))}% "
        f"pairs_with_topic={exp2.get('n_matched_pairs_with_topic')} "
        f"FDR-significant={sig}"
    )


if __name__ == "__main__":
    main()

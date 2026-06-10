#!/usr/bin/env python3
"""Analyze local-vs-LLM contribution in hybrid test--MR alignment.

The script expects per-sample reports produced by the main pipeline under
output/reports/*.json. It summarizes whether final touch/cover labels come
from local evidence, LLM judgment, both channels, or neither channel.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mr_framework.pipeline import model_tag, output_root_for_model  # noqa: E402


def _load_reports(reports_dir: Path, *, model: str | None = None) -> list[dict[str, Any]]:
    tag = model_tag(model) if model is not None else None
    rows: list[dict[str, Any]] = []
    for path in sorted(reports_dir.glob("*.json")):
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if tag:
            is_tagged = path.stem.endswith(f"__{tag}")
            prov_model = str((report.get("provenance") or {}).get("llm_model") or "")
            if not is_tagged and prov_model != (model or ""):
                continue
        rows.append(report)
    return rows


def _classify(local: bool, llm: bool) -> str:
    if local and llm:
        return "both"
    if local:
        return "local_only"
    if llm:
        return "llm_only"
    return "neither"


def _pct(n: int, d: int) -> float:
    return round((100.0 * n / d), 1) if d else 0.0


def _fmt(n: int, d: int) -> str:
    return f"{n} ({_pct(n, d):.1f}\\%)"


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        "touch": {"local_only": 0, "llm_only": 0, "both": 0, "neither": 0},
        "cover": {"local_only": 0, "llm_only": 0, "both": 0, "neither": 0},
    }
    by_library: dict[str, dict[str, Any]] = {}
    total_mrs = 0

    for report in rows:
        meta = report.get("meta") or {}
        lib = str(meta.get("library") or "unknown")
        lib_bucket = by_library.setdefault(
            lib,
            {
                "library": lib,
                "n_reports": 0,
                "total_mrs": 0,
                "touch": {"local_only": 0, "llm_only": 0, "both": 0, "neither": 0},
                "cover": {"local_only": 0, "llm_only": 0, "both": 0, "neither": 0},
            },
        )
        lib_bucket["n_reports"] += 1
        for mr in report.get("mr_coverage") or []:
            if not isinstance(mr, dict):
                continue
            total_mrs += 1
            lib_bucket["total_mrs"] += 1

            touch_src = _classify(bool(mr.get("evidence_touch")), bool(mr.get("llm_touched")))
            cover_src = _classify(bool(mr.get("evidence_covered")), bool(mr.get("llm_covered")))
            totals["touch"][touch_src] += 1
            totals["cover"][cover_src] += 1
            lib_bucket["touch"][touch_src] += 1
            lib_bucket["cover"][cover_src] += 1

    def enrich(kind: str, counts: dict[str, int], denominator: int) -> dict[str, Any]:
        local_positive = counts["local_only"] + counts["both"]
        llm_positive = counts["llm_only"] + counts["both"]
        hybrid_positive = counts["local_only"] + counts["llm_only"] + counts["both"]
        agreement = counts["both"] + counts["neither"]
        disagreement = counts["local_only"] + counts["llm_only"]
        return {
            "decision": kind,
            "total_mrs": denominator,
            **counts,
            "local_positive": local_positive,
            "llm_positive": llm_positive,
            "hybrid_positive": hybrid_positive,
            "agreement": agreement,
            "disagreement": disagreement,
            "local_only_pct_total": _pct(counts["local_only"], denominator),
            "llm_only_pct_total": _pct(counts["llm_only"], denominator),
            "both_pct_total": _pct(counts["both"], denominator),
            "neither_pct_total": _pct(counts["neither"], denominator),
            "hybrid_positive_pct_total": _pct(hybrid_positive, denominator),
            "agreement_pct_total": _pct(agreement, denominator),
            "disagreement_pct_total": _pct(disagreement, denominator),
            "local_only_pct_hybrid_positive": _pct(counts["local_only"], hybrid_positive),
            "llm_only_pct_hybrid_positive": _pct(counts["llm_only"], hybrid_positive),
            "both_pct_hybrid_positive": _pct(counts["both"], hybrid_positive),
        }

    overall = [enrich("touch", totals["touch"], total_mrs), enrich("cover", totals["cover"], total_mrs)]
    libraries = []
    for lib in sorted(by_library):
        bucket = by_library[lib]
        for kind in ("touch", "cover"):
            row = enrich(kind, bucket[kind], int(bucket["total_mrs"]))
            row["library"] = lib
            row["n_reports"] = bucket["n_reports"]
            libraries.append(row)

    return {
        "n_reports": len(rows),
        "total_mrs": total_mrs,
        "overall": overall,
        "by_library": libraries,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], *, include_library: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "decision",
        "total_mrs",
        "local_only",
        "llm_only",
        "both",
        "neither",
        "local_positive",
        "llm_positive",
        "hybrid_positive",
        "agreement",
        "disagreement",
        "local_only_pct_total",
        "llm_only_pct_total",
        "both_pct_total",
        "neither_pct_total",
        "hybrid_positive_pct_total",
        "agreement_pct_total",
        "disagreement_pct_total",
        "local_only_pct_hybrid_positive",
        "llm_only_pct_hybrid_positive",
        "both_pct_hybrid_positive",
    ]
    if include_library:
        fields = ["library", "n_reports", *fields]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_tex(path: Path, summary: dict[str, Any]) -> None:
    rows = {r["decision"]: r for r in summary["overall"]}
    total = int(summary["total_mrs"])
    touch = rows.get("touch", {})
    cover = rows.get("cover", {})
    text = rf"""\begin{{table}}[h]
\centering
\caption{{Contribution of local evidence and LLM judgment in hybrid test--MR alignment.}}
\label{{tab:alignment_source_ablation}}
\footnotesize
\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{lrrrrr}}
\toprule
\textbf{{Decision}} & \textbf{{Local only}} & \textbf{{LLM only}} & \textbf{{Both}} & \textbf{{Neither}} & \textbf{{Agreement}} \\
\midrule
Touch & {_fmt(int(touch.get("local_only", 0)), total)} & {_fmt(int(touch.get("llm_only", 0)), total)} & {_fmt(int(touch.get("both", 0)), total)} & {_fmt(int(touch.get("neither", 0)), total)} & {_fmt(int(touch.get("agreement", 0)), total)} \\
Cover & {_fmt(int(cover.get("local_only", 0)), total)} & {_fmt(int(cover.get("llm_only", 0)), total)} & {_fmt(int(cover.get("both", 0)), total)} & {_fmt(int(cover.get("neither", 0)), total)} & {_fmt(int(cover.get("agreement", 0)), total)} \\
\bottomrule
\multicolumn{{6}}{{l}}{{\footnotesize Percentages are over all {total} MR--test alignment decisions. Agreement = Both + Neither.}}
\end{{tabular}}
\end{{table}}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze hybrid alignment source contributions.")
    parser.add_argument(
        "--reports-dir",
        type=Path,
        action="append",
        default=None,
        help="Report directory to analyze. May be passed multiple times.",
    )
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--separate-by-model", action="store_true")
    args = parser.parse_args()

    out_root = output_root_for_model(args.model, separate_by_model=args.separate_by_model)
    report_dirs = args.reports_dir or [out_root / "reports"]
    out_dir = args.out_dir or (out_root / "analysis")

    reports: list[dict[str, Any]] = []
    for reports_dir in report_dirs:
        reports.extend(_load_reports(reports_dir, model=args.model if args.model and not args.reports_dir else None))
    if not reports:
        dirs = ", ".join(str(p) for p in report_dirs)
        print(f"No report JSON files found in {dirs}", file=sys.stderr)
        return 1

    summary = _summarize(reports)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "alignment_source_ablation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_csv(out_dir / "alignment_source_ablation.csv", summary["overall"])
    _write_csv(out_dir / "alignment_source_ablation_by_library.csv", summary["by_library"], include_library=True)
    _write_tex(out_dir / "alignment_source_ablation.tex", summary)

    print(json.dumps({"reports": summary["n_reports"], "total_mrs": summary["total_mrs"], "out_dir": str(out_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

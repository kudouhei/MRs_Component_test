#!/usr/bin/env python3
"""Aggregate statistics from output/reports/*.json → tables + HTML dashboard."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mr_framework.pipeline import model_tag, output_root_for_model
from mr_framework.samples import PROJECT_ROOT

REPORTS_DIR = PROJECT_ROOT / "output" / "reports"
OUT_DIR = PROJECT_ROOT / "output" / "analysis"


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _load_rows(reports_dir: Path, *, model: str | None = None) -> list[dict]:
    rows = []
    tag = model_tag(model) if model is not None else None
    for path in sorted(reports_dir.glob("*.json")):
        try:
            r = json.loads(path.read_text(encoding="utf-8"))
            if tag:
                is_tagged = path.stem.endswith(f"__{tag}")
                prov_model = str((r.get("provenance") or {}).get("llm_model") or "")
                if not is_tagged and prov_model != (model or ""):
                    continue
            rows.append(r)
        except (json.JSONDecodeError, OSError):
            continue
    return rows


def _sample_row(r: dict) -> dict:
    m = r.get("meta") or {}
    c = r.get("completeness") or {}
    b = r.get("blind_spots") or {}
    return {
        "sample_id": m.get("sample_id"),
        "library": m.get("library"),
        "category": m.get("category"),
        "component_name": m.get("component_name"),
        "total_mrs": int(c.get("total_mrs") or 0),
        "touch_rate": float(c.get("touch_rate") or 0),
        "coverage_rate": float(c.get("coverage_rate") or 0),
        "strict_gap_rate": float(c.get("strict_gap_rate") or 0),
        "touched_not_covered": int(c.get("touched_not_covered") or 0),
        "miss_at_uncov": int(c.get("miss_at_uncov") or 0),
        "issue_pressure": int(r.get("issue_pressure") or 0),
        "weak_oracle": int(b.get("touched_not_covered") or c.get("touched_not_covered") or 0),
    }


def _group_stats(rows: list[dict], key: str) -> list[dict]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        buckets[str(row[key])].append(row)
    out = []
    for name in sorted(buckets.keys()):
        xs = buckets[name]
        covs = [x["coverage_rate"] for x in xs]
        touches = [x["touch_rate"] for x in xs]
        mrs = [x["total_mrs"] for x in xs]
        out.append({
            key: name,
            "n_samples": len(xs),
            "mean_touch_rate": round(statistics.mean(touches), 4),
            "mean_coverage_rate": round(statistics.mean(covs), 4),
            "median_coverage_rate": round(statistics.median(covs), 4),
            "mean_total_mrs": round(statistics.mean(mrs), 2),
            "sum_total_mrs": sum(mrs),
            "zero_coverage_samples": sum(1 for x in xs if x["coverage_rate"] == 0),
        })
    return out


def _coverage_buckets(rows: list[dict]) -> list[dict]:
    edges = [(0, 0.01, "0%"), (0.01, 0.25, "1–24%"), (0.25, 0.5, "25–49%"),
             (0.5, 0.75, "50–74%"), (0.75, 1.01, "75–100%")]
    out = []
    for lo, hi, label in edges:
        n = sum(1 for x in rows if lo <= x["coverage_rate"] < hi)
        out.append({"bucket": label, "count": n, "share": round(n / len(rows), 4) if rows else 0})
    return out


def _svg_bar_chart(
    title: str,
    labels: list[str],
    values: list[float],
    *,
    value_fmt: str = ".0%",
    max_val: float | None = None,
    width: int = 640,
    height: int = 280,
) -> str:
    if not labels:
        return f'<svg width="{width}" height="{height}"><text x="10" y="20">{title}</text></svg>'
    max_v = max_val or max(values) or 1
    pad_l, pad_t, pad_b = 120, 36, 40
    chart_w = width - pad_l - 24
    bar_h = max(14, (height - pad_t - pad_b) // len(labels) - 6)
    total_h = pad_t + len(labels) * (bar_h + 6) + pad_b
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" role="img">',
        f'<text x="12" y="22" font-size="14" font-weight="600">{title}</text>',
    ]
    for i, (lab, val) in enumerate(zip(labels, values)):
        y = pad_t + i * (bar_h + 6)
        w = int(chart_w * (val / max_v)) if max_v else 0
        label = lab[:28] + ("…" if len(lab) > 28 else "")
        if value_fmt.endswith("%"):
            txt = f"{100 * val:.1f}%"
        else:
            txt = f"{val:{value_fmt}}"
        parts.append(f'<text x="8" y="{y + bar_h - 4}" font-size="11">{label}</text>')
        parts.append(f'<rect x="{pad_l}" y="{y}" width="{w}" height="{bar_h}" fill="#3b82f6" rx="3"/>')
        parts.append(f'<text x="{pad_l + w + 6}" y="{y + bar_h - 4}" font-size="11">{txt}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def _build_html(
    *,
    n: int,
    overview: dict,
    by_lib: list[dict],
    by_cat: list[dict],
    buckets: list[dict],
    top_blind: list[dict],
    bottom_samples: list[dict],
    charts: dict[str, str],
) -> str:
    def table(rows: list[dict], cols: list[tuple[str, str]]) -> str:
        if not rows:
            return "<p>—</p>"
        head = "".join(f"<th>{h}</th>" for _, h in cols)
        body = []
        for r in rows:
            tds = []
            for k, h in cols:
                v = r.get(k, "")
                if k.endswith("_rate") and isinstance(v, (int, float)):
                    tds.append(f"<td>{_pct(v)}</td>")
                elif k == "share" and isinstance(v, (int, float)):
                    tds.append(f"<td>{_pct(v)}</td>")
                else:
                    tds.append(f"<td>{v}</td>")
            body.append("<tr>" + "".join(tds) + "</tr>")
        return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <title>MR Completeness — Reports Analysis ({n} samples)</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 24px; max-width: 960px; color: #111; }}
    h1 {{ font-size: 1.5rem; }} h2 {{ margin-top: 2rem; font-size: 1.15rem; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; background: #fafafa; }}
    .card .v {{ font-size: 1.4rem; font-weight: 700; }} .card .l {{ font-size: 0.8rem; color: #555; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; margin: 12px 0; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 6px 10px; text-align: left; }}
    th {{ background: #f3f4f6; }}
    .chart {{ margin: 16px 0; overflow-x: auto; }}
    p.note {{ color: #666; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <h1>UI 组件 MR 完备性统计（output/reports）</h1>
  <p class="note">共 {n} 份报告 · 生成自 analyze_reports.py</p>

  <h2>总览</h2>
  <div class="cards">
    <div class="card"><div class="v">{overview['total_mrs']}</div><div class="l">推断 MR 总数</div></div>
    <div class="card"><div class="v">{_pct(overview['mean_touch'])}</div><div class="l">平均触达率</div></div>
    <div class="card"><div class="v">{_pct(overview['mean_coverage'])}</div><div class="l">平均严格覆盖率</div></div>
    <div class="card"><div class="v">{overview['zero_cov']}</div><div class="l">覆盖率为 0 的组件</div></div>
    <div class="card"><div class="v">{overview['full_touch']}</div><div class="l">触达率 100% 的组件</div></div>
    <div class="card"><div class="v">{overview['total_weak']}</div><div class="l">触达未覆盖 MR 累计</div></div>
  </div>

  <h2>按组件库</h2>
  {table(by_lib, [
    ("library", "库"), ("n_samples", "样本数"), ("mean_touch_rate", "平均触达"),
    ("mean_coverage_rate", "平均覆盖"), ("median_coverage_rate", "覆盖中位数"),
    ("mean_total_mrs", "平均|MR|"), ("zero_coverage_samples", "零覆盖数"),
  ])}
  <div class="chart">{charts['by_library']}</div>

  <h2>按 UI 类别</h2>
  {table(by_cat, [
    ("category", "类别"), ("n_samples", "样本数"), ("mean_touch_rate", "平均触达"),
    ("mean_coverage_rate", "平均覆盖"), ("median_coverage_rate", "覆盖中位数"),
  ])}
  <div class="chart">{charts['by_category']}</div>

  <h2>严格覆盖率分布</h2>
  {table(buckets, [("bucket", "区间"), ("count", "组件数"), ("share", "占比")])}
  <div class="chart">{charts['coverage_buckets']}</div>

  <h2>高频盲区 relation_type（Top 15）</h2>
  {table(top_blind[:15], [("relation_type", "类型"), ("count", "出现次数")])}
  <div class="chart">{charts['top_blind']}</div>

  <h2>严格覆盖率最低（Top 15 组件）</h2>
  {table(bottom_samples, [
    ("sample_id", "sample_id"), ("library", "库"), ("category", "类别"),
    ("component_name", "组件"), ("coverage_rate", "覆盖率"), ("touch_rate", "触达率"),
    ("total_mrs", "|MR|"), ("issue_pressure", "issue压力"),
  ])}
</body>
</html>
"""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", type=Path, default=None)
    p.add_argument("--reports-dir", type=Path, default=None)
    p.add_argument("--model", default=None)
    p.add_argument("--separate-by-model", action="store_true")
    args = p.parse_args()
    out_root = output_root_for_model(args.model, separate_by_model=args.separate_by_model)
    reports_dir = args.reports_dir or (out_root / "reports")
    out: Path = args.out_dir or (out_root / "analysis")

    raw = _load_rows(reports_dir, model=args.model)
    if not raw:
        print("No reports found.", file=sys.stderr)
        return 1
    rows = [_sample_row(r) for r in raw]
    n = len(rows)

    covs = [x["coverage_rate"] for x in rows]
    touches = [x["touch_rate"] for x in rows]
    overview = {
        "n_samples": n,
        "total_mrs": sum(x["total_mrs"] for x in rows),
        "mean_touch": round(statistics.mean(touches), 4),
        "mean_coverage": round(statistics.mean(covs), 4),
        "median_coverage": round(statistics.median(covs), 4),
        "p25_coverage": round(statistics.quantiles(covs, n=4)[0], 4) if len(covs) >= 4 else min(covs),
        "p75_coverage": round(statistics.quantiles(covs, n=4)[2], 4) if len(covs) >= 4 else max(covs),
        "zero_cov": sum(1 for x in rows if x["coverage_rate"] == 0),
        "full_touch": sum(1 for x in rows if x["touch_rate"] == 1),
        "total_weak": sum(x["touched_not_covered"] for x in rows),
        "total_untouched": sum(x["miss_at_uncov"] for x in rows),
    }

    by_lib = _group_stats(rows, "library")
    by_cat = _group_stats(rows, "category")
    buckets = _coverage_buckets(rows)

    blind_counts: dict[str, int] = defaultdict(int)
    for r in raw:
        for item in (r.get("blind_spots") or {}).get("top_blind_mr_types") or []:
            blind_counts[str(item.get("relation_type"))] += int(item.get("blind_count") or 0)
    top_blind = sorted(
        [{"relation_type": k, "count": v} for k, v in blind_counts.items()],
        key=lambda x: -x["count"],
    )

    bottom = sorted(rows, key=lambda x: (x["coverage_rate"], x["touch_rate"]))[:15]
    for x in bottom:
        x["sample_id"] = x["sample_id"]

    charts = {
        "by_library": _svg_bar_chart(
            "平均严格覆盖率 · 按库",
            [x["library"] for x in by_lib],
            [x["mean_coverage_rate"] for x in by_lib],
            max_val=1.0,
        ),
        "by_category": _svg_bar_chart(
            "平均严格覆盖率 · 按类别",
            [x["category"] for x in by_cat],
            [x["mean_coverage_rate"] for x in by_cat],
            max_val=1.0,
        ),
        "coverage_buckets": _svg_bar_chart(
            "组件数量 · 覆盖率区间",
            [x["bucket"] for x in buckets],
            [x["share"] for x in buckets],
            max_val=max(x["share"] for x in buckets) if buckets else 1,
            value_fmt=".1%",
        ),
        "top_blind": _svg_bar_chart(
            "盲区 relation_type Top 12",
            [x["relation_type"] for x in top_blind[:12]],
            [x["count"] for x in top_blind[:12]],
            value_fmt="d",
            max_val=float(top_blind[0]["count"]) if top_blind else 1,
        ),
    }

    out.mkdir(parents=True, exist_ok=True)
    _write_csv(out / "overview.csv", [overview], list(overview.keys()))
    _write_csv(out / "by_library.csv", by_lib, list(by_lib[0].keys()) if by_lib else [])
    _write_csv(out / "by_category.csv", by_cat, list(by_cat[0].keys()) if by_cat else [])
    _write_csv(out / "coverage_buckets.csv", buckets, ["bucket", "count", "share"])
    _write_csv(out / "top_blind_mr_types.csv", top_blind, ["relation_type", "count"])
    _write_csv(
        out / "per_sample_sorted.csv",
        sorted(rows, key=lambda x: x["coverage_rate"]),
        list(rows[0].keys()),
    )

    payload = {
        "overview": overview,
        "by_library": by_lib,
        "by_category": by_cat,
        "coverage_buckets": buckets,
        "top_blind_mr_types": top_blind[:20],
        "bottom_coverage_samples": bottom,
    }
    (out / "dashboard_data.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    html = _build_html(
        n=n,
        overview=overview,
        by_lib=by_lib,
        by_cat=by_cat,
        buckets=buckets,
        top_blind=top_blind,
        bottom_samples=bottom,
        charts=charts,
    )
    (out / "dashboard.html").write_text(html, encoding="utf-8")
    (out / f"dashboard__{model_tag(args.model)}.html").write_text(html, encoding="utf-8")

    md_lines = [
        "# Reports 统计分析",
        "",
        f"样本数：**{n}** · MR 总数：**{overview['total_mrs']}**",
        "",
        "## 总览",
        "",
        "| 指标 | 值 |",
        "|------|-----|",
        f"| 平均触达率 | {_pct(overview['mean_touch'])} |",
        f"| 平均严格覆盖率 | {_pct(overview['mean_coverage'])} |",
        f"| 覆盖率中位数 | {_pct(overview['median_coverage'])} |",
        f"| 零覆盖组件数 | {overview['zero_cov']} |",
        f"| 触达 100% 组件数 | {overview['full_touch']} |",
        "",
        "## 按库",
        "",
        "| 库 | n | 平均触达 | 平均覆盖 |",
        "|----|---|----------|----------|",
    ]
    for x in by_lib:
        md_lines.append(
            f"| {x['library']} | {x['n_samples']} | {_pct(x['mean_touch_rate'])} | {_pct(x['mean_coverage_rate'])} |"
        )
    md_lines.extend(["", "## 按类别", "", "| 类别 | n | 平均覆盖 |", "|------|---|----------|"])
    for x in by_cat:
        md_lines.append(f"| {x['category']} | {x['n_samples']} | {_pct(x['mean_coverage_rate'])} |")
    md_lines.extend([
        "",
        "完整图表见 `output/analysis/dashboard.html`",
        "",
    ])
    summary_text = "\n".join(md_lines)
    (out / "SUMMARY.md").write_text(summary_text, encoding="utf-8")
    (out / f"SUMMARY__{model_tag(args.model)}.md").write_text(summary_text, encoding="utf-8")

    print(f"Wrote {out}/")
    print(f"  dashboard.html  — 打开浏览器查看图表")
    print(f"  SUMMARY.md      — Markdown 摘要")
    print(f"  *.csv           — 表格数据")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

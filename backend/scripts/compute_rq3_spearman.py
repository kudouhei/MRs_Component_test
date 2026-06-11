#!/usr/bin/env python3
"""Recompute RQ3 baseline comparison table using Spearman rank correlation.

Data sources:
  output/coverage/all_runtime_coverage.csv   – runtime stmt/branch for ant-design,
                                               mui-material, mui-base-ui
  output/coverage/ep_runtime_coverage.csv    – runtime stmt/branch for element-plus
  output/aggregate/per_sample_metrics.csv    – MR touch_rate / coverage_rate (all 214)

Output:
  analysis/rq3_baseline_comparison.csv       – updated table (replaces Pearson values)

Usage:
    python backend/scripts/compute_rq3_spearman.py
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = PROJECT_ROOT / "analysis" / "rq3_baseline_comparison.csv"


# ── Spearman rank correlation (pure Python, no scipy) ─────────────────────────
def _rank(xs: list[float]) -> list[float]:
    n = len(xs)
    indexed = sorted(enumerate(xs), key=lambda t: t[1])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n - 1 and indexed[j + 1][1] == indexed[j][1]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg
        i = j + 1
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    rx, ry = _rank(xs), _rank(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx  = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy  = sum((b - my) ** 2 for b in ry) ** 0.5
    return round(num / (dx * dy), 2) if dx and dy else None


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


# ── Load per-component MR metrics (touch_rate, coverage_rate) ─────────────────
pm: dict[str, dict] = {}
with open(PROJECT_ROOT / "output" / "aggregate" / "per_sample_metrics.csv",
          encoding="utf-8") as f:
    for r in csv.DictReader(f):
        pm[r["sample_id"]] = r

# ── Load runtime coverage: ant-design, mui-material, mui-base-ui ──────────────
rt: dict[str, dict] = {}
with open(PROJECT_ROOT / "output" / "coverage" / "all_runtime_coverage.csv",
          encoding="utf-8") as f:
    for r in csv.DictReader(f):
        try:
            rt[r["sample_id"]] = {
                "stmt":   float(r["stmt_cov"]),
                "branch": float(r["branch_cov"]),
                "lib":    r["lib"],
            }
        except (ValueError, KeyError):
            pass

# ── Load runtime coverage: element-plus ──────────────────────────────────────
with open(PROJECT_ROOT / "output" / "coverage" / "ep_runtime_coverage.csv",
          encoding="utf-8") as f:
    for r in csv.DictReader(f):
        try:
            rt[r["sample_id"]] = {
                "stmt":   float(r["stmt_runtime"]) * 100,
                "branch": float(r["branch_runtime"]) * 100,
                "lib":    "element-plus",
            }
        except (ValueError, KeyError):
            pass

# ── Merge: keep only components with both runtime and MR data ─────────────────
rows: list[dict] = []
for sid, rv in rt.items():
    if sid not in pm:
        continue
    p = pm[sid]
    try:
        touch = float(p.get("touch_rate") or 0) * 100
        cover = float(p.get("coverage_rate") or 0) * 100
    except ValueError:
        continue
    rows.append({
        "lib":    rv["lib"],
        "stmt":   rv["stmt"],
        "branch": rv["branch"],
        "touch":  touch,
        "cover":  cover,
    })

# ── Compute per-library + All summary ─────────────────────────────────────────
LIB_DISPLAY = {
    "ant-design":   "ant-design",
    "element-plus": "element-plus",
    "mui-material": "material-ui",
    "mui-base-ui":  "base-ui",
}

lib_groups: dict[str, list] = defaultdict(list)
for r in rows:
    lib_groups[r["lib"]].append(r)


def _summary(group: list[dict], label: str) -> dict:
    stmt   = [r["stmt"]   for r in group]
    branch = [r["branch"] for r in group]
    touch  = [r["touch"]  for r in group]
    cover  = [r["cover"]  for r in group]
    return {
        "library":        label,
        "n":              len(group),
        "stmt_pct":       round(_mean(stmt),   1),
        "branch_pct":     round(_mean(branch), 1),
        "mr_touch_pct":   round(_mean(touch),  1),
        "mr_cover_pct":   round(_mean(cover),  1),
        "r_stmt_cover":   spearman(stmt, cover),
        "r_branch_cover": spearman(branch, cover),
        "r_stmt_touch":   spearman(stmt, touch),
        "r_branch_touch": spearman(branch, touch),
    }


lib_order = ["ant-design", "element-plus", "mui-material", "mui-base-ui"]
results = [_summary(lib_groups[lib], LIB_DISPLAY[lib])
           for lib in lib_order if lib in lib_groups]
results.append(_summary(rows, "All"))

# ── Write CSV ─────────────────────────────────────────────────────────────────
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
fields = ["library", "n",
          "stmt_pct", "branch_pct", "mr_touch_pct", "mr_cover_pct",
          "r_stmt_cover", "r_branch_cover", "r_stmt_touch", "r_branch_touch"]
with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(results)

# ── Print results ─────────────────────────────────────────────────────────────
print("\nSpearman ρ results for RQ3 table (n=201 with complete runtime data):\n")
hdr = f"{'Library':<15} {'n':>4}  {'Stmt':>5}  {'Br':>5}  {'Touch':>5}  {'Cover':>5}"
hdr += f"  {'ρ(s,Cv)':>8}  {'ρ(b,Cv)':>8}  {'ρ(s,Tc)':>8}  {'ρ(b,Tc)':>8}"
print(hdr)
print("-" * len(hdr))
for r in results:
    print(f"{r['library']:<15} {r['n']:>4}  {r['stmt_pct']:>5.1f}  {r['branch_pct']:>5.1f}  "
          f"{r['mr_touch_pct']:>5.1f}  {r['mr_cover_pct']:>5.1f}  "
          f"{str(r['r_stmt_cover']):>8}  {str(r['r_branch_cover']):>8}  "
          f"{str(r['r_stmt_touch']):>8}  {str(r['r_branch_touch']):>8}")

print(f"\nWritten: {OUT_CSV}")

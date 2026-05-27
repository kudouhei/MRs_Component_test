# UI Component MR Completeness Framework

Analyze whether component library tests cover **metamorphic relations (MRs)** inferred from **source (C)**, **description (D)**, and **category**, with **open bug issues** as an external anchor for ICSE-style evaluation.

## Data layout (`data/test/`)

Each sample: `{id}-{library}-{Category}-{ComponentName}/`

| File | Symbol | Role |
|------|--------|------|
| `source.js` | **C** | Component implementation |
| `test.js` | **T** | Tests |
| `description.txt` | **D** | API/docs description |

**Category** (Inputs, Navigation, Feedback, Data display, Layout) drives category-specific MR focus in Phase 1.

## Five phases

1. **LLM** infers **M(C)** from C + D + category + taxonomy  
2. **Hybrid alignment**: LLM judges T↔MR + local token/assertion evidence → touch / strict coverage  
3. **Completeness** metrics + **blind spots** (by category & MR type)  
4. **Open issues** alignment (RQ3, co-occurrence only)  
5. **Priorities** + **improvement suggestions**

## MR taxonomy

The versioned taxonomy uses six top-level categories:
`input_prop_relations`, `state_event_relations`, `interaction_accessibility_relations`,
`visual_layout_relations`, `composition_context_relations`, and `data_flow_relations`.
They are derived from a UI component behavior model covering props, state/events,
interaction/accessibility, visual layout, composition/context, and data flow.

## Setup

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env   # set DEEPSEEK_API_KEY or OPENAI_API_KEY
```

## Run

```bash
# One component
python3 scripts/run_sample.py 1-mui-material-Inputs-Autocomplete

# Smoke (3 samples)
python3 scripts/run_batch.py --limit 3

# Full corpus (190) — requires API quota
python3 scripts/run_batch.py

# Or merge aggregate after all shards finish:
python3 scripts/merge_batch_reports.py

# Manual slice (alternative to --shard-index):
python3 scripts/run_batch.py --offset 0 --limit 64 --skip-aggregate
python3 scripts/run_batch.py --offset 64 --limit 64 --skip-aggregate
python3 scripts/run_batch.py --offset 128 --skip-aggregate && python3 scripts/merge_batch_reports.py

# Background: progress written to output/batch_progress.txt (human) and .json
nohup python3 scripts/run_batch.py --shard-index 1 --num-shards 3 > output/batch_run_1.log 2>&1 &
tail -f output/batch_progress.txt

# By category (paper stratification)
python3 scripts/run_batch.py --category Inputs --limit 20

# No progress UI
python3 scripts/run_batch.py --quiet

# Ablation: run full/partial batch with GPT-5-mini
python3 scripts/run_batch.py --ablation-model gpt-5-mini
```

## Outputs

- `output/reports/{sample_id}.json` — full report + `improvement_suggestions`
- `output/aggregate/batch_summary.json` — RQ1/RQ2 aggregates (by library/category, weighted rates, blind spot subtypes)
- `output/aggregate/alignment_val.json` — RQ3
- `output/aggregate/per_sample_metrics.csv`
- `output/aggregate/test_priorities.csv` — top component × MR type supplementation priorities
- `output/run_config.json` — frozen provenance
- `output/batch_progress.txt` / `batch_progress.json` — live batch progress (updated per sample)
- `output/analysis/dashboard.html` — 全库统计图表（见下方 analyze 命令）
- `output/analysis/*.csv` — 汇总表（按库、类别、覆盖率区间、盲区类型等）
- `output/analysis/component_analysis.xlsx` — 每组件分析 Excel（组件汇总 / MR明细 / 盲区 / 补测优先级）
- `output/analysis/issue_alignment_charts.html` — issue 对齐显著性图表（分桶 + topic enrichment）
- `output/analysis/issue_alignment_stats.xlsx` — issue 对齐统计工作簿（overview / bins / 检验 / 显著性）

```bash
# 从 output/reports 重新生成统计表与 HTML 仪表盘
python3 scripts/analyze_reports.py

# 计算 statement coverage baseline（静态 proxy），并写回 reports
python3 scripts/compute_statement_coverage_baseline.py --update-reports

# 导出每组件分析 Excel（多工作表）
python3 scripts/export_reports_xlsx.py
# → output/analysis/component_analysis.xlsx

# 导出 issue 对齐统计图表与 xlsx
python3 scripts/export_issue_alignment_artifacts.py
# → output/analysis/issue_alignment_charts.html
# → output/analysis/issue_alignment_stats.xlsx
```

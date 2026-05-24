# UI Component MR Completeness Framework

Five-phase pipeline for measuring how well component tests cover **metamorphic relations (MRs)** inferred from source code, with **open GitHub bug issues** as an external anchor (RQ3).

Requirements: [`require.md`](require.md) · **Development guide:** [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) · Open-issues: [`analysis/open_issues/2026-0510-README.md`](analysis/open_issues/2026-0510-README.md)

## Phases

| Phase | Capability |
|-------|------------|
| **1** | Infer **M(C)** from `source.js` (+ optional LLM) |
| **2** | Align **T** to each MR — touch / strict coverage (`evidence_*`) |
| **3** | Completeness metrics + blind-spot diagnostics |
| **4** | Join open-issue pressure ↔ completeness (Exp1, Exp2, VAL) |
| **5** | Insufficient-attention evidence + **test supplementation priorities** |

## Dataset

- **190** samples under `data/test/{id}-{library}-{category}-{component}/`
- `source.js` → **C**, `test.js` → **T**

## Quick start

```bash
cd backend
export OPENAI_API_KEY=sk-...   # required for default (LLM) path

# Single component
python3 scripts/run_sample.py 1-mui-material-Inputs-Autocomplete

# Smoke batch (first 10)
python3 scripts/run_batch.py --limit 10

# Full corpus (~190 samples, LLM MR inference)
python3 scripts/run_batch.py

# Ablation without API
python3 scripts/run_batch.py --heuristic-ablation --limit 10
```

Outputs:

- Per-sample reports: `output/reports/{sample_id}.json`
- Aggregates (RQ1–RQ2): `output/aggregate/batch_summary.json`, `per_sample_metrics.csv`
- RQ3 alignment: `output/aggregate/alignment_val.json`
- Priorities: `output/aggregate/test_priorities.csv`
- Run provenance: `output/run_config.json`, per-report `provenance` field

Phase 1 defaults to **LLM** inference with frozen prompt/taxonomy versions (`backend/mr_framework/versioning.py`). Use `--heuristic-ablation` only for sensitivity or offline runs.

## Refresh open issues (Phase 4)

```bash
# Set GITHUB_TOKEN in repo-root .env
cd backend
python3 scripts/collect_open_issues.py
python3 scripts/collect_open_issues.py --library mui-material --max-pages 30
```

Writes under `analysis/open_issues/` (already populated in this repo).

## Research questions

- **RQ1**: Mean touch/coverage rates by library and category → `batch_summary.json` → `rq1`
- **RQ2**: Global blind MR types → `rq2.top_blind_mr_types_global`
- **RQ3**: Cross-sectional alignment (not prediction) → `alignment_val.json`

## Layout

```text
backend/mr_framework/   # core engines (phases 1–5, pipeline)
backend/scripts/        # CLI entry points
data/test/              # evaluation samples
analysis/open_issues/   # external anchor corpus I
output/                 # generated reports (gitignored)
```

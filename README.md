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

# By category (paper stratification)
python3 scripts/run_batch.py --category Inputs --limit 20
```

## Outputs

- `output/reports/{sample_id}.json` — full report + `improvement_suggestions`
- `output/aggregate/batch_summary.json` — RQ1/RQ2 aggregates (by library/category, weighted rates, blind spot subtypes)
- `output/aggregate/alignment_val.json` — RQ3
- `output/aggregate/per_sample_metrics.csv`
- `output/aggregate/test_priorities.csv` — top component × MR type supplementation priorities
- `output/run_config.json` — frozen provenance

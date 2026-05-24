# Architecture (one-page)

See full guide: [DEVELOPMENT.md](./DEVELOPMENT.md)

```text
                    ┌──────────────────────────────────────┐
                    │           pipeline.py                 │
                    │  analyze_sample / run_batch           │
                    └──────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
   phase1_inference  phase2_*     phase3_*      phase4/5
   + versioning      local_evidence completeness   alignment
   + taxonomy                         blind        priorities
         │              │
    LLM (default)       └── tests.js + optional source.js fallback
    heuristic ablation
```

**Data flow:** `(C,T,meta) → M(C) → O(T,m) → metrics → (+ issues) → report JSON`

**Frozen artifacts:** `taxonomy.py`, prompt version in `versioning.py`, corpus under `analysis/open_issues/`.

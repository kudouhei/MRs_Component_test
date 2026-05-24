#!/usr/bin/env python3
"""Batch MR completeness analysis over data/test (190 samples)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mr_framework.pipeline import run_batch
from mr_framework.versioning import DEFAULT_LLM_MODEL


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--library", help="Filter: mui-material, ant-design, …")
    p.add_argument("--limit", type=int, help="Max samples (smoke test)")
    p.add_argument("--sample-id", help="Single sample id")
    p.add_argument("--heuristic-ablation", action="store_true", help="Ablation only (no API)")
    p.add_argument("--allow-heuristic-fallback", action="store_true")
    p.add_argument("--model", default=None, help=f"LLM model (default: {DEFAULT_LLM_MODEL})")
    args = p.parse_args()

    mode = "heuristic_ablation" if args.heuristic_ablation else "llm"
    print(json.dumps(
        run_batch(
            library=args.library,
            limit=args.limit,
            sample_id=args.sample_id,
            mr_inference_mode=mode,
            model=args.model,
            allow_heuristic_fallback=args.allow_heuristic_fallback,
        ),
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

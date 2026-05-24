#!/usr/bin/env python3
"""Analyze a single data/test sample through the five-phase pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mr_framework.pipeline import analyze_sample, save_report
from mr_framework.samples import iter_samples
from mr_framework.versioning import DEFAULT_LLM_MODEL


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("sample_id", help="e.g. 1-mui-material-Inputs-Autocomplete")
    p.add_argument("--heuristic-ablation", action="store_true")
    p.add_argument("--allow-heuristic-fallback", action="store_true")
    p.add_argument("--model", default=None)
    p.add_argument("--no-save", action="store_true")
    args = p.parse_args()

    meta = next(iter_samples(sample_id=args.sample_id), None)
    if not meta:
        print(f"Unknown sample: {args.sample_id}", file=sys.stderr)
        return 1

    mode = "heuristic_ablation" if args.heuristic_ablation else "llm"
    report = analyze_sample(
        meta,
        mr_inference_mode=mode,
        model=args.model,
        allow_heuristic_fallback=args.allow_heuristic_fallback,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    if not args.no_save:
        print(f"\nSaved → {save_report(report)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

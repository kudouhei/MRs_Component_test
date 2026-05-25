#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mr_framework.pipeline import analyze_sample, save_report
from mr_framework.samples import iter_samples
from mr_framework.llm_client import DEFAULT_LLM_MODEL


def main() -> int:
    p = argparse.ArgumentParser(description="MR completeness analysis for one sample")
    p.add_argument("sample_id")
    p.add_argument("--model", default=None)
    p.add_argument("--no-save", action="store_true")
    args = p.parse_args()

    meta = next(iter_samples(sample_id=args.sample_id), None)
    if not meta:
        print(f"Unknown sample: {args.sample_id}", file=sys.stderr)
        return 1

    report = analyze_sample(
        meta,
        model=args.model or DEFAULT_LLM_MODEL,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    if not args.no_save:
        print(f"\nSaved → {save_report(report)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

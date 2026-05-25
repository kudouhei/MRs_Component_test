#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mr_framework.pipeline import run_batch
from mr_framework.llm_client import DEFAULT_LLM_MODEL


def main() -> int:
    p = argparse.ArgumentParser(description="Batch MR completeness (190 samples)")
    p.add_argument("--library")
    p.add_argument("--category", help="Inputs | Navigation | Feedback | Data display | Layout")
    p.add_argument("--limit", type=int)
    p.add_argument("--sample-id")
    p.add_argument("--model", default=None)
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Disable progress bar and output/batch_progress.* files",
    )
    args = p.parse_args()

    if not args.quiet:
        print(
            "Progress: stderr (live) + output/batch_progress.txt (tail -f) + batch_progress.json",
            file=sys.stderr,
        )

    result = run_batch(
        library=args.library,
        category=args.category,
        limit=args.limit,
        sample_id=args.sample_id,
        model=args.model,
        show_progress=not args.quiet,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

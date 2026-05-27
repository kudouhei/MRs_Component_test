#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mr_framework.pipeline import output_root_for_model, run_batch
from mr_framework.llm_client import ABLATION_MODEL_CHOICES, resolve_model_name
from mr_framework.samples import describe_shards, list_sample_metas, shard_bounds


def main() -> int:
    p = argparse.ArgumentParser(description="Batch MR completeness (190 samples)")
    p.add_argument("--library")
    p.add_argument("--category", help="Inputs | Navigation | Feedback | Data display | Layout")
    p.add_argument("--limit", type=int)
    p.add_argument("--offset", type=int, default=0, help="Skip first N samples (after shard slice)")
    p.add_argument(
        "--shard-index",
        type=int,
        metavar="K",
        help="Run shard K of N (1-based). Use with --num-shards, e.g. 1/3 2/3 3/3",
    )
    p.add_argument(
        "--num-shards",
        type=int,
        metavar="N",
        help="Split corpus into N shards (fair split by sorted sample id)",
    )
    p.add_argument(
        "--describe-shards",
        action="store_true",
        help="Print shard plan for --num-shards and exit (no API calls)",
    )
    p.add_argument("--sample-id")
    p.add_argument("--model", default=None)
    p.add_argument(
        "--ablation-model",
        choices=ABLATION_MODEL_CHOICES,
        default=None,
        help="Use a fixed model preset for ablation (overrides --model)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Disable progress bar and output/batch_progress.* files",
    )
    p.add_argument(
        "--skip-aggregate",
        action="store_true",
        help="Only write per-sample reports; skip shard-local batch_summary",
    )
    p.add_argument(
        "--merge-reports",
        action="store_true",
        help="After this run, rebuild aggregate from ALL output/reports/*.json",
    )
    p.add_argument(
        "--separate-by-model",
        action="store_true",
        help="Write outputs to output/model_runs/<model>/",
    )
    args = p.parse_args()

    if args.describe_shards:
        n = args.num_shards or 3
        total = len(list_sample_metas(library=args.library, category=args.category))
        plan = describe_shards(total, n)
        print(json.dumps({"corpus_total": total, "num_shards": n, "shards": plan}, ensure_ascii=False, indent=2))
        return 0

    if (args.shard_index is None) != (args.num_shards is None):
        print("error: --shard-index and --num-shards must be used together", file=sys.stderr)
        return 2

    model_name = resolve_model_name(args.model, args.ablation_model)
    separate = args.separate_by_model or bool(args.ablation_model)

    if not args.quiet:
        out_root = output_root_for_model(model_name, separate_by_model=separate)
        print(
            f"Progress: stderr (live) + {out_root}/batch_progress.txt (tail -f) + batch_progress.json",
            file=sys.stderr,
        )
        if args.shard_index and args.num_shards:
            total = len(list_sample_metas(library=args.library, category=args.category))
            start, end = shard_bounds(total, args.shard_index, args.num_shards)
            print(
                f"Shard {args.shard_index}/{args.num_shards}: samples {start + 1}-{end} of {total} ({end - start} items)",
                file=sys.stderr,
            )

    result = run_batch(
        library=args.library,
        category=args.category,
        limit=args.limit,
        offset=args.offset,
        shard_index=args.shard_index,
        num_shards=args.num_shards,
        sample_id=args.sample_id,
        model=model_name,
        show_progress=not args.quiet,
        skip_aggregate=args.skip_aggregate,
        merge_reports_after=args.merge_reports,
        separate_by_model=separate,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Rebuild output/aggregate/* from all per-sample JSON reports on disk."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mr_framework.pipeline import merge_aggregate_from_reports


def main() -> int:
    p = argparse.ArgumentParser(description="Merge all output/reports/*.json into aggregate")
    p.add_argument("--model", default=None)
    p.add_argument("--separate-by-model", action="store_true")
    args = p.parse_args()
    result = merge_aggregate_from_reports(
        model=args.model,
        separate_by_model=args.separate_by_model,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mr_framework.pipeline import analyze_sample, output_root_for_model, save_report
from mr_framework.samples import iter_samples
from mr_framework.llm_client import ABLATION_MODEL_CHOICES, DEFAULT_LLM_MODEL, resolve_model_name


def main() -> int:
    p = argparse.ArgumentParser(description="MR completeness analysis for one sample")
    p.add_argument("sample_id")
    p.add_argument("--model", default=None)
    p.add_argument(
        "--ablation-model",
        choices=ABLATION_MODEL_CHOICES,
        default=None,
        help="Use a fixed model preset for ablation (overrides --model)",
    )
    p.add_argument(
        "--separate-by-model",
        action="store_true",
        help="Save report under output/model_runs/<model>/reports/",
    )
    p.add_argument("--no-save", action="store_true")
    args = p.parse_args()

    meta = next(iter_samples(sample_id=args.sample_id), None)
    if not meta:
        print(f"Unknown sample: {args.sample_id}", file=sys.stderr)
        return 1

    model_name = resolve_model_name(args.model, args.ablation_model)
    report = analyze_sample(
        meta,
        model=model_name or DEFAULT_LLM_MODEL,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    if not args.no_save:
        separate = args.separate_by_model or bool(args.ablation_model)
        out_root = output_root_for_model(model_name, separate_by_model=separate)
        reports_dir = out_root / "reports"
        print(
            f"\nSaved → {save_report(report, reports_dir=reports_dir, model=model_name)}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

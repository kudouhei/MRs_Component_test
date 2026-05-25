#!/usr/bin/env python3
"""Evaluate system MR alignment against human annotation CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable


def _bool_cell(value: str) -> bool | None:
    v = (value or "").strip().lower()
    if v in {"1", "true", "t", "yes", "y"}:
        return True
    if v in {"0", "false", "f", "no", "n"}:
        return False
    return None


def _metrics(pairs: Iterable[tuple[bool, bool]]) -> dict[str, float | int | None]:
    vals = list(pairs)
    if not vals:
        return {"n": 0}
    tp = sum(1 for sys_v, hum_v in vals if sys_v and hum_v)
    tn = sum(1 for sys_v, hum_v in vals if not sys_v and not hum_v)
    fp = sum(1 for sys_v, hum_v in vals if sys_v and not hum_v)
    fn = sum(1 for sys_v, hum_v in vals if not sys_v and hum_v)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (2 * precision * recall / (precision + recall)) if precision and recall else None
    accuracy = (tp + tn) / len(vals)
    kappa = _cohen_kappa(tp, tn, fp, fn)
    return {
        "n": len(vals),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 6) if precision is not None else None,
        "recall": round(recall, 6) if recall is not None else None,
        "f1": round(f1, 6) if f1 is not None else None,
        "accuracy": round(accuracy, 6),
        "cohen_kappa": round(kappa, 6) if kappa is not None else None,
    }


def _cohen_kappa(tp: int, tn: int, fp: int, fn: int) -> float | None:
    n = tp + tn + fp + fn
    if n == 0:
        return None
    po = (tp + tn) / n
    sys_pos = (tp + fp) / n
    sys_neg = (tn + fn) / n
    hum_pos = (tp + fn) / n
    hum_neg = (tn + fp) / n
    pe = sys_pos * hum_pos + sys_neg * hum_neg
    if pe == 1:
        return None
    return (po - pe) / (1 - pe)


def main() -> int:
    p = argparse.ArgumentParser(description="Evaluate MR alignment annotations")
    p.add_argument("annotation_csv")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    touched_pairs: list[tuple[bool, bool]] = []
    covered_pairs: list[tuple[bool, bool]] = []
    valid_mr_pairs: list[tuple[bool, bool]] = []
    skipped = 0

    with Path(args.annotation_csv).open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            valid = _bool_cell(row.get("human_valid_mr", ""))
            ht = _bool_cell(row.get("human_touched", ""))
            hc = _bool_cell(row.get("human_covered", ""))
            st = _bool_cell(row.get("system_touched", ""))
            sc = _bool_cell(row.get("system_covered", ""))
            if valid is not None:
                valid_mr_pairs.append((True, valid))
            if valid is False:
                continue
            if ht is not None and st is not None:
                touched_pairs.append((st, ht))
            else:
                skipped += 1
            if hc is not None and sc is not None:
                covered_pairs.append((sc, hc))

    result = {
        "input": args.annotation_csv,
        "skipped_unlabeled_touched": skipped,
        "mr_validity_precision": _metrics(valid_mr_pairs),
        "touched_alignment": _metrics(touched_pairs),
        "strict_coverage_alignment": _metrics(covered_pairs),
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

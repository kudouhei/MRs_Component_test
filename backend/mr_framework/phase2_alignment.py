"""Phase 2 — Test–MR alignment O(T, m)."""

from __future__ import annotations

from typing import Any

from .local_evidence import apply_local_evidence_mr_coverage
from .models import MetamorphicRelation, SampleMeta


def align_tests_to_mrs(
    mrs: list[MetamorphicRelation],
    mr_coverage: list[dict[str, Any]],
    *,
    tests: str,
    code: str,
    meta: SampleMeta,
) -> list[dict[str, Any]]:
    apply_local_evidence_mr_coverage(
        mrs=mrs,
        mr_coverage=mr_coverage,
        tests=tests,
        scenario=meta.scenario,
        code_alignment_fallback=code if not (tests or "").strip() else None,
    )
    return mr_coverage

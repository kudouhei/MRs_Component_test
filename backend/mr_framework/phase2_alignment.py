"""Phase 2 orchestration: hybrid local evidence + LLM alignment."""

from __future__ import annotations

from typing import Any

from .local_evidence import apply_local_evidence_mr_coverage
from .models import MetamorphicRelation, SampleMeta
from .phase2_llm_alignment import align_tests_with_llm

def align_tests_to_mrs(
    mrs: list[MetamorphicRelation],
    mr_coverage: list[dict[str, Any]],
    *,
    tests: str,
    code: str,
    meta: SampleMeta,
    llm_model: str | None = None,
) -> list[dict[str, Any]]:
    mr_coverage, llm_err = align_tests_with_llm(
        mrs, mr_coverage, tests=tests, meta=meta, model=llm_model
    )
    apply_local_evidence_mr_coverage(
        mrs=mrs,
        mr_coverage=mr_coverage,
        tests=tests,
        code_alignment_fallback=code if not tests.strip() else None,
    )

    for it in mr_coverage:
        ev_touch = bool(it.get("evidence_touch"))
        ev_cov = bool(it.get("evidence_covered"))
        llm_touch = bool(it.get("llm_touched"))
        llm_cov = bool(it.get("llm_covered"))
        it["touched"] = ev_touch or llm_touch
        it["covered"] = ev_cov or llm_cov
        it["hybrid_touched"] = it["touched"]
        it["strict_covered"] = it["covered"]

    if llm_err:
        for it in mr_coverage:
            note = f"llm_alignment_note: {llm_err}"
            it["reason"] = f"{it.get('reason', '')} {note}".strip()
    return mr_coverage

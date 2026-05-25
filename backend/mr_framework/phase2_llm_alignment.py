"""Phase 2: LLM judges T vs each MR in M(C)."""

from __future__ import annotations

from typing import Any

from .llm_client import DEFAULT_LLM_MODEL, DEFAULT_LLM_TEMPERATURE, chat_json, resolve_api_key
from .models import MetamorphicRelation, SampleMeta
from .versioning import MR_ALIGNMENT_PROMPT_VERSION

def _brief_mrs(mrs: list[MetamorphicRelation], limit: int = 40) -> list[dict[str, Any]]:
    out = []
    for m in mrs[:limit]:
        out.append(
            {
                "mr_id": m.id,
                "relation_type": m.relation_type,
                "type_category": m.type_category,
                "description": m.description[:300],
                "expected_relation": m.expected_relation[:300],
            }
        )
    return out


def align_tests_with_llm(
    mrs: list[MetamorphicRelation],
    mr_coverage: list[dict[str, Any]],
    *,
    tests: str,
    meta: SampleMeta,
    model: str | None = None,
    temperature: float = DEFAULT_LLM_TEMPERATURE,
) -> tuple[list[dict[str, Any]], str | None]:
    if not resolve_api_key():
        return mr_coverage, "no API key for LLM alignment"
    if not (tests or "").strip():
        return mr_coverage, "empty tests"
    tests_trunc = tests[:20000]
    import json

    user = f"""Component: {meta.component_name} ({meta.library}, category={meta.category})
For each MR, judge whether existing tests TOUCH or STRICTLY COVER it.

Definitions:
- touched: tests reference or exercise the behavior (even weakly).
- covered (strict): tests contain assertions that verify the MR invariant.

Tests T (truncated):
```javascript
{tests_trunc}
```

MRs:
{json.dumps(_brief_mrs(mrs), ensure_ascii=False, indent=2)}

Return JSON:
{{ "mr_coverage": [
  {{ "mr_id": "...", "touched": true/false, "covered": true/false,
     "confidence": 0-1, "reason": "cite test lines/patterns", "related_tests": ["describe/it title"] }}
]}}
Every MR must appear exactly once."""
    try:
        raw = chat_json(
            messages=[
                {
                    "role": "system",
                    "content": "You output only JSON for metamorphic test coverage assessment.",
                },
                {"role": "user", "content": user},
            ],
            model=model or DEFAULT_LLM_MODEL,
            temperature=temperature,
            max_tokens=12288,
        )
    except Exception as exc:  # noqa: BLE001
        return mr_coverage, str(exc)

    rows = raw.get("mr_coverage") or []
    by_id = {r.get("mr_id"): r for r in rows if isinstance(r, dict) and r.get("mr_id")}
    for it in mr_coverage:
        mid = it.get("mr_id")
        llm_row = by_id.get(mid)
        if not llm_row:
            continue
        it["llm_touched"] = bool(llm_row.get("touched"))
        it["llm_covered"] = bool(llm_row.get("covered"))
        it["llm_confidence"] = float(llm_row.get("confidence") or 0.0)
        it["reason"] = str(llm_row.get("reason") or it.get("reason") or "")
        it["related_tests"] = llm_row.get("related_tests") or []
        methods = it.get("alignment_method") or []
        if "llm_alignment" not in methods:
            methods.append("llm_alignment")
        it["alignment_method"] = methods
        if it["llm_covered"]:
            it["covered"] = True
        if it["llm_touched"]:
            it["touched"] = True
    return mr_coverage, None

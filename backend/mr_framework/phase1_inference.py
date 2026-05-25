"""Phase 1: infer M(C) from source C + description D + category."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .category_guidance import category_focus_text
from .llm_client import DEFAULT_LLM_MODEL, DEFAULT_LLM_TEMPERATURE, chat_json, resolve_api_key
from .models import MetamorphicRelation, SampleMeta
from .taxonomy import (
    RELATION_TYPE_CATEGORIES,
    RELATION_TYPE_TO_CATEGORY,
    normalize_type_category,
)
from .versioning import MR_INFERENCE_PROMPT_VERSION, TAXONOMY_VERSION, taxonomy_fingerprint

_COMPONENT_RE = re.compile(r"\b(?:const|function)\s+([A-Z][A-Za-z0-9_]*)\b")


@dataclass
class MrInferenceResult:
    mrs: list[MetamorphicRelation]
    mode: str
    llm_model: str
    llm_temperature: float
    prompt_version: str
    taxonomy_version: str
    taxonomy_fingerprint: str
    fallback_reason: str | None = None


def _component_name(code: str, fallback: str) -> str:
    for m in _COMPONENT_RE.finditer(code or ""):
        n = m.group(1)
        if n not in {"React", "PropTypes", "Component", "Fragment"}:
            return n
    return fallback


def _normalize_type(rt: str) -> tuple[str, str]:
    key = rt.strip().lower().replace("-", "_").replace(" ", "_")
    if key in RELATION_TYPE_TO_CATEGORY:
        return key, RELATION_TYPE_TO_CATEGORY[key]
    aliases = {
        "equivalence": "type_equivalence",
        "visual_consistency": "state_visual_mapping",
        "state_consistency": "state_synchronization",
    }
    if key in aliases:
        k = aliases[key]
        return k, RELATION_TYPE_TO_CATEGORY[k]
    return key, "input_prop_relations"


def _build_phase1_messages(
    *,
    code: str,
    description: str,
    meta: SampleMeta,
) -> list[dict[str, str]]:
    types_lines = []
    for cat, types in RELATION_TYPE_CATEGORIES.items():
        types_lines.append(f"  {cat}: {', '.join(sorted(types.keys()))}")
    desc_block = (description or "(no description file)")[:12000]
    code_block = (code or "")[:14000]
    focus = category_focus_text(meta.category)
    system = (
        "You are an expert in UI component testing and metamorphic relations (MRs). "
        "Infer component-specific MRs from source code AND API/description docs. "
        "Use relation_type from the taxonomy (snake_case). "
        "Account for the component CATEGORY — different categories imply different MR priorities. "
        "Output ONLY valid JSON."
    )
    user = f"""Component: {meta.component_name}
Library: {meta.library}
Category: {meta.category}
Category-specific focus: {focus}
Taxonomy version: {TAXONOMY_VERSION}

Allowed relation_type by type_category:
{chr(10).join(types_lines)}

Return JSON:
{{ "relations": [
  {{ "relation_type": "...", "type_category": "...", "description": "...",
     "expected_relation": "...", "confidence": 0.0-1.0 }}
]}}

Rules:
- Use BOTH source code and description; MRs must be justified by C and/or D.
- Typical count 8–20 depending on complexity; do NOT list the entire taxonomy.
- Each relation_type at most once; be specific to this component and category.

=== Description D ===
{desc_block}

=== Source C ===
```javascript
{code_block}
```
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def infer_mrs_llm(
    code: str,
    description: str,
    meta: SampleMeta,
    *,
    model: str,
    temperature: float,
) -> tuple[list[MetamorphicRelation] | None, str | None]:
    if not resolve_api_key():
        return None, "API key not set (OPENAI_API_KEY or DEEPSEEK_API_KEY)"
    try:
        raw = chat_json(
            messages=_build_phase1_messages(code=code, description=description, meta=meta),
            model=model,
            temperature=temperature,
        )
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
    relations = raw.get("relations") or raw.get("metamorphic_relations") or []
    if not isinstance(relations, list) or not relations:
        return None, "empty relations"
    component = _component_name(code, meta.component_name)
    mrs: list[MetamorphicRelation] = []
    seen: set[str] = set()
    for i, r in enumerate(relations):
        if not isinstance(r, dict):
            continue
        rt_raw = str(r.get("relation_type") or "").strip()
        if not rt_raw:
            continue
        rt, cat = _normalize_type(rt_raw)
        if rt in seen:
            continue
        seen.add(rt)
        cat = normalize_type_category(str(r.get("type_category") or cat), rt)
        mrs.append(
            MetamorphicRelation(
                id=f"mr:{meta.sample_id}:llm:{i+1}:{rt}",
                component=component,
                relation_type=rt,
                type_category=cat,
                description=str(r.get("description") or rt),
                expected_relation=str(
                    r.get("expected_relation") or "Invariant under stated input/state transformation."
                ),
                confidence=float(r.get("confidence") or 0.72),
                source="llm",
                category_context=meta.category,
            )
        )
    return (mrs, None) if mrs else (None, "no valid MR objects")


def infer_mrs(
    code: str,
    description: str,
    meta: SampleMeta,
    *,
    model: str | None = None,
    temperature: float = DEFAULT_LLM_TEMPERATURE,
) -> MrInferenceResult:
    model = model or DEFAULT_LLM_MODEL
    base = dict(
        llm_model=model,
        llm_temperature=temperature,
        prompt_version=MR_INFERENCE_PROMPT_VERSION,
        taxonomy_version=TAXONOMY_VERSION,
        taxonomy_fingerprint=taxonomy_fingerprint(),
    )
    mrs, err = infer_mrs_llm(code, description, meta, model=model, temperature=temperature)
    if mrs:
        return MrInferenceResult(mrs=mrs, mode="llm", fallback_reason=None, **base)
    raise RuntimeError(f"LLM MR inference failed for {meta.sample_id}: {err}")


def mrs_to_coverage_skeleton(mrs: list[MetamorphicRelation]) -> list[dict[str, Any]]:
    return [
        {
            "mr_id": m.id,
            "relation_type": m.relation_type,
            "type_category": m.type_category,
            "mr_description": m.description,
            "expected_relation": m.expected_relation,
            "mr_confidence": m.confidence,
            "covered": False,
            "evidence_touch": False,
            "evidence_covered": False,
            "llm_covered": False,
            "llm_touched": False,
            "touched": False,
            "confidence": 0.0,
            "reason": "",
            "alignment_method": [],
        }
        for m in mrs
    ]

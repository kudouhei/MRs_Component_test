"""Phase 1 — MR space construction: infer M(C) from component source."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Literal

from .models import MetamorphicRelation, SampleMeta
from .taxonomy import (
    CODE_PATTERN_HINTS,
    RELATION_TYPE_CATEGORIES,
    RELATION_TYPE_TO_CATEGORY,
)
from .versioning import (
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_TEMPERATURE,
    MR_INFERENCE_PROMPT_VERSION,
    TAXONOMY_VERSION,
    build_mr_inference_system_prompt,
    build_mr_inference_user_prompt,
    prompt_fingerprint,
    taxonomy_fingerprint,
)

_COMPONENT_RE = re.compile(
    r"\b(?:const|function)\s+([A-Z][A-Za-z0-9_]*)\b"
)

MrInferenceMode = Literal["llm", "heuristic_ablation"]


@dataclass
class MrInferenceResult:
    mrs: list[MetamorphicRelation]
    mode: MrInferenceMode
    llm_model: str
    llm_temperature: float
    prompt_version: str
    prompt_fingerprint: str
    taxonomy_version: str
    taxonomy_fingerprint: str
    fallback_reason: str | None = None

    def provenance_dict(self) -> dict[str, Any]:
        return {
            "mr_inference_mode": self.mode,
            "llm_model": self.llm_model,
            "llm_temperature": self.llm_temperature,
            "prompt_version": self.prompt_version,
            "prompt_fingerprint": self.prompt_fingerprint,
            "taxonomy_version": self.taxonomy_version,
            "taxonomy_fingerprint": self.taxonomy_fingerprint,
            "llm_fallback_reason": self.fallback_reason,
        }


def _extract_component_name(code: str, fallback: str) -> str:
    for m in _COMPONENT_RE.finditer(code or ""):
        name = m.group(1)
        if name not in {"React", "PropTypes", "Component", "Fragment"}:
            return name
    return fallback


def _normalize_relation_type(rt: str) -> tuple[str, str]:
    key = rt.strip().lower().replace("-", "_").replace(" ", "_")
    if key in RELATION_TYPE_TO_CATEGORY:
        return key, RELATION_TYPE_TO_CATEGORY[key]
    aliases = {
        "equivalence": "type_equivalence",
        "boundary": "boundary_preservation",
        "visual_consistency": "state_visual_mapping",
        "state_consistency": "state_synchronization",
        "order_independence": "event_order",
    }
    if key in aliases:
        k2 = aliases[key]
        return k2, RELATION_TYPE_TO_CATEGORY[k2]
    return key, "input_property_relations"


def infer_mrs_from_code_heuristic(code: str, meta: SampleMeta) -> list[MetamorphicRelation]:
    """Ablation-only: pattern hits, no taxonomy fill-up."""
    component = _extract_component_name(code, meta.component_name)
    code_l = (code or "").lower()
    selected: dict[str, str] = {}
    for patterns, relation_types in CODE_PATTERN_HINTS:
        if any(p in code_l for p in patterns):
            for rt in relation_types:
                if rt not in selected:
                    cat = RELATION_TYPE_TO_CATEGORY.get(rt, "input_property_relations")
                    selected[rt] = RELATION_TYPE_CATEGORIES.get(cat, {}).get(rt, rt)
    if not selected:
        selected["type_equivalence"] = RELATION_TYPE_CATEGORIES["input_property_relations"][
            "type_equivalence"
        ]
    mrs: list[MetamorphicRelation] = []
    for i, (rt, desc) in enumerate(sorted(selected.items())):
        cat = RELATION_TYPE_TO_CATEGORY.get(rt, "input_property_relations")
        mrs.append(
            MetamorphicRelation(
                id=f"mr:{meta.sample_id}:heur:{i+1}:{rt}",
                component=component,
                relation_type=rt,
                type_category=cat,
                description=desc,
                expected_relation=f"Pattern-triggered heuristic MR for {rt}: {desc}",
                confidence=0.5,
                source="heuristic_ablation",
            )
        )
    return mrs


def infer_mrs_llm(
    code: str,
    meta: SampleMeta,
    *,
    model: str,
    temperature: float = DEFAULT_LLM_TEMPERATURE,
) -> tuple[list[MetamorphicRelation] | None, str | None]:
    try:
        from openai import OpenAI
    except ImportError:
        return None, "openai package not installed (pip install openai)"
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None, "OPENAI_API_KEY not set"
    base_url = os.environ.get("OPENAI_BASE_URL")
    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    user_prompt = build_mr_inference_user_prompt(
        code=code,
        component_name=meta.component_name,
        library=meta.library,
        category=meta.category,
        taxonomy_types=RELATION_TYPE_CATEGORIES,
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": build_mr_inference_system_prompt()},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        raw = json.loads(resp.choices[0].message.content or "{}")
    except Exception as exc:  # noqa: BLE001
        return None, f"LLM call failed: {exc}"
    relations = raw.get("relations") or raw.get("metamorphic_relations") or []
    if not isinstance(relations, list) or not relations:
        return None, "LLM returned empty relations list"
    component = _extract_component_name(code, meta.component_name)
    mrs: list[MetamorphicRelation] = []
    seen_types: set[str] = set()
    for i, r in enumerate(relations):
        if not isinstance(r, dict):
            continue
        rt_raw = str(r.get("relation_type") or r.get("category") or "").strip()
        if not rt_raw:
            continue
        rt, cat = _normalize_relation_type(rt_raw)
        if rt in seen_types:
            continue
        seen_types.add(rt)
        if r.get("type_category"):
            cat = str(r.get("type_category")).strip()
        mrs.append(
            MetamorphicRelation(
                id=f"mr:{meta.sample_id}:llm:{i+1}:{rt}",
                component=component,
                relation_type=rt,
                type_category=cat,
                description=str(r.get("description") or rt),
                expected_relation=str(
                    r.get("expected_relation")
                    or "Observable behavior remains invariant under the stated transformation."
                ),
                confidence=float(r.get("confidence") or 0.72),
                source="llm",
            )
        )
    if not mrs:
        return None, "LLM JSON had no valid relation objects"
    return mrs, None


def infer_mrs(
    code: str,
    meta: SampleMeta,
    *,
    mode: MrInferenceMode = "llm",
    model: str | None = None,
    temperature: float = DEFAULT_LLM_TEMPERATURE,
    allow_heuristic_fallback: bool = False,
) -> MrInferenceResult:
    model = model or DEFAULT_LLM_MODEL
    pf = prompt_fingerprint(
        code=code,
        component_name=meta.component_name,
        library=meta.library,
        category=meta.category,
    )
    tf = taxonomy_fingerprint()
    base = dict(
        llm_model=model,
        llm_temperature=temperature,
        prompt_version=MR_INFERENCE_PROMPT_VERSION,
        prompt_fingerprint=pf,
        taxonomy_version=TAXONOMY_VERSION,
        taxonomy_fingerprint=tf,
    )
    if mode == "heuristic_ablation":
        return MrInferenceResult(
            mrs=infer_mrs_from_code_heuristic(code, meta),
            mode="heuristic_ablation",
            fallback_reason="explicit ablation mode",
            **base,
        )
    llm_mrs, err = infer_mrs_llm(code, meta, model=model, temperature=temperature)
    if llm_mrs:
        return MrInferenceResult(mrs=llm_mrs, mode="llm", fallback_reason=None, **base)
    if allow_heuristic_fallback:
        return MrInferenceResult(
            mrs=infer_mrs_from_code_heuristic(code, meta),
            mode="heuristic_ablation",
            fallback_reason=err or "unknown LLM failure",
            **base,
        )
    raise RuntimeError(
        f"LLM MR inference failed for {meta.sample_id}: {err}. "
        "Set OPENAI_API_KEY, or run with --heuristic-ablation / --allow-heuristic-fallback."
    )


def mrs_to_coverage_skeleton(mrs: list[MetamorphicRelation]) -> list[dict[str, Any]]:
    return [
        {
            "mr_id": mr.id,
            "relation_type": mr.relation_type,
            "type_category": mr.type_category,
            "covered": False,
            "confidence": 0.0,
            "reason": "",
        }
        for mr in mrs
    ]

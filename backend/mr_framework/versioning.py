"""Frozen provenance for ICSE-style reproducibility (taxonomy, prompts, run config)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

FRAMEWORK_VERSION = "0.2.0"
TAXONOMY_VERSION = "1.0.0"
MR_INFERENCE_PROMPT_VERSION = "icse-phase1-v1"
DEFAULT_LLM_MODEL = os.environ.get("LLM_MODEL_NAME") or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
DEFAULT_LLM_TEMPERATURE = 0.2

_TAXONOMY_PATH = Path(__file__).resolve().parent / "taxonomy.py"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def taxonomy_fingerprint() -> str:
    return file_sha256(_TAXONOMY_PATH)[:16]


def build_mr_inference_system_prompt() -> str:
    return (
        "You are an expert in UI component testing and metamorphic relations (MRs). "
        "Given component source code, list concrete behavioral invariants as MRs. "
        "Each MR must use relation_type from the provided taxonomy (snake_case). "
        "type_category must be one of the five top-level taxonomy keys. "
        "Output ONLY valid JSON."
    )


def build_mr_inference_user_prompt(
    *,
    code: str,
    component_name: str,
    library: str,
    category: str,
    taxonomy_types: dict[str, dict[str, str]],
) -> str:
    lines = [
        f"Component: {component_name}",
        f"Library: {library}",
        f"Category: {category}",
        f"Taxonomy version: {TAXONOMY_VERSION}",
        "",
        "Allowed relation_type values (grouped by type_category):",
    ]
    for cat, types in taxonomy_types.items():
        lines.append(f"  {cat}: {', '.join(sorted(types.keys()))}")
    lines.extend(
        [
            "",
            "Return JSON:",
            '{ "relations": [',
            "  {",
            '    "relation_type": "<taxonomy snake_case>",',
            '    "type_category": "<one of five categories>",',
            '    "description": "<component-specific MR, 1-2 sentences>",',
            '    "expected_relation": "<observable invariant under transformation>",',
            '    "confidence": 0.0-1.0',
            "  }",
            "] }",
            "",
            "Rules:",
            "- Propose only MRs justified by this source (props, state, events, a11y, composition, data flow).",
            "- Do NOT enumerate the full taxonomy; typical count is 8–20 MRs depending on complexity.",
            "- Each relation_type must appear at most once.",
            "- Prefer specific MRs over generic placeholders.",
            "",
            "Source (truncated):",
            f"```javascript\n{(code or '')[:14000]}\n```",
        ]
    )
    return "\n".join(lines)


def prompt_fingerprint(*, code: str, component_name: str, library: str, category: str) -> str:
    from .taxonomy import RELATION_TYPE_CATEGORIES

    user = build_mr_inference_user_prompt(
        code=code,
        component_name=component_name,
        library=library,
        category=category,
        taxonomy_types=RELATION_TYPE_CATEGORIES,
    )
    blob = (
        f"{MR_INFERENCE_PROMPT_VERSION}\n"
        f"{TAXONOMY_VERSION}\n"
        f"{taxonomy_fingerprint()}\n"
        f"{build_mr_inference_system_prompt()}\n"
        f"{user[:2000]}\n"
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def build_run_provenance(
    *,
    mr_inference_mode: str,
    llm_model: str,
    llm_temperature: float,
    prompt_version: str,
    prompt_fingerprint: str,
    taxonomy_version: str,
    taxonomy_fingerprint: str,
    llm_fallback_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "framework_version": FRAMEWORK_VERSION,
        "mr_inference_mode": mr_inference_mode,
        "llm_model": llm_model,
        "llm_temperature": llm_temperature,
        "prompt_version": prompt_version,
        "prompt_fingerprint": prompt_fingerprint,
        "taxonomy_version": taxonomy_version,
        "taxonomy_fingerprint": taxonomy_fingerprint,
        "llm_fallback_reason": llm_fallback_reason,
    }


def default_run_config(**overrides: Any) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "framework_version": FRAMEWORK_VERSION,
        "default_mr_inference_mode": "llm",
        "default_llm_model": DEFAULT_LLM_MODEL,
        "default_llm_temperature": DEFAULT_LLM_TEMPERATURE,
        "taxonomy_version": TAXONOMY_VERSION,
        "taxonomy_fingerprint": taxonomy_fingerprint(),
        "mr_inference_prompt_version": MR_INFERENCE_PROMPT_VERSION,
    }
    cfg.update(overrides)
    return cfg


def write_run_config(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

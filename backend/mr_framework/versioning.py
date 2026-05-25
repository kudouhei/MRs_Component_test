"""Frozen provenance for reproducibility."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .llm_client import DEFAULT_LLM_MODEL, DEFAULT_LLM_TEMPERATURE
from .taxonomy import TAXONOMY_VERSION

FRAMEWORK_VERSION = "0.3.0"
MR_INFERENCE_PROMPT_VERSION = "icse-phase1-cd-v1"
MR_ALIGNMENT_PROMPT_VERSION = "icse-phase2-align-v1"
_TAXONOMY_PATH = Path(__file__).resolve().parent / "taxonomy.py"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def taxonomy_fingerprint() -> str:
    return file_sha256(_TAXONOMY_PATH)[:16]


def build_run_provenance(**fields: Any) -> dict[str, Any]:
    base = {
        "framework_version": FRAMEWORK_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "taxonomy_fingerprint": taxonomy_fingerprint(),
        "mr_inference_prompt_version": MR_INFERENCE_PROMPT_VERSION,
        "mr_alignment_prompt_version": MR_ALIGNMENT_PROMPT_VERSION,
        "default_llm_model": DEFAULT_LLM_MODEL,
        "default_llm_temperature": DEFAULT_LLM_TEMPERATURE,
    }
    base.update(fields)
    return base


def write_run_config(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

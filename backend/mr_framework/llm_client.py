"""OpenAI-compatible LLM client (OpenAI, DeepSeek, etc.)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_ENV_LOADED = False


def _load_dotenv_once() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv_once()

DEFAULT_LLM_MODEL = (
    os.environ.get("LLM_MODEL_NAME")
    or os.environ.get("DEEPSEEK_MODEL")
    or os.environ.get("OPENAI_MODEL")
    or "deepseek-chat"
)
DEFAULT_LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.2"))

# Canonical model names used in experiments / ablation studies.
ABLATION_MODEL_CHOICES = (
    "deepseek-chat",
    "gpt-5-mini",
)


def resolve_api_key() -> str | None:
    return (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or os.environ.get("LLM_API_KEY")
    )


def resolve_base_url() -> str | None:
    return os.environ.get("OPENAI_BASE_URL") or os.environ.get("DEEPSEEK_BASE_URL")


def create_client():
    from openai import OpenAI

    api_key = resolve_api_key()
    if not api_key:
        raise RuntimeError(
            "No API key: set OPENAI_API_KEY or DEEPSEEK_API_KEY in environment or .env"
        )
    base_url = resolve_base_url()
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def chat_json(
    *,
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = DEFAULT_LLM_TEMPERATURE,
    max_tokens: int = 8192,
) -> dict[str, Any]:
    client = create_client()
    resp = client.chat.completions.create(
        model=model or DEFAULT_LLM_MODEL,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
        max_tokens=max_tokens,
    )
    content = resp.choices[0].message.content or "{}"
    return json.loads(content)


def resolve_model_name(model: str | None = None, ablation_model: str | None = None) -> str:
    """Resolve effective model name with optional ablation override."""
    if ablation_model:
        if ablation_model not in ABLATION_MODEL_CHOICES:
            raise ValueError(
                f"Unknown ablation model: {ablation_model}. "
                f"Choices: {', '.join(ABLATION_MODEL_CHOICES)}"
            )
        return ablation_model
    return model or DEFAULT_LLM_MODEL

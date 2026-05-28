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
    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Python package 'openai' is not installed in the current environment. "
            "From repository root run: `cd backend && pip install -r requirements.txt`"
        ) from exc

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
    model_name = model or DEFAULT_LLM_MODEL
    base_payload = {
        "model": model_name,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    # Some models (e.g. gpt-5-mini) only support default temperature.
    temperature_payloads = [{}]
    if not model_name.startswith("gpt-5"):
        temperature_payloads = [{"temperature": temperature}]
    elif temperature == 1:
        temperature_payloads = [{"temperature": temperature}]
    else:
        temperature_payloads = [{}, {"temperature": temperature}]

    # gpt-5-* uses max_completion_tokens, while many OpenAI-compatible APIs still use max_tokens.
    token_params = [("max_tokens", max_tokens)]
    if model_name.startswith("gpt-5"):
        token_params = [("max_completion_tokens", max_tokens), ("max_tokens", max_tokens)]

    last_err: Exception | None = None
    resp = None
    for temp_payload in temperature_payloads:
        for token_key, token_value in token_params:
            try:
                resp = client.chat.completions.create(
                    **base_payload,
                    **temp_payload,
                    **{token_key: token_value},
                )
                break
            except Exception as exc:  # noqa: BLE001
                msg = str(exc).lower()
                unsupported_token = "unsupported parameter" in msg and token_key.lower() in msg
                unsupported_temperature = (
                    "unsupported value" in msg and "temperature" in msg and "temperature" in temp_payload
                )
                if unsupported_token or unsupported_temperature:
                    last_err = exc
                    continue
                raise
        if resp is not None:
            break

    if resp is None:
        if last_err is not None:
            raise last_err
        raise RuntimeError("LLM request failed before receiving a response.")

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

"""OpenAI-compatible LLM client (OpenAI, DeepSeek, Gemini, etc.)."""

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
DEFAULT_LLM_TIMEOUT_SEC = float(os.environ.get("LLM_TIMEOUT_SEC", "120"))

# Gemini typically needs more output tokens for large JSON responses.
_GEMINI_MAX_TOKENS = 16384

# Gemini OpenAI-compatible endpoint
_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Canonical model names used in experiments / ablation studies.
ABLATION_MODEL_CHOICES = (
    "deepseek-chat",
    "gemini-2.5-flash",
    "gpt-5-mini",
)


# ---------------------------------------------------------------------------
# Per-model routing helpers
# ---------------------------------------------------------------------------

def _is_gemini(model: str) -> bool:
    return model.startswith("gemini-")


def _is_gpt5(model: str) -> bool:
    return model.startswith("gpt-5")


def resolve_api_key(model: str | None = None) -> str | None:
    """Return the API key appropriate for the given model.

    When model is None (legacy call-sites that don't know the model yet),
    all known key variables are checked so that a Gemini-only .env still works.
    """
    if model and _is_gemini(model):
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")
    return (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("LLM_API_KEY")
    )


def resolve_base_url(model: str | None = None) -> str | None:
    """Return the base URL appropriate for the given model."""
    if model and _is_gemini(model):
        return os.environ.get("GEMINI_BASE_URL") or _GEMINI_BASE_URL
    return os.environ.get("OPENAI_BASE_URL") or os.environ.get("DEEPSEEK_BASE_URL")


def create_client(model: str | None = None):
    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Python package 'openai' is not installed in the current environment. "
            "From repository root run: `cd backend && pip install -r requirements.txt`"
        ) from exc

    api_key = resolve_api_key(model)
    if not api_key:
        provider = (
            "GEMINI_API_KEY" if (model and _is_gemini(model))
            else "OPENAI_API_KEY or DEEPSEEK_API_KEY"
        )
        raise RuntimeError(f"No API key found. Set {provider} in environment or .env")

    base_url = resolve_base_url(model)
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url, timeout=DEFAULT_LLM_TIMEOUT_SEC)
    return OpenAI(api_key=api_key, timeout=DEFAULT_LLM_TIMEOUT_SEC)


def chat_json(
    *,
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = DEFAULT_LLM_TEMPERATURE,
    max_tokens: int = 8192,
) -> dict[str, Any]:
    model_name = model or DEFAULT_LLM_MODEL
    client = create_client(model_name)

    core_payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
    }

    # --- response_format: try json_object first, fall back to omitting ---
    response_format_payloads: list[dict[str, Any]] = [
        {"response_format": {"type": "json_object"}},
        {},
    ]

    # --- temperature ---
    # gpt-5-*: only default (1) accepted; try without first, then with.
    # gemini-* and others: include temperature directly.
    if _is_gpt5(model_name):
        if temperature == 1:
            temperature_payloads: list[dict[str, Any]] = [{"temperature": temperature}]
        else:
            temperature_payloads = [{}, {"temperature": temperature}]
    else:
        temperature_payloads = [{"temperature": temperature}]

    # --- token limit parameter ---
    # Gemini gets a larger default to avoid JSON truncation.
    # gpt-5-* prefers max_completion_tokens; all others use max_tokens.
    effective_max_tokens = _GEMINI_MAX_TOKENS if _is_gemini(model_name) else max_tokens
    if _is_gpt5(model_name):
        token_params = [("max_completion_tokens", effective_max_tokens), ("max_tokens", effective_max_tokens)]
    else:
        token_params = [("max_tokens", effective_max_tokens)]

    last_err: Exception | None = None
    resp = None

    for response_payload in response_format_payloads:
        for temp_payload in temperature_payloads:
            for token_key, token_value in token_params:
                try:
                    resp = client.chat.completions.create(
                        **core_payload,
                        **response_payload,
                        **temp_payload,
                        **{token_key: token_value},
                    )
                    break
                except Exception as exc:  # noqa: BLE001
                    msg = str(exc).lower()
                    retryable = (
                        ("unsupported parameter" in msg and token_key.lower() in msg)
                        or ("unsupported value" in msg and "temperature" in msg
                            and "temperature" in temp_payload)
                        or ("unsupported parameter" in msg and "response_format" in msg
                            and "response_format" in response_payload)
                    )
                    if retryable:
                        last_err = exc
                        continue
                    raise
            if resp is not None:
                break
        if resp is not None:
            break

    if resp is None:
        if last_err is not None:
            raise last_err
        raise RuntimeError("LLM request failed before receiving a response.")

    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        repaired = _repair_truncated_json(content)
        return json.loads(repaired)


def _repair_truncated_json(text: str) -> str:
    """Best-effort repair of a JSON string that was cut off mid-stream.

    Walks the text character-by-character to track open strings, objects, and
    arrays, then appends the minimum closing tokens needed to make the result
    parseable.  Works for the typical LLM truncation pattern where the response
    ends inside a string value or just before closing brackets.
    """
    stack: list[str] = []
    in_string = False
    escape_next = False

    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack and stack[-1] == ch:
            stack.pop()

    suffix = ""
    if in_string:
        suffix += '"'          # close the dangling string
    suffix += "".join(reversed(stack))  # close open objects / arrays
    return text + suffix


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

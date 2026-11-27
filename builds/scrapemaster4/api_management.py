"""LLM provider access for ScrapeMaster 4.0's structured-extraction step.

The scaffold's own requirements.txt named `google-generativeai==0.2.0` --
confirmed installable (it's a real, if ancient, published version) but it
now prints at import time: "All support for the `google.generativeai`
package has ended... Please switch to the `google.genai` package." This
module uses the real current SDK (`google-genai`, a different package
name entirely, not a version bump) instead, since writing new code against
a retired library would be shipping something already broken.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Callable, Optional

import tiktoken

logger = logging.getLogger(__name__)

_APPROX_CHARS_PER_TOKEN = 4

PLACEHOLDER_MARKERS = ("your_api_key", "your-api-key", "replace_me", "changeme", "xxxx", "<key>")

PROVIDER_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "groq": "llama-3.1-8b-instant",
    "gemini": "gemini-2.0-flash",
}


class MissingAPIKeyError(RuntimeError):
    """Raised with a plain-English message, never a raw SDK auth error."""


class ExtractionError(RuntimeError):
    """The model's response could not be parsed into the requested fields."""


def _env_var_name(provider: str) -> str:
    return {
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }[provider]


def load_api_key(provider: str, env: Optional[dict] = None) -> str:
    """Reads the provider's key from the environment (or an injected dict for
    tests) and fails with a plain-English message rather than a raw auth
    error, on both a missing key and an obvious leftover placeholder."""
    env = os.environ if env is None else env
    var_name = _env_var_name(provider)
    key = env.get(var_name, "").strip()
    if not key:
        raise MissingAPIKeyError(
            f"No {provider} API key found. Set {var_name} in your .env file "
            f"(or your environment) before scraping with {provider}."
        )
    if any(marker in key.lower() for marker in PLACEHOLDER_MARKERS):
        raise MissingAPIKeyError(
            f"{var_name} still looks like a placeholder ({key!r}). "
            f"Replace it with your real {provider} API key."
        )
    return key


def truncate_text(text: str, max_tokens: int, encoding_name: str = "cl100k_base") -> str:
    """Trims text to at most max_tokens tokens, counted the way the model
    actually counts them, so a long scraped page doesn't silently blow the
    provider's context window.

    tiktoken ships no vocabulary data in the pip package itself -- it
    downloads the real encoding file from openaipublic.blob.core.windows.net
    on first use and caches it locally after. That host is blocked by this
    sandbox's egress proxy (confirmed directly: a real run raised a 403
    through the proxy), so the exact path is unverified from here, the
    same standing restriction as every other build in this project needing
    a blocked external host. A real deployment with ordinary internet
    access hits this once, then uses the cached file forever -- but since a
    user's very first run could fail the same way this sandbox does (a
    firewalled network, an offline machine), falling back to a documented
    approximate word-based truncation on any load failure is the honest,
    defensive choice rather than letting that one download turn into an
    unhandled crash."""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
    except Exception as exc:
        logger.warning("tiktoken encoding %r unavailable (%s); using approximate truncation", encoding_name, exc)
        max_chars = max_tokens * _APPROX_CHARS_PER_TOKEN
        return text[:max_chars]
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return encoding.decode(tokens[:max_tokens])


def _build_prompt(text: str, fields: list[str]) -> str:
    field_list = ", ".join(fields)
    return (
        "Extract the following fields from the page content below. "
        f"Fields: {field_list}.\n"
        "Return ONLY a single JSON object with exactly these keys, nothing else. "
        "If a field isn't present in the content, use an empty string for it.\n\n"
        f"PAGE CONTENT:\n{text}"
    )


def _parse_json_response(raw: str, fields: list[str]) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"Model response wasn't valid JSON: {raw[:200]!r}") from exc
    if not isinstance(parsed, dict):
        raise ExtractionError(f"Model response was valid JSON but not an object: {raw[:200]!r}")
    return {field: parsed.get(field, "") for field in fields}


# Each provider call is a plain Callable[[str, str], str] (model, prompt) -> raw text,
# so tests can inject a fake one without a real key or network call.
ProviderCall = Callable[[str, str], str]


def _real_openai_call(api_key: str) -> ProviderCall:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    def call(model: str, prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    return call


def _real_groq_call(api_key: str) -> ProviderCall:
    from groq import Groq

    client = Groq(api_key=api_key)

    def call(model: str, prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    return call


def _real_gemini_call(api_key: str) -> ProviderCall:
    from google import genai

    client = genai.Client(api_key=api_key)

    def call(model: str, prompt: str) -> str:
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text or ""

    return call


_REAL_CALL_FACTORIES = {
    "openai": _real_openai_call,
    "groq": _real_groq_call,
    "gemini": _real_gemini_call,
}


@dataclass
class LLMClient:
    """Dispatches to a real provider SDK, or an injected `call_fn` for tests."""

    provider: str
    model: str
    call_fn: Optional[ProviderCall] = None

    @classmethod
    def for_provider(cls, provider: str, model: Optional[str] = None, env: Optional[dict] = None) -> "LLMClient":
        if provider not in _REAL_CALL_FACTORIES:
            raise ValueError(f"Unknown provider {provider!r}; choose one of {sorted(_REAL_CALL_FACTORIES)}")
        api_key = load_api_key(provider, env=env)
        call_fn = _REAL_CALL_FACTORIES[provider](api_key)
        return cls(provider=provider, model=model or PROVIDER_DEFAULT_MODELS[provider], call_fn=call_fn)

    def extract(self, text: str, fields: list[str], max_input_tokens: int = 6000) -> dict:
        if self.call_fn is None:
            raise RuntimeError("LLMClient has no call_fn configured")
        trimmed = truncate_text(text, max_input_tokens)
        prompt = _build_prompt(trimmed, fields)
        raw = self.call_fn(self.model, prompt)
        return _parse_json_response(raw, fields)

"""AI content generation via OpenAI or Anthropic APIs.

Uses only Python standard library (urllib) to avoid extra dependencies.
"""

import json
import urllib.request
import urllib.error
from typing import Optional

import aqt


class AIGenerationError(Exception):
    pass


def generate_html(front: str, prompt: str) -> str:
    """Generate HTML card content for a given front field value.

    Args:
        front: The word or phrase from the card's Front field.
        prompt: The system prompt for this deck.

    Returns:
        HTML string to be stored in the AI_Content field.

    Raises:
        AIGenerationError: If the API call fails.
    """
    config = aqt.mw.addonManager.getConfig(__name__)
    provider = (config or {}).get("ai_provider", "openai")

    if provider == "anthropic":
        return _call_anthropic(front, prompt, config or {})
    else:
        return _call_openai(front, prompt, config or {})


def _call_openai(front: str, prompt: str, config: dict) -> str:
    api_key = config.get("openai_api_key", "")
    if not api_key:
        raise AIGenerationError(
            "OpenAI API key not set. Please configure it in the add-on settings."
        )
    model = config.get("openai_model", "gpt-4o")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": front},
        ],
        "temperature": 0.7,
        "max_tokens": 1500,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise AIGenerationError(
            f"OpenAI API error {e.code}: {error_body}"
        ) from e
    except Exception as e:
        raise AIGenerationError(f"Network error calling OpenAI: {e}") from e

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise AIGenerationError(f"Unexpected OpenAI response format: {body}") from e

    return _clean_html(content)


def _call_anthropic(front: str, prompt: str, config: dict) -> str:
    api_key = config.get("anthropic_api_key", "")
    if not api_key:
        raise AIGenerationError(
            "Anthropic API key not set. Please configure it in the add-on settings."
        )
    model = config.get("anthropic_model", "claude-sonnet-4-6")

    payload = {
        "model": model,
        "max_tokens": 1500,
        "system": prompt,
        "messages": [
            {"role": "user", "content": front},
        ],
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise AIGenerationError(
            f"Anthropic API error {e.code}: {error_body}"
        ) from e
    except Exception as e:
        raise AIGenerationError(f"Network error calling Anthropic: {e}") from e

    try:
        content = body["content"][0]["text"]
    except (KeyError, IndexError) as e:
        raise AIGenerationError(
            f"Unexpected Anthropic response format: {body}"
        ) from e

    return _clean_html(content)


def _clean_html(text: str) -> str:
    """Strip markdown code fences if the AI wrapped the HTML in them."""
    text = text.strip()
    if text.startswith("```html"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

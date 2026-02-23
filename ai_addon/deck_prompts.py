"""Per-deck prompt storage and retrieval.

Prompts are stored in a JSON file alongside the add-on config.
Each entry maps a deck name to its custom prompt.
Falls back to the default prompt from config.json if no deck-specific prompt exists.
"""

import json
import os
from typing import Optional

import aqt
from anki.decks import DeckId


_PROMPTS_FILENAME = "deck_prompts.json"


def _prompts_path() -> str:
    addon_dir = os.path.dirname(__file__)
    return os.path.join(addon_dir, _PROMPTS_FILENAME)


def load_all() -> dict[str, str]:
    path = _prompts_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_all(prompts: dict[str, str]) -> None:
    path = _prompts_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)


def get_prompt(deck_name: str) -> str:
    """Return the prompt for a deck, falling back to the default."""
    prompts = load_all()
    if deck_name in prompts:
        return prompts[deck_name]
    # Try parent deck names (e.g. "Japanese::N3" → "Japanese")
    parts = deck_name.split("::")
    for i in range(len(parts) - 1, 0, -1):
        parent = "::".join(parts[:i])
        if parent in prompts:
            return prompts[parent]
    return _default_prompt()


def set_prompt(deck_name: str, prompt: str) -> None:
    prompts = load_all()
    if prompt.strip():
        prompts[deck_name] = prompt.strip()
    else:
        prompts.pop(deck_name, None)
    save_all(prompts)


def delete_prompt(deck_name: str) -> None:
    prompts = load_all()
    prompts.pop(deck_name, None)
    save_all(prompts)


def _default_prompt() -> str:
    config = aqt.mw.addonManager.getConfig(__name__)
    if config and config.get("default_prompt"):
        return config["default_prompt"]
    return (
        "You are a language learning assistant. Given a word or phrase, "
        "generate a helpful, well-structured HTML study card. Include: "
        "pronunciation guide, part of speech, definition, 2-3 example sentences, "
        "common collocations or usage notes. Format with clean HTML using inline "
        "styles (no external CSS). Keep it concise and educational."
    )

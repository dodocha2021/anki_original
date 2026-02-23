"""Supabase REST API client.

Uses only Python standard library (urllib) to avoid extra dependencies.
Communicates with Supabase via its PostgREST HTTP API.
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional

import aqt


class SupabaseError(Exception):
    pass


def _get_config() -> tuple[str, str, str]:
    """Return (url, anon_key, table_name) from add-on config."""
    config = aqt.mw.addonManager.getConfig(__name__) or {}
    url = config.get("supabase_url", "").rstrip("/")
    key = config.get("supabase_anon_key", "")
    table = config.get("supabase_table", "ai_card_content")
    return url, key, table


def is_configured() -> bool:
    url, key, _ = _get_config()
    return bool(url and key)


def upsert(
    note_id: str,
    deck_name: str,
    front: str,
    ai_content: str,
    model_used: str = "",
    prompt_used: str = "",
) -> None:
    """Insert or update a row in the ai_card_content table.

    Silently skips if Supabase is not configured.
    Raises SupabaseError on network/API failures.
    """
    url, key, table = _get_config()
    if not url or not key:
        return

    endpoint = f"{url}/rest/v1/{table}"
    payload = {
        "note_id": note_id,
        "deck_name": deck_name,
        "front": front,
        "ai_content": ai_content,
        "model_used": model_used,
        "prompt_used": prompt_used,
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Prefer": "resolution=merge-duplicates",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise SupabaseError(
            f"Supabase upsert failed ({e.code}): {error_body}"
        ) from e
    except Exception as e:
        raise SupabaseError(f"Network error calling Supabase: {e}") from e


def fetch(note_id: str) -> Optional[dict]:
    """Fetch a single row by note_id. Returns None if not found."""
    url, key, table = _get_config()
    if not url or not key:
        return None

    params = urllib.parse.urlencode({"note_id": f"eq.{note_id}"})
    endpoint = f"{url}/rest/v1/{table}?{params}"

    req = urllib.request.Request(
        endpoint,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            rows = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise SupabaseError(
            f"Supabase fetch failed ({e.code}): {error_body}"
        ) from e
    except Exception as e:
        raise SupabaseError(f"Network error calling Supabase: {e}") from e

    return rows[0] if rows else None


SQL_SETUP = """
-- Run this in your Supabase SQL editor to create the required table.

CREATE TABLE IF NOT EXISTS ai_card_content (
    note_id      TEXT PRIMARY KEY,
    deck_name    TEXT NOT NULL,
    front        TEXT NOT NULL,
    ai_content   TEXT NOT NULL,
    model_used   TEXT DEFAULT '',
    prompt_used  TEXT DEFAULT '',
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-update updated_at on row modification
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ai_card_content_updated_at
    BEFORE UPDATE ON ai_card_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Enable Row Level Security (optional but recommended)
ALTER TABLE ai_card_content ENABLE ROW LEVEL SECURITY;

-- Allow anonymous reads and writes (adjust as needed)
CREATE POLICY "Allow anon access" ON ai_card_content
    FOR ALL USING (true) WITH CHECK (true);
"""

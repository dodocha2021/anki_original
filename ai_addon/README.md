# AI Card Generator — Anki Add-on

Generates AI-powered HTML content for Anki card backs using OpenAI or Anthropic APIs.
Each deck can have its own custom system prompt.
Content is optionally synced to Supabase for management and backup.

## Quick Start (Mac)

```bash
# From the root of this repository:
bash ai_addon/setup.sh
```

Then follow the printed instructions.

## What it does

- **Per-deck prompts**: Each deck can have a different system prompt
  (e.g. "JLPT N3 vocabulary" vs "English idioms").
- **Batch generation**: Select cards in the Browser → `Edit → Generate AI Content for Selected`.
- **Empty-only mode**: Skip cards that already have AI content.
- **Supabase sync**: Optionally stores each generated card in Supabase
  (note_id, deck_name, front, ai_content, model_used, prompt_used).
- **Isolated Anki profile**: Runs as `ANKI_BASE=~/AnkiCustomData` so your
  real Anki data is never touched.

## Required Note Type Fields

Create a note type (e.g. "AI Vocabulary") with exactly these fields:

| Field | Purpose |
|-------|---------|
| `Front` | The word or phrase |
| `AI_Content` | AI-generated HTML back (filled by this add-on) |
| `NoteID` | Stable ID used as Supabase primary key (auto-set) |

## Card Templates

Copy the HTML from `card_template/` into your note type's card template editor:

- **Front template**: `card_template/front.html`
- **Back template**: `card_template/back.html`
- **Styling**: `card_template/style.css`

## Configuration

Open **Tools → AI Card Generator → Configure API Keys** and fill in:

```json
{
  "ai_provider": "openai",          // "openai" or "anthropic"
  "openai_api_key": "sk-...",
  "openai_model": "gpt-4o",
  "anthropic_api_key": "sk-ant-...",
  "anthropic_model": "claude-sonnet-4-6",
  "supabase_url": "https://xxx.supabase.co",
  "supabase_anon_key": "eyJ...",
  "supabase_table": "ai_card_content",
  "request_delay_ms": 500
}
```

## Per-Deck Prompts

**Tools → AI Card Generator → Configure Deck Prompts**

- Decks without a custom prompt use the `default_prompt` from config.
- Parent deck prompts apply to sub-decks (e.g. `Japanese` covers `Japanese::N3`).

## Supabase Setup

Run the SQL in `supabase_client.py` (the `SQL_SETUP` string at the bottom)
in your Supabase SQL editor to create the table.

## Files

```
ai_addon/
  __init__.py            Main entry point (menus, hooks)
  config.json            Default configuration
  deck_prompts.py        Per-deck prompt storage
  ai_generator.py        OpenAI / Anthropic API calls
  supabase_client.py     Supabase REST API client + SQL setup
  note_manager.py        Anki note field helpers
  setup.sh               Mac installer script
  ui/
    deck_prompt_dialog.py  Per-deck prompt editor dialog
    generate_dialog.py     Progress dialog for generation
  card_template/
    front.html             Card front template
    back.html              Card back template
    style.css              Card styling
```

## Workflow

1. Add cards with just the `Front` field filled in.
2. Select them in the Browser.
3. `Edit → Generate AI Content for Selected` (or `empty only` to skip regeneration).
4. Review the generated content — edit the `AI_Content` field directly if needed.
5. Sync to AnkiWeb as usual. AnkiDroid will display the field content offline.

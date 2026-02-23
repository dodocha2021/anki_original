"""Helpers for reading and writing Anki note fields.

Expected note type fields:
  Front      - the word or phrase (existing)
  AI_Content - AI-generated HTML (created by this add-on)
  NoteID     - stable string ID used as Supabase primary key (created by this add-on)
"""

from anki.notes import Note

FRONT_FIELD = "Front"
AI_CONTENT_FIELD = "AI_Content"
NOTE_ID_FIELD = "NoteID"


def get_front(note: Note) -> str:
    """Return the value of the Front field, stripped of whitespace."""
    try:
        return note[FRONT_FIELD].strip()
    except KeyError:
        return ""


def get_ai_content(note: Note) -> str:
    """Return existing AI_Content, or empty string if not present."""
    try:
        return note[AI_CONTENT_FIELD]
    except KeyError:
        return ""


def set_ai_content(note: Note, html: str, note_id: str) -> None:
    """Write AI_Content and NoteID fields.

    Silently skips if the note type doesn't have these fields
    (the caller should validate the note type beforehand).
    """
    try:
        note[AI_CONTENT_FIELD] = html
    except KeyError:
        raise ValueError(
            f"Note type '{note.note_type()['name']}' is missing the "
            f"'{AI_CONTENT_FIELD}' field. Please add it in the note type editor."
        )
    try:
        if not note[NOTE_ID_FIELD]:
            note[NOTE_ID_FIELD] = note_id
    except KeyError:
        pass  # NoteID field is optional


def has_required_fields(note: Note) -> bool:
    """Return True if the note has both Front and AI_Content fields."""
    field_names = {f["name"] for f in note.note_type()["flds"]}
    return FRONT_FIELD in field_names and AI_CONTENT_FIELD in field_names


def notes_missing_ai_content(note_ids: list[int], col) -> list[int]:
    """Filter note_ids to those that have an empty AI_Content field."""
    result = []
    for nid in note_ids:
        try:
            note = col.get_note(nid)
            if has_required_fields(note) and not get_ai_content(note).strip():
                result.append(nid)
        except Exception:
            pass
    return result

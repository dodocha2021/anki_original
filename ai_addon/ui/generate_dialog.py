"""Progress dialog shown while AI content is being generated."""

import time
from typing import Callable, Sequence

from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QPushButton,
    Qt,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import showWarning
import aqt

from .. import ai_generator, deck_prompts, note_manager, supabase_client


class GenerateDialog(QDialog):
    """Runs AI generation for a list of note IDs with a progress bar."""

    def __init__(
        self,
        note_ids: Sequence[int],
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)
        self.note_ids = list(note_ids)
        self._cancelled = False
        self.setWindowTitle("Generating AI Content")
        self.resize(500, 350)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.status_label = QLabel(
            f"Ready to generate content for {len(self.note_ids)} card(s)."
        )
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(self.note_ids))
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        btn_box = QDialogButtonBox()
        self.run_btn = QPushButton("Start")
        self.run_btn.clicked.connect(self._run)
        btn_box.addButton(self.run_btn, QDialogButtonBox.ButtonRole.ActionRole)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel)
        btn_box.addButton(self.cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

        self.close_btn = QPushButton("Close")
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        btn_box.addButton(self.close_btn, QDialogButtonBox.ButtonRole.AcceptRole)

        layout.addWidget(btn_box)

    def _log(self, msg: str) -> None:
        self.log.append(msg)
        self.log.verticalScrollBar().setValue(
            self.log.verticalScrollBar().maximum()
        )

    def _cancel(self) -> None:
        self._cancelled = True
        self._log("Cancelling after current card...")

    def _run(self) -> None:
        self.run_btn.setEnabled(False)
        config = aqt.mw.addonManager.getConfig(
            aqt.mw.addonManager.addonFromModule(__name__)
        ) or {}
        delay_ms = config.get("request_delay_ms", 500)

        col = aqt.mw.col
        errors = 0

        for i, nid in enumerate(self.note_ids):
            if self._cancelled:
                self._log("Cancelled.")
                break

            try:
                note = col.get_note(nid)
            except Exception as e:
                self._log(f"[{i+1}] ERROR loading note {nid}: {e}")
                errors += 1
                continue

            front = note_manager.get_front(note)
            if not front:
                self._log(f"[{i+1}] SKIP note {nid}: Front field is empty.")
                self.progress_bar.setValue(i + 1)
                continue

            deck_id = col.cards_of_note(nid)[0].did
            deck_name = col.decks.name(deck_id)
            prompt = deck_prompts.get_prompt(deck_name)

            self.status_label.setText(
                f"[{i+1}/{len(self.note_ids)}] Generating: {front[:50]}"
            )
            # Let the UI update
            aqt.mw.app.processEvents()

            try:
                html = ai_generator.generate_html(front, prompt)
            except ai_generator.AIGenerationError as e:
                self._log(f"[{i+1}] ERROR for '{front}': {e}")
                errors += 1
                self.progress_bar.setValue(i + 1)
                continue

            # Write back to note
            model_used = _model_label(config)
            try:
                note_manager.set_ai_content(note, html, str(nid))
                col.update_note(note)
            except Exception as e:
                self._log(f"[{i+1}] ERROR saving note {nid}: {e}")
                errors += 1
                self.progress_bar.setValue(i + 1)
                continue

            # Sync to Supabase (non-fatal)
            try:
                supabase_client.upsert(
                    note_id=str(nid),
                    deck_name=deck_name,
                    front=front,
                    ai_content=html,
                    model_used=model_used,
                    prompt_used=prompt,
                )
            except supabase_client.SupabaseError as e:
                self._log(f"[{i+1}] Supabase warning for '{front}': {e}")

            self._log(f"[{i+1}] OK: {front}")
            self.progress_bar.setValue(i + 1)

            if i < len(self.note_ids) - 1:
                time.sleep(delay_ms / 1000.0)
                aqt.mw.app.processEvents()

        col.save()
        summary = f"Done. {len(self.note_ids)} card(s) processed, {errors} error(s)."
        self.status_label.setText(summary)
        self._log(f"\n{summary}")
        self.close_btn.setEnabled(True)


def _model_label(config: dict) -> str:
    provider = config.get("ai_provider", "openai")
    if provider == "anthropic":
        return config.get("anthropic_model", "claude-sonnet-4-6")
    return config.get("openai_model", "gpt-4o")

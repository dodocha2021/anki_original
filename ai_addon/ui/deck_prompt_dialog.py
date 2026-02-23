"""Dialog to view and edit per-deck AI prompts."""

from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSplitter,
    Qt,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
import aqt

from .. import deck_prompts


class DeckPromptDialog(QDialog):
    """Shows all decks on the left; prompt editor on the right."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Prompts by Deck")
        self.resize(800, 500)
        self._build_ui()
        self._load_decks()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: deck list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Decks"))
        self.deck_list = QListWidget()
        self.deck_list.currentItemChanged.connect(self._on_deck_selected)
        left_layout.addWidget(self.deck_list)
        splitter.addWidget(left)

        # Right: prompt editor
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.prompt_label = QLabel("Select a deck to edit its prompt.")
        right_layout.addWidget(self.prompt_label)

        self.prompt_editor = QTextEdit()
        self.prompt_editor.setPlaceholderText(
            "Leave empty to use the default prompt from add-on settings."
        )
        self.prompt_editor.setEnabled(False)
        right_layout.addWidget(self.prompt_editor)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save prompt")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_current)
        self.clear_btn = QPushButton("Reset to default")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self._clear_current)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        right_layout.addLayout(btn_row)

        splitter.addWidget(right)
        splitter.setSizes([250, 550])
        layout.addWidget(splitter)

        # Bottom close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_decks(self) -> None:
        col = aqt.mw.col
        all_prompts = deck_prompts.load_all()
        for deck in sorted(col.decks.all(), key=lambda d: d["name"]):
            name = deck["name"]
            item = QListWidgetItem(name)
            if name in all_prompts:
                item.setToolTip("Custom prompt configured")
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.deck_list.addItem(item)

    def _on_deck_selected(
        self, current: QListWidgetItem, previous: QListWidgetItem
    ) -> None:
        if current is None:
            return
        deck_name = current.text()
        self.prompt_label.setText(f"Prompt for: <b>{deck_name}</b>")
        all_prompts = deck_prompts.load_all()
        self.prompt_editor.setPlainText(all_prompts.get(deck_name, ""))
        self.prompt_editor.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)

    def _current_deck_name(self) -> str:
        item = self.deck_list.currentItem()
        return item.text() if item else ""

    def _save_current(self) -> None:
        name = self._current_deck_name()
        if not name:
            return
        text = self.prompt_editor.toPlainText()
        deck_prompts.set_prompt(name, text)
        self._refresh_item_style(name, bold=bool(text.strip()))

    def _clear_current(self) -> None:
        name = self._current_deck_name()
        if not name:
            return
        deck_prompts.delete_prompt(name)
        self.prompt_editor.setPlainText("")
        self._refresh_item_style(name, bold=False)

    def _refresh_item_style(self, deck_name: str, bold: bool) -> None:
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            if item and item.text() == deck_name:
                font = item.font()
                font.setBold(bold)
                item.setFont(font)
                break

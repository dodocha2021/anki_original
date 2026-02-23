"""AI Card Generator add-on for Anki.

Adds per-deck AI prompts and generates HTML content for card backs
using OpenAI or Anthropic APIs, with optional Supabase storage.

Installation:
  See README.md or run setup.sh on Mac.

Menu items added:
  Tools → AI Card Generator → Configure Deck Prompts
  Tools → AI Card Generator → Configure API Keys
  Browser: Edit → Generate AI Content for Selected
  Browser: Edit → Generate AI Content (empty only)
"""

from aqt import gui_hooks, mw
from aqt.qt import QAction, QMenu
from aqt.utils import showInfo, showWarning


def _on_browser_menu(browser) -> None:
    """Add AI generation actions to the Browser's Edit menu."""
    menu = browser.form.menuEdit

    separator = menu.addSeparator()

    action_all = QAction("Generate AI Content for Selected", browser)
    action_all.triggered.connect(lambda: _generate_selected(browser, empty_only=False))
    menu.addAction(action_all)

    action_empty = QAction("Generate AI Content (empty only)", browser)
    action_empty.triggered.connect(lambda: _generate_selected(browser, empty_only=True))
    menu.addAction(action_empty)


def _generate_selected(browser, empty_only: bool = False) -> None:
    from .note_manager import notes_missing_ai_content
    from .ui.generate_dialog import GenerateDialog

    note_ids = browser.selected_notes()
    if not note_ids:
        showWarning("No cards selected.", parent=browser)
        return

    if empty_only:
        note_ids = notes_missing_ai_content(note_ids, mw.col)
        if not note_ids:
            showInfo("All selected cards already have AI content.", parent=browser)
            return

    dlg = GenerateDialog(note_ids, parent=browser)
    dlg.exec()
    browser.model.reset()


def _open_deck_prompt_dialog() -> None:
    from .ui.deck_prompt_dialog import DeckPromptDialog

    dlg = DeckPromptDialog(parent=mw)
    dlg.exec()


def _open_config() -> None:
    mw.addonManager.showConfigEditor(mw.addonManager.addonFromModule(__name__))


def _setup_tools_menu() -> None:
    menu_bar = mw.form.menubar
    ai_menu = QMenu("AI Card Generator", mw)

    prompts_action = QAction("Configure Deck Prompts…", mw)
    prompts_action.triggered.connect(_open_deck_prompt_dialog)
    ai_menu.addAction(prompts_action)

    config_action = QAction("Configure API Keys…", mw)
    config_action.triggered.connect(_open_config)
    ai_menu.addAction(config_action)

    # Insert before the Help menu
    help_menu = mw.form.menuHelp
    menu_bar.insertMenu(help_menu.menuAction(), ai_menu)


# Register hooks once Anki's main window is ready
gui_hooks.main_window_did_init.append(_setup_tools_menu)
gui_hooks.browser_menus_did_init.append(_on_browser_menu)

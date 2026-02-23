#!/usr/bin/env bash
# setup.sh - Install the AI Card Generator add-on for Anki on macOS.
#
# Usage:
#   bash setup.sh
#
# What it does:
#   1. Creates ~/AnkiCustomData as an isolated Anki data directory.
#   2. Copies this add-on into ~/AnkiCustomData/addons21/ai_card_generator/.
#   3. Creates a launch script ~/launch_anki_custom.sh.
#
# After running setup.sh:
#   1. Open ~/launch_anki_custom.sh to start the custom Anki.
#   2. Create a new note type with fields: Front, AI_Content, NoteID
#   3. Use the card templates from card_template/ in this directory.
#   4. Add your API key via: Tools → AI Card Generator → Configure API Keys

set -e

ADDON_NAME="ai_card_generator"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANKI_DATA="$HOME/AnkiCustomData"
ADDON_DEST="$ANKI_DATA/addons21/$ADDON_NAME"
LAUNCH_SCRIPT="$HOME/launch_anki_custom.sh"

echo "=== AI Card Generator — Anki Add-on Installer ==="
echo ""

# ── 1. Create isolated data directory ─────────────────────────────────────────
echo "Creating isolated Anki data directory at: $ANKI_DATA"
mkdir -p "$ANKI_DATA/addons21"

# ── 2. Copy add-on files ───────────────────────────────────────────────────────
echo "Installing add-on to: $ADDON_DEST"
rm -rf "$ADDON_DEST"
cp -r "$SCRIPT_DIR" "$ADDON_DEST"

# Remove the setup script itself and README from the installed copy (not needed at runtime)
rm -f "$ADDON_DEST/setup.sh"

echo "Add-on installed."

# ── 3. Create launch script ────────────────────────────────────────────────────
# NOTE: We use the direct binary path with --base instead of "open -a Anki"
# because macOS's `open` command does NOT reliably pass environment variables
# (like ANKI_BASE) to the launched application.
cat > "$LAUNCH_SCRIPT" << 'LAUNCH_EOF'
#!/usr/bin/env bash
# Launch Anki with the custom (isolated) data directory.
# Your regular Anki profile is NOT affected.
#
# IMPORTANT: Close any currently open Anki window before running this,
# because Anki only runs one instance at a time.

ANKI_BIN="/Applications/Anki.app/Contents/MacOS/anki"

if [ ! -f "$ANKI_BIN" ]; then
  echo "ERROR: Anki not found at $ANKI_BIN"
  echo "Is Anki installed in /Applications? If not, edit this script to fix the path."
  exit 1
fi

echo "Launching Anki with custom data at: $HOME/AnkiCustomData"
"$ANKI_BIN" --base "$HOME/AnkiCustomData" &
LAUNCH_EOF
chmod +x "$LAUNCH_SCRIPT"
echo "Launch script created at: $LAUNCH_SCRIPT"

# ── 4. Done ────────────────────────────────────────────────────────────────────
echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Run: bash ~/launch_anki_custom.sh"
echo "     (Or double-click it in Finder)"
echo ""
echo "  2. In Anki, create a new Note Type with these fields:"
echo "       Front       ← the word or phrase"
echo "       AI_Content  ← AI-generated HTML (leave blank)"
echo "       NoteID      ← auto-set, leave blank"
echo ""
echo "  3. Set the card template:"
echo "       Front template: copy from $SCRIPT_DIR/card_template/front.html"
echo "       Back template:  copy from $SCRIPT_DIR/card_template/back.html"
echo "       Styling:        copy from $SCRIPT_DIR/card_template/style.css"
echo ""
echo "  4. Add your API key:"
echo "       Tools → AI Card Generator → Configure API Keys"
echo ""
echo "  5. Add some cards, then select them in the Browser and choose:"
echo "       Edit → Generate AI Content for Selected"
echo ""
echo "  6. (Optional) Set up Supabase:"
echo "       Run the SQL in ai_addon/supabase_client.py in your Supabase SQL editor."
echo "       Then add supabase_url and supabase_anon_key in the add-on config."

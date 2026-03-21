#!/bin/bash
# ============================================================================
# build_dmg.sh — Création du .dmg pour Note Taker Offline
# ============================================================================
set -e

APP_NAME="Note Taker Offline"
DMG_NAME="${APP_NAME}.dmg"
APP_PATH="dist/${APP_NAME}.app"

# Vérification que le .app existe
if [ ! -d "$APP_PATH" ]; then
    echo "✗ Le bundle $APP_PATH n'existe pas."
    echo "  Exécutez d'abord : .venv/bin/pyinstaller app.spec --noconfirm"
    exit 1
fi

# Supprimer un ancien .dmg s'il existe
rm -f "$DMG_NAME"

echo "▸ Création du DMG '$DMG_NAME'..."

create-dmg \
  --volname "$APP_NAME" \
  --window-size 600 400 \
  --icon-size 128 \
  --icon "$APP_NAME.app" 150 200 \
  --app-drop-link 450 200 \
  --hide-extension "$APP_NAME.app" \
  "$DMG_NAME" \
  "$APP_PATH"

echo ""
echo "✓ DMG créé avec succès : $DMG_NAME"
echo "  Taille : $(du -sh "$DMG_NAME" | cut -f1)"

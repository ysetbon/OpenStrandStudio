#!/bin/bash

################################################################################
# OpenStrand Studio macOS DMG Builder - Version 1.107
# Date: Created January 31, 2026
#
# LOGIC EXPLANATION:
# ==================
# This script creates a macOS .dmg disk image for drag-and-drop installation.
# Unlike PKG installers, DMG files are simple disk images that users mount
# and drag the app to their Applications folder.
#
# DMG CONTENTS:
# -------------
# 1. OpenStrandStudio.app - The application bundle
# 2. Applications symlink - Shortcut to /Applications for easy drag-and-drop
# 3. README.txt - Multilingual release notes and installation instructions
#
# MULTILINGUAL SUPPORT:
# ---------------------
# The README.txt contains release notes in all 7 supported languages:
# English, French, German, Italian, Spanish, Portuguese, Hebrew
#
# BUILD PROCESS:
# --------------
# 1. Creates temporary directory for DMG contents
# 2. Copies .app bundle from dist folder
# 3. Creates symbolic link to /Applications
# 4. Generates README.txt with multilingual release notes
# 5. Creates temporary writable DMG with hdiutil
# 6. Converts to compressed read-only DMG
# 7. Sets custom icon using fileicon
# 8. Verifies DMG integrity
# 9. Cleans up temporary files
################################################################################

# Set variables
APP_NAME="OpenStrandStudio"
VERSION="1.107"
APP_DATE="31_January_2026"
PUBLISHER="Yonatan Setbon"
DMG_NAME="OpenStrandStudioSetup_${APP_DATE}_${VERSION}"

# Create a temporary directory for DMG contents
TMP_DIR="$(mktemp -d)"
DMG_DIR="$TMP_DIR/$APP_NAME"
mkdir -p "$DMG_DIR"

# Create installer_output directory if it doesn't exist
INSTALLER_OUTPUT="/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/installer_output"
mkdir -p "$INSTALLER_OUTPUT"

# Copy the .app bundle from the correct location
APP_SOURCE="/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/dist/OpenStrandStudio.app"
if [ ! -d "$APP_SOURCE" ]; then
    echo "Error: Could not find .app at: $APP_SOURCE"
    echo "Please run 'pyinstaller OpenStrandStudio_mac.spec' first"
    exit 1
fi

# Copy the .app bundle to the temporary directory
cp -R "$APP_SOURCE" "$DMG_DIR/"

# Create a symbolic link to Applications folder
ln -s /Applications "$DMG_DIR/Applications"

# Create README.txt with version info and contact
cat > "$DMG_DIR/README.txt" << EOF
$APP_NAME $VERSION
By $PUBLISHER
Contact: ysetbon@gmail.com

New in Version $VERSION (English):
• Hover Highlights in Attach, Move, and Select Modes: Points and strands now highlight in yellow when hovering, making it clear what will be selected or moved when you click.
• View Mode: New "look only" mode for safely navigating your design. Pan and zoom without accidentally selecting or editing.
• Delete All Button: Added a "Delete All" button in the layer panel to quickly remove all strands at once.
• Crash Log: Added automatic crash logging to help identify and fix bugs in future updates.

Nouveautés de la version $VERSION (Français):
• Surbrillance au survol dans les modes Attacher, Déplacer et Sélection: Les points et brins sont maintenant mis en surbrillance en jaune au survol, indiquant clairement ce qui sera sélectionné ou déplacé.
• Mode Visualisation: Nouveau mode "lecture seule" pour naviguer en toute sécurité. Déplacez-vous et zoomez sans modifier accidentellement.
• Bouton Tout Supprimer: Ajout d'un bouton "Tout Supprimer" dans le panneau des calques.
• Journal des Plantages: Ajout d'un journal automatique des plantages pour les futures mises à jour.

Novità della versione $VERSION (Italiano):
• Evidenziazione al passaggio del mouse nei modi Attacca, Sposta e Selezione: I punti e i trefoli ora si evidenziano in giallo al passaggio del mouse, rendendo chiaro cosa verrà selezionato o spostato quando si clicca.
• Modalità Visualizzazione: Nuova modalità "solo visualizzazione" per navigare in sicurezza nel tuo progetto. Scorri e zooma senza selezionare o modificare accidentalmente.
• Pulsante Elimina Tutto: Aggiunto un pulsante "Elimina Tutto" nel pannello dei livelli per rimuovere rapidamente tutti i trefoli.
• Registro degli Arresti: Aggiunta la registrazione automatica degli arresti anomali per aiutare a identificare e correggere i bug nei futuri aggiornamenti.

Novedades de la versión $VERSION (Español):
• Resaltado al pasar el cursor en modos Adjuntar, Mover y Selección: Los puntos y hebras ahora se resaltan en amarillo al pasar el cursor, dejando claro qué se seleccionará o moverá al hacer clic.
• Modo Visualización: Nuevo modo "solo ver" para navegar su diseño de forma segura. Desplácese y haga zoom sin seleccionar o editar accidentalmente.
• Botón Eliminar Todo: Se agregó un botón "Eliminar Todo" en el panel de capas para eliminar rápidamente todas las hebras.
• Registro de Fallos: Se agregó registro automático de fallos para ayudar a identificar y corregir errores en futuras actualizaciones.

Novidades da versão $VERSION (Português):
• Destaque ao passar o cursor nos modos Anexar, Mover e Seleção: Os pontos e mechas agora são destacados em amarelo ao passar o cursor, tornando claro o que será selecionado ou movido ao clicar.
• Modo Visualização: Novo modo "apenas visualizar" para navegar seu design com segurança. Mova e amplie sem selecionar ou editar acidentalmente.
• Botão Excluir Tudo: Adicionado um botão "Excluir Tudo" no painel de camadas para remover rapidamente todas as mechas.
• Registro de Falhas: Adicionado registro automático de falhas para ajudar a identificar e corrigir bugs em futuras atualizações.

Neu in Version $VERSION (Deutsch):
• Hervorhebung beim Überfahren in Anhänge-, Verschiebe- und Auswahlmodi: Punkte und Stränge werden gelb hervorgehoben, sodass klar erkennbar ist, was beim Klicken ausgewählt oder verschoben wird.
• Ansichtsmodus: Neuer "Nur-Ansicht"-Modus zum sicheren Navigieren. Schwenken und zoomen Sie ohne versehentliche Änderungen.
• Alles Löschen Schaltfläche: Eine "Alles Löschen"-Schaltfläche wurde im Ebenenbedienfeld hinzugefügt.
• Absturzprotokoll: Automatische Absturzprotokollierung für zukünftige Updates hinzugefügt.

מה חדש בגרסה $VERSION (עברית):
• הדגשת ריחוף במצבי חיבור, הזזה ובחירה: נקודות וחוטים מודגשים כעת בצהוב בעת ריחוף, כך שברור מה ייבחר או יוזז בלחיצה.
• מצב צפייה: מצב "צפייה בלבד" חדש לניווט בטוח בעיצוב שלך. גלול והגדל בלי לבחור או לערוך בטעות.
• כפתור מחק הכל: נוסף כפתור "מחק הכל" בפאנל השכבות להסרה מהירה של כל החוטים.
• יומן קריסות: נוספה רישום אוטומטי של קריסות לזיהוי ותיקון באגים בעדכונים עתידיים.

Installation:
1. Drag '$APP_NAME' to the Applications folder
2. Double-click the app in Applications to launch

For support, contact: ysetbon@gmail.com
EOF

# Create temporary DMG
TEMP_DMG="$TMP_DIR/temp.dmg"
FINAL_DMG="$INSTALLER_OUTPUT/${DMG_NAME}.dmg"

echo "Creating temporary DMG..."
hdiutil create -volname "$APP_NAME $VERSION" -srcfolder "$DMG_DIR" -ov -format UDRW "$TEMP_DMG"

echo "Converting to final DMG..."
hdiutil convert "$TEMP_DMG" -format UDZO -imagekey zlib-level=9 -o "$FINAL_DMG"

# Verify the DMG was created successfully
if [ ! -f "$FINAL_DMG" ]; then
    echo "Error: Failed to create DMG"
    exit 1
fi

# Set permissions
chmod 644 "$FINAL_DMG"

# Install fileicon if not already installed
if ! command -v fileicon &> /dev/null; then
    echo "Installing fileicon..."
    brew install fileicon
fi

# Set the DMG icon
echo "Setting DMG icon..."
fileicon set "$FINAL_DMG" "/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/box_stitch.icns"

# Verify the DMG is mountable
echo "Verifying DMG..."
if ! hdiutil verify "$FINAL_DMG" >/dev/null; then
    echo "Warning: DMG verification failed"
else
    echo "DMG verified successfully"
fi

# Clean up
rm -rf "$TMP_DIR"

echo "DMG created at: $FINAL_DMG"
echo "Version: $VERSION"
echo "Publisher: $PUBLISHER"

# Try to mount the DMG to verify it works
echo "Testing DMG mount..."
hdiutil attach "$FINAL_DMG"

# Open the installer_output directory
open "$INSTALLER_OUTPUT"

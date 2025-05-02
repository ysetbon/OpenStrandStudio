#!/bin/bash

# Set variables to match ISS configuration
APP_NAME="OpenStrandStudio"
VERSION="1.092"
APP_DATE="3_May_2025"
PUBLISHER="Yonatan Setbon"
DMG_NAME="OpenStrandStudioSetup_${APP_DATE}_${VERSION}"

# Create a temporary directory for DMG contents
TMP_DIR="$(mktemp -d)"
DMG_DIR="$TMP_DIR/$APP_NAME"
mkdir -p "$DMG_DIR"

# Create installer_output directory if it doesn't exist
INSTALLER_OUTPUT="/Users/yonatansetbon/Documents/GitHub/OpenStrandStudio/src/installer_output"
mkdir -p "$INSTALLER_OUTPUT"

# Copy the .app bundle from the correct location
APP_SOURCE="/Users/yonatansetbon/Documents/GitHub/OpenStrandStudio/src/dist/OpenStrandStudio.app"  # Updated path
if [ ! -d "$APP_SOURCE" ]; then
    echo "Error: Could not find .app at: $APP_SOURCE"
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

New in this version (English):
- Persistent Undo/Redo History: Your undo and redo actions are now saved with your project.
- Customizable Dashed Lines and Arrowheads for strands.
- Improved Control Point Visuals with larger handles.
- Mask Extension Options for better visual effects.
- Enhanced Shading Algorithm for smoother shadows.
- Upgraded Layer Panel with drag-and-drop reordering and quick visibility toggles.

Nouveautés dans cette version (Français):
- Historique Annuler/Rétablir persistant enregistré dans votre projet.
- Lignes et flèches en pointillés personnalisables pour les brins.
- Points de contrôle plus grands et plus visibles.
- Options d'extension des masques pour un meilleur contrôle.
- Algorithme d'ombrage amélioré pour des ombres plus douces.
- Panneau des calques amélioré avec réorganisation par glisser-déposer et bascule rapide de visibilité.

Novità in questa versione (Italiano):
- Cronologia Annulla/Ripristina persistente salvata con il progetto.
- Linee tratteggiate e frecce personalizzabili per i fili.
- Punti di controllo più grandi e visibili.
- Opzioni di estensione delle maschere per maggior controllo.
- Algoritmo di ombreggiatura migliorato con ombre più naturali.
- Pannello livelli potenziato con riordino drag-and-drop e visibilità rapida.

Novedades en esta versión (Español):
- Historial de Deshacer/Rehacer persistente guardado con el proyecto.
- Líneas y flechas discontinuas personalizables para los hilos.
- Puntos de control más grandes y visibles.
- Opciones de extensión de máscaras para mayor control.
- Algoritmo de sombreado mejorado con sombras más suaves.
- Panel de capas mejorado con reordenamiento mediante arrastrar y soltar y visibilidad rápida.

Novidades nesta versão (Português):
- Histórico de Desfazer/Refazer persistente salvo com o projeto.
- Linhas tracejadas e setas personalizáveis para os fios.
- Pontos de controle maiores e mais visíveis.
- Opções de extensão de máscara para maior controle.
- Algoritmo de sombreamento aprimorado com sombras mais suaves.
- Painel de camadas aprimorado com reordenação arrastar-e-soltar e visibilidade rápida.

חדש בגרסה זו (עברית):
- היסטוריית ביטול/חזרה נשמרת עם הפרויקט.
- קווים וחיצים מקווקווים בהתאמה אישית.
- נקודות בקרה גדולות וברורות יותר.
- אפשרויות הארכת מסיכות לשליטה טובה יותר.
- אלגוריתם הצללה משופר לצללים רכים יותר.
- לוח שכבות משופר עם גרור-ושחרר ותפריט תצוגה מהירה.

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
fileicon set "$FINAL_DMG" "/Users/yonatansetbon/Documents/GitHub/OpenStrandStudio/src/box_stitch.icns"

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
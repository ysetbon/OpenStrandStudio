#!/bin/bash

# Set variables to match ISS configuration
APP_NAME="OpenStrandStudio"
VERSION="1.104"
APP_DATE="02_November_2025"
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
APP_SOURCE="/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/dist/OpenStrandStudio.app"  # Updated path
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

New in Version 1.104 (English):
• [TODO: Update with version 1.104 features - e.g., Enhanced attached strand functionality]
• Additional UI improvements and bug fixes
• Performance optimizations

Nouveautés dans la version 1.104 (Français):
• [TODO: Mettre à jour avec les fonctionnalités de la version 1.104 - par exemple, Fonctionnalité de brin attaché améliorée]
• Améliorations de l'interface utilisateur et corrections de bugs supplémentaires
• Optimisations des performances

Novità nella versione 1.104 (Italiano):
• [TODO: Aggiornare con le funzionalità della versione 1.104 - ad esempio, Funzionalità del filamento attaccato migliorata]
• Ulteriori miglioramenti dell'interfaccia utente e correzioni di bug
• Ottimizzazioni delle prestazioni

Novedades en la versión 1.104 (Español):
• [TODO: Actualizar con las características de la versión 1.104 - por ejemplo, Funcionalidad de hilo adjunto mejorada]
• Mejoras adicionales de la interfaz de usuario y correcciones de errores
• Optimizaciones de rendimiento

Novidades na versão 1.104 (Português):
• [TODO: Atualizar com os recursos da versão 1.104 - por exemplo, Funcionalidade de fio anexado aprimorada]
• Melhorias adicionais da interface do usuário e correções de bugs
• Otimizações de desempenho

Neu in Version 1.104 (Deutsch):
• [TODO: Mit den Funktionen von Version 1.104 aktualisieren - z.B., Verbesserte angehängte Strang-Funktionalität]
• Zusätzliche UI-Verbesserungen und Fehlerbehebungen
• Leistungsoptimierungen

מה חדש בגרסה 1.104 (עברית):
• [TODO: עדכן עם תכונות גרסה 1.104 - לדוגמה, פונקציונליות גדיל מחובר משופרת]
• שיפורי ממשק משתמש ותיקוני באגים נוספים
• אופטימיזציות ביצועים

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

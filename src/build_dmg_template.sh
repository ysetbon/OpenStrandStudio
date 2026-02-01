#!/bin/bash

################################################################################
# OpenStrand Studio macOS DMG Builder TEMPLATE
# Date: Created February 1, 2026
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
# TEMPLATE USAGE:
# ---------------
# This is a template file. To create a new version DMG:
# 1. Copy this file to build_dmg_1_XXX.sh (replace XXX with version number)
# 2. Search for "#todo" to find all places where version-specific content is needed
# 3. Update VERSION and APP_DATE variables at the top
# 4. Replace all "#todo" placeholders with actual feature descriptions
# 5. Run the script to generate the DMG
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

# Set variables - #todo: Update these for each new version
APP_NAME="OpenStrandStudio"
VERSION="x"                          # #todo: Update version number (e.g., "1.107")
APP_DATE="xx_Month_20xx"             # #todo: Update date (e.g., "15_January_2026")
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
# #todo: Replace all "#todo" placeholders below with actual feature descriptions
cat > "$DMG_DIR/README.txt" << EOF
$APP_NAME $VERSION
By $PUBLISHER
Contact: ysetbon@gmail.com

New in Version $VERSION (English):
• #todo: Feature description 1
• #todo: Feature description 2
• #todo: Feature description 3
• #todo: Feature description 4
• #todo: Feature description 5

Nouveautés dans la version $VERSION (Français):
• #todo: Description de fonctionnalité 1
• #todo: Description de fonctionnalité 2
• #todo: Description de fonctionnalité 3
• #todo: Description de fonctionnalité 4
• #todo: Description de fonctionnalité 5

Novità nella versione $VERSION (Italiano):
• #todo: Descrizione della funzionalità 1
• #todo: Descrizione della funzionalità 2
• #todo: Descrizione della funzionalità 3
• #todo: Descrizione della funzionalità 4
• #todo: Descrizione della funzionalità 5

Novedades en la versión $VERSION (Español):
• #todo: Descripción de la característica 1
• #todo: Descripción de la característica 2
• #todo: Descripción de la característica 3
• #todo: Descripción de la característica 4
• #todo: Descripción de la característica 5

Novidades na versão $VERSION (Português):
• #todo: Descrição do recurso 1
• #todo: Descrição do recurso 2
• #todo: Descrição do recurso 3
• #todo: Descrição do recurso 4
• #todo: Descrição do recurso 5

Neu in Version $VERSION (Deutsch):
• #todo: Funktionsbeschreibung 1
• #todo: Funktionsbeschreibung 2
• #todo: Funktionsbeschreibung 3
• #todo: Funktionsbeschreibung 4
• #todo: Funktionsbeschreibung 5

מה חדש בגרסה $VERSION (עברית):
• #todo: תיאור תכונה 1
• #todo: תיאור תכונה 2
• #todo: תיאור תכונה 3
• #todo: תיאור תכונה 4
• #todo: תיאור תכונה 5

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

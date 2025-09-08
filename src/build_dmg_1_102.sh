#!/bin/bash

# Set variables to match ISS configuration
APP_NAME="OpenStrandStudio"
VERSION="1.102"
APP_DATE="08_September_2025"
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

New in Version 1.102 (English):
• Enhanced Curvature Bias Controls: New bias control points between center and end control points for fine-tuned curvature adjustment.
• Advanced Curvature Settings: Three new parameters - Control Point Influence, Distance Boost, and Curve Shape for complete curve control.
• Progressive Control Point Display: Control points appear progressively to reduce visual clutter during initial strand placement.
• Improved Shading Rendering: Fixed various shading issues for better visual quality.

Nouveautés dans la version 1.102 (Français):
• Contrôles de biais de courbure améliorés : Nouveaux points de contrôle de biais entre les points de contrôle centraux et finaux pour un ajustement précis de la courbure.
• Paramètres de courbure avancés : Trois nouveaux paramètres - Influence du point de contrôle, Amplification de distance et Forme de courbe pour un contrôle complet des courbes.
• Affichage progressif des points de contrôle : Les points de contrôle apparaissent progressivement pour réduire l'encombrement visuel lors du placement initial.
• Rendu d'ombrage amélioré : Correction de divers problèmes d'ombrage pour une meilleure qualité visuelle.

Novità nella versione 1.102 (Italiano):
• Controlli di bias di curvatura migliorati: Nuovi punti di controllo di bias tra i punti di controllo centrali e finali per una regolazione precisa della curvatura.
• Impostazioni di curvatura avanzate: Tre nuovi parametri - Influenza del punto di controllo, Amplificazione della distanza e Forma della curva per un controllo completo delle curve.
• Visualizzazione progressiva dei punti di controllo: I punti di controllo appaiono progressivamente per ridurre il disordine visivo durante il posizionamento iniziale.
• Rendering di ombreggiatura migliorato: Corretti vari problemi di ombreggiatura per una migliore qualità visiva.

Novedades en la versión 1.102 (Español):
• Controles mejorados de sesgo de curvatura: Nuevos puntos de control de sesgo entre los puntos de control centrales y finales para un ajuste fino de la curvatura.
• Configuración de curvatura avanzada: Tres nuevos parámetros - Influencia del punto de control, Amplificación de distancia y Forma de curva para control completo de curvas.
• Visualización progresiva de puntos de control: Los puntos de control aparecen progresivamente para reducir el desorden visual durante la colocación inicial.
• Renderizado de sombreado mejorado: Se corrigieron varios problemas de sombreado para mejor calidad visual.

Novidades na versão 1.102 (Português):
• Controles de viés de curvatura aprimorados: Novos pontos de controle de viés entre os pontos de controle centrais e finais para ajuste fino da curvatura.
• Configurações de curvatura avançadas: Três novos parâmetros - Influência do ponto de controle, Amplificação de distância e Forma da curva para controle completo das curvas.
• Exibição progressiva de pontos de controle: Os pontos de controle aparecem progressivamente para reduzir a desordem visual durante o posicionamento inicial.
• Renderização de sombreamento aprimorada: Vários problemas de sombreamento corrigidos para melhor qualidade visual.

Neu in Version 1.102 (Deutsch):
• Verbesserte Krümmungsverzerrungskontrollen: Neue Bias-Kontrollpunkte zwischen Mittel- und Endkontrollpunkten für präzise Krümmungsanpassung.
• Erweiterte Krümmungseinstellungen: Drei neue Parameter - Kontrollpunkteinfluss, Distanzverstärkung und Kurvenform für vollständige Kurvenkontrolle.
• Progressive Kontrollpunktanzeige: Kontrollpunkte erscheinen progressiv, um visuelles Durcheinander bei der anfänglichen Strangplatzierung zu reduzieren.
• Verbesserte Schattierungsdarstellung: Verschiedene Schattierungsprobleme für bessere visuelle Qualität behoben.

חדש בגרסה 1.102 (עברית):
• בקרות הטיית עקמומיות משופרות: נקודות בקרת הטיה חדשות בין נקודות בקרה מרכזיות וסופיות לכוונון עקמומיות מדויק.
• הגדרות עקמומיות מתקדמות: שלושה פרמטרים חדשים - השפעת נקודת בקרה, הגברת מרחק וצורת עקומה לשליטה מלאה בעקומות.
• תצוגת נקודות בקרה פרוגרסיבית: נקודות בקרה מופיעות בהדרגה כדי להפחית עומס חזותי במהלך מיקום גדיל ראשוני.
• עיבוד הצללה משופר: תוקנו בעיות הצללה שונות לאיכות חזותית טובה יותר.

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
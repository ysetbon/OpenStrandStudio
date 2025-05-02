#!/bin/bash

# Set variables
APP_NAME="OpenStrandStudio"
VERSION="1_092"
APP_DATE="3_May_2025"
PUBLISHER="Yonatan Setbon"
IDENTIFIER="com.yonatansetbon.openstrandstudio"

# Create directories
WORKING_DIR="$(mktemp -d)"
SCRIPTS_DIR="$WORKING_DIR/scripts"
RESOURCES_DIR="$WORKING_DIR/resources"
PKG_PATH="/Users/yonatansetbon/Documents/GitHub/OpenStrandStudio/src/installer_output/${APP_NAME}_${VERSION}.pkg"

mkdir -p "$SCRIPTS_DIR" "$RESOURCES_DIR"

# Create postinstall script
cat > "$SCRIPTS_DIR/postinstall" << 'EOF'
#!/bin/bash

# Get the user's home directory
USER_HOME=$HOME

# Create Desktop icon
cp -f "/Applications/OpenStrand Studio.app/Contents/Resources/box_stitch.icns" "$USER_HOME/Desktop/OpenStrandStudio.icns"

# Create Launch Agent for auto-start (optional)
LAUNCH_AGENT_DIR="$USER_HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENT_DIR"

# Ensure all dependencies are properly accessible
# This can help with dependency issues like missing PyQt5
if [ -d "/Applications/OpenStrand Studio.app/Contents/Resources/lib/python3.9/site-packages" ]; then
    chmod -R 755 "/Applications/OpenStrand Studio.app/Contents/Resources/lib/python3.9/site-packages"
fi

# Ask if user wants to launch the app now
osascript <<EOD
    tell application "System Events"
        activate
        set launch_now to button returned of (display dialog "Installation Complete! Would you like to launch OpenStrandStudio now?" buttons {"Launch Now", "Later"} default button "Launch Now")
        if launch_now is "Launch Now" then
            tell application "OpenStrandStudio" to activate
        end if
    end tell
EOD

exit 0
EOF

# Make postinstall script executable
chmod +x "$SCRIPTS_DIR/postinstall"

# Create Distribution.xml
cat > "$WORKING_DIR/Distribution.xml" << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>$APP_NAME $VERSION</title>
    <organization>$PUBLISHER</organization>
    <domains enable_localSystem="true"/>
    <options customize="allow" require-scripts="true" allow-external-scripts="no"/>
    <welcome file="welcome.html"/>
    <license file="license.html"/>
    <choices-outline>
        <line choice="default">
            <line choice="com.yonatansetbon.openstrandstudio"/>
        </line>
    </choices-outline>
    <choice id="default"/>
    <choice id="com.yonatansetbon.openstrandstudio" visible="false">
        <pkg-ref id="com.yonatansetbon.openstrandstudio"/>
    </choice>
    <pkg-ref id="com.yonatansetbon.openstrandstudio" version="$VERSION" onConclusion="none">OpenStrandStudio.pkg</pkg-ref>
</installer-gui-script>
EOF

# Create welcome.html
cat > "$RESOURCES_DIR/welcome.html" << EOF
<!DOCTYPE html>
<html>
<body>
    <h2>Welcome to $APP_NAME $VERSION</h2>
    <p>This will install $APP_NAME on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li>Persistent Undo/Redo History: Your undo and redo actions are now saved with your project.</li>
        <li>Customizable Dashed Lines and Arrowheads for strands.</li>
        <li>Improved Control Point Visuals with larger handles.</li>
        <li>Mask Extension Options for finer control.</li>
        <li>Enhanced Shading Algorithm with smoother shadows.</li>
        <li>Upgraded Layer Panel with drag-and-drop reordering and quick visibility toggles.</li>
    </ul>
</body>
</html>
EOF

# Create license.html
cat > "$RESOURCES_DIR/license.html" << EOF
<!DOCTYPE html>
<html>
<body>
    <h2>License Agreement</h2>
    <p>Copyright (c) 2025 $PUBLISHER</p>
    <p>By installing this software, you agree to the terms and conditions.</p>
</body>
</html>
EOF

# Duplicate license.html into localized resource folders
declare -a LANG_CODES=("fr" "it" "es" "pt" "he")
for LANG in "${LANG_CODES[@]}"; do
    mkdir -p "$RESOURCES_DIR/${LANG}.lproj"
    cp "$RESOURCES_DIR/license.html" "$RESOURCES_DIR/${LANG}.lproj/license.html"
done

# Create localized welcome.html files
# French
cat > "$RESOURCES_DIR/fr.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Bienvenue dans OpenStrandStudio 1.092</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li>Historique Annuler/Rétablir persistant enregistré dans votre projet.</li>
        <li>Lignes et flèches en pointillés personnalisables pour les brins.</li>
        <li>Points de contrôle plus grands et plus visibles.</li>
        <li>Options d'extension des masques pour un meilleur contrôle.</li>
        <li>Algorithme d'ombrage amélioré pour des ombres plus douces.</li>
        <li>Panneau des calques amélioré avec réorganisation par glisser-déposer et bascule rapide de visibilité.</li>
    </ul>
</body>
</html>
EOF

# Italian
cat > "$RESOURCES_DIR/it.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Benvenuto in OpenStrandStudio 1.092</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li>Cronologia Annulla/Ripristina persistente salvata con il progetto.</li>
        <li>Linee tratteggiate e frecce personalizzabili per i fili.</li>
        <li>Punti di controllo più grandi e visibili.</li>
        <li>Opzioni di estensione delle maschere per maggior controllo.</li>
        <li>Algoritmo di ombreggiatura migliorato con ombre più naturali.</li>
        <li>Pannello livelli potenziato con riordino drag-and-drop e visibilità rapida.</li>
    </ul>
</body>
</html>
EOF

# Spanish
cat > "$RESOURCES_DIR/es.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Bienvenido a OpenStrandStudio 1.092</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li>Historial de Deshacer/Rehacer persistente guardado con el proyecto.</li>
        <li>Líneas y flechas discontinuas personalizables para los hilos.</li>
        <li>Puntos de control más grandes y visibles.</li>
        <li>Opciones de extensión de máscaras para mayor control.</li>
        <li>Algoritmo de sombreado mejorado con sombras más suaves.</li>
        <li>Panel de capas mejorado con reordenamiento mediante arrastrar y soltar y visibilidad rápida.</li>
    </ul>
</body>
</html>
EOF

# Portuguese
cat > "$RESOURCES_DIR/pt.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Bem-vindo ao OpenStrandStudio 1.092</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li>Histórico de Desfazer/Refazer persistente salvo com o projeto.</li>
        <li>Linhas tracejadas e setas personalizáveis para os fios.</li>
        <li>Pontos de controle maiores e mais visíveis.</li>
        <li>Opções de extensão de máscara para maior controle.</li>
        <li>Algoritmo de sombreamento aprimorado com sombras mais suaves.</li>
        <li>Painel de camadas aprimorado com reordenação arrastar-e-soltar e visibilidade rápida.</li>
    </ul>
</body>
</html>
EOF

# Hebrew
cat > "$RESOURCES_DIR/he.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html dir="rtl">
<body>
    <h2>ברוכים הבאים ל-OpenStrandStudio 1.092</h2>
    <p>אשף זה יתקין את OpenStrandStudio במחשב שלך.</p>
    <p>חדש בגרסה זו:</p>
    <ul>
        <li>היסטוריית ביטול/חזרה נשמרת עם הפרויקט.</li>
        <li>קווים וחיצים מקווקווים בהתאמה אישית.</li>
        <li>נקודות בקרה גדולות וברורות יותר.</li>
        <li>אפשרויות הארכת מסיכות לשליטה טובה יותר.</li>
        <li>אלגוריתם הצללה משופר לצללים רכים יותר.</li>
        <li>לוח שכבות משופר עם גרור-ושחרר ואפשרויות תצוגה מהירה.</li>
    </ul>
</body>
</html>
EOF

# Create component package
pkgbuild \
    --root "/Users/yonatansetbon/Documents/GitHub/OpenStrandStudio/src/dist/OpenStrandStudio.app" \
    --install-location "/Applications/OpenStrandStudio.app" \
    --scripts "$SCRIPTS_DIR" \
    --identifier "$IDENTIFIER" \
    --version "$VERSION" \
    "$WORKING_DIR/OpenStrandStudio.pkg"

# Create product archive without signing
productbuild \
    --distribution "$WORKING_DIR/Distribution.xml" \
    --resources "$RESOURCES_DIR" \
    --package-path "$WORKING_DIR" \
    "$PKG_PATH"

# Clean up
rm -rf "$WORKING_DIR"

echo "Installer package created at: $PKG_PATH"
open "$(dirname "$PKG_PATH")"
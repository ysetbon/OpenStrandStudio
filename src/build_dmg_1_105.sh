#!/bin/bash

################################################################################
# OpenStrand Studio macOS DMG Builder TEMPLATE
# Date: Created November 27, 2025
#
# LOGIC EXPLANATION:
# ==================
# This script creates a macOS .dmg disk image with full multilingual support
# for 7 languages: English, French, German, Italian, Spanish, Portuguese, Hebrew
#
# MULTILINGUAL STRUCTURE:
# -----------------------
# macOS installer uses .lproj folders for localization. Each language needs:
# 1. A license.html file in its own *.lproj folder (e.g., fr.lproj/license.html)
# 2. A welcome.html file in its own *.lproj folder (e.g., fr.lproj/welcome.html)
#
# CRITICAL: Each language's welcome.html contains ALL 7 languages, BUT the
# order is different - the target language appears FIRST, followed by others.
# This ensures users see their preferred language at the top when they select it.
#
# LANGUAGE ORDER IN EACH FILE:
# -----------------------------
# Base (en.lproj):  English, German, French, Italian, Spanish, Portuguese, Hebrew
# fr.lproj:         French, English, German, Italian, Spanish, Portuguese, Hebrew
# de.lproj:         German, English, French, Italian, Spanish, Portuguese, Hebrew
# it.lproj:         Italian, English, German, French, Spanish, Portuguese, Hebrew
# es.lproj:         Spanish, English, French, German, Italian, Portuguese, Hebrew
# pt.lproj:         Portuguese, English, French, German, Italian, Spanish, Hebrew
# he.lproj:         Hebrew, English, French, German, Italian, Spanish, Portuguese
#
# TEMPLATE USAGE:
# ---------------
# This is a template file. To create a new version DMG:
# 1. Copy this file to build_dmg_1_XXX.sh (replace XXX with version number)
# 2. Search for "#todo" to find all places where version-specific content is needed
# 3. Replace "#todo What's New message" with the actual "What's New" header for each language
# 4. Replace each "#todo feature description" with actual feature descriptions
# 5. Update VERSION and APP_DATE variables at the top
#
# BUILD PROCESS:
# --------------
# 1. Creates temporary directories for scripts and resources
# 2. Generates postinstall script (creates desktop icon, offers to launch app)
# 3. Creates Distribution.xml (installer configuration)
# 4. Creates base license.html and welcome.html
# 5. Creates localized license files for each language (.lproj folders)
# 6. Creates localized welcome files for each language (with language-specific ordering)
# 7. Builds component package with pkgbuild
# 8. Builds final product package with productbuild
# 9. Cleans up temporary files
################################################################################

# Set variables
APP_NAME="OpenStrandStudio"
VERSION="1.105"
APP_DATE="06_December_2025"
PUBLISHER="Yonatan Setbon"
IDENTIFIER="com.yonatan.openstrandstudio"

# Create directories
WORKING_DIR="$(mktemp -d)"
SCRIPTS_DIR="$WORKING_DIR/scripts"
RESOURCES_DIR="$WORKING_DIR/resources"
PKG_PATH="/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/installer_output/${APP_NAME}_${VERSION}.pkg"

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
            <line choice="com.yonatan.openstrandstudio"/>
        </line>
    </choices-outline>
    <choice id="default"/>
    <choice id="com.yonatan.openstrandstudio" visible="false">
        <pkg-ref id="com.yonatan.openstrandstudio"/>
    </choice>
    <pkg-ref id="com.yonatan.openstrandstudio" version="$VERSION" onConclusion="none">OpenStrandStudio.pkg</pkg-ref>
</installer-gui-script>
EOF

# Create welcome.html (English + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.105</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p><b>What's New in Version 1.105:</b></p>
    <ul>
        <li><b>Mask Grid:</b> Quickly visualize how many mask strands are created using strong NxN grid rendering with fixed group functionality.</li>
        <li><b>Keyboard Shortcuts:</b> Space to move, Z to undo, X to redo, N for new strand, 1 for names, L for lock, D for delete, A to deselect.</li>
        <li><b>Fixed Selection & Zoom:</b> Selection during zoom mode, selection and connection now remain accurate at all zoom levels.</li>
        <li><b>Smoother Knot Connections:</b> Rendering fix where closed knots sometimes showed seams or visible gaps at the connection point.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.105</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p><b>Neu in Version 1.105:</b></p>
    <ul>
        <li><b>Maskengitter:</b> Visualisieren Sie schnell, wie viele Maskenstränge erstellt werden, mit starkem NxN-Gitter-Rendering und fester Gruppenfunktion.</li>
        <li><b>Tastaturkürzel:</b> Leertaste zum Verschieben, Z zum Rückgängig, X zum Wiederholen, N für neuen Strang, 1 für Namen, L zum Sperren, D zum Löschen, A zum Abwählen.</li>
        <li><b>Auswahl und Zoom korrigiert:</b> Auswahl im Zoom-Modus, Auswahl und Verbindung bleiben jetzt bei allen Zoomstufen genau.</li>
        <li><b>Glattere Knotenverbindungen:</b> Rendering-Korrektur, bei der geschlossene Knoten manchmal Nähte oder sichtbare Lücken am Verbindungspunkt zeigten.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.105</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p><b>Nouveautés de la version 1.105:</b></p>
    <ul>
        <li><b>Grille de masques:</b> Visualisez rapidement le nombre de brins de masque créés grâce à un rendu puissant de grille NxN avec fonction de groupe fixe.</li>
        <li><b>Raccourcis clavier:</b> Espace pour déplacer, Z annuler, X rétablir, N nouveau brin, 1 noms, L verrouiller, D supprimer, A désélectionner.</li>
        <li><b>Sélection et zoom corrigés:</b> Sélection en mode zoom, la sélection et la connexion restent désormais précises à tous les niveaux de zoom.</li>
        <li><b>Connexions de nœuds plus fluides:</b> Correction de rendu où les nœuds fermés montraient parfois des coutures ou des espaces visibles au point de connexion.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.105</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p><b>Novità della versione 1.105:</b></p>
    <ul>
        <li><b>Griglia maschere:</b> Visualizza rapidamente quanti fili maschera vengono creati utilizzando un forte rendering griglia NxN con funzionalità gruppo fisso.</li>
        <li><b>Scorciatoie tastiera:</b> Spazio per spostare, Z annulla, X ripristina, N nuovo filo, 1 nomi, L blocca, D elimina, A deseleziona.</li>
        <li><b>Selezione e zoom corretti:</b> Selezione in modalità zoom, la selezione e connessione ora rimangono accurate a tutti i livelli di zoom.</li>
        <li><b>Connessioni nodi più fluide:</b> Correzione rendering dove nodi chiusi mostravano talvolta cuciture o spazi visibili nel punto di connessione.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.105</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p><b>Novedades de la versión 1.105:</b></p>
    <ul>
        <li><b>Cuadrícula de máscaras:</b> Visualice rápidamente cuántos hilos de máscara se crean usando renderizado fuerte de cuadrícula NxN con funcionalidad de grupo fijo.</li>
        <li><b>Atajos de teclado:</b> Espacio para mover, Z deshacer, X rehacer, N nuevo hilo, 1 nombres, L bloquear, D eliminar, A deseleccionar.</li>
        <li><b>Selección y zoom corregidos:</b> Selección en modo zoom, la selección y conexión ahora permanecen precisas en todos los niveles de zoom.</li>
        <li><b>Conexiones de nudos más suaves:</b> Corrección de renderizado donde nudos cerrados a veces mostraban costuras o espacios visibles en el punto de conexión.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.105</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p><b>Novidades da versão 1.105:</b></p>
    <ul>
        <li><b>Grade de máscaras:</b> Visualize rapidamente quantos fios de máscara são criados usando renderização forte de grade NxN com funcionalidade de grupo fixo.</li>
        <li><b>Atalhos de teclado:</b> Espaço para mover, Z desfazer, X refazer, N novo fio, 1 nomes, L bloquear, D excluir, A desmarcar.</li>
        <li><b>Seleção e zoom corrigidos:</b> Seleção no modo zoom, a seleção e conexão agora permanecem precisas em todos os níveis de zoom.</li>
        <li><b>Conexões de nós mais suaves:</b> Correção de renderização onde nós fechados às vezes mostravam costuras ou lacunas visíveis no ponto de conexão.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.105</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p><b>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.105:</b></p>
    <ul>
        <li><b>&#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E6;&#x05D5;&#x05E8; &#x05D1;&#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D0;&#x05DE;&#x05E6;&#x05E2;&#x05D5;&#x05EA; &#x05DE;&#x05DE;&#x05E9;&#x05E7; &#x05E8;&#x05E9;&#x05EA; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; N&#215;N &#x05D1;&#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E7;&#x05D9;&#x05E6;&#x05D5;&#x05E8;&#x05D9; &#x05DE;&#x05E7;&#x05DC;&#x05D3;&#x05EA;:</b> &#x05E8;&#x05D5;&#x05D5;&#x05D7; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;, Z &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;, X &#x05DC;&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8;, N &#x05DC;&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;, 1 &#x05DC;&#x05E9;&#x05DE;&#x05D5;&#x05EA;, L &#x05DC;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;, D &#x05DC;&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4;, A &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D6;&#x05D5;&#x05DD; &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5;:</b> &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1;&#x05D9; &#x05D4;&#x05D6;&#x05D6;&#x05D4;, &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05EA; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D4;&#x05D6;&#x05D5;&#x05DD;.</li>
        <li><b>&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05DC;&#x05E7;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05D9;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05D1;&#x05D4; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D4;&#x05E6;&#x05D9;&#x05D2;&#x05D5; &#x05DC;&#x05E4;&#x05E2;&#x05DE;&#x05D9;&#x05DD; &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05E4;&#x05E2;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05D1;&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create license.html (English default)
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
declare -a LANG_CODES=("en" "fr" "de" "it" "es" "pt" "he")

# Create translated license pages for each supported language

# French
mkdir -p "$RESOURCES_DIR/fr.lproj"
cat > "$RESOURCES_DIR/fr.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Accord de licence</h2>
    <p>Droit d'auteur (c) 2025 Yonatan Setbon</p>
    <p>En installant ce logiciel, vous acceptez les termes et conditions.</p>
</body>
</html>
EOF

# Italian
mkdir -p "$RESOURCES_DIR/it.lproj"
cat > "$RESOURCES_DIR/it.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Contratto di licenza</h2>
    <p>Copyright (c) 2025 Yonatan Setbon</p>
    <p>Installando questo software, accetti i termini e le condizioni.</p>
</body>
</html>
EOF

# Spanish
mkdir -p "$RESOURCES_DIR/es.lproj"
cat > "$RESOURCES_DIR/es.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Acuerdo de licencia</h2>
    <p>Derechos de autor (c) 2025 Yonatan Setbon</p>
    <p>Al instalar este software, usted acepta los términos y condiciones.</p>
</body>
</html>
EOF

# Portuguese
mkdir -p "$RESOURCES_DIR/pt.lproj"
cat > "$RESOURCES_DIR/pt.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Acordo de licença</h2>
    <p>Direitos autorais (c) 2025 Yonatan Setbon</p>
    <p>Ao instalar este software, você concorda com os termos e condições.</p>
</body>
</html>
EOF

# German
mkdir -p "$RESOURCES_DIR/de.lproj"
cat > "$RESOURCES_DIR/de.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Lizenzvereinbarung</h2>
    <p>Urheberrecht (c) 2025 Yonatan Setbon</p>
    <p>Mit der Installation dieser Software stimmen Sie den Bedingungen zu.</p>
</body>
</html>
EOF

# Hebrew (Right-to-left)
mkdir -p "$RESOURCES_DIR/he.lproj"
cat > "$RESOURCES_DIR/he.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html dir="rtl">
<body>
    <h2>&#x05D4;&#x05E1;&#x05E7;&#x05DD; &#x05E8;&#x05D9;&#x05E9;&#x05D9;&#x05D5;&#x05DF;</h2>
    <p>&#x05D6;&#x05DB;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05E6;&#x05E8;&#x05D9;&#x05DD; (c) 2025 Yonatan Setbon</p>
    <p>&#x05D1;&#x05D4;&#x05EA;&#x05E7;&#x05E0;&#x05D4; &#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D4; &#x05D6;&#x05D5;&#x05D4;, &#x05D0;&#x05EA;&#x05D4; &#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05DC;&#x05EA;&#x05E0;&#x05D0;&#x05D9;&#x05DD; &#x05D5;&#x05DC;&#x05D4;&#x05D2;&#x05D1;&#x05D5;&#x05EA;.</p>
</body>
</html>
EOF


# English (Left-to-right)
mkdir -p "$RESOURCES_DIR/en.lproj"
cp "$RESOURCES_DIR/license.html" "$RESOURCES_DIR/en.lproj/license.html"
cp "$RESOURCES_DIR/welcome.html" "$RESOURCES_DIR/en.lproj/welcome.html"

# -----------------------------------------------------------------------------
# Ensure installer resources are correctly localized
# -----------------------------------------------------------------------------
# 1) Remove the top-level licence file so Installer cannot fall back to it and
#    is forced to use the per-language copies that live inside *.lproj folders.
rm -f "$RESOURCES_DIR/license.html"
# 1) Remove the top-level licence file so Installer cannot fall back to it and
#    is forced to use the per-language copies that live inside *.lproj folders.
rm -f "$RESOURCES_DIR/license.html"
# 2) Guarantee that the multi-language Welcome page is present inside every
#    *.lproj folder (the top-level copy must stay untouched). We simply copy
#    the already-created top-level welcome.html into each language directory.
for lang in "${LANG_CODES[@]}"; do
    mkdir -p "$RESOURCES_DIR/${lang}.lproj"
    cp -f "$RESOURCES_DIR/welcome.html" "$RESOURCES_DIR/${lang}.lproj/welcome.html"
done
# 2) Guarantee that the multi-language Welcome page is present inside every
#    *.lproj folder (the top-level copy must stay untouched). We simply copy
#    the already-created top-level welcome.html into each language directory.
for lang in "${LANG_CODES[@]}"; do
    mkdir -p "$RESOURCES_DIR/${lang}.lproj"
    cp -f "$RESOURCES_DIR/welcome.html" "$RESOURCES_DIR/${lang}.lproj/welcome.html"
done

# Create welcome.html  (welcome French + localized sections).
cat > "$RESOURCES_DIR/fr.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.105</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires pour installer ce logiciel.</p>
    <p><b>Nouveautés de la version 1.105:</b></p>
    <ul>
        <li><b>Grille de masques:</b> Visualisez rapidement le nombre de brins de masque créés grâce à un rendu puissant de grille NxN avec fonction de groupe fixe.</li>
        <li><b>Raccourcis clavier:</b> Espace pour déplacer, Z annuler, X rétablir, N nouveau brin, 1 noms, L verrouiller, D supprimer, A désélectionner.</li>
        <li><b>Sélection et zoom corrigés:</b> Sélection en mode zoom, la sélection et la connexion restent désormais précises à tous les niveaux de zoom.</li>
        <li><b>Connexions de nœuds plus fluides:</b> Correction de rendu où les nœuds fermés montraient parfois des coutures ou des espaces visibles au point de connexion.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.105</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p><b>What's New in Version 1.105:</b></p>
    <ul>
        <li><b>Mask Grid:</b> Quickly visualize how many mask strands are created using strong NxN grid rendering with fixed group functionality.</li>
        <li><b>Keyboard Shortcuts:</b> Space to move, Z to undo, X to redo, N for new strand, 1 for names, L for lock, D for delete, A to deselect.</li>
        <li><b>Fixed Selection & Zoom:</b> Selection during zoom mode, selection and connection now remain accurate at all zoom levels.</li>
        <li><b>Smoother Knot Connections:</b> Rendering fix where closed knots sometimes showed seams or visible gaps at the connection point.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.105</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p><b>Neu in Version 1.105:</b></p>
    <ul>
        <li><b>Maskengitter:</b> Visualisieren Sie schnell, wie viele Maskenstränge erstellt werden, mit starkem NxN-Gitter-Rendering und fester Gruppenfunktion.</li>
        <li><b>Tastaturkürzel:</b> Leertaste zum Verschieben, Z zum Rückgängig, X zum Wiederholen, N für neuen Strang, 1 für Namen, L zum Sperren, D zum Löschen, A zum Abwählen.</li>
        <li><b>Auswahl und Zoom korrigiert:</b> Auswahl im Zoom-Modus, Auswahl und Verbindung bleiben jetzt bei allen Zoomstufen genau.</li>
        <li><b>Glattere Knotenverbindungen:</b> Rendering-Korrektur, bei der geschlossene Knoten manchmal Nähte oder sichtbare Lücken am Verbindungspunkt zeigten.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.105</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p><b>Novità della versione 1.105:</b></p>
    <ul>
        <li><b>Griglia maschere:</b> Visualizza rapidamente quanti fili maschera vengono creati utilizzando un forte rendering griglia NxN con funzionalità gruppo fisso.</li>
        <li><b>Scorciatoie tastiera:</b> Spazio per spostare, Z annulla, X ripristina, N nuovo filo, 1 nomi, L blocca, D elimina, A deseleziona.</li>
        <li><b>Selezione e zoom corretti:</b> Selezione in modalità zoom, la selezione e connessione ora rimangono accurate a tutti i livelli di zoom.</li>
        <li><b>Connessioni nodi più fluide:</b> Correzione rendering dove nodi chiusi mostravano talvolta cuciture o spazi visibili nel punto di connessione.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.105</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p><b>Novedades de la versión 1.105:</b></p>
    <ul>
        <li><b>Cuadrícula de máscaras:</b> Visualice rápidamente cuántos hilos de máscara se crean usando renderizado fuerte de cuadrícula NxN con funcionalidad de grupo fijo.</li>
        <li><b>Atajos de teclado:</b> Espacio para mover, Z deshacer, X rehacer, N nuevo hilo, 1 nombres, L bloquear, D eliminar, A deseleccionar.</li>
        <li><b>Selección y zoom corregidos:</b> Selección en modo zoom, la selección y conexión ahora permanecen precisas en todos los niveles de zoom.</li>
        <li><b>Conexiones de nudos más suaves:</b> Corrección de renderizado donde nudos cerrados a veces mostraban costuras o espacios visibles en el punto de conexión.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.105</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p><b>Novidades da versão 1.105:</b></p>
    <ul>
        <li><b>Grade de máscaras:</b> Visualize rapidamente quantos fios de máscara são criados usando renderização forte de grade NxN com funcionalidade de grupo fixo.</li>
        <li><b>Atalhos de teclado:</b> Espaço para mover, Z desfazer, X refazer, N novo fio, 1 nomes, L bloquear, D excluir, A desmarcar.</li>
        <li><b>Seleção e zoom corrigidos:</b> Seleção no modo zoom, a seleção e conexão agora permanecem precisas em todos os níveis de zoom.</li>
        <li><b>Conexões de nós mais suaves:</b> Correção de renderização onde nós fechados às vezes mostravam costuras ou lacunas visíveis no ponto de conexão.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.105</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p><b>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.105:</b></p>
    <ul>
        <li><b>&#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E6;&#x05D5;&#x05E8; &#x05D1;&#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D0;&#x05DE;&#x05E6;&#x05E2;&#x05D5;&#x05EA; &#x05DE;&#x05DE;&#x05E9;&#x05E7; &#x05E8;&#x05E9;&#x05EA; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; N&#215;N &#x05D1;&#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E7;&#x05D9;&#x05E6;&#x05D5;&#x05E8;&#x05D9; &#x05DE;&#x05E7;&#x05DC;&#x05D3;&#x05EA;:</b> &#x05E8;&#x05D5;&#x05D5;&#x05D7; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;, Z &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;, X &#x05DC;&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8;, N &#x05DC;&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;, 1 &#x05DC;&#x05E9;&#x05DE;&#x05D5;&#x05EA;, L &#x05DC;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;, D &#x05DC;&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4;, A &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D6;&#x05D5;&#x05DD; &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5;:</b> &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1;&#x05D9; &#x05D4;&#x05D6;&#x05D6;&#x05D4;, &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05EA; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D4;&#x05D6;&#x05D5;&#x05DD;.</li>
        <li><b>&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05DC;&#x05E7;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05D9;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05D1;&#x05D4; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D4;&#x05E6;&#x05D9;&#x05D2;&#x05D5; &#x05DC;&#x05E4;&#x05E2;&#x05DE;&#x05D9;&#x05DD; &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05E4;&#x05E2;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05D1;&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome German + localized sections).
cat > "$RESOURCES_DIR/de.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.105</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p><b>Neu in Version 1.105:</b></p>
    <ul>
        <li><b>Maskengitter:</b> Visualisieren Sie schnell, wie viele Maskenstränge erstellt werden, mit starkem NxN-Gitter-Rendering und fester Gruppenfunktion.</li>
        <li><b>Tastaturkürzel:</b> Leertaste zum Verschieben, Z zum Rückgängig, X zum Wiederholen, N für neuen Strang, 1 für Namen, L zum Sperren, D zum Löschen, A zum Abwählen.</li>
        <li><b>Auswahl und Zoom korrigiert:</b> Auswahl im Zoom-Modus, Auswahl und Verbindung bleiben jetzt bei allen Zoomstufen genau.</li>
        <li><b>Glattere Knotenverbindungen:</b> Rendering-Korrektur, bei der geschlossene Knoten manchmal Nähte oder sichtbare Lücken am Verbindungspunkt zeigten.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.105</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p><b>What's New in Version 1.105:</b></p>
    <ul>
        <li><b>Mask Grid:</b> Quickly visualize how many mask strands are created using strong NxN grid rendering with fixed group functionality.</li>
        <li><b>Keyboard Shortcuts:</b> Space to move, Z to undo, X to redo, N for new strand, 1 for names, L for lock, D for delete, A to deselect.</li>
        <li><b>Fixed Selection & Zoom:</b> Selection during zoom mode, selection and connection now remain accurate at all zoom levels.</li>
        <li><b>Smoother Knot Connections:</b> Rendering fix where closed knots sometimes showed seams or visible gaps at the connection point.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.105</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p><b>Nouveautés de la version 1.105:</b></p>
    <ul>
        <li><b>Grille de masques:</b> Visualisez rapidement le nombre de brins de masque créés grâce à un rendu puissant de grille NxN avec fonction de groupe fixe.</li>
        <li><b>Raccourcis clavier:</b> Espace pour déplacer, Z annuler, X rétablir, N nouveau brin, 1 noms, L verrouiller, D supprimer, A désélectionner.</li>
        <li><b>Sélection et zoom corrigés:</b> Sélection en mode zoom, la sélection et la connexion restent désormais précises à tous les niveaux de zoom.</li>
        <li><b>Connexions de nœuds plus fluides:</b> Correction de rendu où les nœuds fermés montraient parfois des coutures ou des espaces visibles au point de connexion.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.105</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p><b>Novità della versione 1.105:</b></p>
    <ul>
        <li><b>Griglia maschere:</b> Visualizza rapidamente quanti fili maschera vengono creati utilizzando un forte rendering griglia NxN con funzionalità gruppo fisso.</li>
        <li><b>Scorciatoie tastiera:</b> Spazio per spostare, Z annulla, X ripristina, N nuovo filo, 1 nomi, L blocca, D elimina, A deseleziona.</li>
        <li><b>Selezione e zoom corretti:</b> Selezione in modalità zoom, la selezione e connessione ora rimangono accurate a tutti i livelli di zoom.</li>
        <li><b>Connessioni nodi più fluide:</b> Correzione rendering dove nodi chiusi mostravano talvolta cuciture o spazi visibili nel punto di connessione.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.105</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p><b>Novedades de la versión 1.105:</b></p>
    <ul>
        <li><b>Cuadrícula de máscaras:</b> Visualice rápidamente cuántos hilos de máscara se crean usando renderizado fuerte de cuadrícula NxN con funcionalidad de grupo fijo.</li>
        <li><b>Atajos de teclado:</b> Espacio para mover, Z deshacer, X rehacer, N nuevo hilo, 1 nombres, L bloquear, D eliminar, A deseleccionar.</li>
        <li><b>Selección y zoom corregidos:</b> Selección en modo zoom, la selección y conexión ahora permanecen precisas en todos los niveles de zoom.</li>
        <li><b>Conexiones de nudos más suaves:</b> Corrección de renderizado donde nudos cerrados a veces mostraban costuras o espacios visibles en el punto de conexión.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.105</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p><b>Novidades da versão 1.105:</b></p>
    <ul>
        <li><b>Grade de máscaras:</b> Visualize rapidamente quantos fios de máscara são criados usando renderização forte de grade NxN com funcionalidade de grupo fixo.</li>
        <li><b>Atalhos de teclado:</b> Espaço para mover, Z desfazer, X refazer, N novo fio, 1 nomes, L bloquear, D excluir, A desmarcar.</li>
        <li><b>Seleção e zoom corrigidos:</b> Seleção no modo zoom, a seleção e conexão agora permanecem precisas em todos os níveis de zoom.</li>
        <li><b>Conexões de nós mais suaves:</b> Correção de renderização onde nós fechados às vezes mostravam costuras ou lacunas visíveis no ponto de conexão.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.105</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p><b>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.105:</b></p>
    <ul>
        <li><b>&#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E6;&#x05D5;&#x05E8; &#x05D1;&#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D0;&#x05DE;&#x05E6;&#x05E2;&#x05D5;&#x05EA; &#x05DE;&#x05DE;&#x05E9;&#x05E7; &#x05E8;&#x05E9;&#x05EA; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; N&#215;N &#x05D1;&#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E7;&#x05D9;&#x05E6;&#x05D5;&#x05E8;&#x05D9; &#x05DE;&#x05E7;&#x05DC;&#x05D3;&#x05EA;:</b> &#x05E8;&#x05D5;&#x05D5;&#x05D7; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;, Z &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;, X &#x05DC;&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8;, N &#x05DC;&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;, 1 &#x05DC;&#x05E9;&#x05DE;&#x05D5;&#x05EA;, L &#x05DC;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;, D &#x05DC;&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4;, A &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D6;&#x05D5;&#x05DD; &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5;:</b> &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1;&#x05D9; &#x05D4;&#x05D6;&#x05D6;&#x05D4;, &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05EA; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D4;&#x05D6;&#x05D5;&#x05DD;.</li>
        <li><b>&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05DC;&#x05E7;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05D9;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05D1;&#x05D4; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D4;&#x05E6;&#x05D9;&#x05D2;&#x05D5; &#x05DC;&#x05E4;&#x05E2;&#x05DE;&#x05D9;&#x05DD; &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05E4;&#x05E2;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05D1;&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome Italian + localized sections).
cat > "$RESOURCES_DIR/it.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.105</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p><b>Novità della versione 1.105:</b></p>
    <ul>
        <li><b>Griglia maschere:</b> Visualizza rapidamente quanti fili maschera vengono creati utilizzando un forte rendering griglia NxN con funzionalità gruppo fisso.</li>
        <li><b>Scorciatoie tastiera:</b> Spazio per spostare, Z annulla, X ripristina, N nuovo filo, 1 nomi, L blocca, D elimina, A deseleziona.</li>
        <li><b>Selezione e zoom corretti:</b> Selezione in modalità zoom, la selezione e connessione ora rimangono accurate a tutti i livelli di zoom.</li>
        <li><b>Connessioni nodi più fluide:</b> Correzione rendering dove nodi chiusi mostravano talvolta cuciture o spazi visibili nel punto di connessione.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.105</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p><b>What's New in Version 1.105:</b></p>
    <ul>
        <li><b>Mask Grid:</b> Quickly visualize how many mask strands are created using strong NxN grid rendering with fixed group functionality.</li>
        <li><b>Keyboard Shortcuts:</b> Space to move, Z to undo, X to redo, N for new strand, 1 for names, L for lock, D for delete, A to deselect.</li>
        <li><b>Fixed Selection & Zoom:</b> Selection during zoom mode, selection and connection now remain accurate at all zoom levels.</li>
        <li><b>Smoother Knot Connections:</b> Rendering fix where closed knots sometimes showed seams or visible gaps at the connection point.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.105</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p><b>Neu in Version 1.105:</b></p>
    <ul>
        <li><b>Maskengitter:</b> Visualisieren Sie schnell, wie viele Maskenstränge erstellt werden, mit starkem NxN-Gitter-Rendering und fester Gruppenfunktion.</li>
        <li><b>Tastaturkürzel:</b> Leertaste zum Verschieben, Z zum Rückgängig, X zum Wiederholen, N für neuen Strang, 1 für Namen, L zum Sperren, D zum Löschen, A zum Abwählen.</li>
        <li><b>Auswahl und Zoom korrigiert:</b> Auswahl im Zoom-Modus, Auswahl und Verbindung bleiben jetzt bei allen Zoomstufen genau.</li>
        <li><b>Glattere Knotenverbindungen:</b> Rendering-Korrektur, bei der geschlossene Knoten manchmal Nähte oder sichtbare Lücken am Verbindungspunkt zeigten.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.105</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p><b>Nouveautés de la version 1.105:</b></p>
    <ul>
        <li><b>Grille de masques:</b> Visualisez rapidement le nombre de brins de masque créés grâce à un rendu puissant de grille NxN avec fonction de groupe fixe.</li>
        <li><b>Raccourcis clavier:</b> Espace pour déplacer, Z annuler, X rétablir, N nouveau brin, 1 noms, L verrouiller, D supprimer, A désélectionner.</li>
        <li><b>Sélection et zoom corrigés:</b> Sélection en mode zoom, la sélection et la connexion restent désormais précises à tous les niveaux de zoom.</li>
        <li><b>Connexions de nœuds plus fluides:</b> Correction de rendu où les nœuds fermés montraient parfois des coutures ou des espaces visibles au point de connexion.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.105</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p><b>Novedades de la versión 1.105:</b></p>
    <ul>
        <li><b>Cuadrícula de máscaras:</b> Visualice rápidamente cuántos hilos de máscara se crean usando renderizado fuerte de cuadrícula NxN con funcionalidad de grupo fijo.</li>
        <li><b>Atajos de teclado:</b> Espacio para mover, Z deshacer, X rehacer, N nuevo hilo, 1 nombres, L bloquear, D eliminar, A deseleccionar.</li>
        <li><b>Selección y zoom corregidos:</b> Selección en modo zoom, la selección y conexión ahora permanecen precisas en todos los niveles de zoom.</li>
        <li><b>Conexiones de nudos más suaves:</b> Corrección de renderizado donde nudos cerrados a veces mostraban costuras o espacios visibles en el punto de conexión.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.105</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p><b>Novidades da versão 1.105:</b></p>
    <ul>
        <li><b>Grade de máscaras:</b> Visualize rapidamente quantos fios de máscara são criados usando renderização forte de grade NxN com funcionalidade de grupo fixo.</li>
        <li><b>Atalhos de teclado:</b> Espaço para mover, Z desfazer, X refazer, N novo fio, 1 nomes, L bloquear, D excluir, A desmarcar.</li>
        <li><b>Seleção e zoom corrigidos:</b> Seleção no modo zoom, a seleção e conexão agora permanecem precisas em todos os níveis de zoom.</li>
        <li><b>Conexões de nós mais suaves:</b> Correção de renderização onde nós fechados às vezes mostravam costuras ou lacunas visíveis no ponto de conexão.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.105</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p><b>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.105:</b></p>
    <ul>
        <li><b>&#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E6;&#x05D5;&#x05E8; &#x05D1;&#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D0;&#x05DE;&#x05E6;&#x05E2;&#x05D5;&#x05EA; &#x05DE;&#x05DE;&#x05E9;&#x05E7; &#x05E8;&#x05E9;&#x05EA; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; N&#215;N &#x05D1;&#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E7;&#x05D9;&#x05E6;&#x05D5;&#x05E8;&#x05D9; &#x05DE;&#x05E7;&#x05DC;&#x05D3;&#x05EA;:</b> &#x05E8;&#x05D5;&#x05D5;&#x05D7; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;, Z &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;, X &#x05DC;&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8;, N &#x05DC;&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;, 1 &#x05DC;&#x05E9;&#x05DE;&#x05D5;&#x05EA;, L &#x05DC;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;, D &#x05DC;&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4;, A &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D6;&#x05D5;&#x05DD; &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5;:</b> &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1;&#x05D9; &#x05D4;&#x05D6;&#x05D6;&#x05D4;, &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05EA; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D4;&#x05D6;&#x05D5;&#x05DD;.</li>
        <li><b>&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05DC;&#x05E7;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05D9;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05D1;&#x05D4; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D4;&#x05E6;&#x05D9;&#x05D2;&#x05D5; &#x05DC;&#x05E4;&#x05E2;&#x05DE;&#x05D9;&#x05DD; &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05E4;&#x05E2;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05D1;&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome Spanish + localized sections).
cat > "$RESOURCES_DIR/es.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.105</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p><b>Novedades de la versión 1.105:</b></p>
    <ul>
        <li><b>Cuadrícula de máscaras:</b> Visualice rápidamente cuántos hilos de máscara se crean usando renderizado fuerte de cuadrícula NxN con funcionalidad de grupo fijo.</li>
        <li><b>Atajos de teclado:</b> Espacio para mover, Z deshacer, X rehacer, N nuevo hilo, 1 nombres, L bloquear, D eliminar, A deseleccionar.</li>
        <li><b>Selección y zoom corregidos:</b> Selección en modo zoom, la selección y conexión ahora permanecen precisas en todos los niveles de zoom.</li>
        <li><b>Conexiones de nudos más suaves:</b> Corrección de renderizado donde nudos cerrados a veces mostraban costuras o espacios visibles en el punto de conexión.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.105</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p><b>What's New in Version 1.105:</b></p>
    <ul>
        <li><b>Mask Grid:</b> Quickly visualize how many mask strands are created using strong NxN grid rendering with fixed group functionality.</li>
        <li><b>Keyboard Shortcuts:</b> Space to move, Z to undo, X to redo, N for new strand, 1 for names, L for lock, D for delete, A to deselect.</li>
        <li><b>Fixed Selection & Zoom:</b> Selection during zoom mode, selection and connection now remain accurate at all zoom levels.</li>
        <li><b>Smoother Knot Connections:</b> Rendering fix where closed knots sometimes showed seams or visible gaps at the connection point.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.105</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p><b>Nouveautés de la version 1.105:</b></p>
    <ul>
        <li><b>Grille de masques:</b> Visualisez rapidement le nombre de brins de masque créés grâce à un rendu puissant de grille NxN avec fonction de groupe fixe.</li>
        <li><b>Raccourcis clavier:</b> Espace pour déplacer, Z annuler, X rétablir, N nouveau brin, 1 noms, L verrouiller, D supprimer, A désélectionner.</li>
        <li><b>Sélection et zoom corrigés:</b> Sélection en mode zoom, la sélection et la connexion restent désormais précises à tous les niveaux de zoom.</li>
        <li><b>Connexions de nœuds plus fluides:</b> Correction de rendu où les nœuds fermés montraient parfois des coutures ou des espaces visibles au point de connexion.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.105</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p><b>Neu in Version 1.105:</b></p>
    <ul>
        <li><b>Maskengitter:</b> Visualisieren Sie schnell, wie viele Maskenstränge erstellt werden, mit starkem NxN-Gitter-Rendering und fester Gruppenfunktion.</li>
        <li><b>Tastaturkürzel:</b> Leertaste zum Verschieben, Z zum Rückgängig, X zum Wiederholen, N für neuen Strang, 1 für Namen, L zum Sperren, D zum Löschen, A zum Abwählen.</li>
        <li><b>Auswahl und Zoom korrigiert:</b> Auswahl im Zoom-Modus, Auswahl und Verbindung bleiben jetzt bei allen Zoomstufen genau.</li>
        <li><b>Glattere Knotenverbindungen:</b> Rendering-Korrektur, bei der geschlossene Knoten manchmal Nähte oder sichtbare Lücken am Verbindungspunkt zeigten.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.105</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p><b>Novità della versione 1.105:</b></p>
    <ul>
        <li><b>Griglia maschere:</b> Visualizza rapidamente quanti fili maschera vengono creati utilizzando un forte rendering griglia NxN con funzionalità gruppo fisso.</li>
        <li><b>Scorciatoie tastiera:</b> Spazio per spostare, Z annulla, X ripristina, N nuovo filo, 1 nomi, L blocca, D elimina, A deseleziona.</li>
        <li><b>Selezione e zoom corretti:</b> Selezione in modalità zoom, la selezione e connessione ora rimangono accurate a tutti i livelli di zoom.</li>
        <li><b>Connessioni nodi più fluide:</b> Correzione rendering dove nodi chiusi mostravano talvolta cuciture o spazi visibili nel punto di connessione.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.105</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p><b>Novidades da versão 1.105:</b></p>
    <ul>
        <li><b>Grade de máscaras:</b> Visualize rapidamente quantos fios de máscara são criados usando renderização forte de grade NxN com funcionalidade de grupo fixo.</li>
        <li><b>Atalhos de teclado:</b> Espaço para mover, Z desfazer, X refazer, N novo fio, 1 nomes, L bloquear, D excluir, A desmarcar.</li>
        <li><b>Seleção e zoom corrigidos:</b> Seleção no modo zoom, a seleção e conexão agora permanecem precisas em todos os níveis de zoom.</li>
        <li><b>Conexões de nós mais suaves:</b> Correção de renderização onde nós fechados às vezes mostravam costuras ou lacunas visíveis no ponto de conexão.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.105</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p><b>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.105:</b></p>
    <ul>
        <li><b>&#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E6;&#x05D5;&#x05E8; &#x05D1;&#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D0;&#x05DE;&#x05E6;&#x05E2;&#x05D5;&#x05EA; &#x05DE;&#x05DE;&#x05E9;&#x05E7; &#x05E8;&#x05E9;&#x05EA; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; N&#215;N &#x05D1;&#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E7;&#x05D9;&#x05E6;&#x05D5;&#x05E8;&#x05D9; &#x05DE;&#x05E7;&#x05DC;&#x05D3;&#x05EA;:</b> &#x05E8;&#x05D5;&#x05D5;&#x05D7; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;, Z &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;, X &#x05DC;&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8;, N &#x05DC;&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;, 1 &#x05DC;&#x05E9;&#x05DE;&#x05D5;&#x05EA;, L &#x05DC;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;, D &#x05DC;&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4;, A &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D6;&#x05D5;&#x05DD; &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5;:</b> &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1;&#x05D9; &#x05D4;&#x05D6;&#x05D6;&#x05D4;, &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05EA; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D4;&#x05D6;&#x05D5;&#x05DD;.</li>
        <li><b>&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05DC;&#x05E7;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05D9;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05D1;&#x05D4; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D4;&#x05E6;&#x05D9;&#x05D2;&#x05D5; &#x05DC;&#x05E4;&#x05E2;&#x05DE;&#x05D9;&#x05DD; &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05E4;&#x05E2;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05D1;&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome Portuguese + localized sections).
cat > "$RESOURCES_DIR/pt.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.105</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p><b>Novidades da versão 1.105:</b></p>
    <ul>
        <li><b>Grade de máscaras:</b> Visualize rapidamente quantos fios de máscara são criados usando renderização forte de grade NxN com funcionalidade de grupo fixo.</li>
        <li><b>Atalhos de teclado:</b> Espaço para mover, Z desfazer, X refazer, N novo fio, 1 nomes, L bloquear, D excluir, A desmarcar.</li>
        <li><b>Seleção e zoom corrigidos:</b> Seleção no modo zoom, a seleção e conexão agora permanecem precisas em todos os níveis de zoom.</li>
        <li><b>Conexões de nós mais suaves:</b> Correção de renderização onde nós fechados às vezes mostravam costuras ou lacunas visíveis no ponto de conexão.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.105</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p><b>What's New in Version 1.105:</b></p>
    <ul>
        <li><b>Mask Grid:</b> Quickly visualize how many mask strands are created using strong NxN grid rendering with fixed group functionality.</li>
        <li><b>Keyboard Shortcuts:</b> Space to move, Z to undo, X to redo, N for new strand, 1 for names, L for lock, D for delete, A to deselect.</li>
        <li><b>Fixed Selection & Zoom:</b> Selection during zoom mode, selection and connection now remain accurate at all zoom levels.</li>
        <li><b>Smoother Knot Connections:</b> Rendering fix where closed knots sometimes showed seams or visible gaps at the connection point.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.105</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p><b>Nouveautés de la version 1.105:</b></p>
    <ul>
        <li><b>Grille de masques:</b> Visualisez rapidement le nombre de brins de masque créés grâce à un rendu puissant de grille NxN avec fonction de groupe fixe.</li>
        <li><b>Raccourcis clavier:</b> Espace pour déplacer, Z annuler, X rétablir, N nouveau brin, 1 noms, L verrouiller, D supprimer, A désélectionner.</li>
        <li><b>Sélection et zoom corrigés:</b> Sélection en mode zoom, la sélection et la connexion restent désormais précises à tous les niveaux de zoom.</li>
        <li><b>Connexions de nœuds plus fluides:</b> Correction de rendu où les nœuds fermés montraient parfois des coutures ou des espaces visibles au point de connexion.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.105</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p><b>Neu in Version 1.105:</b></p>
    <ul>
        <li><b>Maskengitter:</b> Visualisieren Sie schnell, wie viele Maskenstränge erstellt werden, mit starkem NxN-Gitter-Rendering und fester Gruppenfunktion.</li>
        <li><b>Tastaturkürzel:</b> Leertaste zum Verschieben, Z zum Rückgängig, X zum Wiederholen, N für neuen Strang, 1 für Namen, L zum Sperren, D zum Löschen, A zum Abwählen.</li>
        <li><b>Auswahl und Zoom korrigiert:</b> Auswahl im Zoom-Modus, Auswahl und Verbindung bleiben jetzt bei allen Zoomstufen genau.</li>
        <li><b>Glattere Knotenverbindungen:</b> Rendering-Korrektur, bei der geschlossene Knoten manchmal Nähte oder sichtbare Lücken am Verbindungspunkt zeigten.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.105</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p><b>Novità della versione 1.105:</b></p>
    <ul>
        <li><b>Griglia maschere:</b> Visualizza rapidamente quanti fili maschera vengono creati utilizzando un forte rendering griglia NxN con funzionalità gruppo fisso.</li>
        <li><b>Scorciatoie tastiera:</b> Spazio per spostare, Z annulla, X ripristina, N nuovo filo, 1 nomi, L blocca, D elimina, A deseleziona.</li>
        <li><b>Selezione e zoom corretti:</b> Selezione in modalità zoom, la selezione e connessione ora rimangono accurate a tutti i livelli di zoom.</li>
        <li><b>Connessioni nodi più fluide:</b> Correzione rendering dove nodi chiusi mostravano talvolta cuciture o spazi visibili nel punto di connessione.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.105</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p><b>Novedades de la versión 1.105:</b></p>
    <ul>
        <li><b>Cuadrícula de máscaras:</b> Visualice rápidamente cuántos hilos de máscara se crean usando renderizado fuerte de cuadrícula NxN con funcionalidad de grupo fijo.</li>
        <li><b>Atajos de teclado:</b> Espacio para mover, Z deshacer, X rehacer, N nuevo hilo, 1 nombres, L bloquear, D eliminar, A deseleccionar.</li>
        <li><b>Selección y zoom corregidos:</b> Selección en modo zoom, la selección y conexión ahora permanecen precisas en todos los niveles de zoom.</li>
        <li><b>Conexiones de nudos más suaves:</b> Corrección de renderizado donde nudos cerrados a veces mostraban costuras o espacios visibles en el punto de conexión.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.105</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p><b>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.105:</b></p>
    <ul>
        <li><b>&#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E6;&#x05D5;&#x05E8; &#x05D1;&#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D0;&#x05DE;&#x05E6;&#x05E2;&#x05D5;&#x05EA; &#x05DE;&#x05DE;&#x05E9;&#x05E7; &#x05E8;&#x05E9;&#x05EA; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; N&#215;N &#x05D1;&#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E7;&#x05D9;&#x05E6;&#x05D5;&#x05E8;&#x05D9; &#x05DE;&#x05E7;&#x05DC;&#x05D3;&#x05EA;:</b> &#x05E8;&#x05D5;&#x05D5;&#x05D7; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;, Z &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;, X &#x05DC;&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8;, N &#x05DC;&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;, 1 &#x05DC;&#x05E9;&#x05DE;&#x05D5;&#x05EA;, L &#x05DC;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;, D &#x05DC;&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4;, A &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D6;&#x05D5;&#x05DD; &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5;:</b> &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1;&#x05D9; &#x05D4;&#x05D6;&#x05D6;&#x05D4;, &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05EA; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D4;&#x05D6;&#x05D5;&#x05DD;.</li>
        <li><b>&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05DC;&#x05E7;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05D9;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05D1;&#x05D4; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D4;&#x05E6;&#x05D9;&#x05D2;&#x05D5; &#x05DC;&#x05E4;&#x05E2;&#x05DE;&#x05D9;&#x05DD; &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05E4;&#x05E2;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05D1;&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome Hebrew + localized sections).
cat > "$RESOURCES_DIR/he.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.105</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p><b>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.105:</b></p>
    <ul>
        <li><b>&#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E6;&#x05D5;&#x05E8; &#x05D1;&#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D0;&#x05DE;&#x05E6;&#x05E2;&#x05D5;&#x05EA; &#x05DE;&#x05DE;&#x05E9;&#x05E7; &#x05E8;&#x05E9;&#x05EA; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; N&#215;N &#x05D1;&#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E7;&#x05D9;&#x05E6;&#x05D5;&#x05E8;&#x05D9; &#x05DE;&#x05E7;&#x05DC;&#x05D3;&#x05EA;:</b> &#x05E8;&#x05D5;&#x05D5;&#x05D7; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;, Z &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;, X &#x05DC;&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8;, N &#x05DC;&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;, 1 &#x05DC;&#x05E9;&#x05DE;&#x05D5;&#x05EA;, L &#x05DC;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;, D &#x05DC;&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4;, A &#x05DC;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D6;&#x05D5;&#x05DD; &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5;:</b> &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1;&#x05D9; &#x05D4;&#x05D6;&#x05D6;&#x05D4;, &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05EA; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D4;&#x05D6;&#x05D5;&#x05DD;.</li>
        <li><b>&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05DC;&#x05E7;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05D9;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05D1;&#x05D4; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D4;&#x05E6;&#x05D9;&#x05D2;&#x05D5; &#x05DC;&#x05E4;&#x05E2;&#x05DE;&#x05D9;&#x05DD; &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05E4;&#x05E2;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05D1;&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;.</li>
    </ul>
    </div>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.105</h2>
    <p dir="ltr">This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p dir="ltr"><b>What's New in Version 1.105:</b></p>
    <ul dir="ltr">
        <li><b>Mask Grid:</b> Quickly visualize how many mask strands are created using strong NxN grid rendering with fixed group functionality.</li>
        <li><b>Keyboard Shortcuts:</b> Space to move, Z to undo, X to redo, N for new strand, 1 for names, L for lock, D for delete, A to deselect.</li>
        <li><b>Fixed Selection & Zoom:</b> Selection during zoom mode, selection and connection now remain accurate at all zoom levels.</li>
        <li><b>Smoother Knot Connections:</b> Rendering fix where closed knots sometimes showed seams or visible gaps at the connection point.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.105</h2>
    <p dir="ltr">Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p dir="ltr"><b>Nouveautés de la version 1.105:</b></p>
    <ul dir="ltr">
        <li><b>Grille de masques:</b> Visualisez rapidement le nombre de brins de masque créés grâce à un rendu puissant de grille NxN avec fonction de groupe fixe.</li>
        <li><b>Raccourcis clavier:</b> Espace pour déplacer, Z annuler, X rétablir, N nouveau brin, 1 noms, L verrouiller, D supprimer, A désélectionner.</li>
        <li><b>Sélection et zoom corrigés:</b> Sélection en mode zoom, la sélection et la connexion restent désormais précises à tous les niveaux de zoom.</li>
        <li><b>Connexions de nœuds plus fluides:</b> Correction de rendu où les nœuds fermés montraient parfois des coutures ou des espaces visibles au point de connexion.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.105</h2>
    <p dir="ltr">Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p dir="ltr"><b>Neu in Version 1.105:</b></p>
    <ul dir="ltr">
        <li><b>Maskengitter:</b> Visualisieren Sie schnell, wie viele Maskenstränge erstellt werden, mit starkem NxN-Gitter-Rendering und fester Gruppenfunktion.</li>
        <li><b>Tastaturkürzel:</b> Leertaste zum Verschieben, Z zum Rückgängig, X zum Wiederholen, N für neuen Strang, 1 für Namen, L zum Sperren, D zum Löschen, A zum Abwählen.</li>
        <li><b>Auswahl und Zoom korrigiert:</b> Auswahl im Zoom-Modus, Auswahl und Verbindung bleiben jetzt bei allen Zoomstufen genau.</li>
        <li><b>Glattere Knotenverbindungen:</b> Rendering-Korrektur, bei der geschlossene Knoten manchmal Nähte oder sichtbare Lücken am Verbindungspunkt zeigten.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.105</h2>
    <p dir="ltr">Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p dir="ltr"><b>Novità della versione 1.105:</b></p>
    <ul dir="ltr">
        <li><b>Griglia maschere:</b> Visualizza rapidamente quanti fili maschera vengono creati utilizzando un forte rendering griglia NxN con funzionalità gruppo fisso.</li>
        <li><b>Scorciatoie tastiera:</b> Spazio per spostare, Z annulla, X ripristina, N nuovo filo, 1 nomi, L blocca, D elimina, A deseleziona.</li>
        <li><b>Selezione e zoom corretti:</b> Selezione in modalità zoom, la selezione e connessione ora rimangono accurate a tutti i livelli di zoom.</li>
        <li><b>Connessioni nodi più fluide:</b> Correzione rendering dove nodi chiusi mostravano talvolta cuciture o spazi visibili nel punto di connessione.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.105</h2>
    <p dir="ltr">Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p dir="ltr"><b>Novedades de la versión 1.105:</b></p>
    <ul dir="ltr">
        <li><b>Cuadrícula de máscaras:</b> Visualice rápidamente cuántos hilos de máscara se crean usando renderizado fuerte de cuadrícula NxN con funcionalidad de grupo fijo.</li>
        <li><b>Atajos de teclado:</b> Espacio para mover, Z deshacer, X rehacer, N nuevo hilo, 1 nombres, L bloquear, D eliminar, A deseleccionar.</li>
        <li><b>Selección y zoom corregidos:</b> Selección en modo zoom, la selección y conexión ahora permanecen precisas en todos los niveles de zoom.</li>
        <li><b>Conexiones de nudos más suaves:</b> Corrección de renderizado donde nudos cerrados a veces mostraban costuras o espacios visibles en el punto de conexión.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.105</h2>
    <p dir="ltr">Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p dir="ltr"><b>Novidades da versão 1.105:</b></p>
    <ul dir="ltr">
        <li><b>Grade de máscaras:</b> Visualize rapidamente quantos fios de máscara são criados usando renderização forte de grade NxN com funcionalidade de grupo fixo.</li>
        <li><b>Atalhos de teclado:</b> Espaço para mover, Z desfazer, X refazer, N novo fio, 1 nomes, L bloquear, D excluir, A desmarcar.</li>
        <li><b>Seleção e zoom corrigidos:</b> Seleção no modo zoom, a seleção e conexão agora permanecem precisas em todos os níveis de zoom.</li>
        <li><b>Conexões de nós mais suaves:</b> Correção de renderização onde nós fechados às vezes mostravam costuras ou lacunas visíveis no ponto de conexão.</li>
    </ul>
</body>
</html>
EOF

# Build component package
echo "Building component package..."
pkgbuild \
    --root "/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/dist/OpenStrandStudio.app" \
    --install-location "/Applications/OpenStrandStudio.app" \
    --scripts "$SCRIPTS_DIR" \
    --identifier "$IDENTIFIER" \
    --version "$VERSION" \
    "$WORKING_DIR/OpenStrandStudio.pkg"

if [ ! -f "$WORKING_DIR/OpenStrandStudio.pkg" ]; then
    echo "Error: Failed to create component package"
    exit 1
fi

# Build product package
echo "Building product package..."
productbuild \
    --distribution "$WORKING_DIR/Distribution.xml" \
    --resources "$RESOURCES_DIR" \
    --package-path "$WORKING_DIR" \
    "$PKG_PATH"

if [ ! -f "$PKG_PATH" ]; then
    echo "Error: Failed to create product package"
    exit 1
fi

# Sign the package (optional - requires Developer ID)
# productbuild --sign "Developer ID Installer: Your Name (XXXXXXXXXX)" "$PKG_PATH" "$PKG_PATH.signed"
# mv "$PKG_PATH.signed" "$PKG_PATH"

# Verify the package
echo "Verifying package..."
pkgutil --check-signature "$PKG_PATH" 2>/dev/null || echo "Package is unsigned (normal for development)"

# Clean up
rm -rf "$WORKING_DIR"

echo "Package created successfully at: $PKG_PATH"
echo "Version: $VERSION"
echo "Publisher: $PUBLISHER"

# Test the installer
echo "To test the installer, run:"
echo "sudo installer -pkg \"$PKG_PATH\" -target /"

# Open the installer_output directory
open "$(dirname "$PKG_PATH")"

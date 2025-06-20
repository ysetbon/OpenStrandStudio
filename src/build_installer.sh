#!/bin/bash

# Set variables
APP_NAME="OpenStrandStudio"
VERSION="1_100"
APP_DATE="19_June_2025"
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

# Create welcome.html (English default)
cat > "$RESOURCES_DIR/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.100</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li>Persistent Undo/Redo History: Your undo and redo actions are now saved with your project.</li>
        <li>Customizable Dashed Lines and Arrowheads for strands.</li>
        <li>Improved Control Point Visuals with larger handles.</li>
        <li>Mask Extension Options for finer control.</li>
        <li>Enhanced Shading Algorithm with smoother shadows.</li>
        <li>Upgraded Layer Panel with drag-and-drop reordering and quick visibility toggles.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.100</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li>&#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D9;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;.</li>
        <li>&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D9;&#x05E6;&#x05D9;&#x05DD; &#x05DE;&#x05E7;&#x05D5;&#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05D0;&#x05DE;&#x05D4; &#x05D0;&#x05D9;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li>&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E8;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05D0;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05E1;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05DC;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05EA;&#x05DD; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05DC;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E8;&#x05DB;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05DC;&#x05D5;&#x05D7; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05E2;&#x05DD; &#x05D2;&#x05E8;&#x05D5;&#x05E8;-&#x05D5;&#x05E9;&#x05D7;&#x05E8;&#x05E8; &#x05D5;&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D4;.</li>
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
declare -a LANG_CODES=("en" "fr" "it" "es" "pt" "he")

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

# French
cat > "$RESOURCES_DIR/fr.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.100</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li>Persistent Undo/Redo History: Your undo and redo actions are now saved with your project.</li>
        <li>Customizable Dashed Lines and Arrowheads for strands.</li>
        <li>Improved Control Point Visuals with larger handles.</li>
        <li>Mask Extension Options for finer control.</li>
        <li>Enhanced Shading Algorithm with smoother shadows.</li>
        <li>Upgraded Layer Panel with drag-and-drop reordering and quick visibility toggles.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.100</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li>&#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D9;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;.</li>
        <li>&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D9;&#x05E6;&#x05D9;&#x05DD; &#x05DE;&#x05E7;&#x05D5;&#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05D0;&#x05DE;&#x05D4; &#x05D0;&#x05D9;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li>&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E8;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05D0;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05E1;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05DC;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05EA;&#x05DD; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05DC;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E8;&#x05DB;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05DC;&#x05D5;&#x05D7; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05E2;&#x05DD; &#x05D2;&#x05E8;&#x05D5;&#x05E8;-&#x05D5;&#x05E9;&#x05D7;&#x05E8;&#x05E8; &#x05D5;&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D4;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Italian
cat > "$RESOURCES_DIR/it.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.100</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li>Persistent Undo/Redo History: Your undo and redo actions are now saved with your project.</li>
        <li>Customizable Dashed Lines and Arrowheads for strands.</li>
        <li>Improved Control Point Visuals with larger handles.</li>
        <li>Mask Extension Options for finer control.</li>
        <li>Enhanced Shading Algorithm with smoother shadows.</li>
        <li>Upgraded Layer Panel with drag-and-drop reordering and quick visibility toggles.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.100</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li>&#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D9;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;.</li>
        <li>&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D9;&#x05E6;&#x05D9;&#x05DD; &#x05DE;&#x05E7;&#x05D5;&#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05D0;&#x05DE;&#x05D4; &#x05D0;&#x05D9;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li>&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E8;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05D0;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05E1;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05DC;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05EA;&#x05DD; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05DC;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E8;&#x05DB;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05DC;&#x05D5;&#x05D7; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05E2;&#x05DD; &#x05D2;&#x05E8;&#x05D5;&#x05E8;-&#x05D5;&#x05E9;&#x05D7;&#x05E8;&#x05E8; &#x05D5;&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D4;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Spanish
cat > "$RESOURCES_DIR/es.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.100</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li>Persistent Undo/Redo History: Your undo and redo actions are now saved with your project.</li>
        <li>Customizable Dashed Lines and Arrowheads for strands.</li>
        <li>Improved Control Point Visuals with larger handles.</li>
        <li>Mask Extension Options for finer control.</li>
        <li>Enhanced Shading Algorithm with smoother shadows.</li>
        <li>Upgraded Layer Panel with drag-and-drop reordering and quick visibility toggles.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.100</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li>&#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D9;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;.</li>
        <li>&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D9;&#x05E6;&#x05D9;&#x05DD; &#x05DE;&#x05E7;&#x05D5;&#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05D0;&#x05DE;&#x05D4; &#x05D0;&#x05D9;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li>&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E8;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05D0;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05E1;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05DC;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05EA;&#x05DD; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05DC;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E8;&#x05DB;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05DC;&#x05D5;&#x05D7; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05E2;&#x05DD; &#x05D2;&#x05E8;&#x05D5;&#x05E8;-&#x05D5;&#x05E9;&#x05D7;&#x05E8;&#x05E8; &#x05D5;&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D4;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Portuguese
cat > "$RESOURCES_DIR/pt.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.100</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li>Persistent Undo/Redo History: Your undo and redo actions are now saved with your project.</li>
        <li>Customizable Dashed Lines and Arrowheads for strands.</li>
        <li>Improved Control Point Visuals with larger handles.</li>
        <li>Mask Extension Options for finer control.</li>
        <li>Enhanced Shading Algorithm with smoother shadows.</li>
        <li>Upgraded Layer Panel with drag-and-drop reordering and quick visibility toggles.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.100</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li>&#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D9;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;.</li>
        <li>&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D9;&#x05E6;&#x05D9;&#x05DD; &#x05DE;&#x05E7;&#x05D5;&#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05D0;&#x05DE;&#x05D4; &#x05D0;&#x05D9;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li>&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E8;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05D0;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05E1;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05DC;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05EA;&#x05DD; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05DC;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E8;&#x05DB;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05DC;&#x05D5;&#x05D7; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05E2;&#x05DD; &#x05D2;&#x05E8;&#x05D5;&#x05E8;-&#x05D5;&#x05E9;&#x05D7;&#x05E8;&#x05E8; &#x05D5;&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D4;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Hebrew
cat > "$RESOURCES_DIR/he.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.100</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li>&#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D9;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;.</li>
        <li>&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D9;&#x05E6;&#x05D9;&#x05DD; &#x05DE;&#x05E7;&#x05D5;&#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05D0;&#x05DE;&#x05D4; &#x05D0;&#x05D9;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li>&#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E8;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05D0;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05E1;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05D0;&#x05DC;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05EA;&#x05DD; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05DC;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E8;&#x05DB;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li>&#x05DC;&#x05D5;&#x05D7; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8; &#x05E2;&#x05DD; &#x05D2;&#x05E8;&#x05D5;&#x05E8;-&#x05D5;&#x05E9;&#x05D7;&#x05E8;&#x05E8; &#x05D5;&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D4;&#x05D9;&#x05E8;&#x05D4;.</li>
    </ul>
    </div>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.100</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li>Persistent Undo/Redo History: Your undo and redo actions are now saved with your project.</li>
        <li>Customizable Dashed Lines and Arrowheads for strands.</li>
        <li>Improved Control Point Visuals with larger handles.</li>
        <li>Mask Extension Options for finer control.</li>
        <li>Enhanced Shading Algorithm with smoother shadows.</li>
        <li>Upgraded Layer Panel with drag-and-drop reordering and quick visibility toggles.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.100</h2>
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
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.100</h2>
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

# Create component package
pkgbuild \
    --root "/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/dist/OpenStrandStudio.app" \
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
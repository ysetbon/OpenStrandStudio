#!/bin/bash

################################################################################
# OpenStrand Studio macOS PKG Installer Builder for Version 1.104
# Date: November 2, 2025
#
# LOGIC EXPLANATION:
# ==================
# This script creates a macOS .pkg installer with full multilingual support
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
# TODO MARKERS:
# -------------
# Search for "[TODO:" or "<!-- TODO:" to find all places where version 1.104
# features need to be added. Current content shows 1.103 features as templates.
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
VERSION="1_104"
APP_DATE="02_November_2025"
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

# Create welcome.html (English + localized sections). Updated to 1.104 what's-new.
cat > "$RESOURCES_DIR/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.104</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.104:</p>
    <ul>
        <li><b>Enhanced Control Point System:</b> Improved UX for control point movement and activation behavior. Better visual feedback and smoother interaction when working with control points.</li>
        <li><b>Endpoint Properties Management:</b> Save samples and duplicate endpoint properties functionality. Streamlined workflow for managing endpoint configurations.</li>
        <li><b>Advanced Shadow Editor:</b> Fixed dialog layout with multi-language support, subtraction operations, and improved history table for better shadow management.</li>
        <li><b>User Settings Persistence:</b> Save and load functionality for user settings, ensuring your preferences are maintained across sessions.</li>
        <li><b>Rendering Improvements:</b> Fixed side line rendering issues and enhanced undo/redo functionality for more reliable visual output.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.104</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbessertes Kontrollpunktsystem:</b> Verbesserte Benutzerführung für Kontrollpunktbewegung und Aktivierungsverhalten. Besseres visuelles Feedback und flüssigere Interaktion bei der Arbeit mit Kontrollpunkten.</li>
        <li><b>Endpunkt-Eigenschaften-Verwaltung:</b> Speichern von Mustern und Duplizieren von Endpunkt-Eigenschaften. Optimierter Arbeitsablauf für die Verwaltung von Endpunkt-Konfigurationen.</li>
        <li><b>Erweiterter Schatten-Editor:</b> Korrigiertes Dialog-Layout mit Mehrsprachenunterstützung, Subtraktionsoperationen und verbesserter Verlaufstabelle für besseres Schatten-Management.</li>
        <li><b>Benutzereinstellungen-Persistenz:</b> Speicher- und Ladefunktion für Benutzereinstellungen, damit Ihre Präferenzen sitzungsübergreifend erhalten bleiben.</li>
        <li><b>Rendering-Verbesserungen:</b> Behobene Seitenlinien-Rendering-Probleme und verbesserte Rückgängig/Wiederherstellen-Funktionalität für zuverlässigere visuelle Ausgabe.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.104</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Système de points de contrôle amélioré :</b> Interface utilisateur améliorée pour le mouvement des points de contrôle et le comportement d'activation. Meilleur retour visuel et interaction plus fluide lors du travail avec les points de contrôle.</li>
        <li><b>Gestion des propriétés des extrémités :</b> Fonctionnalité de sauvegarde d'échantillons et de duplication des propriétés des extrémités. Flux de travail optimisé pour la gestion des configurations d'extrémités.</li>
        <li><b>Éditeur d'ombres avancé :</b> Disposition de dialogue corrigée avec prise en charge multilingue, opérations de soustraction et table d'historique améliorée pour une meilleure gestion des ombres.</li>
        <li><b>Persistance des paramètres utilisateur :</b> Fonctionnalité de sauvegarde et de chargement des paramètres utilisateur, garantissant que vos préférences sont maintenues d'une session à l'autre.</li>
        <li><b>Améliorations du rendu :</b> Correction des problèmes de rendu des lignes latérales et amélioration de la fonctionnalité annuler/rétablir pour une sortie visuelle plus fiable.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.104</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Sistema di punti di controllo migliorato:</b> Migliorata l'esperienza utente per il movimento dei punti di controllo e il comportamento di attivazione. Miglior feedback visivo e interazione più fluida quando si lavora con i punti di controllo.</li>
        <li><b>Gestione delle proprietà degli endpoint:</b> Funzionalità di salvataggio campioni e duplicazione delle proprietà degli endpoint. Flusso di lavoro ottimizzato per la gestione delle configurazioni degli endpoint.</li>
        <li><b>Editor di ombre avanzato:</b> Layout della finestra di dialogo corretto con supporto multilingue, operazioni di sottrazione e tabella cronologia migliorata per una migliore gestione delle ombre.</li>
        <li><b>Persistenza delle impostazioni utente:</b> Funzionalità di salvataggio e caricamento delle impostazioni utente, garantendo che le preferenze vengano mantenute tra le sessioni.</li>
        <li><b>Miglioramenti del rendering:</b> Risolti i problemi di rendering delle linee laterali e migliorata la funzionalità annulla/ripristina per un output visivo più affidabile.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.104</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Sistema de puntos de control mejorado:</b> Mejor experiencia de usuario para el movimiento de puntos de control y comportamiento de activación. Mejor retroalimentación visual e interacción más fluida al trabajar con puntos de control.</li>
        <li><b>Gestión de propiedades de puntos finales:</b> Funcionalidad de guardar muestras y duplicar propiedades de puntos finales. Flujo de trabajo optimizado para gestionar configuraciones de puntos finales.</li>
        <li><b>Editor de sombras avanzado:</b> Diseño de diálogo corregido con soporte multiidioma, operaciones de sustracción y tabla de historial mejorada para una mejor gestión de sombras.</li>
        <li><b>Persistencia de configuración de usuario:</b> Funcionalidad de guardar y cargar configuración de usuario, asegurando que sus preferencias se mantengan entre sesiones.</li>
        <li><b>Mejoras de renderizado:</b> Solucionados problemas de renderizado de líneas laterales y mejorada la funcionalidad deshacer/rehacer para una salida visual más confiable.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.104</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Sistema de pontos de controle aprimorado:</b> Melhor experiência do usuário para movimento de pontos de controle e comportamento de ativação. Melhor feedback visual e interação mais suave ao trabalhar com pontos de controle.</li>
        <li><b>Gerenciamento de propriedades de pontos finais:</b> Funcionalidade de salvar amostras e duplicar propriedades de pontos finais. Fluxo de trabalho otimizado para gerenciar configurações de pontos finais.</li>
        <li><b>Editor de sombras avançado:</b> Layout de diálogo corrigido com suporte multilíngue, operações de subtração e tabela de histórico aprimorada para melhor gerenciamento de sombras.</li>
        <li><b>Persistência de configurações do usuário:</b> Funcionalidade de salvar e carregar configurações do usuário, garantindo que suas preferências sejam mantidas entre as sessões.</li>
        <li><b>Melhorias de renderização:</b> Corrigidos problemas de renderização de linhas laterais e melhorada a funcionalidade desfazer/refazer para saída visual mais confiável.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.104</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05EA;&#x05E0;&#x05D5;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D5;&#x05D4;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D5;&#x05EA; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D4;. &#x05DE;&#x05E9;&#x05D5;&#x05D1; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D5;&#x05D0;&#x05D9;&#x05E0;&#x05D8;&#x05E8;&#x05D0;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DD; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05D5;&#x05EA; &#x05D5;&#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;. &#x05EA;&#x05D4;&#x05DC;&#x05D9;&#x05DA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05E2;&#x05DC; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05EA;&#x05E6;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DD;:</b> &#x05E4;&#x05E8;&#x05D9;&#x05E1;&#x05EA; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05EA; &#x05E2;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05DB;&#x05D4; &#x05E8;&#x05D1;-&#x05E9;&#x05E4;&#x05EA;&#x05D9;&#x05EA;, &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D7;&#x05D9;&#x05E1;&#x05D5;&#x05E8; &#x05D5;&#x05D8;&#x05D1;&#x05DC;&#x05EA; &#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;, &#x05D4;&#x05DE;&#x05D1;&#x05D8;&#x05D9;&#x05D7;&#x05D4; &#x05E9;&#x05D4;&#x05D4;&#x05E2;&#x05D3;&#x05E4;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DA; &#x05E9;&#x05DE;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05DF; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05D9;&#x05E4;&#x05D5;&#x05E8;&#x05D9; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05E9;&#x05DC; &#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05E6;&#x05D3; &#x05D5;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D4; &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8; &#x05DC;&#x05E4;&#x05DC;&#x05D8; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D0;&#x05DE;&#x05D9;&#x05DF; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
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

# Create welcome.html  (welcome French + localized sections). Updated to 1.104 what's-new.
cat > "$RESOURCES_DIR/fr.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.104</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires pour installer ce logiciel.</p>
    <p>Nouveautés de la version 1.104&nbsp;:</p>
    <ul>
        <li><b>Système de points de contrôle amélioré :</b> Interface utilisateur améliorée pour le mouvement des points de contrôle et le comportement d'activation. Meilleur retour visuel et interaction plus fluide lors du travail avec les points de contrôle.</li>
        <li><b>Gestion des propriétés des extrémités :</b> Fonctionnalité de sauvegarde d'échantillons et de duplication des propriétés des extrémités. Flux de travail optimisé pour la gestion des configurations d'extrémités.</li>
        <li><b>Éditeur d'ombres avancé :</b> Disposition de dialogue corrigée avec prise en charge multilingue, opérations de soustraction et table d'historique améliorée pour une meilleure gestion des ombres.</li>
        <li><b>Persistance des paramètres utilisateur :</b> Fonctionnalité de sauvegarde et de chargement des paramètres utilisateur, garantissant que vos préférences sont maintenues d'une session à l'autre.</li>
        <li><b>Améliorations du rendu :</b> Correction des problèmes de rendu des lignes latérales et amélioration de la fonctionnalité annuler/rétablir pour une sortie visuelle plus fiable.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.104</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.104:</p>
    <ul>
        <li><b>Enhanced Control Point System:</b> Improved UX for control point movement and activation behavior. Better visual feedback and smoother interaction when working with control points.</li>
        <li><b>Endpoint Properties Management:</b> Save samples and duplicate endpoint properties functionality. Streamlined workflow for managing endpoint configurations.</li>
        <li><b>Advanced Shadow Editor:</b> Fixed dialog layout with multi-language support, subtraction operations, and improved history table for better shadow management.</li>
        <li><b>User Settings Persistence:</b> Save and load functionality for user settings, ensuring your preferences are maintained across sessions.</li>
        <li><b>Rendering Improvements:</b> Fixed side line rendering issues and enhanced undo/redo functionality for more reliable visual output.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.104</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbessertes Kontrollpunktsystem:</b> Verbesserte Benutzerführung für Kontrollpunktbewegung und Aktivierungsverhalten. Besseres visuelles Feedback und flüssigere Interaktion bei der Arbeit mit Kontrollpunkten.</li>
        <li><b>Endpunkt-Eigenschaften-Verwaltung:</b> Speichern von Mustern und Duplizieren von Endpunkt-Eigenschaften. Optimierter Arbeitsablauf für die Verwaltung von Endpunkt-Konfigurationen.</li>
        <li><b>Erweiterter Schatten-Editor:</b> Korrigiertes Dialog-Layout mit Mehrsprachenunterstützung, Subtraktionsoperationen und verbesserter Verlaufstabelle für besseres Schatten-Management.</li>
        <li><b>Benutzereinstellungen-Persistenz:</b> Speicher- und Ladefunktion für Benutzereinstellungen, damit Ihre Präferenzen sitzungsübergreifend erhalten bleiben.</li>
        <li><b>Rendering-Verbesserungen:</b> Behobene Seitenlinien-Rendering-Probleme und verbesserte Rückgängig/Wiederherstellen-Funktionalität für zuverlässigere visuelle Ausgabe.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.104</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Sistema di punti di controllo migliorato:</b> Migliorata l'esperienza utente per il movimento dei punti di controllo e il comportamento di attivazione. Miglior feedback visivo e interazione più fluida quando si lavora con i punti di controllo.</li>
        <li><b>Gestione delle proprietà degli endpoint:</b> Funzionalità di salvataggio campioni e duplicazione delle proprietà degli endpoint. Flusso di lavoro ottimizzato per la gestione delle configurazioni degli endpoint.</li>
        <li><b>Editor di ombre avanzato:</b> Layout della finestra di dialogo corretto con supporto multilingue, operazioni di sottrazione e tabella cronologia migliorata per una migliore gestione delle ombre.</li>
        <li><b>Persistenza delle impostazioni utente:</b> Funzionalità di salvataggio e caricamento delle impostazioni utente, garantendo che le preferenze vengano mantenute tra le sessioni.</li>
        <li><b>Miglioramenti del rendering:</b> Risolti i problemi di rendering delle linee laterali e migliorata la funzionalità annulla/ripristina per un output visivo più affidabile.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.104</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Sistema de puntos de control mejorado:</b> Mejor experiencia de usuario para el movimiento de puntos de control y comportamiento de activación. Mejor retroalimentación visual e interacción más fluida al trabajar con puntos de control.</li>
        <li><b>Gestión de propiedades de puntos finales:</b> Funcionalidad de guardar muestras y duplicar propiedades de puntos finales. Flujo de trabajo optimizado para gestionar configuraciones de puntos finales.</li>
        <li><b>Editor de sombras avanzado:</b> Diseño de diálogo corregido con soporte multiidioma, operaciones de sustracción y tabla de historial mejorada para una mejor gestión de sombras.</li>
        <li><b>Persistencia de configuración de usuario:</b> Funcionalidad de guardar y cargar configuración de usuario, asegurando que sus preferencias se mantengan entre sesiones.</li>
        <li><b>Mejoras de renderizado:</b> Solucionados problemas de renderizado de líneas laterales y mejorada la funcionalidad deshacer/rehacer para una salida visual más confiable.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.104</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Sistema de pontos de controle aprimorado:</b> Melhor experiência do usuário para movimento de pontos de controle e comportamento de ativação. Melhor feedback visual e interação mais suave ao trabalhar com pontos de controle.</li>
        <li><b>Gerenciamento de propriedades de pontos finais:</b> Funcionalidade de salvar amostras e duplicar propriedades de pontos finais. Fluxo de trabalho otimizado para gerenciar configurações de pontos finais.</li>
        <li><b>Editor de sombras avançado:</b> Layout de diálogo corrigido com suporte multilíngue, operações de subtração e tabela de histórico aprimorada para melhor gerenciamento de sombras.</li>
        <li><b>Persistência de configurações do usuário:</b> Funcionalidade de salvar e carregar configurações do usuário, garantindo que suas preferências sejam mantidas entre as sessões.</li>
        <li><b>Melhorias de renderização:</b> Corrigidos problemas de renderização de linhas laterais e melhorada a funcionalidade desfazer/refazer para saída visual mais confiável.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.104</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05D7;&#x05D9;&#x05E6;&#x05D9;&#x05DD; &#x05DE;&#x05DC;&#x05D0;&#x05D4;:</b> &#x05EA;&#x05DB;&#x05D5;&#x05E0;&#x05EA; &#x05D7;&#x05D9;&#x05E6;&#x05D9;&#x05DD; &#x05DE;&#x05E7;&#x05D9;&#x05E4;&#x05D4; &#x05E2;&#x05DD; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9;&#x05DD; &#x05D4;&#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D4;&#x05EA;&#x05D0;&#x05DE;&#x05D4; &#x05D0;&#x05D9;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05DB;&#x05DE;&#x05D4;:</b> &#x05D1;&#x05E2;&#x05EA; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA; &#x05E2;&#x05DD; &#x05D2;&#x05D3;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05DE;&#x05D5;&#x05E1;&#x05DB;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05E6;&#x05D1;&#x05D9;&#x05E2;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome German + localized sections). Updated to 1.104 what's-new.
cat > "$RESOURCES_DIR/de.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.104</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbessertes Kontrollpunktsystem:</b> Verbesserte Benutzerführung für Kontrollpunktbewegung und Aktivierungsverhalten. Besseres visuelles Feedback und flüssigere Interaktion bei der Arbeit mit Kontrollpunkten.</li>
        <li><b>Endpunkt-Eigenschaften-Verwaltung:</b> Speichern von Mustern und Duplizieren von Endpunkt-Eigenschaften. Optimierter Arbeitsablauf für die Verwaltung von Endpunkt-Konfigurationen.</li>
        <li><b>Erweiterter Schatten-Editor:</b> Korrigiertes Dialog-Layout mit Mehrsprachenunterstützung, Subtraktionsoperationen und verbesserter Verlaufstabelle für besseres Schatten-Management.</li>
        <li><b>Benutzereinstellungen-Persistenz:</b> Speicher- und Ladefunktion für Benutzereinstellungen, damit Ihre Präferenzen sitzungsübergreifend erhalten bleiben.</li>
        <li><b>Rendering-Verbesserungen:</b> Behobene Seitenlinien-Rendering-Probleme und verbesserte Rückgängig/Wiederherstellen-Funktionalität für zuverlässigere visuelle Ausgabe.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.104</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.104:</p>
    <ul>
        <li><b>Enhanced Control Point System:</b> Improved UX for control point movement and activation behavior. Better visual feedback and smoother interaction when working with control points.</li>
        <li><b>Endpoint Properties Management:</b> Save samples and duplicate endpoint properties functionality. Streamlined workflow for managing endpoint configurations.</li>
        <li><b>Advanced Shadow Editor:</b> Fixed dialog layout with multi-language support, subtraction operations, and improved history table for better shadow management.</li>
        <li><b>User Settings Persistence:</b> Save and load functionality for user settings, ensuring your preferences are maintained across sessions.</li>
        <li><b>Rendering Improvements:</b> Fixed side line rendering issues and enhanced undo/redo functionality for more reliable visual output.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.104</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Système de points de contrôle amélioré :</b> Interface utilisateur améliorée pour le mouvement des points de contrôle et le comportement d'activation. Meilleur retour visuel et interaction plus fluide lors du travail avec les points de contrôle.</li>
        <li><b>Gestion des propriétés des extrémités :</b> Fonctionnalité de sauvegarde d'échantillons et de duplication des propriétés des extrémités. Flux de travail optimisé pour la gestion des configurations d'extrémités.</li>
        <li><b>Éditeur d'ombres avancé :</b> Disposition de dialogue corrigée avec prise en charge multilingue, opérations de soustraction et table d'historique améliorée pour une meilleure gestion des ombres.</li>
        <li><b>Persistance des paramètres utilisateur :</b> Fonctionnalité de sauvegarde et de chargement des paramètres utilisateur, garantissant que vos préférences sont maintenues d'une session à l'autre.</li>
        <li><b>Améliorations du rendu :</b> Correction des problèmes de rendu des lignes latérales et amélioration de la fonctionnalité annuler/rétablir pour une sortie visuelle plus fiable.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.104</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Sistema di punti di controllo migliorato:</b> Migliorata l'esperienza utente per il movimento dei punti di controllo e il comportamento di attivazione. Miglior feedback visivo e interazione più fluida quando si lavora con i punti di controllo.</li>
        <li><b>Gestione delle proprietà degli endpoint:</b> Funzionalità di salvataggio campioni e duplicazione delle proprietà degli endpoint. Flusso di lavoro ottimizzato per la gestione delle configurazioni degli endpoint.</li>
        <li><b>Editor di ombre avanzato:</b> Layout della finestra di dialogo corretto con supporto multilingue, operazioni di sottrazione e tabella cronologia migliorata per una migliore gestione delle ombre.</li>
        <li><b>Persistenza delle impostazioni utente:</b> Funzionalità di salvataggio e caricamento delle impostazioni utente, garantendo che le preferenze vengano mantenute tra le sessioni.</li>
        <li><b>Miglioramenti del rendering:</b> Risolti i problemi di rendering delle linee laterali e migliorata la funzionalità annulla/ripristina per un output visivo più affidabile.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.104</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Sistema de puntos de control mejorado:</b> Mejor experiencia de usuario para el movimiento de puntos de control y comportamiento de activación. Mejor retroalimentación visual e interacción más fluida al trabajar con puntos de control.</li>
        <li><b>Gestión de propiedades de puntos finales:</b> Funcionalidad de guardar muestras y duplicar propiedades de puntos finales. Flujo de trabajo optimizado para gestionar configuraciones de puntos finales.</li>
        <li><b>Editor de sombras avanzado:</b> Diseño de diálogo corregido con soporte multiidioma, operaciones de sustracción y tabla de historial mejorada para una mejor gestión de sombras.</li>
        <li><b>Persistencia de configuración de usuario:</b> Funcionalidad de guardar y cargar configuración de usuario, asegurando que sus preferencias se mantengan entre sesiones.</li>
        <li><b>Mejoras de renderizado:</b> Solucionados problemas de renderizado de líneas laterales y mejorada la funcionalidad deshacer/rehacer para una salida visual más confiable.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.104</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Sistema de pontos de controle aprimorado:</b> Melhor experiência do usuário para movimento de pontos de controle e comportamento de ativação. Melhor feedback visual e interação mais suave ao trabalhar com pontos de controle.</li>
        <li><b>Gerenciamento de propriedades de pontos finais:</b> Funcionalidade de salvar amostras e duplicar propriedades de pontos finais. Fluxo de trabalho otimizado para gerenciar configurações de pontos finais.</li>
        <li><b>Editor de sombras avançado:</b> Layout de diálogo corrigido com suporte multilíngue, operações de subtração e tabela de histórico aprimorada para melhor gerenciamento de sombras.</li>
        <li><b>Persistência de configurações do usuário:</b> Funcionalidade de salvar e carregar configurações do usuário, garantindo que suas preferências sejam mantidas entre as sessões.</li>
        <li><b>Melhorias de renderização:</b> Corrigidos problemas de renderização de linhas laterais e melhorada a funcionalidade desfazer/refazer para saída visual mais confiável.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.104</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05EA;&#x05E0;&#x05D5;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D5;&#x05D4;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D5;&#x05EA; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D4;. &#x05DE;&#x05E9;&#x05D5;&#x05D1; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D5;&#x05D0;&#x05D9;&#x05E0;&#x05D8;&#x05E8;&#x05D0;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DD; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05D5;&#x05EA; &#x05D5;&#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;. &#x05EA;&#x05D4;&#x05DC;&#x05D9;&#x05DA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05E2;&#x05DC; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05EA;&#x05E6;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DD;:</b> &#x05E4;&#x05E8;&#x05D9;&#x05E1;&#x05EA; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05EA; &#x05E2;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05DB;&#x05D4; &#x05E8;&#x05D1;-&#x05E9;&#x05E4;&#x05EA;&#x05D9;&#x05EA;, &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D7;&#x05D9;&#x05E1;&#x05D5;&#x05E8; &#x05D5;&#x05D8;&#x05D1;&#x05DC;&#x05EA; &#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;, &#x05D4;&#x05DE;&#x05D1;&#x05D8;&#x05D9;&#x05D7;&#x05D4; &#x05E9;&#x05D4;&#x05D4;&#x05E2;&#x05D3;&#x05E4;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DA; &#x05E9;&#x05DE;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05DF; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05D9;&#x05E4;&#x05D5;&#x05E8;&#x05D9; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05E9;&#x05DC; &#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05E6;&#x05D3; &#x05D5;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D4; &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8; &#x05DC;&#x05E4;&#x05DC;&#x05D8; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D0;&#x05DE;&#x05D9;&#x05DF; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome Italian + localized sections). Updated to 1.104 what's-new.
cat > "$RESOURCES_DIR/it.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.104</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Sistema di punti di controllo migliorato:</b> Migliorata l'esperienza utente per il movimento dei punti di controllo e il comportamento di attivazione. Miglior feedback visivo e interazione più fluida quando si lavora con i punti di controllo.</li>
        <li><b>Gestione delle proprietà degli endpoint:</b> Funzionalità di salvataggio campioni e duplicazione delle proprietà degli endpoint. Flusso di lavoro ottimizzato per la gestione delle configurazioni degli endpoint.</li>
        <li><b>Editor di ombre avanzato:</b> Layout della finestra di dialogo corretto con supporto multilingue, operazioni di sottrazione e tabella cronologia migliorata per una migliore gestione delle ombre.</li>
        <li><b>Persistenza delle impostazioni utente:</b> Funzionalità di salvataggio e caricamento delle impostazioni utente, garantendo che le preferenze vengano mantenute tra le sessioni.</li>
        <li><b>Miglioramenti del rendering:</b> Risolti i problemi di rendering delle linee laterali e migliorata la funzionalità annulla/ripristina per un output visivo più affidabile.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.104</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.104:</p>
    <ul>
        <li><b>Enhanced Control Point System:</b> Improved UX for control point movement and activation behavior. Better visual feedback and smoother interaction when working with control points.</li>
        <li><b>Endpoint Properties Management:</b> Save samples and duplicate endpoint properties functionality. Streamlined workflow for managing endpoint configurations.</li>
        <li><b>Advanced Shadow Editor:</b> Fixed dialog layout with multi-language support, subtraction operations, and improved history table for better shadow management.</li>
        <li><b>User Settings Persistence:</b> Save and load functionality for user settings, ensuring your preferences are maintained across sessions.</li>
        <li><b>Rendering Improvements:</b> Fixed side line rendering issues and enhanced undo/redo functionality for more reliable visual output.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.104</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbessertes Kontrollpunktsystem:</b> Verbesserte Benutzerführung für Kontrollpunktbewegung und Aktivierungsverhalten. Besseres visuelles Feedback und flüssigere Interaktion bei der Arbeit mit Kontrollpunkten.</li>
        <li><b>Endpunkt-Eigenschaften-Verwaltung:</b> Speichern von Mustern und Duplizieren von Endpunkt-Eigenschaften. Optimierter Arbeitsablauf für die Verwaltung von Endpunkt-Konfigurationen.</li>
        <li><b>Erweiterter Schatten-Editor:</b> Korrigiertes Dialog-Layout mit Mehrsprachenunterstützung, Subtraktionsoperationen und verbesserter Verlaufstabelle für besseres Schatten-Management.</li>
        <li><b>Benutzereinstellungen-Persistenz:</b> Speicher- und Ladefunktion für Benutzereinstellungen, damit Ihre Präferenzen sitzungsübergreifend erhalten bleiben.</li>
        <li><b>Rendering-Verbesserungen:</b> Behobene Seitenlinien-Rendering-Probleme und verbesserte Rückgängig/Wiederherstellen-Funktionalität für zuverlässigere visuelle Ausgabe.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.104</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Système de points de contrôle amélioré :</b> Interface utilisateur améliorée pour le mouvement des points de contrôle et le comportement d'activation. Meilleur retour visuel et interaction plus fluide lors du travail avec les points de contrôle.</li>
        <li><b>Gestion des propriétés des extrémités :</b> Fonctionnalité de sauvegarde d'échantillons et de duplication des propriétés des extrémités. Flux de travail optimisé pour la gestion des configurations d'extrémités.</li>
        <li><b>Éditeur d'ombres avancé :</b> Disposition de dialogue corrigée avec prise en charge multilingue, opérations de soustraction et table d'historique améliorée pour une meilleure gestion des ombres.</li>
        <li><b>Persistance des paramètres utilisateur :</b> Fonctionnalité de sauvegarde et de chargement des paramètres utilisateur, garantissant que vos préférences sont maintenues d'une session à l'autre.</li>
        <li><b>Améliorations du rendu :</b> Correction des problèmes de rendu des lignes latérales et amélioration de la fonctionnalité annuler/rétablir pour une sortie visuelle plus fiable.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.104</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Sistema de puntos de control mejorado:</b> Mejor experiencia de usuario para el movimiento de puntos de control y comportamiento de activación. Mejor retroalimentación visual e interacción más fluida al trabajar con puntos de control.</li>
        <li><b>Gestión de propiedades de puntos finales:</b> Funcionalidad de guardar muestras y duplicar propiedades de puntos finales. Flujo de trabajo optimizado para gestionar configuraciones de puntos finales.</li>
        <li><b>Editor de sombras avanzado:</b> Diseño de diálogo corregido con soporte multiidioma, operaciones de sustracción y tabla de historial mejorada para una mejor gestión de sombras.</li>
        <li><b>Persistencia de configuración de usuario:</b> Funcionalidad de guardar y cargar configuración de usuario, asegurando que sus preferencias se mantengan entre sesiones.</li>
        <li><b>Mejoras de renderizado:</b> Solucionados problemas de renderizado de líneas laterales y mejorada la funcionalidad deshacer/rehacer para una salida visual más confiable.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.104</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Sistema de pontos de controle aprimorado:</b> Melhor experiência do usuário para movimento de pontos de controle e comportamento de ativação. Melhor feedback visual e interação mais suave ao trabalhar com pontos de controle.</li>
        <li><b>Gerenciamento de propriedades de pontos finais:</b> Funcionalidade de salvar amostras e duplicar propriedades de pontos finais. Fluxo de trabalho otimizado para gerenciar configurações de pontos finais.</li>
        <li><b>Editor de sombras avançado:</b> Layout de diálogo corrigido com suporte multilíngue, operações de subtração e tabela de histórico aprimorada para melhor gerenciamento de sombras.</li>
        <li><b>Persistência de configurações do usuário:</b> Funcionalidade de salvar e carregar configurações do usuário, garantindo que suas preferências sejam mantidas entre as sessões.</li>
        <li><b>Melhorias de renderização:</b> Corrigidos problemas de renderização de linhas laterais e melhorada a funcionalidade desfazer/refazer para saída visual mais confiável.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.104</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05EA;&#x05E0;&#x05D5;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D5;&#x05D4;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D5;&#x05EA; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D4;. &#x05DE;&#x05E9;&#x05D5;&#x05D1; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D5;&#x05D0;&#x05D9;&#x05E0;&#x05D8;&#x05E8;&#x05D0;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DD; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05D5;&#x05EA; &#x05D5;&#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;. &#x05EA;&#x05D4;&#x05DC;&#x05D9;&#x05DA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05E2;&#x05DC; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05EA;&#x05E6;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DD;:</b> &#x05E4;&#x05E8;&#x05D9;&#x05E1;&#x05EA; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05EA; &#x05E2;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05DB;&#x05D4; &#x05E8;&#x05D1;-&#x05E9;&#x05E4;&#x05EA;&#x05D9;&#x05EA;, &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D7;&#x05D9;&#x05E1;&#x05D5;&#x05E8; &#x05D5;&#x05D8;&#x05D1;&#x05DC;&#x05EA; &#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;, &#x05D4;&#x05DE;&#x05D1;&#x05D8;&#x05D9;&#x05D7;&#x05D4; &#x05E9;&#x05D4;&#x05D4;&#x05E2;&#x05D3;&#x05E4;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DA; &#x05E9;&#x05DE;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05DF; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05D9;&#x05E4;&#x05D5;&#x05E8;&#x05D9; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05E9;&#x05DC; &#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05E6;&#x05D3; &#x05D5;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D4; &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8; &#x05DC;&#x05E4;&#x05DC;&#x05D8; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D0;&#x05DE;&#x05D9;&#x05DF; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome Spanish + localized sections). Updated to 1.104 what's-new.
cat > "$RESOURCES_DIR/es.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.104</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Sistema de puntos de control mejorado:</b> Mejor experiencia de usuario para el movimiento de puntos de control y comportamiento de activación. Mejor retroalimentación visual e interacción más fluida al trabajar con puntos de control.</li>
        <li><b>Gestión de propiedades de puntos finales:</b> Funcionalidad de guardar muestras y duplicar propiedades de puntos finales. Flujo de trabajo optimizado para gestionar configuraciones de puntos finales.</li>
        <li><b>Editor de sombras avanzado:</b> Diseño de diálogo corregido con soporte multiidioma, operaciones de sustracción y tabla de historial mejorada para una mejor gestión de sombras.</li>
        <li><b>Persistencia de configuración de usuario:</b> Funcionalidad de guardar y cargar configuración de usuario, asegurando que sus preferencias se mantengan entre sesiones.</li>
        <li><b>Mejoras de renderizado:</b> Solucionados problemas de renderizado de líneas laterales y mejorada la funcionalidad deshacer/rehacer para una salida visual más confiable.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.104</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.104:</p>
    <ul>
        <li><b>Enhanced Control Point System:</b> Improved UX for control point movement and activation behavior. Better visual feedback and smoother interaction when working with control points.</li>
        <li><b>Endpoint Properties Management:</b> Save samples and duplicate endpoint properties functionality. Streamlined workflow for managing endpoint configurations.</li>
        <li><b>Advanced Shadow Editor:</b> Fixed dialog layout with multi-language support, subtraction operations, and improved history table for better shadow management.</li>
        <li><b>User Settings Persistence:</b> Save and load functionality for user settings, ensuring your preferences are maintained across sessions.</li>
        <li><b>Rendering Improvements:</b> Fixed side line rendering issues and enhanced undo/redo functionality for more reliable visual output.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.104</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Système de points de contrôle amélioré :</b> Interface utilisateur améliorée pour le mouvement des points de contrôle et le comportement d'activation. Meilleur retour visuel et interaction plus fluide lors du travail avec les points de contrôle.</li>
        <li><b>Gestion des propriétés des extrémités :</b> Fonctionnalité de sauvegarde d'échantillons et de duplication des propriétés des extrémités. Flux de travail optimisé pour la gestion des configurations d'extrémités.</li>
        <li><b>Éditeur d'ombres avancé :</b> Disposition de dialogue corrigée avec prise en charge multilingue, opérations de soustraction et table d'historique améliorée pour une meilleure gestion des ombres.</li>
        <li><b>Persistance des paramètres utilisateur :</b> Fonctionnalité de sauvegarde et de chargement des paramètres utilisateur, garantissant que vos préférences sont maintenues d'une session à l'autre.</li>
        <li><b>Améliorations du rendu :</b> Correction des problèmes de rendu des lignes latérales et amélioration de la fonctionnalité annuler/rétablir pour une sortie visuelle plus fiable.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.104</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbessertes Kontrollpunktsystem:</b> Verbesserte Benutzerführung für Kontrollpunktbewegung und Aktivierungsverhalten. Besseres visuelles Feedback und flüssigere Interaktion bei der Arbeit mit Kontrollpunkten.</li>
        <li><b>Endpunkt-Eigenschaften-Verwaltung:</b> Speichern von Mustern und Duplizieren von Endpunkt-Eigenschaften. Optimierter Arbeitsablauf für die Verwaltung von Endpunkt-Konfigurationen.</li>
        <li><b>Erweiterter Schatten-Editor:</b> Korrigiertes Dialog-Layout mit Mehrsprachenunterstützung, Subtraktionsoperationen und verbesserter Verlaufstabelle für besseres Schatten-Management.</li>
        <li><b>Benutzereinstellungen-Persistenz:</b> Speicher- und Ladefunktion für Benutzereinstellungen, damit Ihre Präferenzen sitzungsübergreifend erhalten bleiben.</li>
        <li><b>Rendering-Verbesserungen:</b> Behobene Seitenlinien-Rendering-Probleme und verbesserte Rückgängig/Wiederherstellen-Funktionalität für zuverlässigere visuelle Ausgabe.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.104</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Sistema di punti di controllo migliorato:</b> Migliorata l'esperienza utente per il movimento dei punti di controllo e il comportamento di attivazione. Miglior feedback visivo e interazione più fluida quando si lavora con i punti di controllo.</li>
        <li><b>Gestione delle proprietà degli endpoint:</b> Funzionalità di salvataggio campioni e duplicazione delle proprietà degli endpoint. Flusso di lavoro ottimizzato per la gestione delle configurazioni degli endpoint.</li>
        <li><b>Editor di ombre avanzato:</b> Layout della finestra di dialogo corretto con supporto multilingue, operazioni di sottrazione e tabella cronologia migliorata per una migliore gestione delle ombre.</li>
        <li><b>Persistenza delle impostazioni utente:</b> Funzionalità di salvataggio e caricamento delle impostazioni utente, garantendo che le preferenze vengano mantenute tra le sessioni.</li>
        <li><b>Miglioramenti del rendering:</b> Risolti i problemi di rendering delle linee laterali e migliorata la funzionalità annulla/ripristina per un output visivo più affidabile.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.104</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Sistema de pontos de controle aprimorado:</b> Melhor experiência do usuário para movimento de pontos de controle e comportamento de ativação. Melhor feedback visual e interação mais suave ao trabalhar com pontos de controle.</li>
        <li><b>Gerenciamento de propriedades de pontos finais:</b> Funcionalidade de salvar amostras e duplicar propriedades de pontos finais. Fluxo de trabalho otimizado para gerenciar configurações de pontos finais.</li>
        <li><b>Editor de sombras avançado:</b> Layout de diálogo corrigido com suporte multilíngue, operações de subtração e tabela de histórico aprimorada para melhor gerenciamento de sombras.</li>
        <li><b>Persistência de configurações do usuário:</b> Funcionalidade de salvar e carregar configurações do usuário, garantindo que suas preferências sejam mantidas entre as sessões.</li>
        <li><b>Melhorias de renderização:</b> Corrigidos problemas de renderização de linhas laterais e melhorada a funcionalidade desfazer/refazer para saída visual mais confiável.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.104</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05EA;&#x05E0;&#x05D5;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D5;&#x05D4;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D5;&#x05EA; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D4;. &#x05DE;&#x05E9;&#x05D5;&#x05D1; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D5;&#x05D0;&#x05D9;&#x05E0;&#x05D8;&#x05E8;&#x05D0;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DD; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05D5;&#x05EA; &#x05D5;&#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;. &#x05EA;&#x05D4;&#x05DC;&#x05D9;&#x05DA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05E2;&#x05DC; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05EA;&#x05E6;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DD;:</b> &#x05E4;&#x05E8;&#x05D9;&#x05E1;&#x05EA; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05EA; &#x05E2;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05DB;&#x05D4; &#x05E8;&#x05D1;-&#x05E9;&#x05E4;&#x05EA;&#x05D9;&#x05EA;, &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D7;&#x05D9;&#x05E1;&#x05D5;&#x05E8; &#x05D5;&#x05D8;&#x05D1;&#x05DC;&#x05EA; &#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;, &#x05D4;&#x05DE;&#x05D1;&#x05D8;&#x05D9;&#x05D7;&#x05D4; &#x05E9;&#x05D4;&#x05D4;&#x05E2;&#x05D3;&#x05E4;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DA; &#x05E9;&#x05DE;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05DF; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05D9;&#x05E4;&#x05D5;&#x05E8;&#x05D9; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05E9;&#x05DC; &#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05E6;&#x05D3; &#x05D5;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D4; &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8; &#x05DC;&#x05E4;&#x05DC;&#x05D8; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D0;&#x05DE;&#x05D9;&#x05DF; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome Portuguese + localized sections). Updated to 1.104 what's-new.
cat > "$RESOURCES_DIR/pt.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.104</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Sistema de pontos de controle aprimorado:</b> Melhor experiência do usuário para movimento de pontos de controle e comportamento de ativação. Melhor feedback visual e interação mais suave ao trabalhar com pontos de controle.</li>
        <li><b>Gerenciamento de propriedades de pontos finais:</b> Funcionalidade de salvar amostras e duplicar propriedades de pontos finais. Fluxo de trabalho otimizado para gerenciar configurações de pontos finais.</li>
        <li><b>Editor de sombras avançado:</b> Layout de diálogo corrigido com suporte multilíngue, operações de subtração e tabela de histórico aprimorada para melhor gerenciamento de sombras.</li>
        <li><b>Persistência de configurações do usuário:</b> Funcionalidade de salvar e carregar configurações do usuário, garantindo que suas preferências sejam mantidas entre as sessões.</li>
        <li><b>Melhorias de renderização:</b> Corrigidos problemas de renderização de linhas laterais e melhorada a funcionalidade desfazer/refazer para saída visual mais confiável.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.104</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.104:</p>
    <ul>
        <li><b>Enhanced Control Point System:</b> Improved UX for control point movement and activation behavior. Better visual feedback and smoother interaction when working with control points.</li>
        <li><b>Endpoint Properties Management:</b> Save samples and duplicate endpoint properties functionality. Streamlined workflow for managing endpoint configurations.</li>
        <li><b>Advanced Shadow Editor:</b> Fixed dialog layout with multi-language support, subtraction operations, and improved history table for better shadow management.</li>
        <li><b>User Settings Persistence:</b> Save and load functionality for user settings, ensuring your preferences are maintained across sessions.</li>
        <li><b>Rendering Improvements:</b> Fixed side line rendering issues and enhanced undo/redo functionality for more reliable visual output.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.104</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Système de points de contrôle amélioré :</b> Interface utilisateur améliorée pour le mouvement des points de contrôle et le comportement d'activation. Meilleur retour visuel et interaction plus fluide lors du travail avec les points de contrôle.</li>
        <li><b>Gestion des propriétés des extrémités :</b> Fonctionnalité de sauvegarde d'échantillons et de duplication des propriétés des extrémités. Flux de travail optimisé pour la gestion des configurations d'extrémités.</li>
        <li><b>Éditeur d'ombres avancé :</b> Disposition de dialogue corrigée avec prise en charge multilingue, opérations de soustraction et table d'historique améliorée pour une meilleure gestion des ombres.</li>
        <li><b>Persistance des paramètres utilisateur :</b> Fonctionnalité de sauvegarde et de chargement des paramètres utilisateur, garantissant que vos préférences sont maintenues d'une session à l'autre.</li>
        <li><b>Améliorations du rendu :</b> Correction des problèmes de rendu des lignes latérales et amélioration de la fonctionnalité annuler/rétablir pour une sortie visuelle plus fiable.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.104</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbessertes Kontrollpunktsystem:</b> Verbesserte Benutzerführung für Kontrollpunktbewegung und Aktivierungsverhalten. Besseres visuelles Feedback und flüssigere Interaktion bei der Arbeit mit Kontrollpunkten.</li>
        <li><b>Endpunkt-Eigenschaften-Verwaltung:</b> Speichern von Mustern und Duplizieren von Endpunkt-Eigenschaften. Optimierter Arbeitsablauf für die Verwaltung von Endpunkt-Konfigurationen.</li>
        <li><b>Erweiterter Schatten-Editor:</b> Korrigiertes Dialog-Layout mit Mehrsprachenunterstützung, Subtraktionsoperationen und verbesserter Verlaufstabelle für besseres Schatten-Management.</li>
        <li><b>Benutzereinstellungen-Persistenz:</b> Speicher- und Ladefunktion für Benutzereinstellungen, damit Ihre Präferenzen sitzungsübergreifend erhalten bleiben.</li>
        <li><b>Rendering-Verbesserungen:</b> Behobene Seitenlinien-Rendering-Probleme und verbesserte Rückgängig/Wiederherstellen-Funktionalität für zuverlässigere visuelle Ausgabe.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.104</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Sistema di punti di controllo migliorato:</b> Migliorata l'esperienza utente per il movimento dei punti di controllo e il comportamento di attivazione. Miglior feedback visivo e interazione più fluida quando si lavora con i punti di controllo.</li>
        <li><b>Gestione delle proprietà degli endpoint:</b> Funzionalità di salvataggio campioni e duplicazione delle proprietà degli endpoint. Flusso di lavoro ottimizzato per la gestione delle configurazioni degli endpoint.</li>
        <li><b>Editor di ombre avanzato:</b> Layout della finestra di dialogo corretto con supporto multilingue, operazioni di sottrazione e tabella cronologia migliorata per una migliore gestione delle ombre.</li>
        <li><b>Persistenza delle impostazioni utente:</b> Funzionalità di salvataggio e caricamento delle impostazioni utente, garantendo che le preferenze vengano mantenute tra le sessioni.</li>
        <li><b>Miglioramenti del rendering:</b> Risolti i problemi di rendering delle linee laterali e migliorata la funzionalità annulla/ripristina per un output visivo più affidabile.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.104</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Sistema de puntos de control mejorado:</b> Mejor experiencia de usuario para el movimiento de puntos de control y comportamiento de activación. Mejor retroalimentación visual e interacción más fluida al trabajar con puntos de control.</li>
        <li><b>Gestión de propiedades de puntos finales:</b> Funcionalidad de guardar muestras y duplicar propiedades de puntos finales. Flujo de trabajo optimizado para gestionar configuraciones de puntos finales.</li>
        <li><b>Editor de sombras avanzado:</b> Diseño de diálogo corregido con soporte multiidioma, operaciones de sustracción y tabla de historial mejorada para una mejor gestión de sombras.</li>
        <li><b>Persistencia de configuración de usuario:</b> Funcionalidad de guardar y cargar configuración de usuario, asegurando que sus preferencias se mantengan entre sesiones.</li>
        <li><b>Mejoras de renderizado:</b> Solucionados problemas de renderizado de líneas laterales y mejorada la funcionalidad deshacer/rehacer para una salida visual más confiable.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.104</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05EA;&#x05E0;&#x05D5;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D5;&#x05D4;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D5;&#x05EA; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D4;. &#x05DE;&#x05E9;&#x05D5;&#x05D1; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D5;&#x05D0;&#x05D9;&#x05E0;&#x05D8;&#x05E8;&#x05D0;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DD; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05D5;&#x05EA; &#x05D5;&#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;. &#x05EA;&#x05D4;&#x05DC;&#x05D9;&#x05DA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05E2;&#x05DC; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05EA;&#x05E6;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DD;:</b> &#x05E4;&#x05E8;&#x05D9;&#x05E1;&#x05EA; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05EA; &#x05E2;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05DB;&#x05D4; &#x05E8;&#x05D1;-&#x05E9;&#x05E4;&#x05EA;&#x05D9;&#x05EA;, &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D7;&#x05D9;&#x05E1;&#x05D5;&#x05E8; &#x05D5;&#x05D8;&#x05D1;&#x05DC;&#x05EA; &#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;, &#x05D4;&#x05DE;&#x05D1;&#x05D8;&#x05D9;&#x05D7;&#x05D4; &#x05E9;&#x05D4;&#x05D4;&#x05E2;&#x05D3;&#x05E4;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DA; &#x05E9;&#x05DE;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05DF; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05D9;&#x05E4;&#x05D5;&#x05E8;&#x05D9; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05E9;&#x05DC; &#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05E6;&#x05D3; &#x05D5;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D4; &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8; &#x05DC;&#x05E4;&#x05DC;&#x05D8; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D0;&#x05DE;&#x05D9;&#x05DF; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome Hebrew + localized sections). Updated to 1.104 what's-new.
cat > "$RESOURCES_DIR/he.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.104</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05EA;&#x05E0;&#x05D5;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D5;&#x05D4;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D5;&#x05EA; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D4;. &#x05DE;&#x05E9;&#x05D5;&#x05D1; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D5;&#x05D0;&#x05D9;&#x05E0;&#x05D8;&#x05E8;&#x05D0;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DD; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;.</li>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05D5;&#x05EA; &#x05D5;&#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;. &#x05EA;&#x05D4;&#x05DC;&#x05D9;&#x05DA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05E2;&#x05DC; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05EA;&#x05E6;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05E7;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DD;:</b> &#x05E4;&#x05E8;&#x05D9;&#x05E1;&#x05EA; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05EA; &#x05E2;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05DB;&#x05D4; &#x05E8;&#x05D1;-&#x05E9;&#x05E4;&#x05EA;&#x05D9;&#x05EA;, &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D7;&#x05D9;&#x05E1;&#x05D5;&#x05E8; &#x05D5;&#x05D8;&#x05D1;&#x05DC;&#x05EA; &#x05D4;&#x05D9;&#x05E1;&#x05D8;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E6;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05EA; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;:</b> &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9;, &#x05D4;&#x05DE;&#x05D1;&#x05D8;&#x05D9;&#x05D7;&#x05D4; &#x05E9;&#x05D4;&#x05D4;&#x05E2;&#x05D3;&#x05E4;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DA; &#x05E9;&#x05DE;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05DF; &#x05D4;&#x05E4;&#x05E2;&#x05DC;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05D9;&#x05E4;&#x05D5;&#x05E8;&#x05D9; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05E9;&#x05DC; &#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05E6;&#x05D3; &#x05D5;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D4; &#x05E4;&#x05D5;&#x05E0;&#x05E7;&#x05E6;&#x05D9;&#x05D5;&#x05E0;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05E9;&#x05D7;&#x05D6;&#x05D5;&#x05E8; &#x05DC;&#x05E4;&#x05DC;&#x05D8; &#x05D7;&#x05D6;&#x05D5;&#x05EA;&#x05D9; &#x05D0;&#x05DE;&#x05D9;&#x05DF; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.104</h2>
    <p dir="ltr">This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p dir="ltr">What's New in Version 1.104:</p>
    <ul dir="ltr">
        <li><b>Enhanced Control Point System:</b> Improved UX for control point movement and activation behavior. Better visual feedback and smoother interaction when working with control points.</li>
        <li><b>Endpoint Properties Management:</b> Save samples and duplicate endpoint properties functionality. Streamlined workflow for managing endpoint configurations.</li>
        <li><b>Advanced Shadow Editor:</b> Fixed dialog layout with multi-language support, subtraction operations, and improved history table for better shadow management.</li>
        <li><b>User Settings Persistence:</b> Save and load functionality for user settings, ensuring your preferences are maintained across sessions.</li>
        <li><b>Rendering Improvements:</b> Fixed side line rendering issues and enhanced undo/redo functionality for more reliable visual output.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.104</h2>
    <p dir="ltr">Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p dir="ltr">Nouveautés dans cette version&nbsp;:</p>
    <ul dir="ltr">
        <li><b>Système de points de contrôle amélioré :</b> Interface utilisateur améliorée pour le mouvement des points de contrôle et le comportement d'activation. Meilleur retour visuel et interaction plus fluide lors du travail avec les points de contrôle.</li>
        <li><b>Gestion des propriétés des extrémités :</b> Fonctionnalité de sauvegarde d'échantillons et de duplication des propriétés des extrémités. Flux de travail optimisé pour la gestion des configurations d'extrémités.</li>
        <li><b>Éditeur d'ombres avancé :</b> Disposition de dialogue corrigée avec prise en charge multilingue, opérations de soustraction et table d'historique améliorée pour une meilleure gestion des ombres.</li>
        <li><b>Persistance des paramètres utilisateur :</b> Fonctionnalité de sauvegarde et de chargement des paramètres utilisateur, garantissant que vos préférences sont maintenues d'une session à l'autre.</li>
        <li><b>Améliorations du rendu :</b> Correction des problèmes de rendu des lignes latérales et amélioration de la fonctionnalité annuler/rétablir pour une sortie visuelle plus fiable.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.104</h2>
    <p dir="ltr">Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p dir="ltr">Was ist neu in dieser Version:</p>
    <ul dir="ltr">
        <li><b>Verbessertes Kontrollpunktsystem:</b> Verbesserte Benutzerführung für Kontrollpunktbewegung und Aktivierungsverhalten. Besseres visuelles Feedback und flüssigere Interaktion bei der Arbeit mit Kontrollpunkten.</li>
        <li><b>Endpunkt-Eigenschaften-Verwaltung:</b> Speichern von Mustern und Duplizieren von Endpunkt-Eigenschaften. Optimierter Arbeitsablauf für die Verwaltung von Endpunkt-Konfigurationen.</li>
        <li><b>Erweiterter Schatten-Editor:</b> Korrigiertes Dialog-Layout mit Mehrsprachenunterstützung, Subtraktionsoperationen und verbesserter Verlaufstabelle für besseres Schatten-Management.</li>
        <li><b>Benutzereinstellungen-Persistenz:</b> Speicher- und Ladefunktion für Benutzereinstellungen, damit Ihre Präferenzen sitzungsübergreifend erhalten bleiben.</li>
        <li><b>Rendering-Verbesserungen:</b> Behobene Seitenlinien-Rendering-Probleme und verbesserte Rückgängig/Wiederherstellen-Funktionalität für zuverlässigere visuelle Ausgabe.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.104</h2>
    <p dir="ltr">Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p dir="ltr">Novità in questa versione:</p>
    <ul dir="ltr">
        <li><b>Sistema di punti di controllo migliorato:</b> Migliorata l'esperienza utente per il movimento dei punti di controllo e il comportamento di attivazione. Miglior feedback visivo e interazione più fluida quando si lavora con i punti di controllo.</li>
        <li><b>Gestione delle proprietà degli endpoint:</b> Funzionalità di salvataggio campioni e duplicazione delle proprietà degli endpoint. Flusso di lavoro ottimizzato per la gestione delle configurazioni degli endpoint.</li>
        <li><b>Editor di ombre avanzato:</b> Layout della finestra di dialogo corretto con supporto multilingue, operazioni di sottrazione e tabella cronologia migliorata per una migliore gestione delle ombre.</li>
        <li><b>Persistenza delle impostazioni utente:</b> Funzionalità di salvataggio e caricamento delle impostazioni utente, garantendo che le preferenze vengano mantenute tra le sessioni.</li>
        <li><b>Miglioramenti del rendering:</b> Risolti i problemi di rendering delle linee laterali e migliorata la funzionalità annulla/ripristina per un output visivo più affidabile.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.104</h2>
    <p dir="ltr">Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p dir="ltr">Novedades en esta versión:</p>
    <ul dir="ltr">
        <li><b>Sistema de puntos de control mejorado:</b> Mejor experiencia de usuario para el movimiento de puntos de control y comportamiento de activación. Mejor retroalimentación visual e interacción más fluida al trabajar con puntos de control.</li>
        <li><b>Gestión de propiedades de puntos finales:</b> Funcionalidad de guardar muestras y duplicar propiedades de puntos finales. Flujo de trabajo optimizado para gestionar configuraciones de puntos finales.</li>
        <li><b>Editor de sombras avanzado:</b> Diseño de diálogo corregido con soporte multiidioma, operaciones de sustracción y tabla de historial mejorada para una mejor gestión de sombras.</li>
        <li><b>Persistencia de configuración de usuario:</b> Funcionalidad de guardar y cargar configuración de usuario, asegurando que sus preferencias se mantengan entre sesiones.</li>
        <li><b>Mejoras de renderizado:</b> Solucionados problemas de renderizado de líneas laterales y mejorada la funcionalidad deshacer/rehacer para una salida visual más confiable.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.104</h2>
    <p dir="ltr">Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p dir="ltr">Novidades nesta versão:</p>
    <ul dir="ltr">
        <li><b>Sistema de pontos de controle aprimorado:</b> Melhor experiência do usuário para movimento de pontos de controle e comportamento de ativação. Melhor feedback visual e interação mais suave ao trabalhar com pontos de controle.</li>
        <li><b>Gerenciamento de propriedades de pontos finais:</b> Funcionalidade de salvar amostras e duplicar propriedades de pontos finais. Fluxo de trabalho otimizado para gerenciar configurações de pontos finais.</li>
        <li><b>Editor de sombras avançado:</b> Layout de diálogo corrigido com suporte multilíngue, operações de subtração e tabela de histórico aprimorada para melhor gerenciamento de sombras.</li>
        <li><b>Persistência de configurações do usuário:</b> Funcionalidade de salvar e carregar configurações do usuário, garantindo que suas preferências sejam mantidas entre as sessões.</li>
        <li><b>Melhorias de renderização:</b> Corrigidos problemas de renderização de linhas laterais e melhorada a funcionalidade desfazer/refazer para saída visual mais confiável.</li>
    </ul>
</body>
</html>
EOF

# Build component package
echo "Building component package..."
pkgbuild \
    --root "/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/dist" \
    --identifier "$IDENTIFIER" \
    --version "$VERSION" \
    --scripts "$SCRIPTS_DIR" \
    --install-location "/Applications" \
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
#!/bin/bash

################################################################################
# OpenStrand Studio macOS DMG Builder TEMPLATE
# Date: Created June 11, 2026
#
# LOGIC EXPLANATION:
# ==================
# This script creates a macOS .dmg disk image with full multilingual support
# for 12 languages: English, French, German, Italian, Spanish, Portuguese, Hebrew, Russian, Finnish, Swedish, Japanese, Chinese
#
# MULTILINGUAL STRUCTURE:
# -----------------------
# macOS installer uses .lproj folders for localization. Each language needs:
# 1. A license.html file in its own *.lproj folder (e.g., fr.lproj/license.html)
# 2. A welcome.html file in its own *.lproj folder (e.g., fr.lproj/welcome.html)
#
# CRITICAL: Each language's welcome.html contains ALL 12 languages, BUT the
# order is different - the target language appears FIRST, followed by others.
# This ensures users see their preferred language at the top when they select it.
#
# LANGUAGE ORDER IN EACH FILE:
# -----------------------------
# Base (en.lproj):  English, German, French, Italian, Spanish, Portuguese, Hebrew, Russian, Finnish, Swedish, Japanese, Chinese
# fr.lproj:         French, English, German, Italian, Spanish, Portuguese, Hebrew, Russian, Finnish, Swedish, Japanese, Chinese
# de.lproj:         German, English, French, Italian, Spanish, Portuguese, Hebrew, Russian, Finnish, Swedish, Japanese, Chinese
# it.lproj:         Italian, English, German, French, Spanish, Portuguese, Hebrew, Russian, Finnish, Swedish, Japanese, Chinese
# es.lproj:         Spanish, English, French, German, Italian, Portuguese, Hebrew, Russian, Finnish, Swedish, Japanese, Chinese
# pt.lproj:         Portuguese, English, French, German, Italian, Spanish, Hebrew, Russian, Finnish, Swedish, Japanese, Chinese
# he.lproj:         Hebrew, English, French, German, Italian, Spanish, Portuguese, Russian, Finnish, Swedish, Japanese, Chinese
# ru.lproj:         Russian, English, German, French, Italian, Spanish, Portuguese, Hebrew, Finnish, Swedish, Japanese, Chinese
# fi.lproj:         Finnish, English, German, French, Italian, Spanish, Portuguese, Hebrew, Russian, Swedish, Japanese, Chinese
# sv.lproj:         Swedish, English, German, French, Italian, Spanish, Portuguese, Hebrew, Russian, Finnish, Japanese, Chinese
# ja.lproj:         Japanese, English, German, French, Italian, Spanish, Portuguese, Hebrew, Russian, Finnish, Swedish, Chinese
# zh-Hans.lproj:    Chinese, English, German, French, Italian, Spanish, Portuguese, Hebrew, Russian, Finnish, Swedish, Japanese
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
VERSION="1.112"
APP_DATE="27_September_2026"
PUBLISHER="Yonatan Setbon"
IDENTIFIER="com.yonatan.openstrandstudio"

# All paths are relative to this script's own directory (the src folder), so
# the build works from any clone location.
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create directories
WORKING_DIR="$(mktemp -d)"
SCRIPTS_DIR="$WORKING_DIR/scripts"
RESOURCES_DIR="$WORKING_DIR/resources"
# Use underscores instead of dots in the output filename (1.112 -> 1_112) so the
# version dot is never mistaken for a file extension. VERSION itself stays dotted
# for the installer title and pkg metadata.
VERSION_FILE="${VERSION//./_}"
PKG_PATH="$SRC_DIR/installer_output/${APP_NAME}_${VERSION_FILE}.pkg"
mkdir -p "$SRC_DIR/installer_output"

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
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create license.html (English default)
cat > "$RESOURCES_DIR/license.html" << EOF
<!DOCTYPE html>
<html>
<body>
    <h2>License Agreement</h2>
    <p>Copyright (c) 2026 $PUBLISHER</p>
    <p>By installing this software, you agree to the terms and conditions.</p>
</body>
</html>
EOF

# Duplicate license.html into localized resource folders
declare -a LANG_CODES=("en" "fr" "de" "it" "es" "pt" "he" "ru" "fi" "sv" "ja" "zh-Hans")

# Create translated license pages for each supported language

# French
mkdir -p "$RESOURCES_DIR/fr.lproj"
cat > "$RESOURCES_DIR/fr.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Accord de licence</h2>
    <p>Droit d'auteur (c) 2026 Yonatan Setbon</p>
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
    <p>Copyright (c) 2026 Yonatan Setbon</p>
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
    <p>Derechos de autor (c) 2026 Yonatan Setbon</p>
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
    <p>Direitos autorais (c) 2026 Yonatan Setbon</p>
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
    <p>Urheberrecht (c) 2026 Yonatan Setbon</p>
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
    <p>&#x05D6;&#x05DB;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05E6;&#x05E8;&#x05D9;&#x05DD; (c) 2026 Yonatan Setbon</p>
    <p>&#x05D1;&#x05D4;&#x05EA;&#x05E7;&#x05E0;&#x05D4; &#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D4; &#x05D6;&#x05D5;&#x05D4;, &#x05D0;&#x05EA;&#x05D4; &#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05DC;&#x05EA;&#x05E0;&#x05D0;&#x05D9;&#x05DD; &#x05D5;&#x05DC;&#x05D4;&#x05D2;&#x05D1;&#x05D5;&#x05EA;.</p>
</body>
</html>
EOF


# Russian
mkdir -p "$RESOURCES_DIR/ru.lproj"
cat > "$RESOURCES_DIR/ru.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Лицензионное соглашение</h2>
    <p>Авторские права (c) 2026 Yonatan Setbon</p>
    <p>Устанавливая это программное обеспечение, вы принимаете условия использования.</p>
</body>
</html>
EOF

# Finnish
mkdir -p "$RESOURCES_DIR/fi.lproj"
cat > "$RESOURCES_DIR/fi.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Lisenssisopimus</h2>
    <p>Tekijänoikeus (c) 2026 Yonatan Setbon</p>
    <p>Asentamalla tämän ohjelmiston hyväksyt käyttöehdot.</p>
</body>
</html>
EOF

# Swedish
mkdir -p "$RESOURCES_DIR/sv.lproj"
cat > "$RESOURCES_DIR/sv.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>Licensavtal</h2>
    <p>Upphovsrätt (c) 2026 Yonatan Setbon</p>
    <p>Genom att installera denna programvara godkänner du villkoren.</p>
</body>
</html>
EOF


# Japanese
mkdir -p "$RESOURCES_DIR/ja.lproj"
cat > "$RESOURCES_DIR/ja.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>使用許諾契約</h2>
    <p>著作権 (c) 2026 Yonatan Setbon</p>
    <p>このソフトウェアをインストールすることで、利用規約に同意したものとみなされます。</p>
</body>
</html>
EOF

# Chinese
mkdir -p "$RESOURCES_DIR/zh-Hans.lproj"
cat > "$RESOURCES_DIR/zh-Hans.lproj/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<body>
    <h2>许可协议</h2>
    <p>版权所有 (c) 2026 Yonatan Setbon</p>
    <p>安装本软件即表示您同意相关条款和条件。</p>
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

# Create welcome.html  (welcome French + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/fr.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires pour installer ce logiciel.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create welcome.html  (welcome German + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/de.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create welcome.html  (welcome Italian + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/it.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create welcome.html  (welcome Spanish + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/es.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create welcome.html  (welcome Portuguese + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/pt.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create welcome.html  (welcome Hebrew + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/he.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p dir="ltr">This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p dir="ltr">What's New in Version 1.112:</p>
    <ul dir="ltr">
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p dir="ltr">Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p dir="ltr">Nouveautés de la version 1.112 :</p>
    <ul dir="ltr">
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p dir="ltr">Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p dir="ltr">Neu in Version 1.112:</p>
    <ul dir="ltr">
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p dir="ltr">Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p dir="ltr">Novità della versione 1.112:</p>
    <ul dir="ltr">
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p dir="ltr">Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p dir="ltr">Novedades de la versión 1.112:</p>
    <ul dir="ltr">
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p dir="ltr">Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p dir="ltr">Novidades da versão 1.112:</p>
    <ul dir="ltr">
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p dir="ltr">Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p dir="ltr">Что нового в версии 1.112:</p>
    <ul dir="ltr">
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p dir="ltr">Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p dir="ltr">Mitä uutta versiossa 1.112:</p>
    <ul dir="ltr">
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p dir="ltr">Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p dir="ltr">Nyheter i version 1.112:</p>
    <ul dir="ltr">
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p dir="ltr">このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p dir="ltr">バージョン 1.112 の新機能:</p>
    <ul dir="ltr">
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p dir="ltr">本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p dir="ltr">版本 1.112 的新功能:</p>
    <ul dir="ltr">
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create welcome.html  (welcome Russian + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/ru.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create welcome.html  (welcome Finnish + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/fi.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create welcome.html  (welcome Swedish + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/sv.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create welcome.html  (welcome Japanese + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/ja.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
</body>
</html>
EOF

# Create welcome.html  (welcome Chinese + localized sections). Template with #todo placeholders.
cat > "$RESOURCES_DIR/zh-Hans.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 1.112</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 1.112 的新功能:</p>
    <ul>
        <li><b>遮罩周围的阴影更好看:</b> 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。</li>
        <li><b>隐藏的阴影保持隐藏:</b> 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.112</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.112:</p>
    <ul>
        <li><b>Better Shadows Around Masks:</b> Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.</li>
        <li><b>Hidden Shadows Stay Hidden:</b> When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.112</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.112:</p>
    <ul>
        <li><b>Bessere Schatten an Masken:</b> Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.</li>
        <li><b>Ausgeblendete Schatten bleiben ausgeblendet:</b> Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.112</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.112 :</p>
    <ul>
        <li><b>De plus belles ombres autour des masques:</b> Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.</li>
        <li><b>Les ombres masquées restent masquées:</b> Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.112</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.112:</p>
    <ul>
        <li><b>Ombre migliori intorno alle maschere:</b> Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.</li>
        <li><b>Le ombre nascoste restano nascoste:</b> Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.112</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.112:</p>
    <ul>
        <li><b>Mejores sombras alrededor de las máscaras:</b> Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.</li>
        <li><b>Las sombras ocultas siguen ocultas:</b> Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.112</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.112:</p>
    <ul>
        <li><b>Sombras melhores à volta das máscaras:</b> Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.</li>
        <li><b>Sombras ocultas continuam ocultas:</b> Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.112</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.112:</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D8;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05E2;&#x05D1;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;, &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05E8;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05DB;&#x05DE;&#x05D5; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05DE;&#x05D9;&#x05EA;&#x05D9;&#x05EA;. &#x05D4;&#x05D8;&#x05E8;&#x05D9;&#x05D6;&#x05D9;&#x05DD; &#x05D4;&#x05DB;&#x05D4;&#x05D9;&#x05DD;, &#x05D4;&#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D5;&#x05EA; &#x05D5;&#x05D4;&#x05E9;&#x05E7;&#x05E2;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D9;&#x05D5;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DC;&#x05D9;&#x05D3; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05DC;&#x05DE;&#x05D5;, &#x05D5;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05DE;&#x05D5;&#x05E8;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05E0;&#x05E7;&#x05D9;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05EA;&#x05D9;&#x05D1; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05E6;&#x05D9;&#x05D2;&#x05D4; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DE;&#x05E6;&#x05D5;&#x05D9;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;:</b> &#x05DB;&#x05E9;&#x05DE;&#x05D1;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E9;&#x05DC; &#x05E6;&#x05DC; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;, &#x05D4;&#x05D5;&#x05D0; &#x05E0;&#x05E2;&#x05DC;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05D2;&#x05DE;&#x05E8;&#x05D9;. &#x05E7;&#x05D5;&#x05D3;&#x05DD; &#x05D9;&#x05DB;&#x05DC;&#x05D4; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05D0;&#x05E4;&#x05D5;&#x05E8;&#x05D4; &#x05E7;&#x05D8;&#x05E0;&#x05D4; &#x05DC;&#x05D9;&#x05D3; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D7;&#x05E8;. &#x05D2;&#x05DD; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8;&#x05D4; &#x05E6;&#x05DC; &#x05E9;&#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05D4;&#x05D9;&#x05E9;&#x05D0;&#x05E8; &#x05D2;&#x05DC;&#x05D5;&#x05D9;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 1.112</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 1.112:</p>
    <ul>
        <li><b>Лучшие тени у масок:</b> там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.</li>
        <li><b>Скрытые тени остаются скрытыми:</b> если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 1.112 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 1.112:</p>
    <ul>
        <li><b>Paremmat varjot maskien ympärillä:</b> kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.</li>
        <li><b>Piilotetut varjot pysyvät piilossa:</b> kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 1.112</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 1.112:</p>
    <ul>
        <li><b>Bättre skuggor kring masker:</b> där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.</li>
        <li><b>Dolda skuggor förblir dolda:</b> när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 1.112 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 1.112 の新機能:</p>
    <ul>
        <li><b>マスクまわりの影がきれいに:</b> マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。</li>
        <li><b>非表示の影はきちんと非表示に:</b> 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
</body>
</html>
EOF

# Build component package
echo "Building component package..."
pkgbuild \
    --root "$SRC_DIR/dist/OpenStrandStudio.app" \
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

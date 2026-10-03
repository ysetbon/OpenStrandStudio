#!/bin/bash

################################################################################
# OpenStrand Studio macOS PKG Installer Builder TEMPLATE
# Date: Created June 1, 2026
#
# LOGIC EXPLANATION:
# ==================
# This script creates a macOS .pkg installer with full multilingual support
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
# This is a template file. To create a new version installer:
# 1. Copy this file to build_installer_1_XXX.sh (replace XXX with version number)
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
VERSION="2.0"
APP_DATE="04_October_2026"
PUBLISHER="Yonatan Setbon"
IDENTIFIER="com.yonatan.openstrandstudio"

# All paths are relative to this script's own directory (the src folder), so
# the build works from any clone location.
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create directories
WORKING_DIR="$(mktemp -d)"
SCRIPTS_DIR="$WORKING_DIR/scripts"
RESOURCES_DIR="$WORKING_DIR/resources"
# Use underscores instead of dots in the output filename (2.0 -> 2_0) so the
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
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires pour installer ce logiciel.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p dir="ltr">This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p dir="ltr">What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p dir="ltr">Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p dir="ltr">Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p dir="ltr">Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p dir="ltr">Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p dir="ltr">Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p dir="ltr">Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p dir="ltr">Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p dir="ltr">Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p dir="ltr">Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p dir="ltr">Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p dir="ltr">Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p dir="ltr">Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p dir="ltr">Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p dir="ltr">Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul dir="ltr">
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p dir="ltr">Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p dir="ltr">Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p dir="ltr">このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p dir="ltr">バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul dir="ltr">
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p dir="ltr">本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p dir="ltr">版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul dir="ltr">
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
        <li><b>7つの新しいサンプル:</b> 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
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
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.0</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.0 的新功能:</p>
    <p>为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>绳股/遮罩标签页:</b> 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。</li>
        <li><b>修复阴影问题:</b> 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。</li>
        <li><b>七个新示例:</b> 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.0</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.0:</p>
    <p>Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Strands and Masks Tabs:</b> The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.</li>
        <li><b>Fixed Shadow Issues:</b> Fixed shadow issues from older versions. Shadows for masks now behave more naturally.</li>
        <li><b>Seven New Samples:</b> In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.0</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.0:</p>
    <p>Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Tabs Stränge und Masken:</b> Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.</li>
        <li><b>Schattenprobleme behoben:</b> Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.</li>
        <li><b>Sieben neue Beispiele:</b> In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.0</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.0 :</p>
    <p>Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Onglets Brins et Masques:</b> La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.</li>
        <li><b>Ombres corrigées:</b> Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.</li>
        <li><b>Sept nouveaux exemples:</b> Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.0</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.0:</p>
    <p>Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Schede Trefoli e Maschere:</b> L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.</li>
        <li><b>Problemi delle ombre risolti:</b> Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.</li>
        <li><b>Sette nuovi esempi:</b> In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.0</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.0:</p>
    <p>¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Pestañas Cordones y Máscaras:</b> La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.</li>
        <li><b>Problemas de sombras corregidos:</b> Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.</li>
        <li><b>Siete ejemplos nuevos:</b> En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.0</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.0:</p>
    <p>Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Separadores Mechas e Máscaras:</b> A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.</li>
        <li><b>Problemas de sombras corrigidos:</b> Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.</li>
        <li><b>Sete novos exemplos:</b> Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.0</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.0:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.0? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;:</b> &#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05EA; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05DE;&#x05D7;&#x05D5;&#x05DC;&#x05E7;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA;, &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05DD; &#x05DE;&#x05EA;&#x05D2; &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05E2;&#x05DC; &#x05E6;&#x05D9;&#x05D9;&#x05E8; &#x05E9;&#x05DE;&#x05D5;&#x05EA;. &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D9;&#x05E9; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05DE;&#x05E9;&#x05DC;&#x05D4;: &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4;, &#x05DE;&#x05D7;&#x05E7; &#x05DE;&#x05E1;&#x05DB;&#x05D4;, &#x05D1;&#x05D8;&#x05DC; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D5;&#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC;, &#x05D5;&#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05DE;&#x05D7;&#x05DC;&#x05D9;&#x05E3; &#x05D0;&#x05EA; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD;. &#x05DE;&#x05D7;&#x05E7; &#x05D4;&#x05DB;&#x05DC; &#x05D1;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05D6;&#x05D5; &#x05DE;&#x05D5;&#x05D7;&#x05E7;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8;, &#x05D5;&#x05D1;&#x05E9;&#x05DC;&#x05D1; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D0;&#x05D7;&#x05D3;. &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D5;&#x05EA; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05DE;&#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DE;&#x05DF; &#x05D1;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05E9;&#x05E0;&#x05D4;, &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05D4;&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D4;&#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05D4; &#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;. &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E0;&#x05D4;&#x05D2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D1;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05E9;&#x05D1;&#x05E2; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA;:</b> &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA;, &#x05EA;&#x05D7;&#x05EA; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA;, &#x05D9;&#x05E9; &#x05E9;&#x05D1;&#x05E2;&#x05D4; &#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; &#x05DC;&#x05E4;&#x05EA;&#x05D5;&#x05D7; &#x05D5;&#x05DC;&#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05DE;&#x05D4;&#x05DD;: &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D9;&#x05E9;&#x05E8;&#x05D4; 12&#x00D7;12, &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05DE;&#x05E2;&#x05D5;&#x05E7;&#x05DC;&#x05EA; 6&#x00D7;6, &#x05E6;&#x05DE;&#x05D4; &#x05E9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;, &#x05E2;&#x05D1;&#x05D4; &#x05D5;&#x05D3;&#x05E7;, &#x05D2;&#x05E9;&#x05E8;, &#x05D6;&#x05D5;&#x05D2;&#x05D5;&#x05EA; &#x05DE;&#x05E4;&#x05D5;&#x05EA;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05EA; &#x05E7;&#x05D2;&#x05D5;&#x05DE;&#x05D4;. &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D0;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05D5;&#x05D3;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E9;&#x05E0;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05D4;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05DC; &#x05D4;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05E0;&#x05DB;&#x05E0;&#x05E1;&#x05EA; &#x05D1;&#x05E2;&#x05DE;&#x05D5;&#x05D3;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.0</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.0:</p>
    <p>Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Вкладки «Пряди» и «Маски»:</b> Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.</li>
        <li><b>Исправлены проблемы с тенями:</b> Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.</li>
        <li><b>Семь новых примеров:</b> в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.0 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.0:</p>
    <p>Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Säikeet- ja Maskit-välilehdet:</b> Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.</li>
        <li><b>Varjo-ongelmat korjattu:</b> Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.</li>
        <li><b>Seitsemän uutta esimerkkiä:</b> asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.0</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.0:</p>
    <p>Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Flikarna Strängar och Masker:</b> Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.</li>
        <li><b>Skuggproblem åtgärdade:</b> Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.</li>
        <li><b>Sju nya exempel:</b> i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.0 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.0 の新機能:</p>
    <p>なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>ストランド/マスクタブ:</b> レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。</li>
        <li><b>影の問題を修正:</b> 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。</li>
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

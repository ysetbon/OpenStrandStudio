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
VERSION="2.1"
APP_DATE="19_October_2026"
PUBLISHER="Yonatan Setbon"
IDENTIFIER="com.yonatan.openstrandstudio"

# All paths are relative to this script's own directory (the src folder), so
# the build works from any clone location.
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create directories
WORKING_DIR="$(mktemp -d)"
SCRIPTS_DIR="$WORKING_DIR/scripts"
RESOURCES_DIR="$WORKING_DIR/resources"
# Use underscores instead of dots in the output filename (2.1 -> 2_1) so the
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
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires pour installer ce logiciel.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p dir="ltr">This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p dir="ltr">What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p dir="ltr">Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p dir="ltr">Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p dir="ltr">Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p dir="ltr">Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p dir="ltr">Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p dir="ltr">Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p dir="ltr">Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p dir="ltr">Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p dir="ltr">Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p dir="ltr">Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p dir="ltr">Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p dir="ltr">Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p dir="ltr">Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p dir="ltr">Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul dir="ltr">
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p dir="ltr">Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p dir="ltr">Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul dir="ltr">
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p dir="ltr">このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p dir="ltr">バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul dir="ltr">
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p dir="ltr">本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p dir="ltr">版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul dir="ltr">
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Chinese -->
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
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
    <h2 dir="ltr">欢迎使用 OpenStrandStudio 2.1</h2>
    <p>本程序将在您的计算机上安装 OpenStrandStudio。安装向导将引导您完成必要的步骤。</p>
    <p>版本 2.1 的新功能:</p>
    <p>为什么是2.1？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。</p>
    <ul>
        <li><b>界面音效:</b> 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。</li>
        <li><b>旋转模式的三角形和表盘:</b> 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。</li>
        <li><b>修复:</b> 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 2.1</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 2.1:</p>
    <p>Why 2.1? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.</p>
    <ul>
        <li><b>Interface Sounds:</b> Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.</li>
        <li><b>Rotate Mode Triangles and Dial:</b> Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.</li>
        <li><b>Fixes:</b> Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 2.1</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 2.1:</p>
    <p>Warum 2.1? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.</p>
    <ul>
        <li><b>Oberflächenklänge:</b> Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.</li>
        <li><b>Dreiecke und Skala im Modus Drehen:</b> Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.</li>
        <li><b>Fehlerbehebungen:</b> Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 2.1</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 2.1 :</p>
    <p>Pourquoi 2.1 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.</p>
    <ul>
        <li><b>Sons de l'interface:</b> Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.</li>
        <li><b>Triangles et cadran en mode Pivoter:</b> Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.</li>
        <li><b>Corrections:</b> Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 2.1</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 2.1:</p>
    <p>Perché 2.1? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.</p>
    <ul>
        <li><b>Suoni dell'interfaccia:</b> Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.</li>
        <li><b>Triangoli e quadrante in modalità Ruota:</b> Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.</li>
        <li><b>Correzioni:</b> Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 2.1</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 2.1:</p>
    <p>¿Por qué 2.1? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.</p>
    <ul>
        <li><b>Sonidos de la interfaz:</b> Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.</li>
        <li><b>Triángulos y dial en el modo Rotar:</b> Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.</li>
        <li><b>Correcciones:</b> Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 2.1</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 2.1:</p>
    <p>Porquê 2.1? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.</p>
    <ul>
        <li><b>Sons da interface:</b> Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.</li>
        <li><b>Triângulos e mostrador no modo Girar:</b> Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.</li>
        <li><b>Correções:</b> As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 2.1</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 2.1:</p>
    <p>&#x05DC;&#x05DE;&#x05D4; 2.1? &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05E8;&#x05D2;&#x05D9;&#x05E9;&#x05D5;&#x05EA; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D4;&#x05E8;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05D8;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05DC;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05E9;. &#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4; &#x05D4;&#x05D9;&#x05D0; &#x05DE;&#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9; &#x05D1;&#x05E7;&#x05E9;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E9;&#x05E8;&#x05D9;&#x05DD;, &#x05D5;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05D4;&#x05DF; &#x05D7;&#x05DC;&#x05E7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05D2;&#x05D4;, &#x05D5;&#x05DC;&#x05DB;&#x05DF; &#x05D6;&#x05D4;&#x05D5; &#x05E6;&#x05E2;&#x05D3; &#x05DE;&#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05EA;&#x05D9; &#x05E2;&#x05D1;&#x05D5;&#x05E8; OpenStrand Studio.</p>
    <ul>
        <li><b>&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;, &#x05EA;&#x05E4;&#x05E8;&#x05D9;&#x05D8;, &#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05EA; &#x05D5;&#x05E8;&#x05E9;&#x05D9;&#x05DE;&#x05D4; &#x05DE;&#x05E9;&#x05DE;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E7;&#x05E6;&#x05E8;, &#x05D5;&#x05DC;&#x05DB;&#x05DC; &#x05DE;&#x05E6;&#x05D1; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05DB;&#x05E9;&#x05DE;&#x05E4;&#x05E2;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05DB;&#x05D1;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05EA;&#x05D5;. &#x05DC;&#x05DB;&#x05DC; &#x05D0;&#x05D6;&#x05D5;&#x05E8; &#x05D1;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05D9;&#x05E9; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05E8;&#x05DA; &#x05DE;&#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1; &#x05E0;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC; &#x05DB;&#x05E9;&#x05EA;&#x05D5;&#x05E4;&#x05E1;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;, &#x05D5;&#x05EA;&#x05E7;&#x05EA;&#x05D5;&#x05E7; &#x05D1;&#x05DB;&#x05DC; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05E2;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4;. &#x05D1;&#x05EA;&#x05D7;&#x05EA;&#x05D9;&#x05EA; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D5;&#x05EA;, &#x05D4;&#x05E9;&#x05EA;&#x05DE;&#x05E9;&#x05D5; &#x05D1;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05DE;&#x05E9;&#x05E7;&#x05F4;, &#x05F4;&#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;&#x05F4; &#x05D5;&#x05F4;&#x05D4;&#x05E9;&#x05DE;&#x05E2; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05E2;&#x05DB;&#x05D1;&#x05E8;&#x05F4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9;&#x05DD;, &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05E2;&#x05D5;&#x05E6;&#x05DE;&#x05EA;&#x05DD; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E8;&#x05E7; &#x05D0;&#x05EA; &#x05E6;&#x05DC;&#x05D9;&#x05DC;&#x05D9; &#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;.</li>
        <li><b>&#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05D5;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E1;&#x05D9;&#x05D1;&#x05D5;&#x05D1;:</b> &#x05DE;&#x05E9;&#x05D5;&#x05DC;&#x05E9;&#x05D9;&#x05DD; &#x05DE;&#x05E1;&#x05DE;&#x05E0;&#x05D9;&#x05DD; &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05DB;&#x05DC; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05D8; &#x05E9;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E1;&#x05D5;&#x05D1;&#x05D1;: &#x05D0;&#x05D3;&#x05D5;&#x05DD; &#x05D1;&#x05EA;&#x05D7;&#x05D9;&#x05DC;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05DB;&#x05D7;&#x05D5;&#x05DC; &#x05D1;&#x05E1;&#x05D5;&#x05E4;&#x05D5; &#x05D5;&#x05E6;&#x05D4;&#x05D5;&#x05D1; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05DE;&#x05DF;. &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D4; &#x05E1;&#x05D1;&#x05D9;&#x05D1; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05E6;&#x05D9;&#x05E8; &#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05E2;&#x05DD; &#x05E1;&#x05D9;&#x05DE;&#x05D5;&#x05DF; &#x05DB;&#x05DC; 15&#x00B0;, &#x05E9;&#x05E6;&#x05D5;&#x05D1;&#x05E2;&#x05EA; &#x05DB;&#x05DE;&#x05D4; &#x05E1;&#x05D5;&#x05D1;&#x05D1;&#x05EA;&#x05DD;. &#x05D1;&#x05EA;&#x05D5;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DE;&#x05E1;&#x05EA;&#x05D5;&#x05D1;&#x05D1; &#x05DC;&#x05D0;&#x05D8; &#x05D9;&#x05D5;&#x05EA;&#x05E8;, &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05E2;&#x05D3;&#x05D9;&#x05DF;. &#x05E2;&#x05D5;&#x05EA;&#x05E7; &#x05D3;&#x05D4;&#x05D5;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05E2;&#x05D3; &#x05E9;&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05EA;&#x05E7;&#x05E4;&#x05DC;&#x05D9;&#x05DD; &#x05DC;&#x05D0;&#x05D7;&#x05D5;&#x05E8; &#x05E2;&#x05DC; &#x05E2;&#x05E6;&#x05DE;&#x05DD; &#x05DB;&#x05E9;&#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4;. &#x05D7;&#x05D5;&#x05D8; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05DE;&#x05D0;&#x05D1;&#x05D3; &#x05D0;&#x05EA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC;&#x05D5; &#x05D1;&#x05DE;&#x05E7;&#x05D5;&#x05DD; &#x05E9;&#x05D1;&#x05D5; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E0;&#x05D5;&#x05D2;&#x05E2;&#x05EA; &#x05D1;&#x05D5; &#x05E8;&#x05E7; &#x05DC;&#x05D0;&#x05D5;&#x05E8;&#x05DA; &#x05E7;&#x05E6;&#x05D4;. &#x05E9;&#x05D7;&#x05E8;&#x05D5;&#x05E8; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DB;&#x05E9;&#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05D5;&#x05D9;&#x05D9;&#x05DD;.</li>
    </ul>
    </div>
    <hr>
    <!-- Russian -->
    <h2 dir="ltr">Добро пожаловать в OpenStrandStudio 2.1</h2>
    <p>Эта программа установит OpenStrandStudio на ваш компьютер. Вы пройдёте все необходимые шаги установки.</p>
    <p>Что нового в версии 2.1:</p>
    <p>Почему 2.1? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.</p>
    <ul>
        <li><b>Звуки интерфейса:</b> Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.</li>
        <li><b>Треугольники и шкала в режиме «Вращать»:</b> Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.</li>
        <li><b>Исправления:</b> Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.</li>
    </ul>
    <hr>
    <!-- Finnish -->
    <h2 dir="ltr">Tervetuloa OpenStrandStudio 2.1 -ohjelmaan</h2>
    <p>Tämä asentaa OpenStrandStudion tietokoneellesi. Sinut opastetaan asennuksen vaiheiden läpi.</p>
    <p>Mitä uutta versiossa 2.1:</p>
    <p>Miksi 2.1? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.</p>
    <ul>
        <li><b>Käyttöliittymän äänet:</b> Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.</li>
        <li><b>Kolmiot ja asteikko Kierrä-tilassa:</b> Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.</li>
        <li><b>Korjaukset:</b> Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.</li>
    </ul>
    <hr>
    <!-- Swedish -->
    <h2 dir="ltr">Välkommen till OpenStrandStudio 2.1</h2>
    <p>Detta installerar OpenStrandStudio på din dator. Du guidas genom stegen som behövs för att installera programmet.</p>
    <p>Nyheter i version 2.1:</p>
    <p>Varför 2.1? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.</p>
    <ul>
        <li><b>Gränssnittsljud:</b> Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.</li>
        <li><b>Trianglar och skala i läget Rotera:</b> Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.</li>
        <li><b>Åtgärdade fel:</b> Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.</li>
    </ul>
    <hr>
    <!-- Japanese -->
    <h2 dir="ltr">OpenStrandStudio 2.1 へようこそ</h2>
    <p>このプログラムは OpenStrandStudio をお使いのコンピューターにインストールします。インストールに必要な手順を順に案内します。</p>
    <p>バージョン 2.1 の新機能:</p>
    <p>なぜ2.1なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。</p>
    <ul>
        <li><b>インターフェース音:</b> すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。</li>
        <li><b>回転モードの三角形とダイヤル:</b> 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。</li>
        <li><b>修正:</b> 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。</li>
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

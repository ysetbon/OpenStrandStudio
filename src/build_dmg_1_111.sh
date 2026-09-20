#!/bin/bash

################################################################################
# OpenStrand Studio macOS DMG Builder TEMPLATE
# Date: Created June 11, 2026
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
VERSION="1.111"
APP_DATE="20_September_2026"
PUBLISHER="Yonatan Setbon"
IDENTIFIER="com.yonatan.openstrandstudio"

# All paths are relative to this script's own directory (the src folder), so
# the build works from any clone location.
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create directories
WORKING_DIR="$(mktemp -d)"
SCRIPTS_DIR="$WORKING_DIR/scripts"
RESOURCES_DIR="$WORKING_DIR/resources"
# Use underscores instead of dots in the output filename (1.111 -> 1_111) so the
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
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.111</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.111:</p>
    <ul>
        <li><b>Stylize End Side:</b> Right-click a layer with a free end and pick Stylize End Side, just under Close the Knot. A dialog lets you choose how the strand ends: Straight, Angled, Rounded, Pointed, Notched or Concave. You can also set the tilt and depth, extend or trim the end, and add a side line with its own thickness and color. The preview is live on the canvas. The shadow, side line and masks all follow the new shape. End styles are saved with your project and work with undo and redo.</li>
        <li><b>Right Size on Scaled Screens:</b> On high-resolution screens with display scaling turned on, the buttons and text used to look too small. The app now follows your display scale. Toolbar labels no longer get cut off, and the toolbar moves onto two rows when the window is narrow. The layer panel can be dragged narrower than before. The OpenStrand Studio logo now appears on every window and in the taskbar.</li>
        <li><b>Dialogs Fit Small Screens:</b> The Settings dialog can now be made smaller, so its Apply and OK buttons always stay on screen. The same goes for Edit Shadow, the group shadow editor, Create Mask Grid, Edit Strand Angles, Change Width and the video player. A dialog never opens larger than your screen, and it keeps the size you give it.</li>
        <li><b>Smoother Dragging:</b> The canvas stays sharp while you drag, even on scaled displays or with supersampling on. Move mode shows a closed hand while dragging a point. View mode can now pan with the left mouse button too. The Refresh button's tooltip now says what it does: reload layers and reset the view.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.111</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.111:</p>
    <ul>
        <li><b>Endseite gestalten:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene mit einem freien Ende und wählen Sie Endseite gestalten, direkt unter Knoten schließen. In einem Dialog wählen Sie, wie der Strang endet: Gerade, Schräg, Abgerundet, Spitz, Eingekerbt oder Konkav. Sie können außerdem Neigung und Tiefe einstellen, das Ende verlängern oder kürzen und eine Seitenlinie mit eigener Dicke und Farbe hinzufügen. Die Vorschau erscheint live auf der Zeichenfläche. Schatten, Seitenlinie und Masken folgen alle der neuen Form. Endstile werden mit dem Projekt gespeichert und funktionieren mit Rückgängig und Wiederherstellen.</li>
        <li><b>Richtige Größe auf skalierten Bildschirmen:</b> Auf hochauflösenden Bildschirmen mit aktivierter Anzeigeskalierung wirkten Schaltflächen und Text zu klein. Die App folgt jetzt Ihrer Anzeigeskalierung. Beschriftungen in der Werkzeugleiste werden nicht mehr abgeschnitten, und die Werkzeugleiste wechselt bei schmalen Fenstern auf zwei Zeilen. Das Ebenenpanel lässt sich schmaler ziehen als zuvor. Das OpenStrand Studio Logo erscheint jetzt in jedem Fenster und in der Taskleiste.</li>
        <li><b>Dialoge passen auf kleine Bildschirme:</b> Der Dialog Einstellungen kann jetzt verkleinert werden, sodass seine Schaltflächen Übernehmen und OK immer sichtbar bleiben. Dasselbe gilt für Schatten bearbeiten, den Gruppenschatten-Editor, Maskenraster Erstellen, Strangwinkel bearbeiten, Breite ändern und den Videoplayer. Ein Dialog öffnet sich nie größer als Ihr Bildschirm und behält die Größe, die Sie ihm geben.</li>
        <li><b>Flüssigeres Ziehen:</b> Die Zeichenfläche bleibt beim Ziehen scharf, auch auf skalierten Bildschirmen oder mit eingeschaltetem Supersampling. Der Verschiebemodus zeigt beim Ziehen eines Punktes eine geschlossene Hand. Der Ansichtsmodus kann jetzt auch mit der linken Maustaste verschoben werden. Der Tooltip der Schaltfläche Aktualisieren sagt jetzt, was sie tut: Ebenen neu laden und Ansicht zurücksetzen.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.111</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.111 :</p>
    <ul>
        <li><b>Styliser le côté d'extrémité:</b> Faites un clic droit sur un calque ayant une extrémité libre et choisissez Styliser le côté d'extrémité, juste sous Fermer le Nœud. Une boîte de dialogue vous laisse choisir la forme de l'extrémité du brin : Droite, Inclinée, Arrondie, Pointue, Entaillée ou Concave. Vous pouvez aussi régler l'inclinaison et la profondeur, allonger ou raccourcir l'extrémité, et ajouter une ligne latérale avec sa propre épaisseur et sa propre couleur. L'aperçu est en direct sur le canevas. L'ombre, la ligne latérale et les masques suivent tous la nouvelle forme. Les styles d'extrémité sont enregistrés avec votre projet et fonctionnent avec annuler et rétablir.</li>
        <li><b>La bonne taille sur les écrans mis à l'échelle:</b> Sur les écrans haute résolution avec une mise à l'échelle de l'affichage, les boutons et le texte paraissaient trop petits. L'application suit désormais l'échelle de votre écran. Les libellés de la barre d'outils ne sont plus coupés, et la barre d'outils passe sur deux lignes quand la fenêtre est étroite. Le panneau des calques peut être réduit plus qu'avant. Le logo OpenStrand Studio apparaît maintenant sur chaque fenêtre et dans la barre des tâches.</li>
        <li><b>Des boîtes de dialogue adaptées aux petits écrans:</b> La boîte de dialogue Paramètres peut désormais être réduite, de sorte que ses boutons Appliquer et OK restent toujours à l'écran. Il en va de même pour Modifier l'ombre, l'éditeur d'ombre de groupe, Créer Grille de Masque, Modifier les angles des brins, Changer largeur et le lecteur vidéo. Une boîte de dialogue ne s'ouvre jamais plus grande que votre écran, et elle garde la taille que vous lui donnez.</li>
        <li><b>Un glissement plus fluide:</b> Le canevas reste net pendant que vous faites glisser, même sur les écrans mis à l'échelle ou avec le suréchantillonnage activé. Le mode déplacement affiche une main fermée pendant le glissement d'un point. Le mode vue peut maintenant aussi se déplacer avec le bouton gauche de la souris. L'info-bulle du bouton Actualiser indique désormais ce qu'il fait : recharger les calques et réinitialiser la vue.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.111</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.111:</p>
    <ul>
        <li><b>Stilizza il lato finale:</b> Fai clic destro su un livello con un'estremità libera e scegli Stilizza il lato finale, subito sotto Chiudi il Nodo. Una finestra ti permette di scegliere come termina il trefolo: Dritta, Inclinata, Arrotondata, Appuntita, Intagliata o Concava. Puoi anche regolare inclinazione e profondità, allungare o accorciare l'estremità e aggiungere una linea laterale con spessore e colore propri. L'anteprima è dal vivo sulla tela. Ombra, linea laterale e maschere seguono tutte la nuova forma. Gli stili delle estremità vengono salvati con il progetto e funzionano con annulla e ripristina.</li>
        <li><b>Dimensione giusta sugli schermi ridimensionati:</b> Sugli schermi ad alta risoluzione con il ridimensionamento attivo, pulsanti e testo apparivano troppo piccoli. L'app ora segue la scala del tuo schermo. Le etichette della barra degli strumenti non vengono più tagliate, e la barra passa su due righe quando la finestra è stretta. Il pannello dei livelli può essere ristretto più di prima. Il logo di OpenStrand Studio appare ora su ogni finestra e nella barra delle applicazioni.</li>
        <li><b>Finestre adatte agli schermi piccoli:</b> La finestra Impostazioni ora può essere rimpicciolita, così i pulsanti Applica e OK restano sempre visibili. Lo stesso vale per Modifica ombra, l'editor dell'ombra di gruppo, Crea Griglia Maschera, Modifica Angoli Trefolo, Cambia larghezza e il lettore video. Una finestra non si apre mai più grande dello schermo e mantiene la dimensione che le dai.</li>
        <li><b>Trascinamento più fluido:</b> La tela resta nitida mentre trascini, anche su schermi ridimensionati o con il supersampling attivo. La modalità sposta mostra una mano chiusa mentre trascini un punto. La modalità vista ora può scorrere anche con il tasto sinistro del mouse. Il suggerimento del pulsante Aggiorna ora dice cosa fa: ricarica i livelli e reimposta la vista.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.111</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.111:</p>
    <ul>
        <li><b>Estilizar lado del extremo:</b> Haz clic derecho en una capa con un extremo libre y elige Estilizar lado del extremo, justo debajo de Cerrar el Nudo. Un cuadro de diálogo te permite elegir cómo termina el cordón: Recto, Inclinado, Redondeado, Puntiagudo, Con muesca o Cóncavo. También puedes ajustar la inclinación y la profundidad, alargar o recortar el extremo, y añadir una línea lateral con su propio grosor y color. La vista previa es en vivo sobre el lienzo. La sombra, la línea lateral y las máscaras siguen la nueva forma. Los estilos de extremo se guardan con tu proyecto y funcionan con deshacer y rehacer.</li>
        <li><b>Tamaño correcto en pantallas escaladas:</b> En pantallas de alta resolución con el escalado activado, los botones y el texto se veían demasiado pequeños. La aplicación ahora sigue la escala de tu pantalla. Las etiquetas de la barra de herramientas ya no se cortan, y la barra pasa a dos filas cuando la ventana es estrecha. El panel de capas se puede estrechar más que antes. El logotipo de OpenStrand Studio aparece ahora en cada ventana y en la barra de tareas.</li>
        <li><b>Diálogos que caben en pantallas pequeñas:</b> El diálogo Configuración ahora se puede hacer más pequeño, así sus botones Aplicar y OK siempre quedan en pantalla. Lo mismo ocurre con Editar sombra, el editor de sombra de grupo, Crear Cuadrícula de Máscara, Editar Ángulos del Cordón, Cambiar ancho y el reproductor de video. Un diálogo nunca se abre más grande que tu pantalla, y conserva el tamaño que le das.</li>
        <li><b>Arrastre más suave:</b> El lienzo se mantiene nítido mientras arrastras, incluso en pantallas escaladas o con el supermuestreo activado. El modo mover muestra una mano cerrada mientras arrastras un punto. El modo vista ahora también puede desplazarse con el botón izquierdo del ratón. La descripción del botón Actualizar ahora dice lo que hace: recargar las capas y restablecer la vista.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.111</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.111:</p>
    <ul>
        <li><b>Estilizar lado da extremidade:</b> Clique com o botão direito numa camada com uma extremidade livre e escolha Estilizar lado da extremidade, logo abaixo de Fechar o Nó. Uma janela permite escolher como a mecha termina: Reta, Inclinada, Arredondada, Pontiaguda, Entalhada ou Côncava. Também pode ajustar a inclinação e a profundidade, alongar ou encurtar a extremidade e adicionar uma linha lateral com espessura e cor próprias. A pré-visualização é ao vivo na tela. A sombra, a linha lateral e as máscaras seguem todas a nova forma. Os estilos de extremidade são salvos com o projeto e funcionam com desfazer e refazer.</li>
        <li><b>Tamanho certo em ecrãs com escala:</b> Em ecrãs de alta resolução com a escala de exibição ativada, os botões e o texto pareciam pequenos demais. A aplicação agora segue a escala do seu ecrã. Os rótulos da barra de ferramentas já não são cortados, e a barra passa para duas linhas quando a janela é estreita. O painel de camadas pode ser estreitado mais do que antes. O logótipo do OpenStrand Studio aparece agora em todas as janelas e na barra de tarefas.</li>
        <li><b>Janelas que cabem em ecrãs pequenos:</b> A janela Configurações agora pode ser reduzida, para que os botões Aplicar e OK fiquem sempre visíveis. O mesmo vale para Editar sombra, o editor de sombra de grupo, Criar Grade de Máscara, Editar Ângulos da Mecha, Mudar largura e o reprodutor de vídeo. Uma janela nunca abre maior do que o seu ecrã e mantém o tamanho que lhe der.</li>
        <li><b>Arrasto mais suave:</b> A tela permanece nítida enquanto arrasta, mesmo em ecrãs com escala ou com a superamostragem ativada. O modo mover mostra uma mão fechada enquanto arrasta um ponto. O modo de visualização agora também pode deslocar-se com o botão esquerdo do rato. A dica do botão Atualizar agora diz o que ele faz: recarregar as camadas e redefinir a vista.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.111</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.111:</p>
    <ul>
        <li><b>&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9; &#x05D5;&#x05D1;&#x05D7;&#x05E8;&#x05D5; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05D0;&#x05D9;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05D9;&#x05DD;: &#x05D9;&#x05E9;&#x05E8;, &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E2;, &#x05DE;&#x05E2;&#x05D5;&#x05D2;&#x05DC;, &#x05DE;&#x05D7;&#x05D5;&#x05D3;&#x05D3;, &#x05D7;&#x05E8;&#x05D5;&#x05E5; &#x05D0;&#x05D5; &#x05E7;&#x05E2;&#x05D5;&#x05E8;. &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05D2;&#x05DD; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05DF; &#x05D0;&#x05EA; &#x05D4;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D5;&#x05D4;&#x05E2;&#x05D5;&#x05DE;&#x05E7;, &#x05DC;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05DA; &#x05D0;&#x05D5; &#x05DC;&#x05E7;&#x05E6;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05D5;&#x05DC;&#x05D4;&#x05D5;&#x05E1;&#x05D9;&#x05E3; &#x05E7;&#x05D5; &#x05E6;&#x05D3; &#x05E2;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05D5;&#x05E6;&#x05D1;&#x05E2; &#x05DE;&#x05E9;&#x05DC;&#x05D5;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05D7;&#x05D9;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;. &#x05D4;&#x05E6;&#x05DC;, &#x05E7;&#x05D5; &#x05D4;&#x05E6;&#x05D3; &#x05D5;&#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D4;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D4;&#x05D7;&#x05D3;&#x05E9;&#x05D4;. &#x05E1;&#x05D2;&#x05E0;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E2;&#x05D5;&#x05D1;&#x05D3;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;.</li>
        <li><b>&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E0;&#x05DB;&#x05D5;&#x05DF; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4;:</b> &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05D1;&#x05E8;&#x05D6;&#x05D5;&#x05DC;&#x05D5;&#x05E6;&#x05D9;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;, &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D4;&#x05D8;&#x05E7;&#x05E1;&#x05D8; &#x05E0;&#x05E8;&#x05D0;&#x05D5; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D9;. &#x05D4;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05E7;&#x05E0;&#x05D4; &#x05D4;&#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;. &#x05EA;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05E0;&#x05D7;&#x05EA;&#x05DB;&#x05D5;&#x05EA;, &#x05D5;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05E8; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05E9;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05DB;&#x05E9;&#x05D4;&#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05E6;&#x05E8;. &#x05D0;&#x05EA; &#x05DC;&#x05D5;&#x05D7; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05D5;&#x05E8; &#x05E6;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D1;&#x05E2;&#x05D1;&#x05E8;. &#x05D4;&#x05DC;&#x05D5;&#x05D2;&#x05D5; &#x05E9;&#x05DC; OpenStrand Studio &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D5;&#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05EA; &#x05D4;&#x05DE;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D7;&#x05DC;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DE;&#x05D9;&#x05DD; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05D0;&#x05EA; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05E7;&#x05D8;&#x05D9;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D7;&#x05DC; &#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA;. &#x05DB;&#x05DA; &#x05D2;&#x05DD; &#x05E2;&#x05E8;&#x05D9;&#x05DB;&#x05EA; &#x05E6;&#x05DC;, &#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC; &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;, &#x05E6;&#x05D5;&#x05E8; &#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05E8;&#x05D5;&#x05DA; &#x05D6;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05E9;&#x05E0;&#x05D4; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D5;&#x05E0;&#x05D2;&#x05DF; &#x05D4;&#x05D5;&#x05D5;&#x05D9;&#x05D3;&#x05D0;&#x05D5;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05DC;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05E0;&#x05E4;&#x05EA;&#x05D7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;, &#x05D5;&#x05D4;&#x05D5;&#x05D0; &#x05E9;&#x05D5;&#x05DE;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E9;&#x05E0;&#x05EA;&#x05EA;&#x05DD; &#x05DC;&#x05D5;.</li>
        <li><b>&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05DC;&#x05E7;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D7;&#x05D3; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4;, &#x05D2;&#x05DD; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05D0;&#x05D5; &#x05E2;&#x05DD; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05EA;-&#x05D9;&#x05EA;&#x05E8; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;&#x05EA;. &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05D9;&#x05D3; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D4; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D4;. &#x05DE;&#x05E6;&#x05D1; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D2;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E9;&#x05DE;&#x05D0;&#x05DC;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D4;&#x05D8;&#x05D9;&#x05E4; &#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E8;&#x05E2;&#x05E0;&#x05D5;&#x05DF; &#x05D0;&#x05D5;&#x05DE;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05D4; &#x05D4;&#x05D5;&#x05D0; &#x05E2;&#x05D5;&#x05E9;&#x05D4;: &#x05D8;&#x05D5;&#x05E2;&#x05DF; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D5;&#x05DE;&#x05D0;&#x05E4;&#x05E1; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;.</li>
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
    <p>Copyright (c) 2026 $PUBLISHER</p>
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
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.111</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires pour installer ce logiciel.</p>
    <p>Nouveautés de la version 1.111 :</p>
    <ul>
        <li><b>Styliser le côté d'extrémité:</b> Faites un clic droit sur un calque ayant une extrémité libre et choisissez Styliser le côté d'extrémité, juste sous Fermer le Nœud. Une boîte de dialogue vous laisse choisir la forme de l'extrémité du brin : Droite, Inclinée, Arrondie, Pointue, Entaillée ou Concave. Vous pouvez aussi régler l'inclinaison et la profondeur, allonger ou raccourcir l'extrémité, et ajouter une ligne latérale avec sa propre épaisseur et sa propre couleur. L'aperçu est en direct sur le canevas. L'ombre, la ligne latérale et les masques suivent tous la nouvelle forme. Les styles d'extrémité sont enregistrés avec votre projet et fonctionnent avec annuler et rétablir.</li>
        <li><b>La bonne taille sur les écrans mis à l'échelle:</b> Sur les écrans haute résolution avec une mise à l'échelle de l'affichage, les boutons et le texte paraissaient trop petits. L'application suit désormais l'échelle de votre écran. Les libellés de la barre d'outils ne sont plus coupés, et la barre d'outils passe sur deux lignes quand la fenêtre est étroite. Le panneau des calques peut être réduit plus qu'avant. Le logo OpenStrand Studio apparaît maintenant sur chaque fenêtre et dans la barre des tâches.</li>
        <li><b>Des boîtes de dialogue adaptées aux petits écrans:</b> La boîte de dialogue Paramètres peut désormais être réduite, de sorte que ses boutons Appliquer et OK restent toujours à l'écran. Il en va de même pour Modifier l'ombre, l'éditeur d'ombre de groupe, Créer Grille de Masque, Modifier les angles des brins, Changer largeur et le lecteur vidéo. Une boîte de dialogue ne s'ouvre jamais plus grande que votre écran, et elle garde la taille que vous lui donnez.</li>
        <li><b>Un glissement plus fluide:</b> Le canevas reste net pendant que vous faites glisser, même sur les écrans mis à l'échelle ou avec le suréchantillonnage activé. Le mode déplacement affiche une main fermée pendant le glissement d'un point. Le mode vue peut maintenant aussi se déplacer avec le bouton gauche de la souris. L'info-bulle du bouton Actualiser indique désormais ce qu'il fait : recharger les calques et réinitialiser la vue.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.111</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.111:</p>
    <ul>
        <li><b>Stylize End Side:</b> Right-click a layer with a free end and pick Stylize End Side, just under Close the Knot. A dialog lets you choose how the strand ends: Straight, Angled, Rounded, Pointed, Notched or Concave. You can also set the tilt and depth, extend or trim the end, and add a side line with its own thickness and color. The preview is live on the canvas. The shadow, side line and masks all follow the new shape. End styles are saved with your project and work with undo and redo.</li>
        <li><b>Right Size on Scaled Screens:</b> On high-resolution screens with display scaling turned on, the buttons and text used to look too small. The app now follows your display scale. Toolbar labels no longer get cut off, and the toolbar moves onto two rows when the window is narrow. The layer panel can be dragged narrower than before. The OpenStrand Studio logo now appears on every window and in the taskbar.</li>
        <li><b>Dialogs Fit Small Screens:</b> The Settings dialog can now be made smaller, so its Apply and OK buttons always stay on screen. The same goes for Edit Shadow, the group shadow editor, Create Mask Grid, Edit Strand Angles, Change Width and the video player. A dialog never opens larger than your screen, and it keeps the size you give it.</li>
        <li><b>Smoother Dragging:</b> The canvas stays sharp while you drag, even on scaled displays or with supersampling on. Move mode shows a closed hand while dragging a point. View mode can now pan with the left mouse button too. The Refresh button's tooltip now says what it does: reload layers and reset the view.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.111</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.111:</p>
    <ul>
        <li><b>Endseite gestalten:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene mit einem freien Ende und wählen Sie Endseite gestalten, direkt unter Knoten schließen. In einem Dialog wählen Sie, wie der Strang endet: Gerade, Schräg, Abgerundet, Spitz, Eingekerbt oder Konkav. Sie können außerdem Neigung und Tiefe einstellen, das Ende verlängern oder kürzen und eine Seitenlinie mit eigener Dicke und Farbe hinzufügen. Die Vorschau erscheint live auf der Zeichenfläche. Schatten, Seitenlinie und Masken folgen alle der neuen Form. Endstile werden mit dem Projekt gespeichert und funktionieren mit Rückgängig und Wiederherstellen.</li>
        <li><b>Richtige Größe auf skalierten Bildschirmen:</b> Auf hochauflösenden Bildschirmen mit aktivierter Anzeigeskalierung wirkten Schaltflächen und Text zu klein. Die App folgt jetzt Ihrer Anzeigeskalierung. Beschriftungen in der Werkzeugleiste werden nicht mehr abgeschnitten, und die Werkzeugleiste wechselt bei schmalen Fenstern auf zwei Zeilen. Das Ebenenpanel lässt sich schmaler ziehen als zuvor. Das OpenStrand Studio Logo erscheint jetzt in jedem Fenster und in der Taskleiste.</li>
        <li><b>Dialoge passen auf kleine Bildschirme:</b> Der Dialog Einstellungen kann jetzt verkleinert werden, sodass seine Schaltflächen Übernehmen und OK immer sichtbar bleiben. Dasselbe gilt für Schatten bearbeiten, den Gruppenschatten-Editor, Maskenraster Erstellen, Strangwinkel bearbeiten, Breite ändern und den Videoplayer. Ein Dialog öffnet sich nie größer als Ihr Bildschirm und behält die Größe, die Sie ihm geben.</li>
        <li><b>Flüssigeres Ziehen:</b> Die Zeichenfläche bleibt beim Ziehen scharf, auch auf skalierten Bildschirmen oder mit eingeschaltetem Supersampling. Der Verschiebemodus zeigt beim Ziehen eines Punktes eine geschlossene Hand. Der Ansichtsmodus kann jetzt auch mit der linken Maustaste verschoben werden. Der Tooltip der Schaltfläche Aktualisieren sagt jetzt, was sie tut: Ebenen neu laden und Ansicht zurücksetzen.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.111</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.111:</p>
    <ul>
        <li><b>Stilizza il lato finale:</b> Fai clic destro su un livello con un'estremità libera e scegli Stilizza il lato finale, subito sotto Chiudi il Nodo. Una finestra ti permette di scegliere come termina il trefolo: Dritta, Inclinata, Arrotondata, Appuntita, Intagliata o Concava. Puoi anche regolare inclinazione e profondità, allungare o accorciare l'estremità e aggiungere una linea laterale con spessore e colore propri. L'anteprima è dal vivo sulla tela. Ombra, linea laterale e maschere seguono tutte la nuova forma. Gli stili delle estremità vengono salvati con il progetto e funzionano con annulla e ripristina.</li>
        <li><b>Dimensione giusta sugli schermi ridimensionati:</b> Sugli schermi ad alta risoluzione con il ridimensionamento attivo, pulsanti e testo apparivano troppo piccoli. L'app ora segue la scala del tuo schermo. Le etichette della barra degli strumenti non vengono più tagliate, e la barra passa su due righe quando la finestra è stretta. Il pannello dei livelli può essere ristretto più di prima. Il logo di OpenStrand Studio appare ora su ogni finestra e nella barra delle applicazioni.</li>
        <li><b>Finestre adatte agli schermi piccoli:</b> La finestra Impostazioni ora può essere rimpicciolita, così i pulsanti Applica e OK restano sempre visibili. Lo stesso vale per Modifica ombra, l'editor dell'ombra di gruppo, Crea Griglia Maschera, Modifica Angoli Trefolo, Cambia larghezza e il lettore video. Una finestra non si apre mai più grande dello schermo e mantiene la dimensione che le dai.</li>
        <li><b>Trascinamento più fluido:</b> La tela resta nitida mentre trascini, anche su schermi ridimensionati o con il supersampling attivo. La modalità sposta mostra una mano chiusa mentre trascini un punto. La modalità vista ora può scorrere anche con il tasto sinistro del mouse. Il suggerimento del pulsante Aggiorna ora dice cosa fa: ricarica i livelli e reimposta la vista.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.111</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.111:</p>
    <ul>
        <li><b>Estilizar lado del extremo:</b> Haz clic derecho en una capa con un extremo libre y elige Estilizar lado del extremo, justo debajo de Cerrar el Nudo. Un cuadro de diálogo te permite elegir cómo termina el cordón: Recto, Inclinado, Redondeado, Puntiagudo, Con muesca o Cóncavo. También puedes ajustar la inclinación y la profundidad, alargar o recortar el extremo, y añadir una línea lateral con su propio grosor y color. La vista previa es en vivo sobre el lienzo. La sombra, la línea lateral y las máscaras siguen la nueva forma. Los estilos de extremo se guardan con tu proyecto y funcionan con deshacer y rehacer.</li>
        <li><b>Tamaño correcto en pantallas escaladas:</b> En pantallas de alta resolución con el escalado activado, los botones y el texto se veían demasiado pequeños. La aplicación ahora sigue la escala de tu pantalla. Las etiquetas de la barra de herramientas ya no se cortan, y la barra pasa a dos filas cuando la ventana es estrecha. El panel de capas se puede estrechar más que antes. El logotipo de OpenStrand Studio aparece ahora en cada ventana y en la barra de tareas.</li>
        <li><b>Diálogos que caben en pantallas pequeñas:</b> El diálogo Configuración ahora se puede hacer más pequeño, así sus botones Aplicar y OK siempre quedan en pantalla. Lo mismo ocurre con Editar sombra, el editor de sombra de grupo, Crear Cuadrícula de Máscara, Editar Ángulos del Cordón, Cambiar ancho y el reproductor de video. Un diálogo nunca se abre más grande que tu pantalla, y conserva el tamaño que le das.</li>
        <li><b>Arrastre más suave:</b> El lienzo se mantiene nítido mientras arrastras, incluso en pantallas escaladas o con el supermuestreo activado. El modo mover muestra una mano cerrada mientras arrastras un punto. El modo vista ahora también puede desplazarse con el botón izquierdo del ratón. La descripción del botón Actualizar ahora dice lo que hace: recargar las capas y restablecer la vista.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.111</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.111:</p>
    <ul>
        <li><b>Estilizar lado da extremidade:</b> Clique com o botão direito numa camada com uma extremidade livre e escolha Estilizar lado da extremidade, logo abaixo de Fechar o Nó. Uma janela permite escolher como a mecha termina: Reta, Inclinada, Arredondada, Pontiaguda, Entalhada ou Côncava. Também pode ajustar a inclinação e a profundidade, alongar ou encurtar a extremidade e adicionar uma linha lateral com espessura e cor próprias. A pré-visualização é ao vivo na tela. A sombra, a linha lateral e as máscaras seguem todas a nova forma. Os estilos de extremidade são salvos com o projeto e funcionam com desfazer e refazer.</li>
        <li><b>Tamanho certo em ecrãs com escala:</b> Em ecrãs de alta resolução com a escala de exibição ativada, os botões e o texto pareciam pequenos demais. A aplicação agora segue a escala do seu ecrã. Os rótulos da barra de ferramentas já não são cortados, e a barra passa para duas linhas quando a janela é estreita. O painel de camadas pode ser estreitado mais do que antes. O logótipo do OpenStrand Studio aparece agora em todas as janelas e na barra de tarefas.</li>
        <li><b>Janelas que cabem em ecrãs pequenos:</b> A janela Configurações agora pode ser reduzida, para que os botões Aplicar e OK fiquem sempre visíveis. O mesmo vale para Editar sombra, o editor de sombra de grupo, Criar Grade de Máscara, Editar Ângulos da Mecha, Mudar largura e o reprodutor de vídeo. Uma janela nunca abre maior do que o seu ecrã e mantém o tamanho que lhe der.</li>
        <li><b>Arrasto mais suave:</b> A tela permanece nítida enquanto arrasta, mesmo em ecrãs com escala ou com a superamostragem ativada. O modo mover mostra uma mão fechada enquanto arrasta um ponto. O modo de visualização agora também pode deslocar-se com o botão esquerdo do rato. A dica do botão Atualizar agora diz o que ele faz: recarregar as camadas e redefinir a vista.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.111</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.111:</p>
    <ul>
        <li><b>&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9; &#x05D5;&#x05D1;&#x05D7;&#x05E8;&#x05D5; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05D0;&#x05D9;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05D9;&#x05DD;: &#x05D9;&#x05E9;&#x05E8;, &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E2;, &#x05DE;&#x05E2;&#x05D5;&#x05D2;&#x05DC;, &#x05DE;&#x05D7;&#x05D5;&#x05D3;&#x05D3;, &#x05D7;&#x05E8;&#x05D5;&#x05E5; &#x05D0;&#x05D5; &#x05E7;&#x05E2;&#x05D5;&#x05E8;. &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05D2;&#x05DD; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05DF; &#x05D0;&#x05EA; &#x05D4;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D5;&#x05D4;&#x05E2;&#x05D5;&#x05DE;&#x05E7;, &#x05DC;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05DA; &#x05D0;&#x05D5; &#x05DC;&#x05E7;&#x05E6;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05D5;&#x05DC;&#x05D4;&#x05D5;&#x05E1;&#x05D9;&#x05E3; &#x05E7;&#x05D5; &#x05E6;&#x05D3; &#x05E2;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05D5;&#x05E6;&#x05D1;&#x05E2; &#x05DE;&#x05E9;&#x05DC;&#x05D5;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05D7;&#x05D9;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;. &#x05D4;&#x05E6;&#x05DC;, &#x05E7;&#x05D5; &#x05D4;&#x05E6;&#x05D3; &#x05D5;&#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D4;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D4;&#x05D7;&#x05D3;&#x05E9;&#x05D4;. &#x05E1;&#x05D2;&#x05E0;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E2;&#x05D5;&#x05D1;&#x05D3;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;.</li>
        <li><b>&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E0;&#x05DB;&#x05D5;&#x05DF; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4;:</b> &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05D1;&#x05E8;&#x05D6;&#x05D5;&#x05DC;&#x05D5;&#x05E6;&#x05D9;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;, &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D4;&#x05D8;&#x05E7;&#x05E1;&#x05D8; &#x05E0;&#x05E8;&#x05D0;&#x05D5; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D9;. &#x05D4;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05E7;&#x05E0;&#x05D4; &#x05D4;&#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;. &#x05EA;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05E0;&#x05D7;&#x05EA;&#x05DB;&#x05D5;&#x05EA;, &#x05D5;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05E8; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05E9;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05DB;&#x05E9;&#x05D4;&#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05E6;&#x05E8;. &#x05D0;&#x05EA; &#x05DC;&#x05D5;&#x05D7; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05D5;&#x05E8; &#x05E6;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D1;&#x05E2;&#x05D1;&#x05E8;. &#x05D4;&#x05DC;&#x05D5;&#x05D2;&#x05D5; &#x05E9;&#x05DC; OpenStrand Studio &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D5;&#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05EA; &#x05D4;&#x05DE;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D7;&#x05DC;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DE;&#x05D9;&#x05DD; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05D0;&#x05EA; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05E7;&#x05D8;&#x05D9;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D7;&#x05DC; &#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA;. &#x05DB;&#x05DA; &#x05D2;&#x05DD; &#x05E2;&#x05E8;&#x05D9;&#x05DB;&#x05EA; &#x05E6;&#x05DC;, &#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC; &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;, &#x05E6;&#x05D5;&#x05E8; &#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05E8;&#x05D5;&#x05DA; &#x05D6;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05E9;&#x05E0;&#x05D4; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D5;&#x05E0;&#x05D2;&#x05DF; &#x05D4;&#x05D5;&#x05D5;&#x05D9;&#x05D3;&#x05D0;&#x05D5;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05DC;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05E0;&#x05E4;&#x05EA;&#x05D7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;, &#x05D5;&#x05D4;&#x05D5;&#x05D0; &#x05E9;&#x05D5;&#x05DE;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E9;&#x05E0;&#x05EA;&#x05EA;&#x05DD; &#x05DC;&#x05D5;.</li>
        <li><b>&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05DC;&#x05E7;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D7;&#x05D3; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4;, &#x05D2;&#x05DD; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05D0;&#x05D5; &#x05E2;&#x05DD; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05EA;-&#x05D9;&#x05EA;&#x05E8; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;&#x05EA;. &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05D9;&#x05D3; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D4; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D4;. &#x05DE;&#x05E6;&#x05D1; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D2;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E9;&#x05DE;&#x05D0;&#x05DC;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D4;&#x05D8;&#x05D9;&#x05E4; &#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E8;&#x05E2;&#x05E0;&#x05D5;&#x05DF; &#x05D0;&#x05D5;&#x05DE;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05D4; &#x05D4;&#x05D5;&#x05D0; &#x05E2;&#x05D5;&#x05E9;&#x05D4;: &#x05D8;&#x05D5;&#x05E2;&#x05DF; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D5;&#x05DE;&#x05D0;&#x05E4;&#x05E1; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;.</li>
    </ul>
    </div>
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
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.111</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.111:</p>
    <ul>
        <li><b>Endseite gestalten:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene mit einem freien Ende und wählen Sie Endseite gestalten, direkt unter Knoten schließen. In einem Dialog wählen Sie, wie der Strang endet: Gerade, Schräg, Abgerundet, Spitz, Eingekerbt oder Konkav. Sie können außerdem Neigung und Tiefe einstellen, das Ende verlängern oder kürzen und eine Seitenlinie mit eigener Dicke und Farbe hinzufügen. Die Vorschau erscheint live auf der Zeichenfläche. Schatten, Seitenlinie und Masken folgen alle der neuen Form. Endstile werden mit dem Projekt gespeichert und funktionieren mit Rückgängig und Wiederherstellen.</li>
        <li><b>Richtige Größe auf skalierten Bildschirmen:</b> Auf hochauflösenden Bildschirmen mit aktivierter Anzeigeskalierung wirkten Schaltflächen und Text zu klein. Die App folgt jetzt Ihrer Anzeigeskalierung. Beschriftungen in der Werkzeugleiste werden nicht mehr abgeschnitten, und die Werkzeugleiste wechselt bei schmalen Fenstern auf zwei Zeilen. Das Ebenenpanel lässt sich schmaler ziehen als zuvor. Das OpenStrand Studio Logo erscheint jetzt in jedem Fenster und in der Taskleiste.</li>
        <li><b>Dialoge passen auf kleine Bildschirme:</b> Der Dialog Einstellungen kann jetzt verkleinert werden, sodass seine Schaltflächen Übernehmen und OK immer sichtbar bleiben. Dasselbe gilt für Schatten bearbeiten, den Gruppenschatten-Editor, Maskenraster Erstellen, Strangwinkel bearbeiten, Breite ändern und den Videoplayer. Ein Dialog öffnet sich nie größer als Ihr Bildschirm und behält die Größe, die Sie ihm geben.</li>
        <li><b>Flüssigeres Ziehen:</b> Die Zeichenfläche bleibt beim Ziehen scharf, auch auf skalierten Bildschirmen oder mit eingeschaltetem Supersampling. Der Verschiebemodus zeigt beim Ziehen eines Punktes eine geschlossene Hand. Der Ansichtsmodus kann jetzt auch mit der linken Maustaste verschoben werden. Der Tooltip der Schaltfläche Aktualisieren sagt jetzt, was sie tut: Ebenen neu laden und Ansicht zurücksetzen.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.111</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.111:</p>
    <ul>
        <li><b>Stylize End Side:</b> Right-click a layer with a free end and pick Stylize End Side, just under Close the Knot. A dialog lets you choose how the strand ends: Straight, Angled, Rounded, Pointed, Notched or Concave. You can also set the tilt and depth, extend or trim the end, and add a side line with its own thickness and color. The preview is live on the canvas. The shadow, side line and masks all follow the new shape. End styles are saved with your project and work with undo and redo.</li>
        <li><b>Right Size on Scaled Screens:</b> On high-resolution screens with display scaling turned on, the buttons and text used to look too small. The app now follows your display scale. Toolbar labels no longer get cut off, and the toolbar moves onto two rows when the window is narrow. The layer panel can be dragged narrower than before. The OpenStrand Studio logo now appears on every window and in the taskbar.</li>
        <li><b>Dialogs Fit Small Screens:</b> The Settings dialog can now be made smaller, so its Apply and OK buttons always stay on screen. The same goes for Edit Shadow, the group shadow editor, Create Mask Grid, Edit Strand Angles, Change Width and the video player. A dialog never opens larger than your screen, and it keeps the size you give it.</li>
        <li><b>Smoother Dragging:</b> The canvas stays sharp while you drag, even on scaled displays or with supersampling on. Move mode shows a closed hand while dragging a point. View mode can now pan with the left mouse button too. The Refresh button's tooltip now says what it does: reload layers and reset the view.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.111</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.111 :</p>
    <ul>
        <li><b>Styliser le côté d'extrémité:</b> Faites un clic droit sur un calque ayant une extrémité libre et choisissez Styliser le côté d'extrémité, juste sous Fermer le Nœud. Une boîte de dialogue vous laisse choisir la forme de l'extrémité du brin : Droite, Inclinée, Arrondie, Pointue, Entaillée ou Concave. Vous pouvez aussi régler l'inclinaison et la profondeur, allonger ou raccourcir l'extrémité, et ajouter une ligne latérale avec sa propre épaisseur et sa propre couleur. L'aperçu est en direct sur le canevas. L'ombre, la ligne latérale et les masques suivent tous la nouvelle forme. Les styles d'extrémité sont enregistrés avec votre projet et fonctionnent avec annuler et rétablir.</li>
        <li><b>La bonne taille sur les écrans mis à l'échelle:</b> Sur les écrans haute résolution avec une mise à l'échelle de l'affichage, les boutons et le texte paraissaient trop petits. L'application suit désormais l'échelle de votre écran. Les libellés de la barre d'outils ne sont plus coupés, et la barre d'outils passe sur deux lignes quand la fenêtre est étroite. Le panneau des calques peut être réduit plus qu'avant. Le logo OpenStrand Studio apparaît maintenant sur chaque fenêtre et dans la barre des tâches.</li>
        <li><b>Des boîtes de dialogue adaptées aux petits écrans:</b> La boîte de dialogue Paramètres peut désormais être réduite, de sorte que ses boutons Appliquer et OK restent toujours à l'écran. Il en va de même pour Modifier l'ombre, l'éditeur d'ombre de groupe, Créer Grille de Masque, Modifier les angles des brins, Changer largeur et le lecteur vidéo. Une boîte de dialogue ne s'ouvre jamais plus grande que votre écran, et elle garde la taille que vous lui donnez.</li>
        <li><b>Un glissement plus fluide:</b> Le canevas reste net pendant que vous faites glisser, même sur les écrans mis à l'échelle ou avec le suréchantillonnage activé. Le mode déplacement affiche une main fermée pendant le glissement d'un point. Le mode vue peut maintenant aussi se déplacer avec le bouton gauche de la souris. L'info-bulle du bouton Actualiser indique désormais ce qu'il fait : recharger les calques et réinitialiser la vue.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.111</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.111:</p>
    <ul>
        <li><b>Stilizza il lato finale:</b> Fai clic destro su un livello con un'estremità libera e scegli Stilizza il lato finale, subito sotto Chiudi il Nodo. Una finestra ti permette di scegliere come termina il trefolo: Dritta, Inclinata, Arrotondata, Appuntita, Intagliata o Concava. Puoi anche regolare inclinazione e profondità, allungare o accorciare l'estremità e aggiungere una linea laterale con spessore e colore propri. L'anteprima è dal vivo sulla tela. Ombra, linea laterale e maschere seguono tutte la nuova forma. Gli stili delle estremità vengono salvati con il progetto e funzionano con annulla e ripristina.</li>
        <li><b>Dimensione giusta sugli schermi ridimensionati:</b> Sugli schermi ad alta risoluzione con il ridimensionamento attivo, pulsanti e testo apparivano troppo piccoli. L'app ora segue la scala del tuo schermo. Le etichette della barra degli strumenti non vengono più tagliate, e la barra passa su due righe quando la finestra è stretta. Il pannello dei livelli può essere ristretto più di prima. Il logo di OpenStrand Studio appare ora su ogni finestra e nella barra delle applicazioni.</li>
        <li><b>Finestre adatte agli schermi piccoli:</b> La finestra Impostazioni ora può essere rimpicciolita, così i pulsanti Applica e OK restano sempre visibili. Lo stesso vale per Modifica ombra, l'editor dell'ombra di gruppo, Crea Griglia Maschera, Modifica Angoli Trefolo, Cambia larghezza e il lettore video. Una finestra non si apre mai più grande dello schermo e mantiene la dimensione che le dai.</li>
        <li><b>Trascinamento più fluido:</b> La tela resta nitida mentre trascini, anche su schermi ridimensionati o con il supersampling attivo. La modalità sposta mostra una mano chiusa mentre trascini un punto. La modalità vista ora può scorrere anche con il tasto sinistro del mouse. Il suggerimento del pulsante Aggiorna ora dice cosa fa: ricarica i livelli e reimposta la vista.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.111</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.111:</p>
    <ul>
        <li><b>Estilizar lado del extremo:</b> Haz clic derecho en una capa con un extremo libre y elige Estilizar lado del extremo, justo debajo de Cerrar el Nudo. Un cuadro de diálogo te permite elegir cómo termina el cordón: Recto, Inclinado, Redondeado, Puntiagudo, Con muesca o Cóncavo. También puedes ajustar la inclinación y la profundidad, alargar o recortar el extremo, y añadir una línea lateral con su propio grosor y color. La vista previa es en vivo sobre el lienzo. La sombra, la línea lateral y las máscaras siguen la nueva forma. Los estilos de extremo se guardan con tu proyecto y funcionan con deshacer y rehacer.</li>
        <li><b>Tamaño correcto en pantallas escaladas:</b> En pantallas de alta resolución con el escalado activado, los botones y el texto se veían demasiado pequeños. La aplicación ahora sigue la escala de tu pantalla. Las etiquetas de la barra de herramientas ya no se cortan, y la barra pasa a dos filas cuando la ventana es estrecha. El panel de capas se puede estrechar más que antes. El logotipo de OpenStrand Studio aparece ahora en cada ventana y en la barra de tareas.</li>
        <li><b>Diálogos que caben en pantallas pequeñas:</b> El diálogo Configuración ahora se puede hacer más pequeño, así sus botones Aplicar y OK siempre quedan en pantalla. Lo mismo ocurre con Editar sombra, el editor de sombra de grupo, Crear Cuadrícula de Máscara, Editar Ángulos del Cordón, Cambiar ancho y el reproductor de video. Un diálogo nunca se abre más grande que tu pantalla, y conserva el tamaño que le das.</li>
        <li><b>Arrastre más suave:</b> El lienzo se mantiene nítido mientras arrastras, incluso en pantallas escaladas o con el supermuestreo activado. El modo mover muestra una mano cerrada mientras arrastras un punto. El modo vista ahora también puede desplazarse con el botón izquierdo del ratón. La descripción del botón Actualizar ahora dice lo que hace: recargar las capas y restablecer la vista.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.111</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.111:</p>
    <ul>
        <li><b>Estilizar lado da extremidade:</b> Clique com o botão direito numa camada com uma extremidade livre e escolha Estilizar lado da extremidade, logo abaixo de Fechar o Nó. Uma janela permite escolher como a mecha termina: Reta, Inclinada, Arredondada, Pontiaguda, Entalhada ou Côncava. Também pode ajustar a inclinação e a profundidade, alongar ou encurtar a extremidade e adicionar uma linha lateral com espessura e cor próprias. A pré-visualização é ao vivo na tela. A sombra, a linha lateral e as máscaras seguem todas a nova forma. Os estilos de extremidade são salvos com o projeto e funcionam com desfazer e refazer.</li>
        <li><b>Tamanho certo em ecrãs com escala:</b> Em ecrãs de alta resolução com a escala de exibição ativada, os botões e o texto pareciam pequenos demais. A aplicação agora segue a escala do seu ecrã. Os rótulos da barra de ferramentas já não são cortados, e a barra passa para duas linhas quando a janela é estreita. O painel de camadas pode ser estreitado mais do que antes. O logótipo do OpenStrand Studio aparece agora em todas as janelas e na barra de tarefas.</li>
        <li><b>Janelas que cabem em ecrãs pequenos:</b> A janela Configurações agora pode ser reduzida, para que os botões Aplicar e OK fiquem sempre visíveis. O mesmo vale para Editar sombra, o editor de sombra de grupo, Criar Grade de Máscara, Editar Ângulos da Mecha, Mudar largura e o reprodutor de vídeo. Uma janela nunca abre maior do que o seu ecrã e mantém o tamanho que lhe der.</li>
        <li><b>Arrasto mais suave:</b> A tela permanece nítida enquanto arrasta, mesmo em ecrãs com escala ou com a superamostragem ativada. O modo mover mostra uma mão fechada enquanto arrasta um ponto. O modo de visualização agora também pode deslocar-se com o botão esquerdo do rato. A dica do botão Atualizar agora diz o que ele faz: recarregar as camadas e redefinir a vista.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.111</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.111:</p>
    <ul>
        <li><b>&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9; &#x05D5;&#x05D1;&#x05D7;&#x05E8;&#x05D5; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05D0;&#x05D9;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05D9;&#x05DD;: &#x05D9;&#x05E9;&#x05E8;, &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E2;, &#x05DE;&#x05E2;&#x05D5;&#x05D2;&#x05DC;, &#x05DE;&#x05D7;&#x05D5;&#x05D3;&#x05D3;, &#x05D7;&#x05E8;&#x05D5;&#x05E5; &#x05D0;&#x05D5; &#x05E7;&#x05E2;&#x05D5;&#x05E8;. &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05D2;&#x05DD; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05DF; &#x05D0;&#x05EA; &#x05D4;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D5;&#x05D4;&#x05E2;&#x05D5;&#x05DE;&#x05E7;, &#x05DC;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05DA; &#x05D0;&#x05D5; &#x05DC;&#x05E7;&#x05E6;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05D5;&#x05DC;&#x05D4;&#x05D5;&#x05E1;&#x05D9;&#x05E3; &#x05E7;&#x05D5; &#x05E6;&#x05D3; &#x05E2;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05D5;&#x05E6;&#x05D1;&#x05E2; &#x05DE;&#x05E9;&#x05DC;&#x05D5;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05D7;&#x05D9;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;. &#x05D4;&#x05E6;&#x05DC;, &#x05E7;&#x05D5; &#x05D4;&#x05E6;&#x05D3; &#x05D5;&#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D4;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D4;&#x05D7;&#x05D3;&#x05E9;&#x05D4;. &#x05E1;&#x05D2;&#x05E0;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E2;&#x05D5;&#x05D1;&#x05D3;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;.</li>
        <li><b>&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E0;&#x05DB;&#x05D5;&#x05DF; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4;:</b> &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05D1;&#x05E8;&#x05D6;&#x05D5;&#x05DC;&#x05D5;&#x05E6;&#x05D9;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;, &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D4;&#x05D8;&#x05E7;&#x05E1;&#x05D8; &#x05E0;&#x05E8;&#x05D0;&#x05D5; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D9;. &#x05D4;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05E7;&#x05E0;&#x05D4; &#x05D4;&#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;. &#x05EA;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05E0;&#x05D7;&#x05EA;&#x05DB;&#x05D5;&#x05EA;, &#x05D5;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05E8; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05E9;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05DB;&#x05E9;&#x05D4;&#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05E6;&#x05E8;. &#x05D0;&#x05EA; &#x05DC;&#x05D5;&#x05D7; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05D5;&#x05E8; &#x05E6;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D1;&#x05E2;&#x05D1;&#x05E8;. &#x05D4;&#x05DC;&#x05D5;&#x05D2;&#x05D5; &#x05E9;&#x05DC; OpenStrand Studio &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D5;&#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05EA; &#x05D4;&#x05DE;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D7;&#x05DC;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DE;&#x05D9;&#x05DD; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05D0;&#x05EA; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05E7;&#x05D8;&#x05D9;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D7;&#x05DC; &#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA;. &#x05DB;&#x05DA; &#x05D2;&#x05DD; &#x05E2;&#x05E8;&#x05D9;&#x05DB;&#x05EA; &#x05E6;&#x05DC;, &#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC; &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;, &#x05E6;&#x05D5;&#x05E8; &#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05E8;&#x05D5;&#x05DA; &#x05D6;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05E9;&#x05E0;&#x05D4; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D5;&#x05E0;&#x05D2;&#x05DF; &#x05D4;&#x05D5;&#x05D5;&#x05D9;&#x05D3;&#x05D0;&#x05D5;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05DC;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05E0;&#x05E4;&#x05EA;&#x05D7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;, &#x05D5;&#x05D4;&#x05D5;&#x05D0; &#x05E9;&#x05D5;&#x05DE;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E9;&#x05E0;&#x05EA;&#x05EA;&#x05DD; &#x05DC;&#x05D5;.</li>
        <li><b>&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05DC;&#x05E7;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D7;&#x05D3; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4;, &#x05D2;&#x05DD; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05D0;&#x05D5; &#x05E2;&#x05DD; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05EA;-&#x05D9;&#x05EA;&#x05E8; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;&#x05EA;. &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05D9;&#x05D3; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D4; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D4;. &#x05DE;&#x05E6;&#x05D1; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D2;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E9;&#x05DE;&#x05D0;&#x05DC;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D4;&#x05D8;&#x05D9;&#x05E4; &#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E8;&#x05E2;&#x05E0;&#x05D5;&#x05DF; &#x05D0;&#x05D5;&#x05DE;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05D4; &#x05D4;&#x05D5;&#x05D0; &#x05E2;&#x05D5;&#x05E9;&#x05D4;: &#x05D8;&#x05D5;&#x05E2;&#x05DF; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D5;&#x05DE;&#x05D0;&#x05E4;&#x05E1; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;.</li>
    </ul>
    </div>
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
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.111</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.111:</p>
    <ul>
        <li><b>Stilizza il lato finale:</b> Fai clic destro su un livello con un'estremità libera e scegli Stilizza il lato finale, subito sotto Chiudi il Nodo. Una finestra ti permette di scegliere come termina il trefolo: Dritta, Inclinata, Arrotondata, Appuntita, Intagliata o Concava. Puoi anche regolare inclinazione e profondità, allungare o accorciare l'estremità e aggiungere una linea laterale con spessore e colore propri. L'anteprima è dal vivo sulla tela. Ombra, linea laterale e maschere seguono tutte la nuova forma. Gli stili delle estremità vengono salvati con il progetto e funzionano con annulla e ripristina.</li>
        <li><b>Dimensione giusta sugli schermi ridimensionati:</b> Sugli schermi ad alta risoluzione con il ridimensionamento attivo, pulsanti e testo apparivano troppo piccoli. L'app ora segue la scala del tuo schermo. Le etichette della barra degli strumenti non vengono più tagliate, e la barra passa su due righe quando la finestra è stretta. Il pannello dei livelli può essere ristretto più di prima. Il logo di OpenStrand Studio appare ora su ogni finestra e nella barra delle applicazioni.</li>
        <li><b>Finestre adatte agli schermi piccoli:</b> La finestra Impostazioni ora può essere rimpicciolita, così i pulsanti Applica e OK restano sempre visibili. Lo stesso vale per Modifica ombra, l'editor dell'ombra di gruppo, Crea Griglia Maschera, Modifica Angoli Trefolo, Cambia larghezza e il lettore video. Una finestra non si apre mai più grande dello schermo e mantiene la dimensione che le dai.</li>
        <li><b>Trascinamento più fluido:</b> La tela resta nitida mentre trascini, anche su schermi ridimensionati o con il supersampling attivo. La modalità sposta mostra una mano chiusa mentre trascini un punto. La modalità vista ora può scorrere anche con il tasto sinistro del mouse. Il suggerimento del pulsante Aggiorna ora dice cosa fa: ricarica i livelli e reimposta la vista.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.111</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.111:</p>
    <ul>
        <li><b>Stylize End Side:</b> Right-click a layer with a free end and pick Stylize End Side, just under Close the Knot. A dialog lets you choose how the strand ends: Straight, Angled, Rounded, Pointed, Notched or Concave. You can also set the tilt and depth, extend or trim the end, and add a side line with its own thickness and color. The preview is live on the canvas. The shadow, side line and masks all follow the new shape. End styles are saved with your project and work with undo and redo.</li>
        <li><b>Right Size on Scaled Screens:</b> On high-resolution screens with display scaling turned on, the buttons and text used to look too small. The app now follows your display scale. Toolbar labels no longer get cut off, and the toolbar moves onto two rows when the window is narrow. The layer panel can be dragged narrower than before. The OpenStrand Studio logo now appears on every window and in the taskbar.</li>
        <li><b>Dialogs Fit Small Screens:</b> The Settings dialog can now be made smaller, so its Apply and OK buttons always stay on screen. The same goes for Edit Shadow, the group shadow editor, Create Mask Grid, Edit Strand Angles, Change Width and the video player. A dialog never opens larger than your screen, and it keeps the size you give it.</li>
        <li><b>Smoother Dragging:</b> The canvas stays sharp while you drag, even on scaled displays or with supersampling on. Move mode shows a closed hand while dragging a point. View mode can now pan with the left mouse button too. The Refresh button's tooltip now says what it does: reload layers and reset the view.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.111</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.111:</p>
    <ul>
        <li><b>Endseite gestalten:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene mit einem freien Ende und wählen Sie Endseite gestalten, direkt unter Knoten schließen. In einem Dialog wählen Sie, wie der Strang endet: Gerade, Schräg, Abgerundet, Spitz, Eingekerbt oder Konkav. Sie können außerdem Neigung und Tiefe einstellen, das Ende verlängern oder kürzen und eine Seitenlinie mit eigener Dicke und Farbe hinzufügen. Die Vorschau erscheint live auf der Zeichenfläche. Schatten, Seitenlinie und Masken folgen alle der neuen Form. Endstile werden mit dem Projekt gespeichert und funktionieren mit Rückgängig und Wiederherstellen.</li>
        <li><b>Richtige Größe auf skalierten Bildschirmen:</b> Auf hochauflösenden Bildschirmen mit aktivierter Anzeigeskalierung wirkten Schaltflächen und Text zu klein. Die App folgt jetzt Ihrer Anzeigeskalierung. Beschriftungen in der Werkzeugleiste werden nicht mehr abgeschnitten, und die Werkzeugleiste wechselt bei schmalen Fenstern auf zwei Zeilen. Das Ebenenpanel lässt sich schmaler ziehen als zuvor. Das OpenStrand Studio Logo erscheint jetzt in jedem Fenster und in der Taskleiste.</li>
        <li><b>Dialoge passen auf kleine Bildschirme:</b> Der Dialog Einstellungen kann jetzt verkleinert werden, sodass seine Schaltflächen Übernehmen und OK immer sichtbar bleiben. Dasselbe gilt für Schatten bearbeiten, den Gruppenschatten-Editor, Maskenraster Erstellen, Strangwinkel bearbeiten, Breite ändern und den Videoplayer. Ein Dialog öffnet sich nie größer als Ihr Bildschirm und behält die Größe, die Sie ihm geben.</li>
        <li><b>Flüssigeres Ziehen:</b> Die Zeichenfläche bleibt beim Ziehen scharf, auch auf skalierten Bildschirmen oder mit eingeschaltetem Supersampling. Der Verschiebemodus zeigt beim Ziehen eines Punktes eine geschlossene Hand. Der Ansichtsmodus kann jetzt auch mit der linken Maustaste verschoben werden. Der Tooltip der Schaltfläche Aktualisieren sagt jetzt, was sie tut: Ebenen neu laden und Ansicht zurücksetzen.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.111</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.111 :</p>
    <ul>
        <li><b>Styliser le côté d'extrémité:</b> Faites un clic droit sur un calque ayant une extrémité libre et choisissez Styliser le côté d'extrémité, juste sous Fermer le Nœud. Une boîte de dialogue vous laisse choisir la forme de l'extrémité du brin : Droite, Inclinée, Arrondie, Pointue, Entaillée ou Concave. Vous pouvez aussi régler l'inclinaison et la profondeur, allonger ou raccourcir l'extrémité, et ajouter une ligne latérale avec sa propre épaisseur et sa propre couleur. L'aperçu est en direct sur le canevas. L'ombre, la ligne latérale et les masques suivent tous la nouvelle forme. Les styles d'extrémité sont enregistrés avec votre projet et fonctionnent avec annuler et rétablir.</li>
        <li><b>La bonne taille sur les écrans mis à l'échelle:</b> Sur les écrans haute résolution avec une mise à l'échelle de l'affichage, les boutons et le texte paraissaient trop petits. L'application suit désormais l'échelle de votre écran. Les libellés de la barre d'outils ne sont plus coupés, et la barre d'outils passe sur deux lignes quand la fenêtre est étroite. Le panneau des calques peut être réduit plus qu'avant. Le logo OpenStrand Studio apparaît maintenant sur chaque fenêtre et dans la barre des tâches.</li>
        <li><b>Des boîtes de dialogue adaptées aux petits écrans:</b> La boîte de dialogue Paramètres peut désormais être réduite, de sorte que ses boutons Appliquer et OK restent toujours à l'écran. Il en va de même pour Modifier l'ombre, l'éditeur d'ombre de groupe, Créer Grille de Masque, Modifier les angles des brins, Changer largeur et le lecteur vidéo. Une boîte de dialogue ne s'ouvre jamais plus grande que votre écran, et elle garde la taille que vous lui donnez.</li>
        <li><b>Un glissement plus fluide:</b> Le canevas reste net pendant que vous faites glisser, même sur les écrans mis à l'échelle ou avec le suréchantillonnage activé. Le mode déplacement affiche une main fermée pendant le glissement d'un point. Le mode vue peut maintenant aussi se déplacer avec le bouton gauche de la souris. L'info-bulle du bouton Actualiser indique désormais ce qu'il fait : recharger les calques et réinitialiser la vue.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.111</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.111:</p>
    <ul>
        <li><b>Estilizar lado del extremo:</b> Haz clic derecho en una capa con un extremo libre y elige Estilizar lado del extremo, justo debajo de Cerrar el Nudo. Un cuadro de diálogo te permite elegir cómo termina el cordón: Recto, Inclinado, Redondeado, Puntiagudo, Con muesca o Cóncavo. También puedes ajustar la inclinación y la profundidad, alargar o recortar el extremo, y añadir una línea lateral con su propio grosor y color. La vista previa es en vivo sobre el lienzo. La sombra, la línea lateral y las máscaras siguen la nueva forma. Los estilos de extremo se guardan con tu proyecto y funcionan con deshacer y rehacer.</li>
        <li><b>Tamaño correcto en pantallas escaladas:</b> En pantallas de alta resolución con el escalado activado, los botones y el texto se veían demasiado pequeños. La aplicación ahora sigue la escala de tu pantalla. Las etiquetas de la barra de herramientas ya no se cortan, y la barra pasa a dos filas cuando la ventana es estrecha. El panel de capas se puede estrechar más que antes. El logotipo de OpenStrand Studio aparece ahora en cada ventana y en la barra de tareas.</li>
        <li><b>Diálogos que caben en pantallas pequeñas:</b> El diálogo Configuración ahora se puede hacer más pequeño, así sus botones Aplicar y OK siempre quedan en pantalla. Lo mismo ocurre con Editar sombra, el editor de sombra de grupo, Crear Cuadrícula de Máscara, Editar Ángulos del Cordón, Cambiar ancho y el reproductor de video. Un diálogo nunca se abre más grande que tu pantalla, y conserva el tamaño que le das.</li>
        <li><b>Arrastre más suave:</b> El lienzo se mantiene nítido mientras arrastras, incluso en pantallas escaladas o con el supermuestreo activado. El modo mover muestra una mano cerrada mientras arrastras un punto. El modo vista ahora también puede desplazarse con el botón izquierdo del ratón. La descripción del botón Actualizar ahora dice lo que hace: recargar las capas y restablecer la vista.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.111</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.111:</p>
    <ul>
        <li><b>Estilizar lado da extremidade:</b> Clique com o botão direito numa camada com uma extremidade livre e escolha Estilizar lado da extremidade, logo abaixo de Fechar o Nó. Uma janela permite escolher como a mecha termina: Reta, Inclinada, Arredondada, Pontiaguda, Entalhada ou Côncava. Também pode ajustar a inclinação e a profundidade, alongar ou encurtar a extremidade e adicionar uma linha lateral com espessura e cor próprias. A pré-visualização é ao vivo na tela. A sombra, a linha lateral e as máscaras seguem todas a nova forma. Os estilos de extremidade são salvos com o projeto e funcionam com desfazer e refazer.</li>
        <li><b>Tamanho certo em ecrãs com escala:</b> Em ecrãs de alta resolução com a escala de exibição ativada, os botões e o texto pareciam pequenos demais. A aplicação agora segue a escala do seu ecrã. Os rótulos da barra de ferramentas já não são cortados, e a barra passa para duas linhas quando a janela é estreita. O painel de camadas pode ser estreitado mais do que antes. O logótipo do OpenStrand Studio aparece agora em todas as janelas e na barra de tarefas.</li>
        <li><b>Janelas que cabem em ecrãs pequenos:</b> A janela Configurações agora pode ser reduzida, para que os botões Aplicar e OK fiquem sempre visíveis. O mesmo vale para Editar sombra, o editor de sombra de grupo, Criar Grade de Máscara, Editar Ângulos da Mecha, Mudar largura e o reprodutor de vídeo. Uma janela nunca abre maior do que o seu ecrã e mantém o tamanho que lhe der.</li>
        <li><b>Arrasto mais suave:</b> A tela permanece nítida enquanto arrasta, mesmo em ecrãs com escala ou com a superamostragem ativada. O modo mover mostra uma mão fechada enquanto arrasta um ponto. O modo de visualização agora também pode deslocar-se com o botão esquerdo do rato. A dica do botão Atualizar agora diz o que ele faz: recarregar as camadas e redefinir a vista.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.111</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.111:</p>
    <ul>
        <li><b>&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9; &#x05D5;&#x05D1;&#x05D7;&#x05E8;&#x05D5; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05D0;&#x05D9;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05D9;&#x05DD;: &#x05D9;&#x05E9;&#x05E8;, &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E2;, &#x05DE;&#x05E2;&#x05D5;&#x05D2;&#x05DC;, &#x05DE;&#x05D7;&#x05D5;&#x05D3;&#x05D3;, &#x05D7;&#x05E8;&#x05D5;&#x05E5; &#x05D0;&#x05D5; &#x05E7;&#x05E2;&#x05D5;&#x05E8;. &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05D2;&#x05DD; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05DF; &#x05D0;&#x05EA; &#x05D4;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D5;&#x05D4;&#x05E2;&#x05D5;&#x05DE;&#x05E7;, &#x05DC;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05DA; &#x05D0;&#x05D5; &#x05DC;&#x05E7;&#x05E6;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05D5;&#x05DC;&#x05D4;&#x05D5;&#x05E1;&#x05D9;&#x05E3; &#x05E7;&#x05D5; &#x05E6;&#x05D3; &#x05E2;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05D5;&#x05E6;&#x05D1;&#x05E2; &#x05DE;&#x05E9;&#x05DC;&#x05D5;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05D7;&#x05D9;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;. &#x05D4;&#x05E6;&#x05DC;, &#x05E7;&#x05D5; &#x05D4;&#x05E6;&#x05D3; &#x05D5;&#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D4;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D4;&#x05D7;&#x05D3;&#x05E9;&#x05D4;. &#x05E1;&#x05D2;&#x05E0;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E2;&#x05D5;&#x05D1;&#x05D3;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;.</li>
        <li><b>&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E0;&#x05DB;&#x05D5;&#x05DF; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4;:</b> &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05D1;&#x05E8;&#x05D6;&#x05D5;&#x05DC;&#x05D5;&#x05E6;&#x05D9;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;, &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D4;&#x05D8;&#x05E7;&#x05E1;&#x05D8; &#x05E0;&#x05E8;&#x05D0;&#x05D5; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D9;. &#x05D4;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05E7;&#x05E0;&#x05D4; &#x05D4;&#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;. &#x05EA;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05E0;&#x05D7;&#x05EA;&#x05DB;&#x05D5;&#x05EA;, &#x05D5;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05E8; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05E9;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05DB;&#x05E9;&#x05D4;&#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05E6;&#x05E8;. &#x05D0;&#x05EA; &#x05DC;&#x05D5;&#x05D7; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05D5;&#x05E8; &#x05E6;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D1;&#x05E2;&#x05D1;&#x05E8;. &#x05D4;&#x05DC;&#x05D5;&#x05D2;&#x05D5; &#x05E9;&#x05DC; OpenStrand Studio &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D5;&#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05EA; &#x05D4;&#x05DE;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D7;&#x05DC;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DE;&#x05D9;&#x05DD; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05D0;&#x05EA; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05E7;&#x05D8;&#x05D9;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D7;&#x05DC; &#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA;. &#x05DB;&#x05DA; &#x05D2;&#x05DD; &#x05E2;&#x05E8;&#x05D9;&#x05DB;&#x05EA; &#x05E6;&#x05DC;, &#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC; &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;, &#x05E6;&#x05D5;&#x05E8; &#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05E8;&#x05D5;&#x05DA; &#x05D6;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05E9;&#x05E0;&#x05D4; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D5;&#x05E0;&#x05D2;&#x05DF; &#x05D4;&#x05D5;&#x05D5;&#x05D9;&#x05D3;&#x05D0;&#x05D5;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05DC;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05E0;&#x05E4;&#x05EA;&#x05D7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;, &#x05D5;&#x05D4;&#x05D5;&#x05D0; &#x05E9;&#x05D5;&#x05DE;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E9;&#x05E0;&#x05EA;&#x05EA;&#x05DD; &#x05DC;&#x05D5;.</li>
        <li><b>&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05DC;&#x05E7;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D7;&#x05D3; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4;, &#x05D2;&#x05DD; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05D0;&#x05D5; &#x05E2;&#x05DD; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05EA;-&#x05D9;&#x05EA;&#x05E8; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;&#x05EA;. &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05D9;&#x05D3; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D4; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D4;. &#x05DE;&#x05E6;&#x05D1; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D2;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E9;&#x05DE;&#x05D0;&#x05DC;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D4;&#x05D8;&#x05D9;&#x05E4; &#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E8;&#x05E2;&#x05E0;&#x05D5;&#x05DF; &#x05D0;&#x05D5;&#x05DE;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05D4; &#x05D4;&#x05D5;&#x05D0; &#x05E2;&#x05D5;&#x05E9;&#x05D4;: &#x05D8;&#x05D5;&#x05E2;&#x05DF; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D5;&#x05DE;&#x05D0;&#x05E4;&#x05E1; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;.</li>
    </ul>
    </div>
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
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.111</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.111:</p>
    <ul>
        <li><b>Estilizar lado del extremo:</b> Haz clic derecho en una capa con un extremo libre y elige Estilizar lado del extremo, justo debajo de Cerrar el Nudo. Un cuadro de diálogo te permite elegir cómo termina el cordón: Recto, Inclinado, Redondeado, Puntiagudo, Con muesca o Cóncavo. También puedes ajustar la inclinación y la profundidad, alargar o recortar el extremo, y añadir una línea lateral con su propio grosor y color. La vista previa es en vivo sobre el lienzo. La sombra, la línea lateral y las máscaras siguen la nueva forma. Los estilos de extremo se guardan con tu proyecto y funcionan con deshacer y rehacer.</li>
        <li><b>Tamaño correcto en pantallas escaladas:</b> En pantallas de alta resolución con el escalado activado, los botones y el texto se veían demasiado pequeños. La aplicación ahora sigue la escala de tu pantalla. Las etiquetas de la barra de herramientas ya no se cortan, y la barra pasa a dos filas cuando la ventana es estrecha. El panel de capas se puede estrechar más que antes. El logotipo de OpenStrand Studio aparece ahora en cada ventana y en la barra de tareas.</li>
        <li><b>Diálogos que caben en pantallas pequeñas:</b> El diálogo Configuración ahora se puede hacer más pequeño, así sus botones Aplicar y OK siempre quedan en pantalla. Lo mismo ocurre con Editar sombra, el editor de sombra de grupo, Crear Cuadrícula de Máscara, Editar Ángulos del Cordón, Cambiar ancho y el reproductor de video. Un diálogo nunca se abre más grande que tu pantalla, y conserva el tamaño que le das.</li>
        <li><b>Arrastre más suave:</b> El lienzo se mantiene nítido mientras arrastras, incluso en pantallas escaladas o con el supermuestreo activado. El modo mover muestra una mano cerrada mientras arrastras un punto. El modo vista ahora también puede desplazarse con el botón izquierdo del ratón. La descripción del botón Actualizar ahora dice lo que hace: recargar las capas y restablecer la vista.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.111</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.111:</p>
    <ul>
        <li><b>Stylize End Side:</b> Right-click a layer with a free end and pick Stylize End Side, just under Close the Knot. A dialog lets you choose how the strand ends: Straight, Angled, Rounded, Pointed, Notched or Concave. You can also set the tilt and depth, extend or trim the end, and add a side line with its own thickness and color. The preview is live on the canvas. The shadow, side line and masks all follow the new shape. End styles are saved with your project and work with undo and redo.</li>
        <li><b>Right Size on Scaled Screens:</b> On high-resolution screens with display scaling turned on, the buttons and text used to look too small. The app now follows your display scale. Toolbar labels no longer get cut off, and the toolbar moves onto two rows when the window is narrow. The layer panel can be dragged narrower than before. The OpenStrand Studio logo now appears on every window and in the taskbar.</li>
        <li><b>Dialogs Fit Small Screens:</b> The Settings dialog can now be made smaller, so its Apply and OK buttons always stay on screen. The same goes for Edit Shadow, the group shadow editor, Create Mask Grid, Edit Strand Angles, Change Width and the video player. A dialog never opens larger than your screen, and it keeps the size you give it.</li>
        <li><b>Smoother Dragging:</b> The canvas stays sharp while you drag, even on scaled displays or with supersampling on. Move mode shows a closed hand while dragging a point. View mode can now pan with the left mouse button too. The Refresh button's tooltip now says what it does: reload layers and reset the view.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.111</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.111 :</p>
    <ul>
        <li><b>Styliser le côté d'extrémité:</b> Faites un clic droit sur un calque ayant une extrémité libre et choisissez Styliser le côté d'extrémité, juste sous Fermer le Nœud. Une boîte de dialogue vous laisse choisir la forme de l'extrémité du brin : Droite, Inclinée, Arrondie, Pointue, Entaillée ou Concave. Vous pouvez aussi régler l'inclinaison et la profondeur, allonger ou raccourcir l'extrémité, et ajouter une ligne latérale avec sa propre épaisseur et sa propre couleur. L'aperçu est en direct sur le canevas. L'ombre, la ligne latérale et les masques suivent tous la nouvelle forme. Les styles d'extrémité sont enregistrés avec votre projet et fonctionnent avec annuler et rétablir.</li>
        <li><b>La bonne taille sur les écrans mis à l'échelle:</b> Sur les écrans haute résolution avec une mise à l'échelle de l'affichage, les boutons et le texte paraissaient trop petits. L'application suit désormais l'échelle de votre écran. Les libellés de la barre d'outils ne sont plus coupés, et la barre d'outils passe sur deux lignes quand la fenêtre est étroite. Le panneau des calques peut être réduit plus qu'avant. Le logo OpenStrand Studio apparaît maintenant sur chaque fenêtre et dans la barre des tâches.</li>
        <li><b>Des boîtes de dialogue adaptées aux petits écrans:</b> La boîte de dialogue Paramètres peut désormais être réduite, de sorte que ses boutons Appliquer et OK restent toujours à l'écran. Il en va de même pour Modifier l'ombre, l'éditeur d'ombre de groupe, Créer Grille de Masque, Modifier les angles des brins, Changer largeur et le lecteur vidéo. Une boîte de dialogue ne s'ouvre jamais plus grande que votre écran, et elle garde la taille que vous lui donnez.</li>
        <li><b>Un glissement plus fluide:</b> Le canevas reste net pendant que vous faites glisser, même sur les écrans mis à l'échelle ou avec le suréchantillonnage activé. Le mode déplacement affiche une main fermée pendant le glissement d'un point. Le mode vue peut maintenant aussi se déplacer avec le bouton gauche de la souris. L'info-bulle du bouton Actualiser indique désormais ce qu'il fait : recharger les calques et réinitialiser la vue.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.111</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.111:</p>
    <ul>
        <li><b>Endseite gestalten:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene mit einem freien Ende und wählen Sie Endseite gestalten, direkt unter Knoten schließen. In einem Dialog wählen Sie, wie der Strang endet: Gerade, Schräg, Abgerundet, Spitz, Eingekerbt oder Konkav. Sie können außerdem Neigung und Tiefe einstellen, das Ende verlängern oder kürzen und eine Seitenlinie mit eigener Dicke und Farbe hinzufügen. Die Vorschau erscheint live auf der Zeichenfläche. Schatten, Seitenlinie und Masken folgen alle der neuen Form. Endstile werden mit dem Projekt gespeichert und funktionieren mit Rückgängig und Wiederherstellen.</li>
        <li><b>Richtige Größe auf skalierten Bildschirmen:</b> Auf hochauflösenden Bildschirmen mit aktivierter Anzeigeskalierung wirkten Schaltflächen und Text zu klein. Die App folgt jetzt Ihrer Anzeigeskalierung. Beschriftungen in der Werkzeugleiste werden nicht mehr abgeschnitten, und die Werkzeugleiste wechselt bei schmalen Fenstern auf zwei Zeilen. Das Ebenenpanel lässt sich schmaler ziehen als zuvor. Das OpenStrand Studio Logo erscheint jetzt in jedem Fenster und in der Taskleiste.</li>
        <li><b>Dialoge passen auf kleine Bildschirme:</b> Der Dialog Einstellungen kann jetzt verkleinert werden, sodass seine Schaltflächen Übernehmen und OK immer sichtbar bleiben. Dasselbe gilt für Schatten bearbeiten, den Gruppenschatten-Editor, Maskenraster Erstellen, Strangwinkel bearbeiten, Breite ändern und den Videoplayer. Ein Dialog öffnet sich nie größer als Ihr Bildschirm und behält die Größe, die Sie ihm geben.</li>
        <li><b>Flüssigeres Ziehen:</b> Die Zeichenfläche bleibt beim Ziehen scharf, auch auf skalierten Bildschirmen oder mit eingeschaltetem Supersampling. Der Verschiebemodus zeigt beim Ziehen eines Punktes eine geschlossene Hand. Der Ansichtsmodus kann jetzt auch mit der linken Maustaste verschoben werden. Der Tooltip der Schaltfläche Aktualisieren sagt jetzt, was sie tut: Ebenen neu laden und Ansicht zurücksetzen.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.111</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.111:</p>
    <ul>
        <li><b>Stilizza il lato finale:</b> Fai clic destro su un livello con un'estremità libera e scegli Stilizza il lato finale, subito sotto Chiudi il Nodo. Una finestra ti permette di scegliere come termina il trefolo: Dritta, Inclinata, Arrotondata, Appuntita, Intagliata o Concava. Puoi anche regolare inclinazione e profondità, allungare o accorciare l'estremità e aggiungere una linea laterale con spessore e colore propri. L'anteprima è dal vivo sulla tela. Ombra, linea laterale e maschere seguono tutte la nuova forma. Gli stili delle estremità vengono salvati con il progetto e funzionano con annulla e ripristina.</li>
        <li><b>Dimensione giusta sugli schermi ridimensionati:</b> Sugli schermi ad alta risoluzione con il ridimensionamento attivo, pulsanti e testo apparivano troppo piccoli. L'app ora segue la scala del tuo schermo. Le etichette della barra degli strumenti non vengono più tagliate, e la barra passa su due righe quando la finestra è stretta. Il pannello dei livelli può essere ristretto più di prima. Il logo di OpenStrand Studio appare ora su ogni finestra e nella barra delle applicazioni.</li>
        <li><b>Finestre adatte agli schermi piccoli:</b> La finestra Impostazioni ora può essere rimpicciolita, così i pulsanti Applica e OK restano sempre visibili. Lo stesso vale per Modifica ombra, l'editor dell'ombra di gruppo, Crea Griglia Maschera, Modifica Angoli Trefolo, Cambia larghezza e il lettore video. Una finestra non si apre mai più grande dello schermo e mantiene la dimensione che le dai.</li>
        <li><b>Trascinamento più fluido:</b> La tela resta nitida mentre trascini, anche su schermi ridimensionati o con il supersampling attivo. La modalità sposta mostra una mano chiusa mentre trascini un punto. La modalità vista ora può scorrere anche con il tasto sinistro del mouse. Il suggerimento del pulsante Aggiorna ora dice cosa fa: ricarica i livelli e reimposta la vista.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.111</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.111:</p>
    <ul>
        <li><b>Estilizar lado da extremidade:</b> Clique com o botão direito numa camada com uma extremidade livre e escolha Estilizar lado da extremidade, logo abaixo de Fechar o Nó. Uma janela permite escolher como a mecha termina: Reta, Inclinada, Arredondada, Pontiaguda, Entalhada ou Côncava. Também pode ajustar a inclinação e a profundidade, alongar ou encurtar a extremidade e adicionar uma linha lateral com espessura e cor próprias. A pré-visualização é ao vivo na tela. A sombra, a linha lateral e as máscaras seguem todas a nova forma. Os estilos de extremidade são salvos com o projeto e funcionam com desfazer e refazer.</li>
        <li><b>Tamanho certo em ecrãs com escala:</b> Em ecrãs de alta resolução com a escala de exibição ativada, os botões e o texto pareciam pequenos demais. A aplicação agora segue a escala do seu ecrã. Os rótulos da barra de ferramentas já não são cortados, e a barra passa para duas linhas quando a janela é estreita. O painel de camadas pode ser estreitado mais do que antes. O logótipo do OpenStrand Studio aparece agora em todas as janelas e na barra de tarefas.</li>
        <li><b>Janelas que cabem em ecrãs pequenos:</b> A janela Configurações agora pode ser reduzida, para que os botões Aplicar e OK fiquem sempre visíveis. O mesmo vale para Editar sombra, o editor de sombra de grupo, Criar Grade de Máscara, Editar Ângulos da Mecha, Mudar largura e o reprodutor de vídeo. Uma janela nunca abre maior do que o seu ecrã e mantém o tamanho que lhe der.</li>
        <li><b>Arrasto mais suave:</b> A tela permanece nítida enquanto arrasta, mesmo em ecrãs com escala ou com a superamostragem ativada. O modo mover mostra uma mão fechada enquanto arrasta um ponto. O modo de visualização agora também pode deslocar-se com o botão esquerdo do rato. A dica do botão Atualizar agora diz o que ele faz: recarregar as camadas e redefinir a vista.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.111</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.111:</p>
    <ul>
        <li><b>&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9; &#x05D5;&#x05D1;&#x05D7;&#x05E8;&#x05D5; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05D0;&#x05D9;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05D9;&#x05DD;: &#x05D9;&#x05E9;&#x05E8;, &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E2;, &#x05DE;&#x05E2;&#x05D5;&#x05D2;&#x05DC;, &#x05DE;&#x05D7;&#x05D5;&#x05D3;&#x05D3;, &#x05D7;&#x05E8;&#x05D5;&#x05E5; &#x05D0;&#x05D5; &#x05E7;&#x05E2;&#x05D5;&#x05E8;. &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05D2;&#x05DD; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05DF; &#x05D0;&#x05EA; &#x05D4;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D5;&#x05D4;&#x05E2;&#x05D5;&#x05DE;&#x05E7;, &#x05DC;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05DA; &#x05D0;&#x05D5; &#x05DC;&#x05E7;&#x05E6;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05D5;&#x05DC;&#x05D4;&#x05D5;&#x05E1;&#x05D9;&#x05E3; &#x05E7;&#x05D5; &#x05E6;&#x05D3; &#x05E2;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05D5;&#x05E6;&#x05D1;&#x05E2; &#x05DE;&#x05E9;&#x05DC;&#x05D5;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05D7;&#x05D9;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;. &#x05D4;&#x05E6;&#x05DC;, &#x05E7;&#x05D5; &#x05D4;&#x05E6;&#x05D3; &#x05D5;&#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D4;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D4;&#x05D7;&#x05D3;&#x05E9;&#x05D4;. &#x05E1;&#x05D2;&#x05E0;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E2;&#x05D5;&#x05D1;&#x05D3;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;.</li>
        <li><b>&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E0;&#x05DB;&#x05D5;&#x05DF; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4;:</b> &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05D1;&#x05E8;&#x05D6;&#x05D5;&#x05DC;&#x05D5;&#x05E6;&#x05D9;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;, &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D4;&#x05D8;&#x05E7;&#x05E1;&#x05D8; &#x05E0;&#x05E8;&#x05D0;&#x05D5; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D9;. &#x05D4;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05E7;&#x05E0;&#x05D4; &#x05D4;&#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;. &#x05EA;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05E0;&#x05D7;&#x05EA;&#x05DB;&#x05D5;&#x05EA;, &#x05D5;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05E8; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05E9;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05DB;&#x05E9;&#x05D4;&#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05E6;&#x05E8;. &#x05D0;&#x05EA; &#x05DC;&#x05D5;&#x05D7; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05D5;&#x05E8; &#x05E6;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D1;&#x05E2;&#x05D1;&#x05E8;. &#x05D4;&#x05DC;&#x05D5;&#x05D2;&#x05D5; &#x05E9;&#x05DC; OpenStrand Studio &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D5;&#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05EA; &#x05D4;&#x05DE;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D7;&#x05DC;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DE;&#x05D9;&#x05DD; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05D0;&#x05EA; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05E7;&#x05D8;&#x05D9;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D7;&#x05DC; &#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA;. &#x05DB;&#x05DA; &#x05D2;&#x05DD; &#x05E2;&#x05E8;&#x05D9;&#x05DB;&#x05EA; &#x05E6;&#x05DC;, &#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC; &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;, &#x05E6;&#x05D5;&#x05E8; &#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05E8;&#x05D5;&#x05DA; &#x05D6;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05E9;&#x05E0;&#x05D4; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D5;&#x05E0;&#x05D2;&#x05DF; &#x05D4;&#x05D5;&#x05D5;&#x05D9;&#x05D3;&#x05D0;&#x05D5;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05DC;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05E0;&#x05E4;&#x05EA;&#x05D7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;, &#x05D5;&#x05D4;&#x05D5;&#x05D0; &#x05E9;&#x05D5;&#x05DE;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E9;&#x05E0;&#x05EA;&#x05EA;&#x05DD; &#x05DC;&#x05D5;.</li>
        <li><b>&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05DC;&#x05E7;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D7;&#x05D3; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4;, &#x05D2;&#x05DD; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05D0;&#x05D5; &#x05E2;&#x05DD; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05EA;-&#x05D9;&#x05EA;&#x05E8; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;&#x05EA;. &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05D9;&#x05D3; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D4; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D4;. &#x05DE;&#x05E6;&#x05D1; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D2;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E9;&#x05DE;&#x05D0;&#x05DC;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D4;&#x05D8;&#x05D9;&#x05E4; &#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E8;&#x05E2;&#x05E0;&#x05D5;&#x05DF; &#x05D0;&#x05D5;&#x05DE;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05D4; &#x05D4;&#x05D5;&#x05D0; &#x05E2;&#x05D5;&#x05E9;&#x05D4;: &#x05D8;&#x05D5;&#x05E2;&#x05DF; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D5;&#x05DE;&#x05D0;&#x05E4;&#x05E1; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;.</li>
    </ul>
    </div>
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
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.111</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.111:</p>
    <ul>
        <li><b>Estilizar lado da extremidade:</b> Clique com o botão direito numa camada com uma extremidade livre e escolha Estilizar lado da extremidade, logo abaixo de Fechar o Nó. Uma janela permite escolher como a mecha termina: Reta, Inclinada, Arredondada, Pontiaguda, Entalhada ou Côncava. Também pode ajustar a inclinação e a profundidade, alongar ou encurtar a extremidade e adicionar uma linha lateral com espessura e cor próprias. A pré-visualização é ao vivo na tela. A sombra, a linha lateral e as máscaras seguem todas a nova forma. Os estilos de extremidade são salvos com o projeto e funcionam com desfazer e refazer.</li>
        <li><b>Tamanho certo em ecrãs com escala:</b> Em ecrãs de alta resolução com a escala de exibição ativada, os botões e o texto pareciam pequenos demais. A aplicação agora segue a escala do seu ecrã. Os rótulos da barra de ferramentas já não são cortados, e a barra passa para duas linhas quando a janela é estreita. O painel de camadas pode ser estreitado mais do que antes. O logótipo do OpenStrand Studio aparece agora em todas as janelas e na barra de tarefas.</li>
        <li><b>Janelas que cabem em ecrãs pequenos:</b> A janela Configurações agora pode ser reduzida, para que os botões Aplicar e OK fiquem sempre visíveis. O mesmo vale para Editar sombra, o editor de sombra de grupo, Criar Grade de Máscara, Editar Ângulos da Mecha, Mudar largura e o reprodutor de vídeo. Uma janela nunca abre maior do que o seu ecrã e mantém o tamanho que lhe der.</li>
        <li><b>Arrasto mais suave:</b> A tela permanece nítida enquanto arrasta, mesmo em ecrãs com escala ou com a superamostragem ativada. O modo mover mostra uma mão fechada enquanto arrasta um ponto. O modo de visualização agora também pode deslocar-se com o botão esquerdo do rato. A dica do botão Atualizar agora diz o que ele faz: recarregar as camadas e redefinir a vista.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.111</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.111:</p>
    <ul>
        <li><b>Stylize End Side:</b> Right-click a layer with a free end and pick Stylize End Side, just under Close the Knot. A dialog lets you choose how the strand ends: Straight, Angled, Rounded, Pointed, Notched or Concave. You can also set the tilt and depth, extend or trim the end, and add a side line with its own thickness and color. The preview is live on the canvas. The shadow, side line and masks all follow the new shape. End styles are saved with your project and work with undo and redo.</li>
        <li><b>Right Size on Scaled Screens:</b> On high-resolution screens with display scaling turned on, the buttons and text used to look too small. The app now follows your display scale. Toolbar labels no longer get cut off, and the toolbar moves onto two rows when the window is narrow. The layer panel can be dragged narrower than before. The OpenStrand Studio logo now appears on every window and in the taskbar.</li>
        <li><b>Dialogs Fit Small Screens:</b> The Settings dialog can now be made smaller, so its Apply and OK buttons always stay on screen. The same goes for Edit Shadow, the group shadow editor, Create Mask Grid, Edit Strand Angles, Change Width and the video player. A dialog never opens larger than your screen, and it keeps the size you give it.</li>
        <li><b>Smoother Dragging:</b> The canvas stays sharp while you drag, even on scaled displays or with supersampling on. Move mode shows a closed hand while dragging a point. View mode can now pan with the left mouse button too. The Refresh button's tooltip now says what it does: reload layers and reset the view.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.111</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.111 :</p>
    <ul>
        <li><b>Styliser le côté d'extrémité:</b> Faites un clic droit sur un calque ayant une extrémité libre et choisissez Styliser le côté d'extrémité, juste sous Fermer le Nœud. Une boîte de dialogue vous laisse choisir la forme de l'extrémité du brin : Droite, Inclinée, Arrondie, Pointue, Entaillée ou Concave. Vous pouvez aussi régler l'inclinaison et la profondeur, allonger ou raccourcir l'extrémité, et ajouter une ligne latérale avec sa propre épaisseur et sa propre couleur. L'aperçu est en direct sur le canevas. L'ombre, la ligne latérale et les masques suivent tous la nouvelle forme. Les styles d'extrémité sont enregistrés avec votre projet et fonctionnent avec annuler et rétablir.</li>
        <li><b>La bonne taille sur les écrans mis à l'échelle:</b> Sur les écrans haute résolution avec une mise à l'échelle de l'affichage, les boutons et le texte paraissaient trop petits. L'application suit désormais l'échelle de votre écran. Les libellés de la barre d'outils ne sont plus coupés, et la barre d'outils passe sur deux lignes quand la fenêtre est étroite. Le panneau des calques peut être réduit plus qu'avant. Le logo OpenStrand Studio apparaît maintenant sur chaque fenêtre et dans la barre des tâches.</li>
        <li><b>Des boîtes de dialogue adaptées aux petits écrans:</b> La boîte de dialogue Paramètres peut désormais être réduite, de sorte que ses boutons Appliquer et OK restent toujours à l'écran. Il en va de même pour Modifier l'ombre, l'éditeur d'ombre de groupe, Créer Grille de Masque, Modifier les angles des brins, Changer largeur et le lecteur vidéo. Une boîte de dialogue ne s'ouvre jamais plus grande que votre écran, et elle garde la taille que vous lui donnez.</li>
        <li><b>Un glissement plus fluide:</b> Le canevas reste net pendant que vous faites glisser, même sur les écrans mis à l'échelle ou avec le suréchantillonnage activé. Le mode déplacement affiche une main fermée pendant le glissement d'un point. Le mode vue peut maintenant aussi se déplacer avec le bouton gauche de la souris. L'info-bulle du bouton Actualiser indique désormais ce qu'il fait : recharger les calques et réinitialiser la vue.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.111</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.111:</p>
    <ul>
        <li><b>Endseite gestalten:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene mit einem freien Ende und wählen Sie Endseite gestalten, direkt unter Knoten schließen. In einem Dialog wählen Sie, wie der Strang endet: Gerade, Schräg, Abgerundet, Spitz, Eingekerbt oder Konkav. Sie können außerdem Neigung und Tiefe einstellen, das Ende verlängern oder kürzen und eine Seitenlinie mit eigener Dicke und Farbe hinzufügen. Die Vorschau erscheint live auf der Zeichenfläche. Schatten, Seitenlinie und Masken folgen alle der neuen Form. Endstile werden mit dem Projekt gespeichert und funktionieren mit Rückgängig und Wiederherstellen.</li>
        <li><b>Richtige Größe auf skalierten Bildschirmen:</b> Auf hochauflösenden Bildschirmen mit aktivierter Anzeigeskalierung wirkten Schaltflächen und Text zu klein. Die App folgt jetzt Ihrer Anzeigeskalierung. Beschriftungen in der Werkzeugleiste werden nicht mehr abgeschnitten, und die Werkzeugleiste wechselt bei schmalen Fenstern auf zwei Zeilen. Das Ebenenpanel lässt sich schmaler ziehen als zuvor. Das OpenStrand Studio Logo erscheint jetzt in jedem Fenster und in der Taskleiste.</li>
        <li><b>Dialoge passen auf kleine Bildschirme:</b> Der Dialog Einstellungen kann jetzt verkleinert werden, sodass seine Schaltflächen Übernehmen und OK immer sichtbar bleiben. Dasselbe gilt für Schatten bearbeiten, den Gruppenschatten-Editor, Maskenraster Erstellen, Strangwinkel bearbeiten, Breite ändern und den Videoplayer. Ein Dialog öffnet sich nie größer als Ihr Bildschirm und behält die Größe, die Sie ihm geben.</li>
        <li><b>Flüssigeres Ziehen:</b> Die Zeichenfläche bleibt beim Ziehen scharf, auch auf skalierten Bildschirmen oder mit eingeschaltetem Supersampling. Der Verschiebemodus zeigt beim Ziehen eines Punktes eine geschlossene Hand. Der Ansichtsmodus kann jetzt auch mit der linken Maustaste verschoben werden. Der Tooltip der Schaltfläche Aktualisieren sagt jetzt, was sie tut: Ebenen neu laden und Ansicht zurücksetzen.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.111</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.111:</p>
    <ul>
        <li><b>Stilizza il lato finale:</b> Fai clic destro su un livello con un'estremità libera e scegli Stilizza il lato finale, subito sotto Chiudi il Nodo. Una finestra ti permette di scegliere come termina il trefolo: Dritta, Inclinata, Arrotondata, Appuntita, Intagliata o Concava. Puoi anche regolare inclinazione e profondità, allungare o accorciare l'estremità e aggiungere una linea laterale con spessore e colore propri. L'anteprima è dal vivo sulla tela. Ombra, linea laterale e maschere seguono tutte la nuova forma. Gli stili delle estremità vengono salvati con il progetto e funzionano con annulla e ripristina.</li>
        <li><b>Dimensione giusta sugli schermi ridimensionati:</b> Sugli schermi ad alta risoluzione con il ridimensionamento attivo, pulsanti e testo apparivano troppo piccoli. L'app ora segue la scala del tuo schermo. Le etichette della barra degli strumenti non vengono più tagliate, e la barra passa su due righe quando la finestra è stretta. Il pannello dei livelli può essere ristretto più di prima. Il logo di OpenStrand Studio appare ora su ogni finestra e nella barra delle applicazioni.</li>
        <li><b>Finestre adatte agli schermi piccoli:</b> La finestra Impostazioni ora può essere rimpicciolita, così i pulsanti Applica e OK restano sempre visibili. Lo stesso vale per Modifica ombra, l'editor dell'ombra di gruppo, Crea Griglia Maschera, Modifica Angoli Trefolo, Cambia larghezza e il lettore video. Una finestra non si apre mai più grande dello schermo e mantiene la dimensione che le dai.</li>
        <li><b>Trascinamento più fluido:</b> La tela resta nitida mentre trascini, anche su schermi ridimensionati o con il supersampling attivo. La modalità sposta mostra una mano chiusa mentre trascini un punto. La modalità vista ora può scorrere anche con il tasto sinistro del mouse. Il suggerimento del pulsante Aggiorna ora dice cosa fa: ricarica i livelli e reimposta la vista.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.111</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.111:</p>
    <ul>
        <li><b>Estilizar lado del extremo:</b> Haz clic derecho en una capa con un extremo libre y elige Estilizar lado del extremo, justo debajo de Cerrar el Nudo. Un cuadro de diálogo te permite elegir cómo termina el cordón: Recto, Inclinado, Redondeado, Puntiagudo, Con muesca o Cóncavo. También puedes ajustar la inclinación y la profundidad, alargar o recortar el extremo, y añadir una línea lateral con su propio grosor y color. La vista previa es en vivo sobre el lienzo. La sombra, la línea lateral y las máscaras siguen la nueva forma. Los estilos de extremo se guardan con tu proyecto y funcionan con deshacer y rehacer.</li>
        <li><b>Tamaño correcto en pantallas escaladas:</b> En pantallas de alta resolución con el escalado activado, los botones y el texto se veían demasiado pequeños. La aplicación ahora sigue la escala de tu pantalla. Las etiquetas de la barra de herramientas ya no se cortan, y la barra pasa a dos filas cuando la ventana es estrecha. El panel de capas se puede estrechar más que antes. El logotipo de OpenStrand Studio aparece ahora en cada ventana y en la barra de tareas.</li>
        <li><b>Diálogos que caben en pantallas pequeñas:</b> El diálogo Configuración ahora se puede hacer más pequeño, así sus botones Aplicar y OK siempre quedan en pantalla. Lo mismo ocurre con Editar sombra, el editor de sombra de grupo, Crear Cuadrícula de Máscara, Editar Ángulos del Cordón, Cambiar ancho y el reproductor de video. Un diálogo nunca se abre más grande que tu pantalla, y conserva el tamaño que le das.</li>
        <li><b>Arrastre más suave:</b> El lienzo se mantiene nítido mientras arrastras, incluso en pantallas escaladas o con el supermuestreo activado. El modo mover muestra una mano cerrada mientras arrastras un punto. El modo vista ahora también puede desplazarse con el botón izquierdo del ratón. La descripción del botón Actualizar ahora dice lo que hace: recargar las capas y restablecer la vista.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.111</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.111:</p>
    <ul>
        <li><b>&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9; &#x05D5;&#x05D1;&#x05D7;&#x05E8;&#x05D5; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05D0;&#x05D9;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05D9;&#x05DD;: &#x05D9;&#x05E9;&#x05E8;, &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E2;, &#x05DE;&#x05E2;&#x05D5;&#x05D2;&#x05DC;, &#x05DE;&#x05D7;&#x05D5;&#x05D3;&#x05D3;, &#x05D7;&#x05E8;&#x05D5;&#x05E5; &#x05D0;&#x05D5; &#x05E7;&#x05E2;&#x05D5;&#x05E8;. &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05D2;&#x05DD; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05DF; &#x05D0;&#x05EA; &#x05D4;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D5;&#x05D4;&#x05E2;&#x05D5;&#x05DE;&#x05E7;, &#x05DC;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05DA; &#x05D0;&#x05D5; &#x05DC;&#x05E7;&#x05E6;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05D5;&#x05DC;&#x05D4;&#x05D5;&#x05E1;&#x05D9;&#x05E3; &#x05E7;&#x05D5; &#x05E6;&#x05D3; &#x05E2;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05D5;&#x05E6;&#x05D1;&#x05E2; &#x05DE;&#x05E9;&#x05DC;&#x05D5;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05D7;&#x05D9;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;. &#x05D4;&#x05E6;&#x05DC;, &#x05E7;&#x05D5; &#x05D4;&#x05E6;&#x05D3; &#x05D5;&#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D4;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D4;&#x05D7;&#x05D3;&#x05E9;&#x05D4;. &#x05E1;&#x05D2;&#x05E0;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E2;&#x05D5;&#x05D1;&#x05D3;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;.</li>
        <li><b>&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E0;&#x05DB;&#x05D5;&#x05DF; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4;:</b> &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05D1;&#x05E8;&#x05D6;&#x05D5;&#x05DC;&#x05D5;&#x05E6;&#x05D9;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;, &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D4;&#x05D8;&#x05E7;&#x05E1;&#x05D8; &#x05E0;&#x05E8;&#x05D0;&#x05D5; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D9;. &#x05D4;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05E7;&#x05E0;&#x05D4; &#x05D4;&#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;. &#x05EA;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05E0;&#x05D7;&#x05EA;&#x05DB;&#x05D5;&#x05EA;, &#x05D5;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05E8; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05E9;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05DB;&#x05E9;&#x05D4;&#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05E6;&#x05E8;. &#x05D0;&#x05EA; &#x05DC;&#x05D5;&#x05D7; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05D5;&#x05E8; &#x05E6;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D1;&#x05E2;&#x05D1;&#x05E8;. &#x05D4;&#x05DC;&#x05D5;&#x05D2;&#x05D5; &#x05E9;&#x05DC; OpenStrand Studio &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D5;&#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05EA; &#x05D4;&#x05DE;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D7;&#x05DC;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DE;&#x05D9;&#x05DD; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05D0;&#x05EA; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05E7;&#x05D8;&#x05D9;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D7;&#x05DC; &#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA;. &#x05DB;&#x05DA; &#x05D2;&#x05DD; &#x05E2;&#x05E8;&#x05D9;&#x05DB;&#x05EA; &#x05E6;&#x05DC;, &#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC; &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;, &#x05E6;&#x05D5;&#x05E8; &#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05E8;&#x05D5;&#x05DA; &#x05D6;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05E9;&#x05E0;&#x05D4; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D5;&#x05E0;&#x05D2;&#x05DF; &#x05D4;&#x05D5;&#x05D5;&#x05D9;&#x05D3;&#x05D0;&#x05D5;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05DC;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05E0;&#x05E4;&#x05EA;&#x05D7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;, &#x05D5;&#x05D4;&#x05D5;&#x05D0; &#x05E9;&#x05D5;&#x05DE;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E9;&#x05E0;&#x05EA;&#x05EA;&#x05DD; &#x05DC;&#x05D5;.</li>
        <li><b>&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05DC;&#x05E7;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D7;&#x05D3; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4;, &#x05D2;&#x05DD; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05D0;&#x05D5; &#x05E2;&#x05DD; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05EA;-&#x05D9;&#x05EA;&#x05E8; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;&#x05EA;. &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05D9;&#x05D3; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D4; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D4;. &#x05DE;&#x05E6;&#x05D1; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D2;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E9;&#x05DE;&#x05D0;&#x05DC;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D4;&#x05D8;&#x05D9;&#x05E4; &#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E8;&#x05E2;&#x05E0;&#x05D5;&#x05DF; &#x05D0;&#x05D5;&#x05DE;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05D4; &#x05D4;&#x05D5;&#x05D0; &#x05E2;&#x05D5;&#x05E9;&#x05D4;: &#x05D8;&#x05D5;&#x05E2;&#x05DF; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D5;&#x05DE;&#x05D0;&#x05E4;&#x05E1; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;.</li>
    </ul>
    </div>
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
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.111</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.111:</p>
    <ul>
        <li><b>&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9; &#x05D5;&#x05D1;&#x05D7;&#x05E8;&#x05D5; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05DE;&#x05DE;&#x05E9; &#x05DE;&#x05EA;&#x05D7;&#x05EA; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D3;&#x05D5;-&#x05E9;&#x05D9;&#x05D7; &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05D0;&#x05D9;&#x05DA; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05D9;&#x05DD;: &#x05D9;&#x05E9;&#x05E8;, &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E2;, &#x05DE;&#x05E2;&#x05D5;&#x05D2;&#x05DC;, &#x05DE;&#x05D7;&#x05D5;&#x05D3;&#x05D3;, &#x05D7;&#x05E8;&#x05D5;&#x05E5; &#x05D0;&#x05D5; &#x05E7;&#x05E2;&#x05D5;&#x05E8;. &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05D2;&#x05DD; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05DF; &#x05D0;&#x05EA; &#x05D4;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D5;&#x05D4;&#x05E2;&#x05D5;&#x05DE;&#x05E7;, &#x05DC;&#x05D4;&#x05D0;&#x05E8;&#x05D9;&#x05DA; &#x05D0;&#x05D5; &#x05DC;&#x05E7;&#x05E6;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4;, &#x05D5;&#x05DC;&#x05D4;&#x05D5;&#x05E1;&#x05D9;&#x05E3; &#x05E7;&#x05D5; &#x05E6;&#x05D3; &#x05E2;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05D5;&#x05E6;&#x05D1;&#x05E2; &#x05DE;&#x05E9;&#x05DC;&#x05D5;. &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D4;&#x05DE;&#x05E7;&#x05D3;&#x05D9;&#x05DE;&#x05D4; &#x05D7;&#x05D9;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1;. &#x05D4;&#x05E6;&#x05DC;, &#x05E7;&#x05D5; &#x05D4;&#x05E6;&#x05D3; &#x05D5;&#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05D4;&#x05E6;&#x05D5;&#x05E8;&#x05D4; &#x05D4;&#x05D7;&#x05D3;&#x05E9;&#x05D4;. &#x05E1;&#x05D2;&#x05E0;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E2;&#x05D5;&#x05D1;&#x05D3;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;.</li>
        <li><b>&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E0;&#x05DB;&#x05D5;&#x05DF; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4;:</b> &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05D1;&#x05E8;&#x05D6;&#x05D5;&#x05DC;&#x05D5;&#x05E6;&#x05D9;&#x05D4; &#x05D2;&#x05D1;&#x05D5;&#x05D4;&#x05D4; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;, &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D4;&#x05D8;&#x05E7;&#x05E1;&#x05D8; &#x05E0;&#x05E8;&#x05D0;&#x05D5; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D9;. &#x05D4;&#x05D0;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05E6;&#x05D9;&#x05D4; &#x05E2;&#x05D5;&#x05E7;&#x05D1;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D7;&#x05E8;&#x05D9; &#x05E7;&#x05E0;&#x05D4; &#x05D4;&#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;. &#x05EA;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05DB;&#x05D1;&#x05E8; &#x05DC;&#x05D0; &#x05E0;&#x05D7;&#x05EA;&#x05DB;&#x05D5;&#x05EA;, &#x05D5;&#x05E1;&#x05E8;&#x05D2;&#x05DC; &#x05D4;&#x05DB;&#x05DC;&#x05D9;&#x05DD; &#x05E2;&#x05D5;&#x05D1;&#x05E8; &#x05DC;&#x05E9;&#x05EA;&#x05D9; &#x05E9;&#x05D5;&#x05E8;&#x05D5;&#x05EA; &#x05DB;&#x05E9;&#x05D4;&#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05E6;&#x05E8;. &#x05D0;&#x05EA; &#x05DC;&#x05D5;&#x05D7; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05D5;&#x05E8; &#x05E6;&#x05E8; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D1;&#x05E2;&#x05D1;&#x05E8;. &#x05D4;&#x05DC;&#x05D5;&#x05D2;&#x05D5; &#x05E9;&#x05DC; OpenStrand Studio &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05DB;&#x05DC; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D5;&#x05D1;&#x05E9;&#x05D5;&#x05E8;&#x05EA; &#x05D4;&#x05DE;&#x05E9;&#x05D9;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D7;&#x05DC;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DE;&#x05D9;&#x05DD; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD;:</b> &#x05D0;&#x05EA; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05E7;&#x05D8;&#x05D9;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D4;&#x05D7;&#x05DC; &#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05E8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DA;. &#x05DB;&#x05DA; &#x05D2;&#x05DD; &#x05E2;&#x05E8;&#x05D9;&#x05DB;&#x05EA; &#x05E6;&#x05DC;, &#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC; &#x05E9;&#x05DC; &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;, &#x05E6;&#x05D5;&#x05E8; &#x05E8;&#x05E9;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA;, &#x05E2;&#x05E8;&#x05D5;&#x05DA; &#x05D6;&#x05D5;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;, &#x05E9;&#x05E0;&#x05D4; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D5;&#x05E0;&#x05D2;&#x05DF; &#x05D4;&#x05D5;&#x05D5;&#x05D9;&#x05D3;&#x05D0;&#x05D5;. &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05DC;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05E0;&#x05E4;&#x05EA;&#x05D7; &#x05D2;&#x05D3;&#x05D5;&#x05DC; &#x05DE;&#x05D4;&#x05DE;&#x05E1;&#x05DA; &#x05E9;&#x05DC;&#x05DB;&#x05DD;, &#x05D5;&#x05D4;&#x05D5;&#x05D0; &#x05E9;&#x05D5;&#x05DE;&#x05E8; &#x05E2;&#x05DC; &#x05D4;&#x05D2;&#x05D5;&#x05D3;&#x05DC; &#x05E9;&#x05E0;&#x05EA;&#x05EA;&#x05DD; &#x05DC;&#x05D5;.</li>
        <li><b>&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4; &#x05D7;&#x05DC;&#x05E7;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E0;&#x05E9;&#x05D0;&#x05E8; &#x05D7;&#x05D3; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D4;&#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05D4;, &#x05D2;&#x05DD; &#x05D1;&#x05DE;&#x05E1;&#x05DB;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D3;&#x05D4; &#x05D0;&#x05D5; &#x05E2;&#x05DD; &#x05D3;&#x05D2;&#x05D9;&#x05DE;&#x05EA;-&#x05D9;&#x05EA;&#x05E8; &#x05DE;&#x05D5;&#x05E4;&#x05E2;&#x05DC;&#x05EA;. &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05D9;&#x05D3; &#x05E1;&#x05D2;&#x05D5;&#x05E8;&#x05D4; &#x05D1;&#x05D6;&#x05DE;&#x05DF; &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D4;. &#x05DE;&#x05E6;&#x05D1; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DB;&#x05E2;&#x05EA; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05D2;&#x05DD; &#x05E2;&#x05DD; &#x05D4;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E9;&#x05DE;&#x05D0;&#x05DC;&#x05D9; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05DB;&#x05D1;&#x05E8;. &#x05D4;&#x05D8;&#x05D9;&#x05E4; &#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05E8;&#x05E2;&#x05E0;&#x05D5;&#x05DF; &#x05D0;&#x05D5;&#x05DE;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05D4; &#x05D4;&#x05D5;&#x05D0; &#x05E2;&#x05D5;&#x05E9;&#x05D4;: &#x05D8;&#x05D5;&#x05E2;&#x05DF; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D5;&#x05DE;&#x05D0;&#x05E4;&#x05E1; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;.</li>
    </ul>
    </div>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.111</h2>
    <p dir="ltr">This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p dir="ltr">What's New in Version 1.111:</p>
    <ul dir="ltr">
        <li><b>Stylize End Side:</b> Right-click a layer with a free end and pick Stylize End Side, just under Close the Knot. A dialog lets you choose how the strand ends: Straight, Angled, Rounded, Pointed, Notched or Concave. You can also set the tilt and depth, extend or trim the end, and add a side line with its own thickness and color. The preview is live on the canvas. The shadow, side line and masks all follow the new shape. End styles are saved with your project and work with undo and redo.</li>
        <li><b>Right Size on Scaled Screens:</b> On high-resolution screens with display scaling turned on, the buttons and text used to look too small. The app now follows your display scale. Toolbar labels no longer get cut off, and the toolbar moves onto two rows when the window is narrow. The layer panel can be dragged narrower than before. The OpenStrand Studio logo now appears on every window and in the taskbar.</li>
        <li><b>Dialogs Fit Small Screens:</b> The Settings dialog can now be made smaller, so its Apply and OK buttons always stay on screen. The same goes for Edit Shadow, the group shadow editor, Create Mask Grid, Edit Strand Angles, Change Width and the video player. A dialog never opens larger than your screen, and it keeps the size you give it.</li>
        <li><b>Smoother Dragging:</b> The canvas stays sharp while you drag, even on scaled displays or with supersampling on. Move mode shows a closed hand while dragging a point. View mode can now pan with the left mouse button too. The Refresh button's tooltip now says what it does: reload layers and reset the view.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.111</h2>
    <p dir="ltr">Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p dir="ltr">Nouveautés de la version 1.111 :</p>
    <ul dir="ltr">
        <li><b>Styliser le côté d'extrémité:</b> Faites un clic droit sur un calque ayant une extrémité libre et choisissez Styliser le côté d'extrémité, juste sous Fermer le Nœud. Une boîte de dialogue vous laisse choisir la forme de l'extrémité du brin : Droite, Inclinée, Arrondie, Pointue, Entaillée ou Concave. Vous pouvez aussi régler l'inclinaison et la profondeur, allonger ou raccourcir l'extrémité, et ajouter une ligne latérale avec sa propre épaisseur et sa propre couleur. L'aperçu est en direct sur le canevas. L'ombre, la ligne latérale et les masques suivent tous la nouvelle forme. Les styles d'extrémité sont enregistrés avec votre projet et fonctionnent avec annuler et rétablir.</li>
        <li><b>La bonne taille sur les écrans mis à l'échelle:</b> Sur les écrans haute résolution avec une mise à l'échelle de l'affichage, les boutons et le texte paraissaient trop petits. L'application suit désormais l'échelle de votre écran. Les libellés de la barre d'outils ne sont plus coupés, et la barre d'outils passe sur deux lignes quand la fenêtre est étroite. Le panneau des calques peut être réduit plus qu'avant. Le logo OpenStrand Studio apparaît maintenant sur chaque fenêtre et dans la barre des tâches.</li>
        <li><b>Des boîtes de dialogue adaptées aux petits écrans:</b> La boîte de dialogue Paramètres peut désormais être réduite, de sorte que ses boutons Appliquer et OK restent toujours à l'écran. Il en va de même pour Modifier l'ombre, l'éditeur d'ombre de groupe, Créer Grille de Masque, Modifier les angles des brins, Changer largeur et le lecteur vidéo. Une boîte de dialogue ne s'ouvre jamais plus grande que votre écran, et elle garde la taille que vous lui donnez.</li>
        <li><b>Un glissement plus fluide:</b> Le canevas reste net pendant que vous faites glisser, même sur les écrans mis à l'échelle ou avec le suréchantillonnage activé. Le mode déplacement affiche une main fermée pendant le glissement d'un point. Le mode vue peut maintenant aussi se déplacer avec le bouton gauche de la souris. L'info-bulle du bouton Actualiser indique désormais ce qu'il fait : recharger les calques et réinitialiser la vue.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.111</h2>
    <p dir="ltr">Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p dir="ltr">Neu in Version 1.111:</p>
    <ul dir="ltr">
        <li><b>Endseite gestalten:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene mit einem freien Ende und wählen Sie Endseite gestalten, direkt unter Knoten schließen. In einem Dialog wählen Sie, wie der Strang endet: Gerade, Schräg, Abgerundet, Spitz, Eingekerbt oder Konkav. Sie können außerdem Neigung und Tiefe einstellen, das Ende verlängern oder kürzen und eine Seitenlinie mit eigener Dicke und Farbe hinzufügen. Die Vorschau erscheint live auf der Zeichenfläche. Schatten, Seitenlinie und Masken folgen alle der neuen Form. Endstile werden mit dem Projekt gespeichert und funktionieren mit Rückgängig und Wiederherstellen.</li>
        <li><b>Richtige Größe auf skalierten Bildschirmen:</b> Auf hochauflösenden Bildschirmen mit aktivierter Anzeigeskalierung wirkten Schaltflächen und Text zu klein. Die App folgt jetzt Ihrer Anzeigeskalierung. Beschriftungen in der Werkzeugleiste werden nicht mehr abgeschnitten, und die Werkzeugleiste wechselt bei schmalen Fenstern auf zwei Zeilen. Das Ebenenpanel lässt sich schmaler ziehen als zuvor. Das OpenStrand Studio Logo erscheint jetzt in jedem Fenster und in der Taskleiste.</li>
        <li><b>Dialoge passen auf kleine Bildschirme:</b> Der Dialog Einstellungen kann jetzt verkleinert werden, sodass seine Schaltflächen Übernehmen und OK immer sichtbar bleiben. Dasselbe gilt für Schatten bearbeiten, den Gruppenschatten-Editor, Maskenraster Erstellen, Strangwinkel bearbeiten, Breite ändern und den Videoplayer. Ein Dialog öffnet sich nie größer als Ihr Bildschirm und behält die Größe, die Sie ihm geben.</li>
        <li><b>Flüssigeres Ziehen:</b> Die Zeichenfläche bleibt beim Ziehen scharf, auch auf skalierten Bildschirmen oder mit eingeschaltetem Supersampling. Der Verschiebemodus zeigt beim Ziehen eines Punktes eine geschlossene Hand. Der Ansichtsmodus kann jetzt auch mit der linken Maustaste verschoben werden. Der Tooltip der Schaltfläche Aktualisieren sagt jetzt, was sie tut: Ebenen neu laden und Ansicht zurücksetzen.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.111</h2>
    <p dir="ltr">Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p dir="ltr">Novità della versione 1.111:</p>
    <ul dir="ltr">
        <li><b>Stilizza il lato finale:</b> Fai clic destro su un livello con un'estremità libera e scegli Stilizza il lato finale, subito sotto Chiudi il Nodo. Una finestra ti permette di scegliere come termina il trefolo: Dritta, Inclinata, Arrotondata, Appuntita, Intagliata o Concava. Puoi anche regolare inclinazione e profondità, allungare o accorciare l'estremità e aggiungere una linea laterale con spessore e colore propri. L'anteprima è dal vivo sulla tela. Ombra, linea laterale e maschere seguono tutte la nuova forma. Gli stili delle estremità vengono salvati con il progetto e funzionano con annulla e ripristina.</li>
        <li><b>Dimensione giusta sugli schermi ridimensionati:</b> Sugli schermi ad alta risoluzione con il ridimensionamento attivo, pulsanti e testo apparivano troppo piccoli. L'app ora segue la scala del tuo schermo. Le etichette della barra degli strumenti non vengono più tagliate, e la barra passa su due righe quando la finestra è stretta. Il pannello dei livelli può essere ristretto più di prima. Il logo di OpenStrand Studio appare ora su ogni finestra e nella barra delle applicazioni.</li>
        <li><b>Finestre adatte agli schermi piccoli:</b> La finestra Impostazioni ora può essere rimpicciolita, così i pulsanti Applica e OK restano sempre visibili. Lo stesso vale per Modifica ombra, l'editor dell'ombra di gruppo, Crea Griglia Maschera, Modifica Angoli Trefolo, Cambia larghezza e il lettore video. Una finestra non si apre mai più grande dello schermo e mantiene la dimensione che le dai.</li>
        <li><b>Trascinamento più fluido:</b> La tela resta nitida mentre trascini, anche su schermi ridimensionati o con il supersampling attivo. La modalità sposta mostra una mano chiusa mentre trascini un punto. La modalità vista ora può scorrere anche con il tasto sinistro del mouse. Il suggerimento del pulsante Aggiorna ora dice cosa fa: ricarica i livelli e reimposta la vista.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.111</h2>
    <p dir="ltr">Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p dir="ltr">Novedades de la versión 1.111:</p>
    <ul dir="ltr">
        <li><b>Estilizar lado del extremo:</b> Haz clic derecho en una capa con un extremo libre y elige Estilizar lado del extremo, justo debajo de Cerrar el Nudo. Un cuadro de diálogo te permite elegir cómo termina el cordón: Recto, Inclinado, Redondeado, Puntiagudo, Con muesca o Cóncavo. También puedes ajustar la inclinación y la profundidad, alargar o recortar el extremo, y añadir una línea lateral con su propio grosor y color. La vista previa es en vivo sobre el lienzo. La sombra, la línea lateral y las máscaras siguen la nueva forma. Los estilos de extremo se guardan con tu proyecto y funcionan con deshacer y rehacer.</li>
        <li><b>Tamaño correcto en pantallas escaladas:</b> En pantallas de alta resolución con el escalado activado, los botones y el texto se veían demasiado pequeños. La aplicación ahora sigue la escala de tu pantalla. Las etiquetas de la barra de herramientas ya no se cortan, y la barra pasa a dos filas cuando la ventana es estrecha. El panel de capas se puede estrechar más que antes. El logotipo de OpenStrand Studio aparece ahora en cada ventana y en la barra de tareas.</li>
        <li><b>Diálogos que caben en pantallas pequeñas:</b> El diálogo Configuración ahora se puede hacer más pequeño, así sus botones Aplicar y OK siempre quedan en pantalla. Lo mismo ocurre con Editar sombra, el editor de sombra de grupo, Crear Cuadrícula de Máscara, Editar Ángulos del Cordón, Cambiar ancho y el reproductor de video. Un diálogo nunca se abre más grande que tu pantalla, y conserva el tamaño que le das.</li>
        <li><b>Arrastre más suave:</b> El lienzo se mantiene nítido mientras arrastras, incluso en pantallas escaladas o con el supermuestreo activado. El modo mover muestra una mano cerrada mientras arrastras un punto. El modo vista ahora también puede desplazarse con el botón izquierdo del ratón. La descripción del botón Actualizar ahora dice lo que hace: recargar las capas y restablecer la vista.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.111</h2>
    <p dir="ltr">Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p dir="ltr">Novidades da versão 1.111:</p>
    <ul dir="ltr">
        <li><b>Estilizar lado da extremidade:</b> Clique com o botão direito numa camada com uma extremidade livre e escolha Estilizar lado da extremidade, logo abaixo de Fechar o Nó. Uma janela permite escolher como a mecha termina: Reta, Inclinada, Arredondada, Pontiaguda, Entalhada ou Côncava. Também pode ajustar a inclinação e a profundidade, alongar ou encurtar a extremidade e adicionar uma linha lateral com espessura e cor próprias. A pré-visualização é ao vivo na tela. A sombra, a linha lateral e as máscaras seguem todas a nova forma. Os estilos de extremidade são salvos com o projeto e funcionam com desfazer e refazer.</li>
        <li><b>Tamanho certo em ecrãs com escala:</b> Em ecrãs de alta resolução com a escala de exibição ativada, os botões e o texto pareciam pequenos demais. A aplicação agora segue a escala do seu ecrã. Os rótulos da barra de ferramentas já não são cortados, e a barra passa para duas linhas quando a janela é estreita. O painel de camadas pode ser estreitado mais do que antes. O logótipo do OpenStrand Studio aparece agora em todas as janelas e na barra de tarefas.</li>
        <li><b>Janelas que cabem em ecrãs pequenos:</b> A janela Configurações agora pode ser reduzida, para que os botões Aplicar e OK fiquem sempre visíveis. O mesmo vale para Editar sombra, o editor de sombra de grupo, Criar Grade de Máscara, Editar Ângulos da Mecha, Mudar largura e o reprodutor de vídeo. Uma janela nunca abre maior do que o seu ecrã e mantém o tamanho que lhe der.</li>
        <li><b>Arrasto mais suave:</b> A tela permanece nítida enquanto arrasta, mesmo em ecrãs com escala ou com a superamostragem ativada. O modo mover mostra uma mão fechada enquanto arrasta um ponto. O modo de visualização agora também pode deslocar-se com o botão esquerdo do rato. A dica do botão Atualizar agora diz o que ele faz: recarregar as camadas e redefinir a vista.</li>
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

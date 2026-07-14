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
VERSION="1.109"
APP_DATE="14_July_2026"
PUBLISHER="Yonatan Setbon"
IDENTIFIER="com.yonatan.openstrandstudio"

# Create directories
WORKING_DIR="$(mktemp -d)"
SCRIPTS_DIR="$WORKING_DIR/scripts"
RESOURCES_DIR="$WORKING_DIR/resources"
# Use underscores instead of dots in the output filename (1.109 -> 1_109) so the
# version dot is never mistaken for a file extension. VERSION itself stays dotted
# for the installer title and pkg metadata.
VERSION_FILE="${VERSION//./_}"
PKG_PATH="/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/installer_output/${APP_NAME}_${VERSION_FILE}.pkg"

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
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.109</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.109:</p>
    <ul>
        <li><b>Lock Mode Redesigned:</b> Each layer button now shows a small padlock in lock mode. Click the padlock to lock/unlock; clicking the layer simply selects it. Locked strands can be selected but not moved or attached to, and New Strand / Delete Strand remain available (delete is blocked only for locked layers). The lock state is also remembered through undo/redo, save/load, and tab switching.</li>
        <li><b>Per-Layer Hide Shadow Option:</b> Right-click a layer to stop it from casting shadow onto other strands. The setting is saved with your project and survives undo/redo and group operations.</li>
        <li><b>Automatic Shadow Correction for Woven Masks:</b> Incorrect shadow marks at mask crossings are now hidden automatically; your manual Shadow Editor settings are always respected.</li>
        <li><b>Mask Shadows in the Shadow Editor:</b> Shadows cast through a mask now appear in the over-strand's Shadow Editor, so you can turn them on or off like any other shadow.</li>
        <li><b>More Accurate Strand Selection:</b> Clicking now selects exactly what you see: strand edges, end caps, and mask outlines are all clickable, the topmost strand is always picked, and the hover highlight always matches what a click will select.</li>
        <li><b>Control Point Visibility Fix:</b> "Show control points only for the selected strand" now hides only control points; other strands keep their endpoint squares and remain movable. Dragging an endpoint no longer makes an untouched control point appear.</li>
        <li><b>Shadow Settings Preserved:</b> A layer's hidden-shadow state is no longer reset by group move or duplicate operations.</li>
        <li><b>Improved Drawing Stability:</b> Fixed internal painting issues that could corrupt the canvas after a drawing error.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.109</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.109:</p>
    <ul>
        <li><b>Sperrmodus überarbeitet:</b> Jede Ebenen-Schaltfläche zeigt im Sperrmodus jetzt ein kleines Vorhängeschloss. Klicken Sie auf das Schloss zum Sperren/Entsperren; ein Klick auf die Ebene wählt sie einfach aus. Gesperrte Stränge können ausgewählt, aber nicht bewegt oder als Ansatzpunkt verwendet werden, und Neuer Strang / Strang löschen bleiben verfügbar (Löschen ist nur für gesperrte Ebenen blockiert). Der Sperrzustand bleibt auch bei Rückgängig/Wiederherstellen, Speichern/Laden und Tab-Wechsel erhalten.</li>
        <li><b>Option „Schatten ausblenden“ pro Ebene:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene, damit sie keinen Schatten mehr auf andere Stränge wirft. Die Einstellung wird mit dem Projekt gespeichert und übersteht Rückgängig/Wiederherstellen sowie Gruppenoperationen.</li>
        <li><b>Automatische Schattenkorrektur für gewebte Masken:</b> Falsche Schattenspuren an Maskenkreuzungen werden jetzt automatisch ausgeblendet; Ihre manuellen Einstellungen im Schatten-Editor werden immer respektiert.</li>
        <li><b>Maskenschatten im Schatten-Editor:</b> Schatten, die durch eine Maske geworfen werden, erscheinen jetzt im Schatten-Editor des oberen Strangs und lassen sich wie jeder andere Schatten ein- oder ausschalten.</li>
        <li><b>Präzisere Strangauswahl:</b> Ein Klick wählt jetzt genau das aus, was Sie sehen: Strangränder, Endkappen und Maskenumrisse sind alle anklickbar, der oberste Strang wird immer gewählt, und die Hervorhebung beim Überfahren entspricht immer dem, was ein Klick auswählen würde.</li>
        <li><b>Kontrollpunkt-Anzeige korrigiert:</b> „Kontrollpunkte nur für den ausgewählten Strang anzeigen“ blendet jetzt nur noch Kontrollpunkte aus; andere Stränge behalten ihre Endpunkt-Quadrate und bleiben beweglich. Das Ziehen eines Endpunkts lässt keinen unbenutzten Kontrollpunkt mehr erscheinen.</li>
        <li><b>Schatteneinstellungen bleiben erhalten:</b> Der Zustand „Schatten ausgeblendet“ einer Ebene wird durch Gruppenverschiebung oder -duplizierung nicht mehr zurückgesetzt.</li>
        <li><b>Verbesserte Zeichenstabilität:</b> Interne Renderprobleme behoben, die nach einem Zeichenfehler die Leinwand beschädigen konnten.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.109</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.109 :</p>
    <ul>
        <li><b>Mode verrouillage repensé:</b> Chaque bouton de calque affiche désormais un petit cadenas en mode verrouillage. Cliquez sur le cadenas pour verrouiller/déverrouiller ; cliquer sur le calque le sélectionne simplement. Les brins verrouillés peuvent être sélectionnés mais ni déplacés ni utilisés pour l'attache, et Nouveau brin / Supprimer le brin restent disponibles (la suppression n'est bloquée que pour les calques verrouillés). L'état de verrouillage est également conservé lors des annulations/rétablissements, de l'enregistrement/du chargement et du changement d'onglet.</li>
        <li><b>Option Masquer l'ombre par calque:</b> Faites un clic droit sur un calque pour l'empêcher de projeter une ombre sur les autres brins. Le réglage est enregistré avec votre projet et survit aux annulations/rétablissements et aux opérations de groupe.</li>
        <li><b>Correction automatique des ombres pour les masques tissés:</b> Les marques d'ombre incorrectes aux croisements des masques sont désormais masquées automatiquement ; vos réglages manuels dans l'éditeur d'ombres sont toujours respectés.</li>
        <li><b>Ombres de masque dans l'éditeur d'ombres:</b> Les ombres projetées à travers un masque apparaissent désormais dans l'éditeur d'ombres du brin supérieur, vous pouvez donc les activer ou les désactiver comme n'importe quelle autre ombre.</li>
        <li><b>Sélection de brins plus précise:</b> Un clic sélectionne désormais exactement ce que vous voyez : les bords des brins, les extrémités et les contours des masques sont tous cliquables, le brin le plus haut est toujours choisi, et la surbrillance au survol correspond toujours à ce qu'un clic sélectionnera.</li>
        <li><b>Correction de l'affichage des points de contrôle:</b> « Afficher les points de contrôle uniquement pour le brin sélectionné » ne masque plus que les points de contrôle ; les autres brins conservent leurs carrés d'extrémité et restent déplaçables. Faire glisser une extrémité ne fait plus apparaître un point de contrôle jamais utilisé.</li>
        <li><b>Réglages d'ombre préservés:</b> L'état « ombre masquée » d'un calque n'est plus réinitialisé par un déplacement ou une duplication de groupe.</li>
        <li><b>Stabilité de dessin améliorée:</b> Correction de problèmes internes de rendu qui pouvaient corrompre le canevas après une erreur de dessin.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.109</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.109:</p>
    <ul>
        <li><b>Modalità blocco ridisegnata:</b> Ogni pulsante di livello ora mostra un piccolo lucchetto in modalità blocco. Fai clic sul lucchetto per bloccare/sbloccare; fare clic sul livello lo seleziona semplicemente. I fili bloccati possono essere selezionati ma non spostati né usati per l'attacco, e Nuovo filo / Elimina filo restano disponibili (l'eliminazione è bloccata solo per i livelli bloccati). Lo stato di blocco viene inoltre ricordato tra annulla/ripristina, salvataggio/caricamento e cambio di scheda.</li>
        <li><b>Opzione Nascondi ombra per livello:</b> Fai clic destro su un livello per impedirgli di proiettare ombra sugli altri fili. L'impostazione viene salvata con il progetto e sopravvive ad annulla/ripristina e alle operazioni di gruppo.</li>
        <li><b>Correzione automatica delle ombre per maschere intrecciate:</b> I segni d'ombra errati agli incroci delle maschere ora vengono nascosti automaticamente; le tue impostazioni manuali nell'editor ombre vengono sempre rispettate.</li>
        <li><b>Ombre delle maschere nell'editor ombre:</b> Le ombre proiettate attraverso una maschera ora appaiono nell'editor ombre del filo superiore, così puoi attivarle o disattivarle come qualsiasi altra ombra.</li>
        <li><b>Selezione dei fili più precisa:</b> Un clic ora seleziona esattamente ciò che vedi: i bordi dei fili, le estremità e i contorni delle maschere sono tutti cliccabili, viene sempre scelto il filo più in alto e l'evidenziazione al passaggio del mouse corrisponde sempre a ciò che un clic selezionerà.</li>
        <li><b>Correzione della visibilità dei punti di controllo:</b> «Mostra i punti di controllo solo per il filo selezionato» ora nasconde solo i punti di controllo; gli altri fili mantengono i loro quadrati alle estremità e restano spostabili. Trascinare un'estremità non fa più apparire un punto di controllo mai utilizzato.</li>
        <li><b>Impostazioni ombra preservate:</b> Lo stato «ombra nascosta» di un livello non viene più azzerato da spostamenti o duplicazioni di gruppo.</li>
        <li><b>Maggiore stabilità di disegno:</b> Risolti problemi interni di rendering che potevano corrompere la tela dopo un errore di disegno.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.109</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.109:</p>
    <ul>
        <li><b>Modo de bloqueo rediseñado:</b> Cada botón de capa ahora muestra un pequeño candado en modo de bloqueo. Haz clic en el candado para bloquear/desbloquear; hacer clic en la capa simplemente la selecciona. Las hebras bloqueadas pueden seleccionarse pero no moverse ni usarse para adjuntar, y Nueva hebra / Eliminar hebra siguen disponibles (la eliminación solo se bloquea para capas bloqueadas). El estado de bloqueo también se recuerda al deshacer/rehacer, guardar/cargar y cambiar de pestaña.</li>
        <li><b>Opción Ocultar sombra por capa:</b> Haz clic derecho en una capa para impedir que proyecte sombra sobre otras hebras. El ajuste se guarda con tu proyecto y sobrevive a deshacer/rehacer y a las operaciones de grupo.</li>
        <li><b>Corrección automática de sombras para máscaras tejidas:</b> Las marcas de sombra incorrectas en los cruces de máscaras ahora se ocultan automáticamente; tus ajustes manuales del editor de sombras siempre se respetan.</li>
        <li><b>Sombras de máscara en el editor de sombras:</b> Las sombras proyectadas a través de una máscara ahora aparecen en el editor de sombras de la hebra superior, para que puedas activarlas o desactivarlas como cualquier otra sombra.</li>
        <li><b>Selección de hebras más precisa:</b> Un clic ahora selecciona exactamente lo que ves: los bordes de las hebras, los extremos y los contornos de las máscaras son todos clicables, siempre se elige la hebra superior, y el resaltado al pasar el cursor siempre coincide con lo que un clic seleccionará.</li>
        <li><b>Corrección de la visibilidad de puntos de control:</b> «Mostrar puntos de control solo para la hebra seleccionada» ahora oculta solo los puntos de control; las demás hebras conservan sus cuadrados de extremo y siguen siendo movibles. Arrastrar un extremo ya no hace aparecer un punto de control sin usar.</li>
        <li><b>Ajustes de sombra preservados:</b> El estado de «sombra oculta» de una capa ya no se restablece al mover o duplicar grupos.</li>
        <li><b>Mayor estabilidad de dibujo:</b> Se corrigieron problemas internos de renderizado que podían corromper el lienzo tras un error de dibujo.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.109</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.109:</p>
    <ul>
        <li><b>Modo de bloqueio redesenhado:</b> Cada botão de camada agora mostra um pequeno cadeado no modo de bloqueio. Clique no cadeado para bloquear/desbloquear; clicar na camada simplesmente a seleciona. Fios bloqueados podem ser selecionados, mas não movidos nem usados para anexar, e Novo fio / Excluir fio continuam disponíveis (a exclusão só é bloqueada para camadas bloqueadas). O estado de bloqueio também é lembrado ao desfazer/refazer, salvar/carregar e trocar de aba.</li>
        <li><b>Opção Ocultar sombra por camada:</b> Clique com o botão direito em uma camada para impedi-la de projetar sombra sobre outros fios. A configuração é salva com o projeto e sobrevive a desfazer/refazer e às operações de grupo.</li>
        <li><b>Correção automática de sombras para máscaras entrelaçadas:</b> Marcas de sombra incorretas nos cruzamentos de máscaras agora são ocultadas automaticamente; suas configurações manuais no editor de sombras são sempre respeitadas.</li>
        <li><b>Sombras de máscara no editor de sombras:</b> Sombras projetadas através de uma máscara agora aparecem no editor de sombras do fio superior, para que você possa ativá-las ou desativá-las como qualquer outra sombra.</li>
        <li><b>Seleção de fios mais precisa:</b> Um clique agora seleciona exatamente o que você vê: bordas dos fios, extremidades e contornos das máscaras são todos clicáveis, o fio mais acima é sempre escolhido, e o destaque ao passar o mouse sempre corresponde ao que um clique selecionará.</li>
        <li><b>Correção da visibilidade dos pontos de controle:</b> «Mostrar pontos de controle apenas para o fio selecionado» agora oculta apenas os pontos de controle; os outros fios mantêm seus quadrados de extremidade e continuam móveis. Arrastar uma extremidade não faz mais aparecer um ponto de controle nunca usado.</li>
        <li><b>Configurações de sombra preservadas:</b> O estado de «sombra oculta» de uma camada não é mais redefinido ao mover ou duplicar grupos.</li>
        <li><b>Maior estabilidade de desenho:</b> Corrigidos problemas internos de renderização que podiam corromper a tela após um erro de desenho.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.109</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.109:</p>
    <ul>
        <li><b>&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05D7;&#x05D3;&#x05E9;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E7;&#x05D8;&#x05DF; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;. &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E0;&#x05D5;&#x05E2;&#x05DC;&#x05EA;/&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05EA;; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E4;&#x05E9;&#x05D5;&#x05D8; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4;. &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D0;&#x05DA; &#x05DC;&#x05D0; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;, &#x05D5;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9; / &#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05EA; &#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05D6;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; (&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4; &#x05D7;&#x05E1;&#x05D5;&#x05DE;&#x05D4; &#x05E8;&#x05E7; &#x05DC;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA;). &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8; &#x05D2;&#x05DD; &#x05D1;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;, &#x05D1;&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4;/&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05D5;&#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D1;&#x05D9;&#x05DF; &#x05DB;&#x05E8;&#x05D8;&#x05D9;&#x05E1;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05EA; &#x05E6;&#x05DC; &#x05DC;&#x05DB;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DE;&#x05E0;&#x05D5;&#x05E2; &#x05DE;&#x05DE;&#x05E0;&#x05D4; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05DC; &#x05E6;&#x05DC; &#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9;&#x05DD;. &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E9;&#x05D5;&#x05E8;&#x05D3;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05D5;&#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E9;&#x05D6;&#x05D5;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05E1;&#x05D9;&#x05DE;&#x05E0;&#x05D9; &#x05E6;&#x05DC; &#x05E9;&#x05D2;&#x05D5;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D3;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D5;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D3;&#x05E8;&#x05DA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05E0;&#x05D9;&#x05EA;&#x05DF; &#x05DC;&#x05D4;&#x05E4;&#x05E2;&#x05D9;&#x05DC; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05DD; &#x05DB;&#x05DE;&#x05D5; &#x05DB;&#x05DC; &#x05E6;&#x05DC; &#x05D0;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05E8;&#x05D5;&#x05D0;&#x05D9;&#x05DD;: &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DB;&#x05D9;&#x05E4;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05E8; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4;, &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF; &#x05D1;&#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E0;&#x05D1;&#x05D7;&#x05E8; &#x05EA;&#x05DE;&#x05D9;&#x05D3;, &#x05D5;&#x05D4;&#x05D4;&#x05D3;&#x05D2;&#x05E9;&#x05D4; &#x05D1;&#x05E8;&#x05D9;&#x05D7;&#x05D5;&#x05E3; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05EA;&#x05D5;&#x05D0;&#x05DE;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05EA;&#x05D1;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;:</b> "&#x05D4;&#x05E6;&#x05D2; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E8;&#x05E7; &#x05E2;&#x05D1;&#x05D5;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E0;&#x05D1;&#x05D7;&#x05E8;" &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E8;&#x05E7; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;; &#x05E9;&#x05D0;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05D5;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DC; &#x05E8;&#x05D9;&#x05D1;&#x05D5;&#x05E2;&#x05D9; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D5;&#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;. &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E6;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D4; &#x05D2;&#x05D5;&#x05E8;&#x05DE;&#x05EA; &#x05E2;&#x05D5;&#x05D3; &#x05DC;&#x05D4;&#x05D5;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05D4;&#x05D5;&#x05D6;&#x05D6;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E6;&#x05DC; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05DE;&#x05E6;&#x05D1; "&#x05E6;&#x05DC; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;" &#x05E9;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D5; &#x05DE;&#x05EA;&#x05D0;&#x05E4;&#x05E1; &#x05E2;&#x05D5;&#x05D3; &#x05D1;&#x05E2;&#x05EA; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05D9;&#x05E6;&#x05D9;&#x05D1;&#x05D5;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05E4;&#x05E0;&#x05D9;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E2;&#x05DC;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D5; &#x05DC;&#x05E4;&#x05D2;&#x05D5;&#x05E2; &#x05D1;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DC;&#x05D0;&#x05D7;&#x05E8; &#x05E9;&#x05D2;&#x05D9;&#x05D0;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8;.</li>
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
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.109</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires pour installer ce logiciel.</p>
    <p>Nouveautés de la version 1.109 :</p>
    <ul>
        <li><b>Mode verrouillage repensé:</b> Chaque bouton de calque affiche désormais un petit cadenas en mode verrouillage. Cliquez sur le cadenas pour verrouiller/déverrouiller ; cliquer sur le calque le sélectionne simplement. Les brins verrouillés peuvent être sélectionnés mais ni déplacés ni utilisés pour l'attache, et Nouveau brin / Supprimer le brin restent disponibles (la suppression n'est bloquée que pour les calques verrouillés). L'état de verrouillage est également conservé lors des annulations/rétablissements, de l'enregistrement/du chargement et du changement d'onglet.</li>
        <li><b>Option Masquer l'ombre par calque:</b> Faites un clic droit sur un calque pour l'empêcher de projeter une ombre sur les autres brins. Le réglage est enregistré avec votre projet et survit aux annulations/rétablissements et aux opérations de groupe.</li>
        <li><b>Correction automatique des ombres pour les masques tissés:</b> Les marques d'ombre incorrectes aux croisements des masques sont désormais masquées automatiquement ; vos réglages manuels dans l'éditeur d'ombres sont toujours respectés.</li>
        <li><b>Ombres de masque dans l'éditeur d'ombres:</b> Les ombres projetées à travers un masque apparaissent désormais dans l'éditeur d'ombres du brin supérieur, vous pouvez donc les activer ou les désactiver comme n'importe quelle autre ombre.</li>
        <li><b>Sélection de brins plus précise:</b> Un clic sélectionne désormais exactement ce que vous voyez : les bords des brins, les extrémités et les contours des masques sont tous cliquables, le brin le plus haut est toujours choisi, et la surbrillance au survol correspond toujours à ce qu'un clic sélectionnera.</li>
        <li><b>Correction de l'affichage des points de contrôle:</b> « Afficher les points de contrôle uniquement pour le brin sélectionné » ne masque plus que les points de contrôle ; les autres brins conservent leurs carrés d'extrémité et restent déplaçables. Faire glisser une extrémité ne fait plus apparaître un point de contrôle jamais utilisé.</li>
        <li><b>Réglages d'ombre préservés:</b> L'état « ombre masquée » d'un calque n'est plus réinitialisé par un déplacement ou une duplication de groupe.</li>
        <li><b>Stabilité de dessin améliorée:</b> Correction de problèmes internes de rendu qui pouvaient corrompre le canevas après une erreur de dessin.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.109</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.109:</p>
    <ul>
        <li><b>Lock Mode Redesigned:</b> Each layer button now shows a small padlock in lock mode. Click the padlock to lock/unlock; clicking the layer simply selects it. Locked strands can be selected but not moved or attached to, and New Strand / Delete Strand remain available (delete is blocked only for locked layers). The lock state is also remembered through undo/redo, save/load, and tab switching.</li>
        <li><b>Per-Layer Hide Shadow Option:</b> Right-click a layer to stop it from casting shadow onto other strands. The setting is saved with your project and survives undo/redo and group operations.</li>
        <li><b>Automatic Shadow Correction for Woven Masks:</b> Incorrect shadow marks at mask crossings are now hidden automatically; your manual Shadow Editor settings are always respected.</li>
        <li><b>Mask Shadows in the Shadow Editor:</b> Shadows cast through a mask now appear in the over-strand's Shadow Editor, so you can turn them on or off like any other shadow.</li>
        <li><b>More Accurate Strand Selection:</b> Clicking now selects exactly what you see: strand edges, end caps, and mask outlines are all clickable, the topmost strand is always picked, and the hover highlight always matches what a click will select.</li>
        <li><b>Control Point Visibility Fix:</b> "Show control points only for the selected strand" now hides only control points; other strands keep their endpoint squares and remain movable. Dragging an endpoint no longer makes an untouched control point appear.</li>
        <li><b>Shadow Settings Preserved:</b> A layer's hidden-shadow state is no longer reset by group move or duplicate operations.</li>
        <li><b>Improved Drawing Stability:</b> Fixed internal painting issues that could corrupt the canvas after a drawing error.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.109</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.109:</p>
    <ul>
        <li><b>Sperrmodus überarbeitet:</b> Jede Ebenen-Schaltfläche zeigt im Sperrmodus jetzt ein kleines Vorhängeschloss. Klicken Sie auf das Schloss zum Sperren/Entsperren; ein Klick auf die Ebene wählt sie einfach aus. Gesperrte Stränge können ausgewählt, aber nicht bewegt oder als Ansatzpunkt verwendet werden, und Neuer Strang / Strang löschen bleiben verfügbar (Löschen ist nur für gesperrte Ebenen blockiert). Der Sperrzustand bleibt auch bei Rückgängig/Wiederherstellen, Speichern/Laden und Tab-Wechsel erhalten.</li>
        <li><b>Option „Schatten ausblenden“ pro Ebene:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene, damit sie keinen Schatten mehr auf andere Stränge wirft. Die Einstellung wird mit dem Projekt gespeichert und übersteht Rückgängig/Wiederherstellen sowie Gruppenoperationen.</li>
        <li><b>Automatische Schattenkorrektur für gewebte Masken:</b> Falsche Schattenspuren an Maskenkreuzungen werden jetzt automatisch ausgeblendet; Ihre manuellen Einstellungen im Schatten-Editor werden immer respektiert.</li>
        <li><b>Maskenschatten im Schatten-Editor:</b> Schatten, die durch eine Maske geworfen werden, erscheinen jetzt im Schatten-Editor des oberen Strangs und lassen sich wie jeder andere Schatten ein- oder ausschalten.</li>
        <li><b>Präzisere Strangauswahl:</b> Ein Klick wählt jetzt genau das aus, was Sie sehen: Strangränder, Endkappen und Maskenumrisse sind alle anklickbar, der oberste Strang wird immer gewählt, und die Hervorhebung beim Überfahren entspricht immer dem, was ein Klick auswählen würde.</li>
        <li><b>Kontrollpunkt-Anzeige korrigiert:</b> „Kontrollpunkte nur für den ausgewählten Strang anzeigen“ blendet jetzt nur noch Kontrollpunkte aus; andere Stränge behalten ihre Endpunkt-Quadrate und bleiben beweglich. Das Ziehen eines Endpunkts lässt keinen unbenutzten Kontrollpunkt mehr erscheinen.</li>
        <li><b>Schatteneinstellungen bleiben erhalten:</b> Der Zustand „Schatten ausgeblendet“ einer Ebene wird durch Gruppenverschiebung oder -duplizierung nicht mehr zurückgesetzt.</li>
        <li><b>Verbesserte Zeichenstabilität:</b> Interne Renderprobleme behoben, die nach einem Zeichenfehler die Leinwand beschädigen konnten.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.109</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.109:</p>
    <ul>
        <li><b>Modalità blocco ridisegnata:</b> Ogni pulsante di livello ora mostra un piccolo lucchetto in modalità blocco. Fai clic sul lucchetto per bloccare/sbloccare; fare clic sul livello lo seleziona semplicemente. I fili bloccati possono essere selezionati ma non spostati né usati per l'attacco, e Nuovo filo / Elimina filo restano disponibili (l'eliminazione è bloccata solo per i livelli bloccati). Lo stato di blocco viene inoltre ricordato tra annulla/ripristina, salvataggio/caricamento e cambio di scheda.</li>
        <li><b>Opzione Nascondi ombra per livello:</b> Fai clic destro su un livello per impedirgli di proiettare ombra sugli altri fili. L'impostazione viene salvata con il progetto e sopravvive ad annulla/ripristina e alle operazioni di gruppo.</li>
        <li><b>Correzione automatica delle ombre per maschere intrecciate:</b> I segni d'ombra errati agli incroci delle maschere ora vengono nascosti automaticamente; le tue impostazioni manuali nell'editor ombre vengono sempre rispettate.</li>
        <li><b>Ombre delle maschere nell'editor ombre:</b> Le ombre proiettate attraverso una maschera ora appaiono nell'editor ombre del filo superiore, così puoi attivarle o disattivarle come qualsiasi altra ombra.</li>
        <li><b>Selezione dei fili più precisa:</b> Un clic ora seleziona esattamente ciò che vedi: i bordi dei fili, le estremità e i contorni delle maschere sono tutti cliccabili, viene sempre scelto il filo più in alto e l'evidenziazione al passaggio del mouse corrisponde sempre a ciò che un clic selezionerà.</li>
        <li><b>Correzione della visibilità dei punti di controllo:</b> «Mostra i punti di controllo solo per il filo selezionato» ora nasconde solo i punti di controllo; gli altri fili mantengono i loro quadrati alle estremità e restano spostabili. Trascinare un'estremità non fa più apparire un punto di controllo mai utilizzato.</li>
        <li><b>Impostazioni ombra preservate:</b> Lo stato «ombra nascosta» di un livello non viene più azzerato da spostamenti o duplicazioni di gruppo.</li>
        <li><b>Maggiore stabilità di disegno:</b> Risolti problemi interni di rendering che potevano corrompere la tela dopo un errore di disegno.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.109</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.109:</p>
    <ul>
        <li><b>Modo de bloqueo rediseñado:</b> Cada botón de capa ahora muestra un pequeño candado en modo de bloqueo. Haz clic en el candado para bloquear/desbloquear; hacer clic en la capa simplemente la selecciona. Las hebras bloqueadas pueden seleccionarse pero no moverse ni usarse para adjuntar, y Nueva hebra / Eliminar hebra siguen disponibles (la eliminación solo se bloquea para capas bloqueadas). El estado de bloqueo también se recuerda al deshacer/rehacer, guardar/cargar y cambiar de pestaña.</li>
        <li><b>Opción Ocultar sombra por capa:</b> Haz clic derecho en una capa para impedir que proyecte sombra sobre otras hebras. El ajuste se guarda con tu proyecto y sobrevive a deshacer/rehacer y a las operaciones de grupo.</li>
        <li><b>Corrección automática de sombras para máscaras tejidas:</b> Las marcas de sombra incorrectas en los cruces de máscaras ahora se ocultan automáticamente; tus ajustes manuales del editor de sombras siempre se respetan.</li>
        <li><b>Sombras de máscara en el editor de sombras:</b> Las sombras proyectadas a través de una máscara ahora aparecen en el editor de sombras de la hebra superior, para que puedas activarlas o desactivarlas como cualquier otra sombra.</li>
        <li><b>Selección de hebras más precisa:</b> Un clic ahora selecciona exactamente lo que ves: los bordes de las hebras, los extremos y los contornos de las máscaras son todos clicables, siempre se elige la hebra superior, y el resaltado al pasar el cursor siempre coincide con lo que un clic seleccionará.</li>
        <li><b>Corrección de la visibilidad de puntos de control:</b> «Mostrar puntos de control solo para la hebra seleccionada» ahora oculta solo los puntos de control; las demás hebras conservan sus cuadrados de extremo y siguen siendo movibles. Arrastrar un extremo ya no hace aparecer un punto de control sin usar.</li>
        <li><b>Ajustes de sombra preservados:</b> El estado de «sombra oculta» de una capa ya no se restablece al mover o duplicar grupos.</li>
        <li><b>Mayor estabilidad de dibujo:</b> Se corrigieron problemas internos de renderizado que podían corromper el lienzo tras un error de dibujo.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.109</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.109:</p>
    <ul>
        <li><b>Modo de bloqueio redesenhado:</b> Cada botão de camada agora mostra um pequeno cadeado no modo de bloqueio. Clique no cadeado para bloquear/desbloquear; clicar na camada simplesmente a seleciona. Fios bloqueados podem ser selecionados, mas não movidos nem usados para anexar, e Novo fio / Excluir fio continuam disponíveis (a exclusão só é bloqueada para camadas bloqueadas). O estado de bloqueio também é lembrado ao desfazer/refazer, salvar/carregar e trocar de aba.</li>
        <li><b>Opção Ocultar sombra por camada:</b> Clique com o botão direito em uma camada para impedi-la de projetar sombra sobre outros fios. A configuração é salva com o projeto e sobrevive a desfazer/refazer e às operações de grupo.</li>
        <li><b>Correção automática de sombras para máscaras entrelaçadas:</b> Marcas de sombra incorretas nos cruzamentos de máscaras agora são ocultadas automaticamente; suas configurações manuais no editor de sombras são sempre respeitadas.</li>
        <li><b>Sombras de máscara no editor de sombras:</b> Sombras projetadas através de uma máscara agora aparecem no editor de sombras do fio superior, para que você possa ativá-las ou desativá-las como qualquer outra sombra.</li>
        <li><b>Seleção de fios mais precisa:</b> Um clique agora seleciona exatamente o que você vê: bordas dos fios, extremidades e contornos das máscaras são todos clicáveis, o fio mais acima é sempre escolhido, e o destaque ao passar o mouse sempre corresponde ao que um clique selecionará.</li>
        <li><b>Correção da visibilidade dos pontos de controle:</b> «Mostrar pontos de controle apenas para o fio selecionado» agora oculta apenas os pontos de controle; os outros fios mantêm seus quadrados de extremidade e continuam móveis. Arrastar uma extremidade não faz mais aparecer um ponto de controle nunca usado.</li>
        <li><b>Configurações de sombra preservadas:</b> O estado de «sombra oculta» de uma camada não é mais redefinido ao mover ou duplicar grupos.</li>
        <li><b>Maior estabilidade de desenho:</b> Corrigidos problemas internos de renderização que podiam corromper a tela após um erro de desenho.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.109</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.109:</p>
    <ul>
        <li><b>&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05D7;&#x05D3;&#x05E9;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E7;&#x05D8;&#x05DF; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;. &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E0;&#x05D5;&#x05E2;&#x05DC;&#x05EA;/&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05EA;; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E4;&#x05E9;&#x05D5;&#x05D8; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4;. &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D0;&#x05DA; &#x05DC;&#x05D0; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;, &#x05D5;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9; / &#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05EA; &#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05D6;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; (&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4; &#x05D7;&#x05E1;&#x05D5;&#x05DE;&#x05D4; &#x05E8;&#x05E7; &#x05DC;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA;). &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8; &#x05D2;&#x05DD; &#x05D1;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;, &#x05D1;&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4;/&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05D5;&#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D1;&#x05D9;&#x05DF; &#x05DB;&#x05E8;&#x05D8;&#x05D9;&#x05E1;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05EA; &#x05E6;&#x05DC; &#x05DC;&#x05DB;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DE;&#x05E0;&#x05D5;&#x05E2; &#x05DE;&#x05DE;&#x05E0;&#x05D4; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05DC; &#x05E6;&#x05DC; &#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9;&#x05DD;. &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E9;&#x05D5;&#x05E8;&#x05D3;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05D5;&#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E9;&#x05D6;&#x05D5;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05E1;&#x05D9;&#x05DE;&#x05E0;&#x05D9; &#x05E6;&#x05DC; &#x05E9;&#x05D2;&#x05D5;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D3;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D5;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D3;&#x05E8;&#x05DA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05E0;&#x05D9;&#x05EA;&#x05DF; &#x05DC;&#x05D4;&#x05E4;&#x05E2;&#x05D9;&#x05DC; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05DD; &#x05DB;&#x05DE;&#x05D5; &#x05DB;&#x05DC; &#x05E6;&#x05DC; &#x05D0;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05E8;&#x05D5;&#x05D0;&#x05D9;&#x05DD;: &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DB;&#x05D9;&#x05E4;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05E8; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4;, &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF; &#x05D1;&#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E0;&#x05D1;&#x05D7;&#x05E8; &#x05EA;&#x05DE;&#x05D9;&#x05D3;, &#x05D5;&#x05D4;&#x05D4;&#x05D3;&#x05D2;&#x05E9;&#x05D4; &#x05D1;&#x05E8;&#x05D9;&#x05D7;&#x05D5;&#x05E3; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05EA;&#x05D5;&#x05D0;&#x05DE;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05EA;&#x05D1;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;:</b> "&#x05D4;&#x05E6;&#x05D2; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E8;&#x05E7; &#x05E2;&#x05D1;&#x05D5;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E0;&#x05D1;&#x05D7;&#x05E8;" &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E8;&#x05E7; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;; &#x05E9;&#x05D0;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05D5;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DC; &#x05E8;&#x05D9;&#x05D1;&#x05D5;&#x05E2;&#x05D9; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D5;&#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;. &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E6;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D4; &#x05D2;&#x05D5;&#x05E8;&#x05DE;&#x05EA; &#x05E2;&#x05D5;&#x05D3; &#x05DC;&#x05D4;&#x05D5;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05D4;&#x05D5;&#x05D6;&#x05D6;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E6;&#x05DC; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05DE;&#x05E6;&#x05D1; "&#x05E6;&#x05DC; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;" &#x05E9;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D5; &#x05DE;&#x05EA;&#x05D0;&#x05E4;&#x05E1; &#x05E2;&#x05D5;&#x05D3; &#x05D1;&#x05E2;&#x05EA; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05D9;&#x05E6;&#x05D9;&#x05D1;&#x05D5;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05E4;&#x05E0;&#x05D9;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E2;&#x05DC;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D5; &#x05DC;&#x05E4;&#x05D2;&#x05D5;&#x05E2; &#x05D1;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DC;&#x05D0;&#x05D7;&#x05E8; &#x05E9;&#x05D2;&#x05D9;&#x05D0;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8;.</li>
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
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.109</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.109:</p>
    <ul>
        <li><b>Sperrmodus überarbeitet:</b> Jede Ebenen-Schaltfläche zeigt im Sperrmodus jetzt ein kleines Vorhängeschloss. Klicken Sie auf das Schloss zum Sperren/Entsperren; ein Klick auf die Ebene wählt sie einfach aus. Gesperrte Stränge können ausgewählt, aber nicht bewegt oder als Ansatzpunkt verwendet werden, und Neuer Strang / Strang löschen bleiben verfügbar (Löschen ist nur für gesperrte Ebenen blockiert). Der Sperrzustand bleibt auch bei Rückgängig/Wiederherstellen, Speichern/Laden und Tab-Wechsel erhalten.</li>
        <li><b>Option „Schatten ausblenden“ pro Ebene:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene, damit sie keinen Schatten mehr auf andere Stränge wirft. Die Einstellung wird mit dem Projekt gespeichert und übersteht Rückgängig/Wiederherstellen sowie Gruppenoperationen.</li>
        <li><b>Automatische Schattenkorrektur für gewebte Masken:</b> Falsche Schattenspuren an Maskenkreuzungen werden jetzt automatisch ausgeblendet; Ihre manuellen Einstellungen im Schatten-Editor werden immer respektiert.</li>
        <li><b>Maskenschatten im Schatten-Editor:</b> Schatten, die durch eine Maske geworfen werden, erscheinen jetzt im Schatten-Editor des oberen Strangs und lassen sich wie jeder andere Schatten ein- oder ausschalten.</li>
        <li><b>Präzisere Strangauswahl:</b> Ein Klick wählt jetzt genau das aus, was Sie sehen: Strangränder, Endkappen und Maskenumrisse sind alle anklickbar, der oberste Strang wird immer gewählt, und die Hervorhebung beim Überfahren entspricht immer dem, was ein Klick auswählen würde.</li>
        <li><b>Kontrollpunkt-Anzeige korrigiert:</b> „Kontrollpunkte nur für den ausgewählten Strang anzeigen“ blendet jetzt nur noch Kontrollpunkte aus; andere Stränge behalten ihre Endpunkt-Quadrate und bleiben beweglich. Das Ziehen eines Endpunkts lässt keinen unbenutzten Kontrollpunkt mehr erscheinen.</li>
        <li><b>Schatteneinstellungen bleiben erhalten:</b> Der Zustand „Schatten ausgeblendet“ einer Ebene wird durch Gruppenverschiebung oder -duplizierung nicht mehr zurückgesetzt.</li>
        <li><b>Verbesserte Zeichenstabilität:</b> Interne Renderprobleme behoben, die nach einem Zeichenfehler die Leinwand beschädigen konnten.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.109</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.109:</p>
    <ul>
        <li><b>Lock Mode Redesigned:</b> Each layer button now shows a small padlock in lock mode. Click the padlock to lock/unlock; clicking the layer simply selects it. Locked strands can be selected but not moved or attached to, and New Strand / Delete Strand remain available (delete is blocked only for locked layers). The lock state is also remembered through undo/redo, save/load, and tab switching.</li>
        <li><b>Per-Layer Hide Shadow Option:</b> Right-click a layer to stop it from casting shadow onto other strands. The setting is saved with your project and survives undo/redo and group operations.</li>
        <li><b>Automatic Shadow Correction for Woven Masks:</b> Incorrect shadow marks at mask crossings are now hidden automatically; your manual Shadow Editor settings are always respected.</li>
        <li><b>Mask Shadows in the Shadow Editor:</b> Shadows cast through a mask now appear in the over-strand's Shadow Editor, so you can turn them on or off like any other shadow.</li>
        <li><b>More Accurate Strand Selection:</b> Clicking now selects exactly what you see: strand edges, end caps, and mask outlines are all clickable, the topmost strand is always picked, and the hover highlight always matches what a click will select.</li>
        <li><b>Control Point Visibility Fix:</b> "Show control points only for the selected strand" now hides only control points; other strands keep their endpoint squares and remain movable. Dragging an endpoint no longer makes an untouched control point appear.</li>
        <li><b>Shadow Settings Preserved:</b> A layer's hidden-shadow state is no longer reset by group move or duplicate operations.</li>
        <li><b>Improved Drawing Stability:</b> Fixed internal painting issues that could corrupt the canvas after a drawing error.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.109</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.109 :</p>
    <ul>
        <li><b>Mode verrouillage repensé:</b> Chaque bouton de calque affiche désormais un petit cadenas en mode verrouillage. Cliquez sur le cadenas pour verrouiller/déverrouiller ; cliquer sur le calque le sélectionne simplement. Les brins verrouillés peuvent être sélectionnés mais ni déplacés ni utilisés pour l'attache, et Nouveau brin / Supprimer le brin restent disponibles (la suppression n'est bloquée que pour les calques verrouillés). L'état de verrouillage est également conservé lors des annulations/rétablissements, de l'enregistrement/du chargement et du changement d'onglet.</li>
        <li><b>Option Masquer l'ombre par calque:</b> Faites un clic droit sur un calque pour l'empêcher de projeter une ombre sur les autres brins. Le réglage est enregistré avec votre projet et survit aux annulations/rétablissements et aux opérations de groupe.</li>
        <li><b>Correction automatique des ombres pour les masques tissés:</b> Les marques d'ombre incorrectes aux croisements des masques sont désormais masquées automatiquement ; vos réglages manuels dans l'éditeur d'ombres sont toujours respectés.</li>
        <li><b>Ombres de masque dans l'éditeur d'ombres:</b> Les ombres projetées à travers un masque apparaissent désormais dans l'éditeur d'ombres du brin supérieur, vous pouvez donc les activer ou les désactiver comme n'importe quelle autre ombre.</li>
        <li><b>Sélection de brins plus précise:</b> Un clic sélectionne désormais exactement ce que vous voyez : les bords des brins, les extrémités et les contours des masques sont tous cliquables, le brin le plus haut est toujours choisi, et la surbrillance au survol correspond toujours à ce qu'un clic sélectionnera.</li>
        <li><b>Correction de l'affichage des points de contrôle:</b> « Afficher les points de contrôle uniquement pour le brin sélectionné » ne masque plus que les points de contrôle ; les autres brins conservent leurs carrés d'extrémité et restent déplaçables. Faire glisser une extrémité ne fait plus apparaître un point de contrôle jamais utilisé.</li>
        <li><b>Réglages d'ombre préservés:</b> L'état « ombre masquée » d'un calque n'est plus réinitialisé par un déplacement ou une duplication de groupe.</li>
        <li><b>Stabilité de dessin améliorée:</b> Correction de problèmes internes de rendu qui pouvaient corrompre le canevas après une erreur de dessin.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.109</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.109:</p>
    <ul>
        <li><b>Modalità blocco ridisegnata:</b> Ogni pulsante di livello ora mostra un piccolo lucchetto in modalità blocco. Fai clic sul lucchetto per bloccare/sbloccare; fare clic sul livello lo seleziona semplicemente. I fili bloccati possono essere selezionati ma non spostati né usati per l'attacco, e Nuovo filo / Elimina filo restano disponibili (l'eliminazione è bloccata solo per i livelli bloccati). Lo stato di blocco viene inoltre ricordato tra annulla/ripristina, salvataggio/caricamento e cambio di scheda.</li>
        <li><b>Opzione Nascondi ombra per livello:</b> Fai clic destro su un livello per impedirgli di proiettare ombra sugli altri fili. L'impostazione viene salvata con il progetto e sopravvive ad annulla/ripristina e alle operazioni di gruppo.</li>
        <li><b>Correzione automatica delle ombre per maschere intrecciate:</b> I segni d'ombra errati agli incroci delle maschere ora vengono nascosti automaticamente; le tue impostazioni manuali nell'editor ombre vengono sempre rispettate.</li>
        <li><b>Ombre delle maschere nell'editor ombre:</b> Le ombre proiettate attraverso una maschera ora appaiono nell'editor ombre del filo superiore, così puoi attivarle o disattivarle come qualsiasi altra ombra.</li>
        <li><b>Selezione dei fili più precisa:</b> Un clic ora seleziona esattamente ciò che vedi: i bordi dei fili, le estremità e i contorni delle maschere sono tutti cliccabili, viene sempre scelto il filo più in alto e l'evidenziazione al passaggio del mouse corrisponde sempre a ciò che un clic selezionerà.</li>
        <li><b>Correzione della visibilità dei punti di controllo:</b> «Mostra i punti di controllo solo per il filo selezionato» ora nasconde solo i punti di controllo; gli altri fili mantengono i loro quadrati alle estremità e restano spostabili. Trascinare un'estremità non fa più apparire un punto di controllo mai utilizzato.</li>
        <li><b>Impostazioni ombra preservate:</b> Lo stato «ombra nascosta» di un livello non viene più azzerato da spostamenti o duplicazioni di gruppo.</li>
        <li><b>Maggiore stabilità di disegno:</b> Risolti problemi interni di rendering che potevano corrompere la tela dopo un errore di disegno.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.109</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.109:</p>
    <ul>
        <li><b>Modo de bloqueo rediseñado:</b> Cada botón de capa ahora muestra un pequeño candado en modo de bloqueo. Haz clic en el candado para bloquear/desbloquear; hacer clic en la capa simplemente la selecciona. Las hebras bloqueadas pueden seleccionarse pero no moverse ni usarse para adjuntar, y Nueva hebra / Eliminar hebra siguen disponibles (la eliminación solo se bloquea para capas bloqueadas). El estado de bloqueo también se recuerda al deshacer/rehacer, guardar/cargar y cambiar de pestaña.</li>
        <li><b>Opción Ocultar sombra por capa:</b> Haz clic derecho en una capa para impedir que proyecte sombra sobre otras hebras. El ajuste se guarda con tu proyecto y sobrevive a deshacer/rehacer y a las operaciones de grupo.</li>
        <li><b>Corrección automática de sombras para máscaras tejidas:</b> Las marcas de sombra incorrectas en los cruces de máscaras ahora se ocultan automáticamente; tus ajustes manuales del editor de sombras siempre se respetan.</li>
        <li><b>Sombras de máscara en el editor de sombras:</b> Las sombras proyectadas a través de una máscara ahora aparecen en el editor de sombras de la hebra superior, para que puedas activarlas o desactivarlas como cualquier otra sombra.</li>
        <li><b>Selección de hebras más precisa:</b> Un clic ahora selecciona exactamente lo que ves: los bordes de las hebras, los extremos y los contornos de las máscaras son todos clicables, siempre se elige la hebra superior, y el resaltado al pasar el cursor siempre coincide con lo que un clic seleccionará.</li>
        <li><b>Corrección de la visibilidad de puntos de control:</b> «Mostrar puntos de control solo para la hebra seleccionada» ahora oculta solo los puntos de control; las demás hebras conservan sus cuadrados de extremo y siguen siendo movibles. Arrastrar un extremo ya no hace aparecer un punto de control sin usar.</li>
        <li><b>Ajustes de sombra preservados:</b> El estado de «sombra oculta» de una capa ya no se restablece al mover o duplicar grupos.</li>
        <li><b>Mayor estabilidad de dibujo:</b> Se corrigieron problemas internos de renderizado que podían corromper el lienzo tras un error de dibujo.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.109</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.109:</p>
    <ul>
        <li><b>Modo de bloqueio redesenhado:</b> Cada botão de camada agora mostra um pequeno cadeado no modo de bloqueio. Clique no cadeado para bloquear/desbloquear; clicar na camada simplesmente a seleciona. Fios bloqueados podem ser selecionados, mas não movidos nem usados para anexar, e Novo fio / Excluir fio continuam disponíveis (a exclusão só é bloqueada para camadas bloqueadas). O estado de bloqueio também é lembrado ao desfazer/refazer, salvar/carregar e trocar de aba.</li>
        <li><b>Opção Ocultar sombra por camada:</b> Clique com o botão direito em uma camada para impedi-la de projetar sombra sobre outros fios. A configuração é salva com o projeto e sobrevive a desfazer/refazer e às operações de grupo.</li>
        <li><b>Correção automática de sombras para máscaras entrelaçadas:</b> Marcas de sombra incorretas nos cruzamentos de máscaras agora são ocultadas automaticamente; suas configurações manuais no editor de sombras são sempre respeitadas.</li>
        <li><b>Sombras de máscara no editor de sombras:</b> Sombras projetadas através de uma máscara agora aparecem no editor de sombras do fio superior, para que você possa ativá-las ou desativá-las como qualquer outra sombra.</li>
        <li><b>Seleção de fios mais precisa:</b> Um clique agora seleciona exatamente o que você vê: bordas dos fios, extremidades e contornos das máscaras são todos clicáveis, o fio mais acima é sempre escolhido, e o destaque ao passar o mouse sempre corresponde ao que um clique selecionará.</li>
        <li><b>Correção da visibilidade dos pontos de controle:</b> «Mostrar pontos de controle apenas para o fio selecionado» agora oculta apenas os pontos de controle; os outros fios mantêm seus quadrados de extremidade e continuam móveis. Arrastar uma extremidade não faz mais aparecer um ponto de controle nunca usado.</li>
        <li><b>Configurações de sombra preservadas:</b> O estado de «sombra oculta» de uma camada não é mais redefinido ao mover ou duplicar grupos.</li>
        <li><b>Maior estabilidade de desenho:</b> Corrigidos problemas internos de renderização que podiam corromper a tela após um erro de desenho.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.109</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.109:</p>
    <ul>
        <li><b>&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05D7;&#x05D3;&#x05E9;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E7;&#x05D8;&#x05DF; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;. &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E0;&#x05D5;&#x05E2;&#x05DC;&#x05EA;/&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05EA;; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E4;&#x05E9;&#x05D5;&#x05D8; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4;. &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D0;&#x05DA; &#x05DC;&#x05D0; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;, &#x05D5;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9; / &#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05EA; &#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05D6;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; (&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4; &#x05D7;&#x05E1;&#x05D5;&#x05DE;&#x05D4; &#x05E8;&#x05E7; &#x05DC;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA;). &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8; &#x05D2;&#x05DD; &#x05D1;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;, &#x05D1;&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4;/&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05D5;&#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D1;&#x05D9;&#x05DF; &#x05DB;&#x05E8;&#x05D8;&#x05D9;&#x05E1;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05EA; &#x05E6;&#x05DC; &#x05DC;&#x05DB;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DE;&#x05E0;&#x05D5;&#x05E2; &#x05DE;&#x05DE;&#x05E0;&#x05D4; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05DC; &#x05E6;&#x05DC; &#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9;&#x05DD;. &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E9;&#x05D5;&#x05E8;&#x05D3;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05D5;&#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E9;&#x05D6;&#x05D5;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05E1;&#x05D9;&#x05DE;&#x05E0;&#x05D9; &#x05E6;&#x05DC; &#x05E9;&#x05D2;&#x05D5;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D3;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D5;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D3;&#x05E8;&#x05DA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05E0;&#x05D9;&#x05EA;&#x05DF; &#x05DC;&#x05D4;&#x05E4;&#x05E2;&#x05D9;&#x05DC; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05DD; &#x05DB;&#x05DE;&#x05D5; &#x05DB;&#x05DC; &#x05E6;&#x05DC; &#x05D0;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05E8;&#x05D5;&#x05D0;&#x05D9;&#x05DD;: &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DB;&#x05D9;&#x05E4;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05E8; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4;, &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF; &#x05D1;&#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E0;&#x05D1;&#x05D7;&#x05E8; &#x05EA;&#x05DE;&#x05D9;&#x05D3;, &#x05D5;&#x05D4;&#x05D4;&#x05D3;&#x05D2;&#x05E9;&#x05D4; &#x05D1;&#x05E8;&#x05D9;&#x05D7;&#x05D5;&#x05E3; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05EA;&#x05D5;&#x05D0;&#x05DE;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05EA;&#x05D1;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;:</b> "&#x05D4;&#x05E6;&#x05D2; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E8;&#x05E7; &#x05E2;&#x05D1;&#x05D5;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E0;&#x05D1;&#x05D7;&#x05E8;" &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E8;&#x05E7; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;; &#x05E9;&#x05D0;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05D5;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DC; &#x05E8;&#x05D9;&#x05D1;&#x05D5;&#x05E2;&#x05D9; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D5;&#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;. &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E6;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D4; &#x05D2;&#x05D5;&#x05E8;&#x05DE;&#x05EA; &#x05E2;&#x05D5;&#x05D3; &#x05DC;&#x05D4;&#x05D5;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05D4;&#x05D5;&#x05D6;&#x05D6;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E6;&#x05DC; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05DE;&#x05E6;&#x05D1; "&#x05E6;&#x05DC; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;" &#x05E9;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D5; &#x05DE;&#x05EA;&#x05D0;&#x05E4;&#x05E1; &#x05E2;&#x05D5;&#x05D3; &#x05D1;&#x05E2;&#x05EA; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05D9;&#x05E6;&#x05D9;&#x05D1;&#x05D5;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05E4;&#x05E0;&#x05D9;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E2;&#x05DC;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D5; &#x05DC;&#x05E4;&#x05D2;&#x05D5;&#x05E2; &#x05D1;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DC;&#x05D0;&#x05D7;&#x05E8; &#x05E9;&#x05D2;&#x05D9;&#x05D0;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8;.</li>
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
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.109</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.109:</p>
    <ul>
        <li><b>Modalità blocco ridisegnata:</b> Ogni pulsante di livello ora mostra un piccolo lucchetto in modalità blocco. Fai clic sul lucchetto per bloccare/sbloccare; fare clic sul livello lo seleziona semplicemente. I fili bloccati possono essere selezionati ma non spostati né usati per l'attacco, e Nuovo filo / Elimina filo restano disponibili (l'eliminazione è bloccata solo per i livelli bloccati). Lo stato di blocco viene inoltre ricordato tra annulla/ripristina, salvataggio/caricamento e cambio di scheda.</li>
        <li><b>Opzione Nascondi ombra per livello:</b> Fai clic destro su un livello per impedirgli di proiettare ombra sugli altri fili. L'impostazione viene salvata con il progetto e sopravvive ad annulla/ripristina e alle operazioni di gruppo.</li>
        <li><b>Correzione automatica delle ombre per maschere intrecciate:</b> I segni d'ombra errati agli incroci delle maschere ora vengono nascosti automaticamente; le tue impostazioni manuali nell'editor ombre vengono sempre rispettate.</li>
        <li><b>Ombre delle maschere nell'editor ombre:</b> Le ombre proiettate attraverso una maschera ora appaiono nell'editor ombre del filo superiore, così puoi attivarle o disattivarle come qualsiasi altra ombra.</li>
        <li><b>Selezione dei fili più precisa:</b> Un clic ora seleziona esattamente ciò che vedi: i bordi dei fili, le estremità e i contorni delle maschere sono tutti cliccabili, viene sempre scelto il filo più in alto e l'evidenziazione al passaggio del mouse corrisponde sempre a ciò che un clic selezionerà.</li>
        <li><b>Correzione della visibilità dei punti di controllo:</b> «Mostra i punti di controllo solo per il filo selezionato» ora nasconde solo i punti di controllo; gli altri fili mantengono i loro quadrati alle estremità e restano spostabili. Trascinare un'estremità non fa più apparire un punto di controllo mai utilizzato.</li>
        <li><b>Impostazioni ombra preservate:</b> Lo stato «ombra nascosta» di un livello non viene più azzerato da spostamenti o duplicazioni di gruppo.</li>
        <li><b>Maggiore stabilità di disegno:</b> Risolti problemi interni di rendering che potevano corrompere la tela dopo un errore di disegno.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.109</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.109:</p>
    <ul>
        <li><b>Lock Mode Redesigned:</b> Each layer button now shows a small padlock in lock mode. Click the padlock to lock/unlock; clicking the layer simply selects it. Locked strands can be selected but not moved or attached to, and New Strand / Delete Strand remain available (delete is blocked only for locked layers). The lock state is also remembered through undo/redo, save/load, and tab switching.</li>
        <li><b>Per-Layer Hide Shadow Option:</b> Right-click a layer to stop it from casting shadow onto other strands. The setting is saved with your project and survives undo/redo and group operations.</li>
        <li><b>Automatic Shadow Correction for Woven Masks:</b> Incorrect shadow marks at mask crossings are now hidden automatically; your manual Shadow Editor settings are always respected.</li>
        <li><b>Mask Shadows in the Shadow Editor:</b> Shadows cast through a mask now appear in the over-strand's Shadow Editor, so you can turn them on or off like any other shadow.</li>
        <li><b>More Accurate Strand Selection:</b> Clicking now selects exactly what you see: strand edges, end caps, and mask outlines are all clickable, the topmost strand is always picked, and the hover highlight always matches what a click will select.</li>
        <li><b>Control Point Visibility Fix:</b> "Show control points only for the selected strand" now hides only control points; other strands keep their endpoint squares and remain movable. Dragging an endpoint no longer makes an untouched control point appear.</li>
        <li><b>Shadow Settings Preserved:</b> A layer's hidden-shadow state is no longer reset by group move or duplicate operations.</li>
        <li><b>Improved Drawing Stability:</b> Fixed internal painting issues that could corrupt the canvas after a drawing error.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.109</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.109:</p>
    <ul>
        <li><b>Sperrmodus überarbeitet:</b> Jede Ebenen-Schaltfläche zeigt im Sperrmodus jetzt ein kleines Vorhängeschloss. Klicken Sie auf das Schloss zum Sperren/Entsperren; ein Klick auf die Ebene wählt sie einfach aus. Gesperrte Stränge können ausgewählt, aber nicht bewegt oder als Ansatzpunkt verwendet werden, und Neuer Strang / Strang löschen bleiben verfügbar (Löschen ist nur für gesperrte Ebenen blockiert). Der Sperrzustand bleibt auch bei Rückgängig/Wiederherstellen, Speichern/Laden und Tab-Wechsel erhalten.</li>
        <li><b>Option „Schatten ausblenden“ pro Ebene:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene, damit sie keinen Schatten mehr auf andere Stränge wirft. Die Einstellung wird mit dem Projekt gespeichert und übersteht Rückgängig/Wiederherstellen sowie Gruppenoperationen.</li>
        <li><b>Automatische Schattenkorrektur für gewebte Masken:</b> Falsche Schattenspuren an Maskenkreuzungen werden jetzt automatisch ausgeblendet; Ihre manuellen Einstellungen im Schatten-Editor werden immer respektiert.</li>
        <li><b>Maskenschatten im Schatten-Editor:</b> Schatten, die durch eine Maske geworfen werden, erscheinen jetzt im Schatten-Editor des oberen Strangs und lassen sich wie jeder andere Schatten ein- oder ausschalten.</li>
        <li><b>Präzisere Strangauswahl:</b> Ein Klick wählt jetzt genau das aus, was Sie sehen: Strangränder, Endkappen und Maskenumrisse sind alle anklickbar, der oberste Strang wird immer gewählt, und die Hervorhebung beim Überfahren entspricht immer dem, was ein Klick auswählen würde.</li>
        <li><b>Kontrollpunkt-Anzeige korrigiert:</b> „Kontrollpunkte nur für den ausgewählten Strang anzeigen“ blendet jetzt nur noch Kontrollpunkte aus; andere Stränge behalten ihre Endpunkt-Quadrate und bleiben beweglich. Das Ziehen eines Endpunkts lässt keinen unbenutzten Kontrollpunkt mehr erscheinen.</li>
        <li><b>Schatteneinstellungen bleiben erhalten:</b> Der Zustand „Schatten ausgeblendet“ einer Ebene wird durch Gruppenverschiebung oder -duplizierung nicht mehr zurückgesetzt.</li>
        <li><b>Verbesserte Zeichenstabilität:</b> Interne Renderprobleme behoben, die nach einem Zeichenfehler die Leinwand beschädigen konnten.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.109</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.109 :</p>
    <ul>
        <li><b>Mode verrouillage repensé:</b> Chaque bouton de calque affiche désormais un petit cadenas en mode verrouillage. Cliquez sur le cadenas pour verrouiller/déverrouiller ; cliquer sur le calque le sélectionne simplement. Les brins verrouillés peuvent être sélectionnés mais ni déplacés ni utilisés pour l'attache, et Nouveau brin / Supprimer le brin restent disponibles (la suppression n'est bloquée que pour les calques verrouillés). L'état de verrouillage est également conservé lors des annulations/rétablissements, de l'enregistrement/du chargement et du changement d'onglet.</li>
        <li><b>Option Masquer l'ombre par calque:</b> Faites un clic droit sur un calque pour l'empêcher de projeter une ombre sur les autres brins. Le réglage est enregistré avec votre projet et survit aux annulations/rétablissements et aux opérations de groupe.</li>
        <li><b>Correction automatique des ombres pour les masques tissés:</b> Les marques d'ombre incorrectes aux croisements des masques sont désormais masquées automatiquement ; vos réglages manuels dans l'éditeur d'ombres sont toujours respectés.</li>
        <li><b>Ombres de masque dans l'éditeur d'ombres:</b> Les ombres projetées à travers un masque apparaissent désormais dans l'éditeur d'ombres du brin supérieur, vous pouvez donc les activer ou les désactiver comme n'importe quelle autre ombre.</li>
        <li><b>Sélection de brins plus précise:</b> Un clic sélectionne désormais exactement ce que vous voyez : les bords des brins, les extrémités et les contours des masques sont tous cliquables, le brin le plus haut est toujours choisi, et la surbrillance au survol correspond toujours à ce qu'un clic sélectionnera.</li>
        <li><b>Correction de l'affichage des points de contrôle:</b> « Afficher les points de contrôle uniquement pour le brin sélectionné » ne masque plus que les points de contrôle ; les autres brins conservent leurs carrés d'extrémité et restent déplaçables. Faire glisser une extrémité ne fait plus apparaître un point de contrôle jamais utilisé.</li>
        <li><b>Réglages d'ombre préservés:</b> L'état « ombre masquée » d'un calque n'est plus réinitialisé par un déplacement ou une duplication de groupe.</li>
        <li><b>Stabilité de dessin améliorée:</b> Correction de problèmes internes de rendu qui pouvaient corrompre le canevas après une erreur de dessin.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.109</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.109:</p>
    <ul>
        <li><b>Modo de bloqueo rediseñado:</b> Cada botón de capa ahora muestra un pequeño candado en modo de bloqueo. Haz clic en el candado para bloquear/desbloquear; hacer clic en la capa simplemente la selecciona. Las hebras bloqueadas pueden seleccionarse pero no moverse ni usarse para adjuntar, y Nueva hebra / Eliminar hebra siguen disponibles (la eliminación solo se bloquea para capas bloqueadas). El estado de bloqueo también se recuerda al deshacer/rehacer, guardar/cargar y cambiar de pestaña.</li>
        <li><b>Opción Ocultar sombra por capa:</b> Haz clic derecho en una capa para impedir que proyecte sombra sobre otras hebras. El ajuste se guarda con tu proyecto y sobrevive a deshacer/rehacer y a las operaciones de grupo.</li>
        <li><b>Corrección automática de sombras para máscaras tejidas:</b> Las marcas de sombra incorrectas en los cruces de máscaras ahora se ocultan automáticamente; tus ajustes manuales del editor de sombras siempre se respetan.</li>
        <li><b>Sombras de máscara en el editor de sombras:</b> Las sombras proyectadas a través de una máscara ahora aparecen en el editor de sombras de la hebra superior, para que puedas activarlas o desactivarlas como cualquier otra sombra.</li>
        <li><b>Selección de hebras más precisa:</b> Un clic ahora selecciona exactamente lo que ves: los bordes de las hebras, los extremos y los contornos de las máscaras son todos clicables, siempre se elige la hebra superior, y el resaltado al pasar el cursor siempre coincide con lo que un clic seleccionará.</li>
        <li><b>Corrección de la visibilidad de puntos de control:</b> «Mostrar puntos de control solo para la hebra seleccionada» ahora oculta solo los puntos de control; las demás hebras conservan sus cuadrados de extremo y siguen siendo movibles. Arrastrar un extremo ya no hace aparecer un punto de control sin usar.</li>
        <li><b>Ajustes de sombra preservados:</b> El estado de «sombra oculta» de una capa ya no se restablece al mover o duplicar grupos.</li>
        <li><b>Mayor estabilidad de dibujo:</b> Se corrigieron problemas internos de renderizado que podían corromper el lienzo tras un error de dibujo.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.109</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.109:</p>
    <ul>
        <li><b>Modo de bloqueio redesenhado:</b> Cada botão de camada agora mostra um pequeno cadeado no modo de bloqueio. Clique no cadeado para bloquear/desbloquear; clicar na camada simplesmente a seleciona. Fios bloqueados podem ser selecionados, mas não movidos nem usados para anexar, e Novo fio / Excluir fio continuam disponíveis (a exclusão só é bloqueada para camadas bloqueadas). O estado de bloqueio também é lembrado ao desfazer/refazer, salvar/carregar e trocar de aba.</li>
        <li><b>Opção Ocultar sombra por camada:</b> Clique com o botão direito em uma camada para impedi-la de projetar sombra sobre outros fios. A configuração é salva com o projeto e sobrevive a desfazer/refazer e às operações de grupo.</li>
        <li><b>Correção automática de sombras para máscaras entrelaçadas:</b> Marcas de sombra incorretas nos cruzamentos de máscaras agora são ocultadas automaticamente; suas configurações manuais no editor de sombras são sempre respeitadas.</li>
        <li><b>Sombras de máscara no editor de sombras:</b> Sombras projetadas através de uma máscara agora aparecem no editor de sombras do fio superior, para que você possa ativá-las ou desativá-las como qualquer outra sombra.</li>
        <li><b>Seleção de fios mais precisa:</b> Um clique agora seleciona exatamente o que você vê: bordas dos fios, extremidades e contornos das máscaras são todos clicáveis, o fio mais acima é sempre escolhido, e o destaque ao passar o mouse sempre corresponde ao que um clique selecionará.</li>
        <li><b>Correção da visibilidade dos pontos de controle:</b> «Mostrar pontos de controle apenas para o fio selecionado» agora oculta apenas os pontos de controle; os outros fios mantêm seus quadrados de extremidade e continuam móveis. Arrastar uma extremidade não faz mais aparecer um ponto de controle nunca usado.</li>
        <li><b>Configurações de sombra preservadas:</b> O estado de «sombra oculta» de uma camada não é mais redefinido ao mover ou duplicar grupos.</li>
        <li><b>Maior estabilidade de desenho:</b> Corrigidos problemas internos de renderização que podiam corromper a tela após um erro de desenho.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.109</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.109:</p>
    <ul>
        <li><b>&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05D7;&#x05D3;&#x05E9;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E7;&#x05D8;&#x05DF; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;. &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E0;&#x05D5;&#x05E2;&#x05DC;&#x05EA;/&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05EA;; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E4;&#x05E9;&#x05D5;&#x05D8; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4;. &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D0;&#x05DA; &#x05DC;&#x05D0; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;, &#x05D5;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9; / &#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05EA; &#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05D6;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; (&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4; &#x05D7;&#x05E1;&#x05D5;&#x05DE;&#x05D4; &#x05E8;&#x05E7; &#x05DC;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA;). &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8; &#x05D2;&#x05DD; &#x05D1;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;, &#x05D1;&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4;/&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05D5;&#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D1;&#x05D9;&#x05DF; &#x05DB;&#x05E8;&#x05D8;&#x05D9;&#x05E1;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05EA; &#x05E6;&#x05DC; &#x05DC;&#x05DB;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DE;&#x05E0;&#x05D5;&#x05E2; &#x05DE;&#x05DE;&#x05E0;&#x05D4; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05DC; &#x05E6;&#x05DC; &#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9;&#x05DD;. &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E9;&#x05D5;&#x05E8;&#x05D3;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05D5;&#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E9;&#x05D6;&#x05D5;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05E1;&#x05D9;&#x05DE;&#x05E0;&#x05D9; &#x05E6;&#x05DC; &#x05E9;&#x05D2;&#x05D5;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D3;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D5;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D3;&#x05E8;&#x05DA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05E0;&#x05D9;&#x05EA;&#x05DF; &#x05DC;&#x05D4;&#x05E4;&#x05E2;&#x05D9;&#x05DC; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05DD; &#x05DB;&#x05DE;&#x05D5; &#x05DB;&#x05DC; &#x05E6;&#x05DC; &#x05D0;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05E8;&#x05D5;&#x05D0;&#x05D9;&#x05DD;: &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DB;&#x05D9;&#x05E4;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05E8; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4;, &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF; &#x05D1;&#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E0;&#x05D1;&#x05D7;&#x05E8; &#x05EA;&#x05DE;&#x05D9;&#x05D3;, &#x05D5;&#x05D4;&#x05D4;&#x05D3;&#x05D2;&#x05E9;&#x05D4; &#x05D1;&#x05E8;&#x05D9;&#x05D7;&#x05D5;&#x05E3; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05EA;&#x05D5;&#x05D0;&#x05DE;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05EA;&#x05D1;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;:</b> "&#x05D4;&#x05E6;&#x05D2; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E8;&#x05E7; &#x05E2;&#x05D1;&#x05D5;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E0;&#x05D1;&#x05D7;&#x05E8;" &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E8;&#x05E7; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;; &#x05E9;&#x05D0;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05D5;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DC; &#x05E8;&#x05D9;&#x05D1;&#x05D5;&#x05E2;&#x05D9; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D5;&#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;. &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E6;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D4; &#x05D2;&#x05D5;&#x05E8;&#x05DE;&#x05EA; &#x05E2;&#x05D5;&#x05D3; &#x05DC;&#x05D4;&#x05D5;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05D4;&#x05D5;&#x05D6;&#x05D6;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E6;&#x05DC; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05DE;&#x05E6;&#x05D1; "&#x05E6;&#x05DC; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;" &#x05E9;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D5; &#x05DE;&#x05EA;&#x05D0;&#x05E4;&#x05E1; &#x05E2;&#x05D5;&#x05D3; &#x05D1;&#x05E2;&#x05EA; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05D9;&#x05E6;&#x05D9;&#x05D1;&#x05D5;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05E4;&#x05E0;&#x05D9;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E2;&#x05DC;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D5; &#x05DC;&#x05E4;&#x05D2;&#x05D5;&#x05E2; &#x05D1;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DC;&#x05D0;&#x05D7;&#x05E8; &#x05E9;&#x05D2;&#x05D9;&#x05D0;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8;.</li>
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
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.109</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.109:</p>
    <ul>
        <li><b>Modo de bloqueo rediseñado:</b> Cada botón de capa ahora muestra un pequeño candado en modo de bloqueo. Haz clic en el candado para bloquear/desbloquear; hacer clic en la capa simplemente la selecciona. Las hebras bloqueadas pueden seleccionarse pero no moverse ni usarse para adjuntar, y Nueva hebra / Eliminar hebra siguen disponibles (la eliminación solo se bloquea para capas bloqueadas). El estado de bloqueo también se recuerda al deshacer/rehacer, guardar/cargar y cambiar de pestaña.</li>
        <li><b>Opción Ocultar sombra por capa:</b> Haz clic derecho en una capa para impedir que proyecte sombra sobre otras hebras. El ajuste se guarda con tu proyecto y sobrevive a deshacer/rehacer y a las operaciones de grupo.</li>
        <li><b>Corrección automática de sombras para máscaras tejidas:</b> Las marcas de sombra incorrectas en los cruces de máscaras ahora se ocultan automáticamente; tus ajustes manuales del editor de sombras siempre se respetan.</li>
        <li><b>Sombras de máscara en el editor de sombras:</b> Las sombras proyectadas a través de una máscara ahora aparecen en el editor de sombras de la hebra superior, para que puedas activarlas o desactivarlas como cualquier otra sombra.</li>
        <li><b>Selección de hebras más precisa:</b> Un clic ahora selecciona exactamente lo que ves: los bordes de las hebras, los extremos y los contornos de las máscaras son todos clicables, siempre se elige la hebra superior, y el resaltado al pasar el cursor siempre coincide con lo que un clic seleccionará.</li>
        <li><b>Corrección de la visibilidad de puntos de control:</b> «Mostrar puntos de control solo para la hebra seleccionada» ahora oculta solo los puntos de control; las demás hebras conservan sus cuadrados de extremo y siguen siendo movibles. Arrastrar un extremo ya no hace aparecer un punto de control sin usar.</li>
        <li><b>Ajustes de sombra preservados:</b> El estado de «sombra oculta» de una capa ya no se restablece al mover o duplicar grupos.</li>
        <li><b>Mayor estabilidad de dibujo:</b> Se corrigieron problemas internos de renderizado que podían corromper el lienzo tras un error de dibujo.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.109</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.109:</p>
    <ul>
        <li><b>Lock Mode Redesigned:</b> Each layer button now shows a small padlock in lock mode. Click the padlock to lock/unlock; clicking the layer simply selects it. Locked strands can be selected but not moved or attached to, and New Strand / Delete Strand remain available (delete is blocked only for locked layers). The lock state is also remembered through undo/redo, save/load, and tab switching.</li>
        <li><b>Per-Layer Hide Shadow Option:</b> Right-click a layer to stop it from casting shadow onto other strands. The setting is saved with your project and survives undo/redo and group operations.</li>
        <li><b>Automatic Shadow Correction for Woven Masks:</b> Incorrect shadow marks at mask crossings are now hidden automatically; your manual Shadow Editor settings are always respected.</li>
        <li><b>Mask Shadows in the Shadow Editor:</b> Shadows cast through a mask now appear in the over-strand's Shadow Editor, so you can turn them on or off like any other shadow.</li>
        <li><b>More Accurate Strand Selection:</b> Clicking now selects exactly what you see: strand edges, end caps, and mask outlines are all clickable, the topmost strand is always picked, and the hover highlight always matches what a click will select.</li>
        <li><b>Control Point Visibility Fix:</b> "Show control points only for the selected strand" now hides only control points; other strands keep their endpoint squares and remain movable. Dragging an endpoint no longer makes an untouched control point appear.</li>
        <li><b>Shadow Settings Preserved:</b> A layer's hidden-shadow state is no longer reset by group move or duplicate operations.</li>
        <li><b>Improved Drawing Stability:</b> Fixed internal painting issues that could corrupt the canvas after a drawing error.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.109</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.109 :</p>
    <ul>
        <li><b>Mode verrouillage repensé:</b> Chaque bouton de calque affiche désormais un petit cadenas en mode verrouillage. Cliquez sur le cadenas pour verrouiller/déverrouiller ; cliquer sur le calque le sélectionne simplement. Les brins verrouillés peuvent être sélectionnés mais ni déplacés ni utilisés pour l'attache, et Nouveau brin / Supprimer le brin restent disponibles (la suppression n'est bloquée que pour les calques verrouillés). L'état de verrouillage est également conservé lors des annulations/rétablissements, de l'enregistrement/du chargement et du changement d'onglet.</li>
        <li><b>Option Masquer l'ombre par calque:</b> Faites un clic droit sur un calque pour l'empêcher de projeter une ombre sur les autres brins. Le réglage est enregistré avec votre projet et survit aux annulations/rétablissements et aux opérations de groupe.</li>
        <li><b>Correction automatique des ombres pour les masques tissés:</b> Les marques d'ombre incorrectes aux croisements des masques sont désormais masquées automatiquement ; vos réglages manuels dans l'éditeur d'ombres sont toujours respectés.</li>
        <li><b>Ombres de masque dans l'éditeur d'ombres:</b> Les ombres projetées à travers un masque apparaissent désormais dans l'éditeur d'ombres du brin supérieur, vous pouvez donc les activer ou les désactiver comme n'importe quelle autre ombre.</li>
        <li><b>Sélection de brins plus précise:</b> Un clic sélectionne désormais exactement ce que vous voyez : les bords des brins, les extrémités et les contours des masques sont tous cliquables, le brin le plus haut est toujours choisi, et la surbrillance au survol correspond toujours à ce qu'un clic sélectionnera.</li>
        <li><b>Correction de l'affichage des points de contrôle:</b> « Afficher les points de contrôle uniquement pour le brin sélectionné » ne masque plus que les points de contrôle ; les autres brins conservent leurs carrés d'extrémité et restent déplaçables. Faire glisser une extrémité ne fait plus apparaître un point de contrôle jamais utilisé.</li>
        <li><b>Réglages d'ombre préservés:</b> L'état « ombre masquée » d'un calque n'est plus réinitialisé par un déplacement ou une duplication de groupe.</li>
        <li><b>Stabilité de dessin améliorée:</b> Correction de problèmes internes de rendu qui pouvaient corrompre le canevas après une erreur de dessin.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.109</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.109:</p>
    <ul>
        <li><b>Sperrmodus überarbeitet:</b> Jede Ebenen-Schaltfläche zeigt im Sperrmodus jetzt ein kleines Vorhängeschloss. Klicken Sie auf das Schloss zum Sperren/Entsperren; ein Klick auf die Ebene wählt sie einfach aus. Gesperrte Stränge können ausgewählt, aber nicht bewegt oder als Ansatzpunkt verwendet werden, und Neuer Strang / Strang löschen bleiben verfügbar (Löschen ist nur für gesperrte Ebenen blockiert). Der Sperrzustand bleibt auch bei Rückgängig/Wiederherstellen, Speichern/Laden und Tab-Wechsel erhalten.</li>
        <li><b>Option „Schatten ausblenden“ pro Ebene:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene, damit sie keinen Schatten mehr auf andere Stränge wirft. Die Einstellung wird mit dem Projekt gespeichert und übersteht Rückgängig/Wiederherstellen sowie Gruppenoperationen.</li>
        <li><b>Automatische Schattenkorrektur für gewebte Masken:</b> Falsche Schattenspuren an Maskenkreuzungen werden jetzt automatisch ausgeblendet; Ihre manuellen Einstellungen im Schatten-Editor werden immer respektiert.</li>
        <li><b>Maskenschatten im Schatten-Editor:</b> Schatten, die durch eine Maske geworfen werden, erscheinen jetzt im Schatten-Editor des oberen Strangs und lassen sich wie jeder andere Schatten ein- oder ausschalten.</li>
        <li><b>Präzisere Strangauswahl:</b> Ein Klick wählt jetzt genau das aus, was Sie sehen: Strangränder, Endkappen und Maskenumrisse sind alle anklickbar, der oberste Strang wird immer gewählt, und die Hervorhebung beim Überfahren entspricht immer dem, was ein Klick auswählen würde.</li>
        <li><b>Kontrollpunkt-Anzeige korrigiert:</b> „Kontrollpunkte nur für den ausgewählten Strang anzeigen“ blendet jetzt nur noch Kontrollpunkte aus; andere Stränge behalten ihre Endpunkt-Quadrate und bleiben beweglich. Das Ziehen eines Endpunkts lässt keinen unbenutzten Kontrollpunkt mehr erscheinen.</li>
        <li><b>Schatteneinstellungen bleiben erhalten:</b> Der Zustand „Schatten ausgeblendet“ einer Ebene wird durch Gruppenverschiebung oder -duplizierung nicht mehr zurückgesetzt.</li>
        <li><b>Verbesserte Zeichenstabilität:</b> Interne Renderprobleme behoben, die nach einem Zeichenfehler die Leinwand beschädigen konnten.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.109</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.109:</p>
    <ul>
        <li><b>Modalità blocco ridisegnata:</b> Ogni pulsante di livello ora mostra un piccolo lucchetto in modalità blocco. Fai clic sul lucchetto per bloccare/sbloccare; fare clic sul livello lo seleziona semplicemente. I fili bloccati possono essere selezionati ma non spostati né usati per l'attacco, e Nuovo filo / Elimina filo restano disponibili (l'eliminazione è bloccata solo per i livelli bloccati). Lo stato di blocco viene inoltre ricordato tra annulla/ripristina, salvataggio/caricamento e cambio di scheda.</li>
        <li><b>Opzione Nascondi ombra per livello:</b> Fai clic destro su un livello per impedirgli di proiettare ombra sugli altri fili. L'impostazione viene salvata con il progetto e sopravvive ad annulla/ripristina e alle operazioni di gruppo.</li>
        <li><b>Correzione automatica delle ombre per maschere intrecciate:</b> I segni d'ombra errati agli incroci delle maschere ora vengono nascosti automaticamente; le tue impostazioni manuali nell'editor ombre vengono sempre rispettate.</li>
        <li><b>Ombre delle maschere nell'editor ombre:</b> Le ombre proiettate attraverso una maschera ora appaiono nell'editor ombre del filo superiore, così puoi attivarle o disattivarle come qualsiasi altra ombra.</li>
        <li><b>Selezione dei fili più precisa:</b> Un clic ora seleziona esattamente ciò che vedi: i bordi dei fili, le estremità e i contorni delle maschere sono tutti cliccabili, viene sempre scelto il filo più in alto e l'evidenziazione al passaggio del mouse corrisponde sempre a ciò che un clic selezionerà.</li>
        <li><b>Correzione della visibilità dei punti di controllo:</b> «Mostra i punti di controllo solo per il filo selezionato» ora nasconde solo i punti di controllo; gli altri fili mantengono i loro quadrati alle estremità e restano spostabili. Trascinare un'estremità non fa più apparire un punto di controllo mai utilizzato.</li>
        <li><b>Impostazioni ombra preservate:</b> Lo stato «ombra nascosta» di un livello non viene più azzerato da spostamenti o duplicazioni di gruppo.</li>
        <li><b>Maggiore stabilità di disegno:</b> Risolti problemi interni di rendering che potevano corrompere la tela dopo un errore di disegno.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.109</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.109:</p>
    <ul>
        <li><b>Modo de bloqueio redesenhado:</b> Cada botão de camada agora mostra um pequeno cadeado no modo de bloqueio. Clique no cadeado para bloquear/desbloquear; clicar na camada simplesmente a seleciona. Fios bloqueados podem ser selecionados, mas não movidos nem usados para anexar, e Novo fio / Excluir fio continuam disponíveis (a exclusão só é bloqueada para camadas bloqueadas). O estado de bloqueio também é lembrado ao desfazer/refazer, salvar/carregar e trocar de aba.</li>
        <li><b>Opção Ocultar sombra por camada:</b> Clique com o botão direito em uma camada para impedi-la de projetar sombra sobre outros fios. A configuração é salva com o projeto e sobrevive a desfazer/refazer e às operações de grupo.</li>
        <li><b>Correção automática de sombras para máscaras entrelaçadas:</b> Marcas de sombra incorretas nos cruzamentos de máscaras agora são ocultadas automaticamente; suas configurações manuais no editor de sombras são sempre respeitadas.</li>
        <li><b>Sombras de máscara no editor de sombras:</b> Sombras projetadas através de uma máscara agora aparecem no editor de sombras do fio superior, para que você possa ativá-las ou desativá-las como qualquer outra sombra.</li>
        <li><b>Seleção de fios mais precisa:</b> Um clique agora seleciona exatamente o que você vê: bordas dos fios, extremidades e contornos das máscaras são todos clicáveis, o fio mais acima é sempre escolhido, e o destaque ao passar o mouse sempre corresponde ao que um clique selecionará.</li>
        <li><b>Correção da visibilidade dos pontos de controle:</b> «Mostrar pontos de controle apenas para o fio selecionado» agora oculta apenas os pontos de controle; os outros fios mantêm seus quadrados de extremidade e continuam móveis. Arrastar uma extremidade não faz mais aparecer um ponto de controle nunca usado.</li>
        <li><b>Configurações de sombra preservadas:</b> O estado de «sombra oculta» de uma camada não é mais redefinido ao mover ou duplicar grupos.</li>
        <li><b>Maior estabilidade de desenho:</b> Corrigidos problemas internos de renderização que podiam corromper a tela após um erro de desenho.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.109</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.109:</p>
    <ul>
        <li><b>&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05D7;&#x05D3;&#x05E9;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E7;&#x05D8;&#x05DF; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;. &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E0;&#x05D5;&#x05E2;&#x05DC;&#x05EA;/&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05EA;; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E4;&#x05E9;&#x05D5;&#x05D8; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4;. &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D0;&#x05DA; &#x05DC;&#x05D0; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;, &#x05D5;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9; / &#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05EA; &#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05D6;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; (&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4; &#x05D7;&#x05E1;&#x05D5;&#x05DE;&#x05D4; &#x05E8;&#x05E7; &#x05DC;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA;). &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8; &#x05D2;&#x05DD; &#x05D1;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;, &#x05D1;&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4;/&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05D5;&#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D1;&#x05D9;&#x05DF; &#x05DB;&#x05E8;&#x05D8;&#x05D9;&#x05E1;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05EA; &#x05E6;&#x05DC; &#x05DC;&#x05DB;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DE;&#x05E0;&#x05D5;&#x05E2; &#x05DE;&#x05DE;&#x05E0;&#x05D4; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05DC; &#x05E6;&#x05DC; &#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9;&#x05DD;. &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E9;&#x05D5;&#x05E8;&#x05D3;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05D5;&#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E9;&#x05D6;&#x05D5;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05E1;&#x05D9;&#x05DE;&#x05E0;&#x05D9; &#x05E6;&#x05DC; &#x05E9;&#x05D2;&#x05D5;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D3;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D5;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D3;&#x05E8;&#x05DA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05E0;&#x05D9;&#x05EA;&#x05DF; &#x05DC;&#x05D4;&#x05E4;&#x05E2;&#x05D9;&#x05DC; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05DD; &#x05DB;&#x05DE;&#x05D5; &#x05DB;&#x05DC; &#x05E6;&#x05DC; &#x05D0;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05E8;&#x05D5;&#x05D0;&#x05D9;&#x05DD;: &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DB;&#x05D9;&#x05E4;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05E8; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4;, &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF; &#x05D1;&#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E0;&#x05D1;&#x05D7;&#x05E8; &#x05EA;&#x05DE;&#x05D9;&#x05D3;, &#x05D5;&#x05D4;&#x05D4;&#x05D3;&#x05D2;&#x05E9;&#x05D4; &#x05D1;&#x05E8;&#x05D9;&#x05D7;&#x05D5;&#x05E3; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05EA;&#x05D5;&#x05D0;&#x05DE;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05EA;&#x05D1;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;:</b> "&#x05D4;&#x05E6;&#x05D2; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E8;&#x05E7; &#x05E2;&#x05D1;&#x05D5;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E0;&#x05D1;&#x05D7;&#x05E8;" &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E8;&#x05E7; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;; &#x05E9;&#x05D0;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05D5;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DC; &#x05E8;&#x05D9;&#x05D1;&#x05D5;&#x05E2;&#x05D9; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D5;&#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;. &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E6;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D4; &#x05D2;&#x05D5;&#x05E8;&#x05DE;&#x05EA; &#x05E2;&#x05D5;&#x05D3; &#x05DC;&#x05D4;&#x05D5;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05D4;&#x05D5;&#x05D6;&#x05D6;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E6;&#x05DC; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05DE;&#x05E6;&#x05D1; "&#x05E6;&#x05DC; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;" &#x05E9;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D5; &#x05DE;&#x05EA;&#x05D0;&#x05E4;&#x05E1; &#x05E2;&#x05D5;&#x05D3; &#x05D1;&#x05E2;&#x05EA; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05D9;&#x05E6;&#x05D9;&#x05D1;&#x05D5;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05E4;&#x05E0;&#x05D9;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E2;&#x05DC;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D5; &#x05DC;&#x05E4;&#x05D2;&#x05D5;&#x05E2; &#x05D1;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DC;&#x05D0;&#x05D7;&#x05E8; &#x05E9;&#x05D2;&#x05D9;&#x05D0;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8;.</li>
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
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.109</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades da versão 1.109:</p>
    <ul>
        <li><b>Modo de bloqueio redesenhado:</b> Cada botão de camada agora mostra um pequeno cadeado no modo de bloqueio. Clique no cadeado para bloquear/desbloquear; clicar na camada simplesmente a seleciona. Fios bloqueados podem ser selecionados, mas não movidos nem usados para anexar, e Novo fio / Excluir fio continuam disponíveis (a exclusão só é bloqueada para camadas bloqueadas). O estado de bloqueio também é lembrado ao desfazer/refazer, salvar/carregar e trocar de aba.</li>
        <li><b>Opção Ocultar sombra por camada:</b> Clique com o botão direito em uma camada para impedi-la de projetar sombra sobre outros fios. A configuração é salva com o projeto e sobrevive a desfazer/refazer e às operações de grupo.</li>
        <li><b>Correção automática de sombras para máscaras entrelaçadas:</b> Marcas de sombra incorretas nos cruzamentos de máscaras agora são ocultadas automaticamente; suas configurações manuais no editor de sombras são sempre respeitadas.</li>
        <li><b>Sombras de máscara no editor de sombras:</b> Sombras projetadas através de uma máscara agora aparecem no editor de sombras do fio superior, para que você possa ativá-las ou desativá-las como qualquer outra sombra.</li>
        <li><b>Seleção de fios mais precisa:</b> Um clique agora seleciona exatamente o que você vê: bordas dos fios, extremidades e contornos das máscaras são todos clicáveis, o fio mais acima é sempre escolhido, e o destaque ao passar o mouse sempre corresponde ao que um clique selecionará.</li>
        <li><b>Correção da visibilidade dos pontos de controle:</b> «Mostrar pontos de controle apenas para o fio selecionado» agora oculta apenas os pontos de controle; os outros fios mantêm seus quadrados de extremidade e continuam móveis. Arrastar uma extremidade não faz mais aparecer um ponto de controle nunca usado.</li>
        <li><b>Configurações de sombra preservadas:</b> O estado de «sombra oculta» de uma camada não é mais redefinido ao mover ou duplicar grupos.</li>
        <li><b>Maior estabilidade de desenho:</b> Corrigidos problemas internos de renderização que podiam corromper a tela após um erro de desenho.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.109</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.109:</p>
    <ul>
        <li><b>Lock Mode Redesigned:</b> Each layer button now shows a small padlock in lock mode. Click the padlock to lock/unlock; clicking the layer simply selects it. Locked strands can be selected but not moved or attached to, and New Strand / Delete Strand remain available (delete is blocked only for locked layers). The lock state is also remembered through undo/redo, save/load, and tab switching.</li>
        <li><b>Per-Layer Hide Shadow Option:</b> Right-click a layer to stop it from casting shadow onto other strands. The setting is saved with your project and survives undo/redo and group operations.</li>
        <li><b>Automatic Shadow Correction for Woven Masks:</b> Incorrect shadow marks at mask crossings are now hidden automatically; your manual Shadow Editor settings are always respected.</li>
        <li><b>Mask Shadows in the Shadow Editor:</b> Shadows cast through a mask now appear in the over-strand's Shadow Editor, so you can turn them on or off like any other shadow.</li>
        <li><b>More Accurate Strand Selection:</b> Clicking now selects exactly what you see: strand edges, end caps, and mask outlines are all clickable, the topmost strand is always picked, and the hover highlight always matches what a click will select.</li>
        <li><b>Control Point Visibility Fix:</b> "Show control points only for the selected strand" now hides only control points; other strands keep their endpoint squares and remain movable. Dragging an endpoint no longer makes an untouched control point appear.</li>
        <li><b>Shadow Settings Preserved:</b> A layer's hidden-shadow state is no longer reset by group move or duplicate operations.</li>
        <li><b>Improved Drawing Stability:</b> Fixed internal painting issues that could corrupt the canvas after a drawing error.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.109</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés de la version 1.109 :</p>
    <ul>
        <li><b>Mode verrouillage repensé:</b> Chaque bouton de calque affiche désormais un petit cadenas en mode verrouillage. Cliquez sur le cadenas pour verrouiller/déverrouiller ; cliquer sur le calque le sélectionne simplement. Les brins verrouillés peuvent être sélectionnés mais ni déplacés ni utilisés pour l'attache, et Nouveau brin / Supprimer le brin restent disponibles (la suppression n'est bloquée que pour les calques verrouillés). L'état de verrouillage est également conservé lors des annulations/rétablissements, de l'enregistrement/du chargement et du changement d'onglet.</li>
        <li><b>Option Masquer l'ombre par calque:</b> Faites un clic droit sur un calque pour l'empêcher de projeter une ombre sur les autres brins. Le réglage est enregistré avec votre projet et survit aux annulations/rétablissements et aux opérations de groupe.</li>
        <li><b>Correction automatique des ombres pour les masques tissés:</b> Les marques d'ombre incorrectes aux croisements des masques sont désormais masquées automatiquement ; vos réglages manuels dans l'éditeur d'ombres sont toujours respectés.</li>
        <li><b>Ombres de masque dans l'éditeur d'ombres:</b> Les ombres projetées à travers un masque apparaissent désormais dans l'éditeur d'ombres du brin supérieur, vous pouvez donc les activer ou les désactiver comme n'importe quelle autre ombre.</li>
        <li><b>Sélection de brins plus précise:</b> Un clic sélectionne désormais exactement ce que vous voyez : les bords des brins, les extrémités et les contours des masques sont tous cliquables, le brin le plus haut est toujours choisi, et la surbrillance au survol correspond toujours à ce qu'un clic sélectionnera.</li>
        <li><b>Correction de l'affichage des points de contrôle:</b> « Afficher les points de contrôle uniquement pour le brin sélectionné » ne masque plus que les points de contrôle ; les autres brins conservent leurs carrés d'extrémité et restent déplaçables. Faire glisser une extrémité ne fait plus apparaître un point de contrôle jamais utilisé.</li>
        <li><b>Réglages d'ombre préservés:</b> L'état « ombre masquée » d'un calque n'est plus réinitialisé par un déplacement ou une duplication de groupe.</li>
        <li><b>Stabilité de dessin améliorée:</b> Correction de problèmes internes de rendu qui pouvaient corrompre le canevas après une erreur de dessin.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.109</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in Version 1.109:</p>
    <ul>
        <li><b>Sperrmodus überarbeitet:</b> Jede Ebenen-Schaltfläche zeigt im Sperrmodus jetzt ein kleines Vorhängeschloss. Klicken Sie auf das Schloss zum Sperren/Entsperren; ein Klick auf die Ebene wählt sie einfach aus. Gesperrte Stränge können ausgewählt, aber nicht bewegt oder als Ansatzpunkt verwendet werden, und Neuer Strang / Strang löschen bleiben verfügbar (Löschen ist nur für gesperrte Ebenen blockiert). Der Sperrzustand bleibt auch bei Rückgängig/Wiederherstellen, Speichern/Laden und Tab-Wechsel erhalten.</li>
        <li><b>Option „Schatten ausblenden“ pro Ebene:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene, damit sie keinen Schatten mehr auf andere Stränge wirft. Die Einstellung wird mit dem Projekt gespeichert und übersteht Rückgängig/Wiederherstellen sowie Gruppenoperationen.</li>
        <li><b>Automatische Schattenkorrektur für gewebte Masken:</b> Falsche Schattenspuren an Maskenkreuzungen werden jetzt automatisch ausgeblendet; Ihre manuellen Einstellungen im Schatten-Editor werden immer respektiert.</li>
        <li><b>Maskenschatten im Schatten-Editor:</b> Schatten, die durch eine Maske geworfen werden, erscheinen jetzt im Schatten-Editor des oberen Strangs und lassen sich wie jeder andere Schatten ein- oder ausschalten.</li>
        <li><b>Präzisere Strangauswahl:</b> Ein Klick wählt jetzt genau das aus, was Sie sehen: Strangränder, Endkappen und Maskenumrisse sind alle anklickbar, der oberste Strang wird immer gewählt, und die Hervorhebung beim Überfahren entspricht immer dem, was ein Klick auswählen würde.</li>
        <li><b>Kontrollpunkt-Anzeige korrigiert:</b> „Kontrollpunkte nur für den ausgewählten Strang anzeigen“ blendet jetzt nur noch Kontrollpunkte aus; andere Stränge behalten ihre Endpunkt-Quadrate und bleiben beweglich. Das Ziehen eines Endpunkts lässt keinen unbenutzten Kontrollpunkt mehr erscheinen.</li>
        <li><b>Schatteneinstellungen bleiben erhalten:</b> Der Zustand „Schatten ausgeblendet“ einer Ebene wird durch Gruppenverschiebung oder -duplizierung nicht mehr zurückgesetzt.</li>
        <li><b>Verbesserte Zeichenstabilität:</b> Interne Renderprobleme behoben, die nach einem Zeichenfehler die Leinwand beschädigen konnten.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.109</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità della versione 1.109:</p>
    <ul>
        <li><b>Modalità blocco ridisegnata:</b> Ogni pulsante di livello ora mostra un piccolo lucchetto in modalità blocco. Fai clic sul lucchetto per bloccare/sbloccare; fare clic sul livello lo seleziona semplicemente. I fili bloccati possono essere selezionati ma non spostati né usati per l'attacco, e Nuovo filo / Elimina filo restano disponibili (l'eliminazione è bloccata solo per i livelli bloccati). Lo stato di blocco viene inoltre ricordato tra annulla/ripristina, salvataggio/caricamento e cambio di scheda.</li>
        <li><b>Opzione Nascondi ombra per livello:</b> Fai clic destro su un livello per impedirgli di proiettare ombra sugli altri fili. L'impostazione viene salvata con il progetto e sopravvive ad annulla/ripristina e alle operazioni di gruppo.</li>
        <li><b>Correzione automatica delle ombre per maschere intrecciate:</b> I segni d'ombra errati agli incroci delle maschere ora vengono nascosti automaticamente; le tue impostazioni manuali nell'editor ombre vengono sempre rispettate.</li>
        <li><b>Ombre delle maschere nell'editor ombre:</b> Le ombre proiettate attraverso una maschera ora appaiono nell'editor ombre del filo superiore, così puoi attivarle o disattivarle come qualsiasi altra ombra.</li>
        <li><b>Selezione dei fili più precisa:</b> Un clic ora seleziona esattamente ciò che vedi: i bordi dei fili, le estremità e i contorni delle maschere sono tutti cliccabili, viene sempre scelto il filo più in alto e l'evidenziazione al passaggio del mouse corrisponde sempre a ciò che un clic selezionerà.</li>
        <li><b>Correzione della visibilità dei punti di controllo:</b> «Mostra i punti di controllo solo per il filo selezionato» ora nasconde solo i punti di controllo; gli altri fili mantengono i loro quadrati alle estremità e restano spostabili. Trascinare un'estremità non fa più apparire un punto di controllo mai utilizzato.</li>
        <li><b>Impostazioni ombra preservate:</b> Lo stato «ombra nascosta» di un livello non viene più azzerato da spostamenti o duplicazioni di gruppo.</li>
        <li><b>Maggiore stabilità di disegno:</b> Risolti problemi interni di rendering che potevano corrompere la tela dopo un errore di disegno.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.109</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades de la versión 1.109:</p>
    <ul>
        <li><b>Modo de bloqueo rediseñado:</b> Cada botón de capa ahora muestra un pequeño candado en modo de bloqueo. Haz clic en el candado para bloquear/desbloquear; hacer clic en la capa simplemente la selecciona. Las hebras bloqueadas pueden seleccionarse pero no moverse ni usarse para adjuntar, y Nueva hebra / Eliminar hebra siguen disponibles (la eliminación solo se bloquea para capas bloqueadas). El estado de bloqueo también se recuerda al deshacer/rehacer, guardar/cargar y cambiar de pestaña.</li>
        <li><b>Opción Ocultar sombra por capa:</b> Haz clic derecho en una capa para impedir que proyecte sombra sobre otras hebras. El ajuste se guarda con tu proyecto y sobrevive a deshacer/rehacer y a las operaciones de grupo.</li>
        <li><b>Corrección automática de sombras para máscaras tejidas:</b> Las marcas de sombra incorrectas en los cruces de máscaras ahora se ocultan automáticamente; tus ajustes manuales del editor de sombras siempre se respetan.</li>
        <li><b>Sombras de máscara en el editor de sombras:</b> Las sombras proyectadas a través de una máscara ahora aparecen en el editor de sombras de la hebra superior, para que puedas activarlas o desactivarlas como cualquier otra sombra.</li>
        <li><b>Selección de hebras más precisa:</b> Un clic ahora selecciona exactamente lo que ves: los bordes de las hebras, los extremos y los contornos de las máscaras son todos clicables, siempre se elige la hebra superior, y el resaltado al pasar el cursor siempre coincide con lo que un clic seleccionará.</li>
        <li><b>Corrección de la visibilidad de puntos de control:</b> «Mostrar puntos de control solo para la hebra seleccionada» ahora oculta solo los puntos de control; las demás hebras conservan sus cuadrados de extremo y siguen siendo movibles. Arrastrar un extremo ya no hace aparecer un punto de control sin usar.</li>
        <li><b>Ajustes de sombra preservados:</b> El estado de «sombra oculta» de una capa ya no se restablece al mover o duplicar grupos.</li>
        <li><b>Mayor estabilidad de dibujo:</b> Se corrigieron problemas internos de renderizado que podían corromper el lienzo tras un error de dibujo.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.109</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.109:</p>
    <ul>
        <li><b>&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05D7;&#x05D3;&#x05E9;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E7;&#x05D8;&#x05DF; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;. &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E0;&#x05D5;&#x05E2;&#x05DC;&#x05EA;/&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05EA;; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E4;&#x05E9;&#x05D5;&#x05D8; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4;. &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D0;&#x05DA; &#x05DC;&#x05D0; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;, &#x05D5;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9; / &#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05EA; &#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05D6;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; (&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4; &#x05D7;&#x05E1;&#x05D5;&#x05DE;&#x05D4; &#x05E8;&#x05E7; &#x05DC;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA;). &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8; &#x05D2;&#x05DD; &#x05D1;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;, &#x05D1;&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4;/&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05D5;&#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D1;&#x05D9;&#x05DF; &#x05DB;&#x05E8;&#x05D8;&#x05D9;&#x05E1;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05EA; &#x05E6;&#x05DC; &#x05DC;&#x05DB;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DE;&#x05E0;&#x05D5;&#x05E2; &#x05DE;&#x05DE;&#x05E0;&#x05D4; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05DC; &#x05E6;&#x05DC; &#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9;&#x05DD;. &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E9;&#x05D5;&#x05E8;&#x05D3;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05D5;&#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E9;&#x05D6;&#x05D5;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05E1;&#x05D9;&#x05DE;&#x05E0;&#x05D9; &#x05E6;&#x05DC; &#x05E9;&#x05D2;&#x05D5;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D3;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D5;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D3;&#x05E8;&#x05DA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05E0;&#x05D9;&#x05EA;&#x05DF; &#x05DC;&#x05D4;&#x05E4;&#x05E2;&#x05D9;&#x05DC; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05DD; &#x05DB;&#x05DE;&#x05D5; &#x05DB;&#x05DC; &#x05E6;&#x05DC; &#x05D0;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05E8;&#x05D5;&#x05D0;&#x05D9;&#x05DD;: &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DB;&#x05D9;&#x05E4;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05E8; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4;, &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF; &#x05D1;&#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E0;&#x05D1;&#x05D7;&#x05E8; &#x05EA;&#x05DE;&#x05D9;&#x05D3;, &#x05D5;&#x05D4;&#x05D4;&#x05D3;&#x05D2;&#x05E9;&#x05D4; &#x05D1;&#x05E8;&#x05D9;&#x05D7;&#x05D5;&#x05E3; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05EA;&#x05D5;&#x05D0;&#x05DE;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05EA;&#x05D1;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;:</b> "&#x05D4;&#x05E6;&#x05D2; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E8;&#x05E7; &#x05E2;&#x05D1;&#x05D5;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E0;&#x05D1;&#x05D7;&#x05E8;" &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E8;&#x05E7; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;; &#x05E9;&#x05D0;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05D5;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DC; &#x05E8;&#x05D9;&#x05D1;&#x05D5;&#x05E2;&#x05D9; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D5;&#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;. &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E6;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D4; &#x05D2;&#x05D5;&#x05E8;&#x05DE;&#x05EA; &#x05E2;&#x05D5;&#x05D3; &#x05DC;&#x05D4;&#x05D5;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05D4;&#x05D5;&#x05D6;&#x05D6;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E6;&#x05DC; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05DE;&#x05E6;&#x05D1; "&#x05E6;&#x05DC; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;" &#x05E9;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D5; &#x05DE;&#x05EA;&#x05D0;&#x05E4;&#x05E1; &#x05E2;&#x05D5;&#x05D3; &#x05D1;&#x05E2;&#x05EA; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05D9;&#x05E6;&#x05D9;&#x05D1;&#x05D5;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05E4;&#x05E0;&#x05D9;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E2;&#x05DC;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D5; &#x05DC;&#x05E4;&#x05D2;&#x05D5;&#x05E2; &#x05D1;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DC;&#x05D0;&#x05D7;&#x05E8; &#x05E9;&#x05D2;&#x05D9;&#x05D0;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8;.</li>
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
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.109</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.109:</p>
    <ul>
        <li><b>&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05D1;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05D7;&#x05D3;&#x05E9;:</b> &#x05DB;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DE;&#x05E6;&#x05D9;&#x05D2; &#x05DB;&#x05E2;&#x05EA; &#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E7;&#x05D8;&#x05DF; &#x05D1;&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;. &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05DE;&#x05E0;&#x05E2;&#x05D5;&#x05DC; &#x05E0;&#x05D5;&#x05E2;&#x05DC;&#x05EA;/&#x05DE;&#x05E9;&#x05D7;&#x05E8;&#x05E8;&#x05EA;; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05E4;&#x05E9;&#x05D5;&#x05D8; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05D4;. &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05DD; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D0;&#x05DA; &#x05DC;&#x05D0; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;, &#x05D5;&#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9; / &#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05EA; &#x05D7;&#x05D5;&#x05D8; &#x05E0;&#x05E9;&#x05D0;&#x05E8;&#x05D9;&#x05DD; &#x05D6;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; (&#x05DE;&#x05D7;&#x05D9;&#x05E7;&#x05D4; &#x05D7;&#x05E1;&#x05D5;&#x05DE;&#x05D4; &#x05E8;&#x05E7; &#x05DC;&#x05E9;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05E0;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA;). &#x05DE;&#x05E6;&#x05D1; &#x05D4;&#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8; &#x05D2;&#x05DD; &#x05D1;&#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9;, &#x05D1;&#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4;/&#x05D8;&#x05E2;&#x05D9;&#x05E0;&#x05D4; &#x05D5;&#x05D1;&#x05DE;&#x05E2;&#x05D1;&#x05E8; &#x05D1;&#x05D9;&#x05DF; &#x05DB;&#x05E8;&#x05D8;&#x05D9;&#x05E1;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D0;&#x05E4;&#x05E9;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05EA; &#x05E6;&#x05DC; &#x05DC;&#x05DB;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4;:</b> &#x05DC;&#x05D7;&#x05E6;&#x05D5; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D9;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05E2;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05DE;&#x05E0;&#x05D5;&#x05E2; &#x05DE;&#x05DE;&#x05E0;&#x05D4; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05DC; &#x05E6;&#x05DC; &#x05E2;&#x05DC; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D0;&#x05D7;&#x05E8;&#x05D9;&#x05DD;. &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D4; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05EA; &#x05E2;&#x05DD; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05E7;&#x05D8; &#x05D5;&#x05E9;&#x05D5;&#x05E8;&#x05D3;&#x05EA; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC;/&#x05D1;&#x05D9;&#x05E6;&#x05D5;&#x05E2; &#x05DE;&#x05D7;&#x05D3;&#x05E9; &#x05D5;&#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9; &#x05DC;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E9;&#x05D6;&#x05D5;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05E1;&#x05D9;&#x05DE;&#x05E0;&#x05D9; &#x05E6;&#x05DC; &#x05E9;&#x05D2;&#x05D5;&#x05D9;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05E6;&#x05D8;&#x05DC;&#x05D1;&#x05D5;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA;; &#x05D4;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D3;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05E6;&#x05DC;&#x05DC;&#x05D9; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD;:</b> &#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05D4;&#x05DE;&#x05D5;&#x05D8;&#x05DC;&#x05D9;&#x05DD; &#x05D3;&#x05E8;&#x05DA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D9;&#x05DD; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05E2;&#x05D5;&#x05E8;&#x05DA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D9;&#x05DD; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF;, &#x05DB;&#x05DA; &#x05E9;&#x05E0;&#x05D9;&#x05EA;&#x05DF; &#x05DC;&#x05D4;&#x05E4;&#x05E2;&#x05D9;&#x05DC; &#x05D0;&#x05D5; &#x05DC;&#x05DB;&#x05D1;&#x05D5;&#x05EA; &#x05D0;&#x05D5;&#x05EA;&#x05DD; &#x05DB;&#x05DE;&#x05D5; &#x05DB;&#x05DC; &#x05E6;&#x05DC; &#x05D0;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;:</b> &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05D1;&#x05D5;&#x05D7;&#x05E8;&#x05EA; &#x05DB;&#x05E2;&#x05EA; &#x05D1;&#x05D3;&#x05D9;&#x05D5;&#x05E7; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05E8;&#x05D5;&#x05D0;&#x05D9;&#x05DD;: &#x05E7;&#x05E6;&#x05D5;&#x05D5;&#x05EA; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DB;&#x05D9;&#x05E4;&#x05D5;&#x05EA; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05D5;&#x05E7;&#x05D5;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05E8; &#x05E9;&#x05DC; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D5;&#x05EA; &#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4;, &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E2;&#x05DC;&#x05D9;&#x05D5;&#x05DF; &#x05D1;&#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05E0;&#x05D1;&#x05D7;&#x05E8; &#x05EA;&#x05DE;&#x05D9;&#x05D3;, &#x05D5;&#x05D4;&#x05D4;&#x05D3;&#x05D2;&#x05E9;&#x05D4; &#x05D1;&#x05E8;&#x05D9;&#x05D7;&#x05D5;&#x05E3; &#x05EA;&#x05DE;&#x05D9;&#x05D3; &#x05EA;&#x05D5;&#x05D0;&#x05DE;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D4; &#x05E9;&#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05EA;&#x05D1;&#x05D7;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05DF; &#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;:</b> "&#x05D4;&#x05E6;&#x05D2; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E8;&#x05E7; &#x05E2;&#x05D1;&#x05D5;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05E0;&#x05D1;&#x05D7;&#x05E8;" &#x05DE;&#x05E1;&#x05EA;&#x05D9;&#x05E8; &#x05DB;&#x05E2;&#x05EA; &#x05E8;&#x05E7; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;; &#x05E9;&#x05D0;&#x05E8; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05D5;&#x05DE;&#x05E8;&#x05D9;&#x05DD; &#x05E2;&#x05DC; &#x05E8;&#x05D9;&#x05D1;&#x05D5;&#x05E2;&#x05D9; &#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D5;&#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D4;&#x05D6;&#x05D6;&#x05D4;. &#x05D2;&#x05E8;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05E6;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D4; &#x05D2;&#x05D5;&#x05E8;&#x05DE;&#x05EA; &#x05E2;&#x05D5;&#x05D3; &#x05DC;&#x05D4;&#x05D5;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05E9;&#x05DE;&#x05E2;&#x05D5;&#x05DC;&#x05DD; &#x05DC;&#x05D0; &#x05D4;&#x05D5;&#x05D6;&#x05D6;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E6;&#x05DC; &#x05E0;&#x05E9;&#x05DE;&#x05E8;&#x05D5;&#x05EA;:</b> &#x05DE;&#x05E6;&#x05D1; "&#x05E6;&#x05DC; &#x05DE;&#x05D5;&#x05E1;&#x05EA;&#x05E8;" &#x05E9;&#x05DC; &#x05E9;&#x05DB;&#x05D1;&#x05D4; &#x05D0;&#x05D9;&#x05E0;&#x05D5; &#x05DE;&#x05EA;&#x05D0;&#x05E4;&#x05E1; &#x05E2;&#x05D5;&#x05D3; &#x05D1;&#x05E2;&#x05EA; &#x05D4;&#x05D6;&#x05D6;&#x05D4; &#x05D0;&#x05D5; &#x05E9;&#x05DB;&#x05E4;&#x05D5;&#x05DC; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;.</li>
        <li><b>&#x05D9;&#x05E6;&#x05D9;&#x05D1;&#x05D5;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E8;&#x05D9;&#x05E0;&#x05D3;&#x05D5;&#x05E8; &#x05E4;&#x05E0;&#x05D9;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E2;&#x05DC;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D4;&#x05D9;&#x05D5; &#x05DC;&#x05E4;&#x05D2;&#x05D5;&#x05E2; &#x05D1;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DC;&#x05D0;&#x05D7;&#x05E8; &#x05E9;&#x05D2;&#x05D9;&#x05D0;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8;.</li>
    </ul>
    </div>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.109</h2>
    <p dir="ltr">This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p dir="ltr">What's New in Version 1.109:</p>
    <ul dir="ltr">
        <li><b>Lock Mode Redesigned:</b> Each layer button now shows a small padlock in lock mode. Click the padlock to lock/unlock; clicking the layer simply selects it. Locked strands can be selected but not moved or attached to, and New Strand / Delete Strand remain available (delete is blocked only for locked layers). The lock state is also remembered through undo/redo, save/load, and tab switching.</li>
        <li><b>Per-Layer Hide Shadow Option:</b> Right-click a layer to stop it from casting shadow onto other strands. The setting is saved with your project and survives undo/redo and group operations.</li>
        <li><b>Automatic Shadow Correction for Woven Masks:</b> Incorrect shadow marks at mask crossings are now hidden automatically; your manual Shadow Editor settings are always respected.</li>
        <li><b>Mask Shadows in the Shadow Editor:</b> Shadows cast through a mask now appear in the over-strand's Shadow Editor, so you can turn them on or off like any other shadow.</li>
        <li><b>More Accurate Strand Selection:</b> Clicking now selects exactly what you see: strand edges, end caps, and mask outlines are all clickable, the topmost strand is always picked, and the hover highlight always matches what a click will select.</li>
        <li><b>Control Point Visibility Fix:</b> "Show control points only for the selected strand" now hides only control points; other strands keep their endpoint squares and remain movable. Dragging an endpoint no longer makes an untouched control point appear.</li>
        <li><b>Shadow Settings Preserved:</b> A layer's hidden-shadow state is no longer reset by group move or duplicate operations.</li>
        <li><b>Improved Drawing Stability:</b> Fixed internal painting issues that could corrupt the canvas after a drawing error.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.109</h2>
    <p dir="ltr">Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p dir="ltr">Nouveautés de la version 1.109 :</p>
    <ul dir="ltr">
        <li><b>Mode verrouillage repensé:</b> Chaque bouton de calque affiche désormais un petit cadenas en mode verrouillage. Cliquez sur le cadenas pour verrouiller/déverrouiller ; cliquer sur le calque le sélectionne simplement. Les brins verrouillés peuvent être sélectionnés mais ni déplacés ni utilisés pour l'attache, et Nouveau brin / Supprimer le brin restent disponibles (la suppression n'est bloquée que pour les calques verrouillés). L'état de verrouillage est également conservé lors des annulations/rétablissements, de l'enregistrement/du chargement et du changement d'onglet.</li>
        <li><b>Option Masquer l'ombre par calque:</b> Faites un clic droit sur un calque pour l'empêcher de projeter une ombre sur les autres brins. Le réglage est enregistré avec votre projet et survit aux annulations/rétablissements et aux opérations de groupe.</li>
        <li><b>Correction automatique des ombres pour les masques tissés:</b> Les marques d'ombre incorrectes aux croisements des masques sont désormais masquées automatiquement ; vos réglages manuels dans l'éditeur d'ombres sont toujours respectés.</li>
        <li><b>Ombres de masque dans l'éditeur d'ombres:</b> Les ombres projetées à travers un masque apparaissent désormais dans l'éditeur d'ombres du brin supérieur, vous pouvez donc les activer ou les désactiver comme n'importe quelle autre ombre.</li>
        <li><b>Sélection de brins plus précise:</b> Un clic sélectionne désormais exactement ce que vous voyez : les bords des brins, les extrémités et les contours des masques sont tous cliquables, le brin le plus haut est toujours choisi, et la surbrillance au survol correspond toujours à ce qu'un clic sélectionnera.</li>
        <li><b>Correction de l'affichage des points de contrôle:</b> « Afficher les points de contrôle uniquement pour le brin sélectionné » ne masque plus que les points de contrôle ; les autres brins conservent leurs carrés d'extrémité et restent déplaçables. Faire glisser une extrémité ne fait plus apparaître un point de contrôle jamais utilisé.</li>
        <li><b>Réglages d'ombre préservés:</b> L'état « ombre masquée » d'un calque n'est plus réinitialisé par un déplacement ou une duplication de groupe.</li>
        <li><b>Stabilité de dessin améliorée:</b> Correction de problèmes internes de rendu qui pouvaient corrompre le canevas après une erreur de dessin.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.109</h2>
    <p dir="ltr">Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p dir="ltr">Neu in Version 1.109:</p>
    <ul dir="ltr">
        <li><b>Sperrmodus überarbeitet:</b> Jede Ebenen-Schaltfläche zeigt im Sperrmodus jetzt ein kleines Vorhängeschloss. Klicken Sie auf das Schloss zum Sperren/Entsperren; ein Klick auf die Ebene wählt sie einfach aus. Gesperrte Stränge können ausgewählt, aber nicht bewegt oder als Ansatzpunkt verwendet werden, und Neuer Strang / Strang löschen bleiben verfügbar (Löschen ist nur für gesperrte Ebenen blockiert). Der Sperrzustand bleibt auch bei Rückgängig/Wiederherstellen, Speichern/Laden und Tab-Wechsel erhalten.</li>
        <li><b>Option „Schatten ausblenden“ pro Ebene:</b> Klicken Sie mit der rechten Maustaste auf eine Ebene, damit sie keinen Schatten mehr auf andere Stränge wirft. Die Einstellung wird mit dem Projekt gespeichert und übersteht Rückgängig/Wiederherstellen sowie Gruppenoperationen.</li>
        <li><b>Automatische Schattenkorrektur für gewebte Masken:</b> Falsche Schattenspuren an Maskenkreuzungen werden jetzt automatisch ausgeblendet; Ihre manuellen Einstellungen im Schatten-Editor werden immer respektiert.</li>
        <li><b>Maskenschatten im Schatten-Editor:</b> Schatten, die durch eine Maske geworfen werden, erscheinen jetzt im Schatten-Editor des oberen Strangs und lassen sich wie jeder andere Schatten ein- oder ausschalten.</li>
        <li><b>Präzisere Strangauswahl:</b> Ein Klick wählt jetzt genau das aus, was Sie sehen: Strangränder, Endkappen und Maskenumrisse sind alle anklickbar, der oberste Strang wird immer gewählt, und die Hervorhebung beim Überfahren entspricht immer dem, was ein Klick auswählen würde.</li>
        <li><b>Kontrollpunkt-Anzeige korrigiert:</b> „Kontrollpunkte nur für den ausgewählten Strang anzeigen“ blendet jetzt nur noch Kontrollpunkte aus; andere Stränge behalten ihre Endpunkt-Quadrate und bleiben beweglich. Das Ziehen eines Endpunkts lässt keinen unbenutzten Kontrollpunkt mehr erscheinen.</li>
        <li><b>Schatteneinstellungen bleiben erhalten:</b> Der Zustand „Schatten ausgeblendet“ einer Ebene wird durch Gruppenverschiebung oder -duplizierung nicht mehr zurückgesetzt.</li>
        <li><b>Verbesserte Zeichenstabilität:</b> Interne Renderprobleme behoben, die nach einem Zeichenfehler die Leinwand beschädigen konnten.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.109</h2>
    <p dir="ltr">Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p dir="ltr">Novità della versione 1.109:</p>
    <ul dir="ltr">
        <li><b>Modalità blocco ridisegnata:</b> Ogni pulsante di livello ora mostra un piccolo lucchetto in modalità blocco. Fai clic sul lucchetto per bloccare/sbloccare; fare clic sul livello lo seleziona semplicemente. I fili bloccati possono essere selezionati ma non spostati né usati per l'attacco, e Nuovo filo / Elimina filo restano disponibili (l'eliminazione è bloccata solo per i livelli bloccati). Lo stato di blocco viene inoltre ricordato tra annulla/ripristina, salvataggio/caricamento e cambio di scheda.</li>
        <li><b>Opzione Nascondi ombra per livello:</b> Fai clic destro su un livello per impedirgli di proiettare ombra sugli altri fili. L'impostazione viene salvata con il progetto e sopravvive ad annulla/ripristina e alle operazioni di gruppo.</li>
        <li><b>Correzione automatica delle ombre per maschere intrecciate:</b> I segni d'ombra errati agli incroci delle maschere ora vengono nascosti automaticamente; le tue impostazioni manuali nell'editor ombre vengono sempre rispettate.</li>
        <li><b>Ombre delle maschere nell'editor ombre:</b> Le ombre proiettate attraverso una maschera ora appaiono nell'editor ombre del filo superiore, così puoi attivarle o disattivarle come qualsiasi altra ombra.</li>
        <li><b>Selezione dei fili più precisa:</b> Un clic ora seleziona esattamente ciò che vedi: i bordi dei fili, le estremità e i contorni delle maschere sono tutti cliccabili, viene sempre scelto il filo più in alto e l'evidenziazione al passaggio del mouse corrisponde sempre a ciò che un clic selezionerà.</li>
        <li><b>Correzione della visibilità dei punti di controllo:</b> «Mostra i punti di controllo solo per il filo selezionato» ora nasconde solo i punti di controllo; gli altri fili mantengono i loro quadrati alle estremità e restano spostabili. Trascinare un'estremità non fa più apparire un punto di controllo mai utilizzato.</li>
        <li><b>Impostazioni ombra preservate:</b> Lo stato «ombra nascosta» di un livello non viene più azzerato da spostamenti o duplicazioni di gruppo.</li>
        <li><b>Maggiore stabilità di disegno:</b> Risolti problemi interni di rendering che potevano corrompere la tela dopo un errore di disegno.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.109</h2>
    <p dir="ltr">Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p dir="ltr">Novedades de la versión 1.109:</p>
    <ul dir="ltr">
        <li><b>Modo de bloqueo rediseñado:</b> Cada botón de capa ahora muestra un pequeño candado en modo de bloqueo. Haz clic en el candado para bloquear/desbloquear; hacer clic en la capa simplemente la selecciona. Las hebras bloqueadas pueden seleccionarse pero no moverse ni usarse para adjuntar, y Nueva hebra / Eliminar hebra siguen disponibles (la eliminación solo se bloquea para capas bloqueadas). El estado de bloqueo también se recuerda al deshacer/rehacer, guardar/cargar y cambiar de pestaña.</li>
        <li><b>Opción Ocultar sombra por capa:</b> Haz clic derecho en una capa para impedir que proyecte sombra sobre otras hebras. El ajuste se guarda con tu proyecto y sobrevive a deshacer/rehacer y a las operaciones de grupo.</li>
        <li><b>Corrección automática de sombras para máscaras tejidas:</b> Las marcas de sombra incorrectas en los cruces de máscaras ahora se ocultan automáticamente; tus ajustes manuales del editor de sombras siempre se respetan.</li>
        <li><b>Sombras de máscara en el editor de sombras:</b> Las sombras proyectadas a través de una máscara ahora aparecen en el editor de sombras de la hebra superior, para que puedas activarlas o desactivarlas como cualquier otra sombra.</li>
        <li><b>Selección de hebras más precisa:</b> Un clic ahora selecciona exactamente lo que ves: los bordes de las hebras, los extremos y los contornos de las máscaras son todos clicables, siempre se elige la hebra superior, y el resaltado al pasar el cursor siempre coincide con lo que un clic seleccionará.</li>
        <li><b>Corrección de la visibilidad de puntos de control:</b> «Mostrar puntos de control solo para la hebra seleccionada» ahora oculta solo los puntos de control; las demás hebras conservan sus cuadrados de extremo y siguen siendo movibles. Arrastrar un extremo ya no hace aparecer un punto de control sin usar.</li>
        <li><b>Ajustes de sombra preservados:</b> El estado de «sombra oculta» de una capa ya no se restablece al mover o duplicar grupos.</li>
        <li><b>Mayor estabilidad de dibujo:</b> Se corrigieron problemas internos de renderizado que podían corromper el lienzo tras un error de dibujo.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.109</h2>
    <p dir="ltr">Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p dir="ltr">Novidades da versão 1.109:</p>
    <ul dir="ltr">
        <li><b>Modo de bloqueio redesenhado:</b> Cada botão de camada agora mostra um pequeno cadeado no modo de bloqueio. Clique no cadeado para bloquear/desbloquear; clicar na camada simplesmente a seleciona. Fios bloqueados podem ser selecionados, mas não movidos nem usados para anexar, e Novo fio / Excluir fio continuam disponíveis (a exclusão só é bloqueada para camadas bloqueadas). O estado de bloqueio também é lembrado ao desfazer/refazer, salvar/carregar e trocar de aba.</li>
        <li><b>Opção Ocultar sombra por camada:</b> Clique com o botão direito em uma camada para impedi-la de projetar sombra sobre outros fios. A configuração é salva com o projeto e sobrevive a desfazer/refazer e às operações de grupo.</li>
        <li><b>Correção automática de sombras para máscaras entrelaçadas:</b> Marcas de sombra incorretas nos cruzamentos de máscaras agora são ocultadas automaticamente; suas configurações manuais no editor de sombras são sempre respeitadas.</li>
        <li><b>Sombras de máscara no editor de sombras:</b> Sombras projetadas através de uma máscara agora aparecem no editor de sombras do fio superior, para que você possa ativá-las ou desativá-las como qualquer outra sombra.</li>
        <li><b>Seleção de fios mais precisa:</b> Um clique agora seleciona exatamente o que você vê: bordas dos fios, extremidades e contornos das máscaras são todos clicáveis, o fio mais acima é sempre escolhido, e o destaque ao passar o mouse sempre corresponde ao que um clique selecionará.</li>
        <li><b>Correção da visibilidade dos pontos de controle:</b> «Mostrar pontos de controle apenas para o fio selecionado» agora oculta apenas os pontos de controle; os outros fios mantêm seus quadrados de extremidade e continuam móveis. Arrastar uma extremidade não faz mais aparecer um ponto de controle nunca usado.</li>
        <li><b>Configurações de sombra preservadas:</b> O estado de «sombra oculta» de uma camada não é mais redefinido ao mover ou duplicar grupos.</li>
        <li><b>Maior estabilidade de desenho:</b> Corrigidos problemas internos de renderização que podiam corromper a tela após um erro de desenho.</li>
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

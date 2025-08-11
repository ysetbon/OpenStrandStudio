#!/bin/bash

# Set variables
APP_NAME="OpenStrandStudio"
VERSION="1_101"
APP_DATE="11_August_2025"
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

# Create welcome.html (English + localized sections). Updated to 1.101 what's-new.
cat > "$RESOURCES_DIR/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.101</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in this version:</p>
    <ul>
        <li><b>Improved Layer Management:</b> Enhanced StateLayerManager structure for better handling of knot connections and strand relationships, providing more reliable layer operations and improved performance.</li>
        <li><b>Group Duplication:</b> Duplicate entire groups with all their strands via right-click → "Duplicate Group". Maintains properties and generates unique layer names.</li>
        <li><b>Hide Mode:</b> New hide mode via the monkey button (🙉/🙈) to quickly hide multiple layers. Enter hide mode, click layers to hide, then exit to apply changes.</li>
        <li><b>Center View:</b> Instantly center all strands with the new target button (🎯). Automatically adjusts the canvas position to show all work centered.</li>
        <li><b>Quick Knot Closing:</b> Right-click on any strand or attached strand with one free end to quickly close the knot. Auto-connects to the nearest compatible free end.</li>
        <li><b>New Language - German (🇩🇪):</b> Switch to German in Settings → Change Language.</li>
        <li><b>New Samples category:</b> Explore ready-to-load sample projects in Settings → Samples. Choose a sample; the dialog will close and the sample will load.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.101</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Neu in dieser Version:</p>
    <ul>
        <li><b>Verbesserte Ebenenverwaltung:</b> Verbesserte StateLayerManager-Struktur für zuverlässigeres Handling von Knotenverbindungen und Strangbeziehungen, mit stabileren Operationen und besserer Performance.</li>
        <li><b>Gruppenduplikation:</b> Ganze Gruppen per Rechtsklick → "Gruppe duplizieren" duplizieren. Eigenschaften bleiben erhalten, eindeutige Ebenennamen werden erzeugt.</li>
        <li><b>Versteckmodus:</b> Neuer Modus über die Affen-Schaltfläche (🙉/🙈), um mehrere Ebenen schnell auszublenden. Aktivieren, Ebenen anklicken, zum Anwenden verlassen.</li>
        <li><b>Ansicht zentrieren:</b> Mit der Ziel-Schaltfläche (🎯) alle Stränge sofort zentrieren. Die Leinwandposition wird automatisch angepasst.</li>
        <li><b>Schnelles Knotenschließen:</b> Rechtsklick auf einen Strang oder verbundenen Strang mit freiem Ende, um den Knoten schnell zu schließen. Verbindet automatisch mit dem nächstgelegenen kompatiblen freien Ende.</li>
        <li><b>Neue Sprache – Deutsch (🇩🇪):</b> Deutsch in Einstellungen → Sprache ändern auswählen.</li>
        <li><b>Neue Kategorie „Beispiele“:</b> Beispielprojekte in Einstellungen → Beispiele. Beispiel wählen; der Dialog schließt sich und das Beispiel wird geladen.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôle de la largeur des brins :</b> Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.</li>
        <li><b>Zoom avant/arrière :</b> Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.</li>
        <li><b>Déplacement de l'écran :</b> Vous pouvez faire glisser le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.</li>
        <li><b>Mode ombre uniquement :</b> Vous pouvez maintenant masquer une couche tout en affichant ses ombres et reflets en faisant un clic droit sur un bouton de couche et en sélectionnant "Ombre uniquement". Cela aide à visualiser les effets d'ombre sans l'encombrement visuel.</li>
        <li><b>Configuration initiale :</b> Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.</li>
        <li><b>Corrections générales :</b> Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.</li>
        <li><b>Rendu de qualité supérieure :</b> Amélioration de la qualité d'affichage du canevas et export d'images en résolution 4x plus élevée pour des résultats nets et professionnels.</li>
        <li><b>Suppression de l'option masque étendu :</b> L'option masque étendu de la couche générale a été supprimée car elle était uniquement nécessaire comme solution de secours pour les problèmes de shader dans les anciennes versions (1.09x). Avec l'ombrage grandement amélioré, cette option n'est plus nécessaire.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controllo della larghezza dei trefoli:</b> Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.</li>
        <li><b>Zoom avanti/indietro:</b> Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.</li>
        <li><b>Spostamento schermo:</b> Puoi trascinare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.</li>
        <li><b>Modalità solo ombra:</b> Ora puoi nascondere un livello pur mostrando le sue ombre e luci facendo clic destro su un pulsante livello e selezionando "Solo Ombra". Questo aiuta a visualizzare gli effetti ombra senza il disordine visivo.</li>
        <li><b>Configurazione iniziale:</b> Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.</li>
        <li><b>Correzioni generali:</b> Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.</li>
        <li><b>Rendering di qualità superiore:</b> Migliorata la qualità di visualizzazione del canvas e esportazione immagini con risoluzione 4x più alta per risultati nitidi e professionali.</li>
        <li><b>Rimossa opzione maschera estesa:</b> L'opzione maschera estesa dal livello generale è stata rimossa poiché era necessaria solo come backup per problemi di shader nelle versioni precedenti (1.09x). Con l'ombreggiatura notevolmente migliorata, questa opzione non è più necessaria.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Control del ancho de las hebras:</b> Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.</li>
        <li><b>Zoom acercar/alejar:</b> Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.</li>
        <li><b>Mover pantalla:</b> Puedes arrastrar el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.</li>
        <li><b>Modo solo sombra:</b> Ahora puedes ocultar una capa mientras sigues mostrando sus sombras y luces haciendo clic derecho en un botón de capa y seleccionando "Solo Sombra". Esto ayuda a visualizar los efectos de sombra sin el desorden visual.</li>
        <li><b>Configuración inicial:</b> Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.</li>
        <li><b>Correcciones generales:</b> Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.</li>
        <li><b>Renderizado de mayor calidad:</b> Mejora en la calidad de visualización del lienzo y exportación de imágenes con resolución 4x más alta para resultados nítidos y profesionales.</li>
        <li><b>Eliminada opción de máscara extendida:</b> La opción de máscara extendida de la capa general ha sido eliminada ya que solo era necesaria como respaldo para problemas de shader en versiones anteriores (1.09x). Con el sombreado considerablemente mejorado, esta opción ya no es necesaria.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controle de largura dos fios:</b> Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.</li>
        <li><b>Zoom ampliar/reduzir:</b> Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.</li>
        <li><b>Mover tela:</b> Você pode arrastar o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.</li>
        <li><b>Modo apenas sombra:</b> Agora você pode ocultar uma camada enquanto ainda mostra suas sombras e destaques clicando com o botão direito em um botão de camada e selecionando "Apenas Sombra". Isso ajuda a visualizar efeitos de sombra sem a desordem visual.</li>
        <li><b>Configuração inicial:</b> Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.</li>
        <li><b>Correções gerais:</b> Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.</li>
        <li><b>Renderização de qualidade superior:</b> Melhoria na qualidade de exibição do canvas e exportação de imagens com resolução 4x mais alta para resultados nítidos e profissionais.</li>
        <li><b>Removida opção de máscara estendida:</b> A opção de máscara estendida da camada geral foi removida pois era necessária apenas como backup para problemas de shader em versões antigas (1.09x). Com o sombreamento muito melhorado, esta opção não é mais necessária.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;:</b> &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05E9;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D1;&#x05E0;&#x05E4;&#x05E8;&#x05D3;, &#x05DB;&#x05DA; &#x05E9;&#x05EA;&#x05D5;&#x05DB;&#x05DC;&#x05D5; &#x05DC;&#x05D9;&#x05E6;&#x05D5;&#x05E8; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D2;&#x05D5;&#x05D5;&#x05E0;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05DC;&#x05D4; &#x05D5;&#x05D4;&#x05E7;&#x05D8;&#x05E0;&#x05D4;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05EA;&#x05E7;&#x05E8;&#x05D1; &#x05D5;&#x05DC;&#x05D4;&#x05EA;&#x05E8;&#x05D7;&#x05E7; &#x05DE;&#x05D4;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05E4;&#x05E8;&#x05D8;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D6;&#x05D6;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DA;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E2;&#x05DC; &#x05D9;&#x05D3;&#x05D9; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05D9;&#x05D3;, &#x05DE;&#x05D4; &#x05E9;&#x05E2;&#x05D5;&#x05D6;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DC; &#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05D4;&#x05EA;&#x05D7;&#x05DC;&#x05EA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4;:</b> &#x05DB;&#x05E9;&#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D4; &#x05D1;&#x05E4;&#x05E2;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D4;, &#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05DC;&#x05D7;&#x05D5;&#x05E5; &#x05E2;&#x05DC; "&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;" &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05DC;&#x05E6;&#x05D9;&#x05D9;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05EA;&#x05E7;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E0;&#x05D2;&#x05E8;&#x05DE;&#x05D5; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;, &#x05DB;&#x05DE;&#x05D5; &#x05DC;&#x05DE;&#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05D9;&#x05E6;&#x05E8;&#x05D5; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D6;&#x05DE;&#x05E0;&#x05D9; &#x05D5;&#x05DC;&#x05D0; &#x05E1;&#x05D9;&#x05E4;&#x05E7;&#x05D5; &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05D7;&#x05DC;&#x05E7;&#x05D4;.</li>
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

# French
cat > "$RESOURCES_DIR/fr.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôle de la largeur des brins :</b> Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.</li>
        <li><b>Zoom avant/arrière :</b> Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.</li>
        <li><b>Déplacement de l'écran :</b> Vous pouvez faire glisser le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.</li>
        <li><b>Mode ombre uniquement :</b> Vous pouvez maintenant masquer une couche tout en affichant ses ombres et reflets en faisant un clic droit sur un bouton de couche et en sélectionnant "Ombre uniquement". Cela aide à visualiser les effets d'ombre sans l'encombrement visuel.</li>
        <li><b>Configuration initiale :</b> Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.</li>
        <li><b>Corrections générales :</b> Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.</li>
        <li><b>Rendu de qualité supérieure :</b> Amélioration de la qualité d'affichage du canevas et export d'images en résolution 4x plus élevée pour des résultats nets et professionnels.</li>
        <li><b>Suppression de l'option masque étendu :</b> L'option masque étendu de la couche générale a été supprimée car elle était uniquement nécessaire comme solution de secours pour les problèmes de shader dans les anciennes versions (1.09x). Avec l'ombrage grandement amélioré, cette option n'est plus nécessaire.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.101</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li><b>Strand Width Control:</b> You can now dynamically adjust the width of individual strands, giving you more flexibility in creating varied knot designs.</li>
        <li><b>Zoom In/Out:</b> You can zoom in and out of your design to see small details or the entire diagram.</li>
        <li><b>Pan Screen:</b> You can drag the canvas by clicking the hand button, which helps when working on larger diagrams.</li>
        <li><b>Shadow-Only Mode:</b> You can now hide a layer while still showing its shadows and highlights by right-clicking on a layer button and selecting "Shadow Only". This helps visualize shadow effects without the visual clutter.</li>
        <li><b>Initial Setup:</b> When first starting the application, you'll need to click "New Strand" to begin creating your first strand.</li>
        <li><b>General Fixes:</b> Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.</li>
        <li><b>Higher Quality Rendering:</b> Improved canvas display quality and 4x higher resolution image export for crisp, professional results.</li>
        <li><b>Removed Extended Mask Option:</b> The extended mask option from the general layer has been removed since it was only needed as a backup for shader issues in older versions (1.09x). With greatly improved shading, this option is no longer necessary.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controllo della larghezza dei trefoli:</b> Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.</li>
        <li><b>Zoom avanti/indietro:</b> Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.</li>
        <li><b>Spostamento schermo:</b> Puoi trascinare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.</li>
        <li><b>Modalità solo ombra:</b> Ora puoi nascondere un livello pur mostrando le sue ombre e luci facendo clic destro su un pulsante livello e selezionando "Solo Ombra". Questo aiuta a visualizzare gli effetti ombra senza il disordine visivo.</li>
        <li><b>Configurazione iniziale:</b> Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.</li>
        <li><b>Correzioni generali:</b> Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.</li>
        <li><b>Rendering di qualità superiore:</b> Migliorata la qualità di visualizzazione del canvas e esportazione immagini con risoluzione 4x più alta per risultati nitidi e professionali.</li>
        <li><b>Rimossa opzione maschera estesa:</b> L'opzione maschera estesa dal livello generale è stata rimossa poiché era necessaria solo come backup per problemi di shader nelle versioni precedenti (1.09x). Con l'ombreggiatura notevolmente migliorata, questa opzione non è più necessaria.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Control del ancho de las hebras:</b> Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.</li>
        <li><b>Zoom acercar/alejar:</b> Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.</li>
        <li><b>Mover pantalla:</b> Puedes arrastrar el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.</li>
        <li><b>Modo solo sombra:</b> Ahora puedes ocultar una capa mientras sigues mostrando sus sombras y luces haciendo clic derecho en un botón de capa y seleccionando "Solo Sombra". Esto ayuda a visualizar los efectos de sombra sin el desorden visual.</li>
        <li><b>Configuración inicial:</b> Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.</li>
        <li><b>Correcciones generales:</b> Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.</li>
        <li><b>Renderizado de mayor calidad:</b> Mejora en la calidad de visualización del lienzo y exportación de imágenes con resolución 4x más alta para resultados nítidos y profesionales.</li>
        <li><b>Eliminada opción de máscara extendida:</b> La opción de máscara extendida de la capa general ha sido eliminada ya que solo era necesaria como respaldo para problemas de shader en versiones anteriores (1.09x). Con el sombreado considerablemente mejorado, esta opción ya no es necesaria.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controle de largura dos fios:</b> Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.</li>
        <li><b>Zoom ampliar/reduzir:</b> Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.</li>
        <li><b>Mover tela:</b> Você pode arrastar o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.</li>
        <li><b>Modo apenas sombra:</b> Agora você pode ocultar uma camada enquanto ainda mostra suas sombras e destaques clicando com o botão direito em um botão de camada e selecionando "Apenas Sombra". Isso ajuda a visualizar efeitos de sombra sem a desordem visual.</li>
        <li><b>Configuração inicial:</b> Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.</li>
        <li><b>Correções gerais:</b> Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.</li>
        <li><b>Renderização de qualidade superior:</b> Melhoria na qualidade de exibição do canvas e exportação de imagens com resolução 4x mais alta para resultados nítidos e profissionais.</li>
        <li><b>Removida opção de máscara estendida:</b> A opção de máscara estendida da camada geral foi removida pois era necessária apenas como backup para problemas de shader em versões antigas (1.09x). Com o sombreamento muito melhorado, esta opção não é mais necessária.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;:</b> &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05E9;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D1;&#x05E0;&#x05E4;&#x05E8;&#x05D3;, &#x05DB;&#x05DA; &#x05E9;&#x05EA;&#x05D5;&#x05DB;&#x05DC;&#x05D5; &#x05DC;&#x05D9;&#x05E6;&#x05D5;&#x05E8; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D2;&#x05D5;&#x05D5;&#x05E0;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05DC;&#x05D4; &#x05D5;&#x05D4;&#x05E7;&#x05D8;&#x05E0;&#x05D4;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05EA;&#x05E7;&#x05E8;&#x05D1; &#x05D5;&#x05DC;&#x05D4;&#x05EA;&#x05E8;&#x05D7;&#x05E7; &#x05DE;&#x05D4;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05E4;&#x05E8;&#x05D8;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D6;&#x05D6;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DA;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E2;&#x05DC; &#x05D9;&#x05D3;&#x05D9; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05D9;&#x05D3;, &#x05DE;&#x05D4; &#x05E9;&#x05E2;&#x05D5;&#x05D6;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DC; &#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05D4;&#x05EA;&#x05D7;&#x05DC;&#x05EA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4;:</b> &#x05DB;&#x05E9;&#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D4; &#x05D1;&#x05E4;&#x05E2;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D4;, &#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05DC;&#x05D7;&#x05D5;&#x05E5; &#x05E2;&#x05DC; "&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;" &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05DC;&#x05E6;&#x05D9;&#x05D9;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05EA;&#x05E7;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E0;&#x05D2;&#x05E8;&#x05DE;&#x05D5; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;, &#x05DB;&#x05DE;&#x05D5; &#x05DC;&#x05DE;&#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05D9;&#x05E6;&#x05E8;&#x05D5; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D6;&#x05DE;&#x05E0;&#x05D9; &#x05D5;&#x05DC;&#x05D0; &#x05E1;&#x05D9;&#x05E4;&#x05E7;&#x05D5; &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05D7;&#x05DC;&#x05E7;&#x05D4;.</li>
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
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controllo della larghezza dei trefoli:</b> Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.</li>
        <li><b>Zoom avanti/indietro:</b> Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.</li>
        <li><b>Spostamento schermo:</b> Puoi trascinare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.</li>
        <li><b>Modalità solo ombra:</b> Ora puoi nascondere un livello pur mostrando le sue ombre e luci facendo clic destro su un pulsante livello e selezionando "Solo Ombra". Questo aiuta a visualizzare gli effetti ombra senza il disordine visivo.</li>
        <li><b>Configurazione iniziale:</b> Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.</li>
        <li><b>Correzioni generali:</b> Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.</li>
        <li><b>Rendering di qualità superiore:</b> Migliorata la qualità di visualizzazione del canvas e esportazione immagini con risoluzione 4x più alta per risultati nitidi e professionali.</li>
        <li><b>Rimossa opzione maschera estesa:</b> L'opzione maschera estesa dal livello generale è stata rimossa poiché era necessaria solo come backup per problemi di shader nelle versioni precedenti (1.09x). Con l'ombreggiatura notevolmente migliorata, questa opzione non è più necessaria.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.101</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li><b>Strand Width Control:</b> You can now dynamically adjust the width of individual strands, giving you more flexibility in creating varied knot designs.</li>
        <li><b>Zoom In/Out:</b> You can zoom in and out of your design to see small details or the entire diagram.</li>
        <li><b>Pan Screen:</b> You can drag the canvas by clicking the hand button, which helps when working on larger diagrams.</li>
        <li><b>Shadow-Only Mode:</b> You can now hide a layer while still showing its shadows and highlights by right-clicking on a layer button and selecting "Shadow Only". This helps visualize shadow effects without the visual clutter.</li>
        <li><b>Initial Setup:</b> When first starting the application, you'll need to click "New Strand" to begin creating your first strand.</li>
        <li><b>General Fixes:</b> Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.</li>
        <li><b>Higher Quality Rendering:</b> Improved canvas display quality and 4x higher resolution image export for crisp, professional results.</li>
        <li><b>Removed Extended Mask Option:</b> The extended mask option from the general layer has been removed since it was only needed as a backup for shader issues in older versions (1.09x). With greatly improved shading, this option is no longer necessary.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôle de la largeur des brins :</b> Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.</li>
        <li><b>Zoom avant/arrière :</b> Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.</li>
        <li><b>Déplacement de l'écran :</b> Vous pouvez faire glisser le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.</li>
        <li><b>Mode ombre uniquement :</b> Vous pouvez maintenant masquer une couche tout en affichant ses ombres et reflets en faisant un clic droit sur un bouton de couche et en sélectionnant "Ombre uniquement". Cela aide à visualiser les effets d'ombre sans l'encombrement visuel.</li>
        <li><b>Configuration initiale :</b> Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.</li>
        <li><b>Corrections générales :</b> Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.</li>
        <li><b>Rendu de qualité supérieure :</b> Amélioration de la qualité d'affichage du canevas et export d'images en résolution 4x plus élevée pour des résultats nets et professionnels.</li>
        <li><b>Suppression de l'option masque étendu :</b> L'option masque étendu de la couche générale a été supprimée car elle était uniquement nécessaire comme solution de secours pour les problèmes de shader dans les anciennes versions (1.09x). Avec l'ombrage grandement amélioré, cette option n'est plus nécessaire.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Control del ancho de las hebras:</b> Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.</li>
        <li><b>Zoom acercar/alejar:</b> Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.</li>
        <li><b>Mover pantalla:</b> Puedes arrastrar el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.</li>
        <li><b>Modo solo sombra:</b> Ahora puedes ocultar una capa mientras sigues mostrando sus sombras y luces haciendo clic derecho en un botón de capa y seleccionando "Solo Sombra". Esto ayuda a visualizar los efectos de sombra sin el desorden visual.</li>
        <li><b>Configuración inicial:</b> Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.</li>
        <li><b>Correcciones generales:</b> Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.</li>
        <li><b>Renderizado de mayor calidad:</b> Mejora en la calidad de visualización del lienzo y exportación de imágenes con resolución 4x más alta para resultados nítidos y profesionales.</li>
        <li><b>Eliminada opción de máscara extendida:</b> La opción de máscara extendida de la capa general ha sido eliminada ya que solo era necesaria como respaldo para problemas de shader en versiones anteriores (1.09x). Con el sombreado considerablemente mejorado, esta opción ya no es necesaria.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controle de largura dos fios:</b> Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.</li>
        <li><b>Zoom ampliar/reduzir:</b> Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.</li>
        <li><b>Mover tela:</b> Você pode arrastar o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.</li>
        <li><b>Modo apenas sombra:</b> Agora você pode ocultar uma camada enquanto ainda mostra suas sombras e destaques clicando com o botão direito em um botão de camada e selecionando "Apenas Sombra". Isso ajuda a visualizar efeitos de sombra sem a desordem visual.</li>
        <li><b>Configuração inicial:</b> Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.</li>
        <li><b>Correções gerais:</b> Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.</li>
        <li><b>Renderização de qualidade superior:</b> Melhoria na qualidade de exibição do canvas e exportação de imagens com resolução 4x mais alta para resultados nítidos e profissionais.</li>
        <li><b>Removida opção de máscara estendida:</b> A opção de máscara estendida da camada geral foi removida pois era necessária apenas como backup para problemas de shader em versões antigas (1.09x). Com o sombreamento muito melhorado, esta opção não é mais necessária.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;:</b> &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05E9;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D1;&#x05E0;&#x05E4;&#x05E8;&#x05D3;, &#x05DB;&#x05DA; &#x05E9;&#x05EA;&#x05D5;&#x05DB;&#x05DC;&#x05D5; &#x05DC;&#x05D9;&#x05E6;&#x05D5;&#x05E8; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D2;&#x05D5;&#x05D5;&#x05E0;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05DC;&#x05D4; &#x05D5;&#x05D4;&#x05E7;&#x05D8;&#x05E0;&#x05D4;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05EA;&#x05E7;&#x05E8;&#x05D1; &#x05D5;&#x05DC;&#x05D4;&#x05EA;&#x05E8;&#x05D7;&#x05E7; &#x05DE;&#x05D4;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05E4;&#x05E8;&#x05D8;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D6;&#x05D6;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DA;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E2;&#x05DC; &#x05D9;&#x05D3;&#x05D9; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05D9;&#x05D3;, &#x05DE;&#x05D4; &#x05E9;&#x05E2;&#x05D5;&#x05D6;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DC; &#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05D4;&#x05EA;&#x05D7;&#x05DC;&#x05EA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4;:</b> &#x05DB;&#x05E9;&#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D4; &#x05D1;&#x05E4;&#x05E2;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D4;, &#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05DC;&#x05D7;&#x05D5;&#x05E5; &#x05E2;&#x05DC; "&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;" &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05DC;&#x05E6;&#x05D9;&#x05D9;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05EA;&#x05E7;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E0;&#x05D2;&#x05E8;&#x05DE;&#x05D5; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;, &#x05DB;&#x05DE;&#x05D5; &#x05DC;&#x05DE;&#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05D9;&#x05E6;&#x05E8;&#x05D5; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D6;&#x05DE;&#x05E0;&#x05D9; &#x05D5;&#x05DC;&#x05D0; &#x05E1;&#x05D9;&#x05E4;&#x05E7;&#x05D5; &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05D7;&#x05DC;&#x05E7;&#x05D4;.</li>
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
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Control del ancho de las hebras:</b> Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.</li>
        <li><b>Zoom acercar/alejar:</b> Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.</li>
        <li><b>Mover pantalla:</b> Puedes arrastrar el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.</li>
        <li><b>Modo solo sombra:</b> Ahora puedes ocultar una capa mientras sigues mostrando sus sombras y luces haciendo clic derecho en un botón de capa y seleccionando "Solo Sombra". Esto ayuda a visualizar los efectos de sombra sin el desorden visual.</li>
        <li><b>Configuración inicial:</b> Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.</li>
        <li><b>Correcciones generales:</b> Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.</li>
        <li><b>Renderizado de mayor calidad:</b> Mejora en la calidad de visualización del lienzo y exportación de imágenes con resolución 4x más alta para resultados nítidos y profesionales.</li>
        <li><b>Eliminada opción de máscara extendida:</b> La opción de máscara extendida de la capa general ha sido eliminada ya que solo era necesaria como respaldo para problemas de shader en versiones anteriores (1.09x). Con el sombreado considerablemente mejorado, esta opción ya no es necesaria.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.101</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li><b>Strand Width Control:</b> You can now dynamically adjust the width of individual strands, giving you more flexibility in creating varied knot designs.</li>
        <li><b>Zoom In/Out:</b> You can zoom in and out of your design to see small details or the entire diagram.</li>
        <li><b>Pan Screen:</b> You can drag the canvas by clicking the hand button, which helps when working on larger diagrams.</li>
        <li><b>Shadow-Only Mode:</b> You can now hide a layer while still showing its shadows and highlights by right-clicking on a layer button and selecting "Shadow Only". This helps visualize shadow effects without the visual clutter.</li>
        <li><b>Initial Setup:</b> When first starting the application, you'll need to click "New Strand" to begin creating your first strand.</li>
        <li><b>General Fixes:</b> Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.</li>
        <li><b>Higher Quality Rendering:</b> Improved canvas display quality and 4x higher resolution image export for crisp, professional results.</li>
        <li><b>Removed Extended Mask Option:</b> The extended mask option from the general layer has been removed since it was only needed as a backup for shader issues in older versions (1.09x). With greatly improved shading, this option is no longer necessary.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôle de la largeur des brins :</b> Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.</li>
        <li><b>Zoom avant/arrière :</b> Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.</li>
        <li><b>Déplacement de l'écran :</b> Vous pouvez faire glisser le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.</li>
        <li><b>Mode ombre uniquement :</b> Vous pouvez maintenant masquer une couche tout en affichant ses ombres et reflets en faisant un clic droit sur un bouton de couche et en sélectionnant "Ombre uniquement". Cela aide à visualiser les effets d'ombre sans l'encombrement visuel.</li>
        <li><b>Configuration initiale :</b> Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.</li>
        <li><b>Corrections générales :</b> Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.</li>
        <li><b>Rendu de qualité supérieure :</b> Amélioration de la qualité d'affichage du canevas et export d'images en résolution 4x plus élevée pour des résultats nets et professionnels.</li>
        <li><b>Suppression de l'option masque étendu :</b> L'option masque étendu de la couche générale a été supprimée car elle était uniquement nécessaire comme solution de secours pour les problèmes de shader dans les anciennes versions (1.09x). Avec l'ombrage grandement amélioré, cette option n'est plus nécessaire.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controllo della larghezza dei trefoli:</b> Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.</li>
        <li><b>Zoom avanti/indietro:</b> Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.</li>
        <li><b>Spostamento schermo:</b> Puoi trascinare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.</li>
        <li><b>Modalità solo ombra:</b> Ora puoi nascondere un livello pur mostrando le sue ombre e luci facendo clic destro su un pulsante livello e selezionando "Solo Ombra". Questo aiuta a visualizzare gli effetti ombra senza il disordine visivo.</li>
        <li><b>Configurazione iniziale:</b> Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.</li>
        <li><b>Correzioni generali:</b> Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.</li>
        <li><b>Rendering di qualità superiore:</b> Migliorata la qualità di visualizzazione del canvas e esportazione immagini con risoluzione 4x più alta per risultati nitidi e professionali.</li>
        <li><b>Rimossa opzione maschera estesa:</b> L'opzione maschera estesa dal livello generale è stata rimossa poiché era necessaria solo come backup per problemi di shader nelle versioni precedenti (1.09x). Con l'ombreggiatura notevolmente migliorata, questa opzione non è più necessaria.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controle de largura dos fios:</b> Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.</li>
        <li><b>Zoom ampliar/reduzir:</b> Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.</li>
        <li><b>Mover tela:</b> Você pode arrastar o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.</li>
        <li><b>Modo apenas sombra:</b> Agora você pode ocultar uma camada enquanto ainda mostra suas sombras e destaques clicando com o botão direito em um botão de camada e selecionando "Apenas Sombra". Isso ajuda a visualizar efeitos de sombra sem a desordem visual.</li>
        <li><b>Configuração inicial:</b> Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.</li>
        <li><b>Correções gerais:</b> Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.</li>
        <li><b>Renderização de qualidade superior:</b> Melhoria na qualidade de exibição do canvas e exportação de imagens com resolução 4x mais alta para resultados nítidos e profissionais.</li>
        <li><b>Removida opção de máscara estendida:</b> A opção de máscara estendida da camada geral foi removida pois era necessária apenas como backup para problemas de shader em versões antigas (1.09x). Com o sombreamento muito melhorado, esta opção não é mais necessária.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;:</b> &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05E9;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D1;&#x05E0;&#x05E4;&#x05E8;&#x05D3;, &#x05DB;&#x05DA; &#x05E9;&#x05EA;&#x05D5;&#x05DB;&#x05DC;&#x05D5; &#x05DC;&#x05D9;&#x05E6;&#x05D5;&#x05E8; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D2;&#x05D5;&#x05D5;&#x05E0;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05DC;&#x05D4; &#x05D5;&#x05D4;&#x05E7;&#x05D8;&#x05E0;&#x05D4;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05EA;&#x05E7;&#x05E8;&#x05D1; &#x05D5;&#x05DC;&#x05D4;&#x05EA;&#x05E8;&#x05D7;&#x05E7; &#x05DE;&#x05D4;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05E4;&#x05E8;&#x05D8;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D6;&#x05D6;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DA;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E2;&#x05DC; &#x05D9;&#x05D3;&#x05D9; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05D9;&#x05D3;, &#x05DE;&#x05D4; &#x05E9;&#x05E2;&#x05D5;&#x05D6;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DC; &#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05D4;&#x05EA;&#x05D7;&#x05DC;&#x05EA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4;:</b> &#x05DB;&#x05E9;&#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D4; &#x05D1;&#x05E4;&#x05E2;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D4;, &#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05DC;&#x05D7;&#x05D5;&#x05E5; &#x05E2;&#x05DC; "&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;" &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05DC;&#x05E6;&#x05D9;&#x05D9;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05EA;&#x05E7;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E0;&#x05D2;&#x05E8;&#x05DE;&#x05D5; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;, &#x05DB;&#x05DE;&#x05D5; &#x05DC;&#x05DE;&#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05D9;&#x05E6;&#x05E8;&#x05D5; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D6;&#x05DE;&#x05E0;&#x05D9; &#x05D5;&#x05DC;&#x05D0; &#x05E1;&#x05D9;&#x05E4;&#x05E7;&#x05D5; &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05D7;&#x05DC;&#x05E7;&#x05D4;.</li>
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
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controle de largura dos fios:</b> Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.</li>
        <li><b>Zoom ampliar/reduzir:</b> Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.</li>
        <li><b>Mover tela:</b> Você pode arrastar o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.</li>
        <li><b>Modo apenas sombra:</b> Agora você pode ocultar uma camada enquanto ainda mostra suas sombras e destaques clicando com o botão direito em um botão de camada e selecionando "Apenas Sombra". Isso ajuda a visualizar efeitos de sombra sem a desordem visual.</li>
        <li><b>Configuração inicial:</b> Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.</li>
        <li><b>Correções gerais:</b> Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.</li>
        <li><b>Renderização de qualidade superior:</b> Melhoria na qualidade de exibição do canvas e exportação de imagens com resolução 4x mais alta para resultados nítidos e profissionais.</li>
        <li><b>Removida opção de máscara estendida:</b> A opção de máscara estendida da camada geral foi removida pois era necessária apenas como backup para problemas de shader em versões antigas (1.09x). Com o sombreamento muito melhorado, esta opção não é mais necessária.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.101</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li><b>Strand Width Control:</b> You can now dynamically adjust the width of individual strands, giving you more flexibility in creating varied knot designs.</li>
        <li><b>Zoom In/Out:</b> You can zoom in and out of your design to see small details or the entire diagram.</li>
        <li><b>Pan Screen:</b> You can drag the canvas by clicking the hand button, which helps when working on larger diagrams.</li>
        <li><b>Shadow-Only Mode:</b> You can now hide a layer while still showing its shadows and highlights by right-clicking on a layer button and selecting "Shadow Only". This helps visualize shadow effects without the visual clutter.</li>
        <li><b>Initial Setup:</b> When first starting the application, you'll need to click "New Strand" to begin creating your first strand.</li>
        <li><b>General Fixes:</b> Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.</li>
        <li><b>Higher Quality Rendering:</b> Improved canvas display quality and 4x higher resolution image export for crisp, professional results.</li>
        <li><b>Removed Extended Mask Option:</b> The extended mask option from the general layer has been removed since it was only needed as a backup for shader issues in older versions (1.09x). With greatly improved shading, this option is no longer necessary.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôle de la largeur des brins :</b> Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.</li>
        <li><b>Zoom avant/arrière :</b> Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.</li>
        <li><b>Déplacement de l'écran :</b> Vous pouvez faire glisser le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.</li>
        <li><b>Mode ombre uniquement :</b> Vous pouvez maintenant masquer une couche tout en affichant ses ombres et reflets en faisant un clic droit sur un bouton de couche et en sélectionnant "Ombre uniquement". Cela aide à visualiser les effets d'ombre sans l'encombrement visuel.</li>
        <li><b>Configuration initiale :</b> Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.</li>
        <li><b>Corrections générales :</b> Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.</li>
        <li><b>Rendu de qualité supérieure :</b> Amélioration de la qualité d'affichage du canevas et export d'images en résolution 4x plus élevée pour des résultats nets et professionnels.</li>
        <li><b>Suppression de l'option masque étendu :</b> L'option masque étendu de la couche générale a été supprimée car elle était uniquement nécessaire comme solution de secours pour les problèmes de shader dans les anciennes versions (1.09x). Avec l'ombrage grandement amélioré, cette option n'est plus nécessaire.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controllo della larghezza dei trefoli:</b> Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.</li>
        <li><b>Zoom avanti/indietro:</b> Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.</li>
        <li><b>Spostamento schermo:</b> Puoi trascinare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.</li>
        <li><b>Modalità solo ombra:</b> Ora puoi nascondere un livello pur mostrando le sue ombre e luci facendo clic destro su un pulsante livello e selezionando "Solo Ombra". Questo aiuta a visualizzare gli effetti ombra senza il disordine visivo.</li>
        <li><b>Configurazione iniziale:</b> Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.</li>
        <li><b>Correzioni generali:</b> Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.</li>
        <li><b>Rendering di qualità superiore:</b> Migliorata la qualità di visualizzazione del canvas e esportazione immagini con risoluzione 4x più alta per risultati nitidi e professionali.</li>
        <li><b>Rimossa opzione maschera estesa:</b> L'opzione maschera estesa dal livello generale è stata rimossa poiché era necessaria solo come backup per problemi di shader nelle versioni precedenti (1.09x). Con l'ombreggiatura notevolmente migliorata, questa opzione non è più necessaria.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Control del ancho de las hebras:</b> Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.</li>
        <li><b>Zoom acercar/alejar:</b> Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.</li>
        <li><b>Mover pantalla:</b> Puedes arrastrar el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.</li>
        <li><b>Modo solo sombra:</b> Ahora puedes ocultar una capa mientras sigues mostrando sus sombras y luces haciendo clic derecho en un botón de capa y seleccionando "Solo Sombra". Esto ayuda a visualizar los efectos de sombra sin el desorden visual.</li>
        <li><b>Configuración inicial:</b> Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.</li>
        <li><b>Correcciones generales:</b> Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.</li>
        <li><b>Renderizado de mayor calidad:</b> Mejora en la calidad de visualización del lienzo y exportación de imágenes con resolución 4x más alta para resultados nítidos y profesionales.</li>
        <li><b>Eliminada opción de máscara extendida:</b> La opción de máscara extendida de la capa general ha sido eliminada ya que solo era necesaria como respaldo para problemas de shader en versiones anteriores (1.09x). Con el sombreado considerablemente mejorado, esta opción ya no es necesaria.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;:</b> &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05E9;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D1;&#x05E0;&#x05E4;&#x05E8;&#x05D3;, &#x05DB;&#x05DA; &#x05E9;&#x05EA;&#x05D5;&#x05DB;&#x05DC;&#x05D5; &#x05DC;&#x05D9;&#x05E6;&#x05D5;&#x05E8; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D2;&#x05D5;&#x05D5;&#x05E0;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05DC;&#x05D4; &#x05D5;&#x05D4;&#x05E7;&#x05D8;&#x05E0;&#x05D4;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05EA;&#x05E7;&#x05E8;&#x05D1; &#x05D5;&#x05DC;&#x05D4;&#x05EA;&#x05E8;&#x05D7;&#x05E7; &#x05DE;&#x05D4;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05E4;&#x05E8;&#x05D8;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D6;&#x05D6;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DA;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E2;&#x05DC; &#x05D9;&#x05D3;&#x05D9; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05D9;&#x05D3;, &#x05DE;&#x05D4; &#x05E9;&#x05E2;&#x05D5;&#x05D6;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DC; &#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05D4;&#x05EA;&#x05D7;&#x05DC;&#x05EA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4;:</b> &#x05DB;&#x05E9;&#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D4; &#x05D1;&#x05E4;&#x05E2;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D4;, &#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05DC;&#x05D7;&#x05D5;&#x05E5; &#x05E2;&#x05DC; "&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;" &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05DC;&#x05E6;&#x05D9;&#x05D9;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05EA;&#x05E7;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E0;&#x05D2;&#x05E8;&#x05DE;&#x05D5; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;, &#x05DB;&#x05DE;&#x05D5; &#x05DC;&#x05DE;&#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05D9;&#x05E6;&#x05E8;&#x05D5; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D6;&#x05DE;&#x05E0;&#x05D9; &#x05D5;&#x05DC;&#x05D0; &#x05E1;&#x05D9;&#x05E4;&#x05E7;&#x05D5; &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05D7;&#x05DC;&#x05E7;&#x05D4;.</li>
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
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9; &#x05E8;&#x05D5;&#x05D7;&#x05D1; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;:</b> &#x05E2;&#x05DB;&#x05E9;&#x05D9;&#x05D5; &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05E9;&#x05E0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05D4;&#x05E2;&#x05D5;&#x05D1;&#x05D9; &#x05E9;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D1;&#x05E0;&#x05E4;&#x05E8;&#x05D3;, &#x05DB;&#x05DA; &#x05E9;&#x05EA;&#x05D5;&#x05DB;&#x05DC;&#x05D5; &#x05DC;&#x05D9;&#x05E6;&#x05D5;&#x05E8; &#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1;&#x05D9;&#x05DD; &#x05D9;&#x05D5;&#x05EA;&#x05E8; &#x05DE;&#x05D2;&#x05D5;&#x05D5;&#x05E0;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05DC;&#x05D4; &#x05D5;&#x05D4;&#x05E7;&#x05D8;&#x05E0;&#x05D4;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05EA;&#x05E7;&#x05E8;&#x05D1; &#x05D5;&#x05DC;&#x05D4;&#x05EA;&#x05E8;&#x05D7;&#x05E7; &#x05DE;&#x05D4;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05E4;&#x05E8;&#x05D8;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D6;&#x05D6;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DA;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E2;&#x05DC; &#x05D9;&#x05D3;&#x05D9; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05D9;&#x05D3;, &#x05DE;&#x05D4; &#x05E9;&#x05E2;&#x05D5;&#x05D6;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DC; &#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05D4;&#x05EA;&#x05D7;&#x05DC;&#x05EA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4;:</b> &#x05DB;&#x05E9;&#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D4; &#x05D1;&#x05E4;&#x05E2;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D4;, &#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05DC;&#x05D7;&#x05D5;&#x05E5; &#x05E2;&#x05DC; "&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;" &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05DC;&#x05E6;&#x05D9;&#x05D9;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05EA;&#x05E7;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E0;&#x05D2;&#x05E8;&#x05DE;&#x05D5; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;, &#x05DB;&#x05DE;&#x05D5; &#x05DC;&#x05DE;&#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05D9;&#x05E6;&#x05E8;&#x05D5; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D6;&#x05DE;&#x05E0;&#x05D9; &#x05D5;&#x05DC;&#x05D0; &#x05E1;&#x05D9;&#x05E4;&#x05E7;&#x05D5; &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05D7;&#x05DC;&#x05E7;&#x05D4;.</li>
    </ul>
    </div>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.101</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li><b>Strand Width Control:</b> You can now dynamically adjust the width of individual strands, giving you more flexibility in creating varied knot designs.</li>
        <li><b>Zoom In/Out:</b> You can zoom in and out of your design to see small details or the entire diagram.</li>
        <li><b>Pan Screen:</b> You can drag the canvas by clicking the hand button, which helps when working on larger diagrams.</li>
        <li><b>Shadow-Only Mode:</b> You can now hide a layer while still showing its shadows and highlights by right-clicking on a layer button and selecting "Shadow Only". This helps visualize shadow effects without the visual clutter.</li>
        <li><b>Initial Setup:</b> When first starting the application, you'll need to click "New Strand" to begin creating your first strand.</li>
        <li><b>General Fixes:</b> Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.</li>
        <li><b>Higher Quality Rendering:</b> Improved canvas display quality and 4x higher resolution image export for crisp, professional results.</li>
        <li><b>Removed Extended Mask Option:</b> The extended mask option from the general layer has been removed since it was only needed as a backup for shader issues in older versions (1.09x). With greatly improved shading, this option is no longer necessary.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôle de la largeur des brins :</b> Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.</li>
        <li><b>Zoom avant/arrière :</b> Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.</li>
        <li><b>Déplacement de l'écran :</b> Vous pouvez faire glisser le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.</li>
        <li><b>Mode ombre uniquement :</b> Vous pouvez maintenant masquer une couche tout en affichant ses ombres et reflets en faisant un clic droit sur un bouton de couche et en sélectionnant "Ombre uniquement". Cela aide à visualiser les effets d'ombre sans l'encombrement visuel.</li>
        <li><b>Configuration initiale :</b> Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.</li>
        <li><b>Corrections générales :</b> Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.</li>
        <li><b>Rendu de qualité supérieure :</b> Amélioration de la qualité d'affichage du canevas et export d'images en résolution 4x plus élevée pour des résultats nets et professionnels.</li>
        <li><b>Suppression de l'option masque étendu :</b> L'option masque étendu de la couche générale a été supprimée car elle était uniquement nécessaire comme solution de secours pour les problèmes de shader dans les anciennes versions (1.09x). Avec l'ombrage grandement amélioré, cette option n'est plus nécessaire.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controllo della larghezza dei trefoli:</b> Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.</li>
        <li><b>Zoom avanti/indietro:</b> Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.</li>
        <li><b>Spostamento schermo:</b> Puoi trascinare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.</li>
        <li><b>Modalità solo ombra:</b> Ora puoi nascondere un livello pur mostrando le sue ombre e luci facendo clic destro su un pulsante livello e selezionando "Solo Ombra". Questo aiuta a visualizzare gli effetti ombra senza il disordine visivo.</li>
        <li><b>Configurazione iniziale:</b> Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.</li>
        <li><b>Correzioni generali:</b> Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.</li>
        <li><b>Rendering di qualità superiore:</b> Migliorata la qualità di visualizzazione del canvas e esportazione immagini con risoluzione 4x più alta per risultati nitidi e professionali.</li>
        <li><b>Rimossa opzione maschera estesa:</b> L'opzione maschera estesa dal livello generale è stata rimossa poiché era necessaria solo come backup per problemi di shader nelle versioni precedenti (1.09x). Con l'ombreggiatura notevolmente migliorata, questa opzione non è più necessaria.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Control del ancho de las hebras:</b> Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.</li>
        <li><b>Zoom acercar/alejar:</b> Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.</li>
        <li><b>Mover pantalla:</b> Puedes arrastrar el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.</li>
        <li><b>Modo solo sombra:</b> Ahora puedes ocultar una capa mientras sigues mostrando sus sombras y luces haciendo clic derecho en un botón de capa y seleccionando "Solo Sombra". Esto ayuda a visualizar los efectos de sombra sin el desorden visual.</li>
        <li><b>Configuración inicial:</b> Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.</li>
        <li><b>Correcciones generales:</b> Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.</li>
        <li><b>Renderizado de mayor calidad:</b> Mejora en la calidad de visualización del lienzo y exportación de imágenes con resolución 4x más alta para resultados nítidos y profesionales.</li>
        <li><b>Eliminada opción de máscara extendida:</b> La opción de máscara extendida de la capa general ha sido eliminada ya que solo era necesaria como respaldo para problemas de shader en versiones anteriores (1.09x). Con el sombreado considerablemente mejorado, esta opción ya no es necesaria.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controle de largura dos fios:</b> Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.</li>
        <li><b>Zoom ampliar/reduzir:</b> Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.</li>
        <li><b>Mover tela:</b> Você pode arrastar o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.</li>
        <li><b>Modo apenas sombra:</b> Agora você pode ocultar uma camada enquanto ainda mostra suas sombras e destaques clicando com o botão direito em um botão de camada e selecionando "Apenas Sombra". Isso ajuda a visualizar efeitos de sombra sem a desordem visual.</li>
        <li><b>Configuração inicial:</b> Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.</li>
        <li><b>Correções gerais:</b> Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.</li>
        <li><b>Renderização de qualidade superior:</b> Melhoria na qualidade de exibição do canvas e exportação de imagens com resolução 4x mais alta para resultados nítidos e profissionais.</li>
        <li><b>Removida opção de máscara estendida:</b> A opção de máscara estendida da camada geral foi removida pois era necessária apenas como backup para problemas de shader em versões antigas (1.09x). Com o sombreamento muito melhorado, esta opção não é mais necessária.</li>
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
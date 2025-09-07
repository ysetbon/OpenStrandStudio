#!/bin/bash

# Set variables
APP_NAME="OpenStrandStudio"
VERSION="1_102"
APP_DATE="07_September_2025"
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
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>SVG Shape Support:</b> Added new SVG-based shapes (circle, square, triangle) for improved rendering quality and scalability. These shapes now load correctly in both the application and exported executables.</li>
        <li><b>Enhanced Canvas Guides:</b> New control point SVG guides for better visual feedback when manipulating canvas elements.</li>
        <li><b>Translation improvements</b> for canvas guide elements.</li>
        <li><b>Improved color consistency</b> for button explanation titles.</li>
    </ul>
    <p>Previous updates (1.101):</p>
    <ul>
        <li>Improved Layer Management, Group Duplication, Hide Mode, Center View, Quick Knot Closing</li>
        <li>New Language - German (🇩🇪)</li>
        <li>New Samples category</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbesserte Ebenenverwaltung:</b> Verbesserte StateLayerManager-Struktur für zuverlässigeres Handling von Knotenverbindungen und Strangbeziehungen, mit stabileren Operationen und besserer Performance.</li>
        <li><b>Gruppenduplikation:</b> Sie können jetzt ganze Gruppen mit allen ihren Strängen duplizieren, indem Sie mit der rechten Maustaste auf eine Gruppenüberschrift klicken und "Gruppe duplizieren" auswählen. Die duplizierte Gruppe behält alle Strangeigenschaften bei und generiert automatisch eindeutige Ebenennamen.</li>
        <li><b>Versteckmodus:</b> Neuer Versteckmodus, der über die Affen-Schaltfläche (🙉/🙈) zugänglich ist, ermöglicht es Ihnen, mehrere Ebenen schnell gleichzeitig auszublenden. Klicken Sie auf die Schaltfläche, um in den Versteckmodus zu wechseln, klicken Sie dann auf Ebenen, um sie auszublenden. Verlassen Sie den Versteckmodus, um die Änderungen zu übernehmen.</li>
        <li><b>Ansicht zentrieren:</b> Zentrieren Sie sofort alle Stränge in Ihrer Ansicht mit der neuen Ziel-Schaltfläche (🎯). Dies passt automatisch die Leinwandposition an, um alle Ihre Arbeit zentriert auf dem Bildschirm anzuzeigen.</li>
        <li><b>Schnelles Knotenschließen:</b> Klicken Sie mit der rechten Maustaste auf einen beliebigen Strang oder verbundenen Strang mit einem freien Ende, um den Knoten schnell zu schließen. Das System findet und verbindet automatisch mit dem nächstgelegenen kompatiblen Strang mit einem freien Ende.</li>
        <li><b>Neue Sprache – Deutsch (🇩🇪):</b> Sie können jetzt zu Deutsch in Einstellungen → Sprache ändern wechseln.</li>
        <li><b>Neue Kategorie „Beispiele" :</b> Entdecken Sie bereit-zu-ladende Beispielprojekte in Einstellungen → Beispiele. Wählen Sie ein Beispiel zum Lernen; der Dialog schließt sich und das Beispiel wird geladen.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Gestion améliorée des couches :</b> Structure StateLayerManager améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.</li>
        <li><b>Duplication de groupe :</b> Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant "Dupliquer le groupe". Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.</li>
        <li><b>Mode masquage :</b> Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permet de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches pour les masquer. Quittez le mode masquage pour appliquer les changements.</li>
        <li><b>Centrer la vue :</b> Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). Cela ajuste automatiquement la position du canevas pour afficher tout votre travail centré à l'écran.</li>
        <li><b>Fermeture rapide de nœud :</b> Cliquez avec le bouton droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et connecte automatiquement au brin compatible le plus proche avec une extrémité libre.</li>
        <li><b>Nouvelle langue - Allemand (🇩🇪) :</b> Vous pouvez maintenant sélectionner l'allemand dans Paramètres → Changer la langue.</li>
        <li><b>Nouvelle catégorie Exemples :</b> Découvrez des projets d'exemple prêts à charger dans Paramètres → Exemples. Choisissez un exemple pour apprendre ; la boîte de dialogue se fermera et l'exemple sera chargé.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Gestione livelli migliorata:</b> Struttura StateLayerManager migliorata per una migliore gestione delle connessioni dei nodi e delle relazioni tra trefoli, offrendo operazioni sui livelli più affidabili e prestazioni migliorate.</li>
        <li><b>Duplicazione gruppo:</b> Ora puoi duplicare interi gruppi con tutti i loro trefoli facendo clic destro sull'intestazione di un gruppo e selezionando "Duplica gruppo". Il gruppo duplicato mantiene tutte le proprietà dei trefoli e genera automaticamente nomi di livelli unici.</li>
        <li><b>Modalità nascondi:</b> Nuova modalità nascondi accessibile tramite il pulsante scimmia (🙉/🙈) permette di nascondere rapidamente più livelli contemporaneamente. Clicca sul pulsante per entrare in modalità nascondi, poi clicca sui livelli per nasconderli. Esci dalla modalità nascondi per applicare le modifiche.</li>
        <li><b>Centra vista:</b> Centra istantaneamente tutti i trefoli nella tua vista con il nuovo pulsante bersaglio (🎯). Questo regola automaticamente la posizione del canvas per mostrare tutto il tuo lavoro centrato sullo schermo.</li>
        <li><b>Chiusura rapida del nodo:</b> Fai clic destro su qualsiasi trefolo o trefolo attaccato con un'estremità libera per chiudere rapidamente il nodo. Il sistema trova e connette automaticamente al trefolo compatibile più vicino con un'estremità libera.</li>
        <li><b>Nuova lingua - Tedesco (🇩🇪):</b> Ora puoi selezionare il tedesco in Impostazioni → Cambia Lingua.</li>
        <li><b>Nuova categoria Esempi:</b> Scopri progetti di esempio pronti al caricamento in Impostazioni → Esempi. Scegli un esempio da cui imparare; la finestra si chiuderà e l'esempio verrà caricato.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Gestión mejorada de capas:</b> Estructura StateLayerManager mejorada para un mejor manejo de las conexiones de nudos y relaciones entre hebras, ofreciendo operaciones de capas más confiables y mejor rendimiento.</li>
        <li><b>Duplicación de grupo:</b> Ahora puedes duplicar grupos completos con todas sus hebras haciendo clic derecho en el encabezado de un grupo y seleccionando "Duplicar grupo". El grupo duplicado mantiene todas las propiedades de las hebras y genera automáticamente nombres de capas únicos.</li>
        <li><b>Modo ocultar:</b> Nuevo modo ocultar accesible a través del botón mono (🙉/🙈) permite ocultar rápidamente múltiples capas a la vez. Haz clic en el botón para entrar en modo ocultar, luego haz clic en las capas para ocultarlas. Sal del modo ocultar para aplicar los cambios.</li>
        <li><b>Centrar vista:</b> Centra instantáneamente todas las hebras en tu vista con el nuevo botón diana (🎯). Esto ajusta automáticamente la posición del lienzo para mostrar todo tu trabajo centrado en la pantalla.</li>
        <li><b>Cierre rápido de nudo:</b> Haz clic derecho en cualquier hebra o hebra adjunta con un extremo libre para cerrar rápidamente el nudo. El sistema encuentra y conecta automáticamente a la hebra compatible más cercana con un extremo libre.</li>
        <li><b>Nuevo idioma - Alemán (🇩🇪):</b> Ahora puedes cambiar a alemán en Configuración → Cambiar Idioma.</li>
        <li><b>Nueva categoría Ejemplos:</b> Explora proyectos de ejemplo listos para cargar en Configuración → Ejemplos. Elige un ejemplo para aprender; el cuadro de diálogo se cerrará y el ejemplo se cargará.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Gestão melhorada de camadas:</b> Estrutura StateLayerManager melhorada para melhor gestão de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.</li>
        <li><b>Duplicação de grupo:</b> Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar Grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.</li>
        <li><b>Modo ocultar:</b> Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente múltiplas camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.</li>
        <li><b>Centralizar vista:</b> Centralize instantaneamente todos os fios na sua vista com o novo botão alvo (🎯). Isso ajusta automaticamente a posição da tela para mostrar todo o seu trabalho centralizado na tela.</li>
        <li><b>Fechamento rápido de nó:</b> Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio compatível mais próximo com uma extremidade livre.</li>
        <li><b>Nova língua - Alemão (🇩🇪):</b> Agora você pode selecionar alemão em Configurações → Alterar Idioma.</li>
        <li><b>Nova categoria Exemplos:</b> Explore projetos de exemplo prontos para carregar em Configurações → Exemplos. Escolha um exemplo para aprender; a caixa de diálogo fechará e o exemplo será carregado.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;:</b> &#x05DE;&#x05D1;&#x05E0;&#x05D4; StateLayerManager &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05D8;&#x05D5;&#x05D1; &#x05D1;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D7;&#x05E1;&#x05D9;&#x05DD; &#x05D1;&#x05D9;&#x05BF; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DE;&#x05D9;&#x05D1;&#x05D9;&#x05D0; &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D0;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05DC;&#x05D4; &#x05D5;&#x05D4;&#x05E7;&#x05D8;&#x05E0;&#x05D4;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05EA;&#x05E7;&#x05E8;&#x05D1; &#x05D5;&#x05DC;&#x05D4;&#x05EA;&#x05E8;&#x05D7;&#x05E7; &#x05DE;&#x05D4;&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E9;&#x05DC;&#x05DB;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05E4;&#x05E8;&#x05D8;&#x05D9;&#x05DD; &#x05E7;&#x05D8;&#x05E0;&#x05D9;&#x05DD; &#x05D0;&#x05D5; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D4;.</li>
        <li><b>&#x05D4;&#x05D6;&#x05D6;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DA;:</b> &#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05D6;&#x05D9;&#x05D6; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05E2;&#x05DC; &#x05D9;&#x05D3;&#x05D9; &#x05DC;&#x05D7;&#x05D9;&#x05E6;&#x05D4; &#x05E2;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8; &#x05D4;&#x05D9;&#x05D3;, &#x05DE;&#x05D4; &#x05E9;&#x05E2;&#x05D5;&#x05D6;&#x05E8; &#x05D1;&#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4; &#x05E2;&#x05DC; &#x05D3;&#x05D9;&#x05D0;&#x05D2;&#x05E8;&#x05DE;&#x05D5;&#x05EA; &#x05D2;&#x05D3;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
        <li><b>&#x05D4;&#x05EA;&#x05D7;&#x05DC;&#x05EA; &#x05E2;&#x05D1;&#x05D5;&#x05D3;&#x05D4;:</b> &#x05DB;&#x05E9;&#x05E4;&#x05D5;&#x05EA;&#x05D7;&#x05D9;&#x05DD; &#x05D0;&#x05EA; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D4; &#x05D1;&#x05E4;&#x05E2;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D4;, &#x05E6;&#x05E8;&#x05D9;&#x05DA; &#x05DC;&#x05DC;&#x05D7;&#x05D5;&#x05E5; &#x05E2;&#x05DC; "&#x05D7;&#x05D5;&#x05D8; &#x05D7;&#x05D3;&#x05E9;" &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05EA;&#x05D7;&#x05D9;&#x05DC; &#x05DC;&#x05E6;&#x05D9;&#x05D9;&#x05E8;.</li>
        <li><b>&#x05EA;&#x05D9;&#x05E7;&#x05D5;&#x05E0;&#x05D9;&#x05DD; &#x05DB;&#x05DC;&#x05DC;&#x05D9;&#x05D9;&#x05DD;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05EA;&#x05E7;&#x05DC;&#x05D5;&#x05EA; &#x05D5;&#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05E0;&#x05D2;&#x05E8;&#x05DE;&#x05D5; &#x05DE;&#x05D2;&#x05E8;&#x05E1;&#x05D0;&#x05D5;&#x05EA; &#x05E7;&#x05D5;&#x05D3;&#x05DE;&#x05D5;&#x05EA;, &#x05DB;&#x05DE;&#x05D5; &#x05DC;&#x05DE;&#x05E9;&#x05DC; &#x05DB;&#x05E4;&#x05EA;&#x05D5;&#x05E8;&#x05D9; &#x05D1;&#x05D9;&#x05D8;&#x05D5;&#x05DC; &#x05D5;&#x05D7;&#x05D6;&#x05E8;&#x05D4; &#x05D9;&#x05E6;&#x05E8;&#x05D5; &#x05D7;&#x05DC;&#x05D5;&#x05DF; &#x05D6;&#x05DE;&#x05E0;&#x05D9; &#x05D5;&#x05DC;&#x05D0; &#x05E1;&#x05D9;&#x05E4;&#x05E7;&#x05D5; &#x05D7;&#x05D5;&#x05D5;&#x05D9;&#x05EA; &#x05DE;&#x05E9;&#x05EA;&#x05DE;&#x05E9; &#x05D7;&#x05DC;&#x05E7;&#x05D4;.</li>
        <li><b>&#x05E9;&#x05E4;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; - &#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; (🇩🇪):</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05E9;&#x05E0;&#x05D9;&#x05EA; &#x05E9;&#x05E4;&#x05D4;.</li>
        <li><b>&#x05E7;&#x05D8;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05E9;&#x05DC; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;:</b> &#x05D7;&#x05E7;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD; &#x05D4;&#x05E8;&#x05D9;&#x05D9;&#x05DD; &#x05DC;&#x05D8;&#x05D5;&#x05D7;&#x05D4; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;. &#x05D1;&#x05D7;&#x05E7;&#x05E8; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05DC;&#x05DC;&#x05DE;&#x05D9;&#x05D3; - &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05DC;&#x05D5;&#x05D2; &#x05D9;&#x05D9;&#x05E1;&#x05D5;&#x05D2; &#x05D5;&#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05D9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;.</li>
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

# Create welcome.html  (welcome French + localized sections). Updated to 1.101 what's-new.
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
        <li><b>Gestion améliorée des couches :</b> Structure StateLayerManager améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.</li>
        <li><b>Duplication de groupe :</b> Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant "Dupliquer le groupe". Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.</li>
        <li><b>Mode masquage :</b> Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permet de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches pour les masquer. Quittez le mode masquage pour appliquer les changements.</li>
        <li><b>Centrer la vue :</b> Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). Cela ajuste automatiquement la position du canevas pour afficher tout votre travail centré à l'écran.</li>
        <li><b>Fermeture rapide de nœud :</b> Cliquez avec le bouton droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et connecte automatiquement au brin compatible le plus proche avec une extrémité libre.</li>
        <li><b>Nouvelle langue - Allemand (🇩🇪) :</b> Vous pouvez maintenant sélectionner l'allemand dans Paramètres → Changer la langue.</li>
        <li><b>Nouvelle catégorie Exemples :</b> Découvrez des projets d'exemple prêts à charger dans Paramètres → Exemples. Choisissez un exemple pour apprendre ; la boîte de dialogue se fermera et l'exemple sera chargé.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>SVG Shape Support:</b> Added new SVG-based shapes (circle, square, triangle) for improved rendering quality and scalability. These shapes now load correctly in both the application and exported executables.</li>
        <li><b>Enhanced Canvas Guides:</b> New control point SVG guides for better visual feedback when manipulating canvas elements.</li>
        <li><b>Translation improvements</b> for canvas guide elements.</li>
        <li><b>Improved color consistency</b> for button explanation titles.</li>
    </ul>
    <p>Previous updates (1.101):</p>
    <ul>
        <li>Improved Layer Management, Group Duplication, Hide Mode, Center View, Quick Knot Closing</li>
        <li>New Language - German (🇩🇪)</li>
        <li>New Samples category</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbesserte Ebenenverwaltung:</b> Verbesserte StateLayerManager-Struktur für zuverlässigeres Handling von Knotenverbindungen und Strangbeziehungen, mit stabileren Operationen und besserer Performance.</li>
        <li><b>Gruppenduplikation:</b> Sie können jetzt ganze Gruppen mit allen ihren Strängen duplizieren, indem Sie mit der rechten Maustaste auf eine Gruppenüberschrift klicken und "Gruppe duplizieren" auswählen. Die duplizierte Gruppe behält alle Strangeigenschaften bei und generiert automatisch eindeutige Ebenennamen.</li>
        <li><b>Versteckmodus:</b> Neuer Versteckmodus, der über die Affen-Schaltfläche (🙉/🙈) zugänglich ist, ermöglicht es Ihnen, mehrere Ebenen schnell gleichzeitig auszublenden. Klicken Sie auf die Schaltfläche, um in den Versteckmodus zu wechseln, klicken Sie dann auf Ebenen, um sie auszublenden. Verlassen Sie den Versteckmodus, um die Änderungen zu übernehmen.</li>
        <li><b>Ansicht zentrieren:</b> Zentrieren Sie sofort alle Stränge in Ihrer Ansicht mit der neuen Ziel-Schaltfläche (🎯). Dies passt automatisch die Leinwandposition an, um alle Ihre Arbeit zentriert auf dem Bildschirm anzuzeigen.</li>
        <li><b>Schnelles Knotenschließen:</b> Klicken Sie mit der rechten Maustaste auf einen beliebigen Strang oder verbundenen Strang mit einem freien Ende, um den Knoten schnell zu schließen. Das System findet und verbindet automatisch mit dem nächstgelegenen kompatiblen Strang mit einem freien Ende.</li>
        <li><b>Neue Sprache – Deutsch (🇩🇪):</b> Sie können jetzt zu Deutsch in Einstellungen → Sprache ändern wechseln.</li>
        <li><b>Neue Kategorie „Beispiele" :</b> Entdecken Sie bereit-zu-ladende Beispielprojekte in Einstellungen → Beispiele. Wählen Sie ein Beispiel zum Lernen; der Dialog schließt sich und das Beispiel wird geladen.</li>
    </ul>
    <hr>

    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Gestione livelli migliorata:</b> Struttura StateLayerManager migliorata per una migliore gestione delle connessioni dei nodi e delle relazioni tra trefoli, offrendo operazioni sui livelli più affidabili e prestazioni migliorate.</li>
        <li><b>Duplicazione gruppo:</b> Ora puoi duplicare interi gruppi con tutti i loro trefoli facendo clic destro sull'intestazione di un gruppo e selezionando "Duplica gruppo". Il gruppo duplicato mantiene tutte le proprietà dei trefoli e genera automaticamente nomi di livelli unici.</li>
        <li><b>Modalità nascondi:</b> Nuova modalità nascondi accessibile tramite il pulsante scimmia (🙉/🙈) permette di nascondere rapidamente più livelli contemporaneamente. Clicca sul pulsante per entrare in modalità nascondi, poi clicca sui livelli per nasconderli. Esci dalla modalità nascondi per applicare le modifiche.</li>
        <li><b>Centra vista:</b> Centra istantaneamente tutti i trefoli nella tua vista con il nuovo pulsante bersaglio (🎯). Questo regola automaticamente la posizione del canvas per mostrare tutto il tuo lavoro centrato sullo schermo.</li>
        <li><b>Chiusura rapida del nodo:</b> Fai clic destro su qualsiasi trefolo o trefolo attaccato con un'estremità libera per chiudere rapidamente il nodo. Il sistema trova e connette automaticamente al trefolo compatibile più vicino con un'estremità libera.</li>
        <li><b>Nuova lingua - Tedesco (🇩🇪):</b> Ora puoi selezionare il tedesco in Impostazioni → Cambia Lingua.</li>
        <li><b>Nuova categoria Esempi:</b> Scopri progetti di esempio pronti al caricamento in Impostazioni → Esempi. Scegli un esempio da cui imparare; la finestra si chiuderà e l'esempio verrà caricato.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Gestión mejorada de capas:</b> Estructura StateLayerManager mejorada para un mejor manejo de las conexiones de nudos y relaciones entre hebras, ofreciendo operaciones de capas más confiables y mejor rendimiento.</li>
        <li><b>Duplicación de grupo:</b> Ahora puedes duplicar grupos completos con todas sus hebras haciendo clic derecho en el encabezado de un grupo y seleccionando "Duplicar grupo". El grupo duplicado mantiene todas las propiedades de las hebras y genera automáticamente nombres de capas únicos.</li>
        <li><b>Modo ocultar:</b> Nuevo modo ocultar accesible a través del botón mono (🙉/🙈) permite ocultar rápidamente múltiples capas a la vez. Haz clic en el botón para entrar en modo ocultar, luego haz clic en las capas para ocultarlas. Sal del modo ocultar para aplicar los cambios.</li>
        <li><b>Centrar vista:</b> Centra instantáneamente todas las hebras en tu vista con el nuevo botón diana (🎯). Esto ajusta automáticamente la posición del lienzo para mostrar todo tu trabajo centrado en la pantalla.</li>
        <li><b>Cierre rápido de nudo:</b> Haz clic derecho en cualquier hebra o hebra adjunta con un extremo libre para cerrar rápidamente el nudo. El sistema encuentra y conecta automáticamente a la hebra compatible más cercana con un extremo libre.</li>
        <li><b>Nuevo idioma - Alemán (🇩🇪):</b> Ahora puedes cambiar a alemán en Configuración → Cambiar Idioma.</li>
        <li><b>Nueva categoría Ejemplos:</b> Explora proyectos de ejemplo listos para cargar en Configuración → Ejemplos. Elige un ejemplo para aprender; el cuadro de diálogo se cerrará y el ejemplo se cargará.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Gestão melhorada de camadas:</b> Estrutura StateLayerManager melhorada para melhor gestão de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.</li>
        <li><b>Duplicação de grupo:</b> Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar Grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.</li>
        <li><b>Modo ocultar:</b> Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente múltiplas camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.</li>
        <li><b>Centralizar vista:</b> Centralize instantaneamente todos os fios na sua vista com o novo botão alvo (🎯). Isso ajusta automaticamente a posição da tela para mostrar todo o seu trabalho centralizado na tela.</li>
        <li><b>Fechamento rápido de nó:</b> Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio compatível mais próximo com uma extremidade livre.</li>
        <li><b>Nova língua - Alemão (🇩🇪):</b> Agora você pode selecionar alemão em Configurações → Alterar Idioma.</li>
        <li><b>Nova categoria Exemplos:</b> Explore projetos de exemplo prontos para carregar em Configurações → Exemplos. Escolha um exemplo para aprender; a caixa de diálogo fechará e o exemplo será carregado.</li>
    </ul>
    <hr>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;:</b> &#x05DE;&#x05D1;&#x05E0;&#x05D4; StateLayerManager &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05D8;&#x05D5;&#x05D1; &#x05D1;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D7;&#x05E1;&#x05D9;&#x05DD; &#x05D1;&#x05D9;&#x05BF; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DE;&#x05D9;&#x05D1;&#x05D9;&#x05D0; &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D0;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;.</li>
        <li><b>&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05D4; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;:</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DE;&#x05D5;&#x05EA; &#x05E2;&#x05DD; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05E2;&#x05DC; &#x05DB;&#x05EA;&#x05E8;&#x05D9;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;. &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D4;&#x05DE;&#x05D5;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7;&#x05EA; &#x05DE;&#x05D7;&#x05D6;&#x05D9;&#x05E7;&#x05D4; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05D9;&#x05D9;&#x05E8;&#x05D2;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05E9;&#x05DE;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D9;&#x05D7;&#x05D9;&#x05D3;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;:</b> &#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D4;&#x05E0;&#x05D9;&#x05D7;&#x05D9;&#x05D4; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; (🙉/🙈) &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D6;&#x05D9;&#x05D0;&#x05D4; &#x05D0;&#x05D7;&#x05D3;. &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05DB;&#x05E0;&#x05D9;&#x05E1; &#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;, &#x05D0;&#x05D6; &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;. &#x05E6;&#x05D0; &#x05DE;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05D7;&#x05D9;&#x05DC; &#x05D0;&#x05EA; &#x05D4;&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;:</b> &#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05D8; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05D4;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DC; &#x05D4;&#x05D8;&#x05E8;&#x05D2;&#x05D8; (🎯). &#x05D6;&#x05D4; &#x05DE;&#x05D9;&#x05D8;&#x05D9;&#x05D1; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D9;&#x05D3;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05E2;&#x05D1;&#x05D5;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05DEְ&#x05D5;&#x05E8;&#x05D9;&#x05D6; &#x05D1;&#x05D4;&#x05E4;&#x05E0;&#x05D4;.</li>
        <li><b>&#x05E1;&#x05D9;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05E9;&#x05DC; &#x05E7;&#x05E9;&#x05E8;:</b> &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D5; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D5;&#x05D5;&#x05D2;&#x05D3; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D4;&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05EA; &#x05D5;&#x05DE;&#x05D7;&#x05D1;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05DC;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05D0;&#x05D9;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05E4;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; - &#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; (🇩🇪):</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05E9;&#x05E0;&#x05D9;&#x05EA; &#x05E9;&#x05E4;&#x05D4;.</li>
        <li><b>&#x05E7;&#x05D8;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05E9;&#x05DC; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;:</b> &#x05D7;&#x05E7;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD; &#x05D4;&#x05E8;&#x05D9;&#x05D9;&#x05DD; &#x05DC;&#x05D8;&#x05D5;&#x05D7;&#x05D4; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;. &#x05D1;&#x05D7;&#x05E7;&#x05E8; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05DC;&#x05DC;&#x05DE;&#x05D9;&#x05D3; - &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05DC;&#x05D5;&#x05D2; &#x05D9;&#x05D9;&#x05E1;&#x05D5;&#x05D2; &#x05D5;&#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05D9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome German + localized sections). Updated to 1.101 what's-new.

cat > "$RESOURCES_DIR/fr.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbesserte Ebenenverwaltung:</b> Verbesserte StateLayerManager-Struktur für zuverlässigeres Handling von Knotenverbindungen und Strangbeziehungen, mit stabileren Operationen und besserer Performance.</li>
        <li><b>Gruppenduplikation:</b> Sie können jetzt ganze Gruppen mit allen ihren Strängen duplizieren, indem Sie mit der rechten Maustaste auf eine Gruppenüberschrift klicken und "Gruppe duplizieren" auswählen. Die duplizierte Gruppe behält alle Strangeigenschaften bei und generiert automatisch eindeutige Ebenennamen.</li>
        <li><b>Versteckmodus:</b> Neuer Versteckmodus, der über die Affen-Schaltfläche (🙉/🙈) zugänglich ist, ermöglicht es Ihnen, mehrere Ebenen schnell gleichzeitig auszublenden. Klicken Sie auf die Schaltfläche, um in den Versteckmodus zu wechseln, klicken Sie dann auf Ebenen, um sie auszublenden. Verlassen Sie den Versteckmodus, um die Änderungen zu übernehmen.</li>
        <li><b>Ansicht zentrieren:</b> Zentrieren Sie sofort alle Stränge in Ihrer Ansicht mit der neuen Ziel-Schaltfläche (🎯). Dies passt automatisch die Leinwandposition an, um alle Ihre Arbeit zentriert auf dem Bildschirm anzuzeigen.</li>
        <li><b>Schnelles Knotenschließen:</b> Klicken Sie mit der rechten Maustaste auf einen beliebigen Strang oder verbundenen Strang mit einem freien Ende, um den Knoten schnell zu schließen. Das System findet und verbindet automatisch mit dem nächstgelegenen kompatiblen Strang mit einem freien Ende.</li>
        <li><b>Neue Sprache – Deutsch (🇩🇪):</b> Sie können jetzt zu Deutsch in Einstellungen → Sprache ändern wechseln.</li>
        <li><b>Neue Kategorie „Beispiele" :</b> Entdecken Sie bereit-zu-ladende Beispielprojekte in Einstellungen → Beispiele. Wählen Sie ein Beispiel zum Lernen; der Dialog schließt sich und das Beispiel wird geladen.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>SVG Shape Support:</b> Added new SVG-based shapes (circle, square, triangle) for improved rendering quality and scalability. These shapes now load correctly in both the application and exported executables.</li>
        <li><b>Enhanced Canvas Guides:</b> New control point SVG guides for better visual feedback when manipulating canvas elements.</li>
        <li><b>Translation improvements</b> for canvas guide elements.</li>
        <li><b>Improved color consistency</b> for button explanation titles.</li>
    </ul>
    <p>Previous updates (1.101):</p>
    <ul>
        <li>Improved Layer Management, Group Duplication, Hide Mode, Center View, Quick Knot Closing</li>
        <li>New Language - German (🇩🇪)</li>
        <li>New Samples category</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Gestion améliorée des couches :</b> Structure StateLayerManager améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.</li>
        <li><b>Duplication de groupe :</b> Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant "Dupliquer le groupe". Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.</li>
        <li><b>Mode masquage :</b> Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permet de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches pour les masquer. Quittez le mode masquage pour appliquer les changements.</li>
        <li><b>Centrer la vue :</b> Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). Cela ajuste automatiquement la position du canevas pour afficher tout votre travail centré à l'écran.</li>
        <li><b>Fermeture rapide de nœud :</b> Cliquez avec le bouton droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et connecte automatiquement au brin compatible le plus proche avec une extrémité libre.</li>
        <li><b>Nouvelle langue - Allemand (🇩🇪) :</b> Vous pouvez maintenant sélectionner l'allemand dans Paramètres → Changer la langue.</li>
        <li><b>Nouvelle catégorie Exemples :</b> Découvrez des projets d'exemple prêts à charger dans Paramètres → Exemples. Choisissez un exemple pour apprendre ; la boîte de dialogue se fermera et l'exemple sera chargé.</li>
    </ul>
    <hr>    
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Gestione livelli migliorata:</b> Struttura StateLayerManager migliorata per una migliore gestione delle connessioni dei nodi e delle relazioni tra trefoli, offrendo operazioni sui livelli più affidabili e prestazioni migliorate.</li>
        <li><b>Duplicazione gruppo:</b> Ora puoi duplicare interi gruppi con tutti i loro trefoli facendo clic destro sull'intestazione di un gruppo e selezionando "Duplica gruppo". Il gruppo duplicato mantiene tutte le proprietà dei trefoli e genera automaticamente nomi di livelli unici.</li>
        <li><b>Modalità nascondi:</b> Nuova modalità nascondi accessibile tramite il pulsante scimmia (🙉/🙈) permette di nascondere rapidamente più livelli contemporaneamente. Clicca sul pulsante per entrare in modalità nascondi, poi clicca sui livelli per nasconderli. Esci dalla modalità nascondi per applicare le modifiche.</li>
        <li><b>Centra vista:</b> Centra istantaneamente tutti i trefoli nella tua vista con il nuovo pulsante bersaglio (🎯). Questo regola automaticamente la posizione del canvas per mostrare tutto il tuo lavoro centrato sullo schermo.</li>
        <li><b>Chiusura rapida del nodo:</b> Fai clic destro su qualsiasi trefolo o trefolo attaccato con un'estremità libera per chiudere rapidamente il nodo. Il sistema trova e connette automaticamente al trefolo compatibile più vicino con un'estremità libera.</li>
        <li><b>Nuova lingua - Tedesco (🇩🇪):</b> Ora puoi selezionare il tedesco in Impostazioni → Cambia Lingua.</li>
        <li><b>Nuova categoria Esempi:</b> Scopri progetti di esempio pronti al caricamento in Impostazioni → Esempi. Scegli un esempio da cui imparare; la finestra si chiuderà e l'esempio verrà caricato.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Gestión mejorada de capas:</b> Estructura StateLayerManager mejorada para un mejor manejo de las conexiones de nudos y relaciones entre hebras, ofreciendo operaciones de capas más confiables y mejor rendimiento.</li>
        <li><b>Duplicación de grupo:</b> Ahora puedes duplicar grupos completos con todas sus hebras haciendo clic derecho en el encabezado de un grupo y seleccionando "Duplicar grupo". El grupo duplicado mantiene todas las propiedades de las hebras y genera automáticamente nombres de capas únicos.</li>
        <li><b>Modo ocultar:</b> Nuevo modo ocultar accesible a través del botón mono (🙉/🙈) permite ocultar rápidamente múltiples capas a la vez. Haz clic en el botón para entrar en modo ocultar, luego haz clic en las capas para ocultarlas. Sal del modo ocultar para aplicar los cambios.</li>
        <li><b>Centrar vista:</b> Centra instantáneamente todas las hebras en tu vista con el nuevo botón diana (🎯). Esto ajusta automáticamente la posición del lienzo para mostrar todo tu trabajo centrado en la pantalla.</li>
        <li><b>Cierre rápido de nudo:</b> Haz clic derecho en cualquier hebra o hebra adjunta con un extremo libre para cerrar rápidamente el nudo. El sistema encuentra y conecta automáticamente a la hebra compatible más cercana con un extremo libre.</li>
        <li><b>Nuevo idioma - Alemán (🇩🇪):</b> Ahora puedes cambiar a alemán en Configuración → Cambiar Idioma.</li>
        <li><b>Nueva categoría Ejemplos:</b> Explora proyectos de ejemplo listos para cargar en Configuración → Ejemplos. Elige un ejemplo para aprender; el cuadro de diálogo se cerrará y el ejemplo se cargará.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Gestão melhorada de camadas:</b> Estrutura StateLayerManager melhorada para melhor gestão de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.</li>
        <li><b>Duplicação de grupo:</b> Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar Grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.</li>
        <li><b>Modo ocultar:</b> Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente múltiplas camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.</li>
        <li><b>Centralizar vista:</b> Centralize instantaneamente todos os fios na sua vista com o novo botão alvo (🎯). Isso ajusta automaticamente a posição da tela para mostrar todo o seu trabalho centralizado na tela.</li>
        <li><b>Fechamento rápido de nó:</b> Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio compatível mais próximo com uma extremidade livre.</li>
        <li><b>Nova língua - Alemão (🇩🇪):</b> Agora você pode selecionar alemão em Configurações → Alterar Idioma.</li>
        <li><b>Nova categoria Exemplos:</b> Explore projetos de exemplo prontos para carregar em Configurações → Exemplos. Escolha um exemplo para aprender; a caixa de diálogo fechará e o exemplo será carregado.</li>
    </ul>
    <hr>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;:</b> &#x05DE;&#x05D1;&#x05E0;&#x05D4; StateLayerManager &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05D8;&#x05D5;&#x05D1; &#x05D1;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D7;&#x05E1;&#x05D9;&#x05DD; &#x05D1;&#x05D9;&#x05BF; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DE;&#x05D9;&#x05D1;&#x05D9;&#x05D0; &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D0;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;.</li>
        <li><b>&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05D4; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;:</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DE;&#x05D5;&#x05EA; &#x05E2;&#x05DD; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05E2;&#x05DC; &#x05DB;&#x05EA;&#x05E8;&#x05D9;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;. &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D4;&#x05DE;&#x05D5;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7;&#x05EA; &#x05DE;&#x05D7;&#x05D6;&#x05D9;&#x05E7;&#x05D4; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05D9;&#x05D9;&#x05E8;&#x05D2;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05E9;&#x05DE;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D9;&#x05D7;&#x05D9;&#x05D3;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;:</b> &#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D4;&#x05E0;&#x05D9;&#x05D7;&#x05D9;&#x05D4; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; (🙉/🙈) &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D6;&#x05D9;&#x05D0;&#x05D4; &#x05D0;&#x05D7;&#x05D3;. &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05DB;&#x05E0;&#x05D9;&#x05E1; &#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;, &#x05D0;&#x05D6; &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;. &#x05E6;&#x05D0; &#x05DE;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05D7;&#x05D9;&#x05DC; &#x05D0;&#x05EA; &#x05D4;&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;:</b> &#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05D8; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05D4;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DC; &#x05D4;&#x05D8;&#x05E8;&#x05D2;&#x05D8; (🎯). &#x05D6;&#x05D4; &#x05DE;&#x05D9;&#x05D8;&#x05D9;&#x05D1; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D9;&#x05D3;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05E2;&#x05D1;&#x05D5;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05DEְ&#x05D5;&#x05E8;&#x05D9;&#x05D6; &#x05D1;&#x05D4;&#x05E4;&#x05E0;&#x05D4;.</li>
        <li><b>&#x05E1;&#x05D9;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05E9;&#x05DC; &#x05E7;&#x05E9;&#x05E8;:</b> &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D5; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D5;&#x05D5;&#x05D2;&#x05D3; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D4;&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05EA; &#x05D5;&#x05DE;&#x05D7;&#x05D1;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05DC;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05D0;&#x05D9;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05E4;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; - &#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; (🇩🇪):</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05E9;&#x05E0;&#x05D9;&#x05EA; &#x05E9;&#x05E4;&#x05D4;.</li>
        <li><b>&#x05E7;&#x05D8;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05E9;&#x05DC; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;:</b> &#x05D7;&#x05E7;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD; &#x05D4;&#x05E8;&#x05D9;&#x05D9;&#x05DD; &#x05DC;&#x05D8;&#x05D5;&#x05D7;&#x05D4; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;. &#x05D1;&#x05D7;&#x05E7;&#x05E8; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05DC;&#x05DC;&#x05DE;&#x05D9;&#x05D3; - &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05DC;&#x05D5;&#x05D2; &#x05D9;&#x05D9;&#x05E1;&#x05D5;&#x05D2; &#x05D5;&#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05D9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;.</li>
    </ul>
    </div>
</body>
</html>
EOF


# Create welcome.html  (welcome Italian + localized sections). Updated to 1.101 what's-new.
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
        <li><b>Gestione livelli migliorata:</b> Struttura StateLayerManager migliorata per una migliore gestione delle connessioni dei nodi e delle relazioni tra trefoli, offrendo operazioni sui livelli più affidabili e prestazioni migliorate.</li>
        <li><b>Duplicazione gruppo:</b> Ora puoi duplicare interi gruppi con tutti i loro trefoli facendo clic destro sull'intestazione di un gruppo e selezionando "Duplica gruppo". Il gruppo duplicato mantiene tutte le proprietà dei trefoli e genera automaticamente nomi di livelli unici.</li>
        <li><b>Modalità nascondi:</b> Nuova modalità nascondi accessibile tramite il pulsante scimmia (🙉/🙈) permette di nascondere rapidamente più livelli contemporaneamente. Clicca sul pulsante per entrare in modalità nascondi, poi clicca sui livelli per nasconderli. Esci dalla modalità nascondi per applicare le modifiche.</li>
        <li><b>Centra vista:</b> Centra istantaneamente tutti i trefoli nella tua vista con il nuovo pulsante bersaglio (🎯). Questo regola automaticamente la posizione del canvas per mostrare tutto il tuo lavoro centrato sullo schermo.</li>
        <li><b>Chiusura rapida del nodo:</b> Fai clic destro su qualsiasi trefolo o trefolo attaccato con un'estremità libera per chiudere rapidamente il nodo. Il sistema trova e connette automaticamente al trefolo compatibile più vicino con un'estremità libera.</li>
        <li><b>Nuova lingua - Tedesco (🇩🇪):</b> Ora puoi selezionare il tedesco in Impostazioni → Cambia Lingua.</li>
        <li><b>Nuova categoria Esempi:</b> Scopri progetti di esempio pronti al caricamento in Impostazioni → Esempi. Scegli un esempio da cui imparare; la finestra si chiuderà e l'esempio verrà caricato.</li>
    </ul>
    <hr>
        <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>SVG Shape Support:</b> Added new SVG-based shapes (circle, square, triangle) for improved rendering quality and scalability. These shapes now load correctly in both the application and exported executables.</li>
        <li><b>Enhanced Canvas Guides:</b> New control point SVG guides for better visual feedback when manipulating canvas elements.</li>
        <li><b>Translation improvements</b> for canvas guide elements.</li>
        <li><b>Improved color consistency</b> for button explanation titles.</li>
    </ul>
    <p>Previous updates (1.101):</p>
    <ul>
        <li>Improved Layer Management, Group Duplication, Hide Mode, Center View, Quick Knot Closing</li>
        <li>New Language - German (🇩🇪)</li>
        <li>New Samples category</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Gestion améliorée des couches :</b> Structure StateLayerManager améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.</li>
        <li><b>Duplication de groupe :</b> Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant "Dupliquer le groupe". Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.</li>
        <li><b>Mode masquage :</b> Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permet de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches pour les masquer. Quittez le mode masquage pour appliquer les changements.</li>
        <li><b>Centrer la vue :</b> Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). Cela ajuste automatiquement la position du canevas pour afficher tout votre travail centré à l'écran.</li>
        <li><b>Fermeture rapide de nœud :</b> Cliquez avec le bouton droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et connecte automatiquement au brin compatible le plus proche avec une extrémité libre.</li>
        <li><b>Nouvelle langue - Allemand (🇩🇪) :</b> Vous pouvez maintenant sélectionner l'allemand dans Paramètres → Changer la langue.</li>
        <li><b>Nouvelle catégorie Exemples :</b> Découvrez des projets d'exemple prêts à charger dans Paramètres → Exemples. Choisissez un exemple pour apprendre ; la boîte de dialogue se fermera et l'exemple sera chargé.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbesserte Ebenenverwaltung:</b> Verbesserte StateLayerManager-Struktur für zuverlässigeres Handling von Knotenverbindungen und Strangbeziehungen, mit stabileren Operationen und besserer Performance.</li>
        <li><b>Gruppenduplikation:</b> Sie können jetzt ganze Gruppen mit allen ihren Strängen duplizieren, indem Sie mit der rechten Maustaste auf eine Gruppenüberschrift klicken und "Gruppe duplizieren" auswählen. Die duplizierte Gruppe behält alle Strangeigenschaften bei und generiert automatisch eindeutige Ebenennamen.</li>
        <li><b>Versteckmodus:</b> Neuer Versteckmodus, der über die Affen-Schaltfläche (🙉/🙈) zugänglich ist, ermöglicht es Ihnen, mehrere Ebenen schnell gleichzeitig auszublenden. Klicken Sie auf die Schaltfläche, um in den Versteckmodus zu wechseln, klicken Sie dann auf Ebenen, um sie auszublenden. Verlassen Sie den Versteckmodus, um die Änderungen zu übernehmen.</li>
        <li><b>Ansicht zentrieren:</b> Zentrieren Sie sofort alle Stränge in Ihrer Ansicht mit der neuen Ziel-Schaltfläche (🎯). Dies passt automatisch die Leinwandposition an, um alle Ihre Arbeit zentriert auf dem Bildschirm anzuzeigen.</li>
        <li><b>Schnelles Knotenschließen:</b> Klicken Sie mit der rechten Maustaste auf einen beliebigen Strang oder verbundenen Strang mit einem freien Ende, um den Knoten schnell zu schließen. Das System findet und verbindet automatisch mit dem nächstgelegenen kompatiblen Strang mit einem freien Ende.</li>
        <li><b>Neue Sprache – Deutsch (🇩🇪):</b> Sie können jetzt zu Deutsch in Einstellungen → Sprache ändern wechseln.</li>
        <li><b>Neue Kategorie „Beispiele" :</b> Entdecken Sie bereit-zu-ladende Beispielprojekte in Einstellungen → Beispiele. Wählen Sie ein Beispiel zum Lernen; der Dialog schließt sich und das Beispiel wird geladen.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Gestión mejorada de capas:</b> Estructura StateLayerManager mejorada para un mejor manejo de las conexiones de nudos y relaciones entre hebras, ofreciendo operaciones de capas más confiables y mejor rendimiento.</li>
        <li><b>Duplicación de grupo:</b> Ahora puedes duplicar grupos completos con todas sus hebras haciendo clic derecho en el encabezado de un grupo y seleccionando "Duplicar grupo". El grupo duplicado mantiene todas las propiedades de las hebras y genera automáticamente nombres de capas únicos.</li>
        <li><b>Modo ocultar:</b> Nuevo modo ocultar accesible a través del botón mono (🙉/🙈) permite ocultar rápidamente múltiples capas a la vez. Haz clic en el botón para entrar en modo ocultar, luego haz clic en las capas para ocultarlas. Sal del modo ocultar para aplicar los cambios.</li>
        <li><b>Centrar vista:</b> Centra instantáneamente todas las hebras en tu vista con el nuevo botón diana (🎯). Esto ajusta automáticamente la posición del lienzo para mostrar todo tu trabajo centrado en la pantalla.</li>
        <li><b>Cierre rápido de nudo:</b> Haz clic derecho en cualquier hebra o hebra adjunta con un extremo libre para cerrar rápidamente el nudo. El sistema encuentra y conecta automáticamente a la hebra compatible más cercana con un extremo libre.</li>
        <li><b>Nuevo idioma - Alemán (🇩🇪):</b> Ahora puedes cambiar a alemán en Configuración → Cambiar Idioma.</li>
        <li><b>Nueva categoría Ejemplos:</b> Explora proyectos de ejemplo listos para cargar en Configuración → Ejemplos. Elige un ejemplo para aprender; el cuadro de diálogo se cerrará y el ejemplo se cargará.</li>
    </ul>
    <hr>
        <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Gestão melhorada de camadas:</b> Estrutura StateLayerManager melhorada para melhor gestão de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.</li>
        <li><b>Duplicação de grupo:</b> Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar Grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.</li>
        <li><b>Modo ocultar:</b> Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente múltiplas camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.</li>
        <li><b>Centralizar vista:</b> Centralize instantaneamente todos os fios na sua vista com o novo botão alvo (🎯). Isso ajusta automaticamente a posição da tela para mostrar todo o seu trabalho centralizado na tela.</li>
        <li><b>Fechamento rápido de nó:</b> Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio compatível mais próximo com uma extremidade livre.</li>
        <li><b>Nova língua - Alemão (🇩🇪):</b> Agora você pode selecionar alemão em Configurações → Alterar Idioma.</li>
        <li><b>Nova categoria Exemplos:</b> Explore projetos de exemplo prontos para carregar em Configurações → Exemplos. Escolha um exemplo para aprender; a caixa de diálogo fechará e o exemplo será carregado.</li>
    </ul>
    <hr>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;:</b> &#x05DE;&#x05D1;&#x05E0;&#x05D4; StateLayerManager &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05D8;&#x05D5;&#x05D1; &#x05D1;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D7;&#x05E1;&#x05D9;&#x05DD; &#x05D1;&#x05D9;&#x05BF; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DE;&#x05D9;&#x05D1;&#x05D9;&#x05D0; &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D0;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;.</li>
        <li><b>&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05D4; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;:</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DE;&#x05D5;&#x05EA; &#x05E2;&#x05DD; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05E2;&#x05DC; &#x05DB;&#x05EA;&#x05E8;&#x05D9;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;. &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D4;&#x05DE;&#x05D5;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7;&#x05EA; &#x05DE;&#x05D7;&#x05D6;&#x05D9;&#x05E7;&#x05D4; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05D9;&#x05D9;&#x05E8;&#x05D2;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05E9;&#x05DE;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D9;&#x05D7;&#x05D9;&#x05D3;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;:</b> &#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D4;&#x05E0;&#x05D9;&#x05D7;&#x05D9;&#x05D4; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; (🙉/🙈) &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D6;&#x05D9;&#x05D0;&#x05D4; &#x05D0;&#x05D7;&#x05D3;. &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05DB;&#x05E0;&#x05D9;&#x05E1; &#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;, &#x05D0;&#x05D6; &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;. &#x05E6;&#x05D0; &#x05DE;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05D7;&#x05D9;&#x05DC; &#x05D0;&#x05EA; &#x05D4;&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;:</b> &#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05D8; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05D4;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DC; &#x05D4;&#x05D8;&#x05E8;&#x05D2;&#x05D8; (🎯). &#x05D6;&#x05D4; &#x05DE;&#x05D9;&#x05D8;&#x05D9;&#x05D1; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D9;&#x05D3;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05E2;&#x05D1;&#x05D5;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05DEְ&#x05D5;&#x05E8;&#x05D9;&#x05D6; &#x05D1;&#x05D4;&#x05E4;&#x05E0;&#x05D4;.</li>
        <li><b>&#x05E1;&#x05D9;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05E9;&#x05DC; &#x05E7;&#x05E9;&#x05E8;:</b> &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D5; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D5;&#x05D5;&#x05D2;&#x05D3; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D4;&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05EA; &#x05D5;&#x05DE;&#x05D7;&#x05D1;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05DC;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05D0;&#x05D9;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05E4;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; - &#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; (🇩🇪):</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05E9;&#x05E0;&#x05D9;&#x05EA; &#x05E9;&#x05E4;&#x05D4;.</li>
        <li><b>&#x05E7;&#x05D8;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05E9;&#x05DC; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;:</b> &#x05D7;&#x05E7;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD; &#x05D4;&#x05E8;&#x05D9;&#x05D9;&#x05DD; &#x05DC;&#x05D8;&#x05D5;&#x05D7;&#x05D4; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;. &#x05D1;&#x05D7;&#x05E7;&#x05E8; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05DC;&#x05DC;&#x05DE;&#x05D9;&#x05D3; - &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05DC;&#x05D5;&#x05D2; &#x05D9;&#x05D9;&#x05E1;&#x05D5;&#x05D2; &#x05D5;&#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05D9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;.</li>
    </ul>
    </div>
</body>
</html>
EOF
# Create welcome.html  (welcome Spanish + localized sections). Updated to 1.101 what's-new.
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
        <li><b>Gestión mejorada de capas:</b> Estructura StateLayerManager mejorada para un mejor manejo de las conexiones de nudos y relaciones entre hebras, ofreciendo operaciones de capas más confiables y mejor rendimiento.</li>
        <li><b>Duplicación de grupo:</b> Ahora puedes duplicar grupos completos con todas sus hebras haciendo clic derecho en el encabezado de un grupo y seleccionando "Duplicar grupo". El grupo duplicado mantiene todas las propiedades de las hebras y genera automáticamente nombres de capas únicos.</li>
        <li><b>Modo ocultar:</b> Nuevo modo ocultar accesible a través del botón mono (🙉/🙈) permite ocultar rápidamente múltiples capas a la vez. Haz clic en el botón para entrar en modo ocultar, luego haz clic en las capas para ocultarlas. Sal del modo ocultar para aplicar los cambios.</li>
        <li><b>Centrar vista:</b> Centra instantáneamente todas las hebras en tu vista con el nuevo botón diana (🎯). Esto ajusta automáticamente la posición del lienzo para mostrar todo tu trabajo centrado en la pantalla.</li>
        <li><b>Cierre rápido de nudo:</b> Haz clic derecho en cualquier hebra o hebra adjunta con un extremo libre para cerrar rápidamente el nudo. El sistema encuentra y conecta automáticamente a la hebra compatible más cercana con un extremo libre.</li>
        <li><b>Nuevo idioma - Alemán (🇩🇪):</b> Ahora puedes cambiar a alemán en Configuración → Cambiar Idioma.</li>
        <li><b>Nueva categoría Ejemplos:</b> Explora proyectos de ejemplo listos para cargar en Configuración → Ejemplos. Elige un ejemplo para aprender; el cuadro de diálogo se cerrará y el ejemplo se cargará.</li>
    </ul>
    <hr>
        <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>SVG Shape Support:</b> Added new SVG-based shapes (circle, square, triangle) for improved rendering quality and scalability. These shapes now load correctly in both the application and exported executables.</li>
        <li><b>Enhanced Canvas Guides:</b> New control point SVG guides for better visual feedback when manipulating canvas elements.</li>
        <li><b>Translation improvements</b> for canvas guide elements.</li>
        <li><b>Improved color consistency</b> for button explanation titles.</li>
    </ul>
    <p>Previous updates (1.101):</p>
    <ul>
        <li>Improved Layer Management, Group Duplication, Hide Mode, Center View, Quick Knot Closing</li>
        <li>New Language - German (🇩🇪)</li>
        <li>New Samples category</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Gestion améliorée des couches :</b> Structure StateLayerManager améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.</li>
        <li><b>Duplication de groupe :</b> Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant "Dupliquer le groupe". Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.</li>
        <li><b>Mode masquage :</b> Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permet de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches pour les masquer. Quittez le mode masquage pour appliquer les changements.</li>
        <li><b>Centrer la vue :</b> Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). Cela ajuste automatiquement la position du canevas pour afficher tout votre travail centré à l'écran.</li>
        <li><b>Fermeture rapide de nœud :</b> Cliquez avec le bouton droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et connecte automatiquement au brin compatible le plus proche avec une extrémité libre.</li>
        <li><b>Nouvelle langue - Allemand (🇩🇪) :</b> Vous pouvez maintenant sélectionner l'allemand dans Paramètres → Changer la langue.</li>
        <li><b>Nouvelle catégorie Exemples :</b> Découvrez des projets d'exemple prêts à charger dans Paramètres → Exemples. Choisissez un exemple pour apprendre ; la boîte de dialogue se fermera et l'exemple sera chargé.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbesserte Ebenenverwaltung:</b> Verbesserte StateLayerManager-Struktur für zuverlässigeres Handling von Knotenverbindungen und Strangbeziehungen, mit stabileren Operationen und besserer Performance.</li>
        <li><b>Gruppenduplikation:</b> Sie können jetzt ganze Gruppen mit allen ihren Strängen duplizieren, indem Sie mit der rechten Maustaste auf eine Gruppenüberschrift klicken und "Gruppe duplizieren" auswählen. Die duplizierte Gruppe behält alle Strangeigenschaften bei und generiert automatisch eindeutige Ebenennamen.</li>
        <li><b>Versteckmodus:</b> Neuer Versteckmodus, der über die Affen-Schaltfläche (🙉/🙈) zugänglich ist, ermöglicht es Ihnen, mehrere Ebenen schnell gleichzeitig auszublenden. Klicken Sie auf die Schaltfläche, um in den Versteckmodus zu wechseln, klicken Sie dann auf Ebenen, um sie auszublenden. Verlassen Sie den Versteckmodus, um die Änderungen zu übernehmen.</li>
        <li><b>Ansicht zentrieren:</b> Zentrieren Sie sofort alle Stränge in Ihrer Ansicht mit der neuen Ziel-Schaltfläche (🎯). Dies passt automatisch die Leinwandposition an, um alle Ihre Arbeit zentriert auf dem Bildschirm anzuzeigen.</li>
        <li><b>Schnelles Knotenschließen:</b> Klicken Sie mit der rechten Maustaste auf einen beliebigen Strang oder verbundenen Strang mit einem freien Ende, um den Knoten schnell zu schließen. Das System findet und verbindet automatisch mit dem nächstgelegenen kompatiblen Strang mit einem freien Ende.</li>
        <li><b>Neue Sprache – Deutsch (🇩🇪):</b> Sie können jetzt zu Deutsch in Einstellungen → Sprache ändern wechseln.</li>
        <li><b>Neue Kategorie „Beispiele" :</b> Entdecken Sie bereit-zu-ladende Beispielprojekte in Einstellungen → Beispiele. Wählen Sie ein Beispiel zum Lernen; der Dialog schließt sich und das Beispiel wird geladen.</li>
    </ul>
    <hr>    
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Gestione livelli migliorata:</b> Struttura StateLayerManager migliorata per una migliore gestione delle connessioni dei nodi e delle relazioni tra trefoli, offrendo operazioni sui livelli più affidabili e prestazioni migliorate.</li>
        <li><b>Duplicazione gruppo:</b> Ora puoi duplicare interi gruppi con tutti i loro trefoli facendo clic destro sull'intestazione di un gruppo e selezionando "Duplica gruppo". Il gruppo duplicato mantiene tutte le proprietà dei trefoli e genera automaticamente nomi di livelli unici.</li>
        <li><b>Modalità nascondi:</b> Nuova modalità nascondi accessibile tramite il pulsante scimmia (🙉/🙈) permette di nascondere rapidamente più livelli contemporaneamente. Clicca sul pulsante per entrare in modalità nascondi, poi clicca sui livelli per nasconderli. Esci dalla modalità nascondi per applicare le modifiche.</li>
        <li><b>Centra vista:</b> Centra istantaneamente tutti i trefoli nella tua vista con il nuovo pulsante bersaglio (🎯). Questo regola automaticamente la posizione del canvas per mostrare tutto il tuo lavoro centrato sullo schermo.</li>
        <li><b>Chiusura rapida del nodo:</b> Fai clic destro su qualsiasi trefolo o trefolo attaccato con un'estremità libera per chiudere rapidamente il nodo. Il sistema trova e connette automaticamente al trefolo compatibile più vicino con un'estremità libera.</li>
        <li><b>Nuova lingua - Tedesco (🇩🇪):</b> Ora puoi selezionare il tedesco in Impostazioni → Cambia Lingua.</li>
        <li><b>Nuova categoria Esempi:</b> Scopri progetti di esempio pronti al caricamento in Impostazioni → Esempi. Scegli un esempio da cui imparare; la finestra si chiuderà e l'esempio verrà caricato.</li>
    </ul>
    <hr>
        <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Gestão melhorada de camadas:</b> Estrutura StateLayerManager melhorada para melhor gestão de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.</li>
        <li><b>Duplicação de grupo:</b> Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar Grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.</li>
        <li><b>Modo ocultar:</b> Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente múltiplas camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.</li>
        <li><b>Centralizar vista:</b> Centralize instantaneamente todos os fios na sua vista com o novo botão alvo (🎯). Isso ajusta automaticamente a posição da tela para mostrar todo o seu trabalho centralizado na tela.</li>
        <li><b>Fechamento rápido de nó:</b> Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio compatível mais próximo com uma extremidade livre.</li>
        <li><b>Nova língua - Alemão (🇩🇪):</b> Agora você pode selecionar alemão em Configurações → Alterar Idioma.</li>
        <li><b>Nova categoria Exemplos:</b> Explore projetos de exemplo prontos para carregar em Configurações → Exemplos. Escolha um exemplo para aprender; a caixa de diálogo fechará e o exemplo será carregado.</li>
    </ul>
    <hr>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;:</b> &#x05DE;&#x05D1;&#x05E0;&#x05D4; StateLayerManager &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05D8;&#x05D5;&#x05D1; &#x05D1;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D7;&#x05E1;&#x05D9;&#x05DD; &#x05D1;&#x05D9;&#x05BF; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DE;&#x05D9;&#x05D1;&#x05D9;&#x05D0; &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D0;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;.</li>
        <li><b>&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05D4; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;:</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DE;&#x05D5;&#x05EA; &#x05E2;&#x05DD; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05E2;&#x05DC; &#x05DB;&#x05EA;&#x05E8;&#x05D9;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;. &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D4;&#x05DE;&#x05D5;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7;&#x05EA; &#x05DE;&#x05D7;&#x05D6;&#x05D9;&#x05E7;&#x05D4; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05D9;&#x05D9;&#x05E8;&#x05D2;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05E9;&#x05DE;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D9;&#x05D7;&#x05D9;&#x05D3;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;:</b> &#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D4;&#x05E0;&#x05D9;&#x05D7;&#x05D9;&#x05D4; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; (🙉/🙈) &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D6;&#x05D9;&#x05D0;&#x05D4; &#x05D0;&#x05D7;&#x05D3;. &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05DB;&#x05E0;&#x05D9;&#x05E1; &#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;, &#x05D0;&#x05D6; &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;. &#x05E6;&#x05D0; &#x05DE;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05D7;&#x05D9;&#x05DC; &#x05D0;&#x05EA; &#x05D4;&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;:</b> &#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05D8; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05D4;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DC; &#x05D4;&#x05D8;&#x05E8;&#x05D2;&#x05D8; (🎯). &#x05D6;&#x05D4; &#x05DE;&#x05D9;&#x05D8;&#x05D9;&#x05D1; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D9;&#x05D3;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05E2;&#x05D1;&#x05D5;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05DEְ&#x05D5;&#x05E8;&#x05D9;&#x05D6; &#x05D1;&#x05D4;&#x05E4;&#x05E0;&#x05D4;.</li>
        <li><b>&#x05E1;&#x05D9;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05E9;&#x05DC; &#x05E7;&#x05E9;&#x05E8;:</b> &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D5; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D5;&#x05D5;&#x05D2;&#x05D3; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D4;&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05EA; &#x05D5;&#x05DE;&#x05D7;&#x05D1;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05DC;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05D0;&#x05D9;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05E4;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; - &#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; (🇩🇪):</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05E9;&#x05E0;&#x05D9;&#x05EA; &#x05E9;&#x05E4;&#x05D4;.</li>
        <li><b>&#x05E7;&#x05D8;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05E9;&#x05DC; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;:</b> &#x05D7;&#x05E7;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD; &#x05D4;&#x05E8;&#x05D9;&#x05D9;&#x05DD; &#x05DC;&#x05D8;&#x05D5;&#x05D7;&#x05D4; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;. &#x05D1;&#x05D7;&#x05E7;&#x05E8; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05DC;&#x05DC;&#x05DE;&#x05D9;&#x05D3; - &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05DC;&#x05D5;&#x05D2; &#x05D9;&#x05D9;&#x05E1;&#x05D5;&#x05D2; &#x05D5;&#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05D9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;.</li>
    </ul>
    </div>
</body>
</html>
EOF
# Create welcome.html  (welcome Portuguese + localized sections). Updated to 1.101 what's-new.

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
        <li><b>Gestão melhorada de camadas:</b> Estrutura StateLayerManager melhorada para melhor gestão de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.</li>
        <li><b>Duplicação de grupo:</b> Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar Grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.</li>
        <li><b>Modo ocultar:</b> Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente múltiplas camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.</li>
        <li><b>Centralizar vista:</b> Centralize instantaneamente todos os fios na sua vista com o novo botão alvo (🎯). Isso ajusta automaticamente a posição da tela para mostrar todo o seu trabalho centralizado na tela.</li>
        <li><b>Fechamento rápido de nó:</b> Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio compatível mais próximo com uma extremidade livre.</li>
        <li><b>Nova língua - Alemão (🇩🇪):</b> Agora você pode selecionar alemão em Configurações → Alterar Idioma.</li>
        <li><b>Nova categoria Exemplos:</b> Explore projetos de exemplo prontos para carregar em Configurações → Exemplos. Escolha um exemplo para aprender; a caixa de diálogo fechará e o exemplo será carregado.</li>
    </ul>
    <hr>
        <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>SVG Shape Support:</b> Added new SVG-based shapes (circle, square, triangle) for improved rendering quality and scalability. These shapes now load correctly in both the application and exported executables.</li>
        <li><b>Enhanced Canvas Guides:</b> New control point SVG guides for better visual feedback when manipulating canvas elements.</li>
        <li><b>Translation improvements</b> for canvas guide elements.</li>
        <li><b>Improved color consistency</b> for button explanation titles.</li>
    </ul>
    <p>Previous updates (1.101):</p>
    <ul>
        <li>Improved Layer Management, Group Duplication, Hide Mode, Center View, Quick Knot Closing</li>
        <li>New Language - German (🇩🇪)</li>
        <li>New Samples category</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Gestion améliorée des couches :</b> Structure StateLayerManager améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.</li>
        <li><b>Duplication de groupe :</b> Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant "Dupliquer le groupe". Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.</li>
        <li><b>Mode masquage :</b> Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permet de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches pour les masquer. Quittez le mode masquage pour appliquer les changements.</li>
        <li><b>Centrer la vue :</b> Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). Cela ajuste automatiquement la position du canevas pour afficher tout votre travail centré à l'écran.</li>
        <li><b>Fermeture rapide de nœud :</b> Cliquez avec le bouton droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et connecte automatiquement au brin compatible le plus proche avec une extrémité libre.</li>
        <li><b>Nouvelle langue - Allemand (🇩🇪) :</b> Vous pouvez maintenant sélectionner l'allemand dans Paramètres → Changer la langue.</li>
        <li><b>Nouvelle catégorie Exemples :</b> Découvrez des projets d'exemple prêts à charger dans Paramètres → Exemples. Choisissez un exemple pour apprendre ; la boîte de dialogue se fermera et l'exemple sera chargé.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbesserte Ebenenverwaltung:</b> Verbesserte StateLayerManager-Struktur für zuverlässigeres Handling von Knotenverbindungen und Strangbeziehungen, mit stabileren Operationen und besserer Performance.</li>
        <li><b>Gruppenduplikation:</b> Sie können jetzt ganze Gruppen mit allen ihren Strängen duplizieren, indem Sie mit der rechten Maustaste auf eine Gruppenüberschrift klicken und "Gruppe duplizieren" auswählen. Die duplizierte Gruppe behält alle Strangeigenschaften bei und generiert automatisch eindeutige Ebenennamen.</li>
        <li><b>Versteckmodus:</b> Neuer Versteckmodus, der über die Affen-Schaltfläche (🙉/🙈) zugänglich ist, ermöglicht es Ihnen, mehrere Ebenen schnell gleichzeitig auszublenden. Klicken Sie auf die Schaltfläche, um in den Versteckmodus zu wechseln, klicken Sie dann auf Ebenen, um sie auszublenden. Verlassen Sie den Versteckmodus, um die Änderungen zu übernehmen.</li>
        <li><b>Ansicht zentrieren:</b> Zentrieren Sie sofort alle Stränge in Ihrer Ansicht mit der neuen Ziel-Schaltfläche (🎯). Dies passt automatisch die Leinwandposition an, um alle Ihre Arbeit zentriert auf dem Bildschirm anzuzeigen.</li>
        <li><b>Schnelles Knotenschließen:</b> Klicken Sie mit der rechten Maustaste auf einen beliebigen Strang oder verbundenen Strang mit einem freien Ende, um den Knoten schnell zu schließen. Das System findet und verbindet automatisch mit dem nächstgelegenen kompatiblen Strang mit einem freien Ende.</li>
        <li><b>Neue Sprache – Deutsch (🇩🇪):</b> Sie können jetzt zu Deutsch in Einstellungen → Sprache ändern wechseln.</li>
        <li><b>Neue Kategorie „Beispiele" :</b> Entdecken Sie bereit-zu-ladende Beispielprojekte in Einstellungen → Beispiele. Wählen Sie ein Beispiel zum Lernen; der Dialog schließt sich und das Beispiel wird geladen.</li>
    </ul>
    <hr>    
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Gestione livelli migliorata:</b> Struttura StateLayerManager migliorata per una migliore gestione delle connessioni dei nodi e delle relazioni tra trefoli, offrendo operazioni sui livelli più affidabili e prestazioni migliorate.</li>
        <li><b>Duplicazione gruppo:</b> Ora puoi duplicare interi gruppi con tutti i loro trefoli facendo clic destro sull'intestazione di un gruppo e selezionando "Duplica gruppo". Il gruppo duplicato mantiene tutte le proprietà dei trefoli e genera automaticamente nomi di livelli unici.</li>
        <li><b>Modalità nascondi:</b> Nuova modalità nascondi accessibile tramite il pulsante scimmia (🙉/🙈) permette di nascondere rapidamente più livelli contemporaneamente. Clicca sul pulsante per entrare in modalità nascondi, poi clicca sui livelli per nasconderli. Esci dalla modalità nascondi per applicare le modifiche.</li>
        <li><b>Centra vista:</b> Centra istantaneamente tutti i trefoli nella tua vista con il nuovo pulsante bersaglio (🎯). Questo regola automaticamente la posizione del canvas per mostrare tutto il tuo lavoro centrato sullo schermo.</li>
        <li><b>Chiusura rapida del nodo:</b> Fai clic destro su qualsiasi trefolo o trefolo attaccato con un'estremità libera per chiudere rapidamente il nodo. Il sistema trova e connette automaticamente al trefolo compatibile più vicino con un'estremità libera.</li>
        <li><b>Nuova lingua - Tedesco (🇩🇪):</b> Ora puoi selezionare il tedesco in Impostazioni → Cambia Lingua.</li>
        <li><b>Nuova categoria Esempi:</b> Scopri progetti di esempio pronti al caricamento in Impostazioni → Esempi. Scegli un esempio da cui imparare; la finestra si chiuderà e l'esempio verrà caricato.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Gestión mejorada de capas:</b> Estructura StateLayerManager mejorada para un mejor manejo de las conexiones de nudos y relaciones entre hebras, ofreciendo operaciones de capas más confiables y mejor rendimiento.</li>
        <li><b>Duplicación de grupo:</b> Ahora puedes duplicar grupos completos con todas sus hebras haciendo clic derecho en el encabezado de un grupo y seleccionando "Duplicar grupo". El grupo duplicado mantiene todas las propiedades de las hebras y genera automáticamente nombres de capas únicos.</li>
        <li><b>Modo ocultar:</b> Nuevo modo ocultar accesible a través del botón mono (🙉/🙈) permite ocultar rápidamente múltiples capas a la vez. Haz clic en el botón para entrar en modo ocultar, luego haz clic en las capas para ocultarlas. Sal del modo ocultar para aplicar los cambios.</li>
        <li><b>Centrar vista:</b> Centra instantáneamente todas las hebras en tu vista con el nuevo botón diana (🎯). Esto ajusta automáticamente la posición del lienzo para mostrar todo tu trabajo centrado en la pantalla.</li>
        <li><b>Cierre rápido de nudo:</b> Haz clic derecho en cualquier hebra o hebra adjunta con un extremo libre para cerrar rápidamente el nudo. El sistema encuentra y conecta automáticamente a la hebra compatible más cercana con un extremo libre.</li>
        <li><b>Nuevo idioma - Alemán (🇩🇪):</b> Ahora puedes cambiar a alemán en Configuración → Cambiar Idioma.</li>
        <li><b>Nueva categoría Ejemplos:</b> Explora proyectos de ejemplo listos para cargar en Configuración → Ejemplos. Elige un ejemplo para aprender; el cuadro de diálogo se cerrará y el ejemplo se cargará.</li>
    </ul>
    <hr>
        <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Gestão melhorada de camadas:</b> Estrutura StateLayerManager melhorada para melhor gestão de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.</li>
        <li><b>Duplicação de grupo:</b> Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar Grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.</li>
        <li><b>Modo ocultar:</b> Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente múltiplas camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.</li>
        <li><b>Centralizar vista:</b> Centralize instantaneamente todos os fios na sua vista com o novo botão alvo (🎯). Isso ajusta automaticamente a posição da tela para mostrar todo o seu trabalho centralizado na tela.</li>
        <li><b>Fechamento rápido de nó:</b> Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio compatível mais próximo com uma extremidade livre.</li>
        <li><b>Nova língua - Alemão (🇩🇪):</b> Agora você pode selecionar alemão em Configurações → Alterar Idioma.</li>
        <li><b>Nova categoria Exemplos:</b> Explore projetos de exemplo prontos para carregar em Configurações → Exemplos. Escolha um exemplo para aprender; a caixa de diálogo fechará e o exemplo será carregado.</li>
    </ul>
    <hr>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.101</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;:</b> &#x05DE;&#x05D1;&#x05E0;&#x05D4; StateLayerManager &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05D8;&#x05D5;&#x05D1; &#x05D1;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D7;&#x05E1;&#x05D9;&#x05DD; &#x05D1;&#x05D9;&#x05BF; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DE;&#x05D9;&#x05D1;&#x05D9;&#x05D0; &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D0;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;.</li>
        <li><b>&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05D4; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;:</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DE;&#x05D5;&#x05EA; &#x05E2;&#x05DD; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05E2;&#x05DC; &#x05DB;&#x05EA;&#x05E8;&#x05D9;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;. &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D4;&#x05DE;&#x05D5;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7;&#x05EA; &#x05DE;&#x05D7;&#x05D6;&#x05D9;&#x05E7;&#x05D4; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05D9;&#x05D9;&#x05E8;&#x05D2;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05E9;&#x05DE;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D9;&#x05D7;&#x05D9;&#x05D3;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;:</b> &#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D4;&#x05E0;&#x05D9;&#x05D7;&#x05D9;&#x05D4; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; (🙉/🙈) &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D6;&#x05D9;&#x05D0;&#x05D4; &#x05D0;&#x05D7;&#x05D3;. &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05DB;&#x05E0;&#x05D9;&#x05E1; &#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;, &#x05D0;&#x05D6; &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;. &#x05E6;&#x05D0; &#x05DE;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05D7;&#x05D9;&#x05DC; &#x05D0;&#x05EA; &#x05D4;&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;:</b> &#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05D8; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05D4;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DC; &#x05D4;&#x05D8;&#x05E8;&#x05D2;&#x05D8; (🎯). &#x05D6;&#x05D4; &#x05DE;&#x05D9;&#x05D8;&#x05D9;&#x05D1; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D9;&#x05D3;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05E2;&#x05D1;&#x05D5;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05DEְ&#x05D5;&#x05E8;&#x05D9;&#x05D6; &#x05D1;&#x05D4;&#x05E4;&#x05E0;&#x05D4;.</li>
        <li><b>&#x05E1;&#x05D9;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05E9;&#x05DC; &#x05E7;&#x05E9;&#x05E8;:</b> &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D5; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D5;&#x05D5;&#x05D2;&#x05D3; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D4;&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05EA; &#x05D5;&#x05DE;&#x05D7;&#x05D1;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05DC;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05D0;&#x05D9;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05E4;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; - &#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; (🇩🇪):</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05E9;&#x05E0;&#x05D9;&#x05EA; &#x05E9;&#x05E4;&#x05D4;.</li>
        <li><b>&#x05E7;&#x05D8;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05E9;&#x05DC; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;:</b> &#x05D7;&#x05E7;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD; &#x05D4;&#x05E8;&#x05D9;&#x05D9;&#x05DD; &#x05DC;&#x05D8;&#x05D5;&#x05D7;&#x05D4; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;. &#x05D1;&#x05D7;&#x05E7;&#x05E8; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05DC;&#x05DC;&#x05DE;&#x05D9;&#x05D3; - &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05DC;&#x05D5;&#x05D2; &#x05D9;&#x05D9;&#x05E1;&#x05D5;&#x05D2; &#x05D5;&#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05D9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome Hebrew + localized sections). Updated to 1.101 what's-new.
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
        <li><b>&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;:</b> &#x05DE;&#x05D1;&#x05E0;&#x05D4; StateLayerManager &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3; &#x05DC;&#x05E0;&#x05D9;&#x05D4;&#x05D5;&#x05DC; &#x05D8;&#x05D5;&#x05D1; &#x05D1;&#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8; &#x05D7;&#x05D9;&#x05D1;&#x05D5;&#x05E8;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D7;&#x05E1;&#x05D9;&#x05DD; &#x05D1;&#x05D9;&#x05BF; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;, &#x05DE;&#x05D9;&#x05D1;&#x05D9;&#x05D0; &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D9;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D0;&#x05DE;&#x05D9;&#x05E0;&#x05D9;&#x05DD; &#x05D5;&#x05D9;&#x05D3;&#x05D9;&#x05E0;&#x05D4; &#x05DE;&#x05D9;&#x05D5;&#x05D7;&#x05D3;.</li>
        <li><b>&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05D4; &#x05E9;&#x05DC; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;:</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA; &#x05E9;&#x05DC;&#x05DE;&#x05D5;&#x05EA; &#x05E2;&#x05DD; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05E9;&#x05DC;&#x05D4;&#x05DD; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05E2;&#x05DC; &#x05DB;&#x05EA;&#x05E8;&#x05D9;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D5;&#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05D4; &#x05D1;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05D9;&#x05E7;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4;. &#x05D4;&#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D4; &#x05D4;&#x05DE;&#x05D5;&#x05D3;&#x05D5;&#x05E4;&#x05DC;&#x05E7;&#x05EA; &#x05DE;&#x05D7;&#x05D6;&#x05D9;&#x05E7;&#x05D4; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05EA;&#x05D5;&#x05DB;&#x05E0;&#x05D5;&#x05EA; &#x05E9;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D5;&#x05DE;&#x05D9;&#x05D9;&#x05E8;&#x05D2;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05E9;&#x05DE;&#x05D5;&#x05EA; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D9;&#x05D7;&#x05D9;&#x05D3;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;:</b> &#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D4;&#x05E0;&#x05D9;&#x05D7;&#x05D9;&#x05D4; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; (🙉/🙈) &#x05DE;&#x05D0;&#x05E4;&#x05E9;&#x05E8; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05D1;&#x05D6;&#x05D9;&#x05D0;&#x05D4; &#x05D0;&#x05D7;&#x05D3;. &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05DB;&#x05E0;&#x05D9;&#x05E1; &#x05DC;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4;, &#x05D0;&#x05D6; &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05D4;&#x05E9;&#x05D9;&#x05D1;&#x05D5;&#x05D9;&#x05DD; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D9;&#x05DD;. &#x05E6;&#x05D0; &#x05DE;&#x05DE;&#x05D5;&#x05D3; &#x05D4;&#x05D4;&#x05E1;&#x05EA;&#x05E8;&#x05D4; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05D7;&#x05D9;&#x05DC; &#x05D0;&#x05EA; &#x05D4;&#x05E9;&#x05D9;&#x05E0;&#x05D5;&#x05D9;&#x05DD;.</li>
        <li><b>&#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4;:</b> &#x05DE;&#x05E8;&#x05D9;&#x05D6; &#x05D0;&#x05D9;&#x05E9;&#x05D5;&#x05D8; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD; &#x05D1;&#x05D4;&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05D1;&#x05E2;&#x05D3; &#x05D4;&#x05E7;&#x05E4;&#x05D5;&#x05D3; &#x05D4;&#x05D7;&#x05D3;&#x05E9; &#x05E9;&#x05DC; &#x05D4;&#x05D8;&#x05E8;&#x05D2;&#x05D8; (🎯). &#x05D6;&#x05D4; &#x05DE;&#x05D9;&#x05D8;&#x05D9;&#x05D1; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05D0;&#x05EA; &#x05DE;&#x05D9;&#x05D3;&#x05EA; &#x05D4;&#x05E7;&#x05E0;&#x05D1;&#x05E1; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05D4;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05D0;&#x05EA; &#x05DB;&#x05DC; &#x05D4;&#x05E2;&#x05D1;&#x05D5;&#x05D4; &#x05E9;&#x05DC; &#x05DA; &#x05DEְ&#x05D5;&#x05E8;&#x05D9;&#x05D6; &#x05D1;&#x05D4;&#x05E4;&#x05E0;&#x05D4;.</li>
        <li><b>&#x05E1;&#x05D9;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05D9;&#x05E8; &#x05E9;&#x05DC; &#x05E7;&#x05E9;&#x05E8;:</b> &#x05E2;&#x05E9;&#x05D9;&#x05E7; &#x05E2;&#x05DC; &#x05DB;&#x05DC; &#x05D7;&#x05D5;&#x05D8; &#x05D0;&#x05D5; &#x05D7;&#x05D5;&#x05D8; &#x05DE;&#x05D5;&#x05D5;&#x05D2;&#x05D3; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA; &#x05D1;&#x05E2;&#x05D9;&#x05E7; &#x05D9;&#x05DE;&#x05D9;&#x05DF; &#x05DB;&#x05D3;&#x05D9; &#x05DC;&#x05E1;&#x05D2;&#x05D5;&#x05E8; &#x05DE;&#x05D4;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E7;&#x05E9;&#x05E8;. &#x05D4;&#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05DE;&#x05D5;&#x05D0;&#x05D9;&#x05E9;&#x05EA; &#x05D5;&#x05DE;&#x05D7;&#x05D1;&#x05E8;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05DC;&#x05D4;&#x05D7;&#x05D5;&#x05D8; &#x05D4;&#x05D0;&#x05D9;&#x05D5;&#x05D9; &#x05D4;&#x05DE;&#x05EA;&#x05D0;&#x05D9;&#x05DD; &#x05E2;&#x05DD; &#x05E7;&#x05E6;&#x05D4; &#x05D7;&#x05D5;&#x05E4;&#x05E9;&#x05D9;&#x05EA;.</li>
        <li><b>&#x05E9;&#x05E4;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; - &#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; (🇩🇪):</b> &#x05D0;&#x05EA;&#x05D4; &#x05D9;&#x05DB;&#x05D5;&#x05DC; &#x05DC;&#x05D1;&#x05D7;&#x05D5;&#x05E8; &#x05DC;&#x05D2;&#x05E8;&#x05DE;&#x05E0;&#x05D9;&#x05EA; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05E9;&#x05E0;&#x05D9;&#x05EA; &#x05E9;&#x05E4;&#x05D4;.</li>
        <li><b>&#x05E7;&#x05D8;&#x05D2;&#x05D5;&#x05E8;&#x05D9;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D4; &#x05E9;&#x05DC; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;:</b> &#x05D7;&#x05E7;&#x05E8; &#x05D0;&#x05EA; &#x05D4;&#x05E4;&#x05E8;&#x05D5;&#x05D9;&#x05D9;&#x05E7;&#x05D8;&#x05D9;&#x05DD; &#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD; &#x05D4;&#x05E8;&#x05D9;&#x05D9;&#x05DD; &#x05DC;&#x05D8;&#x05D5;&#x05D7;&#x05D4; &#x05D1;&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; → &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D9;&#x05DD;. &#x05D1;&#x05D7;&#x05E7;&#x05E8; &#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05DC;&#x05DC;&#x05DE;&#x05D9;&#x05D3; - &#x05D4;&#x05D3;&#x05D9;&#x05D0;&#x05DC;&#x05D5;&#x05D2; &#x05D9;&#x05D9;&#x05E1;&#x05D5;&#x05D2; &#x05D5;&#x05D4;&#x05D3;&#x05D5;&#x05D2;&#x05DE;&#x05D4; &#x05D9;&#x05D8;&#x05D5;&#x05D7;&#x05D4;.</li>
    </ul>
    </div>
    <hr>
        <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>SVG Shape Support:</b> Added new SVG-based shapes (circle, square, triangle) for improved rendering quality and scalability. These shapes now load correctly in both the application and exported executables.</li>
        <li><b>Enhanced Canvas Guides:</b> New control point SVG guides for better visual feedback when manipulating canvas elements.</li>
        <li><b>Translation improvements</b> for canvas guide elements.</li>
        <li><b>Improved color consistency</b> for button explanation titles.</li>
    </ul>
    <p>Previous updates (1.101):</p>
    <ul>
        <li>Improved Layer Management, Group Duplication, Hide Mode, Center View, Quick Knot Closing</li>
        <li>New Language - German (🇩🇪)</li>
        <li>New Samples category</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.101</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Gestion améliorée des couches :</b> Structure StateLayerManager améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.</li>
        <li><b>Duplication de groupe :</b> Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant "Dupliquer le groupe". Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.</li>
        <li><b>Mode masquage :</b> Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permet de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches pour les masquer. Quittez le mode masquage pour appliquer les changements.</li>
        <li><b>Centrer la vue :</b> Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). Cela ajuste automatiquement la position du canevas pour afficher tout votre travail centré à l'écran.</li>
        <li><b>Fermeture rapide de nœud :</b> Cliquez avec le bouton droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et connecte automatiquement au brin compatible le plus proche avec une extrémité libre.</li>
        <li><b>Nouvelle langue - Allemand (🇩🇪) :</b> Vous pouvez maintenant sélectionner l'allemand dans Paramètres → Changer la langue.</li>
        <li><b>Nouvelle catégorie Exemples :</b> Découvrez des projets d'exemple prêts à charger dans Paramètres → Exemples. Choisissez un exemple pour apprendre ; la boîte de dialogue se fermera et l'exemple sera chargé.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Verbesserte Ebenenverwaltung:</b> Verbesserte StateLayerManager-Struktur für zuverlässigeres Handling von Knotenverbindungen und Strangbeziehungen, mit stabileren Operationen und besserer Performance.</li>
        <li><b>Gruppenduplikation:</b> Sie können jetzt ganze Gruppen mit allen ihren Strängen duplizieren, indem Sie mit der rechten Maustaste auf eine Gruppenüberschrift klicken und "Gruppe duplizieren" auswählen. Die duplizierte Gruppe behält alle Strangeigenschaften bei und generiert automatisch eindeutige Ebenennamen.</li>
        <li><b>Versteckmodus:</b> Neuer Versteckmodus, der über die Affen-Schaltfläche (🙉/🙈) zugänglich ist, ermöglicht es Ihnen, mehrere Ebenen schnell gleichzeitig auszublenden. Klicken Sie auf die Schaltfläche, um in den Versteckmodus zu wechseln, klicken Sie dann auf Ebenen, um sie auszublenden. Verlassen Sie den Versteckmodus, um die Änderungen zu übernehmen.</li>
        <li><b>Ansicht zentrieren:</b> Zentrieren Sie sofort alle Stränge in Ihrer Ansicht mit der neuen Ziel-Schaltfläche (🎯). Dies passt automatisch die Leinwandposition an, um alle Ihre Arbeit zentriert auf dem Bildschirm anzuzeigen.</li>
        <li><b>Schnelles Knotenschließen:</b> Klicken Sie mit der rechten Maustaste auf einen beliebigen Strang oder verbundenen Strang mit einem freien Ende, um den Knoten schnell zu schließen. Das System findet und verbindet automatisch mit dem nächstgelegenen kompatiblen Strang mit einem freien Ende.</li>
        <li><b>Neue Sprache – Deutsch (🇩🇪):</b> Sie können jetzt zu Deutsch in Einstellungen → Sprache ändern wechseln.</li>
        <li><b>Neue Kategorie „Beispiele" :</b> Entdecken Sie bereit-zu-ladende Beispielprojekte in Einstellungen → Beispiele. Wählen Sie ein Beispiel zum Lernen; der Dialog schließt sich und das Beispiel wird geladen.</li>
    </ul>
    <hr>    
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.101</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Gestione livelli migliorata:</b> Struttura StateLayerManager migliorata per una migliore gestione delle connessioni dei nodi e delle relazioni tra trefoli, offrendo operazioni sui livelli più affidabili e prestazioni migliorate.</li>
        <li><b>Duplicazione gruppo:</b> Ora puoi duplicare interi gruppi con tutti i loro trefoli facendo clic destro sull'intestazione di un gruppo e selezionando "Duplica gruppo". Il gruppo duplicato mantiene tutte le proprietà dei trefoli e genera automaticamente nomi di livelli unici.</li>
        <li><b>Modalità nascondi:</b> Nuova modalità nascondi accessibile tramite il pulsante scimmia (🙉/🙈) permette di nascondere rapidamente più livelli contemporaneamente. Clicca sul pulsante per entrare in modalità nascondi, poi clicca sui livelli per nasconderli. Esci dalla modalità nascondi per applicare le modifiche.</li>
        <li><b>Centra vista:</b> Centra istantaneamente tutti i trefoli nella tua vista con il nuovo pulsante bersaglio (🎯). Questo regola automaticamente la posizione del canvas per mostrare tutto il tuo lavoro centrato sullo schermo.</li>
        <li><b>Chiusura rapida del nodo:</b> Fai clic destro su qualsiasi trefolo o trefolo attaccato con un'estremità libera per chiudere rapidamente il nodo. Il sistema trova e connette automaticamente al trefolo compatibile più vicino con un'estremità libera.</li>
        <li><b>Nuova lingua - Tedesco (🇩🇪):</b> Ora puoi selezionare il tedesco in Impostazioni → Cambia Lingua.</li>
        <li><b>Nuova categoria Esempi:</b> Scopri progetti di esempio pronti al caricamento in Impostazioni → Esempi. Scegli un esempio da cui imparare; la finestra si chiuderà e l'esempio verrà caricato.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.101</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Gestión mejorada de capas:</b> Estructura StateLayerManager mejorada para un mejor manejo de las conexiones de nudos y relaciones entre hebras, ofreciendo operaciones de capas más confiables y mejor rendimiento.</li>
        <li><b>Duplicación de grupo:</b> Ahora puedes duplicar grupos completos con todas sus hebras haciendo clic derecho en el encabezado de un grupo y seleccionando "Duplicar grupo". El grupo duplicado mantiene todas las propiedades de las hebras y genera automáticamente nombres de capas únicos.</li>
        <li><b>Modo ocultar:</b> Nuevo modo ocultar accesible a través del botón mono (🙉/🙈) permite ocultar rápidamente múltiples capas a la vez. Haz clic en el botón para entrar en modo ocultar, luego haz clic en las capas para ocultarlas. Sal del modo ocultar para aplicar los cambios.</li>
        <li><b>Centrar vista:</b> Centra instantáneamente todas las hebras en tu vista con el nuevo botón diana (🎯). Esto ajusta automáticamente la posición del lienzo para mostrar todo tu trabajo centrado en la pantalla.</li>
        <li><b>Cierre rápido de nudo:</b> Haz clic derecho en cualquier hebra o hebra adjunta con un extremo libre para cerrar rápidamente el nudo. El sistema encuentra y conecta automáticamente a la hebra compatible más cercana con un extremo libre.</li>
        <li><b>Nuevo idioma - Alemán (🇩🇪):</b> Ahora puedes cambiar a alemán en Configuración → Cambiar Idioma.</li>
        <li><b>Nueva categoría Ejemplos:</b> Explora proyectos de ejemplo listos para cargar en Configuración → Ejemplos. Elige un ejemplo para aprender; el cuadro de diálogo se cerrará y el ejemplo se cargará.</li>
    </ul>
    <hr>
        <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.101</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Gestão melhorada de camadas:</b> Estrutura StateLayerManager melhorada para melhor gestão de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.</li>
        <li><b>Duplicação de grupo:</b> Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar Grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.</li>
        <li><b>Modo ocultar:</b> Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente múltiplas camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.</li>
        <li><b>Centralizar vista:</b> Centralize instantaneamente todos os fios na sua vista com o novo botão alvo (🎯). Isso ajusta automaticamente a posição da tela para mostrar todo o seu trabalho centralizado na tela.</li>
        <li><b>Fechamento rápido de nó:</b> Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio compatível mais próximo com uma extremidade livre.</li>
        <li><b>Nova língua - Alemão (🇩🇪):</b> Agora você pode selecionar alemão em Configurações → Alterar Idioma.</li>
        <li><b>Nova categoria Exemplos:</b> Explore projetos de exemplo prontos para carregar em Configurações → Exemplos. Escolha um exemplo para aprender; a caixa de diálogo fechará e o exemplo será carregado.</li>
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
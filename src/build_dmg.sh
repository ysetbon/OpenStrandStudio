#!/bin/bash

# Set variables to match ISS configuration
APP_NAME="OpenStrandStudio"
VERSION="1.102"
APP_DATE="08_September_2025"
PUBLISHER="Yonatan Setbon"
DMG_NAME="OpenStrandStudioSetup_${APP_DATE}_${VERSION}"

# Create a temporary directory for DMG contents
TMP_DIR="$(mktemp -d)"
DMG_DIR="$TMP_DIR/$APP_NAME"
mkdir -p "$DMG_DIR"

# Create installer_output directory if it doesn't exist
INSTALLER_OUTPUT="/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/installer_output"
mkdir -p "$INSTALLER_OUTPUT"

# Copy the .app bundle from the correct location
APP_SOURCE="/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/dist/OpenStrandStudio.app"  # Updated path
if [ ! -d "$APP_SOURCE" ]; then
    echo "Error: Could not find .app at: $APP_SOURCE"
    echo "Please run 'pyinstaller OpenStrandStudio_mac.spec' first"
    exit 1
fi

# Copy the .app bundle to the temporary directory
cp -R "$APP_SOURCE" "$DMG_DIR/"

# Create a symbolic link to Applications folder
ln -s /Applications "$DMG_DIR/Applications"

# Create README.txt with version info and contact
cat > "$DMG_DIR/README.txt" << EOF
$APP_NAME $VERSION
By $PUBLISHER
Contact: ysetbon@gmail.com

New in this version (English):
• Improved Layer Management: Enhanced StateLayerManager structure for better handling of knot connections and strand relationships, providing more reliable layer operations and improved performance.
• Group Duplication: You can now duplicate entire groups with all their strands by right-clicking on a group header and selecting "Duplicate Group". The duplicated group maintains all strand properties and automatically generates unique layer names.
• Hide Mode: New hide mode accessible via the monkey button (🙉/🙈) allows you to quickly hide multiple layers at once. Click the button to enter hide mode, then click on layers to hide them. Exit hide mode to apply changes.
• Center View: Instantly center all strands in your view with the new target button (🎯). This automatically adjusts the canvas position to show all your work centered on screen.
• Quick Knot Closing: Right-click on any strand or attached strand with one free end to quickly close the knot. The system automatically finds and connects to the nearest compatible strand with a free end.
• New Language - German (🇩🇪): Switch to German in Settings → Change Language.
• New Samples category: Explore ready-to-load sample projects in Settings → Samples. Choose a sample to learn from; the dialog will close and the sample will be loaded.

Nouveautés dans cette version (Français):
• Gestion améliorée des couches : Structure StateLayerManager améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.
• Duplication de groupe : Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant "Dupliquer le groupe". Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.
• Mode masquage : Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permet de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches pour les masquer. Quittez le mode masquage pour appliquer les changements.
• Centrer la vue : Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). Cela ajuste automatiquement la position du canevas pour afficher tout votre travail centré à l'écran.
• Fermeture rapide de nœud : Cliquez avec le bouton droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et connecte automatiquement au brin compatible le plus proche avec une extrémité libre.
• Nouvelle langue - Allemand (🇩🇪) : Vous pouvez maintenant sélectionner l'allemand dans Paramètres → Changer la langue.
• Nouvelle catégorie Exemples : Découvrez des projets d'exemple prêts à charger dans Paramètres → Exemples. Choisissez un exemple pour apprendre ; la boîte de dialogue se fermera et l'exemple sera chargé.

Novità in questa versione (Italiano):
• Gestione livelli migliorata: Struttura StateLayerManager migliorata per una migliore gestione delle connessioni dei nodi e delle relazioni tra trefoli, offrendo operazioni sui livelli più affidabili e prestazioni migliorate.
• Duplicazione gruppo: Ora puoi duplicare interi gruppi con tutti i loro trefoli facendo clic destro sull'intestazione di un gruppo e selezionando "Duplica gruppo". Il gruppo duplicato mantiene tutte le proprietà dei trefoli e genera automaticamente nomi di livelli unici.
• Modalità nascondi: Nuova modalità nascondi accessibile tramite il pulsante scimmia (🙉/🙈) permette di nascondere rapidamente più livelli contemporaneamente. Clicca sul pulsante per entrare in modalità nascondi, poi clicca sui livelli per nasconderli. Esci dalla modalità nascondi per applicare le modifiche.
• Centra vista: Centra istantaneamente tutti i trefoli nella tua vista con il nuovo pulsante bersaglio (🎯). Questo regola automaticamente la posizione del canvas per mostrare tutto il tuo lavoro centrato sullo schermo.
• Chiusura rapida del nodo: Fai clic destro su qualsiasi trefolo o trefolo attaccato con un'estremità libera per chiudere rapidamente il nodo. Il sistema trova e connette automaticamente al trefolo compatibile più vicino con un'estremità libera.
• Nuova lingua - Tedesco (🇩🇪): Ora puoi selezionare il tedesco in Impostazioni → Cambia Lingua.
• Nuova categoria Esempi: Scopri progetti di esempio pronti al caricamento in Impostazioni → Esempi. Scegli un esempio da cui imparare; la finestra si chiuderà e l'esempio verrà caricato.

Novedades en esta versión (Español):
• Gestión mejorada de capas: Estructura StateLayerManager mejorada para un mejor manejo de las conexiones de nudos y relaciones entre hebras, ofreciendo operaciones de capas más confiables y mejor rendimiento.
• Duplicación de grupo: Ahora puedes duplicar grupos completos con todas sus hebras haciendo clic derecho en el encabezado de un grupo y seleccionando "Duplicar grupo". El grupo duplicado mantiene todas las propiedades de las hebras y genera automáticamente nombres de capas únicos.
• Modo ocultar: Nuevo modo ocultar accesible a través del botón mono (🙉/🙈) permite ocultar rápidamente múltiples capas a la vez. Haz clic en el botón para entrar en modo ocultar, luego haz clic en las capas para ocultarlas. Sal del modo ocultar para aplicar los cambios.
• Centrar vista: Centra instantáneamente todas las hebras en tu vista con el nuevo botón diana (🎯). Esto ajusta automáticamente la posición del lienzo para mostrar todo tu trabajo centrado en la pantalla.
• Cierre rápido de nudo: Haz clic derecho en cualquier hebra o hebra adjunta con un extremo libre para cerrar rápidamente el nudo. El sistema encuentra y conecta automáticamente a la hebra compatible más cercana con un extremo libre.
• Nuevo idioma - Alemán (🇩🇪): Ahora puedes cambiar a alemán en Configuración → Cambiar Idioma.
• Nueva categoría Ejemplos: Explora proyectos de ejemplo listos para cargar en Configuración → Ejemplos. Elige un ejemplo para aprender; el cuadro de diálogo se cerrará y el ejemplo se cargará.

Novidades nesta versão (Português):
• Gestão melhorada de camadas: Estrutura StateLayerManager melhorada para melhor gestão de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.
• Duplicação de grupo: Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar Grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.
• Modo ocultar: Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente múltiplas camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.
• Centralizar vista: Centralize instantaneamente todos os fios na sua vista com o novo botão alvo (🎯). Isso ajusta automaticamente a posição da tela para mostrar todo o seu trabalho centralizado na tela.
• Fechamento rápido de nó: Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio compatível mais próximo com uma extremidade livre.
• Nova língua - Alemão (🇩🇪): Agora você pode selecionar alemão em Configurações → Alterar Idioma.
• Nova categoria Exemplos: Explore projetos de exemplo prontos para carregar em Configurações → Exemplos. Escolha um exemplo para aprender; a caixa de diálogo fechará e o exemplo será carregado.

Neu in dieser Version (Deutsch):
• Verbesserte Ebenenverwaltung: Verbesserte StateLayerManager-Struktur für zuverlässigeres Handling von Knotenverbindungen und Strangbeziehungen, mit stabileren Operationen und besserer Performance.
• Gruppenduplikation: Sie können jetzt ganze Gruppen mit allen ihren Strängen duplizieren, indem Sie mit der rechten Maustaste auf eine Gruppenüberschrift klicken und "Gruppe duplizieren" auswählen. Die duplizierte Gruppe behält alle Strangeigenschaften bei und generiert automatisch eindeutige Ebenennamen.
• Versteckmodus: Neuer Versteckmodus, der über die Affen-Schaltfläche (🙉/🙈) zugänglich ist, ermöglicht es Ihnen, mehrere Ebenen schnell gleichzeitig auszublenden. Klicken Sie auf die Schaltfläche, um in den Versteckmodus zu wechseln, klicken Sie dann auf Ebenen, um sie auszublenden. Verlassen Sie den Versteckmodus, um die Änderungen zu übernehmen.
• Ansicht zentrieren: Zentrieren Sie sofort alle Stränge in Ihrer Ansicht mit der neuen Ziel-Schaltfläche (🎯). Dies passt automatisch die Leinwandposition an, um alle Ihre Arbeit zentriert auf dem Bildschirm anzuzeigen.
• Schnelles Knotenschließen: Klicken Sie mit der rechten Maustaste auf einen beliebigen Strang oder verbundenen Strang mit einem freien Ende, um den Knoten schnell zu schließen. Das System findet und verbindet automatisch mit dem nächstgelegenen kompatiblen Strang mit einem freien Ende.
• Neue Sprache – Deutsch (🇩🇪): Sie können jetzt zu Deutsch in Einstellungen → Sprache ändern wechseln.
• Neue Kategorie „Beispiele": Entdecken Sie bereit-zu-ladende Beispielprojekte in Einstellungen → Beispiele. Wählen Sie ein Beispiel zum Lernen; der Dialog schließt sich und das Beispiel wird geladen.

חדש בגרסה זו (עברית):
• ניהול שכבות משופר: מבנה StateLayerManager משופר לניהול טוב יותר של חיבורי קשרים ויחסים בין חוטים, המספק פעולות שכבות אמינות יותר וביצועים משופרים.
• שכפול קבוצה: עכשיו אפשר לשכפל קבוצות שלמות עם כל החוטים שלהן על ידי לחיצה ימנית על כותרת קבוצה ובחירת "שכפל קבוצה". הקבוצה המשוכפלת שומרת על כל תכונות החוטים ומייצרת אוטומטית שמות שכבות ייחודיים.
• מצב הסתרה: מצב הסתרה חדש נגיש דרך כפתור הקוף (🙉/🙈) מאפשר להסתיר במהירות מספר שכבות בבת אחת. לחץ על הכפתור כדי להיכנס למצב הסתרה, ואז לחץ על השכבות כדי להסתיר אותן. צא ממצב ההסתרה כדי להחיל שינויים.
• מרכוז תצוגה: מרכז מיד את כל החוטים בתצוגה שלך עם כפתור המטרה החדש (🎯). זה מתאים אוטומטית את מיקום הקנבס כדי להראות את כל העבודה שלך ממורכזת על המסך.
• סגירת קשר מהירה: לחץ ימני על כל חוט או חוט מחובר עם קצה חופשי כדי לסגור במהירות את הקשר. המערכת מוצאת ומחברת אוטומטית לחוט התואם הקרוב ביותר עם קצה חופשי.
• שפה חדשה - גרמנית (🇩🇪): עכשיו אפשר לעבור לגרמנית בהגדרות → שנה שפה.
• קטגוריית דוגמאות חדשה: חקור פרויקטי דוגמה מוכנים לטעינה בהגדרות → דוגמאות. בחר דוגמה ללמוד ממנה; הדו-שיח ייסגר והדוגמה תיטען.

Installation:
1. Drag '$APP_NAME' to the Applications folder
2. Double-click the app in Applications to launch

For support, contact: ysetbon@gmail.com
EOF

# Create temporary DMG
TEMP_DMG="$TMP_DIR/temp.dmg"
FINAL_DMG="$INSTALLER_OUTPUT/${DMG_NAME}.dmg"

echo "Creating temporary DMG..."
hdiutil create -volname "$APP_NAME $VERSION" -srcfolder "$DMG_DIR" -ov -format UDRW "$TEMP_DMG"

echo "Converting to final DMG..."
hdiutil convert "$TEMP_DMG" -format UDZO -imagekey zlib-level=9 -o "$FINAL_DMG"

# Verify the DMG was created successfully
if [ ! -f "$FINAL_DMG" ]; then
    echo "Error: Failed to create DMG"
    exit 1
fi

# Set permissions
chmod 644 "$FINAL_DMG"

# Install fileicon if not already installed
if ! command -v fileicon &> /dev/null; then
    echo "Installing fileicon..."
    brew install fileicon
fi

# Set the DMG icon
echo "Setting DMG icon..."
fileicon set "$FINAL_DMG" "/Users/yonatan/Documents/GitHub/OpenStrandStudio/src/box_stitch.icns"

# Verify the DMG is mountable
echo "Verifying DMG..."
if ! hdiutil verify "$FINAL_DMG" >/dev/null; then
    echo "Warning: DMG verification failed"
else
    echo "DMG verified successfully"
fi

# Clean up
rm -rf "$TMP_DIR"

echo "DMG created at: $FINAL_DMG"
echo "Version: $VERSION"
echo "Publisher: $PUBLISHER"

# Try to mount the DMG to verify it works
echo "Testing DMG mount..."
hdiutil attach "$FINAL_DMG"

# Open the installer_output directory
open "$INSTALLER_OUTPUT"
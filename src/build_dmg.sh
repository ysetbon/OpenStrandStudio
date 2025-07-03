#!/bin/bash

# Set variables to match ISS configuration
APP_NAME="OpenStrandStudio"
VERSION="1.100"
APP_DATE="3_July_2025"
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
• Strand Width Control: You can now dynamically adjust the width of individual strands, giving you more flexibility in creating varied knot designs.
• Zoom In/Out: You can zoom in and out of your design to see small details or the entire diagram.
• Pan Screen: You can drag the canvas by clicking the hand button, which helps when working on larger diagrams.
• Shadow-Only Mode: You can now hide a layer while still showing its shadows and highlights by right-clicking on a layer button and selecting "Shadow Only". This helps visualize shadow effects without the visual clutter.
• Initial Setup: When first starting the application, you'll need to click "New Strand" to begin creating your first strand.
• General Fixes: Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.
• Higher Quality Rendering: Improved canvas display quality and 4x higher resolution image export for crisp, professional results.
• Removed Extended Mask Option: The extended mask option from the general layer has been removed since it was only needed as a backup for shader issues in older versions (1.09x). With greatly improved shading, this option is no longer necessary.

Nouveautés dans cette version (Français):
• Contrôle de la largeur des brins : Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.
• Zoom avant/arrière : Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.
• Déplacement de l'écran : Vous pouvez faire glisser le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.
• Mode ombre uniquement : Vous pouvez maintenant masquer une couche tout en affichant ses ombres et reflets en faisant un clic droit sur un bouton de couche et en sélectionnant "Ombre uniquement". Cela aide à visualiser les effets d'ombre sans l'encombrement visuel.
• Configuration initiale : Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.
• Corrections générales : Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.
• Rendu de qualité supérieure : Amélioration de la qualité d'affichage du canevas et export d'images en résolution 4x plus élevée pour des résultats nets et professionnels.
• Suppression de l'option masque étendu : L'option masque étendu de la couche générale a été supprimée car elle était uniquement nécessaire comme solution de secours pour les problèmes de shader dans les anciennes versions (1.09x). Avec l'ombrage grandement amélioré, cette option n'est plus nécessaire.

Novità in questa versione (Italiano):
• Controllo della larghezza dei trefoli: Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.
• Zoom avanti/indietro: Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.
• Spostamento schermo: Puoi trascinare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.
• Modalità solo ombra: Ora puoi nascondere un livello pur mostrando le sue ombre e luci facendo clic destro su un pulsante livello e selezionando "Solo Ombra". Questo aiuta a visualizzare gli effetti ombra senza il disordine visivo.
• Configurazione iniziale: Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.
• Correzioni generali: Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.
• Rendering di qualità superiore: Migliorata la qualità di visualizzazione del canvas e esportazione immagini con risoluzione 4x più alta per risultati nitidi e professionali.
• Rimossa opzione maschera estesa: L'opzione maschera estesa dal livello generale è stata rimossa poiché era necessaria solo come backup per problemi di shader nelle versioni precedenti (1.09x). Con l'ombreggiatura notevolmente migliorata, questa opzione non è più necessaria.

Novedades en esta versión (Español):
• Control del ancho de las hebras: Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.
• Zoom acercar/alejar: Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.
• Mover pantalla: Puedes arrastrar el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.
• Modo solo sombra: Ahora puedes ocultar una capa mientras sigues mostrando sus sombras y luces haciendo clic derecho en un botón de capa y seleccionando "Solo Sombra". Esto ayuda a visualizar los efectos de sombra sin el desorden visual.
• Configuración inicial: Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.
• Correcciones generales: Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.
• Renderizado de mayor calidad: Mejora en la calidad de visualización del lienzo y exportación de imágenes con resolución 4x más alta para resultados nítidos y profesionales.
• Eliminada opción de máscara extendida: La opción de máscara extendida de la capa general ha sido eliminada ya que solo era necesaria como respaldo para problemas de shader en versiones anteriores (1.09x). Con el sombreado considerablemente mejorado, esta opción ya no es necesaria.

Novidades nesta versão (Português):
• Controle de largura dos fios: Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.
• Zoom ampliar/reduzir: Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.
• Mover tela: Você pode arrastar o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.
• Modo apenas sombra: Agora você pode ocultar uma camada enquanto ainda mostra suas sombras e destaques clicando com o botão direito em um botão de camada e selecionando "Apenas Sombra". Isso ajuda a visualizar efeitos de sombra sem a desordem visual.
• Configuração inicial: Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.
• Correções gerais: Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.
• Renderização de qualidade superior: Melhoria na qualidade de exibição do canvas e exportação de imagens com resolução 4x mais alta para resultados nítidos e profissionais.
• Removida opção de máscara estendida: A opção de máscara estendida da camada geral foi removida pois era necessária apenas como backup para problemas de shader em versões antigas (1.09x). Com o sombreamento muito melhorado, esta opção não é mais necessária.

חדש בגרסה זו (עברית):
• שינוי רוחב חוטים: עכשיו אפשר לשנות את העובי של כל חוט בנפרד, כך שתוכלו ליצור עיצובים יותר מגוונים.
• הגדלה והקטנה: אפשר להתקרב ולהתרחק מהעיצוב שלכם כדי לראות פרטים קטנים או את כל הדיאגרמה.
• הזזת המסך: אפשר לגרור את הקנבס על ידי לחיצה על כפתור היד, מה שעוזר בעבודה על דיאגרמות גדולות יותר.
• מצב צל בלבד: עכשיו אפשר להסתיר שכבה תוך הצגת הצללים וההדגשות שלה על ידי לחיצה ימנית על כפתור שכבה ובחירת "צל בלבד". זה עוזר להמחיש אפקטי צל ללא העומס החזותי.
• התחלת עבודה: כשפותחים את התוכנה בפעם הראשונה, צריך ללחוץ על "חוט חדש" כדי להתחיל לצייר.
• תיקונים כלליים: תוקנו מספר תקלות ובעיות שנגרמו מגרסאות קודמות, כמו למשל כפתורי ביטול וחזרה יצרו חלון זמני ולא סיפקו חווית משתמש חלקה.
• איכות תצוגה משופרת: שיפור באיכות תצוגת הקנבס ויצוא תמונות ברזולוציה גבוהה פי 4 לתוצאות חדות ומקצועיות.
• הסרת אפשרות מסכה מורחבת: האפשרות למסכה מורחבת בשכבה הכללית הוסרה מכיוון שהיא הייתה נחוצה רק כגיבוי לבעיות shader בגרסאות קודמות (1.09x). עם שיפור ההצללה באופן משמעותי, אפשרות זו אינה נחוצה עוד.

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
#!/bin/bash

# Set variables to match ISS configuration
APP_NAME="OpenStrandStudio"
VERSION="1.100"
APP_DATE="19_June_2025"
PUBLISHER="Yonatan Setbon"
DMG_NAME="OpenStrandStudioSetup_${APP_DATE}_${VERSION}"

# Create a temporary directory for DMG contents
TMP_DIR="$(mktemp -d)"
DMG_DIR="$TMP_DIR/$APP_NAME"
mkdir -p "$DMG_DIR"

# Create installer_output directory if it doesn't exist
INSTALLER_OUTPUT="/Users/yonatansetbon/Documents/GitHub/OpenStrandStudio/src/installer_output"
mkdir -p "$INSTALLER_OUTPUT"

# Copy the .app bundle from the correct location
APP_SOURCE="/Users/yonatansetbon/Documents/GitHub/OpenStrandStudio/src/dist/OpenStrandStudio.app"  # Updated path
if [ ! -d "$APP_SOURCE" ]; then
    echo "Error: Could not find .app at: $APP_SOURCE"
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
• Pan Screen: You can move the canvas by clicking the hand button, which helps when working on larger diagrams.
• Initial Setup: When first starting the application, you'll need to click "New Strand" to begin creating your first strand.
• General Fixes: Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.

Nouveautés dans cette version (Français):
• Contrôle de la largeur des brins : Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.
• Zoom avant/arrière : Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.
• Déplacement de l'écran : Vous pouvez déplacer le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.
• Configuration initiale : Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.
• Corrections générales : Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.

Novità in questa versione (Italiano):
• Controllo della larghezza dei trefoli: Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.
• Zoom avanti/indietro: Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.
• Spostamento schermo: Puoi spostare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.
• Configurazione iniziale: Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.
• Correzioni generali: Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.

Novedades en esta versión (Español):
• Control del ancho de las hebras: Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.
• Zoom acercar/alejar: Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.
• Mover pantalla: Puedes mover el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.
• Configuración inicial: Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.
• Correcciones generales: Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.

Novidades nesta versão (Português):
• Controle de largura dos fios: Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.
• Zoom ampliar/reduzir: Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.
• Mover tela: Você pode mover o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.
• Configuração inicial: Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.
• Correções gerais: Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.

חדש בגרסה זו (עברית):
• שינוי רוחב חוטים: עכשיו אפשר לשנות את העובי של כל חוט בנפרד, כך שתוכלו ליצור עיצובים יותר מגוונים.
• הגדלה והקטנה: אפשר להתקרב ולהתרחק מהעיצוב שלכם כדי לראות פרטים קטנים או את כל הדיאגרמה.
• הזזת המסך: אפשר להזיז את הקנבס על ידי לחיצה על כפתור היד, מה שעוזר בעבודה על דיאגרמות גדולות יותר.
• התחלת עבודה: כשפותחים את התוכנה בפעם הראשונה, צריך ללחוץ על "חוט חדש" כדי להתחיל לצייר.
• תיקונים כלליים: תוקנו מספר תקלות ובעיות שנגרמו מגרסאות קודמות, כמו למשל כפתורי ביטול וחזרה יצרו חלון זמני ולא סיפקו חווית משתמש חלקה.

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
fileicon set "$FINAL_DMG" "/Users/yonatansetbon/Documents/GitHub/OpenStrandStudio/src/box_stitch.icns"

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
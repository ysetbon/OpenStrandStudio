#!/bin/bash

# Set variables to match ISS configuration
APP_NAME="OpenStrandStudio"
VERSION="1.103"
APP_DATE="30_September_2025"
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

New in Version 1.103 (English):
• Full Arrow System: Comprehensive arrow feature with multiple customizable properties including arrow color (independent from strand), transparency (0-100%), head texture (None, Stripes, Dots, Crosshatch), shaft style (Solid, Stripes, Dots, Tiles), shadow support, head visibility toggle, and dimension controls.
• Smart Mask Group Selection: When creating groups with masked strands, selecting one component automatically includes its mask partner, maintaining mask integrity in grouped operations.
• Enhanced Painting System: Fixed rendering issues for strand paths and attached strands during draw operations, ensuring consistent visual representation.

Nouveautés dans la version 1.103 (Français):
• Système de flèches complet : Fonction de flèche complète avec plusieurs propriétés personnalisables incluant la couleur de flèche (indépendante du brin), transparence (0-100%), texture de tête (Aucune, Rayures, Points, Hachures croisées), style de tige (Solide, Rayures, Points, Carreaux), support d'ombre, visibilité de tête, et contrôles de dimension.
• Sélection intelligente de groupe masqué : Lors de la création de groupes avec des brins masqués, la sélection d'un composant inclut automatiquement son partenaire de masque, maintenant l'intégrité du masque dans les opérations groupées.
• Système de peinture amélioré : Correction des problèmes de rendu pour les chemins de brin et les brins attachés pendant les opérations de dessin.

Novità nella versione 1.103 (Italiano):
• Sistema di frecce completo: Funzione freccia completa con molteplici proprietà personalizzabili tra cui colore freccia (indipendente dal filamento), trasparenza (0-100%), texture della punta (Nessuna, Strisce, Punti, Tratteggio incrociato), stile dell'asta (Solido, Strisce, Punti, Piastrelle), supporto ombra, visibilità della punta e controlli dimensionali.
• Selezione intelligente gruppo maschera: Quando si creano gruppi con filamenti mascherati, selezionando un componente si include automaticamente il suo partner maschera, mantenendo l'integrità della maschera nelle operazioni di gruppo.
• Sistema di pittura migliorato: Risolti problemi di rendering per percorsi di filamento e filamenti attaccati durante le operazioni di disegno.

Novedades en la versión 1.103 (Español):
• Sistema de flechas completo: Función de flecha completa con múltiples propiedades personalizables incluyendo color de flecha (independiente del hilo), transparencia (0-100%), textura de punta (Ninguna, Rayas, Puntos, Trama cruzada), estilo del eje (Sólido, Rayas, Puntos, Azulejos), soporte de sombra, visibilidad de punta y controles de dimensión.
• Selección inteligente de grupo de máscara: Al crear grupos con hilos enmascarados, seleccionar un componente incluye automáticamente su compañero de máscara, manteniendo la integridad de la máscara en operaciones agrupadas.
• Sistema de pintura mejorado: Corregidos problemas de renderizado para rutas de hilos e hilos adjuntos durante operaciones de dibujo.

Novidades na versão 1.103 (Português):
• Sistema de setas completo: Recurso de seta abrangente com várias propriedades personalizáveis incluindo cor da seta (independente do fio), transparência (0-100%), textura da ponta (Nenhuma, Listras, Pontos, Hachura cruzada), estilo do eixo (Sólido, Listras, Pontos, Azulejos), suporte de sombra, visibilidade da ponta e controles dimensionais.
• Seleção inteligente de grupo de máscara: Ao criar grupos com fios mascarados, selecionar um componente inclui automaticamente seu parceiro de máscara, mantendo a integridade da máscara em operações agrupadas.
• Sistema de pintura aprimorado: Corrigidos problemas de renderização para caminhos de fios e fios anexados durante operações de desenho.

Neu in Version 1.103 (Deutsch):
• Vollständiges Pfeilsystem: Umfassende Pfeilfunktion mit mehreren anpassbaren Eigenschaften wie Pfeilfarbe (unabhängig vom Strang), Transparenz (0-100%), Kopftextur (Keine, Streifen, Punkte, Schraffur), Schaftstil (Solide, Streifen, Punkte, Kacheln), Schattenunterstützung, Kopfsichtbarkeit und Dimensionskontrollen.
• Intelligente Maskengruppenauswahl: Beim Erstellen von Gruppen mit maskierten Strängen wird beim Auswählen einer Komponente automatisch der Maskenpartner eingeschlossen, wodurch die Maskenintegrität in gruppierten Operationen erhalten bleibt.
• Verbessertes Malsystem: Behobene Renderprobleme für Strangpfade und angehängte Stränge während Zeichenoperationen.

&#x05DE;&#x05D4; &#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; 1.103 (&#x05E2;&#x05D1;&#x05E8;&#x05D9;&#x05EA;):
&#x2022; &#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05D7;&#x05D9;&#x05E6;&#x05D9;&#x05DD; &#x05DE;&#x05DC;&#x05D0;&#x05D4;: &#x05EA;&#x05DB;&#x05D5;&#x05E0;&#x05EA; &#x05D7;&#x05D9;&#x05E6;&#x05D9;&#x05DD; &#x05DE;&#x05E7;&#x05D9;&#x05E4;&#x05D4; &#x05E2;&#x05DD; &#x05DE;&#x05E1;&#x05E4;&#x05E8; &#x05DE;&#x05D0;&#x05E4;&#x05D9;&#x05D9;&#x05E0;&#x05D9;&#x05DD; &#x05D4;&#x05E0;&#x05D9;&#x05EA;&#x05E0;&#x05D9;&#x05DD; &#x05DC;&#x05D4;&#x05EA;&#x05D0;&#x05DE;&#x05D4; &#x05D0;&#x05D9;&#x05E9;&#x05D9;&#x05EA; &#x05DB;&#x05D5;&#x05DC;&#x05DC; &#x05E6;&#x05D1;&#x05E2; &#x05D7;&#x05E5; (&#x05D1;&#x05DC;&#x05EA;&#x05D9; &#x05EA;&#x05DC;&#x05D5;&#x05D9; &#x05D1;&#x05D2;&#x05D3;&#x05D9;&#x05DC;), &#x05E9;&#x05E7;&#x05D9;&#x05E4;&#x05D5;&#x05EA; (0-100%), &#x05DE;&#x05E8;&#x05E7;&#x05DD; &#x05E8;&#x05D0;&#x05E9; (&#x05DC;&#x05DC;&#x05D0;, &#x05E4;&#x05E1;&#x05D9;&#x05DD;, &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA;, &#x05D1;&#x05E7;&#x05D9;&#x05E2;&#x05D4; &#x05E6;&#x05D5;&#x05DC;&#x05D1;&#x05EA;), &#x05E1;&#x05D2;&#x05E0;&#x05D5;&#x05DF; &#x05E6;&#x05D9;&#x05E8; (&#x05DE;&#x05D5;&#x05E6;&#x05E7;, &#x05E4;&#x05E1;&#x05D9;&#x05DD;, &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA;, &#x05D0;&#x05E8;&#x05D9;&#x05D7;&#x05D9;&#x05DD;), &#x05EA;&#x05DE;&#x05D9;&#x05DB;&#x05D4; &#x05D1;&#x05E6;&#x05DC;, &#x05E0;&#x05E8;&#x05D0;&#x05D5;&#x05EA; &#x05E8;&#x05D0;&#x05E9; &#x05D5;&#x05E7;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05D9;&#x05DE;&#x05D3;.
&#x2022; &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05EA; &#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D7;&#x05DB;&#x05DE;&#x05D4;: &#x05D1;&#x05E2;&#x05EA; &#x05D9;&#x05E6;&#x05D9;&#x05E8;&#x05EA; &#x05E7;&#x05D1;&#x05D5;&#x05E6;&#x05D5;&#x05EA; &#x05E2;&#x05DD; &#x05D2;&#x05D3;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05DE;&#x05D5;&#x05E1;&#x05DB;&#x05D9;&#x05DD;, &#x05D1;&#x05D7;&#x05D9;&#x05E8;&#x05EA; &#x05E8;&#x05DB;&#x05D9;&#x05D1; &#x05D0;&#x05D7;&#x05D3; &#x05DB;&#x05D5;&#x05DC;&#x05DC;&#x05EA; &#x05D0;&#x05D5;&#x05D8;&#x05D5;&#x05DE;&#x05D8;&#x05D9;&#x05EA; &#x05D0;&#x05EA; &#x05E9;&#x05D5;&#x05EA;&#x05E3; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05E9;&#x05DC;&#x05D5;, &#x05EA;&#x05D5;&#x05DA; &#x05E9;&#x05DE;&#x05D9;&#x05E8;&#x05D4; &#x05E2;&#x05DC; &#x05E9;&#x05DC;&#x05DE;&#x05D5;&#x05EA; &#x05D4;&#x05DE;&#x05E1;&#x05DB;&#x05D4; &#x05D1;&#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05DE;&#x05E7;&#x05D5;&#x05D1;&#x05E6;&#x05D5;&#x05EA;.
&#x2022; &#x05DE;&#x05E2;&#x05E8;&#x05DB;&#x05EA; &#x05E6;&#x05D1;&#x05D9;&#x05E2;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05EA;: &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05E2;&#x05D1;&#x05D5;&#x05E8; &#x05E0;&#x05EA;&#x05D9;&#x05D1;&#x05D9; &#x05D2;&#x05D3;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05D5;&#x05D2;&#x05D3;&#x05D9;&#x05DC;&#x05D9;&#x05DD; &#x05DE;&#x05D7;&#x05D5;&#x05D1;&#x05E8;&#x05D9;&#x05DD; &#x05D1;&#x05DE;&#x05D4;&#x05DC;&#x05DA; &#x05E4;&#x05E2;&#x05D5;&#x05DC;&#x05D5;&#x05EA; &#x05E6;&#x05D9;&#x05D5;&#x05E8;.

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
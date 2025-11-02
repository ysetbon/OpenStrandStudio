#!/bin/bash

# Set variables to match ISS configuration
APP_NAME="OpenStrandStudio"
VERSION="1.104"
APP_DATE="02_November_2025"
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

New in Version 1.104 (English):
• Enhanced Control Point System: Improved UX for control point movement and activation behavior
• Endpoint Properties Management: Save samples and duplicate endpoint properties functionality
• Advanced Shadow Editor: Fixed dialog layout with multi-language support, subtraction operations, and improved history table
• User Settings Persistence: Save and load functionality for user settings
• Rendering Improvements: Fixed side line rendering issues and enhanced undo/redo functionality
• Additional UI improvements and bug fixes
• Performance optimizations

Nouveautés dans la version 1.104 (Français):
• Système de points de contrôle amélioré : Interface utilisateur améliorée pour le mouvement des points de contrôle et le comportement d'activation
• Gestion des propriétés des extrémités : Fonctionnalité de sauvegarde d'échantillons et de duplication des propriétés des extrémités
• Éditeur d'ombres avancé : Disposition de dialogue corrigée avec prise en charge multilingue, opérations de soustraction et table d'historique améliorée
• Persistance des paramètres utilisateur : Fonctionnalité de sauvegarde et de chargement des paramètres utilisateur
• Améliorations du rendu : Correction des problèmes de rendu des lignes latérales et amélioration de la fonctionnalité annuler/rétablir
• Améliorations de l'interface utilisateur et corrections de bugs supplémentaires
• Optimisations des performances

Novità nella versione 1.104 (Italiano):
• Sistema di punti di controllo migliorato: Migliorata l'esperienza utente per il movimento dei punti di controllo e il comportamento di attivazione
• Gestione delle proprietà degli endpoint: Funzionalità di salvataggio campioni e duplicazione delle proprietà degli endpoint
• Editor di ombre avanzato: Layout della finestra di dialogo corretto con supporto multilingue, operazioni di sottrazione e tabella cronologia migliorata
• Persistenza delle impostazioni utente: Funzionalità di salvataggio e caricamento delle impostazioni utente
• Miglioramenti del rendering: Risolti i problemi di rendering delle linee laterali e migliorata la funzionalità annulla/ripristina
• Ulteriori miglioramenti dell'interfaccia utente e correzioni di bug
• Ottimizzazioni delle prestazioni

Novedades en la versión 1.104 (Español):
• Sistema de puntos de control mejorado: Mejor experiencia de usuario para el movimiento de puntos de control y comportamiento de activación
• Gestión de propiedades de puntos finales: Funcionalidad de guardar muestras y duplicar propiedades de puntos finales
• Editor de sombras avanzado: Diseño de diálogo corregido con soporte multiidioma, operaciones de sustracción y tabla de historial mejorada
• Persistencia de configuración de usuario: Funcionalidad de guardar y cargar configuración de usuario
• Mejoras de renderizado: Solucionados problemas de renderizado de líneas laterales y mejorada la funcionalidad deshacer/rehacer
• Mejoras adicionales de la interfaz de usuario y correcciones de errores
• Optimizaciones de rendimiento

Novidades na versão 1.104 (Português):
• Sistema de pontos de controle aprimorado: Melhor experiência do usuário para movimento de pontos de controle e comportamento de ativação
• Gerenciamento de propriedades de pontos finais: Funcionalidade de salvar amostras e duplicar propriedades de pontos finais
• Editor de sombras avançado: Layout de diálogo corrigido com suporte multilíngue, operações de subtração e tabela de histórico aprimorada
• Persistência de configurações do usuário: Funcionalidade de salvar e carregar configurações do usuário
• Melhorias de renderização: Corrigidos problemas de renderização de linhas laterais e melhorada a funcionalidade desfazer/refazer
• Melhorias adicionais da interface do usuário e correções de bugs
• Otimizações de desempenho

Neu in Version 1.104 (Deutsch):
• Verbessertes Kontrollpunktsystem: Verbesserte Benutzerführung für Kontrollpunktbewegung und Aktivierungsverhalten
• Endpunkt-Eigenschaften-Verwaltung: Speichern von Mustern und Duplizieren von Endpunkt-Eigenschaften
• Erweiterter Schatten-Editor: Korrigiertes Dialog-Layout mit Mehrsprachenunterstützung, Subtraktionsoperationen und verbesserter Verlaufstabelle
• Benutzereinstellungen-Persistenz: Speicher- und Ladefunktion für Benutzereinstellungen
• Rendering-Verbesserungen: Behobene Seitenlinien-Rendering-Probleme und verbesserte Rückgängig/Wiederherstellen-Funktionalität
• Zusätzliche UI-Verbesserungen und Fehlerbehebungen
• Leistungsoptimierungen

מה חדש בגרסה 1.104 (עברית):
• מערכת נקודות בקרה משופרת: חווית משתמש משופרת לתנועת נקודות בקרה והתנהגות הפעלה
• ניהול מאפייני נקודות קצה: פונקציונליות שמירת דגימות ושכפול מאפייני נקודות קצה
• עורך צלים מתקדם: פריסת דו-שיח מתוקנת עם תמיכה רב-שפתית, פעולות חיסור וטבלת היסטוריה משופרת
• שמירת הגדרות משתמש: פונקציונליות שמירה וטעינה של הגדרות משתמש
• שיפורי עיבוד: תוקנו בעיות עיבוד של קווי צד ושופרה פונקציונליות ביטול/שחזור
• שיפורי ממשק משתמש ותיקוני באגים נוספים
• אופטימיזציות ביצועים

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

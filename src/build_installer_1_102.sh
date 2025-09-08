#!/bin/bash

# Set variables
APP_NAME="OpenStrandStudio"
VERSION="1_102"
APP_DATE="08_September_2025"
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

# Create welcome.html (English + localized sections). Updated to 1.102 what's-new.
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
        <li><b>Enhanced Curvature Bias Controls:</b> New bias control points between center and end control points for fine-tuned curvature adjustment.</li>
        <li><b>Advanced Curvature Settings:</b> Three new parameters - Control Point Influence, Distance Boost, and Curve Shape for complete curve control.</li>
        <li><b>Progressive Control Point Display:</b> Control points appear progressively to reduce visual clutter during initial strand placement.</li>
        <li><b>Improved Shading Rendering:</b> Fixed various shading issues for better visual quality.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Erweiterte Krümmungs-Bias-Steuerung:</b> Neue Bias-Kontrollpunkte zwischen mittlerem und End-Kontrollpunkten für präzise Krümmungsanpassung.</li>
        <li><b>Erweiterte Krümmungseinstellungen:</b> Drei neue Parameter - Kontrollpunkt-Einfluss, Distanz-Verstärkung und Kurvenform für vollständige Kurvenkontrolle.</li>
        <li><b>Progressive Kontrollpunkt-Anzeige:</b> Kontrollpunkte erscheinen progressiv, um visuelle Unordnung bei der anfänglichen Strangplatzierung zu reduzieren.</li>
        <li><b>Verbesserte Schattierungsdarstellung:</b> Verschiedene Schattierungsprobleme behoben für bessere visuelle Qualität.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.102</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôles de biais de courbure améliorés :</b> Nouveaux points de contrôle de biais entre les points de contrôle central et d'extrémité pour un ajustement précis de la courbure.</li>
        <li><b>Paramètres de courbure avancés :</b> Trois nouveaux paramètres - Influence du point de contrôle, Amplification de distance et Forme de courbe pour un contrôle complet des courbes.</li>
        <li><b>Affichage progressif des points de contrôle :</b> Les points de contrôle apparaissent progressivement pour réduire l'encombrement visuel lors du placement initial.</li>
        <li><b>Rendu d'ombrage amélioré :</b> Correction de divers problèmes d'ombrage pour une meilleure qualité visuelle.</li>
    </ul>
    <hr>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.102</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controlli di bias di curvatura avanzati:</b> Nuovi punti di controllo del bias tra i punti di controllo centrale e finali per una regolazione fine della curvatura.</li>
        <li><b>Impostazioni di curvatura avanzate:</b> Tre nuovi parametri - Influenza del punto di controllo, Amplificazione della distanza e Forma della curva per il controllo completo delle curve.</li>
        <li><b>Visualizzazione progressiva dei punti di controllo:</b> I punti di controllo appaiono progressivamente per ridurre il disordine visivo durante il posizionamento iniziale.</li>
        <li><b>Rendering delle ombreggiature migliorato:</b> Risolti vari problemi di ombreggiatura per una migliore qualità visiva.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.102</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Controles de sesgo de curvatura mejorados:</b> Nuevos puntos de control de sesgo entre los puntos de control central y finales para un ajuste fino de la curvatura.</li>
        <li><b>Configuración de curvatura avanzada:</b> Tres nuevos parámetros - Influencia del punto de control, Amplificación de distancia y Forma de curva para control completo de curvas.</li>
        <li><b>Visualización progresiva de puntos de control:</b> Los puntos de control aparecen progresivamente para reducir el desorden visual durante la colocación inicial.</li>
        <li><b>Renderizado de sombreado mejorado:</b> Se corrigieron varios problemas de sombreado para mejor calidad visual.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.102</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controles de viés de curvatura aprimorados:</b> Novos pontos de controle de viés entre os pontos de controle central e finais para ajuste fino de curvatura.</li>
        <li><b>Configurações de curvatura avançadas:</b> Três novos parâmetros - Influência do ponto de controle, Amplificação de distância e Forma da curva para controle completo das curvas.</li>
        <li><b>Exibição progressiva de pontos de controle:</b> Os pontos de controle aparecem progressivamente para reduzir a desordem visual durante o posicionamento inicial.</li>
        <li><b>Renderização de sombreamento aprimorada:</b> Vários problemas de sombreamento corrigidos para melhor qualidade visual.</li>
    </ul>
    <hr>
    <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.102</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05D1;&#x05E7;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D9;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D1;&#x05D9;&#x05DF; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D4;&#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9;&#x05EA; &#x05D5;&#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05D5;&#x05EA;:</b> &#x05E9;&#x05DC;&#x05D5;&#x05E9;&#x05D4; &#x05E4;&#x05E8;&#x05DE;&#x05D8;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; - &#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;, &#x05D4;&#x05D2;&#x05D1;&#x05E8;&#x05EA; &#x05DE;&#x05E8;&#x05D7;&#x05E7; &#x05D5;&#x05E6;&#x05D5;&#x05E8;&#x05EA; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D4; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05DE;&#x05DC;&#x05D0;&#x05D4; &#x05E2;&#x05DC; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D5;&#x05EA; &#x05D1;&#x05D4;&#x05D3;&#x05E8;&#x05D2;&#x05D4; &#x05DC;&#x05D4;&#x05E4;&#x05D7;&#x05EA;&#x05EA; &#x05E2;&#x05D5;&#x05DE;&#x05E1; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9; &#x05D1;&#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D9;.</li>
        <li><b>&#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05E9;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05DC;&#x05D0;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9;&#x05EA; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
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

# Create welcome.html  (welcome French + localized sections). Updated to 1.102 what's-new.
cat > "$RESOURCES_DIR/fr.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.102</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôles de biais de courbure améliorés :</b> Nouveaux points de contrôle de biais entre les points de contrôle central et d'extrémité pour un ajustement précis de la courbure.</li>
        <li><b>Paramètres de courbure avancés :</b> Trois nouveaux paramètres - Influence du point de contrôle, Amplification de distance et Forme de courbe pour un contrôle complet des courbes.</li>
        <li><b>Affichage progressif des points de contrôle :</b> Les points de contrôle apparaissent progressivement pour réduire l'encombrement visuel lors du placement initial.</li>
        <li><b>Rendu d'ombrage amélioré :</b> Correction de divers problèmes d'ombrage pour une meilleure qualité visuelle.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>Enhanced Curvature Bias Controls:</b> New bias control points between center and end control points for fine-tuned curvature adjustment.</li>
        <li><b>Advanced Curvature Settings:</b> Three new parameters - Control Point Influence, Distance Boost, and Curve Shape for complete curve control.</li>
        <li><b>Progressive Control Point Display:</b> Control points appear progressively to reduce visual clutter during initial strand placement.</li>
        <li><b>Improved Shading Rendering:</b> Fixed various shading issues for better visual quality.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Erweiterte Krümmungs-Bias-Steuerung:</b> Neue Bias-Kontrollpunkte zwischen mittlerem und End-Kontrollpunkten für präzise Krümmungsanpassung.</li>
        <li><b>Erweiterte Krümmungseinstellungen:</b> Drei neue Parameter - Kontrollpunkt-Einfluss, Distanz-Verstärkung und Kurvenform für vollständige Kurvenkontrolle.</li>
        <li><b>Progressive Kontrollpunkt-Anzeige:</b> Kontrollpunkte erscheinen progressiv, um visuelle Unordnung bei der anfänglichen Strangplatzierung zu reduzieren.</li>
        <li><b>Verbesserte Schattierungsdarstellung:</b> Verschiedene Schattierungsprobleme behoben für bessere visuelle Qualität.</li>
    </ul>
    <hr>

    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.102</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controlli di bias di curvatura avanzati:</b> Nuovi punti di controllo del bias tra i punti di controllo centrale e finali per una regolazione fine della curvatura.</li>
        <li><b>Impostazioni di curvatura avanzate:</b> Tre nuovi parametri - Influenza del punto di controllo, Amplificazione della distanza e Forma della curva per il controllo completo delle curve.</li>
        <li><b>Visualizzazione progressiva dei punti di controllo:</b> I punti di controllo appaiono progressivamente per ridurre il disordine visivo durante il posizionamento iniziale.</li>
        <li><b>Rendering delle ombreggiature migliorato:</b> Risolti vari problemi di ombreggiatura per una migliore qualità visiva.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.102</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Controles de sesgo de curvatura mejorados:</b> Nuevos puntos de control de sesgo entre los puntos de control central y finales para un ajuste fino de la curvatura.</li>
        <li><b>Configuración de curvatura avanzada:</b> Tres nuevos parámetros - Influencia del punto de control, Amplificación de distancia y Forma de curva para control completo de curvas.</li>
        <li><b>Visualización progresiva de puntos de control:</b> Los puntos de control aparecen progresivamente para reducir el desorden visual durante la colocación inicial.</li>
        <li><b>Renderizado de sombreado mejorado:</b> Se corrigieron varios problemas de sombreado para mejor calidad visual.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.102</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controles de viés de curvatura aprimorados:</b> Novos pontos de controle de viés entre os pontos de controle central e finais para ajuste fino de curvatura.</li>
        <li><b>Configurações de curvatura avançadas:</b> Três novos parâmetros - Influência do ponto de controle, Amplificação de distância e Forma da curva para controle completo das curvas.</li>
        <li><b>Exibição progressiva de pontos de controle:</b> Os pontos de controle aparecem progressivamente para reduzir a desordem visual durante o posicionamento inicial.</li>
        <li><b>Renderização de sombreamento aprimorada:</b> Vários problemas de sombreamento corrigidos para melhor qualidade visual.</li>
    </ul>
    <hr>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.102</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05D1;&#x05E7;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D9;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D1;&#x05D9;&#x05DF; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D4;&#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9;&#x05EA; &#x05D5;&#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05D5;&#x05EA;:</b> &#x05E9;&#x05DC;&#x05D5;&#x05E9;&#x05D4; &#x05E4;&#x05E8;&#x05DE;&#x05D8;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; - &#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;, &#x05D4;&#x05D2;&#x05D1;&#x05E8;&#x05EA; &#x05DE;&#x05E8;&#x05D7;&#x05E7; &#x05D5;&#x05E6;&#x05D5;&#x05E8;&#x05EA; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D4; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05DE;&#x05DC;&#x05D0;&#x05D4; &#x05E2;&#x05DC; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D5;&#x05EA; &#x05D1;&#x05D4;&#x05D3;&#x05E8;&#x05D2;&#x05D4; &#x05DC;&#x05D4;&#x05E4;&#x05D7;&#x05EA;&#x05EA; &#x05E2;&#x05D5;&#x05DE;&#x05E1; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9; &#x05D1;&#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D9;.</li>
        <li><b>&#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05E9;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05DC;&#x05D0;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9;&#x05EA; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome German + localized sections). Updated to 1.102 what's-new.

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
        <li><b>Erweiterte Krümmungs-Bias-Steuerung:</b> Neue Bias-Kontrollpunkte zwischen mittlerem und End-Kontrollpunkten für präzise Krümmungsanpassung.</li>
        <li><b>Erweiterte Krümmungseinstellungen:</b> Drei neue Parameter - Kontrollpunkt-Einfluss, Distanz-Verstärkung und Kurvenform für vollständige Kurvenkontrolle.</li>
        <li><b>Progressive Kontrollpunkt-Anzeige:</b> Kontrollpunkte erscheinen progressiv, um visuelle Unordnung bei der anfänglichen Strangplatzierung zu reduzieren.</li>
        <li><b>Verbesserte Schattierungsdarstellung:</b> Verschiedene Schattierungsprobleme behoben für bessere visuelle Qualität.</li>
    </ul>
    <hr>
    <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>Enhanced Curvature Bias Controls:</b> New bias control points between center and end control points for fine-tuned curvature adjustment.</li>
        <li><b>Advanced Curvature Settings:</b> Three new parameters - Control Point Influence, Distance Boost, and Curve Shape for complete curve control.</li>
        <li><b>Progressive Control Point Display:</b> Control points appear progressively to reduce visual clutter during initial strand placement.</li>
        <li><b>Improved Shading Rendering:</b> Fixed various shading issues for better visual quality.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.102</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôles de biais de courbure améliorés :</b> Nouveaux points de contrôle de biais entre les points de contrôle central et d'extrémité pour un ajustement précis de la courbure.</li>
        <li><b>Paramètres de courbure avancés :</b> Trois nouveaux paramètres - Influence du point de contrôle, Amplification de distance et Forme de courbe pour un contrôle complet des courbes.</li>
        <li><b>Affichage progressif des points de contrôle :</b> Les points de contrôle apparaissent progressivement pour réduire l'encombrement visuel lors du placement initial.</li>
        <li><b>Rendu d'ombrage amélioré :</b> Correction de divers problèmes d'ombrage pour une meilleure qualité visuelle.</li>
    </ul>
    <hr>    
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.102</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controlli di bias di curvatura avanzati:</b> Nuovi punti di controllo del bias tra i punti di controllo centrale e finali per una regolazione fine della curvatura.</li>
        <li><b>Impostazioni di curvatura avanzate:</b> Tre nuovi parametri - Influenza del punto di controllo, Amplificazione della distanza e Forma della curva per il controllo completo delle curve.</li>
        <li><b>Visualizzazione progressiva dei punti di controllo:</b> I punti di controllo appaiono progressivamente per ridurre il disordine visivo durante il posizionamento iniziale.</li>
        <li><b>Rendering delle ombreggiature migliorato:</b> Risolti vari problemi di ombreggiatura per una migliore qualità visiva.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.102</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Controles de sesgo de curvatura mejorados:</b> Nuevos puntos de control de sesgo entre los puntos de control central y finales para un ajuste fino de la curvatura.</li>
        <li><b>Configuración de curvatura avanzada:</b> Tres nuevos parámetros - Influencia del punto de control, Amplificación de distancia y Forma de curva para control completo de curvas.</li>
        <li><b>Visualización progresiva de puntos de control:</b> Los puntos de control aparecen progresivamente para reducir el desorden visual durante la colocación inicial.</li>
        <li><b>Renderizado de sombreado mejorado:</b> Se corrigieron varios problemas de sombreado para mejor calidad visual.</li>
    </ul>
    <hr>
    <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.102</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controles de viés de curvatura aprimorados:</b> Novos pontos de controle de viés entre os pontos de controle central e finais para ajuste fino de curvatura.</li>
        <li><b>Configurações de curvatura avançadas:</b> Três novos parâmetros - Influência do ponto de controle, Amplificação de distância e Forma da curva para controle completo das curvas.</li>
        <li><b>Exibição progressiva de pontos de controle:</b> Os pontos de controle aparecem progressivamente para reduzir a desordem visual durante o posicionamento inicial.</li>
        <li><b>Renderização de sombreamento aprimorada:</b> Vários problemas de sombreamento corrigidos para melhor qualidade visual.</li>
    </ul>
    <hr>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.102</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05D1;&#x05E7;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D9;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D1;&#x05D9;&#x05DF; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D4;&#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9;&#x05EA; &#x05D5;&#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05D5;&#x05EA;:</b> &#x05E9;&#x05DC;&#x05D5;&#x05E9;&#x05D4; &#x05E4;&#x05E8;&#x05DE;&#x05D8;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; - &#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;, &#x05D4;&#x05D2;&#x05D1;&#x05E8;&#x05EA; &#x05DE;&#x05E8;&#x05D7;&#x05E7; &#x05D5;&#x05E6;&#x05D5;&#x05E8;&#x05EA; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D4; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05DE;&#x05DC;&#x05D0;&#x05D4; &#x05E2;&#x05DC; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D5;&#x05EA; &#x05D1;&#x05D4;&#x05D3;&#x05E8;&#x05D2;&#x05D4; &#x05DC;&#x05D4;&#x05E4;&#x05D7;&#x05EA;&#x05EA; &#x05E2;&#x05D5;&#x05DE;&#x05E1; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9; &#x05D1;&#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D9;.</li>
        <li><b>&#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05E9;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05DC;&#x05D0;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9;&#x05EA; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF


# Create welcome.html  (welcome Italian + localized sections). Updated to 1.102 what's-new.
cat > "$RESOURCES_DIR/it.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.102</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controlli di bias di curvatura avanzati:</b> Nuovi punti di controllo del bias tra i punti di controllo centrale e finali per una regolazione fine della curvatura.</li>
        <li><b>Impostazioni di curvatura avanzate:</b> Tre nuovi parametri - Influenza del punto di controllo, Amplificazione della distanza e Forma della curva per il controllo completo delle curve.</li>
        <li><b>Visualizzazione progressiva dei punti di controllo:</b> I punti di controllo appaiono progressivamente per ridurre il disordine visivo durante il posizionamento iniziale.</li>
        <li><b>Rendering delle ombreggiature migliorato:</b> Risolti vari problemi di ombreggiatura per una migliore qualità visiva.</li>
    </ul>
    <hr>
        <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>Enhanced Curvature Bias Controls:</b> New bias control points between center and end control points for fine-tuned curvature adjustment.</li>
        <li><b>Advanced Curvature Settings:</b> Three new parameters - Control Point Influence, Distance Boost, and Curve Shape for complete curve control.</li>
        <li><b>Progressive Control Point Display:</b> Control points appear progressively to reduce visual clutter during initial strand placement.</li>
        <li><b>Improved Shading Rendering:</b> Fixed various shading issues for better visual quality.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.102</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôles de biais de courbure améliorés :</b> Nouveaux points de contrôle de biais entre les points de contrôle central et d'extrémité pour un ajustement précis de la courbure.</li>
        <li><b>Paramètres de courbure avancés :</b> Trois nouveaux paramètres - Influence du point de contrôle, Amplification de distance et Forme de courbe pour un contrôle complet des courbes.</li>
        <li><b>Affichage progressif des points de contrôle :</b> Les points de contrôle apparaissent progressivement pour réduire l'encombrement visuel lors du placement initial.</li>
        <li><b>Rendu d'ombrage amélioré :</b> Correction de divers problèmes d'ombrage pour une meilleure qualité visuelle.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Erweiterte Krümmungs-Bias-Steuerung:</b> Neue Bias-Kontrollpunkte zwischen mittlerem und End-Kontrollpunkten für präzise Krümmungsanpassung.</li>
        <li><b>Erweiterte Krümmungseinstellungen:</b> Drei neue Parameter - Kontrollpunkt-Einfluss, Distanz-Verstärkung und Kurvenform für vollständige Kurvenkontrolle.</li>
        <li><b>Progressive Kontrollpunkt-Anzeige:</b> Kontrollpunkte erscheinen progressiv, um visuelle Unordnung bei der anfänglichen Strangplatzierung zu reduzieren.</li>
        <li><b>Verbesserte Schattierungsdarstellung:</b> Verschiedene Schattierungsprobleme behoben für bessere visuelle Qualität.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.102</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Controles de sesgo de curvatura mejorados:</b> Nuevos puntos de control de sesgo entre los puntos de control central y finales para un ajuste fino de la curvatura.</li>
        <li><b>Configuración de curvatura avanzada:</b> Tres nuevos parámetros - Influencia del punto de control, Amplificación de distancia y Forma de curva para control completo de curvas.</li>
        <li><b>Visualización progresiva de puntos de control:</b> Los puntos de control aparecen progresivamente para reducir el desorden visual durante la colocación inicial.</li>
        <li><b>Renderizado de sombreado mejorado:</b> Se corrigieron varios problemas de sombreado para mejor calidad visual.</li>
    </ul>
    <hr>
        <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.102</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controles de viés de curvatura aprimorados:</b> Novos pontos de controle de viés entre os pontos de controle central e finais para ajuste fino de curvatura.</li>
        <li><b>Configurações de curvatura avançadas:</b> Três novos parâmetros - Influência do ponto de controle, Amplificação de distância e Forma da curva para controle completo das curvas.</li>
        <li><b>Exibição progressiva de pontos de controle:</b> Os pontos de controle aparecem progressivamente para reduzir a desordem visual durante o posicionamento inicial.</li>
        <li><b>Renderização de sombreamento aprimorada:</b> Vários problemas de sombreamento corrigidos para melhor qualidade visual.</li>
    </ul>
    <hr>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.102</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05D1;&#x05E7;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D9;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D1;&#x05D9;&#x05DF; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D4;&#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9;&#x05EA; &#x05D5;&#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05D5;&#x05EA;:</b> &#x05E9;&#x05DC;&#x05D5;&#x05E9;&#x05D4; &#x05E4;&#x05E8;&#x05DE;&#x05D8;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; - &#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;, &#x05D4;&#x05D2;&#x05D1;&#x05E8;&#x05EA; &#x05DE;&#x05E8;&#x05D7;&#x05E7; &#x05D5;&#x05E6;&#x05D5;&#x05E8;&#x05EA; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D4; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05DE;&#x05DC;&#x05D0;&#x05D4; &#x05E2;&#x05DC; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D5;&#x05EA; &#x05D1;&#x05D4;&#x05D3;&#x05E8;&#x05D2;&#x05D4; &#x05DC;&#x05D4;&#x05E4;&#x05D7;&#x05EA;&#x05EA; &#x05E2;&#x05D5;&#x05DE;&#x05E1; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9; &#x05D1;&#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D9;.</li>
        <li><b>&#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05E9;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05DC;&#x05D0;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9;&#x05EA; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF
# Create welcome.html  (welcome Spanish + localized sections). Updated to 1.102 what's-new.
cat > "$RESOURCES_DIR/es.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.102</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Controles de sesgo de curvatura mejorados:</b> Nuevos puntos de control de sesgo entre los puntos de control central y finales para un ajuste fino de la curvatura.</li>
        <li><b>Configuración de curvatura avanzada:</b> Tres nuevos parámetros - Influencia del punto de control, Amplificación de distancia y Forma de curva para control completo de curvas.</li>
        <li><b>Visualización progresiva de puntos de control:</b> Los puntos de control aparecen progresivamente para reducir el desorden visual durante la colocación inicial.</li>
        <li><b>Renderizado de sombreado mejorado:</b> Se corrigieron varios problemas de sombreado para mejor calidad visual.</li>
    </ul>
    <hr>
        <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>Enhanced Curvature Bias Controls:</b> New bias control points between center and end control points for fine-tuned curvature adjustment.</li>
        <li><b>Advanced Curvature Settings:</b> Three new parameters - Control Point Influence, Distance Boost, and Curve Shape for complete curve control.</li>
        <li><b>Progressive Control Point Display:</b> Control points appear progressively to reduce visual clutter during initial strand placement.</li>
        <li><b>Improved Shading Rendering:</b> Fixed various shading issues for better visual quality.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.102</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôles de biais de courbure améliorés :</b> Nouveaux points de contrôle de biais entre les points de contrôle central et d'extrémité pour un ajustement précis de la courbure.</li>
        <li><b>Paramètres de courbure avancés :</b> Trois nouveaux paramètres - Influence du point de contrôle, Amplification de distance et Forme de courbe pour un contrôle complet des courbes.</li>
        <li><b>Affichage progressif des points de contrôle :</b> Les points de contrôle apparaissent progressivement pour réduire l'encombrement visuel lors du placement initial.</li>
        <li><b>Rendu d'ombrage amélioré :</b> Correction de divers problèmes d'ombrage pour une meilleure qualité visuelle.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Erweiterte Krümmungs-Bias-Steuerung:</b> Neue Bias-Kontrollpunkte zwischen mittlerem und End-Kontrollpunkten für präzise Krümmungsanpassung.</li>
        <li><b>Erweiterte Krümmungseinstellungen:</b> Drei neue Parameter - Kontrollpunkt-Einfluss, Distanz-Verstärkung und Kurvenform für vollständige Kurvenkontrolle.</li>
        <li><b>Progressive Kontrollpunkt-Anzeige:</b> Kontrollpunkte erscheinen progressiv, um visuelle Unordnung bei der anfänglichen Strangplatzierung zu reduzieren.</li>
        <li><b>Verbesserte Schattierungsdarstellung:</b> Verschiedene Schattierungsprobleme behoben für bessere visuelle Qualität.</li>
    </ul>
    <hr>    
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.102</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controlli di bias di curvatura avanzati:</b> Nuovi punti di controllo del bias tra i punti di controllo centrale e finali per una regolazione fine della curvatura.</li>
        <li><b>Impostazioni di curvatura avanzate:</b> Tre nuovi parametri - Influenza del punto di controllo, Amplificazione della distanza e Forma della curva per il controllo completo delle curve.</li>
        <li><b>Visualizzazione progressiva dei punti di controllo:</b> I punti di controllo appaiono progressivamente per ridurre il disordine visivo durante il posizionamento iniziale.</li>
        <li><b>Rendering delle ombreggiature migliorato:</b> Risolti vari problemi di ombreggiatura per una migliore qualità visiva.</li>
    </ul>
    <hr>
        <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.102</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controles de viés de curvatura aprimorados:</b> Novos pontos de controle de viés entre os pontos de controle central e finais para ajuste fino de curvatura.</li>
        <li><b>Configurações de curvatura avançadas:</b> Três novos parâmetros - Influência do ponto de controle, Amplificação de distância e Forma da curva para controle completo das curvas.</li>
        <li><b>Exibição progressiva de pontos de controle:</b> Os pontos de controle aparecem progressivamente para reduzir a desordem visual durante o posicionamento inicial.</li>
        <li><b>Renderização de sombreamento aprimorada:</b> Vários problemas de sombreamento corrigidos para melhor qualidade visual.</li>
    </ul>
    <hr>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.102</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05D1;&#x05E7;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D9;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D1;&#x05D9;&#x05DF; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D4;&#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9;&#x05EA; &#x05D5;&#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05D5;&#x05EA;:</b> &#x05E9;&#x05DC;&#x05D5;&#x05E9;&#x05D4; &#x05E4;&#x05E8;&#x05DE;&#x05D8;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; - &#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;, &#x05D4;&#x05D2;&#x05D1;&#x05E8;&#x05EA; &#x05DE;&#x05E8;&#x05D7;&#x05E7; &#x05D5;&#x05E6;&#x05D5;&#x05E8;&#x05EA; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D4; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05DE;&#x05DC;&#x05D0;&#x05D4; &#x05E2;&#x05DC; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D5;&#x05EA; &#x05D1;&#x05D4;&#x05D3;&#x05E8;&#x05D2;&#x05D4; &#x05DC;&#x05D4;&#x05E4;&#x05D7;&#x05EA;&#x05EA; &#x05E2;&#x05D5;&#x05DE;&#x05E1; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9; &#x05D1;&#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D9;.</li>
        <li><b>&#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05E9;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05DC;&#x05D0;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9;&#x05EA; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF
# Create welcome.html  (welcome Portuguese + localized sections). Updated to 1.102 what's-new.

cat > "$RESOURCES_DIR/pt.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
        <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.102</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controles de viés de curvatura aprimorados:</b> Novos pontos de controle de viés entre os pontos de controle central e finais para ajuste fino de curvatura.</li>
        <li><b>Configurações de curvatura avançadas:</b> Três novos parâmetros - Influência do ponto de controle, Amplificação de distância e Forma da curva para controle completo das curvas.</li>
        <li><b>Exibição progressiva de pontos de controle:</b> Os pontos de controle aparecem progressivamente para reduzir a desordem visual durante o posicionamento inicial.</li>
        <li><b>Renderização de sombreamento aprimorada:</b> Vários problemas de sombreamento corrigidos para melhor qualidade visual.</li>
    </ul>
    <hr>
        <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>Enhanced Curvature Bias Controls:</b> New bias control points between center and end control points for fine-tuned curvature adjustment.</li>
        <li><b>Advanced Curvature Settings:</b> Three new parameters - Control Point Influence, Distance Boost, and Curve Shape for complete curve control.</li>
        <li><b>Progressive Control Point Display:</b> Control points appear progressively to reduce visual clutter during initial strand placement.</li>
        <li><b>Improved Shading Rendering:</b> Fixed various shading issues for better visual quality.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.102</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôles de biais de courbure améliorés :</b> Nouveaux points de contrôle de biais entre les points de contrôle central et d'extrémité pour un ajustement précis de la courbure.</li>
        <li><b>Paramètres de courbure avancés :</b> Trois nouveaux paramètres - Influence du point de contrôle, Amplification de distance et Forme de courbe pour un contrôle complet des courbes.</li>
        <li><b>Affichage progressif des points de contrôle :</b> Les points de contrôle apparaissent progressivement pour réduire l'encombrement visuel lors du placement initial.</li>
        <li><b>Rendu d'ombrage amélioré :</b> Correction de divers problèmes d'ombrage pour une meilleure qualité visuelle.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Erweiterte Krümmungs-Bias-Steuerung:</b> Neue Bias-Kontrollpunkte zwischen mittlerem und End-Kontrollpunkten für präzise Krümmungsanpassung.</li>
        <li><b>Erweiterte Krümmungseinstellungen:</b> Drei neue Parameter - Kontrollpunkt-Einfluss, Distanz-Verstärkung und Kurvenform für vollständige Kurvenkontrolle.</li>
        <li><b>Progressive Kontrollpunkt-Anzeige:</b> Kontrollpunkte erscheinen progressiv, um visuelle Unordnung bei der anfänglichen Strangplatzierung zu reduzieren.</li>
        <li><b>Verbesserte Schattierungsdarstellung:</b> Verschiedene Schattierungsprobleme behoben für bessere visuelle Qualität.</li>
    </ul>
    <hr>    
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.102</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controlli di bias di curvatura avanzati:</b> Nuovi punti di controllo del bias tra i punti di controllo centrale e finali per una regolazione fine della curvatura.</li>
        <li><b>Impostazioni di curvatura avanzate:</b> Tre nuovi parametri - Influenza del punto di controllo, Amplificazione della distanza e Forma della curva per il controllo completo delle curve.</li>
        <li><b>Visualizzazione progressiva dei punti di controllo:</b> I punti di controllo appaiono progressivamente per ridurre il disordine visivo durante il posizionamento iniziale.</li>
        <li><b>Rendering delle ombreggiature migliorato:</b> Risolti vari problemi di ombreggiatura per una migliore qualità visiva.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.102</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Controles de sesgo de curvatura mejorados:</b> Nuevos puntos de control de sesgo entre los puntos de control central y finales para un ajuste fino de la curvatura.</li>
        <li><b>Configuración de curvatura avanzada:</b> Tres nuevos parámetros - Influencia del punto de control, Amplificación de distancia y Forma de curva para control completo de curvas.</li>
        <li><b>Visualización progresiva de puntos de control:</b> Los puntos de control aparecen progresivamente para reducir el desorden visual durante la colocación inicial.</li>
        <li><b>Renderizado de sombreado mejorado:</b> Se corrigieron varios problemas de sombreado para mejor calidad visual.</li>
    </ul>
    <hr>
        <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.102</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controles de viés de curvatura aprimorados:</b> Novos pontos de controle de viés entre os pontos de controle central e finais para ajuste fino de curvatura.</li>
        <li><b>Configurações de curvatura avançadas:</b> Três novos parâmetros - Influência do ponto de controle, Amplificação de distância e Forma da curva para controle completo das curvas.</li>
        <li><b>Exibição progressiva de pontos de controle:</b> Os pontos de controle aparecem progressivamente para reduzir a desordem visual durante o posicionamento inicial.</li>
        <li><b>Renderização de sombreamento aprimorada:</b> Vários problemas de sombreamento corrigidos para melhor qualidade visual.</li>
    </ul>
    <hr>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.102</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05D1;&#x05E7;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D9;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D1;&#x05D9;&#x05DF; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D4;&#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9;&#x05EA; &#x05D5;&#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05D5;&#x05EA;:</b> &#x05E9;&#x05DC;&#x05D5;&#x05E9;&#x05D4; &#x05E4;&#x05E8;&#x05DE;&#x05D8;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; - &#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;, &#x05D4;&#x05D2;&#x05D1;&#x05E8;&#x05EA; &#x05DE;&#x05E8;&#x05D7;&#x05E7; &#x05D5;&#x05E6;&#x05D5;&#x05E8;&#x05EA; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D4; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05DE;&#x05DC;&#x05D0;&#x05D4; &#x05E2;&#x05DC; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D5;&#x05EA; &#x05D1;&#x05D4;&#x05D3;&#x05E8;&#x05D2;&#x05D4; &#x05DC;&#x05D4;&#x05E4;&#x05D7;&#x05EA;&#x05EA; &#x05E2;&#x05D5;&#x05DE;&#x05E1; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9; &#x05D1;&#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D9;.</li>
        <li><b>&#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05E9;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05DC;&#x05D0;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9;&#x05EA; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
</body>
</html>
EOF

# Create welcome.html  (welcome Hebrew + localized sections). Updated to 1.102 what's-new.
cat > "$RESOURCES_DIR/he.lproj/welcome.html" << 'EOF'
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
</head>
<body>
        <!-- Hebrew -->
    <div dir="rtl">
    <h2>&#x05D1;&#x05E8;&#x05D5;&#x05DB;&#x05D9;&#x05DD; &#x05D4;&#x05D1;&#x05D0;&#x05D9;&#x05DD; &#x05DC;-OpenStrandStudio 1.102</h2>
    <p>&#x05D0;&#x05E9;&#x05E3; &#x05D6;&#x05D4; &#x05D9;&#x05EA;&#x05E7;&#x05D9;&#x05DF; &#x05D0;&#x05EA; OpenStrandStudio &#x05D1;&#x05DE;&#x05D7;&#x05E9;&#x05D1; &#x05E9;&#x05DC;&#x05DA;.</p>
    <p>&#x05D7;&#x05D3;&#x05E9; &#x05D1;&#x05D2;&#x05E8;&#x05E1;&#x05D4; &#x05D6;&#x05D5;:</p>
    <ul>
        <li><b>&#x05D1;&#x05E7;&#x05E8;&#x05D5;&#x05EA; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D9;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D7;&#x05D3;&#x05E9;&#x05D5;&#x05EA; &#x05DC;&#x05D4;&#x05D8;&#x05D9;&#x05D4; &#x05D1;&#x05D9;&#x05DF; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D4;&#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05D4;&#x05DE;&#x05E8;&#x05DB;&#x05D6;&#x05D9;&#x05EA; &#x05D5;&#x05D4;&#x05E7;&#x05E6;&#x05D4; &#x05DC;&#x05DB;&#x05D5;&#x05D5;&#x05E0;&#x05D5;&#x05DF; &#x05DE;&#x05D3;&#x05D5;&#x05D9;&#x05E7; &#x05E9;&#x05DC; &#x05D4;&#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05D4;&#x05D2;&#x05D3;&#x05E8;&#x05D5;&#x05EA; &#x05E2;&#x05E7;&#x05DE;&#x05D5;&#x05DE;&#x05D9;&#x05D5;&#x05EA; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05D5;&#x05EA;:</b> &#x05E9;&#x05DC;&#x05D5;&#x05E9;&#x05D4; &#x05E4;&#x05E8;&#x05DE;&#x05D8;&#x05E8;&#x05D9;&#x05DD; &#x05D7;&#x05D3;&#x05E9;&#x05D9;&#x05DD; - &#x05D4;&#x05E9;&#x05E4;&#x05E2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4;, &#x05D4;&#x05D2;&#x05D1;&#x05E8;&#x05EA; &#x05DE;&#x05E8;&#x05D7;&#x05E7; &#x05D5;&#x05E6;&#x05D5;&#x05E8;&#x05EA; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D4; &#x05DC;&#x05E9;&#x05DC;&#x05D9;&#x05D8;&#x05D4; &#x05DE;&#x05DC;&#x05D0;&#x05D4; &#x05E2;&#x05DC; &#x05E2;&#x05E7;&#x05D5;&#x05DE;&#x05D5;&#x05EA;.</li>
        <li><b>&#x05EA;&#x05E6;&#x05D5;&#x05D2;&#x05EA; &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05EA;&#x05E7;&#x05D3;&#x05DE;&#x05EA;:</b> &#x05E0;&#x05E7;&#x05D5;&#x05D3;&#x05D5;&#x05EA; &#x05D1;&#x05E7;&#x05E8;&#x05D4; &#x05DE;&#x05D5;&#x05E4;&#x05D9;&#x05E2;&#x05D5;&#x05EA; &#x05D1;&#x05D4;&#x05D3;&#x05E8;&#x05D2;&#x05D4; &#x05DC;&#x05D4;&#x05E4;&#x05D7;&#x05EA;&#x05EA; &#x05E2;&#x05D5;&#x05DE;&#x05E1; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9; &#x05D1;&#x05DE;&#x05D9;&#x05E7;&#x05D5;&#x05DD; &#x05D4;&#x05E8;&#x05D0;&#x05E9;&#x05D5;&#x05E0;&#x05D9;.</li>
        <li><b>&#x05E2;&#x05D9;&#x05D1;&#x05D5;&#x05D3; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05DE;&#x05E9;&#x05D5;&#x05E4;&#x05E8;:</b> &#x05EA;&#x05D5;&#x05E7;&#x05E0;&#x05D5; &#x05D1;&#x05E2;&#x05D9;&#x05D5;&#x05EA; &#x05D4;&#x05E6;&#x05DC;&#x05DC;&#x05D4; &#x05E9;&#x05D5;&#x05E0;&#x05D5;&#x05EA; &#x05DC;&#x05D0;&#x05D9;&#x05DB;&#x05D5;&#x05EA; &#x05D5;&#x05D5;&#x05D9;&#x05D6;&#x05D5;&#x05D0;&#x05DC;&#x05D9;&#x05EA; &#x05D8;&#x05D5;&#x05D1;&#x05D4; &#x05D9;&#x05D5;&#x05EA;&#x05E8;.</li>
    </ul>
    </div>
    <hr>
        <!-- English -->
    <h2 dir="ltr">Welcome to OpenStrandStudio 1.102</h2>
    <p>This will install OpenStrandStudio on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>What's New in Version 1.102:</p>
    <ul>
        <li><b>Enhanced Curvature Bias Controls:</b> New bias control points between center and end control points for fine-tuned curvature adjustment.</li>
        <li><b>Advanced Curvature Settings:</b> Three new parameters - Control Point Influence, Distance Boost, and Curve Shape for complete curve control.</li>
        <li><b>Progressive Control Point Display:</b> Control points appear progressively to reduce visual clutter during initial strand placement.</li>
        <li><b>Improved Shading Rendering:</b> Fixed various shading issues for better visual quality.</li>
    </ul>
    <hr>
    <!-- French -->
    <h2 dir="ltr">Bienvenue dans OpenStrandStudio 1.102</h2>
    <p>Ceci va installer OpenStrandStudio sur votre ordinateur. Vous serez guidé à travers les étapes nécessaires.</p>
    <p>Nouveautés dans cette version&nbsp;:</p>
    <ul>
        <li><b>Contrôles de biais de courbure améliorés :</b> Nouveaux points de contrôle de biais entre les points de contrôle central et d'extrémité pour un ajustement précis de la courbure.</li>
        <li><b>Paramètres de courbure avancés :</b> Trois nouveaux paramètres - Influence du point de contrôle, Amplification de distance et Forme de courbe pour un contrôle complet des courbes.</li>
        <li><b>Affichage progressif des points de contrôle :</b> Les points de contrôle apparaissent progressivement pour réduire l'encombrement visuel lors du placement initial.</li>
        <li><b>Rendu d'ombrage amélioré :</b> Correction de divers problèmes d'ombrage pour une meilleure qualité visuelle.</li>
    </ul>
    <hr>
    <!-- German -->
    <h2 dir="ltr">Willkommen bei OpenStrandStudio 1.102</h2>
    <p>Dies installiert OpenStrandStudio auf Ihrem Computer. Sie werden durch die notwendigen Schritte geführt.</p>
    <p>Was ist neu in dieser Version:</p>
    <ul>
        <li><b>Erweiterte Krümmungs-Bias-Steuerung:</b> Neue Bias-Kontrollpunkte zwischen mittlerem und End-Kontrollpunkten für präzise Krümmungsanpassung.</li>
        <li><b>Erweiterte Krümmungseinstellungen:</b> Drei neue Parameter - Kontrollpunkt-Einfluss, Distanz-Verstärkung und Kurvenform für vollständige Kurvenkontrolle.</li>
        <li><b>Progressive Kontrollpunkt-Anzeige:</b> Kontrollpunkte erscheinen progressiv, um visuelle Unordnung bei der anfänglichen Strangplatzierung zu reduzieren.</li>
        <li><b>Verbesserte Schattierungsdarstellung:</b> Verschiedene Schattierungsprobleme behoben für bessere visuelle Qualität.</li>
    </ul>
    <hr>    
    <!-- Italian -->
    <h2 dir="ltr">Benvenuto in OpenStrandStudio 1.102</h2>
    <p>Questa procedura installerà OpenStrandStudio sul tuo computer.</p>
    <p>Novità in questa versione:</p>
    <ul>
        <li><b>Controlli di bias di curvatura avanzati:</b> Nuovi punti di controllo del bias tra i punti di controllo centrale e finali per una regolazione fine della curvatura.</li>
        <li><b>Impostazioni di curvatura avanzate:</b> Tre nuovi parametri - Influenza del punto di controllo, Amplificazione della distanza e Forma della curva per il controllo completo delle curve.</li>
        <li><b>Visualizzazione progressiva dei punti di controllo:</b> I punti di controllo appaiono progressivamente per ridurre il disordine visivo durante il posizionamento iniziale.</li>
        <li><b>Rendering delle ombreggiature migliorato:</b> Risolti vari problemi di ombreggiatura per una migliore qualità visiva.</li>
    </ul>
    <hr>
    <!-- Spanish -->
    <h2 dir="ltr">Bienvenido a OpenStrandStudio 1.102</h2>
    <p>Este asistente instalará OpenStrandStudio en su equipo.</p>
    <p>Novedades en esta versión:</p>
    <ul>
        <li><b>Controles de sesgo de curvatura mejorados:</b> Nuevos puntos de control de sesgo entre los puntos de control central y finales para un ajuste fino de la curvatura.</li>
        <li><b>Configuración de curvatura avanzada:</b> Tres nuevos parámetros - Influencia del punto de control, Amplificación de distancia y Forma de curva para control completo de curvas.</li>
        <li><b>Visualización progresiva de puntos de control:</b> Los puntos de control aparecen progresivamente para reducir el desorden visual durante la colocación inicial.</li>
        <li><b>Renderizado de sombreado mejorado:</b> Se corrigieron varios problemas de sombreado para mejor calidad visual.</li>
    </ul>
    <hr>
        <!-- Portuguese -->
    <h2 dir="ltr">Bem-vindo ao OpenStrandStudio 1.102</h2>
    <p>Este assistente instalará o OpenStrandStudio no seu computador.</p>
    <p>Novidades nesta versão:</p>
    <ul>
        <li><b>Controles de viés de curvatura aprimorados:</b> Novos pontos de controle de viés entre os pontos de controle central e finais para ajuste fino de curvatura.</li>
        <li><b>Configurações de curvatura avançadas:</b> Três novos parâmetros - Influência do ponto de controle, Amplificação de distância e Forma da curva para controle completo das curvas.</li>
        <li><b>Exibição progressiva de pontos de controle:</b> Os pontos de controle aparecem progressivamente para reduzir a desordem visual durante o posicionamento inicial.</li>
        <li><b>Renderização de sombreamento aprimorada:</b> Vários problemas de sombreamento corrigidos para melhor qualidade visual.</li>
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
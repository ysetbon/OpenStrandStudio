#!/bin/bash

# Set variables
APP_NAME="OpenStrand Studio"
VERSION="1.071"
APP_DATE="27_Oct_2024"
PUBLISHER="Yonatan Setbon"
IDENTIFIER="com.yonatansetbon.openstrandstudio"

# Create directories
WORKING_DIR="$(mktemp -d)"
SCRIPTS_DIR="$WORKING_DIR/scripts"
RESOURCES_DIR="$WORKING_DIR/resources"
PKG_PATH="/Users/yonatansetbon/Documents/GitHub/OpenStrandStudio/src/installer_output/${APP_NAME}_${VERSION}.pkg"

mkdir -p "$SCRIPTS_DIR" "$RESOURCES_DIR"

# Create postinstall script
cat > "$SCRIPTS_DIR/postinstall" << 'EOF'
#!/bin/bash

# Get the user's home directory
USER_HOME=$HOME

# Create Desktop icon
cp -f "/Applications/OpenStrand Studio.app/Contents/Resources/box_stitch.icns" "$USER_HOME/Desktop/OpenStrand Studio.icns"

# Create Launch Agent for auto-start (optional)
LAUNCH_AGENT_DIR="$USER_HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENT_DIR"

# Ask if user wants to launch the app now
osascript <<EOD
    tell application "System Events"
        activate
        set launch_now to button returned of (display dialog "Installation Complete! Would you like to launch OpenStrand Studio now?" buttons {"Launch Now", "Later"} default button "Launch Now")
        if launch_now is "Launch Now" then
            tell application "OpenStrand Studio" to activate
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
            <line choice="com.yonatansetbon.openstrandstudio"/>
        </line>
    </choices-outline>
    <choice id="default"/>
    <choice id="com.yonatansetbon.openstrandstudio" visible="false">
        <pkg-ref id="com.yonatansetbon.openstrandstudio"/>
    </choice>
    <pkg-ref id="com.yonatansetbon.openstrandstudio" version="$VERSION" onConclusion="none">OpenStrandStudio.pkg</pkg-ref>
</installer-gui-script>
EOF

# Create welcome.html
cat > "$RESOURCES_DIR/welcome.html" << EOF
<!DOCTYPE html>
<html>
<body>
    <h2>Welcome to $APP_NAME $VERSION</h2>
    <p>This will install $APP_NAME on your computer. You will be guided through the steps necessary to install this software.</p>
    <p>New features in this version:</p>
    <ul>
        <li>Enhanced mask creation with visual feedback</li>
        <li>New mask editing features</li>
        <li>Improved attached strand visualization</li>
        <li>Optimized for macOS</li>
    </ul>
</body>
</html>
EOF

# Create license.html
cat > "$RESOURCES_DIR/license.html" << EOF
<!DOCTYPE html>
<html>
<body>
    <h2>License Agreement</h2>
    <p>Copyright (c) 2024 $PUBLISHER</p>
    <p>By installing this software, you agree to the terms and conditions.</p>
</body>
</html>
EOF

# Create component package
pkgbuild \
    --root "/Users/yonatansetbon/Documents/GitHub/OpenStrandStudio/src/dist/OpenStrand Studio.app" \
    --install-location "/Applications/OpenStrand Studio.app" \
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
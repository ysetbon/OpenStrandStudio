; OpenStrand Studio1_071_mac.iss - macOS Specific Installer

#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.071"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrand Studio.app"
#define MyAppDate "27_Oct_2024"
#define SourcePath "dist"
#define ExePath "dist"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact=ysetbon@gmail.com
AppComments=The program is brought to you by Yonatan Setbon, you can contact me at ysetbon@gmail.com
DefaultDirName=/Applications/{#MyAppName}  ; Changed to macOS standard path
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=OpenStrandStudio_Mac_{#MyAppDate}_1_071
Compression=lzma
SolidCompression=yes
SetupIconFile=box_stitch.icns
UninstallDisplayIcon={app}\box_stitch.icns
UninstallDisplayName={#MyAppName}
AppId={{YOUR-UNIQUE-APP-ID-HERE}}
VersionInfoVersion={#MyAppVersion}

; macOS specific settings
MacOSXArchitectures=x64 arm64  ; Support both Intel and Apple Silicon
DisableProgramGroupPage=yes    ; No start menu on macOS
DisableWelcomePage=no
DisableDirPage=no
AlwaysShowDirOnReadyPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
; Main application bundle
Source: "{#ExePath}\{#MyAppExeName}/*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "box_stitch.icns"; DestDir: "{app}"; Flags: ignoreversion
Source: "settings_icon.png"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}/Contents"
Name: "{app}/Contents/MacOS"
Name: "{app}/Contents/Resources"

[Run]
; macOS specific post-install commands
Filename: "/usr/bin/xattr"; Parameters: "-cr ""{app}"""; Flags: runhidden
Filename: "/bin/chmod"; Parameters: "+x ""{app}/Contents/MacOS/*"""; Flags: runhidden

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Verify macOS environment
  if not IsMacOS then
  begin
    MsgBox('This installer is specifically designed for macOS.' + #13#10 +
           'Please use the Windows version for Windows installation.',
           mbInformation, MB_OK);
    Result := False;
  end;
end;

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] on your Mac.%n%nNew in this version:%n- Enhanced mask creation with visual feedback: first strand selection is now highlighted in red for better clarity%n- New mask editing features: right-click on masked layers to edit or reset the mask intersection%n- Improved attached strand visualization with properly masked half-circles%n- Optimized for macOS with native look and feel%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre Mac.%n%nNouveautés dans cette version :%n- Amélioration de la création de masques avec retour visuel : la sélection du premier brin est maintenant mise en évidence en rouge pour plus de clarté%n- Nouvelles fonctionnalités d'édition de masques : clic droit sur les calques masqués pour éditer ou réinitialiser l'intersection%n- Amélioration de la visualisation des brins attachés avec des demi-cercles correctement masqués%n- Optimisé pour macOS avec une interface native%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.

english.LaunchAfterInstall=Open OpenStrand Studio
french.LaunchAfterInstall=Ouvrir OpenStrand Studio

[Messages]
english.FinishedLabel=Setup has finished installing [name] on your Mac. The application has been installed in the Applications folder.
french.FinishedLabel=L'installation de [name] sur votre Mac est terminée. L'application a été installée dans le dossier Applications. 
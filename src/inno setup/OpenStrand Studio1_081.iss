#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.081"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "28_Jan_2025"
#define SourcePath "E:\githubFiles\OpenStrandStudio-main\OpenStrandStudio-main"
#define ExePath "E:\githubFiles\OpenStrandStudio-main\OpenStrandStudio-main\src\dist"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact=ysetbon@gmail.com
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=E:\githubFiles\OpenStrandStudio-main\OpenStrandStudio-main\installer_output
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_081
Compression=lzma2/ultra64
InternalCompressLevel=max
CompressionThreads=auto
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4
LZMABlockSize=65536
SolidCompression=yes
DiskSpanning=no
MinVersion=6.1sp1
PrivilegesRequired=admin
UninstallDisplayIcon={app}\box_stitch.ico
SetupIconFile={#SourcePath}\box_stitch.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "{#ExePath}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion solidbreak
Source: "{#SourcePath}\box_stitch.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\settings_icon.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; MinVersion: 0,1
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; Tasks: desktopicon; MinVersion: 0,1

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchAfterInstall}"; Flags: nowait postinstall skipifsilent

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nNew in this version:%n- Move and attach mode is now more clear and user-friendly%n- Fixed attachment issues after creating groups and using the angle strand dialog%n- Improved colors and style of buttons in the main window%n- Enhanced layer loading from JSON saves to maintain correct order%n- Improved mask editing and rotation with groups%n- circle transparent stroke when rightclick%n- better font in setting dialog%n- when deleting a strand the semi transparent circles for starting and ending points for the strand is now being updated%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation
french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés dans cette version :%n- Le mode déplacement et attachement est maintenant plus clair et convivial%n- Correction des problèmes d'attachement après la création de groupes et l'utilisation du dialogue d'angle des brins%n- Amélioration des couleurs et du style des boutons dans la fenêtre principale%n- Chargement amélioré des calques depuis les sauvegardes JSON pour maintenir l'ordre correct%n- Amélioration de l'édition et de la rotation des masques avec les groupes%n- Le trait de cercle transparent lors du clic droit%n- Meilleure police dans la boîte de dialogue des paramètres%n- Lors de la suppression d'un brin, les cercles semi-transparents pour les points de départ et d'arrivée sont maintenant mis à jour%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l''installation
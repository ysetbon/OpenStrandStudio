; OpenStrand Studio1_072.iss

#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.072"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe" ; Updated to match PyInstaller's output if different
#define MyAppDate "5_Nov_2024"
#define SourcePath "C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src"
#define ExePath "C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\dist"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact=ysetbon@gmail.com
AppComments=The program is brought to you by Yonatan Setbon, you can contact me at ysetbon@gmail.com
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\installer_output
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_072
Compression=lzma
SolidCompression=yes
SetupIconFile={#SourcePath}\box_stitch.ico
UninstallDisplayIcon={app}\box_stitch.ico
UninstallDisplayName={#MyAppName}
AppId={{YOUR-UNIQUE-APP-ID-HERE}}
VersionInfoVersion={#MyAppVersion}
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "{#ExePath}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ExePath}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourcePath}\box_stitch.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\settings_icon.png"; DestDir: "{app}"; Flags: ignoreversion
; No need to include default settings file or settings directory

; [Dirs] Section is no longer needed and can be removed
; [Dirs]
; Name: "{commonappdata}\{#MyAppName}"; Permissions: users-full

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\box_stitch.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\box_stitch.ico"; Tasks: desktopicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; IconFilename: "{app}\box_stitch.ico"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent


[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nNew in this version:%n- Improved group management: groups now correctly update when new strands are attached, ensuring proper movement, rotation, and angle adjustments%n- Enhanced mask editing: edited masks now properly update their position when moving associated strands%n- Improved attached strand visualization with properly masked half-circles%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés dans cette version :%n- Amélioration de la gestion des groupes : les groupes se mettent à jour correctement lors de l'attachement de nouveaux brins, assurant des mouvements, rotations et ajustements d'angles appropriés%n- Amélioration de l'édition des masques : les masques édités mettent à jour correctement leur position lors du déplacement des brins associés%n- Amélioration de la visualisation des brins attachés avec des demi-cercles correctement masqués%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.

english.LaunchAfterInstall=Launch {#MyAppName} after installation
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

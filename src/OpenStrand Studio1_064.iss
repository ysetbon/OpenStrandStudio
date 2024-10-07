; OpenStrand Studio1_064.iss

#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.064"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe" ; Updated to match PyInstaller's output if different
#define MyAppDate "07_Oct_2024"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_064
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nNew in this version:%n- Added a refresh button for the layer panel to align the layers to the bottom.%n- When attaching a new strand related to an attached strand from a group, the group gets automatically deleted to prevent issues.%n- Saving will no longer save the group since it caused issues.%n- When setting a new theme, group colors now appear correctly.%n- When loading a JSON file, the order of importing layers is now correct, including masked layers.%n- Included video tutorials for better user guidance.%n- Added "About Open Strand" in the settings for more information about the application.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés dans cette version :%n- Ajout d'un bouton de rafraîchissement pour le panneau des couches afin d'aligner les couches en bas.%n- Lors de l'attachement d'un nouveau brin lié à un brin attaché d'un groupe, le groupe est automatiquement supprimé pour éviter des problèmes.%n- La sauvegarde ne sauvegardera plus le groupe car cela causait des problèmes.%n- Lors du changement de thème, les couleurs des groupes apparaissent maintenant correctement.%n- Lors du chargement d'un fichier JSON, l'ordre d'importation des couches est désormais correct, y compris pour les couches masquées.%n- Ajout de tutoriels vidéo pour une meilleure orientation des utilisateurs.%n- Ajout de "À propos d'Open Strand" dans les paramètres pour plus d'informations sur l'application.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.

english.LaunchAfterInstall=Launch {#MyAppName} after installation
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation
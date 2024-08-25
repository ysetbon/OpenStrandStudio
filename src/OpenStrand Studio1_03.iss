#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.03"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "8_25_2024"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact=ysetbon@gmail.com
AppComments=The program is brought to you by Yonatan Setbon, you can contact me at ysetbon@gmail.com
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\installer_output
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}
Compression=lzma
SolidCompression=yes
SetupIconFile=C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\box_stitch.ico
UninstallDisplayIcon={app}\box_stitch.ico
UninstallDisplayName={#MyAppName}
AppId={{YOUR-UNIQUE-APP-ID-HERE}}
VersionInfoVersion={#MyAppVersion}
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\dist\OpenStrandStudio\OpenStrandStudio.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\dist\OpenStrandStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\box_stitch.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; Tasks: desktopicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; IconFilename: "{app}\box_stitch.ico"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  // You can add update checking logic here
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nNew in this version:%n- Added a "Save Image" button%n- Added a "Mask Mode" button%n- Added a "Select Strand" button%n- After adjusting the angle of a strand, it is now deselected once updated%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.

[CustomMessages]
LaunchAfterInstall=Launch {#MyAppName} after installation
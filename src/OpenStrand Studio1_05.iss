#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.05"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "12_Sept_2024"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}
Compression=lzma
SolidCompression=yes
SetupIconFile={#SourcePath}\box_stitch.ico
UninstallDisplayIcon={app}\box_stitch.ico
UninstallDisplayName={#MyAppName}
AppId={{YOUR-UNIQUE-APP-ID-HERE}}
VersionInfoVersion={#MyAppVersion}
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Files]
Source: "{#ExePath}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ExePath}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourcePath}\box_stitch.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; Tasks: desktopicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; IconFilename: "{app}\box_stitch.ico"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  // You can add update checking logic here
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nNew in this version:%n- Added a better implementation for masking, now the circle of the attached strand is also considered.%n- Improved button style at the top of the canvas.%n- Angle adjust mode improved: disables strands that cannot have new strands attached, simplifying the process.%n- Better overall functionality for angle adjust, improving user experience and precision.%n- Enhanced typography for canvas overlay buttons.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.

[CustomMessages]
LaunchAfterInstall=Launch {#MyAppName} after installation
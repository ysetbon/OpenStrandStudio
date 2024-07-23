#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.0"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "main.exe"
#define MyAppDate "7_23_2024"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact=ysetbon@gmail.com
AppComments=The program is brought to you by Yonatan Setbon, you can contact me at ysetbon@gmail.com
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=C:\Users\YonatanSetbon\.vscode\lanyard_program_beta\installer_output
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}
Compression=lzma
SolidCompression=yes
SetupIconFile=C:\Users\YonatanSetbon\.vscode\lanyard_program_beta\box_stitch.ico

[Files]
Source: "C:\Users\YonatanSetbon\.vscode\lanyard_program_beta\dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\YonatanSetbon\.vscode\lanyard_program_beta\box_stitch.ico"; DestDir: "{app}"; Flags: ignoreversion
; Add any additional files your program needs here, such as:
; Source: "C:\Users\YonatanSetbon\.vscode\lanyard_program_beta\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  // You can add update checking logic here
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
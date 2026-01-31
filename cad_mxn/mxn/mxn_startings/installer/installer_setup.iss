; Inno Setup Script for MxN CAD Generator
; This script creates a Windows installer for the application

#define MyAppName "MxN CAD Generator"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "OpenStrandStudio"
#define MyAppURL "https://github.com/OpenStrandStudio"
#define MyAppExeName "MxN_CAD_Generator.exe"

[Setup]
; Application identity
AppId={{E8F7A6B5-4C3D-2E1F-0A9B-8C7D6E5F4A3B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output settings
OutputDir=output
OutputBaseFilename=MxN_CAD_Generator_Setup_{#MyAppVersion}
SetupIconFile=..\..\..\..\box_stitch.ico

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Visual settings
WizardStyle=modern
WizardSizePercent=100

; Uninstall settings
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable - built by PyInstaller
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Copy the icon file
Source: "..\..\..\..\box_stitch.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; Tasks: desktopicon

; Uninstall shortcut
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Option to run after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Custom code for installation checks
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Post-installation tasks can be added here
  end;
end;

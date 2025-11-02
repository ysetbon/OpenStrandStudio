#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.104"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "02_Nov_2025"
#define SourcePath "C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src"
#define ExePath "C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\dist"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact=ysetbon@gmail.com
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\dist
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_104
Compression=lzma2/ultra64
InternalCompressLevel=max
CompressionThreads=auto
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4
LZMABlockSize=65536
SolidCompression=yes
DiskSpanning=no
MinVersion=6.1sp1
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\box_stitch.ico
SetupIconFile={#SourcePath}\box_stitch.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"

[Files]
Source: "{#ExePath}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion solidbreak
Source: "{#SourcePath}\box_stitch.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\settings_icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\flags\*.png"; DestDir: "{app}\flags"; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\mp4\*.mp4"; DestDir: "{app}\mp4"; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\samples\*.json"; DestDir: "{app}\samples"; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\images\*.svg"; DestDir: "{app}\images"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; MinVersion: 0,1
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; Tasks: desktopicon; MinVersion: 0,1
Name: "{userprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"
Name: "{userprograms}\{#MyAppName}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Registry]
Root: HKCR; Subkey: ".oss"; ValueType: string; ValueData: "OpenStrandStudioFile"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "OpenStrandStudioFile"; ValueType: string; ValueData: "OpenStrand Studio Project"; Flags: uninsdeletekey
Root: HKCR; Subkey: "OpenStrandStudioFile\DefaultIcon"; ValueType: string; ValueData: "{app}\box_stitch.ico"
Root: HKCR; Subkey: "OpenStrandStudioFile\shell\open\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\OpenStrandStudio"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchAfterInstall}"; Flags: nowait postinstall skipifsilent

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.104:%n%n• [TODO: Update with version 1.104 features]%n• Enhanced attached strand functionality with improved controls%n• Additional UI improvements and bug fixes%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.104:%n%n• [TODO: Mettre à jour avec les fonctionnalités de la version 1.104]%n• Fonctionnalité de brin attaché améliorée avec des contrôles améliorés%n• Améliorations de l'interface utilisateur et corrections de bugs supplémentaires%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.104:%n%n• [TODO: Mit den Funktionen von Version 1.104 aktualisieren]%n• Verbesserte angehängte Strang-Funktionalität mit verbesserten Steuerungen%n• Zusätzliche UI-Verbesserungen und Fehlerbehebungen%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.104:%n%n• [TODO: Aggiornare con le funzionalità della versione 1.104]%n• Funzionalità del filamento attaccato migliorata con controlli migliorati%n• Ulteriori miglioramenti dell'interfaccia utente e correzioni di bug%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.104:%n%n• [TODO: Actualizar con las características de la versión 1.104]%n• Funcionalidad de hilo adjunto mejorada con controles mejorados%n• Mejoras adicionales de la interfaz de usuario y correcciones de errores%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.104:%n%n• [TODO: Atualizar com os recursos da versão 1.104]%n• Funcionalidade de fio anexado aprimorada com controles aprimorados%n• Melhorias adicionais da interface do usuário e correções de bugs%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.104:%n%n• [TODO: עדכן עם תכונות גרסה 1.104]%n• פונקציונליות גדיל מחובר משופרת עם בקרות משופרות%n• שיפורי ממשק משתמש ותיקוני באגים נוספים%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

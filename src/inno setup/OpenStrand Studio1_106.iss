#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.106"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "04_Jan_2026"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_106
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
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; Tasks: desktopicon
Name: "{userprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"
Name: "{userprograms}\{#MyAppName}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Registry]
Root: HKCU; Subkey: "Software\Classes\.oss"; ValueType: string; ValueData: "OpenStrandStudioFile"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\OpenStrandStudioFile"; ValueType: string; ValueData: "OpenStrand Studio Project"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\OpenStrandStudioFile\DefaultIcon"; ValueType: string; ValueData: "{app}\box_stitch.ico"
Root: HKCU; Subkey: "Software\Classes\OpenStrandStudioFile\shell\open\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\OpenStrandStudio"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchAfterInstall}"; Flags: nowait postinstall skipifsilent

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.106:%n%n• Hover Highlight in Select and Mask Modes: Strands now highlight when hovering over them in Select mode and Mask mode, providing better visual feedback for strand selection.%n• Main Buttons Responsiveness: Fixed main window buttons (at the top of the canvas) to display correctly on any screen size and aspect ratio.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.106:%n%n• Surbrillance au survol dans les modes Sélection et Masque: Les brins sont maintenant mis en surbrillance lorsque vous passez la souris dessus en mode Sélection et en mode Masque, offrant un meilleur retour visuel pour la sélection des brins.%n• Réactivité des boutons principaux: Correction des boutons de la fenêtre principale (en haut du canevas) pour qu'ils s'affichent correctement sur toute taille d'écran et tout rapport d'aspect.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.106:%n%n• Hervorhebung beim Überfahren in Auswahl- und Maskenmodi: Stränge werden jetzt hervorgehoben, wenn Sie mit der Maus darüber fahren, im Auswahlmodus und im Maskenmodus, für besseres visuelles Feedback bei der Strangauswahl.%n• Reaktionsfähigkeit der Hauptschaltflächen: Die Schaltflächen im Hauptfenster (oben auf der Leinwand) werden jetzt auf jeder Bildschirmgröße und jedem Seitenverhältnis korrekt angezeigt.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.106:%n%n• Evidenziazione al passaggio del mouse nei modi Selezione e Maschera: I trefoli ora si evidenziano quando si passa il mouse sopra di essi in modalità Selezione e in modalità Maschera, fornendo un miglior feedback visivo per la selezione dei trefoli.%n• Reattività dei pulsanti principali: Corretti i pulsanti della finestra principale (in alto sulla tela) per visualizzarsi correttamente su qualsiasi dimensione dello schermo e rapporto d'aspetto.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.106:%n%n• Resaltado al pasar el cursor en modos Selección y Máscara: Las hebras ahora se resaltan al pasar el cursor sobre ellas en modo Selección y en modo Máscara, proporcionando mejor retroalimentación visual para la selección de hebras.%n• Reactividad de los botones principales: Corregidos los botones de la ventana principal (en la parte superior del lienzo) para que se muestren correctamente en cualquier tamaño de pantalla y relación de aspecto.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.106:%n%n• Destaque ao passar o cursor nos modos Seleção e Máscara: As mechas agora são destacadas ao passar o cursor sobre elas no modo Seleção e no modo Máscara, fornecendo melhor feedback visual para a seleção de mechas.%n• Responsividade dos botões principais: Corrigidos os botões da janela principal (no topo da tela) para serem exibidos corretamente em qualquer tamanho de tela e proporção de aspecto.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.106:%n%n• הדגשה בריחוף במצבי בחירה ומסכה: חוטים מודגשים כעת בריחוף מעליהם במצב בחירה ובמצב מסכה, מספקים משוב חזותי טוב יותר לבחירת חוטים.%n• תגובתיות כפתורים ראשיים: תוקנו כפתורי החלון הראשי (בחלק העליון של הקנבס) להצגה נכונה בכל גודל מסך ויחס גובה-רוחב.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

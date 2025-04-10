#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.091"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "10_Apr_2025"
#define SourcePath "C:\Users\YonatanSetbon\.vscode\OpenStrandStudio"
#define ExePath "C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\dist"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact=ysetbon@gmail.com
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\dist
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_091
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
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"

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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nNew in this version:%n- Undo/Redo functionality%n- History tab in settings to view past actions%n- Bug Fixes: Improved drawing in move mode and corrected main strand drawing when connecting attached strands to start points. Added support for more languages: Italian, Spanish, Portuguese, and Hebrew.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation
french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés dans cette version :%n- Fonctionnalité Annuler/Rétablir%n- Onglet Historique dans les paramètres pour voir les actions passées%n- Corrections de bugs : Amélioration du dessin en mode déplacement et correction du dessin du brin principal lors de la connexion de brins attachés aux points de départ. Ajout de la prise en charge de plusieurs langues supplémentaires : Italien, Espagnol, Portugais et Hébreu.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation 

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità in questa versione:%n- Funzionalità Annulla/Ripristina%n- Scheda Cronologia nelle impostazioni per visualizzare le azioni passate%n- Correzioni di bug: Migliorato il disegno in modalità spostamento e corretto il disegno del filo principale durante la connessione dei fili collegati ai punti di partenza. Aggiunto supporto per più lingue: Italiano, Spagnolo, Portoghese ed Ebraico.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades en esta versión:%n- Funcionalidad Deshacer/Rehacer%n- Pestaña Historial en la configuración para ver acciones pasadas%n- Correcciones de errores: Dibujo mejorado en modo mover y dibujo corregido del hilo principal al conectar hilos adjuntos a los puntos de inicio. Se agregó soporte para más idiomas: Italiano, Español, Portugués y Hebreo.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades nesta versão:%n- Funcionalidade Desfazer/Refazer%n- Aba Histórico nas configurações para visualizar ações passadas%n- Correções de bugs: Desenho aprimorado no modo mover e desenho corrigido do fio principal ao conectar fios anexados aos pontos de partida. Adicionado suporte para mais idiomas: Italiano, Espanhol, Português e Hebraico.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nחדש בגרסה זו:%n- פונקציונליות בטל/בצע מחדש%n- לשונית היסטוריה בהגדרות לצפייה בפעולות קודמות%n- תיקוני באגים: שיפור הציור במצב הזזה ותיקון ציור החוט הראשי בעת חיבור חוטים מצורפים לנקודות ההתחלה. נוספה תמיכה בשפות נוספות: איטלקית, ספרדית, פורטוגזית ועברית.%n%nהתוכנית מובאת אליכם על ידי יונתן סתבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.092"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "3_May_2025"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_092
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nNew in this version:%n- Persistent Undo/Redo history saved with your project.%n- Customizable dashed lines and arrowheads for strands.%n- Improved control point visuals with larger handles.%n- Mask extension options for finer control.%n- Enhanced shading algorithm with smoother shadows.%n- Upgraded layer panel with drag-and-drop reordering and quick visibility toggles.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation
french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés dans cette version :%n- Historique Annuler/Rétablir persistant enregistré dans votre projet.%n- Lignes et flèches en pointillés personnalisables pour les brins.%n- Points de contrôle plus grands et plus visibles.%n- Options d'extension des masques pour un meilleur contrôle.%n- Algorithme d'ombrage amélioré pour des ombres plus douces.%n- Panneau des calques amélioré avec réorganisation par glisser-déposer et bascule rapide de visibilité.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità in questa versione:%n- Cronologia Annulla/Ripristina persistente salvata con il progetto.%n- Linee tratteggiate e frecce personalizzabili per i fili.%n- Punti di controllo più grandi e visibili.%n- Opzioni di estensione delle maschere per maggior controllo.%n- Algoritmo di ombreggiatura migliorato con ombre più naturali.%n- Pannello livelli potenziato con riordino drag-and-drop e visibilità rapida.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades en esta versión:%n- Historial de Deshacer/Rehacer persistente guardado con el proyecto.%n- Líneas y flechas discontinuas personalizables para los hilos.%n- Puntos de control más grandes y visibles.%n- Opciones de extensión de máscaras para mayor control.%n- Algoritmo de sombreado mejorado con sombras más suaves.%n- Panel de capas mejorado con reordenamiento mediante arrastrar y soltar y visibilidad rápida.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades nesta versão:%n- Histórico de Desfazer/Refazer persistente salvo com o projeto.%n- Linhas tracejadas e setas personalizáveis para os fios.%n- Pontos de controle maiores e mais visíveis.%n- Opções de extensão de máscara para maior controle.%n- Algoritmo de sombreamento aprimorado com sombras mais suaves.%n- Painel de camadas aprimorado com reordenação arrastar-e-soltar e visibilidade rápida.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nחדש בגרסה זו:%n- היסטוריית ביטול/חזרה נשמרת עם הפרויקט.%n- קווים וחיצים מקווקווים בהתאמה אישית.%n- נקודות בקרה גדולות וברורות יותר.%n- אפשרויות הארכת מסיכות לשליטה טובה יותר.%n- אלגוריתם הצללה משופר לצללים רכים יותר.%n- לוח שכבות משופר עם גרור-ושחרר ותפריט תצוגה מהירה.%n%nהתוכנית מובאת אליכם על ידי יונתן סתבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.105"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "06_Dec_2025"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_105
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.105:%n%n• Mask Grid: Quickly create multiple strand masks using a visual NxN grid interface in group functionalities.%n• Keyboard Shortcuts: Space to pan, Z to undo, X to redo, N for new strand, 1 for draw names, L to lock layers, D to delete strand, A to deselect all.%n• Fixed Selection & Zoom: Selection in move, select, and attach modes now remains accurate at all zoom levels.%n• Smoother Node Connections: Fixed a rendering issue where closed nodes sometimes showed visible seams or gaps at the connection point.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.105:%n%n• Grille de Masques: Créez rapidement plusieurs masques de brins à l'aide d'une interface de grille visuelle NxN dans les fonctionnalités de groupe.%n• Raccourcis Clavier: Espace pour panoramique, Z pour annuler, X pour rétablir, N pour nouveau brin, 1 pour dessiner les noms, L pour verrouiller les calques, D pour supprimer le brin, A pour tout désélectionner.%n• Sélection et Zoom Corrigés: La sélection dans les modes déplacer, sélectionner et attacher reste désormais précise à tous les niveaux de zoom.%n• Connexions de Nœuds Plus Lisses: Correction d'un problème de rendu où les nœuds fermés présentaient parfois des coutures ou des espaces visibles au point de connexion.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.105:%n%n• Maskenraster: Erstellen Sie schnell mehrere Strangmasken mit einer visuellen NxN-Rasteroberfläche in Gruppenfunktionen.%n• Tastaturkürzel: Leertaste zum Schwenken, Z zum Rückgängig machen, X zum Wiederherstellen, N für neuen Strang, 1 für Namen zeigen, L zum Sperren, D zum Entfernen, A zum Abwählen.%n• Auswahl & Zoom Korrigiert: Die Auswahl in den Modi Verschieben, Auswählen und Anhängen bleibt nun auf allen Zoomstufen präzise.%n• Glattere Knotenverbindungen: Ein Rendering-Problem wurde behoben, bei dem geschlossene Knoten manchmal sichtbare Nähte oder Lücken am Verbindungspunkt zeigten.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.105:%n%n• Griglia Maschera: Crea rapidamente più maschere di trefolo utilizzando un'interfaccia griglia visiva NxN nelle funzionalità di gruppo.%n• Scorciatoie da Tastiera: Spazio per panoramica, Z per annullare, X per ripristinare, N per nuovo trefolo, 1 per nomi, L per bloccare, D per eliminare, A per deselezionare.%n• Selezione e Zoom Corretti: La selezione nelle modalità sposta, seleziona e attacca ora rimane precisa a tutti i livelli di zoom.%n• Connessioni Nodi Più Fluide: Risolto un problema di rendering in cui i nodi chiusi mostravano a volte cuciture o spazi visibili nel punto di connessione.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.105:%n%n• Cuadrícula de Máscaras: Cree rápidamente múltiples máscaras de hilo usando una interfaz de cuadrícula visual NxN en las funcionalidades de grupo.%n• Atajos de Teclado: Espacio para desplazar, Z para deshacer, X para rehacer, N para nuevo hilo, 1 para nombres, L para bloquear, D para eliminar, A para deseleccionar.%n• Selección y Zoom Corregidos: La selección en los modos mover, seleccionar y adjuntar ahora permanece precisa en todos los niveles de zoom.%n• Conexiones de Nodos Más Suaves: Se corrigió un problema de renderizado donde los nodos cerrados a veces mostraban costuras o espacios visibles en el punto de conexión.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.105:%n%n• Grade de Máscaras: Crie rapidamente várias máscaras de fio usando uma interface de grade visual NxN nas funcionalidades de grupo.%n• Atalhos de Teclado: Espaço para panorâmica, Z para desfazer, X para refazer, N para novo fio, 1 para nomes, L para bloquear, D para excluir, A para desmarcar.%n• Seleção e Zoom Corrigidos: A seleção nos modos mover, selecionar e anexar agora permanece precisa em todos os níveis de zoom.%n• Conexões de Nós Mais Suaves: Corrigido um problema de renderização onde os nós fechados às vezes mostravam costuras ou lacunas visíveis no ponto de conexão.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.105:%n%n• רשת מסכות: צור במהירות מספר מסכות גדיל באמצעות ממשק רשת חזותי NxN בפונקציות קבוצה.%n• קיצורי מקלדת: רווח להזזה, Z לביטול, X לשחזור, N לגדיל חדש, 1 לשמות, L לנעילה, D למחיקה, A לביטול בחירה.%n• תיקון בחירה וזום: בחירה במצבי הזזה, בחירה וצירוף נשארת מדויקת בכל רמות הזום.%n• חיבורי צמתים חלקים יותר: תוקנה בעיית רינדור שבה צמתים סגורים הראו לעיתים תפרים או רווחים נראים בנקודת החיבור.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

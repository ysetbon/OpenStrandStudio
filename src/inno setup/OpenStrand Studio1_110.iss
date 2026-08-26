#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.110"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "26_Aug_2026"
; Paths are relative to this .iss file (src\inno setup\), so the installer
; compiles from any clone location.
#define SourcePath ".."
#define ExePath "..\dist"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact=ysetbon@gmail.com
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\dist
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_110
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
Source: "{#SourcePath}\layer_panel_icons\*.png"; DestDir: "{app}\layer_panel_icons"; Flags: ignoreversion recursesubdirs
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.110:%n%n• Layer-Only Colors and Set-Wide Stroke Color: The layer menu now pairs every color option with a layer-only version: Change Color / Change Color (This Layer Only) and Change Stroke Color / Change Stroke Color (This Layer Only), matching the existing width entries. Change Stroke Color now recolors the whole set just like Change Color, while the layer-only entries repaint only the clicked layer. Per-layer exceptions are saved with your project and survive undo/redo, tab switching and group operations; changing the set color again resets them.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.110:%n%n• Couleurs par calque et couleur du trait pour tout l'ensemble: Le menu des calques associe désormais à chaque option de couleur une version pour un seul calque : Changer la couleur / Changer la couleur (ce calque seulement) et Changer la couleur du trait / Changer la couleur du trait (ce calque seulement), comme les entrées de largeur existantes. Changer la couleur du trait recolore maintenant tout l'ensemble comme le fait Changer la couleur, tandis que les entrées « ce calque seulement » ne repeignent que le calque cliqué. Les exceptions par calque sont enregistrées avec votre projet et survivent aux annulations/rétablissements, au changement d'onglet et aux opérations de groupe ; changer à nouveau la couleur de l'ensemble les réinitialise.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.110:%n%n• Ebenen-eigene Farben und satzweite Konturfarbe: Das Ebenenmenü bietet jetzt zu jeder Farboption eine Variante für nur eine Ebene: Farbe ändern / Farbe ändern (nur diese Ebene) und Konturfarbe ändern / Konturfarbe ändern (nur diese Ebene), passend zu den vorhandenen Breite-Einträgen. Konturfarbe ändern färbt jetzt wie Farbe ändern den gesamten Satz um, während die Einträge „nur diese Ebene“ ausschließlich die angeklickte Ebene umfärben. Ebenen-Ausnahmen werden mit dem Projekt gespeichert und überstehen Rückgängig/Wiederherstellen, Tab-Wechsel und Gruppenoperationen; eine erneute Satzfarbe setzt sie zurück.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.110:%n%n• Colori per singolo livello e colore del tratto per tutto il set: Il menu dei livelli affianca ora a ogni opzione di colore una versione per il solo livello: Cambia colore / Cambia colore (solo questo livello) e Cambia colore del tratto / Cambia colore del tratto (solo questo livello), come le voci di larghezza già esistenti. Cambia colore del tratto ora ricolora l'intero set proprio come Cambia colore, mentre le voci «solo questo livello» ridipingono soltanto il livello su cui hai fatto clic. Le eccezioni per livello vengono salvate con il progetto e sopravvivono ad annulla/ripristina, al cambio di scheda e alle operazioni di gruppo; cambiando di nuovo il colore del set vengono azzerate.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.110:%n%n• Colores por capa y color del trazo para todo el conjunto: El menú de capas acompaña ahora cada opción de color con una versión para una sola capa: Cambiar color / Cambiar color (solo esta capa) y Cambiar color del trazo / Cambiar color del trazo (solo esta capa), igual que las entradas de ancho ya existentes. Cambiar color del trazo ahora recolorea todo el conjunto como lo hace Cambiar color, mientras que las entradas «solo esta capa» repintan únicamente la capa en la que hiciste clic. Las excepciones por capa se guardan con tu proyecto y sobreviven a deshacer/rehacer, al cambio de pestaña y a las operaciones de grupo; volver a cambiar el color del conjunto las restablece.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.110:%n%n• Cores por camada e cor do traço para todo o conjunto: O menu de camadas agora acompanha cada opção de cor com uma versão para uma única camada: Mudar cor / Mudar cor (apenas esta camada) e Mudar cor do traço / Mudar cor do traço (apenas esta camada), tal como as entradas de largura já existentes. Mudar cor do traço agora recolore todo o conjunto como Mudar cor faz, enquanto as entradas «apenas esta camada» repintam somente a camada clicada. As exceções por camada são salvas com o projeto e sobrevivem a desfazer/refazer, à troca de aba e às operações de grupo; mudar novamente a cor do conjunto as redefine.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.110:%n%n• צבעים לשכבה בודדת וצבע קו לכל הסט: תפריט השכבות מציע כעת לכל אפשרות צבע גם גרסה לשכבה בודדת: שנה צבע / שנה צבע (שכבה זו בלבד) ושנה צבע קו / שנה צבע קו (שכבה זו בלבד), בדומה לפריטי הרוחב הקיימים. שנה צבע קו משנה כעת את כל הסט בדיוק כמו שנה צבע, ואילו הפריטים "שכבה זו בלבד" צובעים רק את השכבה שנלחצה. החריגים לכל שכבה נשמרים עם הפרויקט ושורדים ביטול/ביצוע מחדש, מעבר בין כרטיסיות ופעולות קבוצה; שינוי חוזר של צבע הסט מאפס אותם.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

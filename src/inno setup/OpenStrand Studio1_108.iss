#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.108"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "01_Jun_2026"
#define SourcePath "C:\Users\YonatanSetbon\projects\OpenStrandStudio\src"
#define ExePath "C:\Users\YonatanSetbon\projects\OpenStrandStudio\src\dist"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact=ysetbon@gmail.com
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=C:\Users\YonatanSetbon\projects\OpenStrandStudio\src\dist
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_108
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.108:%n%n• Multi-Tab Workspace: A new Tabs button opens a draggable tab edge that magnet-snaps to the side of the canvas. Each tab is an independent session with its own strands, groups, and undo/redo history, and you are warned before quitting when a tab still has unsaved changes.%n• View Mode Toggles in Settings: New settings let you hide the selection highlight and hide control points while in View mode, giving you a clean, capture-ready canvas without changing your actual selection.%n• Folded-Over Start Edge by Default: A new Layer Panel setting makes every newly attached strand begin with a folded-over (transparent) start edge automatically, so you no longer have to set it strand by strand from the layer button menu.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.108:%n%n• Espace de travail multi-onglets: Un nouveau bouton Onglets ouvre un bord d'onglets déplaçable qui s'aimante sur le côté du canevas. Chaque onglet est une session indépendante avec ses propres brins, groupes et historique d'annulation/rétablissement, et vous êtes averti avant de quitter lorsqu'un onglet contient encore des modifications non enregistrées.%n• Options du mode Vue dans les Paramètres: De nouveaux paramètres permettent de masquer la surbrillance de sélection et de masquer les points de contrôle en mode Vue, vous offrant un canevas épuré et prêt pour la capture sans modifier votre sélection réelle.%n• Bord de départ replié par défaut : Un nouveau paramètre du panneau des calques fait commencer automatiquement chaque nouveau brin attaché avec un bord de départ replié (transparent), sans avoir à le définir brin par brin depuis le menu du bouton de calque.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.108:%n%n• Multi-Tab-Arbeitsbereich: Eine neue Schaltfläche „Tabs“ öffnet eine verschiebbare Tab-Leiste, die magnetisch an der Seite der Leinwand einrastet. Jeder Tab ist eine eigenständige Sitzung mit eigenen Strängen, Gruppen und Rückgängig-/Wiederherstellen-Verlauf, und Sie werden vor dem Beenden gewarnt, wenn ein Tab noch nicht gespeicherte Änderungen enthält.%n• Ansichtsmodus-Optionen in den Einstellungen: Neue Einstellungen blenden die Auswahl-Hervorhebung und die Kontrollpunkte im Ansichtsmodus aus und sorgen für eine aufgeräumte, aufnahmebereite Leinwand, ohne Ihre tatsächliche Auswahl zu ändern.%n• Umgefaltete Startkante als Standard: Eine neue Einstellung im Ebenenbereich lässt jeden neu angehängten Strang automatisch mit einer umgefalteten (transparenten) Startkante beginnen, sodass Sie dies nicht mehr für jeden Strang einzeln über das Ebenen-Schaltflächenmenü festlegen müssen.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.108:%n%n• Area di lavoro multi-scheda: Un nuovo pulsante Schede apre un bordo di schede trascinabile che si aggancia magneticamente al lato della tela. Ogni scheda è una sessione indipendente con i propri fili, gruppi e cronologia di annullamento/ripristino, e vieni avvisato prima di uscire quando una scheda contiene ancora modifiche non salvate.%n• Opzioni della modalità Vista nelle Impostazioni: Nuove impostazioni consentono di nascondere l'evidenziazione della selezione e i punti di controllo in modalità Vista, offrendoti una tela pulita e pronta per l'acquisizione senza modificare la selezione effettiva.%n• Bordo iniziale ripiegato come predefinito: Una nuova impostazione nel pannello dei livelli fa iniziare automaticamente ogni nuovo filo collegato con un bordo iniziale ripiegato (trasparente), così non devi più impostarlo filo per filo dal menu del pulsante del livello.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.108:%n%n• Espacio de trabajo con pestañas: Un nuevo botón Pestañas abre un borde de pestañas arrastrable que se acopla magnéticamente al lado del lienzo. Cada pestaña es una sesión independiente con sus propias hebras, grupos e historial de deshacer/rehacer, y se te avisa antes de salir cuando una pestaña todavía tiene cambios sin guardar.%n• Opciones del modo Ver en Ajustes: Nuevos ajustes permiten ocultar el resaltado de selección y los puntos de control en modo Ver, ofreciéndote un lienzo limpio y listo para capturar sin cambiar tu selección real.%n• Borde inicial replegado por defecto: Un nuevo ajuste en el panel de capas hace que cada nueva hebra adjunta comience automáticamente con un borde inicial replegado (transparente), por lo que ya no tienes que configurarlo hebra por hebra desde el menú del botón de capa.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.108:%n%n• Espaço de trabalho com abas: Um novo botão Abas abre uma borda de abas arrastável que se encaixa magneticamente na lateral da tela. Cada aba é uma sessão independente com seus próprios fios, grupos e histórico de desfazer/refazer, e você é avisado antes de sair quando uma aba ainda tem alterações não salvas.%n• Opções do modo Visualização nas Configurações: Novas configurações permitem ocultar o destaque de seleção e os pontos de controle no modo Visualização, oferecendo uma tela limpa e pronta para captura sem alterar sua seleção real.%n• Borda inicial dobrada por padrão: Uma nova configuração no painel de camadas faz cada novo fio anexado começar automaticamente com uma borda inicial dobrada (transparente), para que você não precise mais defini-la fio por fio no menu do botão de camada.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.108:%n%n• כרטיסיות מרובות: כפתור "כרטיסיות" חדש פותח קצה כרטיסיות נגרר שנצמד מגנטית לצד הקנבס. כל כרטיסייה היא הפעלה עצמאית עם החוטים, הקבוצות והיסטוריית הביטול/ביצוע מחדש שלה, ותקבלו אזהרה לפני יציאה כאשר בכרטיסייה עדיין יש שינויים שלא נשמרו.%n• אפשרויות מצב תצוגה בהגדרות: הגדרות חדשות מאפשרות להסתיר את הדגשת הבחירה ואת נקודות הבקרה במצב תצוגה, ומעניקות לכם קנבס נקי ומוכן לצילום מבלי לשנות את הבחירה בפועל.%n• קצה התחלה מקופל כברירת מחדל: הגדרה חדשה בלוח השכבות גורמת לכל חוט מחובר חדש להתחיל אוטומטית עם קצה התחלה מקופל (שקוף), כך שאין צורך להגדיר זאת לכל חוט בנפרד מתפריט כפתור השכבה.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

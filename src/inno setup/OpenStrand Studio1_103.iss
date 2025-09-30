#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.103"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "30_Sep_2025"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_103
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.103:%n%n• Full Arrow System: Comprehensive arrow feature with multiple customizable properties including arrow color (independent from strand), transparency (0-100%), head texture (None, Stripes, Dots, Crosshatch), shaft style (Solid, Stripes, Dots, Tiles), shadow support, head visibility toggle, and dimension controls.%n• Smart Mask Group Selection: When creating groups with masked strands, selecting one component automatically includes its mask partner, maintaining mask integrity in grouped operations.%n• Enhanced Painting System: Fixed rendering issues for strand paths and attached strands during draw operations, ensuring consistent visual representation.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.103:%n%n• Système de flèches complet : Fonction de flèche complète avec plusieurs propriétés personnalisables incluant la couleur de flèche (indépendante du brin), transparence (0-100%), texture de tête (Aucune, Rayures, Points, Hachures croisées), style de tige (Solide, Rayures, Points, Carreaux), support d'ombre, visibilité de tête, et contrôles de dimension.%n• Sélection intelligente de groupe masqué : Lors de la création de groupes avec des brins masqués, la sélection d'un composant inclut automatiquement son partenaire de masque, maintenant l'intégrité du masque dans les opérations groupées.%n• Système de peinture amélioré : Correction des problèmes de rendu pour les chemins de brin et les brins attachés pendant les opérations de dessin.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.103:%n%n• Vollständiges Pfeilsystem: Umfassende Pfeilfunktion mit mehreren anpassbaren Eigenschaften wie Pfeilfarbe (unabhängig vom Strang), Transparenz (0-100%), Kopftextur (Keine, Streifen, Punkte, Schraffur), Schaftstil (Solide, Streifen, Punkte, Kacheln), Schattenunterstützung, Kopfsichtbarkeit und Dimensionskontrollen.%n• Intelligente Maskengruppenauswahl: Beim Erstellen von Gruppen mit maskierten Strängen wird beim Auswählen einer Komponente automatisch der Maskenpartner eingeschlossen, wodurch die Maskenintegrität in gruppierten Operationen erhalten bleibt.%n• Verbessertes Malsystem: Behobene Renderprobleme für Strangpfade und angehängte Stränge während Zeichenoperationen.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.103:%n%n• Sistema di frecce completo: Funzione freccia completa con molteplici proprietà personalizzabili tra cui colore freccia (indipendente dal filamento), trasparenza (0-100%), texture della punta (Nessuna, Strisce, Punti, Tratteggio incrociato), stile dell'asta (Solido, Strisce, Punti, Piastrelle), supporto ombra, visibilità della punta e controlli dimensionali.%n• Selezione intelligente gruppo maschera: Quando si creano gruppi con filamenti mascherati, selezionando un componente si include automaticamente il suo partner maschera, mantenendo l'integrità della maschera nelle operazioni di gruppo.%n• Sistema di pittura migliorato: Risolti problemi di rendering per percorsi di filamento e filamenti attaccati durante le operazioni di disegno.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.103:%n%n• Sistema de flechas completo: Función de flecha completa con múltiples propiedades personalizables incluyendo color de flecha (independiente del hilo), transparencia (0-100%), textura de punta (Ninguna, Rayas, Puntos, Trama cruzada), estilo del eje (Sólido, Rayas, Puntos, Azulejos), soporte de sombra, visibilidad de punta y controles de dimensión.%n• Selección inteligente de grupo de máscara: Al crear grupos con hilos enmascarados, seleccionar un componente incluye automáticamente su compañero de máscara, manteniendo la integridad de la máscara en operaciones agrupadas.%n• Sistema de pintura mejorado: Corregidos problemas de renderizado para rutas de hilos e hilos adjuntos durante operaciones de dibujo.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.103:%n%n• Sistema de setas completo: Recurso de seta abrangente com várias propriedades personalizáveis incluindo cor da seta (independente do fio), transparência (0-100%), textura da ponta (Nenhuma, Listras, Pontos, Hachura cruzada), estilo do eixo (Sólido, Listras, Pontos, Azulejos), suporte de sombra, visibilidade da ponta e controles dimensionais.%n• Seleção inteligente de grupo de máscara: Ao criar grupos com fios mascarados, selecionar um componente inclui automaticamente seu parceiro de máscara, mantendo a integridade da máscara em operações agrupadas.%n• Sistema de pintura aprimorado: Corrigidos problemas de renderização para caminhos de fios e fios anexados durante operações de desenho.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.103:%n%n• מערכת חיצים מלאה: תכונת חיצים מקיפה עם מספר מאפיינים הניתנים להתאמה אישית כולל צבע חץ (בלתי תלוי בגדיל), שקיפות (0-100%), מרקם ראש (ללא, פסים, נקודות, בקיעה צולבת), סגנון ציר (מוצק, פסים, נקודות, אריחים), תמיכה בצל, נראות ראש וקרות מימד.%n• בחירת קבוצת מסכה חכמה: בעת יצירת קבוצות עם גדילים ממוסכים, בחירת רכיב אחד כוללת אוטומטית את שותף המסכה שלו, תוך שמירה על שלמות המסכה בפעולות מקובצות.%n• מערכת צביעה משופרת: תוקנו בעיות עיבוד עבור נתיבי גדילים וגדילים מחוברים במהלך פעולות ציור.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה
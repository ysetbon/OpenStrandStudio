#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.107"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "20_Apr_2026"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_107
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.107:%n%n• Group Shadow Editor: Shadows can now be edited for entire groups, giving you full control over how group strands cast shadows on the canvas.%n• Shadow Editor Fixes && Masked Strand Support: Shadow subtraction logic is unified between the main renderer and the shadow preview, and masked strands can now be edited through the shadow editor dialog with smart defaults.%n• Selected Strand Settings: A new Selected Strand category in Settings gathers options that apply only to the currently selected strand — move-only, control-points-only, shadow-only, and a customizable selection highlight color.%n• Group Creation Stability: Fixed unexpected crashes caused by orphan hidden group dialogs when creating groups or exiting the application.%n• Hebrew Right-to-Left Alignment: The main window, settings dialog, group context menu, and group panel are now mirrored right-to-left in Hebrew for a natural reading order.%n• View Button: New View button in the main window that hides all mode indicators (Move, Attach, etc.) so you can see your design clearly without any UI overlays.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.107:%n%n• Éditeur d'ombres de groupe: Les ombres peuvent désormais être modifiées pour des groupes entiers, vous offrant un contrôle total sur la façon dont les brins d'un groupe projettent leurs ombres sur le canevas.%n• Corrections de l'éditeur d'ombres et prise en charge des brins masqués: La logique de soustraction des ombres est unifiée entre le rendu principal et l'aperçu des ombres, et les brins masqués peuvent maintenant être modifiés via la boîte de dialogue de l'éditeur d'ombres avec des valeurs par défaut intelligentes.%n• Paramètres du brin sélectionné: Une nouvelle catégorie « Brin Sélectionné » dans les paramètres regroupe des options qui ne s'appliquent qu'au brin actuellement sélectionné — déplacement seul, points de contrôle seuls, ombre seule, et une couleur de surbrillance de sélection personnalisable.%n• Stabilité de la création de groupes: Correction des plantages inattendus causés par des boîtes de dialogue de groupe cachées orphelines lors de la création de groupes ou de la fermeture de l'application.%n• Alignement de droite à gauche pour l'hébreu: La fenêtre principale, la boîte de dialogue des paramètres, le menu contextuel de groupe et le panneau de groupe sont désormais mis en miroir de droite à gauche en hébreu pour un ordre de lecture naturel.%n• Bouton Vue: Nouveau bouton Vue dans la fenêtre principale qui masque tous les indicateurs de mode (Bouger, Lier, etc.) pour que vous puissiez voir votre conception clairement, sans aucune superposition d'interface.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.107:%n%n• Gruppen-Schatten-Editor: Schatten können jetzt für ganze Gruppen bearbeitet werden, was Ihnen die volle Kontrolle darüber gibt, wie die Stränge einer Gruppe ihre Schatten auf der Leinwand werfen.%n• Schatten-Editor-Korrekturen && Unterstützung für maskierte Stränge: Die Logik zur Schattensubtraktion ist zwischen dem Hauptrenderer und der Schattenvorschau vereinheitlicht, und maskierte Stränge können jetzt über den Schatten-Editor-Dialog mit intelligenten Standardwerten bearbeitet werden.%n• Einstellungen für ausgewählten Strang: Eine neue Kategorie „Ausgewählter Strang" in den Einstellungen bündelt Optionen, die nur auf den aktuell ausgewählten Strang wirken — nur Bewegung, nur Kontrollpunkte, nur Schatten und eine anpassbare Auswahl-Hervorhebungsfarbe.%n• Stabilität bei der Gruppenerstellung: Unerwartete Abstürze durch verwaiste, ausgeblendete Gruppendialoge beim Erstellen von Gruppen oder beim Beenden der Anwendung wurden behoben.%n• Rechts-nach-links-Ausrichtung für Hebräisch: Hauptfenster, Einstellungsdialog, Gruppen-Kontextmenü und Gruppenpanel sind für Hebräisch nun von rechts nach links gespiegelt, um eine natürliche Leserichtung zu gewährleisten.%n• Ansichtsschaltfläche: Neue Ansichtsschaltfläche im Hauptfenster, die alle Modusanzeigen (Bewegen, Anfügen usw.) ausblendet, damit Sie Ihr Design ohne störende UI-Elemente klar sehen können.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.107:%n%n• Editor delle ombre di gruppo: Le ombre ora possono essere modificate per interi gruppi, offrendoti il pieno controllo sul modo in cui i fili di un gruppo proiettano le loro ombre sulla tela.%n• Correzioni dell'editor delle ombre e supporto per fili mascherati: La logica di sottrazione delle ombre è unificata tra il renderer principale e l'anteprima delle ombre, e i fili mascherati possono ora essere modificati tramite la finestra di dialogo dell'editor delle ombre con impostazioni predefinite intelligenti.%n• Impostazioni del filo selezionato: Una nuova categoria "Filo Selezionato" nelle Impostazioni raggruppa opzioni che si applicano solo al filo attualmente selezionato — solo movimento, solo punti di controllo, sola ombra e un colore di evidenziazione della selezione personalizzabile.%n• Stabilità nella creazione dei gruppi: Corretti gli arresti anomali inattesi causati da finestre di dialogo di gruppo nascoste orfane durante la creazione di gruppi o la chiusura dell'applicazione.%n• Allineamento da destra a sinistra per l'ebraico: La finestra principale, la finestra delle impostazioni, il menu contestuale del gruppo e il pannello dei gruppi sono ora rispecchiati da destra a sinistra in ebraico per un ordine di lettura naturale.%n• Pulsante Vista: Nuovo pulsante Vista nella finestra principale che nasconde tutti gli indicatori di modalità (Muovi, Collega, ecc.) in modo da poter vedere chiaramente il tuo progetto senza sovrapposizioni dell'interfaccia.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.107:%n%n• Editor de sombras de grupo: Ahora se pueden editar las sombras de grupos completos, ofreciéndote control total sobre cómo las hebras de un grupo proyectan sus sombras en el lienzo.%n• Correcciones del editor de sombras y soporte para hebras enmascaradas: La lógica de sustracción de sombras se ha unificado entre el renderizador principal y la vista previa de sombras, y las hebras enmascaradas ahora pueden editarse a través del diálogo del editor de sombras con valores predeterminados inteligentes.%n• Ajustes de hebra seleccionada: Una nueva categoría "Hebra Seleccionada" en Ajustes reúne opciones que solo se aplican a la hebra actualmente seleccionada — solo mover, solo puntos de control, solo sombra y un color de resaltado de selección personalizable.%n• Estabilidad en la creación de grupos: Corregidos los cierres inesperados causados por diálogos de grupo ocultos huérfanos al crear grupos o al cerrar la aplicación.%n• Alineación de derecha a izquierda para el hebreo: La ventana principal, el diálogo de ajustes, el menú contextual de grupo y el panel de grupos ahora se reflejan de derecha a izquierda en hebreo para un orden de lectura natural.%n• Botón Ver: Nuevo botón Ver en la ventana principal que oculta todos los indicadores de modo (Mover, Adjuntar, etc.) para que puedas ver tu diseño claramente sin superposiciones de interfaz.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.107:%n%n• Editor de sombras de grupo: As sombras agora podem ser editadas para grupos inteiros, dando a você controle total sobre como as mechas de um grupo projetam suas sombras na tela.%n• Correções do editor de sombras e suporte a mechas mascaradas: A lógica de subtração de sombras foi unificada entre o renderizador principal e a pré-visualização de sombras, e as mechas mascaradas agora podem ser editadas através da caixa de diálogo do editor de sombras com valores padrão inteligentes.%n• Configurações de mecha selecionada: Uma nova categoria "Fio Selecionado" em Configurações reúne opções que se aplicam apenas à mecha atualmente selecionada — apenas mover, apenas pontos de controle, apenas sombra e uma cor de destaque da seleção personalizável.%n• Estabilidade na criação de grupos: Corrigidas as falhas inesperadas causadas por caixas de diálogo de grupo ocultas órfãs ao criar grupos ou ao fechar o aplicativo.%n• Alinhamento da direita para a esquerda para hebraico: A janela principal, a caixa de diálogo de configurações, o menu de contexto do grupo e o painel de grupos agora são espelhados da direita para a esquerda em hebraico para uma ordem de leitura natural.%n• Botão Ver: Novo botão Ver na janela principal que oculta todos os indicadores de modo (Mover, Anexar, etc.) para que você possa ver seu design claramente sem sobreposições de interface.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.107:%n%n• עורך צללים לקבוצה: ניתן כעת לערוך צללים עבור קבוצות שלמות, ומעניק לך שליטה מלאה על האופן שבו חוטי הקבוצה מטילים צללים על הקנבס.%n• תיקונים בעורך הצללים ותמיכה בחוטים ממוסכים: לוגיקת חיסור הצללים אוחדה בין המעבד הראשי לבין תצוגת הצללים, וכעת ניתן לערוך חוטים ממוסכים דרך חלון עורך הצללים עם ברירות מחדל חכמות.%n• הגדרות חוט נבחר: קטגוריה חדשה "חוט נבחר" בהגדרות מאגדת אפשרויות שחלות רק על החוט הנבחר כעת — הזזה בלבד, נקודות בקרה בלבד, צל בלבד וצבע הדגשה מותאם אישית לבחירה.%n• יציבות ביצירת קבוצות: תוקנו קריסות לא צפויות הנגרמות על ידי חלונות קבוצה מוסתרים יתומים בעת יצירת קבוצות או יציאה מהיישום.%n• יישור מימין לשמאל בעברית: החלון הראשי, חלון ההגדרות, תפריט ההקשר של קבוצות וחלונית הקבוצות ממוסכים כעת מימין לשמאל בעברית לסדר קריאה טבעי.%n• כפתור תצוגה: כפתור תצוגה חדש בחלון הראשי שמסתיר את כל מחווני המצב (הזז, חבר וכו') כך שתוכל לראות את העיצוב שלך בבירור ללא שכבות ממשק נוספות.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.101"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "9_Jan_2025"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_101
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
Source: "{#SourcePath}\flags\*.png"; DestDir: "{app}\flags"; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\mp4\*.mp4"; DestDir: "{app}\mp4"; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\samples\*.json"; DestDir: "{app}\samples"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; MinVersion: 0,1
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\box_stitch.ico"; Tasks: desktopicon; MinVersion: 0,1

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchAfterInstall}"; Flags: nowait postinstall skipifsilent

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.101:%n%n• Improved Layer Management: Enhanced StateLayerManager structure for better handling of knot connections and strand relationships, providing more reliable layer operations and improved performance.%n• Group Duplication: You can now duplicate entire groups with all their strands by right-clicking on a group header and selecting "Duplicate Group". The duplicated group maintains all strand properties and automatically generates unique layer names.%n• Hide Mode: New hide mode accessible via the monkey button (🙉/🙈) allows you to quickly hide multiple layers at once. Click the button to enter hide mode, then click on layers to hide them. Exit hide mode to apply changes.%n• Center View: Instantly center all strands in your view with the new target button (🎯). This automatically adjusts the canvas position to show all your work centered on screen.%n• Quick Knot Closure: Right-click on any strand or attached strand with a free end to quickly close the knot. The system automatically finds and connects to the nearest matching strand with a free end.%n• Sample Projects: Access sample projects directly from the settings dialog to quickly load example knot designs and learn different techniques.%n• Enhanced Settings Dialog: Improved settings interface with better organization and new sample projects section for easy access to example files.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.101:%n%n• Gestion améliorée des couches : Structure StateLayerManager améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.%n• Duplication de groupe : Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant "Dupliquer le groupe". Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.%n• Mode masquage : Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permet de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches pour les masquer. Quittez le mode masquage pour appliquer les changements.%n• Centrer la vue : Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). Cela ajuste automatiquement la position du canevas pour afficher tout votre travail centré à l'écran.%n• Fermeture rapide de nœud : Faites un clic droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et se connecte automatiquement au brin correspondant le plus proche avec une extrémité libre.%n• Projets exemples : Accédez aux projets exemples directement depuis la boîte de dialogue des paramètres pour charger rapidement des designs de nœuds exemples et apprendre différentes techniques.%n• Dialogue de paramètres amélioré : Interface de paramètres améliorée avec une meilleure organisation et une nouvelle section de projets exemples pour un accès facile aux fichiers exemples.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.101:%n%n• Gestione livelli migliorata: Struttura StateLayerManager migliorata per una migliore gestione delle connessioni dei nodi e delle relazioni tra trefoli, offrendo operazioni sui livelli più affidabili e prestazioni migliorate.%n• Duplicazione gruppo: Ora puoi duplicare interi gruppi con tutti i loro trefoli facendo clic destro sull'intestazione di un gruppo e selezionando "Duplica gruppo". Il gruppo duplicato mantiene tutte le proprietà dei trefoli e genera automaticamente nomi di livelli unici.%n• Modalità nascondi: Nuova modalità nascondi accessibile tramite il pulsante scimmia (🙉/🙈) permette di nascondere rapidamente più livelli contemporaneamente. Clicca sul pulsante per entrare in modalità nascondi, poi clicca sui livelli per nasconderli. Esci dalla modalità nascondi per applicare le modifiche.%n• Centra vista: Centra istantaneamente tutti i trefoli nella tua vista con il nuovo pulsante bersaglio (🎯). Questo regola automaticamente la posizione del canvas per mostrare tutto il tuo lavoro centrato sullo schermo.%n• Chiusura rapida del nodo: Fai clic destro su qualsiasi trefolo o trefolo attaccato con un'estremità libera per chiudere rapidamente il nodo. Il sistema trova e collega automaticamente al trefolo corrispondente più vicino con un'estremità libera.%n• Progetti di esempio: Accedi ai progetti di esempio direttamente dalla finestra di dialogo delle impostazioni per caricare rapidamente design di nodi di esempio e imparare diverse tecniche.%n• Dialogo impostazioni migliorato: Interfaccia impostazioni migliorata con migliore organizzazione e nuova sezione progetti di esempio per facile accesso ai file di esempio.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.101:%n%n• Gestión mejorada de capas: Estructura StateLayerManager mejorada para un mejor manejo de las conexiones de nudos y relaciones entre hebras, ofreciendo operaciones de capas más confiables y mejor rendimiento.%n• Duplicación de grupo: Ahora puedes duplicar grupos completos con todas sus hebras haciendo clic derecho en el encabezado de un grupo y seleccionando "Duplicar grupo". El grupo duplicado mantiene todas las propiedades de las hebras y genera automáticamente nombres de capas únicos.%n• Modo ocultar: Nuevo modo ocultar accesible a través del botón mono (🙉/🙈) permite ocultar rápidamente múltiples capas a la vez. Haz clic en el botón para entrar en modo ocultar, luego haz clic en las capas para ocultarlas. Sal del modo ocultar para aplicar los cambios.%n• Centrar vista: Centra instantáneamente todas las hebras en tu vista con el nuevo botón diana (🎯). Esto ajusta automáticamente la posición del lienzo para mostrar todo tu trabajo centrado en la pantalla.%n• Cierre rápido de nudo: Haz clic derecho en cualquier hebra o hebra adjunta con un extremo libre para cerrar rápidamente el nudo. El sistema encuentra y conecta automáticamente a la hebra coincidente más cercana con un extremo libre.%n• Proyectos de muestra: Accede a proyectos de muestra directamente desde el diálogo de configuración para cargar rápidamente diseños de nudos de ejemplo y aprender diferentes técnicas.%n• Diálogo de configuración mejorado: Interfaz de configuración mejorada con mejor organización y nueva sección de proyectos de muestra para fácil acceso a archivos de ejemplo.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.101:%n%n• Gerenciamento de camadas aprimorado: Estrutura StateLayerManager aprimorada para melhor gerenciamento de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.%n• Duplicação de grupo: Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.%n• Modo ocultar: Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente várias camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.%n• Centralizar visualização: Centralize instantaneamente todos os fios em sua visualização com o novo botão alvo (🎯). Isso ajusta automaticamente a posição do canvas para mostrar todo o seu trabalho centralizado na tela.%n• Fechamento rápido de nó: Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio correspondente mais próximo com uma extremidade livre.%n• Projetos de exemplo: Acesse projetos de exemplo diretamente da caixa de diálogo de configurações para carregar rapidamente designs de nós de exemplo e aprender diferentes técnicas.%n• Diálogo de configurações aprimorado: Interface de configurações aprimorada com melhor organização e nova seção de projetos de exemplo para fácil acesso a arquivos de exemplo.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.101:%n%n• ניהול שכבות משופר: מבנה StateLayerManager משופר לניהול טוב יותר של חיבורי קשרים ויחסים בין חוטים, המספק פעולות שכבה אמינות יותר וביצועים משופרים.%n• שכפול קבוצה: עכשיו אפשר לשכפל קבוצות שלמות עם כל החוטים שלהן על ידי לחיצה ימנית על כותרת הקבוצה ובחירת "שכפל קבוצה". הקבוצה המשוכפלת שומרת על כל המאפיינים של החוטים ויוצרת אוטומטית שמות שכבה ייחודיים.%n• מצב הסתרה: מצב הסתרה חדש נגיש דרך כפתור הקוף (🙉/🙈) מאפשר להסתיר במהירות מספר שכבות בבת אחת. לחץ על הכפתור כדי להיכנס למצב הסתרה, ואז לחץ על שכבות כדי להסתיר אותן. צא ממצב הסתרה כדי להחיל את השינויים.%n• מרכוז תצוגה: מרכז מיידית את כל החוטים בתצוגה שלך עם כפתור המטרה החדש (🎯). זה מכוונן אוטומטית את מיקום הקנבס כדי להציג את כל העבודה שלך במרכז המסך.%n• סגירת קשר מהירה: לחץ לחיצה ימנית על כל חוט או חוט מחובר עם קצה חופשי כדי לסגור במהירות את הקשר. המערכת מוצאת ומתחברת אוטומטית לחוט התואם הקרוב ביותר עם קצה חופשי.%n• פרויקטים לדוגמה: גישה לפרויקטים לדוגמה ישירות מתיבת הדו-שיח של ההגדרות כדי לטעון במהירות עיצובי קשרים לדוגמה וללמוד טכניקות שונות.%n• תיבת דו-שיח הגדרות משופרת: ממשק הגדרות משופר עם ארגון טוב יותר וסעיף חדש של פרויקטים לדוגמה לגישה קלה לקבצי דוגמה.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה
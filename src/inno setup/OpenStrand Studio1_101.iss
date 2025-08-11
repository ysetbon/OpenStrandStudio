#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.101"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "11_Aug_2025"
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
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.101:%n%n• Improved Layer Management: Enhanced StateLayerManager structure for better handling of knot connections and strand relationships, providing more reliable layer operations and improved performance.%n• Group Duplication: You can now duplicate entire groups with all their strands by right-clicking on a group header and selecting "Duplicate Group". The duplicated group maintains all strand properties and automatically generates unique layer names.%n• Hide Mode: New hide mode accessible via the monkey button (🙉/🙈) allows you to quickly hide multiple layers at once. Click the button to enter hide mode, then click on layers to hide them. Exit hide mode to apply changes.%n• Center View: Instantly center all strands in your view with the new target button (🎯). This automatically adjusts the canvas position to show all your work centered on screen.%n• Quick Knot Closing: Right-click on any strand or attached strand with one free end to quickly close the knot. The system automatically finds and connects to the nearest compatible strand with a free end.%n• New Language - German (🇩🇪): You can now switch to German in Settings → Change Language.%n• New Samples category: Explore ready-to-load sample projects in Settings → Samples. Choose a sample to learn from; the dialog will close and the sample will be loaded.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.101:%n%n• Gestion améliorée des couches : Structure StateLayerManager améliorée pour une meilleure gestion des connexions de nœuds et des relations entre brins, offrant des opérations de couches plus fiables et de meilleures performances.%n• Duplication de groupe : Vous pouvez maintenant dupliquer des groupes entiers avec tous leurs brins en faisant un clic droit sur l'en-tête d'un groupe et en sélectionnant "Dupliquer le groupe". Le groupe dupliqué conserve toutes les propriétés des brins et génère automatiquement des noms de couches uniques.%n• Mode masquage : Nouveau mode masquage accessible via le bouton singe (🙉/🙈) permet de masquer rapidement plusieurs couches à la fois. Cliquez sur le bouton pour entrer en mode masquage, puis cliquez sur les couches pour les masquer. Quittez le mode masquage pour appliquer les changements.%n• Centrer la vue : Centrez instantanément tous les brins dans votre vue avec le nouveau bouton cible (🎯). Cela ajuste automatiquement la position du canevas pour afficher tout votre travail centré à l'écran.%n• Fermeture rapide de nœud : Cliquez avec le bouton droit sur n'importe quel brin ou brin attaché avec une extrémité libre pour fermer rapidement le nœud. Le système trouve et connecte automatiquement au brin compatible le plus proche avec une extrémité libre.%n• Nouvelle langue - allemand (🇩🇪) : Vous pouvez maintenant sélectionner l’allemand dans Paramètres → Changer la langue.%n• Nouvelle catégorie Exemples : Découvrez des projets d’exemple prêts à charger dans Paramètres → Exemples. Choisissez un exemple pour apprendre ; la boîte de dialogue se fermera et l’exemple sera chargé.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.101:%n%n• Gestione livelli migliorata: Struttura StateLayerManager migliorata per una migliore gestione delle connessioni dei nodi e delle relazioni tra trefoli, offrendo operazioni sui livelli più affidabili e prestazioni migliorate.%n• Duplicazione gruppo: Ora puoi duplicare interi gruppi con tutti i loro trefoli facendo clic destro sull'intestazione di un gruppo e selezionando "Duplica gruppo". Il gruppo duplicato mantiene tutte le proprietà dei trefoli e genera automaticamente nomi di livelli unici.%n• Modalità nascondi: Nuova modalità nascondi accessibile tramite il pulsante scimmia (🙉/🙈) permette di nascondere rapidamente più livelli contemporaneamente. Clicca sul pulsante per entrare in modalità nascondi, poi clicca sui livelli per nasconderli. Esci dalla modalità nascondi per applicare le modifiche.%n• Centra vista: Centra istantaneamente tutti i trefoli nella tua vista con il nuovo pulsante bersaglio (🎯). Questo regola automaticamente la posizione del canvas per mostrare tutto il tuo lavoro centrato sullo schermo.%n• Chiusura rapida del nodo: Fai clic destro su qualsiasi trefolo o trefolo attaccato con un'estremità libera per chiudere rapidamente il nodo. Il sistema trova e connette automaticamente al trefolo compatibile più vicino con un'estremità libera.%n• Nuova lingua - Tedesco (🇩🇪): Ora puoi selezionare il tedesco in Impostazioni → Cambia Lingua.%n• Nuova categoria Esempi: Scopri progetti di esempio pronti al caricamento in Impostazioni → Esempi. Scegli un esempio da cui imparare; la finestra si chiuderà e l'esempio verrà caricato.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.101:%n%n• Gestión mejorada de capas: Estructura StateLayerManager mejorada para un mejor manejo de las conexiones de nudos y relaciones entre hebras, ofreciendo operaciones de capas más confiables y mejor rendimiento.%n• Duplicación de grupo: Ahora puedes duplicar grupos completos con todas sus hebras haciendo clic derecho en el encabezado de un grupo y seleccionando "Duplicar grupo". El grupo duplicado mantiene todas las propiedades de las hebras y genera automáticamente nombres de capas únicos.%n• Modo ocultar: Nuevo modo ocultar accesible a través del botón mono (🙉/🙈) permite ocultar rápidamente múltiples capas a la vez. Haz clic en el botón para entrar en modo ocultar, luego haz clic en las capas para ocultarlas. Sal del modo ocultar para aplicar los cambios.%n• Centrar vista: Centra instantáneamente todas las hebras en tu vista con el nuevo botón diana (🎯). Esto ajusta automáticamente la posición del lienzo para mostrar todo tu trabajo centrado en la pantalla.%n• Cierre rápido de nudo: Haz clic derecho en cualquier hebra o hebra adjunta con un extremo libre para cerrar rápidamente el nudo. El sistema encuentra y conecta automáticamente a la hebra compatible más cercana con un extremo libre.%n• Nuevo idioma - Alemán (🇩🇪): Ahora puedes cambiar a alemán en Configuración → Cambiar Idioma.%n• Nueva categoría Ejemplos: Explora proyectos de ejemplo listos para cargar en Configuración → Ejemplos. Elige un ejemplo para aprender; el cuadro de diálogo se cerrará y el ejemplo se cargará.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.101:%n%n• Gerenciamento de camadas aprimorado: Estrutura StateLayerManager aprimorada para melhor gerenciamento de conexões de nós e relações entre fios, oferecendo operações de camadas mais confiáveis e melhor desempenho.%n• Duplicação de grupo: Agora você pode duplicar grupos inteiros com todos os seus fios clicando com o botão direito no cabeçalho de um grupo e selecionando "Duplicar grupo". O grupo duplicado mantém todas as propriedades dos fios e gera automaticamente nomes de camadas únicos.%n• Modo ocultar: Novo modo ocultar acessível através do botão macaco (🙉/🙈) permite ocultar rapidamente várias camadas de uma vez. Clique no botão para entrar no modo ocultar, depois clique nas camadas para ocultá-las. Saia do modo ocultar para aplicar as mudanças.%n• Centralizar visualização: Centralize instantaneamente todos os fios em sua visualização com o novo botão alvo (🎯). Isso ajusta automaticamente a posição do canvas para mostrar todo o seu trabalho centrado na tela.%n• Fechamento rápido de nó: Clique com o botão direito em qualquer fio ou fio anexado com uma extremidade livre para fechar rapidamente o nó. O sistema encontra e conecta automaticamente ao fio compatível mais próximo com uma extremidade livre.%n• Novo idioma - Alemão (🇩🇪): Agora você pode alternar para alemão em Configurações → Mudar Idioma.%n• Nova categoria Exemplos: Explore projetos de exemplo prontos para carregar em Configurações → Exemplos. Escolha um exemplo para aprender; a janela será fechada e o exemplo será carregado.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.101:%n%n• ניהול שכבות משופר: מבנה StateLayerManager משופר לניהול טוב יותר של חיבורי קשרים ויחסים בין חוטים, המספק פעולות שכבה אמינות יותר וביצועים משופרים.%n• שכפול קבוצה: עכשיו ניתן לשכפל קבוצות שלמות עם כל החוטים שלהן באמצעות לחיצה ימנית על כותרת הקבוצה ובחירה ב"שכפל קבוצה". הקבוצה המשוכפלת שומרת על כל מאפייני החוטים ויוצרת אוטומטית שמות שכבה ייחודיים.%n• מצב הסתרה: מצב חדש (🙉/🙈) שמאפשר להסתיר במהירות מספר שכבות בלחיצה. כנס למצב הסתרה, לחץ על שכבות כדי להסתירן וצא כדי להחיל את השינויים.%n• מרכוז תצוגה: כפתור מטרה חדש (🎯) שמרכז מיידית את כל החוטים בתצוגה ומתאים אוטומטית את מיקום הקנבס.%n• סגירת קשר מהירה: לחיצה ימנית על חוט או חוט מחובר עם קצה חופשי סוגרת במהירות את הקשר. המערכת מאתרת ומתחברת אוטומטית לחוט תואם קרוב עם קצה חופשי.%n• שפה חדשה - גרמנית (🇩🇪): ניתן לבחור גרמנית דרך הגדרות → שינוי שפה.%n• קטגוריית דוגמאות חדשה: טען פרויקטים לדוגמה דרך הגדרות → דוגמאות. בחירת דוגמה תסגור את החלון והדוגמה תיטען.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.101:%n%n• Verbesserte Ebenenverwaltung: Verbesserte StateLayerManager-Struktur für ein zuverlässigeres Handling von Knotenverbindungen und Strangbeziehungen, was stabilere Operationen und bessere Performance bietet.%n• Gruppenduplikation: Ganze Gruppen mit allen Strängen per Rechtsklick auf den Gruppen-Header und Auswahl von "Gruppe duplizieren" duplizieren. Die duplizierte Gruppe behält alle Eigenschaften und erzeugt automatisch eindeutige Ebenennamen.%n• Versteckmodus: Neuer Modus über die Affen-Schaltfläche (🙉/🙈), um mehrere Ebenen schnell auszublenden. Klicken, um zu aktivieren, dann Ebenen anklicken. Zum Anwenden wieder verlassen.%n• Ansicht zentrieren: Zentriert alle Stränge sofort mit der Ziel-Schaltfläche (🎯). Die Leinwandposition wird automatisch so angepasst, dass alles zentriert dargestellt wird.%n• Schnelles Knotenschließen: Rechtsklick auf einen Strang oder verbundenen Strang mit freiem Ende, um den Knoten schnell zu schließen. Das System findet automatisch den nächstgelegenen kompatiblen Strang mit freiem Ende.%n• Neue Sprache – Deutsch (🇩🇪): In den Einstellungen → Sprache ändern kann nun Deutsch ausgewählt werden.%n• Neue Kategorie „Beispiele“: Entdecken Sie Beispielprojekte in Einstellungen → Beispiele. Wählen Sie ein Beispiel; der Dialog schließt sich und das Beispiel wird geladen.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten
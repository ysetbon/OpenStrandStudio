#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.102"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "07_Sep_2025"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_102
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

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchAfterInstall}"; Flags: nowait postinstall skipifsilent

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.102:%n%n• SVG Shape Support: Added new SVG-based shapes (circle, square, triangle) for improved rendering quality and scalability. These shapes now load correctly in both the application and exported executables.%n• Enhanced Canvas Guides: New control point SVG guides for better visual feedback when manipulating canvas elements.%n• Translation improvements for canvas guide elements.%n• Improved color consistency for button explanation titles.%n%nPrevious updates (1.101):%n• Improved Layer Management, Group Duplication, Hide Mode, Center View, Quick Knot Closing%n• New Language - German (🇩🇪)%n• New Samples category%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.102:%n%n• Support des formes SVG : Ajout de nouvelles formes basées sur SVG (cercle, carré, triangle) pour une meilleure qualité de rendu et évolutivité. Ces formes se chargent maintenant correctement dans l'application et les exécutables exportés.%n• Guides de canvas améliorés : Nouveaux guides SVG de points de contrôle pour un meilleur retour visuel lors de la manipulation des éléments du canvas.%n• Améliorations de traduction pour les éléments de guide du canvas.%n• Amélioration de la cohérence des couleurs pour les titres d'explication des boutons.%n%nMises à jour précédentes (1.101):%n• Gestion améliorée des couches, Duplication de groupe, Mode masquage, Centrer la vue, Fermeture rapide de nœud%n• Nouvelle langue - Allemand (🇩🇪)%n• Nouvelle catégorie Exemples%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.102:%n%n• SVG-Formunterstützung: Neue SVG-basierte Formen (Kreis, Quadrat, Dreieck) für verbesserte Renderqualität und Skalierbarkeit. Diese Formen werden jetzt korrekt in der Anwendung und exportierten Executables geladen.%n• Verbesserte Canvas-Hilfslinien: Neue SVG-Kontrollpunkt-Hilfslinien für besseres visuelles Feedback bei der Manipulation von Canvas-Elementen.%n• Übersetzungsverbesserungen für Canvas-Führungselemente.%n• Verbesserte Farbkonsistenz für Schaltflächen-Erklärungstitel.%n%nVorherige Updates (1.101):%n• Verbesserte Ebenenverwaltung, Gruppenduplikation, Versteckmodus, Ansicht zentrieren, Schnelles Knotenschließen%n• Neue Sprache – Deutsch (🇩🇪)%n• Neue Kategorie „Beispiele"%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.102:%n%n• Supporto forme SVG: Aggiunte nuove forme basate su SVG (cerchio, quadrato, triangolo) per una migliore qualità di rendering e scalabilità. Queste forme ora si caricano correttamente sia nell'applicazione che negli eseguibili esportati.%n• Guide canvas migliorate: Nuove guide SVG dei punti di controllo per un migliore feedback visivo durante la manipolazione degli elementi del canvas.%n• Miglioramenti di traduzione per gli elementi guida del canvas.%n• Migliorata coerenza dei colori per i titoli di spiegazione dei pulsanti.%n%nAggiornamenti precedenti (1.101):%n• Gestione livelli migliorata, Duplicazione gruppo, Modalità nascondi, Centra vista, Chiusura rapida del nodo%n• Nuova lingua - Tedesco (🇩🇪)%n• Nuova categoria Esempi%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.102:%n%n• Soporte de formas SVG: Añadidas nuevas formas basadas en SVG (círculo, cuadrado, triángulo) para mejorar la calidad de renderizado y escalabilidad. Estas formas ahora se cargan correctamente tanto en la aplicación como en los ejecutables exportados.%n• Guías de canvas mejoradas: Nuevas guías SVG de puntos de control para mejor retroalimentación visual al manipular elementos del canvas.%n• Mejoras de traducción para elementos de guía del canvas.%n• Mejora en la consistencia de colores para títulos de explicación de botones.%n%nActualizaciones anteriores (1.101):%n• Gestión mejorada de capas, Duplicación de grupo, Modo ocultar, Centrar vista, Cierre rápido de nudo%n• Nuevo idioma - Alemán (🇩🇪)%n• Nueva categoría Ejemplos%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.102:%n%n• Suporte a formas SVG: Adicionadas novas formas baseadas em SVG (círculo, quadrado, triângulo) para melhor qualidade de renderização e escalabilidade. Essas formas agora carregam corretamente tanto no aplicativo quanto nos executáveis exportados.%n• Guias de canvas aprimoradas: Novas guias SVG de pontos de controle para melhor feedback visual ao manipular elementos do canvas.%n• Melhorias de tradução para elementos de guia do canvas.%n• Melhor consistência de cores para títulos de explicação de botões.%n%nAtualizações anteriores (1.101):%n• Gerenciamento de camadas aprimorado, Duplicação de grupo, Modo ocultar, Centralizar visualização, Fechamento rápido de nó%n• Novo idioma - Alemão (🇩🇪)%n• Nova categoria Exemplos%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.102:%n%n• תמיכה בצורות SVG: נוספו צורות חדשות מבוססות SVG (עיגול, ריבוע, משולש) לאיכות רינדור וסקלביליות משופרת. צורות אלו נטענות כעת כראוי גם באפליקציה וגם בקבצי ההפעלה המיוצאים.%n• מדריכי קנבס משופרים: מדריכי SVG חדשים של נקודות בקרה למשוב חזותי טוב יותר בעת טיפול באלמנטים של הקנבס.%n• שיפורי תרגום לאלמנטי הדרכה של הקנבס.%n• עקביות צבעים משופרת לכותרות הסבר של כפתורים.%n%nעדכונים קודמים (1.101):%n• ניהול שכבות משופר, שכפול קבוצה, מצב הסתרה, מרכוז תצוגה, סגירת קשר מהירה%n• שפה חדשה - גרמנית (🇩🇪)%n• קטגוריית דוגמאות חדשה%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

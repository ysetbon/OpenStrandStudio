#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.111"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "19_Sep_2026"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_111
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.111:%n%n• Stylize End Side: Right-click a layer with a free end and pick Stylize End Side, just under Close the Knot. A dialog lets you choose how the strand ends: Straight, Angled, Rounded, Pointed, Notched or Concave. You can also set the tilt and depth, extend or trim the end, and add a side line with its own thickness and color. The preview is live on the canvas. The shadow, side line and masks all follow the new shape. End styles are saved with your project and work with undo and redo.%n• Right Size on Scaled Screens: On high-resolution screens with display scaling turned on, the buttons and text used to look too small. The app now follows your display scale. Toolbar labels no longer get cut off, and the toolbar moves onto two rows when the window is narrow. The layer panel can be dragged narrower than before. The OpenStrand Studio logo now appears on every window and in the taskbar.%n• Dialogs Fit Small Screens: The Settings dialog can now be made smaller, so its Apply and OK buttons always stay on screen. The same goes for Edit Shadow, the group shadow editor, Create Mask Grid, Edit Strand Angles, Change Width and the video player. A dialog never opens larger than your screen, and it keeps the size you give it.%n• Smoother Dragging: The canvas stays sharp while you drag, even on scaled displays or with supersampling on. Move mode shows a closed hand while dragging a point. View mode can now pan with the left mouse button too. The Refresh button's tooltip now says what it does: reload layers and reset the view.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.111:%n%n• Styliser le côté d'extrémité: Faites un clic droit sur un calque ayant une extrémité libre et choisissez Styliser le côté d'extrémité, juste sous Fermer le Nœud. Une boîte de dialogue vous laisse choisir la forme de l'extrémité du brin : Droite, Inclinée, Arrondie, Pointue, Entaillée ou Concave. Vous pouvez aussi régler l'inclinaison et la profondeur, allonger ou raccourcir l'extrémité, et ajouter une ligne latérale avec sa propre épaisseur et sa propre couleur. L'aperçu est en direct sur le canevas. L'ombre, la ligne latérale et les masques suivent tous la nouvelle forme. Les styles d'extrémité sont enregistrés avec votre projet et fonctionnent avec annuler et rétablir.%n• La bonne taille sur les écrans mis à l'échelle: Sur les écrans haute résolution avec une mise à l'échelle de l'affichage, les boutons et le texte paraissaient trop petits. L'application suit désormais l'échelle de votre écran. Les libellés de la barre d'outils ne sont plus coupés, et la barre d'outils passe sur deux lignes quand la fenêtre est étroite. Le panneau des calques peut être réduit plus qu'avant. Le logo OpenStrand Studio apparaît maintenant sur chaque fenêtre et dans la barre des tâches.%n• Des boîtes de dialogue adaptées aux petits écrans: La boîte de dialogue Paramètres peut désormais être réduite, de sorte que ses boutons Appliquer et OK restent toujours à l'écran. Il en va de même pour Modifier l'ombre, l'éditeur d'ombre de groupe, Créer Grille de Masque, Modifier les angles des brins, Changer largeur et le lecteur vidéo. Une boîte de dialogue ne s'ouvre jamais plus grande que votre écran, et elle garde la taille que vous lui donnez.%n• Un glissement plus fluide: Le canevas reste net pendant que vous faites glisser, même sur les écrans mis à l'échelle ou avec le suréchantillonnage activé. Le mode déplacement affiche une main fermée pendant le glissement d'un point. Le mode vue peut maintenant aussi se déplacer avec le bouton gauche de la souris. L'info-bulle du bouton Actualiser indique désormais ce qu'il fait : recharger les calques et réinitialiser la vue.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.111:%n%n• Endseite gestalten: Klicken Sie mit der rechten Maustaste auf eine Ebene mit einem freien Ende und wählen Sie Endseite gestalten, direkt unter Knoten schließen. In einem Dialog wählen Sie, wie der Strang endet: Gerade, Schräg, Abgerundet, Spitz, Eingekerbt oder Konkav. Sie können außerdem Neigung und Tiefe einstellen, das Ende verlängern oder kürzen und eine Seitenlinie mit eigener Dicke und Farbe hinzufügen. Die Vorschau erscheint live auf der Zeichenfläche. Schatten, Seitenlinie und Masken folgen alle der neuen Form. Endstile werden mit dem Projekt gespeichert und funktionieren mit Rückgängig und Wiederherstellen.%n• Richtige Größe auf skalierten Bildschirmen: Auf hochauflösenden Bildschirmen mit aktivierter Anzeigeskalierung wirkten Schaltflächen und Text zu klein. Die App folgt jetzt Ihrer Anzeigeskalierung. Beschriftungen in der Werkzeugleiste werden nicht mehr abgeschnitten, und die Werkzeugleiste wechselt bei schmalen Fenstern auf zwei Zeilen. Das Ebenenpanel lässt sich schmaler ziehen als zuvor. Das OpenStrand Studio Logo erscheint jetzt in jedem Fenster und in der Taskleiste.%n• Dialoge passen auf kleine Bildschirme: Der Dialog Einstellungen kann jetzt verkleinert werden, sodass seine Schaltflächen Übernehmen und OK immer sichtbar bleiben. Dasselbe gilt für Schatten bearbeiten, den Gruppenschatten-Editor, Maskenraster Erstellen, Strangwinkel bearbeiten, Breite ändern und den Videoplayer. Ein Dialog öffnet sich nie größer als Ihr Bildschirm und behält die Größe, die Sie ihm geben.%n• Flüssigeres Ziehen: Die Zeichenfläche bleibt beim Ziehen scharf, auch auf skalierten Bildschirmen oder mit eingeschaltetem Supersampling. Der Verschiebemodus zeigt beim Ziehen eines Punktes eine geschlossene Hand. Der Ansichtsmodus kann jetzt auch mit der linken Maustaste verschoben werden. Der Tooltip der Schaltfläche Aktualisieren sagt jetzt, was sie tut: Ebenen neu laden und Ansicht zurücksetzen.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.111:%n%n• Stilizza il lato finale: Fai clic destro su un livello con un'estremità libera e scegli Stilizza il lato finale, subito sotto Chiudi il Nodo. Una finestra ti permette di scegliere come termina il trefolo: Dritta, Inclinata, Arrotondata, Appuntita, Intagliata o Concava. Puoi anche regolare inclinazione e profondità, allungare o accorciare l'estremità e aggiungere una linea laterale con spessore e colore propri. L'anteprima è dal vivo sulla tela. Ombra, linea laterale e maschere seguono tutte la nuova forma. Gli stili delle estremità vengono salvati con il progetto e funzionano con annulla e ripristina.%n• Dimensione giusta sugli schermi ridimensionati: Sugli schermi ad alta risoluzione con il ridimensionamento attivo, pulsanti e testo apparivano troppo piccoli. L'app ora segue la scala del tuo schermo. Le etichette della barra degli strumenti non vengono più tagliate, e la barra passa su due righe quando la finestra è stretta. Il pannello dei livelli può essere ristretto più di prima. Il logo di OpenStrand Studio appare ora su ogni finestra e nella barra delle applicazioni.%n• Finestre adatte agli schermi piccoli: La finestra Impostazioni ora può essere rimpicciolita, così i pulsanti Applica e OK restano sempre visibili. Lo stesso vale per Modifica ombra, l'editor dell'ombra di gruppo, Crea Griglia Maschera, Modifica Angoli Trefolo, Cambia larghezza e il lettore video. Una finestra non si apre mai più grande dello schermo e mantiene la dimensione che le dai.%n• Trascinamento più fluido: La tela resta nitida mentre trascini, anche su schermi ridimensionati o con il supersampling attivo. La modalità sposta mostra una mano chiusa mentre trascini un punto. La modalità vista ora può scorrere anche con il tasto sinistro del mouse. Il suggerimento del pulsante Aggiorna ora dice cosa fa: ricarica i livelli e reimposta la vista.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.111:%n%n• Estilizar lado del extremo: Haz clic derecho en una capa con un extremo libre y elige Estilizar lado del extremo, justo debajo de Cerrar el Nudo. Un cuadro de diálogo te permite elegir cómo termina el cordón: Recto, Inclinado, Redondeado, Puntiagudo, Con muesca o Cóncavo. También puedes ajustar la inclinación y la profundidad, alargar o recortar el extremo, y añadir una línea lateral con su propio grosor y color. La vista previa es en vivo sobre el lienzo. La sombra, la línea lateral y las máscaras siguen la nueva forma. Los estilos de extremo se guardan con tu proyecto y funcionan con deshacer y rehacer.%n• Tamaño correcto en pantallas escaladas: En pantallas de alta resolución con el escalado activado, los botones y el texto se veían demasiado pequeños. La aplicación ahora sigue la escala de tu pantalla. Las etiquetas de la barra de herramientas ya no se cortan, y la barra pasa a dos filas cuando la ventana es estrecha. El panel de capas se puede estrechar más que antes. El logotipo de OpenStrand Studio aparece ahora en cada ventana y en la barra de tareas.%n• Diálogos que caben en pantallas pequeñas: El diálogo Configuración ahora se puede hacer más pequeño, así sus botones Aplicar y OK siempre quedan en pantalla. Lo mismo ocurre con Editar sombra, el editor de sombra de grupo, Crear Cuadrícula de Máscara, Editar Ángulos del Cordón, Cambiar ancho y el reproductor de video. Un diálogo nunca se abre más grande que tu pantalla, y conserva el tamaño que le das.%n• Arrastre más suave: El lienzo se mantiene nítido mientras arrastras, incluso en pantallas escaladas o con el supermuestreo activado. El modo mover muestra una mano cerrada mientras arrastras un punto. El modo vista ahora también puede desplazarse con el botón izquierdo del ratón. La descripción del botón Actualizar ahora dice lo que hace: recargar las capas y restablecer la vista.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.111:%n%n• Estilizar lado da extremidade: Clique com o botão direito numa camada com uma extremidade livre e escolha Estilizar lado da extremidade, logo abaixo de Fechar o Nó. Uma janela permite escolher como a mecha termina: Reta, Inclinada, Arredondada, Pontiaguda, Entalhada ou Côncava. Também pode ajustar a inclinação e a profundidade, alongar ou encurtar a extremidade e adicionar uma linha lateral com espessura e cor próprias. A pré-visualização é ao vivo na tela. A sombra, a linha lateral e as máscaras seguem todas a nova forma. Os estilos de extremidade são salvos com o projeto e funcionam com desfazer e refazer.%n• Tamanho certo em ecrãs com escala: Em ecrãs de alta resolução com a escala de exibição ativada, os botões e o texto pareciam pequenos demais. A aplicação agora segue a escala do seu ecrã. Os rótulos da barra de ferramentas já não são cortados, e a barra passa para duas linhas quando a janela é estreita. O painel de camadas pode ser estreitado mais do que antes. O logótipo do OpenStrand Studio aparece agora em todas as janelas e na barra de tarefas.%n• Janelas que cabem em ecrãs pequenos: A janela Configurações agora pode ser reduzida, para que os botões Aplicar e OK fiquem sempre visíveis. O mesmo vale para Editar sombra, o editor de sombra de grupo, Criar Grade de Máscara, Editar Ângulos da Mecha, Mudar largura e o reprodutor de vídeo. Uma janela nunca abre maior do que o seu ecrã e mantém o tamanho que lhe der.%n• Arrasto mais suave: A tela permanece nítida enquanto arrasta, mesmo em ecrãs com escala ou com a superamostragem ativada. O modo mover mostra uma mão fechada enquanto arrasta um ponto. O modo de visualização agora também pode deslocar-se com o botão esquerdo do rato. A dica do botão Atualizar agora diz o que ele faz: recarregar as camadas e redefinir a vista.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.111:%n%n• עיצוב צד הקצה: לחצו לחיצה ימנית על שכבה עם קצה חופשי ובחרו עיצוב צד הקצה, ממש מתחת לסגור את הקשר. חלון דו-שיח מאפשר לבחור איך החוט מסתיים: ישר, משופע, מעוגל, מחודד, חרוץ או קעור. אפשר גם לכוון את ההטיה והעומק, להאריך או לקצר את הקצה, ולהוסיף קו צד עם עובי וצבע משלו. התצוגה המקדימה חיה על הקנבס. הצל, קו הצד והמסכות עוקבים כולם אחרי הצורה החדשה. סגנונות הקצה נשמרים עם הפרויקט ועובדים עם ביטול וביצוע מחדש.%n• גודל נכון במסכים עם קנה מידה: במסכים ברזולוציה גבוהה עם קנה מידה של התצוגה מופעל, הכפתורים והטקסט נראו קטנים מדי. האפליקציה עוקבת כעת אחרי קנה המידה של המסך שלכם. תוויות סרגל הכלים כבר לא נחתכות, וסרגל הכלים עובר לשתי שורות כשהחלון צר. את לוח השכבות אפשר לגרור צר יותר מבעבר. הלוגו של OpenStrand Studio מופיע כעת בכל חלון ובשורת המשימות.%n• חלונות שמתאימים למסכים קטנים: את חלון ההגדרות אפשר כעת להקטין, כך שכפתורי החל ואישור נשארים תמיד על המסך. כך גם עריכת צל, עורך הצל של הקבוצה, צור רשת מסכות, ערוך זוויות חוט, שנה רוחב ונגן הווידאו. חלון לעולם לא נפתח גדול מהמסך שלכם, והוא שומר על הגודל שנתתם לו.%n• גרירה חלקה יותר: הקנבס נשאר חד בזמן הגרירה, גם במסכים עם קנה מידה או עם דגימת-יתר מופעלת. מצב הזזה מציג יד סגורה בזמן גרירת נקודה. מצב תצוגה יכול כעת להזיז את התצוגה גם עם הכפתור השמאלי של העכבר. הטיפ של כפתור הרענון אומר כעת מה הוא עושה: טוען מחדש שכבות ומאפס את התצוגה.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

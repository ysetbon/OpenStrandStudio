#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.100"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "22_June_2025"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_100
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.100:%n%n• Strand Width Control: You can now dynamically adjust the width of individual strands, giving you more flexibility in creating varied knot designs.%n• Zoom In/Out: You can zoom in and out of your design to see small details or the entire diagram.%n• Pan Screen: You can move the canvas by clicking the hand button, which helps when working on larger diagrams.%n• Initial Setup: When first starting the application, you'll need to click "New Strand" to begin creating your first strand.%n• General Fixes: Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation
french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.100:%n%n• Contrôle de la largeur des brins : Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.%n• Zoom avant/arrière : Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.%n• Déplacement de l'écran : Vous pouvez déplacer le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.%n• Configuration initiale : Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.%n• Corrections générales : Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.100:%n%n• Controllo della larghezza dei trefoli: Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.%n• Zoom avanti/indietro: Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.%n• Spostamento schermo: Puoi spostare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.%n• Configurazione iniziale: Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.%n• Correzioni generali: Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.100:%n%n• Control del ancho de las hebras: Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.%n• Zoom acercar/alejar: Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.%n• Mover pantalla: Puedes mover el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.%n• Configuración inicial: Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.%n• Correcciones generales: Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.100:%n%n• Controle de largura dos fios: Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.%n• Zoom ampliar/reduzir: Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.%n• Mover tela: Você pode mover o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.%n• Configuração inicial: Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.%n• Correções gerais: Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.100:%n%n• שינוי רוחב חוטים: עכשיו אפשר לשנות את העובי של כל חוט בנפרד, כך שתוכלו ליצור עיצובים יותר מגוונים.%n• הגדלה והקטנה: אפשר להתקרב ולהתרחק מהעיצוב שלכם כדי לראות פרטים קטנים או את כל הדיאגרמה.%n• הזזת המסך: אפשר להזיז את הקנבס על ידי לחיצה על כפתור היד, מה שעוזר בעבודה על דיאגרמות גדולות יותר.%n• התחלת עבודה: כשפותחים את התוכנה בפעם הראשונה, צריך ללחוץ על "חוט חדש" כדי להתחיל לצייר.%n• תיקונים כלליים: תוקנו מספר תקלות ובעיות שנגרמו מגרסאות קודמות, כמו למשל כפתורי ביטול וחזרה יצרו חלון זמני ולא סיפקו חווית משתמש חלקה.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה
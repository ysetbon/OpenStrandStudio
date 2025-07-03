#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.100"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "3_July_2025"
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.100:%n%n• Strand Width Control: You can now dynamically adjust the width of individual strands, giving you more flexibility in creating varied knot designs.%n• Zoom In/Out: You can zoom in and out of your design to see small details or the entire diagram.%n• Pan Screen: You can drag the canvas by clicking the hand button, which helps when working on larger diagrams.%n• Shadow-Only Mode: You can now hide a layer while still showing its shadows and highlights by right-clicking on a layer button and selecting "Shadow Only". This helps visualize shadow effects without the visual clutter.%n• Initial Setup: When first starting the application, you'll need to click "New Strand" to begin creating your first strand.%n• General Fixes: Fixed several bugs and issues from previous versions, such as undo/redo buttons creating temporary windows and not providing a smooth user experience.%n• Higher Quality Rendering: Improved canvas display quality and 4x higher resolution image export for crisp, professional results.%n• Removed Extended Mask Option: The extended mask option from the general layer has been removed since it was only needed as a backup for shader issues in older versions (1.09x). With greatly improved shading, this option is no longer necessary.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation
french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.100:%n%n• Contrôle de la largeur des brins : Vous pouvez maintenant ajuster dynamiquement la largeur de chaque brin individuellement, offrant plus de flexibilité dans la création de designs de nœuds variés.%n• Zoom avant/arrière : Vous pouvez zoomer et dézoomer sur votre création pour voir les petits détails ou l'ensemble du diagramme.%n• Déplacement de l'écran : Vous pouvez faire glisser le canevas en cliquant sur le bouton main, ce qui aide lors du travail sur des diagrammes plus grands.%n• Mode ombre uniquement : Vous pouvez maintenant masquer une couche tout en affichant ses ombres et reflets en faisant un clic droit sur un bouton de couche et en sélectionnant "Ombre uniquement". Cela aide à visualiser les effets d'ombre sans l'encombrement visuel.%n• Configuration initiale : Au premier démarrage de l'application, vous devrez cliquer sur "Nouveau Brin" pour commencer à créer votre premier brin.%n• Corrections générales : Correction de plusieurs bugs et problèmes des versions précédentes, comme les boutons annuler/refaire qui créaient des fenêtres temporaires et ne fournissaient pas une expérience utilisateur fluide.%n• Rendu de qualité supérieure : Amélioration de la qualité d'affichage du canevas et export d'images en résolution 4x plus élevée pour des résultats nets et professionnels.%n• Suppression de l'option masque étendu : L'option masque étendu de la couche générale a été supprimée car elle était uniquement nécessaire comme solution de secours pour les problèmes de shader dans les anciennes versions (1.09x). Avec l'ombrage grandement amélioré, cette option n'est plus nécessaire.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.100:%n%n• Controllo della larghezza dei trefoli: Ora puoi regolare dinamicamente la larghezza dei singoli trefoli, offrendo maggiore flessibilità nella creazione di design di nodi variati.%n• Zoom avanti/indietro: Puoi ingrandire e rimpicciolire il tuo design per vedere piccoli dettagli o l'intero diagramma.%n• Spostamento schermo: Puoi trascinare il canvas cliccando il pulsante mano, che aiuta quando si lavora su diagrammi più grandi.%n• Modalità solo ombra: Ora puoi nascondere un livello pur mostrando le sue ombre e luci facendo clic destro su un pulsante livello e selezionando "Solo Ombra". Questo aiuta a visualizzare gli effetti ombra senza il disordine visivo.%n• Configurazione iniziale: Al primo avvio dell'applicazione, dovrai cliccare su "Nuovo Trefolo" per iniziare a creare il tuo primo trefolo.%n• Correzioni generali: Corretti diversi bug e problemi dalle versioni precedenti, come i pulsanti annulla/ripeti che creavano finestre temporanee e non fornivano un'esperienza utente fluida.%n• Rendering di qualità superiore: Migliorata la qualità di visualizzazione del canvas e esportazione immagini con risoluzione 4x più alta per risultati nitidi e professionali.%n• Rimossa opzione maschera estesa: L'opzione maschera estesa dal livello generale è stata rimossa poiché era necessaria solo come backup per problemi di shader nelle versioni precedenti (1.09x). Con l'ombreggiatura notevolmente migliorata, questa opzione non è più necessaria.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.100:%n%n• Control del ancho de las hebras: Ahora puedes ajustar dinámicamente el ancho de hebras individuales, dándote más flexibilidad en la creación de diseños de nudos variados.%n• Zoom acercar/alejar: Puedes acercar y alejar tu diseño para ver pequeños detalles o todo el diagrama.%n• Mover pantalla: Puedes arrastrar el lienzo haciendo clic en el botón de mano, lo que ayuda al trabajar en diagramas más grandes.%n• Modo solo sombra: Ahora puedes ocultar una capa mientras sigues mostrando sus sombras y luces haciendo clic derecho en un botón de capa y seleccionando "Solo Sombra". Esto ayuda a visualizar los efectos de sombra sin el desorden visual.%n• Configuración inicial: Al iniciar la aplicación por primera vez, deberás hacer clic en "Nueva Hebra" para empezar a crear tu primera hebra.%n• Correcciones generales: Se corrigieron varios errores y problemas de versiones anteriores, como los botones deshacer/rehacer que creaban ventanas temporales y no proporcionaban una experiencia de usuario fluida.%n• Renderizado de mayor calidad: Mejora en la calidad de visualización del lienzo y exportación de imágenes con resolución 4x más alta para resultados nítidos y profesionales.%n• Eliminada opción de máscara extendida: La opción de máscara extendida de la capa general ha sido eliminada ya que solo era necesaria como respaldo para problemas de shader en versiones anteriores (1.09x). Con el sombreado considerablemente mejorado, esta opción ya no es necesaria.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.100:%n%n• Controle de largura dos fios: Agora você pode ajustar dinamicamente a largura de fios individuais, proporcionando mais flexibilidade na criação de designs de nós variados.%n• Zoom ampliar/reduzir: Você pode ampliar e reduzir seu design para ver pequenos detalhes ou todo o diagrama.%n• Mover tela: Você pode arrastar o canvas clicando no botão de mão, o que ajuda ao trabalhar em diagramas maiores.%n• Modo apenas sombra: Agora você pode ocultar uma camada enquanto ainda mostra suas sombras e destaques clicando com o botão direito em um botão de camada e selecionando "Apenas Sombra". Isso ajuda a visualizar efeitos de sombra sem a desordem visual.%n• Configuração inicial: Ao iniciar o aplicativo pela primeira vez, você precisará clicar em "Novo Fio" para começar a criar seu primeiro fio.%n• Correções gerais: Corrigidos vários bugs e problemas de versões anteriores, como os botões desfazer/refazer que criavam janelas temporárias e não forneciam uma experiência de usuário fluida.%n• Renderização de qualidade superior: Melhoria na qualidade de exibição do canvas e exportação de imagens com resolução 4x mais alta para resultados nítidos e profissionais.%n• Removida opção de máscara estendida: A opção de máscara estendida da camada geral foi removida pois era necessária apenas como backup para problemas de shader em versões antigas (1.09x). Com o sombreamento muito melhorado, esta opção não é mais necessária.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.100:%n%n• שינוי רוחב חוטים: עכשיו אפשר לשנות את העובי של כל חוט בנפרד, כך שתוכלו ליצור עיצובים יותר מגוונים.%n• הגדלה והקטנה: אפשר להתקרב ולהתרחק מהעיצוב שלכם כדי לראות פרטים קטנים או את כל הדיאגרמה.%n• הזזת המסך: אפשר לגרור את הקנבס על ידי לחיצה על כפתור היד, מה שעוזר בעבודה על דיאגרמות גדולות יותר.%n• מצב צל בלבד: עכשיו אפשר להסתיר שכבה תוך הצגת הצללים וההדגשות שלה על ידי לחיצה ימנית על כפתור שכבה ובחירת "צל בלבד". זה עוזר להמחיש אפקטי צל ללא העומס החזותי.%n• התחלת עבודה: כשפותחים את התוכנה בפעם הראשונה, צריך ללחוץ על "חוט חדש" כדי להתחיל לצייר.%n• תיקונים כלליים: תוקנו מספר תקלות ובעיות שנגרמו מגרסאות קודמות, כמו למשל כפתורי ביטול וחזרה יצרו חלון זמני ולא סיפקו חווית משתמש חלקה.%n• איכות תצוגה משופרת: שיפור באיכות תצוגת הקנבס ויצוא תמונות ברזולוציה גבוהה פי 4 לתוצאות חדות ומקצועיות.%n• הסרת אפשרות מסכה מורחבת: האפשרות למסכה מורחבת בשכבה הכללית הוסרה מכיוון שהיא הייתה נחוצה רק כגיבוי לבעיות shader בגרסאות קודמות (1.09x). עם שיפור ההצללה באופן משמעותי, אפשרות זו אינה נחוצה עוד.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה
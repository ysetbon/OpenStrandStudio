#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.107"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "31_Jan_2026"
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.107:%n%n• Hover Highlights in Attach, Move, and Select Modes: Points and strands now highlight in yellow when hovering, making it clear what will be selected or moved when you click.%n• View Mode: New "look only" mode for safely navigating your design. Pan and zoom without accidentally selecting or editing.%n• Delete All Button: Added a "Delete All" button in the layer panel to quickly remove all strands at once.%n• Crash Log: Added automatic crash logging to help identify and fix bugs in future updates.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.107:%n%n• Surbrillance au survol dans les modes Attacher, Déplacer et Sélection: Les points et brins sont maintenant mis en surbrillance en jaune au survol, indiquant clairement ce qui sera sélectionné ou déplacé.%n• Mode Visualisation: Nouveau mode "lecture seule" pour naviguer en toute sécurité. Déplacez-vous et zoomez sans modifier accidentellement.%n• Bouton Tout Supprimer: Ajout d'un bouton "Tout Supprimer" dans le panneau des calques.%n• Journal des Plantages: Ajout d'un journal automatique des plantages pour les futures mises à jour.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.107:%n%n• Hervorhebung beim Überfahren in Anhänge-, Verschiebe- und Auswahlmodi: Punkte und Stränge werden gelb hervorgehoben, sodass klar erkennbar ist, was beim Klicken ausgewählt oder verschoben wird.%n• Ansichtsmodus: Neuer "Nur-Ansicht"-Modus zum sicheren Navigieren. Schwenken und zoomen Sie ohne versehentliche Änderungen.%n• Alles Löschen Schaltfläche: Eine "Alles Löschen"-Schaltfläche wurde im Ebenenbedienfeld hinzugefügt.%n• Absturzprotokoll: Automatische Absturzprotokollierung für zukünftige Updates hinzugefügt.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.107:%n%n• Evidenziazione al passaggio del mouse nei modi Attacca, Sposta e Selezione: I punti e i trefoli ora si evidenziano in giallo al passaggio del mouse, rendendo chiaro cosa verrà selezionato o spostato quando si clicca.%n• Modalità Visualizzazione: Nuova modalità "solo visualizzazione" per navigare in sicurezza nel tuo progetto. Scorri e zooma senza selezionare o modificare accidentalmente.%n• Pulsante Elimina Tutto: Aggiunto un pulsante "Elimina Tutto" nel pannello dei livelli per rimuovere rapidamente tutti i trefoli.%n• Registro degli Arresti: Aggiunta la registrazione automatica degli arresti anomali per aiutare a identificare e correggere i bug nei futuri aggiornamenti.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.107:%n%n• Resaltado al pasar el cursor en modos Adjuntar, Mover y Selección: Los puntos y hebras ahora se resaltan en amarillo al pasar el cursor, dejando claro qué se seleccionará o moverá al hacer clic.%n• Modo Visualización: Nuevo modo "solo ver" para navegar su diseño de forma segura. Desplácese y haga zoom sin seleccionar o editar accidentalmente.%n• Botón Eliminar Todo: Se agregó un botón "Eliminar Todo" en el panel de capas para eliminar rápidamente todas las hebras.%n• Registro de Fallos: Se agregó registro automático de fallos para ayudar a identificar y corregir errores en futuras actualizaciones.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.107:%n%n• Destaque ao passar o cursor nos modos Anexar, Mover e Seleção: Os pontos e mechas agora são destacados em amarelo ao passar o cursor, tornando claro o que será selecionado ou movido ao clicar.%n• Modo Visualização: Novo modo "apenas visualizar" para navegar seu design com segurança. Mova e amplie sem selecionar ou editar acidentalmente.%n• Botão Excluir Tudo: Adicionado um botão "Excluir Tudo" no painel de camadas para remover rapidamente todas as mechas.%n• Registro de Falhas: Adicionado registro automático de falhas para ajudar a identificar e corrigir bugs em futuras atualizações.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.107:%n%n• הדגשת ריחוף במצבי חיבור, הזזה ובחירה: נקודות וחוטים מודגשים כעת בצהוב בעת ריחוף, כך שברור מה ייבחר או יוזז בלחיצה.%n• מצב צפייה: מצב "צפייה בלבד" חדש לניווט בטוח בעיצוב שלך. גלול והגדל בלי לבחור או לערוך בטעות.%n• כפתור מחק הכל: נוסף כפתור "מחק הכל" בפאנל השכבות להסרה מהירה של כל החוטים.%n• יומן קריסות: נוספה רישום אוטומטי של קריסות לזיהוי ותיקון באגים בעדכונים עתידיים.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

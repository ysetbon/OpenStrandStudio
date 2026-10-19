#define MyAppName "OpenStrand Studio"
#define MyAppVersion "2.1"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "19_Oct_2026"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_2_1
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
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "swedish"; MessagesFile: "compiler:Languages\Swedish.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
Source: "{#ExePath}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion solidbreak
Source: "{#SourcePath}\box_stitch.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\settings_icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\flags\*.png"; DestDir: "{app}\flags"; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\layer_panel_icons\*.png"; DestDir: "{app}\layer_panel_icons"; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\guide_images\levels_masks\*.png"; DestDir: "{app}\guide_images\levels_masks"; Flags: ignoreversion recursesubdirs
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 2.1:%n%n• Interface Sounds: Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.%n• Rotate Mode Triangles and Dial: Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.%n• Fixes: Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 2.1:%n%n• Sons de l'interface: Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol.%n• Triangles et cadran en mode Pivoter: Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez.%n• Corrections: Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 2.1:%n%n• Oberflächenklänge: Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.%n• Dreiecke und Skala im Modus Drehen: Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.%n• Fehlerbehebungen: Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 2.1:%n%n• Suoni dell'interfaccia: Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse.%n• Triangoli e quadrante in modalità Ruota: Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci.%n• Correzioni: Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 2.1:%n%n• Sonidos de la interfaz: Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.%n• Triángulos y dial en el modo Rotar: Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.%n• Correcciones: Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 2.1:%n%n• Sons da interface: Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.%n• Triângulos e mostrador no modo Girar: Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.%n• Correções: As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 2.1:%n%n• צלילי ממשק: כל כפתור, תפריט, לשונית ורשימה משמיעים עכשיו צליל קצר, ולכל מצב יש צליל משלו כשמפעילים ומכבים אותו. לכל אזור באפליקציה יש צליל רך משלו במעבר עכבר. במצב סיבוב נשמע צליל כשתופסים ומשחררים קצה של חוט, ותקתוק בכל סימון על החוגה. בתחתית ההגדרות הכלליות, השתמשו ב״השמע צלילי ממשק״, ״עוצמת הצלילים״ ו״השמע צלילים במעבר עכבר״ כדי לכבות את הצלילים, לשנות את עוצמתם או לכבות רק את צלילי מעבר העכבר.%n• משולשים וחוגה במצב סיבוב: משולשים מסמנים עכשיו כל קצה חוט שאפשר לסובב: אדום בתחילת חוט, כחול בסופו וצהוב מתחת לסמן. בזמן הגרירה מופיעה סביב נקודת הציר חוגה עם סימון כל 15°, שצובעת כמה סובבתם. בתוך החוגה הקצה מסתובב לאט יותר, לכוונון עדין. עותק דהוי של החוט נשאר במקום שבו התחיל עד שמשחררים.%n• תיקונים: קצוות של חוטים כבר לא מתקפלים לאחור על עצמם כשהשפעת נקודת הבקרה גבוהה. חוט כבר לא מאבד את הצל שלו במקום שבו מסכה נוגעת בו רק לאורך קצה. שחרור חוט מהיר יותר כשהצללים כבויים.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

russian.WelcomeLabel2=Эта программа установит [name/ver] на ваш компьютер.%n%nЧто нового в версии 2.1:%n%n• Звуки интерфейса: Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.%n• Треугольники и шкала в режиме «Вращать»: Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.%n• Исправления: Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.%n%nПрограмму создал Йонатан Сетбон. Связаться со мной можно по адресу ysetbon@gmail.com.%n%nРекомендуется закрыть все остальные приложения, прежде чем продолжить.
russian.LaunchAfterInstall=Запустить {#MyAppName} после установки

finnish.WelcomeLabel2=Tämä asentaa [name/ver] tietokoneellesi.%n%nMitä uutta versiossa 2.1:%n%n• Käyttöliittymän äänet: Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.%n• Kolmiot ja asteikko Kierrä-tilassa: Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.%n• Korjaukset: Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.%n%nOhjelman on tehnyt Yonatan Setbon. Voit ottaa minuun yhteyttä osoitteessa ysetbon@gmail.com.%n%nOn suositeltavaa sulkea kaikki muut sovellukset ennen jatkamista.
finnish.LaunchAfterInstall=Käynnistä {#MyAppName} asennuksen jälkeen

swedish.WelcomeLabel2=Detta installerar [name/ver] på din dator.%n%nNyheter i version 2.1:%n%n• Gränssnittsljud: Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.%n• Trianglar och skala i läget Rotera: Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.%n• Åtgärdade fel: Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.%n%nProgrammet kommer från Yonatan Setbon. Du kan kontakta mig på ysetbon@gmail.com.%n%nDet rekommenderas att du stänger alla andra program innan du fortsätter.
swedish.LaunchAfterInstall=Starta {#MyAppName} efter installationen

japanese.WelcomeLabel2=このプログラムは [name/ver] をお使いのコンピューターにインストールします。%n%nバージョン 2.1 の新機能:%n%n• インターフェース音: すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。%n• 回転モードの三角形とダイヤル: 回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。%n• 修正: 制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。%n%nこのプログラムは Yonatan Setbon が提供しています。ysetbon@gmail.com までご連絡ください。%n%n続行する前に、他のすべてのアプリケーションを閉じることをお勧めします。
japanese.LaunchAfterInstall=インストール後に {#MyAppName} を起動する

chinese.WelcomeLabel2=本程序将在您的计算机上安装 [name/ver]。%n%n版本 2.1 的新功能:%n%n• 界面音效: 每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。%n• 旋转模式的三角形和表盘: 现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。%n• 修复: 控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。%n%n本程序由 Yonatan Setbon 提供。您可以通过 ysetbon@gmail.com 联系我。%n%n建议您在继续之前关闭所有其他应用程序。
chinese.LaunchAfterInstall=安装后启动 {#MyAppName}

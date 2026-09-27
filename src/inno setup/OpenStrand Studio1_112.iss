#define MyAppName "OpenStrand Studio"
#define MyAppVersion "1.112"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "27_Sep_2026"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_1_112
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 1.112:%n%n• Better Shadows Around Masks: Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.%n• Hidden Shadows Stay Hidden: When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.%n• Seven New Samples: In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 1.112:%n%n• De plus belles ombres autour des masques: Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas.%n• Les ombres masquées restent masquées: Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible.%n• Sept nouveaux exemples: Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 1.112:%n%n• Bessere Schatten an Masken: Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet.%n• Ausgeblendete Schatten bleiben ausgeblendet: Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen.%n• Sieben neue Beispiele: In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 1.112:%n%n• Ombre migliori intorno alle maschere: Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna.%n• Le ombre nascoste restano nascoste: Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile.%n• Sette nuovi esempi: In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 1.112:%n%n• Mejores sombras alrededor de las máscaras: Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo.%n• Las sombras ocultas siguen ocultas: Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible.%n• Siete ejemplos nuevos: En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 1.112:%n%n• Sombras melhores à volta das máscaras: Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha.%n• Sombras ocultas continuam ocultas: Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível.%n• Sete novos exemplos: Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 1.112:%n%n• צללים טובים יותר סביב מסכות: במקום שבו מסכה מעבירה חוט אחד מעל חוט אחר, הצללים נראים עכשיו בדיוק כמו בהצטלבות אמיתית. הטריזים הכהים, הבליטות והשקעים המיותרים ליד מסכות נעלמו, והחוט המורם נשאר נקי. התצוגה המקדימה נתיב צל בעורך הצללים מציגה עכשיו בדיוק את מה שמצויר על הקנבס.%n• צללים מוסתרים נשארים מוסתרים: כשמבטלים את הסימון של צל בעורך הצללים, הוא נעלם עכשיו לגמרי. קודם יכלה להישאר בליטה אפורה קטנה ליד חוט אחר. גם יצירת מסכה כבר לא מסתירה צל שצריך להישאר גלוי.%n• שבע דוגמאות חדשות: בהגדרות, תחת דוגמאות, יש שבעה פרויקטים חדשים לפתוח וללמוד מהם: אריגה ישרה 12×12, אריגה מעוקלת 6×6, צמה שטוחה, עבה ודק, גשר, זוגות מפותלים ואריגת קגומה. כפתורי הדוגמאות מסודרים עכשיו שניים בשורה, כך שכל הרשימה נכנסת בעמוד.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

russian.WelcomeLabel2=Эта программа установит [name/ver] на ваш компьютер.%n%nЧто нового в версии 1.112:%n%n• Лучшие тени у масок: там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.%n• Скрытые тени остаются скрытыми: если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.%n• Семь новых примеров: в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.%n%nПрограмму создал Йонатан Сетбон. Связаться со мной можно по адресу ysetbon@gmail.com.%n%nРекомендуется закрыть все остальные приложения, прежде чем продолжить.
russian.LaunchAfterInstall=Запустить {#MyAppName} после установки

finnish.WelcomeLabel2=Tämä asentaa [name/ver] tietokoneellesi.%n%nMitä uutta versiossa 1.112:%n%n• Paremmat varjot maskien ympärillä: kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.%n• Piilotetut varjot pysyvät piilossa: kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.%n• Seitsemän uutta esimerkkiä: asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.%n%nOhjelman on tehnyt Yonatan Setbon. Voit ottaa minuun yhteyttä osoitteessa ysetbon@gmail.com.%n%nOn suositeltavaa sulkea kaikki muut sovellukset ennen jatkamista.
finnish.LaunchAfterInstall=Käynnistä {#MyAppName} asennuksen jälkeen

swedish.WelcomeLabel2=Detta installerar [name/ver] på din dator.%n%nNyheter i version 1.112:%n%n• Bättre skuggor kring masker: där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.%n• Dolda skuggor förblir dolda: när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.%n• Sju nya exempel: i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.%n%nProgrammet kommer från Yonatan Setbon. Du kan kontakta mig på ysetbon@gmail.com.%n%nDet rekommenderas att du stänger alla andra program innan du fortsätter.
swedish.LaunchAfterInstall=Starta {#MyAppName} efter installationen

japanese.WelcomeLabel2=このプログラムは [name/ver] をお使いのコンピューターにインストールします。%n%nバージョン 1.112 の新機能:%n%n• マスクまわりの影がきれいに: マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。%n• 非表示の影はきちんと非表示に: 影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。%n• 7つの新しいサンプル: 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。%n%nこのプログラムは Yonatan Setbon が提供しています。ysetbon@gmail.com までご連絡ください。%n%n続行する前に、他のすべてのアプリケーションを閉じることをお勧めします。
japanese.LaunchAfterInstall=インストール後に {#MyAppName} を起動する

chinese.WelcomeLabel2=本程序将在您的计算机上安装 [name/ver]。%n%n版本 1.112 的新功能:%n%n• 遮罩周围的阴影更好看: 在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。%n• 隐藏的阴影保持隐藏: 在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。%n• 七个新示例: 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。%n%n本程序由 Yonatan Setbon 提供。您可以通过 ysetbon@gmail.com 联系我。%n%n建议您在继续之前关闭所有其他应用程序。
chinese.LaunchAfterInstall=安装后启动 {#MyAppName}

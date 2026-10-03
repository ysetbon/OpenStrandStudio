#define MyAppName "OpenStrand Studio"
#define MyAppVersion "2.0"
#define MyAppPublisher "Yonatan Setbon"
#define MyAppExeName "OpenStrandStudio.exe"
#define MyAppDate "04_Oct_2026"
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
OutputBaseFilename=OpenStrandStudioSetup_{#MyAppDate}_2_0
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
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nWhat's New in Version 2.0:%n%nWhy 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.%n%n• Strands and Masks Tabs: The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.%n• Fixed Shadow Issues: Fixed shadow issues from older versions. Shadows for masks now behave more naturally.%n• Seven New Samples: In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.
english.LaunchAfterInstall=Launch {#MyAppName} after installation

french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version 2.0:%n%nPourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.%n%n• Onglets Brins et Masques: La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous.%n• Ombres corrigées: Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle.%n• Sept nouveaux exemples: Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.
french.LaunchAfterInstall=Lancer {#MyAppName} après l'installation

german.WelcomeLabel2=Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version 2.0:%n%nWarum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.%n%n• Tabs Stränge und Masken: Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.%n• Schattenprobleme behoben: Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.%n• Sieben neue Beispiele: In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.
german.LaunchAfterInstall={#MyAppName} nach der Installation starten

italian.WelcomeLabel2=Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione 2.0:%n%nPerché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.%n%n• Schede Trefoli e Maschere: L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi.%n• Problemi delle ombre risolti: Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.%n• Sette nuovi esempi: In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina.%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.
italian.LaunchAfterInstall=Avvia {#MyAppName} dopo l'installazione

spanish.WelcomeLabel2=Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión 2.0:%n%n¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.%n%n• Pestañas Cordones y Máscaras: La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.%n• Problemas de sombras corregidos: Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.%n• Siete ejemplos nuevos: En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.
spanish.LaunchAfterInstall=Iniciar {#MyAppName} después de la instalación

portuguese.WelcomeLabel2=Isto instalará [name/ver] no seu computador.%n%nNovidades da versão 2.0:%n%nPorquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.%n%n• Separadores Mechas e Máscaras: A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.%n• Problemas de sombras corrigidos: Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.%n• Sete novos exemplos: Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.
portuguese.LaunchAfterInstall=Iniciar {#MyAppName} após a instalação

hebrew.WelcomeLabel2=פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה 2.0:%n%nלמה 2.0? המסכות מרגישות עכשיו הרבה יותר טבעיות לשימוש. אריגה היא מרכיב מרכזי בקשירת קשרים, ומסכות הן חלק גדול מהאריגה, ולכן זהו צעד משמעותי עבור OpenStrand Studio.%n%n• לשוניות חוטים ומסכות: רשימת השכבות מחולקת עכשיו לשתי לשוניות, חוטים ומסכות, עם מתג ממש מעל צייר שמות. בלשונית מסכות יש כפתורים משלה: מסכה חדשה, מחק מסכה, בטל בחירה ומחק הכל, והכפתור מסכה חדשה מחליף את כפתור המסכה בסרגל הכלים. מחק הכל בלשונית הזו מוחקת רק את המסכות, אחרי אישור, ובשלב ביטול אחד. המסכות נשארות תמיד מעל כל החוטים, ולכן מיקומן ברשימה כבר לא משנה, ובחירת שכבה מהלשונית השנייה פותחת אותה אוטומטית.%n• תיקוני צללים: תוקנו בעיות צללים מגרסאות קודמות. הצללים של מסכות מתנהגים עכשיו בצורה טבעית יותר.%n• שבע דוגמאות חדשות: בהגדרות, תחת דוגמאות, יש שבעה פרויקטים חדשים לפתוח וללמוד מהם: אריגה ישרה 12×12, אריגה מעוקלת 6×6, צמה שטוחה, עבה ודק, גשר, זוגות מפותלים ואריגת קגומה. כפתורי הדוגמאות מסודרים עכשיו שניים בשורה, כך שכל הרשימה נכנסת בעמוד.%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.
hebrew.LaunchAfterInstall=הפעל את {#MyAppName} לאחר ההתקנה

russian.WelcomeLabel2=Эта программа установит [name/ver] на ваш компьютер.%n%nЧто нового в версии 2.0:%n%nПочему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.%n%n• Вкладки «Пряди» и «Маски»: Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.%n• Исправлены проблемы с тенями: Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.%n• Семь новых примеров: в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.%n%nПрограмму создал Йонатан Сетбон. Связаться со мной можно по адресу ysetbon@gmail.com.%n%nРекомендуется закрыть все остальные приложения, прежде чем продолжить.
russian.LaunchAfterInstall=Запустить {#MyAppName} после установки

finnish.WelcomeLabel2=Tämä asentaa [name/ver] tietokoneellesi.%n%nMitä uutta versiossa 2.0:%n%nMiksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.%n%n• Säikeet- ja Maskit-välilehdet: Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.%n• Varjo-ongelmat korjattu: Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.%n• Seitsemän uutta esimerkkiä: asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.%n%nOhjelman on tehnyt Yonatan Setbon. Voit ottaa minuun yhteyttä osoitteessa ysetbon@gmail.com.%n%nOn suositeltavaa sulkea kaikki muut sovellukset ennen jatkamista.
finnish.LaunchAfterInstall=Käynnistä {#MyAppName} asennuksen jälkeen

swedish.WelcomeLabel2=Detta installerar [name/ver] på din dator.%n%nNyheter i version 2.0:%n%nVarför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.%n%n• Flikarna Strängar och Masker: Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.%n• Skuggproblem åtgärdade: Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.%n• Sju nya exempel: i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.%n%nProgrammet kommer från Yonatan Setbon. Du kan kontakta mig på ysetbon@gmail.com.%n%nDet rekommenderas att du stänger alla andra program innan du fortsätter.
swedish.LaunchAfterInstall=Starta {#MyAppName} efter installationen

japanese.WelcomeLabel2=このプログラムは [name/ver] をお使いのコンピューターにインストールします。%n%nバージョン 2.0 の新機能:%n%nなぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。%n%n• ストランド/マスクタブ: レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。%n• 影の問題を修正: 以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。%n• 7つの新しいサンプル: 設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。%n%nこのプログラムは Yonatan Setbon が提供しています。ysetbon@gmail.com までご連絡ください。%n%n続行する前に、他のすべてのアプリケーションを閉じることをお勧めします。
japanese.LaunchAfterInstall=インストール後に {#MyAppName} を起動する

chinese.WelcomeLabel2=本程序将在您的计算机上安装 [name/ver]。%n%n版本 2.0 的新功能:%n%n为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。%n%n• 绳股/遮罩标签页: 图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。%n• 修复阴影问题: 修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。%n• 七个新示例: 在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。%n%n本程序由 Yonatan Setbon 提供。您可以通过 ysetbon@gmail.com 联系我。%n%n建议您在继续之前关闭所有其他应用程序。
chinese.LaunchAfterInstall=安装后启动 {#MyAppName}

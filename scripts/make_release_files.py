# -*- coding: utf-8 -*-
"""Generate all release files for a new OpenStrand Studio version.

For each release (e.g. 1.109 -> 1.110), edit ONLY the CONFIG section below:
  1. OLD_VERSION / NEW_VERSION and the two date strings
  2. The BULLETS dict: the what's-new bullets in all 12 languages

Then run from the repo root (or anywhere):
    python scripts/make_release_files.py

It reads the previous version's files and produces:
  - src/inno setup/OpenStrand Studio<NEW>.iss     (Windows installer)
  - src/build_installer_<NEW>.sh                  (macOS .pkg)
  - src/build_dmg_<NEW>.sh                        (macOS .dmg)
  - src/build_mac_<NEW>.sh                        (macOS one-command build)
  - updates src/translations.py                   (12 whats_new_info blocks)
  - updates src/OpenStrandStudio_mac.spec         (CFBundle versions)

Notes:
  - Hebrew text in the macOS .sh welcome pages is automatically converted to
    &#xXXXX; HTML entities (the .iss and translations.py keep plain Hebrew).
  - The script is idempotent for translations.py / the spec: if they are
    already at NEW_VERSION it skips them.
"""
import re, os, sys

# =============================================================================
# CONFIG — edit this section for each release
# =============================================================================
OLD_VERSION = '2.0'          # version the source files belong to
NEW_VERSION = '2.1'          # version to generate
OLD_DATE_SH = '04_October_2026'   # APP_DATE in the old .sh files
NEW_DATE_SH = '19_October_2026'
OLD_DATE_ISS = '04_Oct_2026'   # MyAppDate in the old .iss
NEW_DATE_ISS = '19_Oct_2026'

# What's-new bullets per language: list of (title, text). Same bullets are
# used for the Windows installer, the macOS installer pages, and the in-app
# "What's New?" dialog (translations.py). Write plain unicode text everywhere;
# Hebrew entity-encoding for the .sh files is handled automatically.
BULLETS = {
 'en': [
  ('Interface Sounds', 'Every button, menu, tab and list now plays a short sound, and each mode has its own sound when you turn it on and off. Each area of the app has its own soft hover sound. In Rotate mode you hear a sound when you grab and release a strand end, and a tick at each mark of the dial. At the bottom of General Settings, use Play interface sounds, Sound volume and Play hover sounds to turn the sounds off, change their volume or turn off only the hover sounds.'),
  ('Rotate Mode Triangles and Dial', 'Triangles now mark every strand end you can rotate: red at strand starts, blue at strand ends and yellow under the pointer. While you drag, a dial with a mark every 15° appears around the pivot and shades how far you have turned. Inside the dial the end turns more slowly, for fine control. A faded copy of the strand stays where it started until you let go.'),
  ('Fixes', 'Strand ends no longer fold back on themselves at a high Control Point Influence. A strand no longer loses its shadow where a mask only touches it along an edge. Releasing a strand is faster while shadows are off.'),
 ],
 'fr': [
  ("Sons de l'interface", "Chaque bouton, menu, onglet et liste joue maintenant un petit son, et chaque mode a son propre son quand vous l'activez et le désactivez. Chaque zone de l'application a son propre son discret au survol. En mode Pivoter, un son accompagne la prise et le relâchement d'une extrémité de brin, et un tic marque chaque graduation du cadran. En bas des Paramètres généraux, utilisez « Jouer les sons de l'interface », « Volume des sons » et « Jouer les sons au survol » pour couper les sons, régler leur volume ou couper seulement les sons au survol."),
  ('Triangles et cadran en mode Pivoter', "Des triangles marquent maintenant chaque extrémité de brin que vous pouvez faire pivoter : rouges au début des brins, bleus à leur fin et jaunes sous le pointeur. Pendant le glissement, un cadran gradué tous les 15° apparaît autour du pivot et colore l'angle parcouru. À l'intérieur du cadran, l'extrémité tourne plus lentement, pour un réglage fin. Une copie estompée du brin reste à sa position de départ jusqu'à ce que vous relâchiez."),
  ('Corrections', "Les extrémités des brins ne se replient plus sur elles-mêmes avec une forte Influence du Point de Contrôle. Un brin ne perd plus son ombre là où un masque ne le touche que par un bord. Relâcher un brin est plus rapide quand les ombres sont désactivées."),
 ],
 'de': [
  ('Oberflächenklänge', 'Jede Schaltfläche, jedes Menü, jeder Tab und jede Liste spielt jetzt einen kurzen Klang, und jeder Modus hat einen eigenen Klang beim Ein- und Ausschalten. Jeder Bereich der App hat einen eigenen leisen Klang beim Überfahren. Im Modus Drehen hören Sie einen Klang, wenn Sie ein Strangende greifen und loslassen, und ein Ticken an jeder Markierung der Skala. Unten in den Einstellungen schalten Sie mit „Oberflächenklänge abspielen“, „Lautstärke der Klänge“ und „Klänge beim Überfahren abspielen“ die Klänge aus, ändern ihre Lautstärke oder schalten nur die Klänge beim Überfahren aus.'),
  ('Dreiecke und Skala im Modus Drehen', 'Dreiecke markieren jetzt jedes Strangende, das Sie drehen können: rot am Anfang eines Strangs, blau am Ende und gelb unter dem Mauszeiger. Beim Ziehen erscheint um den Drehpunkt eine Skala mit einer Markierung alle 15°, die farbig zeigt, wie weit Sie gedreht haben. Innerhalb der Skala dreht sich das Ende langsamer, für feine Einstellungen. Eine blasse Kopie des Strangs bleibt an seiner Ausgangsposition, bis Sie loslassen.'),
  ('Fehlerbehebungen', 'Strangenden klappen bei hohem Kontrollpunkt-Einfluss nicht mehr auf sich selbst zurück. Ein Strang verliert seinen Schatten nicht mehr dort, wo eine Maske ihn nur an einer Kante berührt. Das Loslassen eines Strangs ist schneller, wenn Schatten ausgeschaltet sind.'),
 ],
 'it': [
  ("Suoni dell'interfaccia", "Ogni pulsante, menu, scheda ed elenco ora riproduce un breve suono, e ogni modalità ha il suo suono quando la attivi e la disattivi. Ogni area dell'app ha il suo suono leggero al passaggio del mouse. In modalità Ruota senti un suono quando afferri e rilasci l'estremità di un trefolo, e un tic a ogni tacca del quadrante. In fondo a Impostazioni Generali, usa «Riproduci i suoni dell'interfaccia», «Volume dei suoni» e «Riproduci i suoni al passaggio del mouse» per disattivare i suoni, cambiarne il volume o disattivare solo i suoni al passaggio del mouse."),
  ('Triangoli e quadrante in modalità Ruota', "Dei triangoli ora segnano ogni estremità di trefolo che puoi ruotare: rossi all'inizio dei trefoli, blu alla fine e gialli sotto il puntatore. Mentre trascini, attorno al perno appare un quadrante con una tacca ogni 15° che colora l'angolo percorso. Dentro il quadrante l'estremità ruota più lentamente, per una regolazione fine. Una copia sbiadita del trefolo resta nella posizione di partenza finché non rilasci."),
  ('Correzioni', "Le estremità dei trefoli non si ripiegano più su se stesse con un'alta Influenza Punto di Controllo. Un trefolo non perde più la sua ombra dove una maschera lo tocca solo lungo un bordo. Rilasciare un trefolo è più veloce quando le ombre sono disattivate."),
 ],
 'es': [
  ('Sonidos de la interfaz', 'Cada botón, menú, pestaña y lista reproduce ahora un sonido corto, y cada modo tiene su propio sonido al activarlo y desactivarlo. Cada zona de la aplicación tiene su propio sonido suave al pasar el cursor. En el modo Rotar oirás un sonido al agarrar y soltar el extremo de un cordón, y un tic en cada marca del dial. Al final de Configuración General, usa «Reproducir sonidos de la interfaz», «Volumen de los sonidos» y «Reproducir sonidos al pasar el cursor» para apagar los sonidos, cambiar su volumen o apagar solo los sonidos al pasar el cursor.'),
  ('Triángulos y dial en el modo Rotar', 'Ahora unos triángulos marcan cada extremo de cordón que puedes girar: rojos al inicio de los cordones, azules al final y amarillos bajo el puntero. Mientras arrastras, aparece alrededor del pivote un dial con una marca cada 15° que sombrea cuánto has girado. Dentro del dial el extremo gira más despacio, para un ajuste fino. Una copia atenuada del cordón se queda donde empezó hasta que sueltas.'),
  ('Correcciones', 'Los extremos de los cordones ya no se doblan sobre sí mismos con una Influencia del Punto de Control alta. Un cordón ya no pierde su sombra donde una máscara solo lo toca por un borde. Soltar un cordón es más rápido cuando las sombras están desactivadas.'),
 ],
 'pt': [
  ('Sons da interface', 'Cada botão, menu, separador e lista toca agora um som curto, e cada modo tem o seu próprio som ao ligá-lo e desligá-lo. Cada área da aplicação tem o seu próprio som suave ao passar o cursor. No modo Girar ouve um som ao agarrar e largar a ponta de uma mecha, e um tique em cada marca do mostrador. No fim de Configurações Gerais, use «Reproduzir sons da interface», «Volume dos sons» e «Reproduzir sons ao passar o cursor» para desligar os sons, mudar o volume ou desligar apenas os sons ao passar o cursor.'),
  ('Triângulos e mostrador no modo Girar', 'Agora há triângulos a marcar cada ponta de mecha que pode girar: vermelhos no início das mechas, azuis no fim e amarelos sob o cursor. Enquanto arrasta, aparece à volta do pivô um mostrador com uma marca a cada 15° que sombreia quanto já girou. Dentro do mostrador a ponta gira mais devagar, para um ajuste fino. Uma cópia esbatida da mecha fica onde começou até largar.'),
  ('Correções', 'As pontas das mechas já não se dobram sobre si mesmas com uma Influência do Ponto de Controle alta. Uma mecha já não perde a sua sombra onde uma máscara só lhe toca por uma aresta. Largar uma mecha é mais rápido quando as sombras estão desligadas.'),
 ],
 'he': [
  ('צלילי ממשק', 'כל כפתור, תפריט, לשונית ורשימה משמיעים עכשיו צליל קצר, ולכל מצב יש צליל משלו כשמפעילים ומכבים אותו. לכל אזור באפליקציה יש צליל רך משלו במעבר עכבר. במצב סיבוב נשמע צליל כשתופסים ומשחררים קצה של חוט, ותקתוק בכל סימון על החוגה. בתחתית ההגדרות הכלליות, השתמשו ב״השמע צלילי ממשק״, ״עוצמת הצלילים״ ו״השמע צלילים במעבר עכבר״ כדי לכבות את הצלילים, לשנות את עוצמתם או לכבות רק את צלילי מעבר העכבר.'),
  ('משולשים וחוגה במצב סיבוב', 'משולשים מסמנים עכשיו כל קצה חוט שאפשר לסובב: אדום בתחילת חוט, כחול בסופו וצהוב מתחת לסמן. בזמן הגרירה מופיעה סביב נקודת הציר חוגה עם סימון כל 15°, שצובעת כמה סובבתם. בתוך החוגה הקצה מסתובב לאט יותר, לכוונון עדין. עותק דהוי של החוט נשאר במקום שבו התחיל עד שמשחררים.'),
  ('תיקונים', 'קצוות של חוטים כבר לא מתקפלים לאחור על עצמם כשהשפעת נקודת הבקרה גבוהה. חוט כבר לא מאבד את הצל שלו במקום שבו מסכה נוגעת בו רק לאורך קצה. שחרור חוט מהיר יותר כשהצללים כבויים.'),
 ],
 'ru': [
  ('Звуки интерфейса', 'Каждая кнопка, меню, вкладка и список теперь издают короткий звук, а у каждого режима есть свой звук включения и выключения. У каждой области приложения свой тихий звук при наведении. В режиме «Вращать» слышен звук, когда вы берёте и отпускаете конец пряди, и щелчок на каждой отметке шкалы. Внизу общих настроек с помощью «Воспроизводить звуки интерфейса», «Громкость звуков» и «Воспроизводить звуки при наведении» можно выключить звуки, изменить их громкость или выключить только звуки при наведении.'),
  ('Треугольники и шкала в режиме «Вращать»', 'Треугольники теперь отмечают каждый конец пряди, который можно повернуть: красные в начале прядей, синие в конце и жёлтые под указателем. Во время перетаскивания вокруг точки поворота появляется шкала с отметкой каждые 15°, которая закрашивает пройденный угол. Внутри шкалы конец поворачивается медленнее, для точной настройки. Бледная копия пряди остаётся на исходном месте, пока вы не отпустите.'),
  ('Исправления', 'Концы прядей больше не загибаются назад при сильном влиянии контрольных точек. Прядь больше не теряет тень там, где маска касается её только краем. Отпускание пряди работает быстрее, когда тени выключены.'),
 ],
 'fi': [
  ('Käyttöliittymän äänet', 'Jokainen painike, valikko, välilehti ja luettelo soittaa nyt lyhyen äänen, ja jokaisella tilalla on oma äänensä, kun se otetaan käyttöön ja poistetaan käytöstä. Sovelluksen jokaisella alueella on oma hiljainen äänensä osoitettaessa. Kierrä-tilassa kuuluu ääni, kun tartut säikeen päähän ja päästät irti, ja naksahdus asteikon jokaisen merkin kohdalla. Yleisten asetusten alareunassa voit valinnoilla Toista käyttöliittymän äänet, Äänten voimakkuus ja Toista äänet osoitettaessa mykistää äänet, muuttaa niiden voimakkuutta tai mykistää vain osoitusäänet.'),
  ('Kolmiot ja asteikko Kierrä-tilassa', 'Kolmiot merkitsevät nyt jokaisen säikeen pään, jota voit kiertää: punainen säikeen alussa, sininen lopussa ja keltainen osoittimen alla. Vetäessäsi kiertopisteen ympärille ilmestyy asteikko, jossa on merkki 15°:n välein ja joka värittää, kuinka paljon olet kiertänyt. Asteikon sisällä pää kiertyy hitaammin tarkkaa säätöä varten. Säikeestä jää haalea kopio sen alkuperäiselle paikalle, kunnes päästät irti.'),
  ('Korjaukset', 'Säikeiden päät eivät enää taitu takaisin itsensä päälle, kun ohjauspisteen vaikutus on suuri. Säie ei enää menetä varjoaan kohdasta, jossa maski koskettaa sitä vain reunalta. Säikeen päästäminen irti on nopeampaa, kun varjot ovat pois päältä.'),
 ],
 'sv': [
  ('Gränssnittsljud', 'Varje knapp, meny, flik och lista spelar nu ett kort ljud, och varje läge har ett eget ljud när du slår på och stänger av det. Varje del av appen har ett eget mjukt ljud vid hovring. I läget Rotera hörs ett ljud när du tar tag i och släpper en strängände, och ett tick vid varje markering på skalan. Längst ned i Allmänna inställningar använder du Spela gränssnittsljud, Ljudvolym och Spela ljud vid hovring för att stänga av ljuden, ändra volymen eller stänga av bara hovringsljuden.'),
  ('Trianglar och skala i läget Rotera', 'Trianglar markerar nu varje strängände som du kan rotera: röda i början av strängar, blå i slutet och gula under pekaren. Medan du drar visas en skala runt vridpunkten med en markering var 15:e grad, och den färgar hur långt du har vridit. Innanför skalan vrids änden långsammare, för finjustering. En blek kopia av strängen ligger kvar där den började tills du släpper.'),
  ('Åtgärdade fel', 'Strängändar viker sig inte längre tillbaka över sig själva vid högt inflytande för kontrollpunkterna. En sträng tappar inte längre sin skugga där en mask bara rör vid den längs en kant. Att släppa en sträng går snabbare när skuggorna är avstängda.'),
 ],
 'ja': [
  ('インターフェース音', 'すべてのボタン、メニュー、タブ、リストで短い音が鳴るようになり、各モードにはオンとオフでそれぞれ専用の音があります。アプリのエリアごとに、ホバー時の控えめな音も用意されています。回転モードでは、ストランドの端をつかむときと離すときに音が鳴り、ダイヤルの目盛りごとにカチッと鳴ります。一般設定の一番下にある「インターフェース音を再生」「効果音の音量」「ホバー時に音を再生」で、音をオフにしたり、音量を変えたり、ホバー音だけをオフにしたりできます。'),
  ('回転モードの三角形とダイヤル', '回転できるストランドの端に三角形が表示されるようになりました: ストランドの始点は赤、終点は青、ポインターの下は黄色です。ドラッグ中は回転の中心の周りに15°ごとの目盛りが付いたダイヤルが現れ、回した角度に色が付きます。ダイヤルの内側では端がゆっくり回るので、細かく調整できます。マウスを離すまで、ストランドの薄いコピーが元の位置に残ります。'),
  ('修正', '制御点の影響を強くしたときに、ストランドの端が折り返してしまう問題を修正しました。マスクが端だけで接している場所で、ストランドの影が消えなくなりました。影がオフのときは、ストランドを離す操作が速くなりました。'),
 ],
 'zh': [
  ('界面音效', '每个按钮、菜单、标签页和列表现在都会播放简短的音效，每种模式在开启和关闭时也有各自的音效。应用的每个区域都有自己轻柔的悬停音效。在旋转模式中，抓起和松开绳股端点时会有音效，转到表盘的每个刻度时会有滴答声。在常规设置的底部，可以用“播放界面音效”“音效音量”和“悬停时播放音效”来关闭音效、调整音量，或只关闭悬停音效。'),
  ('旋转模式的三角形和表盘', '现在每个可以旋转的绳股端点都会显示三角形: 绳股起点为红色，终点为蓝色，指针下方为黄色。拖动时，枢轴周围会出现每 15° 一个刻度的表盘，并为已转过的角度着色。在表盘内侧，端点转得更慢，便于精细调整。松开之前，绳股的淡色副本会留在原来的位置。'),
  ('修复', '控制点影响力较高时，绳股端点不再向回折叠。遮罩只沿边缘接触绳股时，绳股不再丢失阴影。关闭阴影时，松开绳股的速度更快。'),
 ],
}

# Optional one-paragraph note shown above the bullets (why this version number).
# Leave as {} for a normal release.
INTRO = {}

# The previous release's bullets and note. The in-app "What's New?" dialog
# lists them under the new ones (SHOW_OLD_IN_APP); the installers show only
# the new bullets, and OLD_INTRO is removed from the macOS .sh welcome pages.
# For the next release, move BULLETS/INTRO here and write the new ones above.
SHOW_OLD_IN_APP = True

OLD_BULLETS = {
 'en': [
  ('Strands and Masks Tabs', 'The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.'),
  ('Fixed Shadow Issues', 'Fixed shadow issues from older versions. Shadows for masks now behave more naturally.'),
  ('Seven New Samples', 'In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.'),
 ],
 'fr': [
  ('Onglets Brins et Masques', "La liste des calques est maintenant séparée en deux onglets, Brins et Masques, avec un sélecteur juste au-dessus de Dessin. Noms. L'onglet Masques a ses propres boutons Nouv. Masque, Suppr. Masque, Désél. Tous et Suppr. Tout, et Nouv. Masque remplace le bouton Masque de la barre d'outils. Suppr. Tout sur cet onglet ne supprime que les masques, après confirmation, en une seule étape d'annulation. Les masques restent toujours au-dessus de tous les brins, donc leur place dans la liste n'a plus d'importance, et sélectionner un calque de l'autre onglet ouvre cet onglet pour vous."),
  ('Ombres corrigées', "Des problèmes d'ombres des versions précédentes ont été corrigés. Les ombres des masques se comportent maintenant de façon plus naturelle."),
  ('Sept nouveaux exemples', 'Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page.'),
 ],
 'de': [
  ('Tabs Stränge und Masken', 'Die Ebenenliste ist jetzt in zwei Tabs aufgeteilt, Stränge und Masken, mit einem Umschalter direkt über Namen zeigen. Der Tab Masken hat eigene Schaltflächen für Neue Maske, Maske entf., Alle abwählen und Alle löschen, und Neue Maske ersetzt die Maske-Schaltfläche in der Werkzeugleiste. Alle löschen löscht in diesem Tab nur die Masken, nach einer Bestätigung und in einem einzigen Rückgängig-Schritt. Masken liegen jetzt immer über allen Strängen, ihre Position in der Liste spielt also keine Rolle mehr, und wer eine Ebene des anderen Tabs auswählt, wird automatisch zu diesem Tab gebracht.'),
  ('Schattenprobleme behoben', 'Schattenprobleme aus älteren Versionen wurden behoben. Schatten von Masken verhalten sich jetzt natürlicher.'),
  ('Sieben neue Beispiele', 'In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt.'),
 ],
 'it': [
  ('Schede Trefoli e Maschere', "L'elenco dei livelli è ora diviso in due schede, Trefoli e Maschere, con un selettore subito sopra Disegna Nomi. La scheda Maschere ha i suoi pulsanti Nuova Masch., Elim. Maschera, Desel. Tutto ed Elimina Tutto, e Nuova Masch. sostituisce il pulsante Maschera della barra degli strumenti. Elimina Tutto in questa scheda elimina solo le maschere, dopo una conferma, in un unico passo di annullamento. Le maschere restano sempre sopra tutti i trefoli, quindi la loro posizione nell'elenco non conta più, e selezionare un livello dell'altra scheda apre quella scheda per voi."),
  ('Problemi delle ombre risolti', 'Sono stati risolti problemi delle ombre presenti nelle versioni precedenti. Le ombre delle maschere ora si comportano in modo più naturale.'),
  ('Sette nuovi esempi', "In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina."),
 ],
 'es': [
  ('Pestañas Cordones y Máscaras', 'La lista de capas ahora se divide en dos pestañas, Cordones y Máscaras, con un selector justo encima de Ver Nombres. La pestaña Máscaras tiene sus propios botones Nueva Másc., Elim. Máscara, Deselec. Todo y Eliminar Todo, y Nueva Másc. reemplaza el botón Máscara de la barra de herramientas. Eliminar Todo en esta pestaña elimina solo las máscaras, tras una confirmación y en un único paso de deshacer. Las máscaras ahora se mantienen siempre por encima de todos los cordones, así que su posición en la lista ya no importa, y al seleccionar una capa de la otra pestaña se abre esa pestaña automáticamente.'),
  ('Problemas de sombras corregidos', 'Se corrigieron problemas de sombras de versiones anteriores. Las sombras de las máscaras ahora se comportan de forma más natural.'),
  ('Siete ejemplos nuevos', 'En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página.'),
 ],
 'pt': [
  ('Separadores Mechas e Máscaras', 'A lista de camadas agora está dividida em dois separadores, Mechas e Máscaras, com um seletor mesmo acima de Exib. Nomes. O separador Máscaras tem os seus próprios botões Nova Másc., Excl. Máscara, Desmar. Tudo e Excluir Tudo, e Nova Másc. substitui o botão Máscara da barra de ferramentas. Excluir Tudo neste separador elimina apenas as máscaras, após uma confirmação e num único passo de anular. As máscaras ficam sempre acima de todas as mechas, por isso a sua posição na lista já não importa, e selecionar uma camada do outro separador abre esse separador por si.'),
  ('Problemas de sombras corrigidos', 'Foram corrigidos problemas de sombras de versões anteriores. As sombras das máscaras agora comportam-se de forma mais natural.'),
  ('Sete novos exemplos', 'Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página.'),
 ],
 'he': [
  ('לשוניות חוטים ומסכות', 'רשימת השכבות מחולקת עכשיו לשתי לשוניות, חוטים ומסכות, עם מתג ממש מעל צייר שמות. בלשונית מסכות יש כפתורים משלה: מסכה חדשה, מחק מסכה, בטל בחירה ומחק הכל, והכפתור מסכה חדשה מחליף את כפתור המסכה בסרגל הכלים. מחק הכל בלשונית הזו מוחקת רק את המסכות, אחרי אישור, ובשלב ביטול אחד. המסכות נשארות תמיד מעל כל החוטים, ולכן מיקומן ברשימה כבר לא משנה, ובחירת שכבה מהלשונית השנייה פותחת אותה אוטומטית.'),
  ('תיקוני צללים', 'תוקנו בעיות צללים מגרסאות קודמות. הצללים של מסכות מתנהגים עכשיו בצורה טבעית יותר.'),
  ('שבע דוגמאות חדשות', 'בהגדרות, תחת דוגמאות, יש שבעה פרויקטים חדשים לפתוח וללמוד מהם: אריגה ישרה 12×12, אריגה מעוקלת 6×6, צמה שטוחה, עבה ודק, גשר, זוגות מפותלים ואריגת קגומה. כפתורי הדוגמאות מסודרים עכשיו שניים בשורה, כך שכל הרשימה נכנסת בעמוד.'),
 ],
 'ru': [
  ('Вкладки «Пряди» и «Маски»', 'Список слоёв теперь разделён на две вкладки, «Пряди» и «Маски», с переключателем прямо над кнопкой «Показ имён». У вкладки «Маски» свои кнопки: «Новая маска», «Удалить маску», «Снять выбор» и «Удалить все», а «Новая маска» заменяет кнопку «Маска» на панели инструментов. «Удалить все» на этой вкладке удаляет только маски, после подтверждения и одним шагом отмены. Маски теперь всегда лежат над всеми прядями, поэтому их место в списке больше не важно, а выбор слоя с другой вкладки сам открывает эту вкладку.'),
  ('Исправлены проблемы с тенями', 'Исправлены проблемы с тенями из прошлых версий. Тени масок теперь ведут себя естественнее.'),
  ('Семь новых примеров', 'в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.'),
 ],
 'fi': [
  ('Säikeet- ja Maskit-välilehdet', 'Kerroslista on nyt jaettu kahteen välilehteen, Säikeet ja Maskit, ja valitsin on heti Näytä nimet -painikkeen yläpuolella. Maskit-välilehdellä on omat painikkeensa: Uusi maski, Poista maski, Poista valinnat ja Poista kaikki, ja Uusi maski korvaa työkalupalkin Maski-painikkeen. Poista kaikki poistaa tällä välilehdellä vain maskit, vahvistuksen jälkeen ja yhdellä kumoamisaskeleella. Maskit pysyvät nyt aina kaikkien säikeiden päällä, joten maskin paikalla listassa ei ole enää väliä, ja toisen välilehden kerroksen valinta avaa kyseisen välilehden puolestasi.'),
  ('Varjo-ongelmat korjattu', 'Vanhojen versioiden varjo-ongelmat on korjattu. Maskien varjot käyttäytyvät nyt luonnollisemmin.'),
  ('Seitsemän uutta esimerkkiä', 'asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.'),
 ],
 'sv': [
  ('Flikarna Strängar och Masker', 'Lagerlistan är nu uppdelad i två flikar, Strängar och Masker, med en växlare precis ovanför Visa namn. Fliken Masker har egna knappar: Ny mask, Ta bort mask, Avmarkera alla och Ta bort alla, och Ny mask ersätter Mask-knappen i verktygsfältet. Ta bort alla på den här fliken tar bara bort maskerna, efter en bekräftelse och i ett enda ångra-steg. Masker ligger nu alltid ovanför alla strängar, så var en mask står i listan spelar ingen roll längre, och när du markerar ett lager på den andra fliken öppnas den fliken åt dig.'),
  ('Skuggproblem åtgärdade', 'Skuggproblem från äldre versioner har åtgärdats. Skuggor för masker beter sig nu mer naturligt.'),
  ('Sju nya exempel', 'i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.'),
 ],
 'ja': [
  ('ストランド/マスクタブ', 'レイヤーリストが「ストランド」と「マスク」の2つのタブに分かれ、「名前を表示」のすぐ上に切り替えが付きました。マスクタブには専用の「新しいマスク」「マスクを削除」「すべて選択解除」「すべて削除」ボタンがあり、「新しいマスク」はツールバーのマスクボタンの代わりになります。このタブの「すべて削除」はマスクだけを、確認のあとに1回の元に戻す操作で削除します。マスクは常にすべてのストランドの上に保たれるため、リスト内の位置は気にする必要がなくなり、もう一方のタブのレイヤーを選ぶとそのタブが自動で開きます。'),
  ('影の問題を修正', '以前のバージョンにあった影の問題を修正しました。マスクの影がより自然な動きになりました。'),
  ('7つの新しいサンプル', '設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。'),
 ],
 'zh': [
  ('绳股/遮罩标签页', '图层列表现在分为“绳股”和“遮罩”两个标签页，切换按钮就在“显示名称”上方。“遮罩”标签页有自己的“新建遮罩”“删除遮罩”“取消全选”和“全部删除”按钮，“新建遮罩”取代了工具栏中的遮罩按钮。在此标签页中“全部删除”只会删除遮罩，需确认，并且只算一次撤销。遮罩现在始终位于所有绳股之上，因此它在列表中的位置不再重要，选择另一个标签页中的图层时会自动打开该标签页。'),
  ('修复阴影问题', '修复了旧版本中的阴影问题，遮罩的阴影现在表现得更自然。'),
  ('七个新示例', '在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。'),
 ],
}

OLD_INTRO = {
 'en': "Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.",
 'fr': "Pourquoi 2.0 ? Les masques sont maintenant beaucoup plus naturels à utiliser. Le tissage est essentiel pour faire des nœuds, et les masques en sont une grande partie : c'est une étape majeure pour OpenStrand Studio.",
 'de': "Warum 2.0? Masken fühlen sich jetzt viel natürlicher an. Weben ist entscheidend beim Knüpfen von Knoten, und Masken sind ein großer Teil davon – ein wichtiger Schritt für OpenStrand Studio.",
 'it': "Perché 2.0? Le maschere ora sono molto più naturali da usare. L'intreccio è fondamentale per fare i nodi e le maschere ne sono una parte importante: è un passo importante per OpenStrand Studio.",
 'es': "¿Por qué 2.0? Las máscaras ahora son mucho más naturales de usar. El tejido es clave para hacer nudos y las máscaras son una gran parte del tejido, así que es un gran paso para OpenStrand Studio.",
 'pt': "Porquê 2.0? As máscaras agora são muito mais naturais de usar. A tecelagem é essencial para fazer nós e as máscaras são uma grande parte dela, por isso é um grande passo para o OpenStrand Studio.",
 'he': "למה 2.0? המסכות מרגישות עכשיו הרבה יותר טבעיות לשימוש. אריגה היא מרכיב מרכזי בקשירת קשרים, ומסכות הן חלק גדול מהאריגה, ולכן זהו צעד משמעותי עבור OpenStrand Studio.",
 'ru': "Почему 2.0? Маски теперь гораздо естественнее в работе. Плетение — основа завязывания узлов, а маски — большая его часть, поэтому это важный шаг для OpenStrand Studio.",
 'fi': "Miksi 2.0? Maskit tuntuvat nyt paljon luonnollisemmilta käyttää. Kudonta on keskeistä solmujen tekemisessä, ja maskit ovat suuri osa kudontaa, joten tämä on iso askel OpenStrand Studiolle.",
 'sv': "Varför 2.0? Masker känns nu mycket mer naturliga att använda. Vävning är nyckeln till att knyta knutar och masker är en stor del av vävningen, så detta är ett stort steg för OpenStrand Studio.",
 'ja': "なぜ2.0なのか: マスクがずっと自然に使えるようになりました。結び目を作るには織りが重要で、マスクは織りの大きな部分を占めるため、OpenStrand Studioにとって大きな一歩です。",
 'zh': "为什么是2.0？遮罩现在用起来自然得多。编织是打绳结的关键，而遮罩是编织的重要组成部分，因此这是 OpenStrand Studio 的重要一步。",
}

# A short unique substring of each language's FIRST bullet title in the OLD
# version's files, used to recognize which language a <ul> block belongs to.
# Update these to match the previous release's first bullet. For Hebrew give
# the &#x....; entity form of the first few letters (as it appears in the .sh).
MARKERS = {
 'en': 'Strands and Masks Tabs',
 'fr': 'Onglets Brins et Masques',
 'de': 'Tabs Stränge und Masken',
 'it': 'Schede Trefoli e Maschere',
 'es': 'Pestañas Cordones y Máscaras',
 'pt': 'Separadores Mechas e Máscaras',
 'he': '&#x05DC;&#x05E9;&#x05D5;&#x05E0;&#x05D9;&#x05D5;&#x05EA; &#x05D7;&#x05D5;&#x05D8;&#x05D9;&#x05DD;',
 'ru': 'Вкладки «Пряди»',
 'fi': 'Säikeet- ja Maskit',
 'sv': 'Flikarna Strängar',
 'ja': 'ストランド/マスクタブ',
 'zh': '绳股/遮罩标签页',
}
# =============================================================================
# END CONFIG
# =============================================================================

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')
OLD_U = OLD_VERSION.replace('.', '_')
NEW_U = NEW_VERSION.replace('.', '_')

def he_entities(s):
    """Encode non-ASCII chars as &#xXXXX; HTML entities (macOS welcome pages)."""
    return ''.join(ch if ord(ch) < 128 else '&#x%04X;' % ord(ch) for ch in s)

def li_block_sh(lang):
    lines = []
    for title, text in BULLETS[lang]:
        li = '        <li><b>%s:</b> %s</li>' % (title, text)
        if lang == 'he':
            li = he_entities(li)
        lines.append(li)
    return '\n'.join(lines)

def intro_sh(lang, intro=None):
    intro = INTRO if intro is None else intro
    if lang not in intro:
        return ''
    p = '<p>%s</p>\n    ' % intro[lang]
    return he_entities(p) if lang == 'he' else p

def intro_translations(lang, intro=None):
    intro = INTRO if intro is None else intro
    if lang not in intro:
        return ''
    return '            <p style="font-size:14px;">%s</p>\n' % intro[lang]

def li_block_translations(lang, bullets=None):
    bullets = BULLETS if bullets is None else bullets
    return '\n'.join('            <li style="font-size:14px;"><b>%s:</b> %s</li>' % (t, x)
                     for t, x in bullets[lang])

def old_section_translations(lang, h2):
    """The previous release's notes, listed under the new ones in the app."""
    if not SHOW_OLD_IN_APP:
        return ''
    return ('\n\n            <h3>%s %s</h3>\n%s%s'
            % (h2, OLD_VERSION, intro_translations(lang, OLD_INTRO),
               li_block_translations(lang, OLD_BULLETS)))

def iss_bullets(lang):
    return '%n'.join('• %s: %s' % (t, x) for t, x in BULLETS[lang])

def read(p):
    with open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()

def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)

# ----------------------------------------------------------------------------
# 1) macOS .sh files (installer + dmg): version, date, and all 49 bullet lists
# ----------------------------------------------------------------------------
def gen_sh(src_name, dst_name):
    text = read(os.path.join(SRC, src_name))
    text = text.replace(OLD_VERSION, NEW_VERSION).replace(OLD_U, NEW_U)
    text = text.replace(OLD_DATE_SH, NEW_DATE_SH)

    # The old note sits just before its <ul>; the new one (if any) is added below
    for lang in OLD_INTRO:
        text = text.replace(intro_sh(lang, OLD_INTRO), '')

    counts = {k: 0 for k in BULLETS}
    def repl(m):
        attrs, inner = m.group(1), m.group(2)
        for lang, marker in MARKERS.items():
            if marker in inner:
                counts[lang] += 1
                return '%s<ul%s>\n%s\n    </ul>' % (intro_sh(lang), attrs, li_block_sh(lang))
        raise SystemExit('Unrecognized <ul> block in %s: %r...' % (src_name, inner[:80]))
    text = re.sub(r'<ul([^>]*)>\s*(.*?)\s*</ul>', repl, text, flags=re.S)

    write(os.path.join(SRC, dst_name), text)
    print(dst_name, 'ul-blocks replaced per lang:', counts)
    if len(set(counts.values())) != 1:
        raise SystemExit('Unbalanced language counts - check MARKERS')

gen_sh('build_installer_%s.sh' % OLD_U, 'build_installer_%s.sh' % NEW_U)
gen_sh('build_dmg_%s.sh' % OLD_U, 'build_dmg_%s.sh' % NEW_U)

# ----------------------------------------------------------------------------
# 2) build_mac_<NEW>.sh
# ----------------------------------------------------------------------------
text = read(os.path.join(SRC, 'build_mac_%s.sh' % OLD_U))
text = text.replace(OLD_VERSION, NEW_VERSION).replace(OLD_U, NEW_U)
write(os.path.join(SRC, 'build_mac_%s.sh' % NEW_U), text)
print('build_mac_%s.sh written' % NEW_U)

# ----------------------------------------------------------------------------
# 3) Inno Setup .iss: defines + the 12 WelcomeLabel2 lines
#    The fixed sentences around the bullets are kept from release to release.
# ----------------------------------------------------------------------------
ISS_WRAP = {
 'english': ("This will install [name/ver] on your computer.%n%nWhat's New in Version {v}:%n%n",
   "%n%nThe program is brought to you by Yonatan Setbon. You can contact me at ysetbon@gmail.com.%n%nIt is recommended that you close all other applications before continuing.", 'en'),
 'french': ("Ceci va installer [name/ver] sur votre ordinateur.%n%nNouveautés de la version {v}:%n%n",
   "%n%nLe programme vous est proposé par Yonatan Setbon. Vous pouvez me contacter à ysetbon@gmail.com.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.", 'fr'),
 'german': ("Dies installiert [name/ver] auf Ihrem Computer.%n%nNeu in Version {v}:%n%n",
   "%n%nDas Programm wird bereitgestellt von Yonatan Setbon. Kontakt: ysetbon@gmail.com.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor Sie fortfahren.", 'de'),
 'italian': ("Questo installerà [name/ver] sul tuo computer.%n%nNovità della versione {v}:%n%n",
   "%n%nIl programma è offerto da Yonatan Setbon. Puoi contattarmi a ysetbon@gmail.com.%n%nSi raccomanda di chiudere tutte le altre applicazioni prima di continuare.", 'it'),
 'spanish': ("Esto instalará [name/ver] en su computadora.%n%nNovedades de la versión {v}:%n%n",
   "%n%nEl programa es presentado por Yonatan Setbon. Puede contactarme en ysetbon@gmail.com.%n%nSe recomienda que cierre todas las demás aplicaciones antes de continuar.", 'es'),
 'portuguese': ("Isto instalará [name/ver] no seu computador.%n%nNovidades da versão {v}:%n%n",
   "%n%nO programa é oferecido por Yonatan Setbon. Você pode me contatar em ysetbon@gmail.com.%n%nRecomenda-se que você feche todos os outros aplicativos antes de continuar.", 'pt'),
 'hebrew': ("פעולה זו תתקין את [name/ver] על המחשב שלך.%n%nמה חדש בגרסה {v}:%n%n",
   "%n%nהתוכנית מובאת אליכם על ידי יהונתן סטבון. ניתן ליצור איתי קשר בכתובת ysetbon@gmail.com.%n%nמומלץ לסגור את כל היישומים האחרים לפני שתמשיך.", 'he'),
 'russian': ('Эта программа установит [name/ver] на ваш компьютер.%n%nЧто нового в версии {v}:%n%n',
   '%n%nПрограмму создал Йонатан Сетбон. Связаться со мной можно по адресу ysetbon@gmail.com.%n%nРекомендуется закрыть все остальные приложения, прежде чем продолжить.', 'ru'),
 'finnish': ('Tämä asentaa [name/ver] tietokoneellesi.%n%nMitä uutta versiossa {v}:%n%n',
   '%n%nOhjelman on tehnyt Yonatan Setbon. Voit ottaa minuun yhteyttä osoitteessa ysetbon@gmail.com.%n%nOn suositeltavaa sulkea kaikki muut sovellukset ennen jatkamista.', 'fi'),
 'swedish': ('Detta installerar [name/ver] på din dator.%n%nNyheter i version {v}:%n%n',
   '%n%nProgrammet kommer från Yonatan Setbon. Du kan kontakta mig på ysetbon@gmail.com.%n%nDet rekommenderas att du stänger alla andra program innan du fortsätter.', 'sv'),
 'japanese': ('このプログラムは [name/ver] をお使いのコンピューターにインストールします。%n%nバージョン {v} の新機能:%n%n',
   '%n%nこのプログラムは Yonatan Setbon が提供しています。ysetbon@gmail.com までご連絡ください。%n%n続行する前に、他のすべてのアプリケーションを閉じることをお勧めします。', 'ja'),
 'chinese': ('本程序将在您的计算机上安装 [name/ver]。%n%n版本 {v} 的新功能:%n%n',
   '%n%n本程序由 Yonatan Setbon 提供。您可以通过 ysetbon@gmail.com 联系我。%n%n建议您在继续之前关闭所有其他应用程序。', 'zh'),
}

text = read(os.path.join(SRC, 'inno setup', 'OpenStrand Studio%s.iss' % OLD_U))
text = text.replace('"%s"' % OLD_VERSION, '"%s"' % NEW_VERSION)
text = text.replace('"%s"' % OLD_DATE_ISS, '"%s"' % NEW_DATE_ISS)
text = text.replace('_{#MyAppDate}_%s' % OLD_U, '_{#MyAppDate}_%s' % NEW_U)

out = []
for line in text.split('\n'):
    m = re.match(r'^(\w+)\.WelcomeLabel2=', line)
    if m and m.group(1) in ISS_WRAP:
        pre, post, lang = ISS_WRAP[m.group(1)]
        out.append('%s.WelcomeLabel2=%s%s%s'
                   % (m.group(1), pre.format(v=NEW_VERSION),
                      (INTRO[lang] + '%n%n' if lang in INTRO else '') + iss_bullets(lang), post))
    else:
        out.append(line)
write(os.path.join(SRC, 'inno setup', 'OpenStrand Studio%s.iss' % NEW_U), '\n'.join(out))
print('OpenStrand Studio%s.iss written' % NEW_U)

# ----------------------------------------------------------------------------
# 4) translations.py: the 12 whats_new_info blocks (in-app What's New dialog)
# ----------------------------------------------------------------------------
TR = {
 'en': ("What's New in Version", "© 2026 OpenStrand Studio - Version"),
 'fr': ("Nouveautés de la version", "© 2026 OpenStrand Studio - Version"),
 'de': ("Neu in Version", "© 2026 OpenStrand Studio - Version"),
 'it': ("Novità della versione", "© 2026 OpenStrand Studio - Versione"),
 'es': ("Novedades de la versión", "© 2026 OpenStrand Studio - Versión"),
 'pt': ("Novidades da versão", "© 2026 OpenStrand Studio – Versão"),
 'he': ("מה חדש בגרסה", "© 2026 OpenStrand Studio - גרסה"),
 'ru': ('Что нового в версии', '© 2026 OpenStrand Studio - Версия'),
 'fi': ('Mitä uutta versiossa', '© 2026 OpenStrand Studio - Versio'),
 'sv': ('Vad är nytt i version', '© 2026 OpenStrand Studio - Version'),
 'ja': ('新機能: バージョン', '© 2026 OpenStrand Studio - バージョン'),
 'zh': ('新功能: 版本', '© 2026 OpenStrand Studio - 版本'),
}

tr_path = os.path.join(SRC, 'translations.py')
text = read(tr_path)
n_total = 0
for lang, (h2, cp) in TR.items():
    pattern = re.compile(
        re.escape('<h2>%s %s</h2>' % (h2, OLD_VERSION)) + r'\r?\n\r?\n.*?\r?\n\r?\n(\s*)' +
        re.escape('<p style="font-size:14px;">%s %s</p>' % (cp, OLD_VERSION)), re.S)
    def repl(m):
        return ('<h2>%s %s</h2>\n\n%s\n\n%s<p style="font-size:14px;">%s %s</p>'
                % (h2, NEW_VERSION, intro_translations(lang) + li_block_translations(lang)
                   + old_section_translations(lang, h2), m.group(1), cp, NEW_VERSION))
    text, n = pattern.subn(repl, text)
    n_total += n
    if n not in (0, 1):
        raise SystemExit('translations.py: expected 1 block for %s, replaced %d' % (lang, n))
if n_total:
    write(tr_path, text)
print('translations.py: replaced %d whats_new_info blocks' % n_total)

# ----------------------------------------------------------------------------
# 5) OpenStrandStudio_mac.spec: CFBundleShortVersionString / CFBundleVersion
# ----------------------------------------------------------------------------
spec_path = os.path.join(SRC, 'OpenStrandStudio_mac.spec')
text = read(spec_path)
n = text.count("'%s'" % OLD_VERSION)
text = text.replace("'%s'" % OLD_VERSION, "'%s'" % NEW_VERSION)
write(spec_path, text)
print('OpenStrandStudio_mac.spec: %d version strings bumped' % n)

print('ALL DONE')

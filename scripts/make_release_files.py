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
OLD_VERSION = '1.110'          # version the source files belong to
NEW_VERSION = '1.111'          # version to generate
OLD_DATE_SH = '07_September_2026'   # APP_DATE in the old .sh files
NEW_DATE_SH = '22_September_2026'
OLD_DATE_ISS = '07_Sep_2026'   # MyAppDate in the old .iss
NEW_DATE_ISS = '22_Sep_2026'

# What's-new bullets per language: list of (title, text). Same bullets are
# used for the Windows installer, the macOS installer pages, and the in-app
# "What's New?" dialog (translations.py). Write plain unicode text everywhere;
# Hebrew entity-encoding for the .sh files is handled automatically.
BULLETS = {
 'en': [
  ("Stylize End Side", "Right-click a layer with a free end and pick Stylize End Side, just under Close the Knot. A dialog lets you choose how the strand ends: Straight, Angled, Rounded, Pointed, Notched or Concave. You can also set the tilt and depth, extend or trim the end, and add a side line with its own thickness and color. The preview is live on the canvas. The shadow, side line and masks all follow the new shape. End styles are saved with your project and work with undo and redo."),
  ("Right Size on Scaled Screens", "On high-resolution screens with display scaling turned on, the buttons and text used to look too small. The app now follows your display scale. Toolbar labels no longer get cut off, and the toolbar moves onto two rows when the window is narrow. The layer panel can be dragged narrower than before. The OpenStrand Studio logo now appears on every window and in the taskbar."),
  ("Dialogs Fit Small Screens", "The Settings dialog can now be made smaller, so its Apply and OK buttons always stay on screen. The same goes for Edit Shadow, the group shadow editor, Create Mask Grid, Edit Strand Angles, Change Width and the video player. A dialog never opens larger than your screen, and it keeps the size you give it."),
  ("Smoother Dragging", "The canvas stays sharp while you drag, even on scaled displays or with supersampling on. Move mode shows a closed hand while dragging a point. View mode can now pan with the left mouse button too. The Refresh button's tooltip now says what it does: reload layers and reset the view."),
  ('Russian, Finnish, Swedish, Japanese and Chinese', 'The app is now available in Russian, Finnish, Swedish, Japanese and Chinese. Choose the language in Settings, under Change Language: every button, menu, dialog and help text is translated, and each language has its flag in the list.'),
 ],
 'fr': [
  ("Styliser le côté d'extrémité", "Faites un clic droit sur un calque ayant une extrémité libre et choisissez Styliser le côté d'extrémité, juste sous Fermer le Nœud. Une boîte de dialogue vous laisse choisir la forme de l'extrémité du brin : Droite, Inclinée, Arrondie, Pointue, Entaillée ou Concave. Vous pouvez aussi régler l'inclinaison et la profondeur, allonger ou raccourcir l'extrémité, et ajouter une ligne latérale avec sa propre épaisseur et sa propre couleur. L'aperçu est en direct sur le canevas. L'ombre, la ligne latérale et les masques suivent tous la nouvelle forme. Les styles d'extrémité sont enregistrés avec votre projet et fonctionnent avec annuler et rétablir."),
  ("La bonne taille sur les écrans mis à l'échelle", "Sur les écrans haute résolution avec une mise à l'échelle de l'affichage, les boutons et le texte paraissaient trop petits. L'application suit désormais l'échelle de votre écran. Les libellés de la barre d'outils ne sont plus coupés, et la barre d'outils passe sur deux lignes quand la fenêtre est étroite. Le panneau des calques peut être réduit plus qu'avant. Le logo OpenStrand Studio apparaît maintenant sur chaque fenêtre et dans la barre des tâches."),
  ("Des boîtes de dialogue adaptées aux petits écrans", "La boîte de dialogue Paramètres peut désormais être réduite, de sorte que ses boutons Appliquer et OK restent toujours à l'écran. Il en va de même pour Modifier l'ombre, l'éditeur d'ombre de groupe, Créer Grille de Masque, Modifier les angles des brins, Changer largeur et le lecteur vidéo. Une boîte de dialogue ne s'ouvre jamais plus grande que votre écran, et elle garde la taille que vous lui donnez."),
  ("Un glissement plus fluide", "Le canevas reste net pendant que vous faites glisser, même sur les écrans mis à l'échelle ou avec le suréchantillonnage activé. Le mode déplacement affiche une main fermée pendant le glissement d'un point. Le mode vue peut maintenant aussi se déplacer avec le bouton gauche de la souris. L'info-bulle du bouton Actualiser indique désormais ce qu'il fait : recharger les calques et réinitialiser la vue."),
  ('Russe, finnois, suédois, japonais et chinois', "L'application est désormais disponible en russe, en finnois, en suédois, en japonais et en chinois. Choisissez la langue dans Paramètres, sous Changer de langue : chaque bouton, menu, boîte de dialogue et texte d'aide est traduit, et chaque langue a son drapeau dans la liste."),
 ],
 'de': [
  ("Endseite gestalten", "Klicken Sie mit der rechten Maustaste auf eine Ebene mit einem freien Ende und wählen Sie Endseite gestalten, direkt unter Knoten schließen. In einem Dialog wählen Sie, wie der Strang endet: Gerade, Schräg, Abgerundet, Spitz, Eingekerbt oder Konkav. Sie können außerdem Neigung und Tiefe einstellen, das Ende verlängern oder kürzen und eine Seitenlinie mit eigener Dicke und Farbe hinzufügen. Die Vorschau erscheint live auf der Zeichenfläche. Schatten, Seitenlinie und Masken folgen alle der neuen Form. Endstile werden mit dem Projekt gespeichert und funktionieren mit Rückgängig und Wiederherstellen."),
  ("Richtige Größe auf skalierten Bildschirmen", "Auf hochauflösenden Bildschirmen mit aktivierter Anzeigeskalierung wirkten Schaltflächen und Text zu klein. Die App folgt jetzt Ihrer Anzeigeskalierung. Beschriftungen in der Werkzeugleiste werden nicht mehr abgeschnitten, und die Werkzeugleiste wechselt bei schmalen Fenstern auf zwei Zeilen. Das Ebenenpanel lässt sich schmaler ziehen als zuvor. Das OpenStrand Studio Logo erscheint jetzt in jedem Fenster und in der Taskleiste."),
  ("Dialoge passen auf kleine Bildschirme", "Der Dialog Einstellungen kann jetzt verkleinert werden, sodass seine Schaltflächen Übernehmen und OK immer sichtbar bleiben. Dasselbe gilt für Schatten bearbeiten, den Gruppenschatten-Editor, Maskenraster Erstellen, Strangwinkel bearbeiten, Breite ändern und den Videoplayer. Ein Dialog öffnet sich nie größer als Ihr Bildschirm und behält die Größe, die Sie ihm geben."),
  ("Flüssigeres Ziehen", "Die Zeichenfläche bleibt beim Ziehen scharf, auch auf skalierten Bildschirmen oder mit eingeschaltetem Supersampling. Der Verschiebemodus zeigt beim Ziehen eines Punktes eine geschlossene Hand. Der Ansichtsmodus kann jetzt auch mit der linken Maustaste verschoben werden. Der Tooltip der Schaltfläche Aktualisieren sagt jetzt, was sie tut: Ebenen neu laden und Ansicht zurücksetzen."),
  ('Russisch, Finnisch, Schwedisch, Japanisch und Chinesisch', 'Die App ist jetzt auch auf Russisch, Finnisch, Schwedisch, Japanisch und Chinesisch verfügbar. Wählen Sie die Sprache in den Einstellungen unter Sprache ändern: Jede Schaltfläche, jedes Menü, jeder Dialog und jeder Hilfetext ist übersetzt, und jede Sprache hat ihre Flagge in der Liste.'),
 ],
 'it': [
  ("Stilizza il lato finale", "Fai clic destro su un livello con un'estremità libera e scegli Stilizza il lato finale, subito sotto Chiudi il Nodo. Una finestra ti permette di scegliere come termina il trefolo: Dritta, Inclinata, Arrotondata, Appuntita, Intagliata o Concava. Puoi anche regolare inclinazione e profondità, allungare o accorciare l'estremità e aggiungere una linea laterale con spessore e colore propri. L'anteprima è dal vivo sulla tela. Ombra, linea laterale e maschere seguono tutte la nuova forma. Gli stili delle estremità vengono salvati con il progetto e funzionano con annulla e ripristina."),
  ("Dimensione giusta sugli schermi ridimensionati", "Sugli schermi ad alta risoluzione con il ridimensionamento attivo, pulsanti e testo apparivano troppo piccoli. L'app ora segue la scala del tuo schermo. Le etichette della barra degli strumenti non vengono più tagliate, e la barra passa su due righe quando la finestra è stretta. Il pannello dei livelli può essere ristretto più di prima. Il logo di OpenStrand Studio appare ora su ogni finestra e nella barra delle applicazioni."),
  ("Finestre adatte agli schermi piccoli", "La finestra Impostazioni ora può essere rimpicciolita, così i pulsanti Applica e OK restano sempre visibili. Lo stesso vale per Modifica ombra, l'editor dell'ombra di gruppo, Crea Griglia Maschera, Modifica Angoli Trefolo, Cambia larghezza e il lettore video. Una finestra non si apre mai più grande dello schermo e mantiene la dimensione che le dai."),
  ("Trascinamento più fluido", "La tela resta nitida mentre trascini, anche su schermi ridimensionati o con il supersampling attivo. La modalità sposta mostra una mano chiusa mentre trascini un punto. La modalità vista ora può scorrere anche con il tasto sinistro del mouse. Il suggerimento del pulsante Aggiorna ora dice cosa fa: ricarica i livelli e reimposta la vista."),
  ('Russo, finlandese, svedese, giapponese e cinese', "L'app è ora disponibile in russo, finlandese, svedese, giapponese e cinese. Scegli la lingua in Impostazioni, sotto Cambia lingua: ogni pulsante, menu, finestra e testo di aiuto è tradotto, e ogni lingua ha la sua bandiera nell'elenco."),
 ],
 'es': [
  ("Estilizar lado del extremo", "Haz clic derecho en una capa con un extremo libre y elige Estilizar lado del extremo, justo debajo de Cerrar el Nudo. Un cuadro de diálogo te permite elegir cómo termina el cordón: Recto, Inclinado, Redondeado, Puntiagudo, Con muesca o Cóncavo. También puedes ajustar la inclinación y la profundidad, alargar o recortar el extremo, y añadir una línea lateral con su propio grosor y color. La vista previa es en vivo sobre el lienzo. La sombra, la línea lateral y las máscaras siguen la nueva forma. Los estilos de extremo se guardan con tu proyecto y funcionan con deshacer y rehacer."),
  ("Tamaño correcto en pantallas escaladas", "En pantallas de alta resolución con el escalado activado, los botones y el texto se veían demasiado pequeños. La aplicación ahora sigue la escala de tu pantalla. Las etiquetas de la barra de herramientas ya no se cortan, y la barra pasa a dos filas cuando la ventana es estrecha. El panel de capas se puede estrechar más que antes. El logotipo de OpenStrand Studio aparece ahora en cada ventana y en la barra de tareas."),
  ("Diálogos que caben en pantallas pequeñas", "El diálogo Configuración ahora se puede hacer más pequeño, así sus botones Aplicar y OK siempre quedan en pantalla. Lo mismo ocurre con Editar sombra, el editor de sombra de grupo, Crear Cuadrícula de Máscara, Editar Ángulos del Cordón, Cambiar ancho y el reproductor de video. Un diálogo nunca se abre más grande que tu pantalla, y conserva el tamaño que le das."),
  ("Arrastre más suave", "El lienzo se mantiene nítido mientras arrastras, incluso en pantallas escaladas o con el supermuestreo activado. El modo mover muestra una mano cerrada mientras arrastras un punto. El modo vista ahora también puede desplazarse con el botón izquierdo del ratón. La descripción del botón Actualizar ahora dice lo que hace: recargar las capas y restablecer la vista."),
  ('Ruso, finés, sueco, japonés y chino', 'La aplicación ya está disponible en ruso, finés, sueco, japonés y chino. Elige el idioma en Configuración, bajo Cambiar idioma: todos los botones, menús, diálogos y textos de ayuda están traducidos, y cada idioma tiene su bandera en la lista.'),
 ],
 'pt': [
  ("Estilizar lado da extremidade", "Clique com o botão direito numa camada com uma extremidade livre e escolha Estilizar lado da extremidade, logo abaixo de Fechar o Nó. Uma janela permite escolher como a mecha termina: Reta, Inclinada, Arredondada, Pontiaguda, Entalhada ou Côncava. Também pode ajustar a inclinação e a profundidade, alongar ou encurtar a extremidade e adicionar uma linha lateral com espessura e cor próprias. A pré-visualização é ao vivo na tela. A sombra, a linha lateral e as máscaras seguem todas a nova forma. Os estilos de extremidade são salvos com o projeto e funcionam com desfazer e refazer."),
  ("Tamanho certo em ecrãs com escala", "Em ecrãs de alta resolução com a escala de exibição ativada, os botões e o texto pareciam pequenos demais. A aplicação agora segue a escala do seu ecrã. Os rótulos da barra de ferramentas já não são cortados, e a barra passa para duas linhas quando a janela é estreita. O painel de camadas pode ser estreitado mais do que antes. O logótipo do OpenStrand Studio aparece agora em todas as janelas e na barra de tarefas."),
  ("Janelas que cabem em ecrãs pequenos", "A janela Configurações agora pode ser reduzida, para que os botões Aplicar e OK fiquem sempre visíveis. O mesmo vale para Editar sombra, o editor de sombra de grupo, Criar Grade de Máscara, Editar Ângulos da Mecha, Mudar largura e o reprodutor de vídeo. Uma janela nunca abre maior do que o seu ecrã e mantém o tamanho que lhe der."),
  ("Arrasto mais suave", "A tela permanece nítida enquanto arrasta, mesmo em ecrãs com escala ou com a superamostragem ativada. O modo mover mostra uma mão fechada enquanto arrasta um ponto. O modo de visualização agora também pode deslocar-se com o botão esquerdo do rato. A dica do botão Atualizar agora diz o que ele faz: recarregar as camadas e redefinir a vista."),
  ('Russo, finlandês, sueco, japonês e chinês', 'A aplicação está agora disponível em russo, finlandês, sueco, japonês e chinês. Escolha o idioma em Configurações, em Mudar idioma: todos os botões, menus, janelas e textos de ajuda estão traduzidos, e cada idioma tem a sua bandeira na lista.'),
 ],
 'he': [
  ("עיצוב צד הקצה", "לחצו לחיצה ימנית על שכבה עם קצה חופשי ובחרו עיצוב צד הקצה, ממש מתחת לסגור את הקשר. חלון דו-שיח מאפשר לבחור איך החוט מסתיים: ישר, משופע, מעוגל, מחודד, חרוץ או קעור. אפשר גם לכוון את ההטיה והעומק, להאריך או לקצר את הקצה, ולהוסיף קו צד עם עובי וצבע משלו. התצוגה המקדימה חיה על הקנבס. הצל, קו הצד והמסכות עוקבים כולם אחרי הצורה החדשה. סגנונות הקצה נשמרים עם הפרויקט ועובדים עם ביטול וביצוע מחדש."),
  ("גודל נכון במסכים עם קנה מידה", "במסכים ברזולוציה גבוהה עם קנה מידה של התצוגה מופעל, הכפתורים והטקסט נראו קטנים מדי. האפליקציה עוקבת כעת אחרי קנה המידה של המסך שלכם. תוויות סרגל הכלים כבר לא נחתכות, וסרגל הכלים עובר לשתי שורות כשהחלון צר. את לוח השכבות אפשר לגרור צר יותר מבעבר. הלוגו של OpenStrand Studio מופיע כעת בכל חלון ובשורת המשימות."),
  ("חלונות שמתאימים למסכים קטנים", "את חלון ההגדרות אפשר כעת להקטין, כך שכפתורי החל ואישור נשארים תמיד על המסך. כך גם עריכת צל, עורך הצל של הקבוצה, צור רשת מסכות, ערוך זוויות חוט, שנה רוחב ונגן הווידאו. חלון לעולם לא נפתח גדול מהמסך שלכם, והוא שומר על הגודל שנתתם לו."),
  ("גרירה חלקה יותר", "הקנבס נשאר חד בזמן הגרירה, גם במסכים עם קנה מידה או עם דגימת-יתר מופעלת. מצב הזזה מציג יד סגורה בזמן גרירת נקודה. מצב תצוגה יכול כעת להזיז את התצוגה גם עם הכפתור השמאלי של העכבר. הטיפ של כפתור הרענון אומר כעת מה הוא עושה: טוען מחדש שכבות ומאפס את התצוגה."),
  ('רוסית, פינית, שוודית, יפנית וסינית', 'האפליקציה זמינה כעת גם ברוסית, בפינית, בשוודית, ביפנית ובסינית. בחרו את השפה בהגדרות, תחת שינוי שפה: כל כפתור, תפריט, חלון וטקסט עזרה מתורגמים, ולכל שפה יש דגל ברשימה.'),
 ],
 'ru': [
  ('Оформление конца', 'щёлкните правой кнопкой по слою со свободным концом и выберите «Оформить конец» сразу под пунктом «Замкнуть узел». В диалоге можно выбрать, как заканчивается прядь: прямой, скошенный, скруглённый, заострённый, с вырезом или вогнутый конец. Также можно задать наклон и глубину, удлинить или укоротить конец и добавить боковую линию со своей толщиной и цветом. Предпросмотр отображается на холсте сразу. Тень, боковая линия и маски следуют новой форме. Стили концов сохраняются вместе с проектом и работают с отменой и повтором.'),
  ('Правильный размер на масштабированных экранах', 'на экранах с высоким разрешением и включённым масштабированием кнопки и текст выглядели слишком мелко. Теперь приложение учитывает масштаб экрана. Надписи на панели инструментов больше не обрезаются, а при узком окне панель переносится на две строки. Панель слоёв можно сузить сильнее, чем раньше. Логотип OpenStrand Studio теперь показывается в каждом окне и на панели задач.'),
  ('Диалоги помещаются на маленьких экранах', 'диалог настроек теперь можно уменьшить, поэтому кнопки «Применить» и «ОК» всегда остаются на экране. То же касается редактора теней, редактора теней группы, создания сетки масок, изменения углов прядей, изменения ширины и видеоплеера. Диалог никогда не открывается больше экрана и сохраняет заданный вами размер.'),
  ('Более плавное перетаскивание', 'холст остаётся чётким во время перетаскивания даже на масштабированных экранах или при включённом суперсэмплинге. В режиме перемещения при перетаскивании точки показывается сжатая ладонь. В режиме обзора теперь можно панорамировать и левой кнопкой мыши. Подсказка кнопки «Обновить» теперь говорит, что она делает: перезагружает слои и сбрасывает вид.'),
  ('Русский, финский, шведский, японский и китайский', 'приложение теперь доступно на русском, финском, шведском, японском и китайском языках. Выберите язык в настройках, в разделе «Сменить язык»: переведены все кнопки, меню, диалоги и справочные тексты, а у каждого языка в списке есть свой флаг.'),
 ],
 'fi': [
  ('Muotoile pää', 'napsauta hiiren oikealla painikkeella tasoa, jolla on vapaa pää, ja valitse Muotoile pää heti Sulje solmu -kohdan alta. Ikkunassa voit valita, miten säie päättyy: suora, viisto, pyöristetty, terävä, lovettu tai kovera. Voit myös asettaa kallistuksen ja syvyyden, pidentää tai lyhentää päätä sekä lisätä sivuviivan, jolla on oma paksuus ja väri. Esikatselu näkyy piirtoalueella heti. Varjo, sivuviiva ja maskit seuraavat uutta muotoa. Pään tyylit tallentuvat projektin mukana ja toimivat kumoamisen ja uudelleentekemisen kanssa.'),
  ('Oikea koko skaalatuilla näytöillä', 'korkean resoluution näytöillä, joilla näytön skaalaus on päällä, painikkeet ja teksti näyttivät ennen liian pieniltä. Sovellus noudattaa nyt näytön skaalausta. Työkalupalkin tekstit eivät enää katkea, ja työkalupalkki siirtyy kahdelle riville, kun ikkuna on kapea. Tasopaneelin voi vetää entistä kapeammaksi. OpenStrand Studion logo näkyy nyt jokaisessa ikkunassa ja tehtäväpalkissa.'),
  ('Ikkunat mahtuvat pienille näytöille', 'Asetukset-ikkunan voi nyt pienentää, joten sen Käytä- ja OK-painikkeet pysyvät aina näytöllä. Sama koskee varjoeditoria, ryhmän varjoeditoria, maskiruudukon luontia, säikeiden kulmien muokkausta, leveyden muutosta ja videosoitinta. Ikkuna ei koskaan avaudu näyttöä suurempana, ja se säilyttää antamasi koon.'),
  ('Sujuvampi raahaus', 'piirtoalue pysyy terävänä raahauksen aikana myös skaalatuilla näytöillä tai ylinäytteistyksen ollessa päällä. Siirtotila näyttää suljetun käden pistettä raahattaessa. Katselutilassa voi nyt panoroida myös hiiren vasemmalla painikkeella. Päivitä-painikkeen vihje kertoo nyt, mitä se tekee: lataa tasot uudelleen ja palauttaa näkymän.'),
  ('Venäjä, suomi, ruotsi, japani ja kiina', 'Sovellus on nyt saatavilla venäjäksi, suomeksi, ruotsiksi, japaniksi ja kiinaksi. Valitse kieli asetuksista kohdasta Vaihda kieli: jokainen painike, valikko, ikkuna ja ohjeteksti on käännetty, ja jokaisella kielellä on oma lippunsa luettelossa.'),
 ],
 'sv': [
  ('Forma ändsida', 'högerklicka på ett lager med en fri ände och välj Forma ändsida, strax under Slut knopen. I en dialog väljer du hur strängen slutar: rak, vinklad, rundad, spetsig, skårad eller konkav. Du kan också ställa in lutning och djup, förlänga eller korta änden och lägga till en sidolinje med egen tjocklek och färg. Förhandsvisningen är live på arbetsytan. Skuggan, sidolinjen och maskerna följer alla den nya formen. Ändstilar sparas med projektet och fungerar med ångra och gör om.'),
  ('Rätt storlek på skalade skärmar', 'på högupplösta skärmar med skärmskalning påslagen såg knappar och text för små ut. Programmet följer nu din skärmskalning. Verktygsfältets etiketter klipps inte längre av, och verktygsfältet läggs på två rader när fönstret är smalt. Lagerpanelen kan dras smalare än förut. OpenStrand Studio-logotypen visas nu i varje fönster och i aktivitetsfältet.'),
  ('Dialoger får plats på små skärmar', 'inställningsdialogen kan nu göras mindre, så att dess Verkställ- och OK-knappar alltid stannar på skärmen. Detsamma gäller Redigera skugga, gruppens skuggredigerare, Skapa maskrutnät, Redigera strängvinklar, Ändra bredd och videospelaren. En dialog öppnas aldrig större än skärmen, och den behåller storleken du ger den.'),
  ('Mjukare dragning', 'arbetsytan förblir skarp medan du drar, även på skalade skärmar eller med supersampling påslaget. Flyttläget visar en knuten hand när en punkt dras. Vyläget kan nu panorera även med vänster musknapp. Uppdatera-knappens verktygstips säger nu vad den gör: laddar om lagren och återställer vyn.'),
  ('Ryska, finska, svenska, japanska och kinesiska', 'Programmet finns nu på ryska, finska, svenska, japanska och kinesiska. Välj språk i Inställningar under Byt språk: varje knapp, meny, dialog och hjälptext är översatt, och varje språk har sin flagga i listan.'),
 ],
 'ja': [
  ('端のスタイル設定', '自由な端を持つレイヤーを右クリックし、「結び目を閉じる」のすぐ下にある「端のスタイル設定」を選びます。ダイアログでストランドの終わり方を選べます: 直線、斜め、丸み、尖り、切り欠き、凹み。傾きと深さの設定、端の延長や切り詰め、独自の太さと色を持つサイドラインの追加もできます。プレビューはキャンバス上にリアルタイムで表示されます。影、サイドライン、マスクはすべて新しい形に追従します。端のスタイルはプロジェクトと一緒に保存され、元に戻す/やり直しにも対応します。'),
  ('拡大表示の画面で適切なサイズに', '表示の拡大縮小を有効にした高解像度の画面では、ボタンや文字が小さく見えていました。アプリは画面の拡大率に従うようになりました。ツールバーのラベルが切れなくなり、ウィンドウが狭いときはツールバーが2行になります。レイヤーパネルは以前より細くドラッグできます。OpenStrand Studio のロゴがすべてのウィンドウとタスクバーに表示されます。'),
  ('小さな画面に収まるダイアログ', '設定ダイアログを小さくできるようになり、「適用」と「OK」のボタンが常に画面内に収まります。影の編集、グループ影エディター、マスクグリッドの作成、ストランドの角度を編集、幅を変更、動画プレーヤーも同様です。ダイアログは画面より大きく開くことはなく、指定したサイズを保ちます。'),
  ('より滑らかなドラッグ', '拡大表示の画面やスーパーサンプリングが有効なときでも、ドラッグ中のキャンバスは鮮明なままです。移動モードでは点をドラッグ中に握った手のカーソルが表示されます。表示モードでは左マウスボタンでもパンできるようになりました。更新ボタンのツールチップが実際の動作を示すようになりました: レイヤーを再読み込みして表示をリセット。'),
  ('ロシア語、フィンランド語、スウェーデン語、日本語、中国語', 'アプリがロシア語、フィンランド語、スウェーデン語、日本語、中国語で使えるようになりました。設定の「言語を変更」で言語を選んでください。すべてのボタン、メニュー、ダイアログ、ヘルプテキストが翻訳され、各言語には一覧に国旗が表示されます。'),
 ],
 'zh': [
  ('末端样式', '右键点击有自由端的图层，在“闭合绳结”正下方选择“末端样式”。对话框可让你选择绳股的收尾方式: 平直、斜切、圆角、尖角、缺口或凹陷。还可以设置倾斜和深度、延长或修剪末端，并添加带有独立粗细和颜色的侧线。预览会实时显示在画布上。阴影、侧线和遮罩都会跟随新形状。末端样式随项目保存，并支持撤销和重做。'),
  ('缩放屏幕上的正确尺寸', '在开启了显示缩放的高分辨率屏幕上，按钮和文字以前看起来太小。应用现在会遵循你的显示缩放。工具栏标签不再被截断，窗口较窄时工具栏会换成两行。图层面板可以拖得比以前更窄。OpenStrand Studio 的标志现在显示在每个窗口和任务栏中。'),
  ('对话框适应小屏幕', '设置对话框现在可以缩小，因此“应用”和“确定”按钮始终留在屏幕上。编辑阴影、组阴影编辑器、创建遮罩网格、编辑绳股角度、更改宽度和视频播放器也是如此。对话框打开时绝不会大于屏幕，并且会保持你设置的大小。'),
  ('更流畅的拖动', '拖动时画布保持清晰，即使在缩放屏幕上或开启超级采样时也是如此。移动模式下拖动点时会显示握紧的手形光标。查看模式现在也可以用鼠标左键平移。刷新按钮的提示现在说明了它的作用: 重新加载图层并重置视图。'),
  ('俄语、芬兰语、瑞典语、日语和中文', '应用现已支持俄语、芬兰语、瑞典语、日语和中文。在“设置”的“更改语言”中选择语言: 所有按钮、菜单、对话框和帮助文本都已翻译，每种语言在列表中都有自己的国旗。'),
 ],
}

# A short unique substring of each language's FIRST bullet title in the OLD
# version's files, used to recognize which language a <ul> block belongs to.
# Update these to match the previous release's first bullet. For Hebrew give
# the &#x....; entity form of the first few letters (as it appears in the .sh).
MARKERS = {
 'en': "Layer-Only Colors",
 'fr': "Couleurs par calque",
 'de': "Ebenen-eigene Farben",
 'it': "Colori per singolo livello",
 'es': "Colores por capa",
 'pt': "Cores por camada",
 'he': "&#x05E6;&#x05D1;&#x05E2;&#x05D9;&#x05DD; &#x05DC;&#x05E9;&#x05DB;&#x05D1;&#x05D4;",
 'ru': 'Оформление конца',
 'fi': 'Muotoile pää',
 'sv': 'Forma ändsida',
 'ja': '端のスタイル設定',
 'zh': '末端样式',
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

def li_block_translations(lang):
    return '\n'.join('            <li style="font-size:14px;"><b>%s:</b> %s</li>' % (t, x)
                     for t, x in BULLETS[lang])

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

    counts = {k: 0 for k in BULLETS}
    def repl(m):
        attrs, inner = m.group(1), m.group(2)
        for lang, marker in MARKERS.items():
            if marker in inner:
                counts[lang] += 1
                return '<ul%s>\n%s\n    </ul>' % (attrs, li_block_sh(lang))
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
                   % (m.group(1), pre.format(v=NEW_VERSION), iss_bullets(lang), post))
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
                % (h2, NEW_VERSION, li_block_translations(lang), m.group(1), cp, NEW_VERSION))
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

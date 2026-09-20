# -*- coding: utf-8 -*-
"""Generate all release files for a new OpenStrand Studio version.

For each release (e.g. 1.109 -> 1.110), edit ONLY the CONFIG section below:
  1. OLD_VERSION / NEW_VERSION and the two date strings
  2. The BULLETS dict: the what's-new bullets in all 7 languages

Then run from the repo root (or anywhere):
    python scripts/make_release_files.py

It reads the previous version's files and produces:
  - src/inno setup/OpenStrand Studio<NEW>.iss     (Windows installer)
  - src/build_installer_<NEW>.sh                  (macOS .pkg)
  - src/build_dmg_<NEW>.sh                        (macOS .dmg)
  - src/build_mac_<NEW>.sh                        (macOS one-command build)
  - updates src/translations.py                   (7 whats_new_info blocks)
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
NEW_DATE_SH = '20_September_2026'
OLD_DATE_ISS = '07_Sep_2026'   # MyAppDate in the old .iss
NEW_DATE_ISS = '20_Sep_2026'

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
 ],
 'fr': [
  ("Styliser le côté d'extrémité", "Faites un clic droit sur un calque ayant une extrémité libre et choisissez Styliser le côté d'extrémité, juste sous Fermer le Nœud. Une boîte de dialogue vous laisse choisir la forme de l'extrémité du brin : Droite, Inclinée, Arrondie, Pointue, Entaillée ou Concave. Vous pouvez aussi régler l'inclinaison et la profondeur, allonger ou raccourcir l'extrémité, et ajouter une ligne latérale avec sa propre épaisseur et sa propre couleur. L'aperçu est en direct sur le canevas. L'ombre, la ligne latérale et les masques suivent tous la nouvelle forme. Les styles d'extrémité sont enregistrés avec votre projet et fonctionnent avec annuler et rétablir."),
  ("La bonne taille sur les écrans mis à l'échelle", "Sur les écrans haute résolution avec une mise à l'échelle de l'affichage, les boutons et le texte paraissaient trop petits. L'application suit désormais l'échelle de votre écran. Les libellés de la barre d'outils ne sont plus coupés, et la barre d'outils passe sur deux lignes quand la fenêtre est étroite. Le panneau des calques peut être réduit plus qu'avant. Le logo OpenStrand Studio apparaît maintenant sur chaque fenêtre et dans la barre des tâches."),
  ("Des boîtes de dialogue adaptées aux petits écrans", "La boîte de dialogue Paramètres peut désormais être réduite, de sorte que ses boutons Appliquer et OK restent toujours à l'écran. Il en va de même pour Modifier l'ombre, l'éditeur d'ombre de groupe, Créer Grille de Masque, Modifier les angles des brins, Changer largeur et le lecteur vidéo. Une boîte de dialogue ne s'ouvre jamais plus grande que votre écran, et elle garde la taille que vous lui donnez."),
  ("Un glissement plus fluide", "Le canevas reste net pendant que vous faites glisser, même sur les écrans mis à l'échelle ou avec le suréchantillonnage activé. Le mode déplacement affiche une main fermée pendant le glissement d'un point. Le mode vue peut maintenant aussi se déplacer avec le bouton gauche de la souris. L'info-bulle du bouton Actualiser indique désormais ce qu'il fait : recharger les calques et réinitialiser la vue."),
 ],
 'de': [
  ("Endseite gestalten", "Klicken Sie mit der rechten Maustaste auf eine Ebene mit einem freien Ende und wählen Sie Endseite gestalten, direkt unter Knoten schließen. In einem Dialog wählen Sie, wie der Strang endet: Gerade, Schräg, Abgerundet, Spitz, Eingekerbt oder Konkav. Sie können außerdem Neigung und Tiefe einstellen, das Ende verlängern oder kürzen und eine Seitenlinie mit eigener Dicke und Farbe hinzufügen. Die Vorschau erscheint live auf der Zeichenfläche. Schatten, Seitenlinie und Masken folgen alle der neuen Form. Endstile werden mit dem Projekt gespeichert und funktionieren mit Rückgängig und Wiederherstellen."),
  ("Richtige Größe auf skalierten Bildschirmen", "Auf hochauflösenden Bildschirmen mit aktivierter Anzeigeskalierung wirkten Schaltflächen und Text zu klein. Die App folgt jetzt Ihrer Anzeigeskalierung. Beschriftungen in der Werkzeugleiste werden nicht mehr abgeschnitten, und die Werkzeugleiste wechselt bei schmalen Fenstern auf zwei Zeilen. Das Ebenenpanel lässt sich schmaler ziehen als zuvor. Das OpenStrand Studio Logo erscheint jetzt in jedem Fenster und in der Taskleiste."),
  ("Dialoge passen auf kleine Bildschirme", "Der Dialog Einstellungen kann jetzt verkleinert werden, sodass seine Schaltflächen Übernehmen und OK immer sichtbar bleiben. Dasselbe gilt für Schatten bearbeiten, den Gruppenschatten-Editor, Maskenraster Erstellen, Strangwinkel bearbeiten, Breite ändern und den Videoplayer. Ein Dialog öffnet sich nie größer als Ihr Bildschirm und behält die Größe, die Sie ihm geben."),
  ("Flüssigeres Ziehen", "Die Zeichenfläche bleibt beim Ziehen scharf, auch auf skalierten Bildschirmen oder mit eingeschaltetem Supersampling. Der Verschiebemodus zeigt beim Ziehen eines Punktes eine geschlossene Hand. Der Ansichtsmodus kann jetzt auch mit der linken Maustaste verschoben werden. Der Tooltip der Schaltfläche Aktualisieren sagt jetzt, was sie tut: Ebenen neu laden und Ansicht zurücksetzen."),
 ],
 'it': [
  ("Stilizza il lato finale", "Fai clic destro su un livello con un'estremità libera e scegli Stilizza il lato finale, subito sotto Chiudi il Nodo. Una finestra ti permette di scegliere come termina il trefolo: Dritta, Inclinata, Arrotondata, Appuntita, Intagliata o Concava. Puoi anche regolare inclinazione e profondità, allungare o accorciare l'estremità e aggiungere una linea laterale con spessore e colore propri. L'anteprima è dal vivo sulla tela. Ombra, linea laterale e maschere seguono tutte la nuova forma. Gli stili delle estremità vengono salvati con il progetto e funzionano con annulla e ripristina."),
  ("Dimensione giusta sugli schermi ridimensionati", "Sugli schermi ad alta risoluzione con il ridimensionamento attivo, pulsanti e testo apparivano troppo piccoli. L'app ora segue la scala del tuo schermo. Le etichette della barra degli strumenti non vengono più tagliate, e la barra passa su due righe quando la finestra è stretta. Il pannello dei livelli può essere ristretto più di prima. Il logo di OpenStrand Studio appare ora su ogni finestra e nella barra delle applicazioni."),
  ("Finestre adatte agli schermi piccoli", "La finestra Impostazioni ora può essere rimpicciolita, così i pulsanti Applica e OK restano sempre visibili. Lo stesso vale per Modifica ombra, l'editor dell'ombra di gruppo, Crea Griglia Maschera, Modifica Angoli Trefolo, Cambia larghezza e il lettore video. Una finestra non si apre mai più grande dello schermo e mantiene la dimensione che le dai."),
  ("Trascinamento più fluido", "La tela resta nitida mentre trascini, anche su schermi ridimensionati o con il supersampling attivo. La modalità sposta mostra una mano chiusa mentre trascini un punto. La modalità vista ora può scorrere anche con il tasto sinistro del mouse. Il suggerimento del pulsante Aggiorna ora dice cosa fa: ricarica i livelli e reimposta la vista."),
 ],
 'es': [
  ("Estilizar lado del extremo", "Haz clic derecho en una capa con un extremo libre y elige Estilizar lado del extremo, justo debajo de Cerrar el Nudo. Un cuadro de diálogo te permite elegir cómo termina el cordón: Recto, Inclinado, Redondeado, Puntiagudo, Con muesca o Cóncavo. También puedes ajustar la inclinación y la profundidad, alargar o recortar el extremo, y añadir una línea lateral con su propio grosor y color. La vista previa es en vivo sobre el lienzo. La sombra, la línea lateral y las máscaras siguen la nueva forma. Los estilos de extremo se guardan con tu proyecto y funcionan con deshacer y rehacer."),
  ("Tamaño correcto en pantallas escaladas", "En pantallas de alta resolución con el escalado activado, los botones y el texto se veían demasiado pequeños. La aplicación ahora sigue la escala de tu pantalla. Las etiquetas de la barra de herramientas ya no se cortan, y la barra pasa a dos filas cuando la ventana es estrecha. El panel de capas se puede estrechar más que antes. El logotipo de OpenStrand Studio aparece ahora en cada ventana y en la barra de tareas."),
  ("Diálogos que caben en pantallas pequeñas", "El diálogo Configuración ahora se puede hacer más pequeño, así sus botones Aplicar y OK siempre quedan en pantalla. Lo mismo ocurre con Editar sombra, el editor de sombra de grupo, Crear Cuadrícula de Máscara, Editar Ángulos del Cordón, Cambiar ancho y el reproductor de video. Un diálogo nunca se abre más grande que tu pantalla, y conserva el tamaño que le das."),
  ("Arrastre más suave", "El lienzo se mantiene nítido mientras arrastras, incluso en pantallas escaladas o con el supermuestreo activado. El modo mover muestra una mano cerrada mientras arrastras un punto. El modo vista ahora también puede desplazarse con el botón izquierdo del ratón. La descripción del botón Actualizar ahora dice lo que hace: recargar las capas y restablecer la vista."),
 ],
 'pt': [
  ("Estilizar lado da extremidade", "Clique com o botão direito numa camada com uma extremidade livre e escolha Estilizar lado da extremidade, logo abaixo de Fechar o Nó. Uma janela permite escolher como a mecha termina: Reta, Inclinada, Arredondada, Pontiaguda, Entalhada ou Côncava. Também pode ajustar a inclinação e a profundidade, alongar ou encurtar a extremidade e adicionar uma linha lateral com espessura e cor próprias. A pré-visualização é ao vivo na tela. A sombra, a linha lateral e as máscaras seguem todas a nova forma. Os estilos de extremidade são salvos com o projeto e funcionam com desfazer e refazer."),
  ("Tamanho certo em ecrãs com escala", "Em ecrãs de alta resolução com a escala de exibição ativada, os botões e o texto pareciam pequenos demais. A aplicação agora segue a escala do seu ecrã. Os rótulos da barra de ferramentas já não são cortados, e a barra passa para duas linhas quando a janela é estreita. O painel de camadas pode ser estreitado mais do que antes. O logótipo do OpenStrand Studio aparece agora em todas as janelas e na barra de tarefas."),
  ("Janelas que cabem em ecrãs pequenos", "A janela Configurações agora pode ser reduzida, para que os botões Aplicar e OK fiquem sempre visíveis. O mesmo vale para Editar sombra, o editor de sombra de grupo, Criar Grade de Máscara, Editar Ângulos da Mecha, Mudar largura e o reprodutor de vídeo. Uma janela nunca abre maior do que o seu ecrã e mantém o tamanho que lhe der."),
  ("Arrasto mais suave", "A tela permanece nítida enquanto arrasta, mesmo em ecrãs com escala ou com a superamostragem ativada. O modo mover mostra uma mão fechada enquanto arrasta um ponto. O modo de visualização agora também pode deslocar-se com o botão esquerdo do rato. A dica do botão Atualizar agora diz o que ele faz: recarregar as camadas e redefinir a vista."),
 ],
 'he': [
  ("עיצוב צד הקצה", "לחצו לחיצה ימנית על שכבה עם קצה חופשי ובחרו עיצוב צד הקצה, ממש מתחת לסגור את הקשר. חלון דו-שיח מאפשר לבחור איך החוט מסתיים: ישר, משופע, מעוגל, מחודד, חרוץ או קעור. אפשר גם לכוון את ההטיה והעומק, להאריך או לקצר את הקצה, ולהוסיף קו צד עם עובי וצבע משלו. התצוגה המקדימה חיה על הקנבס. הצל, קו הצד והמסכות עוקבים כולם אחרי הצורה החדשה. סגנונות הקצה נשמרים עם הפרויקט ועובדים עם ביטול וביצוע מחדש."),
  ("גודל נכון במסכים עם קנה מידה", "במסכים ברזולוציה גבוהה עם קנה מידה של התצוגה מופעל, הכפתורים והטקסט נראו קטנים מדי. האפליקציה עוקבת כעת אחרי קנה המידה של המסך שלכם. תוויות סרגל הכלים כבר לא נחתכות, וסרגל הכלים עובר לשתי שורות כשהחלון צר. את לוח השכבות אפשר לגרור צר יותר מבעבר. הלוגו של OpenStrand Studio מופיע כעת בכל חלון ובשורת המשימות."),
  ("חלונות שמתאימים למסכים קטנים", "את חלון ההגדרות אפשר כעת להקטין, כך שכפתורי החל ואישור נשארים תמיד על המסך. כך גם עריכת צל, עורך הצל של הקבוצה, צור רשת מסכות, ערוך זוויות חוט, שנה רוחב ונגן הווידאו. חלון לעולם לא נפתח גדול מהמסך שלכם, והוא שומר על הגודל שנתתם לו."),
  ("גרירה חלקה יותר", "הקנבס נשאר חד בזמן הגרירה, גם במסכים עם קנה מידה או עם דגימת-יתר מופעלת. מצב הזזה מציג יד סגורה בזמן גרירת נקודה. מצב תצוגה יכול כעת להזיז את התצוגה גם עם הכפתור השמאלי של העכבר. הטיפ של כפתור הרענון אומר כעת מה הוא עושה: טוען מחדש שכבות ומאפס את התצוגה."),
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
# 3) Inno Setup .iss: defines + the 7 WelcomeLabel2 lines
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
# 4) translations.py: the 7 whats_new_info blocks (in-app What's New dialog)
# ----------------------------------------------------------------------------
TR = {
 'en': ("What's New in Version", "© 2026 OpenStrand Studio - Version"),
 'fr': ("Nouveautés de la version", "© 2026 OpenStrand Studio - Version"),
 'de': ("Neu in Version", "© 2026 OpenStrand Studio - Version"),
 'it': ("Novità della versione", "© 2026 OpenStrand Studio - Versione"),
 'es': ("Novedades de la versión", "© 2026 OpenStrand Studio - Versión"),
 'pt': ("Novidades da versão", "© 2026 OpenStrand Studio – Versão"),
 'he': ("מה חדש בגרסה", "© 2026 OpenStrand Studio - גרסה"),
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

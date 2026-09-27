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
OLD_VERSION = '1.111'          # version the source files belong to
NEW_VERSION = '1.112'          # version to generate
OLD_DATE_SH = '22_September_2026'   # APP_DATE in the old .sh files
NEW_DATE_SH = '27_September_2026'
OLD_DATE_ISS = '22_Sep_2026'   # MyAppDate in the old .iss
NEW_DATE_ISS = '27_Sep_2026'

# What's-new bullets per language: list of (title, text). Same bullets are
# used for the Windows installer, the macOS installer pages, and the in-app
# "What's New?" dialog (translations.py). Write plain unicode text everywhere;
# Hebrew entity-encoding for the .sh files is handled automatically.
BULLETS = {
 'en': [
  ("Better Shadows Around Masks", "Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws."),
  ("Hidden Shadows Stay Hidden", "When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible."),
  ("Seven New Samples", "In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page."),
 ],
 'fr': [
  ("De plus belles ombres autour des masques", "Là où un masque fait passer un brin par-dessus un autre, les ombres ressemblent maintenant à un vrai croisement. Les coins sombres, les bosses et les entailles parasites près des masques ont disparu, et le brin soulevé reste net. L'aperçu Chemin d'Ombre de l'Éditeur d'Ombres montre maintenant exactement ce que dessine le canevas."),
  ("Les ombres masquées restent masquées", "Quand vous décochez une ombre dans l'Éditeur d'Ombres, elle disparaît maintenant entièrement. Avant, une petite bosse grise pouvait rester à côté d'un autre brin. Créer un masque ne cache plus non plus une ombre qui doit rester visible."),
  ("Sept nouveaux exemples", "Dans Paramètres, sous Exemples, vous trouverez sept nouveaux projets à ouvrir et à étudier : Tissage droit 12×12, Tissage courbe 6×6, Natte, Épais et fin, Pont, Paires torsadées et Tissage kagome. Les boutons des exemples sont maintenant deux par ligne, pour que toute la liste tienne sur la page."),
 ],
 'de': [
  ("Bessere Schatten an Masken", "Wo eine Maske einen Strang über einen anderen legt, sehen die Schatten jetzt aus wie bei einer echten Kreuzung. Die störenden dunklen Keile, Beulen und Dellen an Masken sind verschwunden, und der angehobene Strang bleibt sauber. Die Vorschau Schattenpfad im Schatten-Editor zeigt jetzt genau das, was die Zeichenfläche zeichnet."),
  ("Ausgeblendete Schatten bleiben ausgeblendet", "Wenn Sie einen Schatten im Schatten-Editor abwählen, verschwindet er jetzt ganz. Vorher konnte eine kleine graue Beule neben einem anderen Strang zurückbleiben. Beim Erstellen einer Maske werden außerdem keine Schatten mehr ausgeblendet, die sichtbar bleiben sollen."),
  ("Sieben neue Beispiele", "In den Einstellungen unter Beispiele finden Sie sieben neue Projekte zum Öffnen und Lernen: Gerades Geflecht 12×12, Geschwungenes Geflecht 6×6, Flechtzopf, Dick und dünn, Brücke, Verdrehte Paare und Kagome-Geflecht. Die Beispiel-Schaltflächen stehen jetzt zu zweit in einer Reihe, sodass die ganze Liste auf die Seite passt."),
 ],
 'it': [
  ("Ombre migliori intorno alle maschere", "Dove una maschera fa passare un trefolo sopra un altro, le ombre ora sembrano quelle di un vero incrocio. I cunei scuri, le gobbe e le tacche indesiderate vicino alle maschere sono spariti, e il trefolo sollevato resta pulito. L'anteprima Percorso Ombra dell'Editor di Ombre ora mostra esattamente ciò che la tela disegna."),
  ("Le ombre nascoste restano nascoste", "Quando togli la spunta a un'ombra nell'Editor di Ombre, ora sparisce del tutto. Prima poteva restare una piccola gobba grigia accanto a un altro trefolo. Creare una maschera inoltre non nasconde più un'ombra che deve restare visibile."),
  ("Sette nuovi esempi", "In Impostazioni, sotto Esempi, trovi sette nuovi progetti da aprire e da cui imparare: Intreccio dritto 12×12, Intreccio curvo 6×6, Treccia piatta, Spesso e sottile, Ponte, Coppie ritorte e Intreccio kagome. I pulsanti degli esempi ora sono due per riga, così l'elenco intero sta nella pagina."),
 ],
 'es': [
  ("Mejores sombras alrededor de las máscaras", "Donde una máscara pasa un cordón por encima de otro, las sombras ahora se ven como en un cruce real. Las cuñas oscuras, los bultos y las muescas sueltas cerca de las máscaras desaparecieron, y el cordón levantado queda limpio. La vista previa Ruta de Sombra del Editor de Sombras ahora muestra exactamente lo que dibuja el lienzo."),
  ("Las sombras ocultas siguen ocultas", "Cuando desmarcas una sombra en el Editor de Sombras, ahora desaparece por completo. Antes podía quedar un pequeño bulto gris junto a otro cordón. Además, crear una máscara ya no oculta una sombra que debe seguir visible."),
  ("Siete ejemplos nuevos", "En Configuración, bajo Ejemplos, encontrarás siete proyectos nuevos para abrir y aprender: Tejido recto 12×12, Tejido curvo 6×6, Trenza plana, Grueso y fino, Puente, Pares torcidos y Tejido kagome. Los botones de ejemplos ahora van de dos en dos por fila, así la lista entera cabe en la página."),
 ],
 'pt': [
  ("Sombras melhores à volta das máscaras", "Onde uma máscara passa uma mecha por cima de outra, as sombras agora parecem as de um cruzamento real. As cunhas escuras, os altos e os entalhes soltos perto das máscaras desapareceram, e a mecha levantada fica limpa. A pré-visualização Caminho de Sombra do Editor de Sombras agora mostra exatamente o que a tela desenha."),
  ("Sombras ocultas continuam ocultas", "Quando desmarca uma sombra no Editor de Sombras, ela agora desaparece por completo. Antes, podia ficar um pequeno alto cinzento ao lado de outra mecha. Criar uma máscara também já não oculta uma sombra que deve continuar visível."),
  ("Sete novos exemplos", "Em Configurações, em Exemplos, encontra sete novos projetos para abrir e aprender: Tecelagem reta 12×12, Tecelagem curva 6×6, Trança plana, Grosso e fino, Ponte, Pares torcidos e Tecelagem kagome. Os botões dos exemplos agora ficam dois por linha, para que a lista inteira caiba na página."),
 ],
 'he': [
  ("צללים טובים יותר סביב מסכות", "במקום שבו מסכה מעבירה חוט אחד מעל חוט אחר, הצללים נראים עכשיו בדיוק כמו בהצטלבות אמיתית. הטריזים הכהים, הבליטות והשקעים המיותרים ליד מסכות נעלמו, והחוט המורם נשאר נקי. התצוגה המקדימה נתיב צל בעורך הצללים מציגה עכשיו בדיוק את מה שמצויר על הקנבס."),
  ("צללים מוסתרים נשארים מוסתרים", "כשמבטלים את הסימון של צל בעורך הצללים, הוא נעלם עכשיו לגמרי. קודם יכלה להישאר בליטה אפורה קטנה ליד חוט אחר. גם יצירת מסכה כבר לא מסתירה צל שצריך להישאר גלוי."),
  ("שבע דוגמאות חדשות", "בהגדרות, תחת דוגמאות, יש שבעה פרויקטים חדשים לפתוח וללמוד מהם: אריגה ישרה 12×12, אריגה מעוקלת 6×6, צמה שטוחה, עבה ודק, גשר, זוגות מפותלים ואריגת קגומה. כפתורי הדוגמאות מסודרים עכשיו שניים בשורה, כך שכל הרשימה נכנסת בעמוד."),
 ],
 'ru': [
  ('Лучшие тени у масок', 'там, где маска поднимает одну прядь над другой, тени теперь выглядят как у настоящего пересечения. Лишние тёмные клинья, бугорки и вмятины возле масок исчезли, а поднятая прядь остаётся чистой. Предпросмотр «Контур тени» в редакторе теней теперь показывает ровно то, что рисуется на холсте.'),
  ('Скрытые тени остаются скрытыми', 'если снять флажок у тени в редакторе теней, она теперь исчезает полностью. Раньше рядом с другой прядью мог остаться маленький серый бугорок. Кроме того, создание маски больше не скрывает тень, которая должна оставаться видимой.'),
  ('Семь новых примеров', 'в настройках, в разделе «Примеры», появилось семь новых проектов, которые можно открыть и изучить: Прямое плетение 12×12, Изогнутое плетение 6×6, Плоская коса, Толстые и тонкие, Мост, Скрученные пары и Плетение кагомэ. Кнопки примеров теперь стоят по две в ряд, поэтому весь список помещается на странице.'),
 ],
 'fi': [
  ('Paremmat varjot maskien ympärillä', 'kun maski nostaa säikeen toisen yli, varjot näyttävät nyt aivan oikealta risteykseltä. Maskien lähellä olleet ylimääräiset tummat kiilat, kyhmyt ja painaumat ovat poissa, ja nostettu säie pysyy siistinä. Varjoeditorin Varjon polku -esikatselu näyttää nyt täsmälleen sen, mitä piirtoalueelle piirretään.'),
  ('Piilotetut varjot pysyvät piilossa', 'kun poistat varjon valinnan varjoeditorissa, se katoaa nyt kokonaan. Aiemmin toisen säikeen viereen saattoi jäädä pieni harmaa kyhmy. Maskin luominen ei myöskään enää piilota varjoa, jonka pitää näkyä.'),
  ('Seitsemän uutta esimerkkiä', 'asetuksissa, kohdassa Esimerkit, on seitsemän uutta projektia avattavaksi ja opittavaksi: Suora kudos 12×12, Kaareva kudos 6×6, Palmikko, Paksu ja ohut, Silta, Kierretyt parit ja Kagome-kudos. Esimerkkipainikkeet ovat nyt kaksi rinnakkain, joten koko luettelo mahtuu sivulle.'),
 ],
 'sv': [
  ('Bättre skuggor kring masker', 'där en mask lyfter en sträng över en annan ser skuggorna nu ut precis som vid en riktig korsning. De lösa mörka kilarna, bulorna och bucklorna nära masker är borta, och den lyfta strängen förblir ren. Förhandsvisningen Skuggbana i skuggredigeraren visar nu exakt det som ritas på arbetsytan.'),
  ('Dolda skuggor förblir dolda', 'när du avmarkerar en skugga i skuggredigeraren försvinner hela skuggan nu. Förut kunde en liten grå bula bli kvar bredvid en annan sträng. Att skapa en mask döljer inte heller längre en skugga som ska synas.'),
  ('Sju nya exempel', 'i Inställningar, under Exempel, finns sju nya projekt att öppna och lära sig av: Rak väv 12×12, Böjd väv 6×6, Platt fläta, Tjock och tunn, Bro, Tvinnade par och Kagomeväv. Exempelknapparna står nu två i varje rad, så hela listan får plats på sidan.'),
 ],
 'ja': [
  ('マスクまわりの影がきれいに', 'マスクで一方のストランドをもう一方の上に重ねた部分の影が、本物の交差と同じ見た目になりました。マスクの近くに出ていた余分な暗いくさび、こぶ、へこみはなくなり、持ち上げたストランドもきれいなままです。影エディターの「影のパス」プレビューは、キャンバスに描かれるとおりの影を表示するようになりました。'),
  ('非表示の影はきちんと非表示に', '影エディターで影のチェックを外すと、その影が完全に消えるようになりました。以前は、別のストランドの横に小さな灰色のこぶが残ることがありました。また、マスクを作成したときに、表示されるべき影が隠れることもなくなりました。'),
  ('7つの新しいサンプル', '設定の「サンプル」に、開いて学べる新しいプロジェクトが7つ加わりました: 直線の織り 12×12、曲線の織り 6×6、平編み、太い線と細い線、橋、ねじれたペア、かごめ編み。サンプルのボタンは1行に2つずつ並ぶようになり、一覧全体がページに収まります。'),
 ],
 'zh': [
  ('遮罩周围的阴影更好看', '在遮罩把一根绳股抬到另一根上方的地方，阴影现在看起来就像真正的交叉一样。遮罩附近多余的暗色楔形、凸起和凹痕都消失了，被抬起的绳股也保持干净。阴影编辑器中的“阴影路径”预览现在会准确显示画布上绘制的内容。'),
  ('隐藏的阴影保持隐藏', '在阴影编辑器中取消勾选某个阴影后，它现在会完全消失。以前，另一根绳股旁边可能会留下一个灰色的小凸起。另外，创建遮罩时也不会再隐藏本应显示的阴影。'),
  ('七个新示例', '在“设置”的“示例”中，新增了七个可以打开学习的项目: 直线编织 12×12、曲线编织 6×6、扁平辫、粗与细、桥、扭绞线对和笼目编织。示例按钮现在每行两个，整个列表可以完整显示在页面上。'),
 ],
}

# A short unique substring of each language's FIRST bullet title in the OLD
# version's files, used to recognize which language a <ul> block belongs to.
# Update these to match the previous release's first bullet. For Hebrew give
# the &#x....; entity form of the first few letters (as it appears in the .sh).
MARKERS = {
 'en': "Stylize End Side",
 'fr': "Styliser le côté d'extrémité",
 'de': "Endseite gestalten",
 'it': "Stilizza il lato finale",
 'es': "Estilizar lado del extremo",
 'pt': "Estilizar lado da extremidade",
 'he': "&#x05E2;&#x05D9;&#x05E6;&#x05D5;&#x05D1; &#x05E6;&#x05D3; &#x05D4;&#x05E7;&#x05E6;&#x05D4;",
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

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
OLD_VERSION = '1.109'          # version the source files belong to
NEW_VERSION = '1.110'          # version to generate
OLD_DATE_SH = '14_July_2026'   # APP_DATE in the old .sh files
NEW_DATE_SH = 'DD_Month_YYYY'  # e.g. '14_July_2026'
OLD_DATE_ISS = '14_Jul_2026'   # MyAppDate in the old .iss
NEW_DATE_ISS = 'DD_Mon_YYYY'   # e.g. '14_Jul_2026'

# What's-new bullets per language: list of (title, text). Same bullets are
# used for the Windows installer, the macOS installer pages, and the in-app
# "What's New?" dialog (translations.py). Write plain unicode text everywhere;
# Hebrew entity-encoding for the .sh files is handled automatically.
BULLETS = {
 'en': [
  ("Feature Title", "Feature description."),
 ],
 'fr': [
  ("Titre", "Description."),
 ],
 'de': [
  ("Titel", "Beschreibung."),
 ],
 'it': [
  ("Titolo", "Descrizione."),
 ],
 'es': [
  ("Título", "Descripción."),
 ],
 'pt': [
  ("Título", "Descrição."),
 ],
 'he': [
  ("כותרת", "תיאור."),
 ],
}

# A short unique substring of each language's FIRST bullet title in the OLD
# version's files, used to recognize which language a <ul> block belongs to.
# Update these to match the previous release's first bullet. For Hebrew give
# the &#x....; entity form of the first few letters (as it appears in the .sh).
MARKERS = {
 'en': "Lock Mode Redesigned",
 'fr': "Mode verrouillage repens",
 'de': "Sperrmodus",
 'it': "blocco ridisegnata",
 'es': "bloqueo redise",
 'pt': "bloqueio redesenhado",
 'he': "&#x05DE;&#x05E6;&#x05D1; &#x05E0;&#x05E2;&#x05D9;&#x05DC;&#x05D4;",
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

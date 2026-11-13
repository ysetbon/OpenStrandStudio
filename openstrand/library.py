"""The craft library: ready-made designs found by any name people use.

craft_library/catalog.json lists designs by craft (boondoggle, macrame,
Chinese knotting, knitting, crochet): a name, the other names people use,
one line about it and how it is built. The knot recipes beside it
(craft_library/<craft>/recipes/, see recipes.py), each with its tying steps,
and the knots `tie` makes from its own libraries are listed too. A request for "scoubidou", "cobra knot" or
"mystic knot" then finds its design by looking it up, not by drawing it.

It is a backend library: only the openstrand command and the agent read it.
Nothing in it is listed on the Samples page of the app's settings, and it is
not part of the app's installers (tests/test_craft_library.py checks both).

    from openstrand import library
    for entry in library.search('box stitch'):
        print(library.line(entry))
"""
import json
import re
import unicodedata

from . import ROOT

FOLDER = ROOT / 'craft_library'
CATALOG = FOLDER / 'catalog.json'
BUILDS = ('file', 'sample', 'mxn', 'turks_head', 'tie', 'make')

# Words in a request that say nothing about which design is meant.
_ASIDE = {'a', 'an', 'the', 'of', 'in', 'for', 'with', 'and', 'how', 'to', 'tie', 'make', 'do', 'i', 'me', 'show',
          'tutorial', 'pattern', 'design', 'sample', 'samples'}
# Words most entries share: they count only when the request has nothing else.
_COMMON = {'knot', 'knots', 'stitch', 'stitches'}


class LibraryError(ValueError):
    pass


def words(text):
    """Lower-case words without accents or apostrophes: "Turk's Macramé" -> turks, macrame."""
    plain = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode()
    return re.findall(r'[a-z0-9]+', plain.lower().replace("'", ''))


def read_catalog(path=CATALOG):
    """The catalog file as written: {'crafts': {craft: about}, 'entries': [...]}."""
    return json.loads(path.read_text(encoding='utf-8'))


def _knots():
    """An entry for every knot `tie` makes, from the knot libraries themselves."""
    from . import bends, tying
    out = []
    for key, title, _, _, aliases, about in tying.library():
        out.append(dict(name=title.lower(), craft='knots', title=title, also=list(aliases), about=about,
                        build={'tie': key}))
    for key, title, kind, _, _, _, about in bends.library():
        craft = 'macrame' if 'filler' in kind else 'knots'
        # Every other name the knot has (library() lists only the first few).
        also = [a for a in ([bends.LIBRARY[key].get('also')] + list(bends.LIBRARY[key]['aliases'])) if a]
        out.append(dict(name=title.lower(), craft=craft, title=title, also=list(dict.fromkeys(also)),
                        about=about, build={'tie': key}))
    return out


def _recipes():
    """An entry for every knot recipe of the craft library (craft_library/<craft>/recipes/)."""
    from . import recipes
    return [dict(name=name, craft=recipe['craft'], title=recipe['title'], also=list(recipe['aliases']),
                 about=recipe['about'], build={'tie': recipe['title'].lower()}, patterns=list(recipe['patterns']),
                 steps=len(recipe['steps']))
            for name, recipe in recipes.library().items()]


def entries():
    """Every entry: the catalog's, the craft library's knot recipes, then the other knots `tie` makes."""
    return [dict(e) for e in read_catalog()['entries']] + _recipes() + _knots()


def crafts():
    """{craft: one line about it} for the crafts the catalog knows."""
    return dict(read_catalog()['crafts'])


def _texts(entry):
    """The entry's words by weight: its names, its other names, the rest."""
    return (words(entry['name']) + words(entry['title']),
            [w for a in entry.get('also', ()) for w in words(a)],
            words(entry['craft']) + words(entry.get('about', '')))


def _names(entry):
    """Every name of an entry, as words."""
    return [words(n) for n in [entry['name'], entry['title']] + list(entry.get('also', ()))]


def search(text):
    """Entries that match every telling word of text, best first: one whose name is
    what was asked, then names before other names before descriptions. Empty text
    gives all."""
    asked = [w for w in words(text) if w not in _ASIDE]
    telling = [w for w in asked if w not in _COMMON] or asked
    if not telling:
        return entries()
    found = []
    for position, entry in enumerate(entries()):
        groups = _texts(entry)
        score = 0
        for word in telling:
            weights = [weight for weight, group in zip((4, 3, 1), groups)
                       if any(word in w or (len(w) > 3 and w in word) for w in group)]
            if not weights:
                break
            score += max(weights)
        else:
            # "square stitch" is the box stitch, not the square knot: the whole name, and
            # the common word (knot, stitch) asked for, settle it.
            score += 20 * (asked in _names(entry)) + sum(w in groups[0] + groups[1] for w in asked if w in _COMMON)
            found.append((-score, position, entry))
    return [entry for _, _, entry in sorted(found, key=lambda f: f[:2])]


def find(name):
    """The entry with this name, else the first with this title or other name (however
    it is spelled), or None."""
    asked = words(name)
    found = entries()
    return (next((entry for entry in found if asked == words(entry['name'])), None)
            or next((entry for entry in found if asked in _names(entry)), None))


def how(entry, cli=False):
    """The tool call (or the command, with cli) that makes the entry."""
    build = entry['build']
    kind, value = next(iter(build.items()))
    if kind in ('file', 'sample'):
        return f'make sample {entry["name"]}' if cli else f'load_sample name="{entry["name"]}"'
    if kind == 'mxn':
        extra = ''.join(f' --{k} {v}' if cli else f', {k}="{v}"' for k, v in value.items() if k == 'hand')
        stretch = (' --stretch' if cli else ', stretch=true') if value.get('stretch') else ''
        return (f'make mxn --m {value["m"]} --n {value["n"]}{extra}{stretch}' if cli
                else f'make_mxn m={value["m"]}, n={value["n"]}{extra}{stretch}')
    if kind == 'turks_head':
        return (f'make turks_head --leads {value["leads"]} --bights {value["bights"]}' if cli
                else f'make_turks_head leads={value["leads"]}, bights={value["bights"]}')
    if kind == 'tie':
        return f'tie "{value}"' if cli else f'tie_knot knot="{value}" (with its tying steps)'
    return f'make {value} with the size asked for' if cli else f'make_{value} with the size asked for'


def line(entry, cli=False):
    """One line about an entry: name, craft, what people call it, what it is, how to get it."""
    also = f' (also: {", ".join(entry["also"][:6])})' if entry.get('also') else ''
    about = entry.get('about', '').split('. ')[0].rstrip('.')
    return (f'{entry["name"]} · {entry["craft"]} · {entry["title"]}{also} · {about} · '
            f'get it: {how(entry, cli)}')


def path_of(entry):
    """The project file of an entry built from a file, inside the repository."""
    path = (ROOT / entry['build']['file']).resolve()
    if ROOT.resolve() not in path.parents:
        raise LibraryError(f'{entry["name"]}: its file is outside the repository')
    return path


def build(entry):
    """(project, warnings, source) for an entry a file or a generator makes."""
    from . import generators, project
    kind, value = next(iter(entry['build'].items()))
    if kind == 'file':
        return project.read(path_of(entry)), [], entry['name']
    if kind == 'sample':
        return generators.sample(value)
    if kind == 'mxn':
        return generators.mxn(value['m'], value['n'], value.get('hand', 'lh'), bool(value.get('stretch')))
    if kind == 'turks_head':
        from . import colors
        return generators.turks_head(value['leads'], value['bights'], colors.parse(value.get('color', 'teal')))
    raise LibraryError(f'"{entry["name"]}" is not one ready-made file: use {how(entry)} '
                       f'(the command: openstrand {how(entry, cli=True)})')

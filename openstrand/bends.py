"""Knots that join cords or make a loop, from checked drawings.

tying.py ties a knot in one cord by simulating it. These knots it cannot
simulate: a bend joins two cords, a bowline holds a loop, a macrame square
knot is tied round two other cords. Each is kept here as a drawing instead:
for every cord the points it passes through and how high it lies there, so
that where two parts cross, the higher one is on top. Nothing about a drawing
is left to the eye:

- its crossing code (invariants.code: every cord's crossings in order, over
  or under at each) must be the reference written next to it, letter for
  letter, before anything is built;
- the built design is read back from its strands, masks and layers, the way
  the app draws them (identify.code), and must have that same code; so must
  each tying step, for the part of the knot it shows;
- the mask check (masks.check) must find every crossing drawn the right way
  all over.

The references were worked out from how each knot is tied, and tests check
them against what is known about each knot (tests/test_bends.py): a square
knot closes to the square knot and not the granny, a bowline with its loop
cut is a sheet bend, each cord of a fisherman's knot is an overhand knot
with the other cord through it.

    from openstrand import bends
    made = bends.tie('square knot')
    for step in made['steps']:
        print(step['title'], step['caption'])
"""
import math
import re

import numpy as np

from . import colors as color_names
from . import draw, invariants
from .progress import picture as picture_of

CENTRE = (600.0, 400.0)
MIN_WIDTH, MAX_WIDTH = 14, 30       # a cord much wider than drawn would touch its neighbours


class BendError(ValueError):
    """A knot that cannot be made as asked; the message says what to change."""


# ------------------------------------------------------------------ layouts
# A cord is a list of (x, y, height) points, a few of them named: (x, y,
# height, 'name'). The names are where a tying step stops drawing the cord.
def _turned(points, centre=CENTRE):
    """The cord turned half round about the centre: the other cord of a knot
    that looks the same from both ends."""
    return [(2 * centre[0] - p[0], 2 * centre[1] - p[1]) + tuple(p[2:]) for p in points]


def _square(granny=False):
    """Two bights hooked through each other. Cord 1 comes from the left and
    turns back on the right; cord 2 is the same shape turned half round. Both
    legs of cord 1 lie over cord 2's turn, cord 1's turn lies over both legs
    of cord 2, and cord 2 goes over cord 1 where the legs cross in the middle.
    In a granny knot the upper three crossings are the other way round."""
    up = -1 if granny else 1
    one = [(120, 435, 0), (296, 435, 1), (500, 435, 0), (560, 448, -1), (600, 473, -1), (640, 497, -1),
           (700, 510, 0), (800, 510, 1), (878, 478, 1), (904, 435, 1), (910, 400, 1 if not granny else 0),
           (904, 365, up), (878, 322, up), (800, 290, up), (700, 290, 0), (640, 303, -up), (600, 327, -up),
           (560, 352, -up), (500, 365, 0), (296, 365, up), (120, 365, 0)]
    two = [(x, y, 0) for x, y, _ in _turned(one)]
    two[6] += ('through',)          # past the first two crossings: up through the bight, over the upper leg
    two[13] += ('round',)           # round behind both legs
    return [one, two]


def _sheet_bend():
    """Cord 1 is a bight: its standing part along the lower leg, its short
    end along the upper one. Cord 2 comes up through the bight from under its
    turn, goes over the upper leg, round behind both legs, back over the lower
    leg and under itself, its end lying over the upper leg: both short ends on
    the same side."""
    one = [(210, 460, 0), (340, 460, 0), (471, 460, 0), (619, 460, 0), (700, 460, 0), (742, 442, 0),
           (760, 400, 0), (742, 358, 0), (700, 340, 0), (648, 340, 0), (560, 340, 0), (471, 340, 0),
           (372, 340, 0)]
    two = [(990, 400, -1), (880, 400, -1), (760, 400, -1), (700, 400, 0.5), (640, 400, 2),
           (606, 393, 2, 'through'), (580, 372, 1.5), (562, 340, 1), (553, 316, 0.6), (530, 304, 0.3),
           (497, 318, -0.5), (463, 352, -1), (450, 400, -1), (463, 448, -1), (497, 482, -0.5),
           (545, 495, 0, 'round'), (592, 482, 0.5), (627, 448, 1), (640, 400, 1), (645, 360, 1), (650, 340, 1),
           (657, 296, 1), (664, 250, 1)]
    return [one, two]


def _bowline():
    """One cord. Its standing part comes down from the top and makes a small
    loop, the cord crossing over the standing part. The cord goes on round
    the big loop, comes up through the small loop from underneath, passes
    behind the standing part and goes back down through the small loop, its
    end lying inside the big loop."""
    return [[
        # the standing part, and the small loop round where the two legs will pass
        (600, 70, 1), (600, 150, 1), (600, 240, 1), (600, 300, -0.5), (600, 360, -2), (593, 394, -2),
        (572, 420, -1.5), (540, 438, -1), (518, 446, -0.6), (506, 468, -0.3), (518, 503, 0.5), (552, 537, 1),
        (600, 550, 1), (648, 537, 1), (682, 503, 0.5), (695, 455, 0), (682, 408, -0.5), (648, 373, -1),
        (600, 360, -1), (560, 353, -1), (540, 350, -1), (490, 350, -0.5), (446, 368, 0, 'loop'),
        # the big loop
        (412, 410, 0), (392, 480, 0), (392, 560, 0), (414, 640, 0), (462, 706, 0), (535, 742, 0),
        (610, 736, 0), (668, 694, 0), (688, 630, 0), (676, 572, 0),
        # up through the small loop, behind the standing part, down through the small loop
        (660, 529, 0), (660, 381, 0), (660, 335, 0, 'up'), (660, 300, 0), (642, 258, 0), (600, 240, 0),
        (558, 258, 0), (540, 300, 0, 'behind'), (540, 350, 0), (540, 438, 0), (540, 529, 0), (540, 640, 0)]]


def _star(turns, centre, radius, depth, drop, tail):
    """An overhand knot (turns = 3) or a double overhand knot (turns = 5) laid
    open as a star: the cord winds twice round the centre, over and under in
    turn, and its two ends leave the open point at the bottom, the standing
    part to the left and the short end to the right, both along the line drop
    below the centre. Points from where the standing part reaches that line."""
    cx, cy = centre
    half = math.pi / (2 * turns)                # the open point spans this much either side of straight down
    body = []
    for t in np.linspace(half, 2 * math.pi - half, 14 * turns):
        r = radius + depth * math.cos(turns * t)
        angle = 2 * t + math.pi / 2
        body.append((cx + r * math.cos(angle), cy + r * math.sin(angle), math.sin(turns * t)))
    level = cy + drop

    def run_out(at, before, way):
        """From the knot's first or last crossing straight on, then round to the line."""
        ux, uy = at[0] - before[0], at[1] - before[1]
        fall = level - at[1]
        slope = ux / max(uy, 1e-6)
        return [(at[0] + slope * 0.45 * fall, at[1] + 0.45 * fall, 0),
                (at[0] + way * 0.55 * fall, level - 0.08 * fall, 0), (at[0] + way * 1.1 * fall, level, 0)]
    lead = run_out(body[0], body[1], -1)[::-1]
    trail = run_out(body[-1], body[-2], 1)
    lead[0] += ('laid',)                        # the standing part, before the knot is tied
    # The cord has gone once round the centre when it meets its first crossing
    # again (the middle of the way); the step stops a little past that, or,
    # for a double overhand, past the second time round.
    stop = min(range(len(body)), key=lambda k: abs(k / (len(body) - 1) - (0.66 if turns == 3 else 0.82)))
    body[stop] += ('round',)
    return lead + body + trail + [(trail[-1][0] + tail, level, 0)]


def _fisherman(turns=3, radius=100, depth=55, drop=135, apart=420, off=-24, tail=70):
    """Two cords side by side, their ends pointing opposite ways. The end of
    each is tied in an overhand knot (turns = 3; a double overhand for 5)
    round the other cord: the other cord goes over the near side of the knot,
    through its middle and under its far side. off: how far below (above, if
    negative) the knot's centre the other cord passes, to keep clear of the
    knot's own crossings."""
    cy = (2 * CENTRE[1] - drop - off) / 2       # the right-hand knot's centre: the other is it turned half round
    cx = CENTRE[0] + apart / 2
    knot = _star(turns, (cx, cy), radius, depth, drop, tail)
    level = cy + drop
    there = 2 * CENTRE[0] - cx                  # the other knot's centre
    reach = radius + depth + 30
    # The standing part: from the far end, over the near side of the other
    # knot, down through its middle, under its far side.
    line = [(there - reach - 110, level, 0), (there - reach, level, 0), (there - reach + 40, level, 2),
            (there - 28, level, 2), (there + 28, level, -2), (there + reach - 40, level, -2),
            (there + reach, level, 0)]
    one = line + knot
    return [one, _turned(one)]


def _double_fisherman():
    return _fisherman(turns=5, radius=112, depth=50, drop=140, apart=470, off=22, tail=60)


def _macrame_square():
    """Two filler cords down the middle, a working cord each side. First
    half: the left cord goes across in front of the fillers and under the
    right cord; the right cord goes behind the fillers and comes up through
    the loop the left cord left. Second half: the same from the other side.
    The left cord lies in front of the fillers both times, the right cord
    behind them: a square knot of the two working cords, round the fillers."""
    left = [(470, 80, 1), (425, 140, 1, 'start'), (400, 200, 1), (420, 250, 1), (470, 270, 1), (565, 270, 1),
            (635, 270, 1), (720, 270, 1), (775, 285, 1), (800, 340, 1), (800, 385, 1, 'across'), (800, 430, 1),
            (775, 485, 1), (720, 500, 1), (635, 500, 1), (565, 500, 1), (505, 500, 1), (440, 512, 1),
            (402, 560, 1), (412, 630, 1), (470, 720, 1)]
    filler_1 = [(565, 80, 0), (565, 400, 0), (565, 720, 0)]
    filler_2 = [(635, 80, 0), (635, 400, 0), (635, 720, 0)]
    right = [(720, 80, 2), (720, 180, 2, 'start'), (720, 270, 2), (714, 316, 0, 'over'), (688, 338, -1),
             (635, 340, -1), (565, 340, -1), (512, 337, -1), (486, 312, 0), (480, 270, 0), (474, 222, 1),
             (445, 192, 2), (400, 187, 2), (356, 198, 2), (333, 240, 2), (328, 330, 2, 'half'), (332, 400, 2),
             (352, 436, 2), (410, 447, 2), (470, 450, 2), (500, 470, 2), (505, 500, 2), (512, 545, 0, 'over again'),
             (545, 568, -1), (565, 570, -1), (635, 570, -1), (690, 567, -1), (716, 545, 0), (720, 500, 0),
             (724, 452, 1), (758, 424, 2), (800, 420, 2), (846, 436, 2), (868, 490, 2), (866, 600, 2),
             (820, 680, 2), (790, 720, 2)]
    return [left, filler_1, filler_2, right]


# ------------------------------------------------------------------ library
# patterns: the reference. For each cord, in order from its first point, the
# crossings it passes: O where it goes over, U where it goes under. alone:
# what each cord is on its own, the others taken away (the Alexander
# polynomial of the cord, its ends joined). steps: what each tying picture
# shows (for every cord: None, not there yet; a name, drawn as far as that
# point; 'all'), which cord's end carries the arrow, and what to do.
UNKNOT, TREFOIL, CINQUEFOIL = (1,), (1, -1, 1), (1, -1, 1, -1, 1)
LIBRARY = {
    'square': dict(
        title='Square knot', also="reef knot", kind='bend', layout=_square, width=24,
        aliases=('reef knot', 'Hercules knot'),
        about='Joins two cords of the same thickness, or the two ends of one cord round a parcel or a '
              'bandage. Two half knots, the second the mirror image of the first: tied with the ends it is '
              '"right over left and under, then left over right and under". Lies flat; can slip in '
              'smooth or unequal cords.',
        cords=(('First cord', 'teal'), ('Second cord', 'gold')),
        patterns=('OUOOUO', 'UOUUOU'), alone=(UNKNOT, UNKNOT),
        steps=(((('all', None), None), 'Lay the first cord in a bight: a U-turn, both its ends to the left.'),
               ((('all', 'through'), 1), 'Bring the end of the second cord up through the bight: under the '
                                         'turn of the first cord, then over its upper leg.'),
               ((('all', 'round'), 1), 'Take it round behind both legs of the first cord.'),
               ((('all', 'all'), None), 'Bring it back over the lower leg and down through the bight, so it '
                                        'leaves beside its own standing part. Pull all four ends: each cord\'s '
                                        'two ends come out together, on the same side of the other\'s turn.'))),
    'granny': dict(
        title='Granny knot', kind='bend', layout=lambda: _square(granny=True), width=24,
        aliases=('false knot', "lubber's knot", 'booby knot'),
        about='What a square knot becomes when both half knots are tied the same way ("right over left" '
              'twice). It slips, then jams: shown so it can be told from a square knot, not to be used. '
              'The ends of each cord come out on opposite sides of the other\'s turn.',
        cords=(('First cord', 'teal'), ('Second cord', 'gold')),
        note='A granny knot is not a square knot: its two halves turn the same way, so it slips and jams.',
        patterns=('OUOUOU', 'OUOUOU'), alone=(UNKNOT, UNKNOT),
        steps=(((('all', None), None), 'Lay the first cord in a bight: a U-turn, both its ends to the left.'),
               ((('all', 'through'), 1), 'Bring the end of the second cord down through the bight: over the '
                                         'turn of the first cord, then under its upper leg.'),
               ((('all', 'round'), 1), 'Take it round the two legs: over the upper one, under the lower one.'),
               ((('all', 'all'), None), 'Bring it back over the lower leg and under the turn. The two ends of '
                                        'each cord now leave on opposite sides of the other\'s turn: that is '
                                        'the granny, and why it does not hold.'))),
    'sheet bend': dict(
        title='Sheet bend', also="weaver's knot", kind='bend', layout=_sheet_bend, width=22,
        aliases=("weaver's knot", 'becket bend', "weaver's bend", 'common bend', 'flag bend', 'simple bend',
                 'weaver knot'),
        about='Joins two cords, also of different thickness or stiffness: the thicker one makes the bight. '
              'It does not alternate: the working cord passes behind both legs of the bight, then under '
              'itself. Both short ends must lie on the same side. Same structure as a bowline.',
        cords=(('Bight', 'teal'), ('Working cord', 'gold')),
        patterns=('OUOUUO', 'UOOUUOUO'), alone=(UNKNOT, UNKNOT),
        steps=(((('all', None), None), 'Make a bight in the thicker cord: its short end is the upper leg.'),
               ((('all', 'through'), 1), 'Pass the end of the other cord up through the bight, from '
                                         'underneath.'),
               ((('all', 'round'), 1), 'Take it over the short end\'s leg and round behind both legs of the '
                                       'bight.'),
               ((('all', 'all'), None), 'Bring it back over the bight and tuck it under itself. Both short '
                                        'ends are on the same side; pull the two long parts.'))),
    'bowline': dict(
        title='Bowline', kind='loop', layout=_bowline, width=22,
        aliases=('bowline loop', 'king of knots'),
        about='A loop at the end of a cord that neither slips nor jams. "The rabbit comes up out of the '
              'hole, round behind the tree and back down the hole": the hole is a small loop in the standing '
              'part (the tree), the rabbit is the end. Same structure as a sheet bend.',
        cords=(('Bowline', 'teal'),),
        patterns=('OUUOOUOUUOUOOU',), alone=None,
        steps=(((('loop',), 0), 'Make a small loop in the cord, leaving enough for the big loop: the cord '
                                'crosses over its standing part.'),
               ((('up',), 0), 'Take the end round, the size of the loop you want, and bring it up through '
                              'the small loop from underneath.'),
               ((('behind',), 0), 'Pass it behind the standing part.'),
               ((('all',), None), 'And back down through the small loop, beside itself. Hold the end against '
                                  'the loop and pull the standing part.'))),
    'fisherman': dict(
        title="Fisherman's knot", also="magic knot", kind='bend', layout=_fisherman, width=22,
        # Not "fisherman's bend": that is the anchor hitch, another knot.
        aliases=('magic knot', 'English knot', "Englishman's knot", "angler's knot", "waterman's knot",
                 'halibut knot', 'angler knot', 'waterman knot'),
        about='Joins two cords or yarns: the end of each is tied in an overhand knot round the other cord, '
              'and the two knots slide together and lock. Knitters call it the magic knot.',
        cords=(('First cord', 'teal'), ('Second cord', 'gold')),
        patterns=('OOUUOOUUOUOOUU', 'OOUUOOUUOUOOUU'), alone=(TREFOIL, TREFOIL),
        steps=(((('laid', 'laid'), None), 'Lay the two cords side by side, their ends pointing opposite '
                                          'ways.'),
               ((('round', 'laid'), 0), 'Take the end of the first cord round the second cord and across '
                                        'itself: a loop round the second cord.'),
               ((('all', 'laid'), 0), 'Pass the end through that loop, beside the second cord: an overhand '
                                      'knot round it.'),
               ((('all', 'round'), 1), 'Now the second cord: its end round the first cord and across itself.'),
               ((('all', 'all'), None), 'And through its loop. Pull each end to snug its knot, then pull the '
                                        'two long parts: the knots slide together and lock.'))),
    'double fisherman': dict(
        title="Double fisherman's knot", also="grapevine knot", kind='bend', layout=_double_fisherman, width=20,
        aliases=('grapevine knot', 'grapevine bend', "double fisherman's bend", 'double English knot'),
        about='A fisherman\'s knot with each end wound twice: each cord is tied in a double overhand knot '
              'round the other. Bulkier and far more secure; climbers join ropes and close slings with it.',
        cords=(('First cord', 'teal'), ('Second cord', 'gold')),
        patterns=('OOUUOOUOUUOUOOUOUU', 'OOUUOOUOUUOUOOUOUU'), alone=(CINQUEFOIL, CINQUEFOIL),
        steps=(((('laid', 'laid'), None), 'Lay the two cords side by side, their ends pointing opposite '
                                          'ways.'),
               ((('round', 'laid'), 0), 'Wind the end of the first cord twice round the second cord, the '
                                        'second turn crossing over the first.'),
               ((('all', 'laid'), 0), 'Pass the end back through both turns, beside the second cord: a '
                                      'double overhand knot round it.'),
               ((('all', 'round'), 1), 'Now the second cord: its end twice round the first cord, crossing '
                                       'over itself.'),
               ((('all', 'all'), None), 'And back through both turns. Pull each end to snug its knot, then '
                                        'pull the two long parts: the knots slide together and lock.'))),
    'macrame square': dict(
        title='Macrame square knot', kind='macrame', layout=_macrame_square, width=22,
        aliases=('cobra knot', 'Solomon bar', 'Portuguese sinnet', 'macrame flat knot', 'cobra stitch',
                 'square knot macrame', 'macrame knot'),
        about='The basic macrame knot: two working cords tied round two filler cords, in two halves, the '
              'second the mirror image of the first. Rows of it make the flat bands of bracelets and plant '
              'hangers; the same half tied again and again twists into a spiral instead.',
        cords=(('Left working cord', 'teal'), ('Filler cords', 'gold'), ('Filler cords', 'gold'),
               ('Right working cord', 'rose')),
        patterns=('UOOOUUOOOU', 'UOUO', 'UOUO', 'OUUUOOUUUO'), alone=(UNKNOT, UNKNOT, UNKNOT, UNKNOT),
        steps=(((('start', 'all', 'all', 'start'), None), 'Four cords side by side: two filler cords in the '
                                                          'middle, a working cord on each side.'),
               ((('across', 'all', 'all', 'over'), 0), 'First half. Take the left cord across in front of '
                                                       'the two fillers and under the right cord.'),
               ((('across', 'all', 'all', 'half'), 3), 'Take the right cord behind the fillers and up '
                                                       'through the loop on the left. That is a half knot.'),
               ((('all', 'all', 'all', 'over again'), 0), 'Second half, the other way. Take the cord now on '
                                                          'the right across in front of the fillers and '
                                                          'under the cord on the left.'),
               ((('all', 'all', 'all', 'all'), None), 'Take the left cord behind the fillers and up through '
                                                      'the loop on the right. Pull both working cords: the '
                                                      'square knot is done.'))),
}
KINDS = {'bend': 'joins two cords', 'loop': 'a loop in one cord', 'macrame': 'tied round two filler cords',
         'hitch': 'tied round a holding cord', 'decorative': 'a decorative knot',
         'braid': 'cords plaited together', 'sennit': 'the same knot tied again and again'}

# More knots, of the same shape as LIBRARY's: the craft library's recipes
# (openstrand/recipes.py, read from craft_library/) and any recipe put in
# EXTRA to be tried before it is one of them. tie, find and recognise know
# them; library() and the tests of LIBRARY list only the knots written here.
EXTRA = {}


def more():
    """{key: recipe} of the knots that are not in LIBRARY."""
    from . import recipes
    return {**recipes.library(), **EXTRA}


def recipe_of(key):
    return LIBRARY[key] if key in LIBRARY else more()[key]


# Words a request for a knot is wrapped in: "how do I tie a bowline", "square
# knot tutorial". Not "bend": a fisherman's bend is not a fisherman's knot.
_ASIDE = ('a', 'an', 'the', 'knot', 'knots', 'tutorial', 'how', 'to', 'tie', 'tying', 'do', 'i', 'you', 'me',
          'show', 'make', 'please', 'steps', 'for')


def _plain(name):
    """A name as it is looked up: small letters, no punctuation, apostrophes
    and the words every request for a knot has left out."""
    key = str(name or '').lower().replace("'", '').replace('’', '')
    key = re.sub(r'[^a-z0-9]+', ' ', key).strip()
    key = re.sub(r'\bmacram[eé]?\b', 'macrame', key)
    words = [w for w in key.split() if w not in _ASIDE]
    return ' '.join(words) or key


def find(name):
    """The library key for a knot name or one of its other names, or None."""
    key = _plain(name)
    if not key:
        return None
    every = {**LIBRARY, **more()}
    names = {k: {_plain(n) for n in (k, recipe['title']) + tuple(recipe['aliases'])} for k, recipe in every.items()}
    for k, known in names.items():
        if key in known:
            return k
    # Written as one word, or as two: "sheetbend", "squareknot", "bow line".
    squeezed = re.sub(r'[^a-z0-9]', '', str(name or '').lower())
    for k, known in names.items():
        full = (k, every[k]['title']) + tuple(every[k]['aliases'])
        if {key.replace(' ', ''), squeezed} & ({n.replace(' ', '') for n in known}
                                              | {re.sub(r'[^a-z0-9]', '', n.lower()) for n in full}):
            return k
    return None


def library():
    """[(key, title, kind in words, cords, crossings, other names, about)] for every knot."""
    out = []
    for key, recipe in LIBRARY.items():
        crossings = sum(len(p) for p in recipe['patterns']) // 2
        out.append((key, recipe['title'], KINDS[recipe['kind']], len(recipe['cords']), crossings,
                    recipe['aliases'][:4], recipe['about']))
    return out


def full_title(key):
    """'Square knot (reef knot)': the title with the other name people know it by."""
    recipe = recipe_of(key)
    return recipe['title'] + (f" ({recipe['also']})" if recipe.get('also') else '')


# ----------------------------------------------------------------- drawings
def centrelines(key, shown=None):
    """Each cord of the knot as a polyline of (x, y, height), sampled as the
    drawing is built (draw.centerline); with shown, each cord only as far as
    the point named there (None: not at all, 'all': the whole cord). A cord
    not shown is None."""
    out = []
    for k, points in enumerate(recipe_of(key)['layout']()):
        stop = 'all' if shown is None else shown[k]
        if stop is None:
            out.append(None)
            continue
        poly, _, heights = draw.centerline({'points': [list(p[:2]) for p in points],
                                            'heights': [p[2] for p in points]}, k, with_heights=True)
        line = np.c_[np.asarray(poly, dtype=float), heights]
        if stop != 'all':
            named = [n for n, p in enumerate(points) if len(p) > 3 and p[3] == stop]
            if not named:
                raise BendError(f'{key}: cord {k + 1} has no point named "{stop}"')
            line = line[:_sample_of(points, poly, named[0]) + 1]
        out.append(line)
    return out


def _sample_of(points, poly, index):
    """Which sample of the polyline is the cord's point number index: the
    curve passes through its points in order, so each is looked for a little
    way on from the one before."""
    start = 0
    for n, p in enumerate(points[:index + 1]):
        reach = 12 if n == 0 else int(1.6 * math.dist(points[n - 1][:2], p[:2]) / draw.SPACING) + 12
        stop = min(len(poly), start + reach)
        start = min(range(start, max(stop, start + 1)),
                    key=lambda i: (poly[i][0] - p[0]) ** 2 + (poly[i][1] - p[1]) ** 2)
    return start


def code_of(lines):
    """The crossing code of cords given as (x, y, height) polylines, a cord
    that is not there (None) left out."""
    return invariants.code_of([line for line in lines if line is not None])


def reference(key):
    """The knot's crossing code, from its drawing. The drawing must pass the
    crossings the library writes down for it, letter for letter: a drawing
    that has drifted from its reference is an error, never a knot."""
    recipe = recipe_of(key)
    found = code_of(centrelines(key))
    drawn = tuple(invariants.pattern(found, k) for k in range(len(found['passes'])))
    if drawn != tuple(recipe['patterns']):
        raise BendError(f"the drawing of the {recipe['title']} passes its crossings as {drawn}, "
                        f"not as its reference {tuple(recipe['patterns'])}")
    return found


def design(key, shown=None, colors=None, width=None):
    """The knot (or the part of it a step shows) as a design for draw.build:
    every cord with its points and heights, its colour and its name. colors:
    one per cord with its own name (the two fillers share theirs)."""
    recipe = recipe_of(key)
    return _design(key, shown, _colors(recipe, colors), float(width or recipe['width']))


def _design(key, shown, picked, width):
    recipe = recipe_of(key)
    cords = []
    for (label, _), color, line in zip(recipe['cords'], picked, centrelines(key, shown)):
        if line is None:
            continue
        step = max(1, int(math.ceil(len(line) / 380)))
        kept = line[::step]
        if not np.allclose(kept[-1], line[-1]):
            kept = np.vstack([kept, line[-1]])
        cords.append({'points': np.round(kept[:, :2], 2).tolist(), 'heights': np.round(kept[:, 2], 3).tolist(),
                      'width': width, 'color': color, 'label': label})
    return {'name': recipe['title'], 'cords': cords}


def _colors(recipe, colors):
    """One colour per cord: the knot's own, or the ones asked for, in order
    (cords that share a name, such as the two fillers, share a colour)."""
    roles = []
    for label, _ in recipe['cords']:
        if label not in roles:
            roles.append(label)
    own = {label: color for label, color in recipe['cords']}
    given = [colors] if isinstance(colors, str) else list(colors or [])
    if len(given) > len(roles):
        raise BendError(f"the {recipe['title']} has {len(roles)} colour{'s' if len(roles) != 1 else ''} to "
                        f"choose ({', '.join(r.lower() for r in roles)}); {len(given)} were given")
    for role, color in zip(roles, given):
        if color:
            own[role] = color
    return [color_names.parse(str(own[label])) for label, _ in recipe['cords']]


# ------------------------------------------------------------------ checking
def check(data, expected):
    """Whether a built design is the drawing it was built from: its crossing
    code, read back from its strands, masks and layers the way the app draws
    them, against the expected one. Returns (ok, what is wrong or '')."""
    from . import identify
    found = invariants.compare(identify.code(data), expected)
    if found is None:
        return False, 'its cords do not pass the same crossings in the same order'
    if found['flipped'] or found['mirror']:
        where = ', '.join(f'({x:.0f}, {y:.0f})' for x, y in
                          (identify.code(data)['points'][k] for k in found['flipped'][:6]))
        return False, (f"{len(found['flipped'])} crossing{'s' if len(found['flipped']) != 1 else ''} drawn the "
                       f"other way round ({where})" if found['flipped'] else 'it is drawn as the mirror image')
    return True, ''


def tie(name, colors=None, width=None, build=True, progress=None):
    """The steps to tie a library knot, each a full OpenStrand design, the
    last one the finished knot.

    Returns dict(key, title, kind, about, cords, crossings, patterns, steps,
    checks, ok): steps [dict(title, caption, data, report, masks)] (data None
    when build is False); checks [dict(stage, ok, note)]: the drawing against
    its reference, then every built step read back from its strands and its
    masks checked; ok when all of them hold. progress (openstrand.progress)
    hears how far it has got, with a picture of each step as it is drawn."""
    key = find(name)
    if key is None:
        names = ', '.join(r['title'] for r in LIBRARY.values())
        raise BendError(f'"{name}" is not one of the ready-made knots ({names})')
    recipe = recipe_of(key)
    width = float(width or recipe['width'])
    if not MIN_WIDTH <= width <= MAX_WIDTH:
        raise BendError(f'width must be between {MIN_WIDTH} and {MAX_WIDTH} px for this drawing: a wider cord '
                        'would touch its neighbours')
    picked = _colors(recipe, colors)
    whole = reference(key)
    checks = [dict(stage='the drawing against its reference', ok=True,
                   note='; '.join(f'cord {k + 1} passes {p}' for k, p in enumerate(recipe['patterns'])))]
    alone = recipe.get('alone')
    if alone:
        lines = centrelines(key)
        for k, expected in enumerate(alone):
            found = invariants.alexander(lines[k])
            if tuple(found) != tuple(expected):
                checks.append(dict(stage=f'cord {k + 1} on its own', ok=False,
                                   note=f'Alexander polynomial {found}, not {expected}'))
    steps = []
    tell = progress or (lambda *a, **k: None)
    plan = recipe['steps']
    lengths = []
    for (shown, _), _ in plan:
        lines = centrelines(key, shown)
        lengths.append(sum(float(np.hypot(*np.diff(line[:, :2], axis=0).T).sum()) for line in lines
                           if line is not None))
    starts = np.concatenate([[0.0], np.cumsum(lengths)])[:-1] / max(sum(lengths), 1e-9)
    for n, (((shown, arrow), caption)) in enumerate(plan, start=1):
        lines = centrelines(key, shown)
        there = [line for line in lines if line is not None]
        hues = [color for color, line in zip(picked, lines) if line is not None]
        entry = dict(title=f'Step {n}', caption=caption, data=None, report='', masks=None)
        if build:
            tell(float(starts[n - 1]), 'draw_step', lambda: picture_of(there, width, hues), step=n, steps=len(plan))
            data, report = draw.build(_design(key, shown, picked, width), mask_check=False)
            expected = code_of(lines) if n < len(plan) else whole
            ok, note = check(data, expected)
            fixed, left = [], []
            from . import masks
            problems = masks.check(data)['problems']
            if problems:
                # A mask that paints beside its crossing: fix what is safe, and
                # keep the fix only if the knot is still the knot.
                repaired, fixed, left = masks.repair(data, create_masks=True)
                if check(repaired, expected)[0]:
                    data, ok, note = repaired, True, ''
                else:
                    fixed, left = [], problems
            if arrow is not None and lines[arrow] is not None and n < len(plan):
                from .tying import _arrow
                _arrow(data, tuple(lines[arrow][-1, :2]))
            entry.update(data=data, report=report, masks=dict(fixed=fixed, left=left))
            checks.append(dict(stage=f'step {n} as drawn in the app', ok=ok and not left,
                               note=note or ('; '.join(p['text'] for p in left) if left else
                                             f"{len(expected['hand'])} crossing"
                                             f"{'s' if len(expected['hand']) != 1 else ''}, each as in the "
                                             'reference')))
        steps.append(entry)
    tell(1.0)
    return dict(key=key, title=full_title(key), kind=recipe['kind'], about=recipe['about'],
                cords=[label for label, _ in recipe['cords']], crossings=len(whole['hand']),
                patterns=list(recipe['patterns']), steps=steps, checks=checks,
                ok=all(c['ok'] for c in checks))


def checked(made):
    """What tie() checked, in a sentence or two, for a person or the agent."""
    first, rest = made['checks'][0], made['checks'][1:]
    text = f"the drawing passes its crossings as the reference says ({first['note']})"
    wrong = [c for c in rest if not c['ok']]
    steps = [c for c in rest if c['stage'].startswith('step')]
    if steps and not wrong:
        text += (f"; steps 1 to {len(steps)}, read back from their strands, masks and layers as the app draws "
                 'them: every crossing as in the reference, every mask right')
    for c in wrong:
        text += f"; {c['stage']}: NOT AS THE REFERENCE ({c['note']})"
    return text + '.'


# --------------------------------------------------------------- recognising
_REFERENCES = {}
_MORE_REFERENCES = {}


def references():
    """{key: crossing code} of every library knot, worked out once."""
    if not _REFERENCES:
        for key in LIBRARY:
            _REFERENCES[key] = reference(key)
    found = dict(_REFERENCES)
    for key in more():
        if key not in _MORE_REFERENCES:
            _MORE_REFERENCES[key] = reference(key)
        found[key] = _MORE_REFERENCES[key]
    return found


def recognise(code, alone=None, closed=None):
    """Which library knot a drawing with this crossing code is.

    None when it is laid like none of them, else dict(key, title, how,
    flipped, mirror, cords, note). how is 'exact' when every crossing goes
    the way the library's drawing has it (a mirror image has the same name);
    'structure' for a fisherman's knot laid some other way (why says what
    makes it one: alone gives each cord's own knot, its Alexander
    polynomial); 'near' when the drawing has a library knot's layout but some
    of its crossings (flipped: their numbers in the code) go the other way
    round."""
    best = None
    order = list(references())
    for key, ref in references().items():
        found = invariants.compare(code, ref)
        if found is None:
            continue
        rank = (len(found['flipped']), order.index(key))
        if best is None or rank < best[0]:
            best = (rank, dict(key=key, title=full_title(key), how='near' if found['flipped'] else 'exact',
                               flipped=found['flipped'], mirror=found['mirror'], cords=found['cords'],
                               note=recipe_of(key).get('note', '')))
    if best and best[1]['how'] == 'exact':
        return best[1]
    tied = _tied_round_each_other(code, alone, closed)
    return tied or (best[1] if best else None)


def _tied_round_each_other(code, alone, closed):
    """A fisherman's knot (or a double one), however it is laid: two open
    cords, each an overhand knot (a double overhand knot) on its own, each
    passing through a loop of the other."""
    if alone is None or len(alone) != 2 or len(code['passes']) != 2 or any(closed or ()):
        return None
    for knot, key, what in ((TREFOIL, 'fisherman', 'an overhand knot'),
                            (CINQUEFOIL, 'double fisherman', 'a double overhand knot')):
        if all(tuple(a) == knot for a in alone) and all(
                any(abs(v) >= 1 for v in invariants.through(code, loop, other).values())
                for loop, other in ((0, 1), (1, 0))):
            return dict(key=key, title=full_title(key), how='structure', flipped=[], mirror=False,
                        cords=[0, 1], note='',
                        why=f'each cord is tied in {what} with the other cord through it')
    return None

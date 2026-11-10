"""The assistant's working animation, drawn live: the OpenStrand logo, a box stitch, tied
from a plus and then continued level after level, each level k = 1 or k = 0.

The steps, in the logo's colours (set 1 blue, set 2 orange), starting right-handed like
the logo (the same geometry scripts/build_box_stitch_spinner.py renders with the canvas):

1. A plus: 1_1 across, 2_1 up.
2. It turns to an x, the way 1_1 and 2_1 lie in the 1x1 starting stitch.
3. The attached strands grow from both ends of both: the starting stitch, the logo.
4. It stretches into the stretched 1x1 starting stitch, keeping its centre.
5. Levels, for as long as the assistant works. In every level the four newest strands
   shorten and four new ones grow from their ends:
   - k = 1: each new strand leaves its parent's end turned 126.87 degrees (2 atan 2), the one
     angle at which the level is an exact copy of the one under it. The stitch spirals:
     one way right-handed, the other way left-handed.
   - k = 0: each new strand folds straight back over its own parent. The stitch does not
     turn and its hand switches, so the next k = 1 level spirals the other way.

Which k a level gets is drawn by lot (K0_SHARE, never more than SAME_RUN alike in a row),
unless one was asked for (flip_next). Now and then, and when asked (start_over), the stitch
is let go and tied again from the plus.

Stitch is the geometry and its time, with no Qt in it; paint_stitch draws it with QPainter.
Lengths are the project's own units, about the stitch's centre; time is the animation's own
milliseconds (45 ms a frame at speed 1, as the rendered frames had).
"""
import math
import random

WIDTH, STROKE = 46, 4            # a strand and its outline
ARM, SHORT = 168.0, 112.0        # a strand's length while it is the newest, and once covered
TURN = 2 * math.atan(2)          # k = 1: 126.87 degrees a level
VIEW = 153.0                     # half the side of the square the picture shows
FRAME_MS = 45
TURN_MS, ATTACH_MS, STRETCH_MS = 11 * FRAME_MS, 34 * FRAME_MS, 11 * FRAME_MS
INTRO_MS = TURN_MS + ATTACH_MS + STRETCH_MS
LEVEL_MS = 52 * FRAME_MS
LEAVE_MS = 9 * FRAME_MS          # letting go before it starts again: it shrinks away
KEEP = 12                        # levels drawn: the ones under them are covered
K0_SHARE = 0.4                   # how often a level is k = 0
SAME_RUN = 3                     # never more levels alike in a row
AGAIN = (9, 14)                  # levels before it starts again from the plus (drawn by lot)

# The 1x1 starting stitch and its stretched form: name -> (start, end). Mains first, then
# the four arms in order round the centre.
START = {'2_1': ((-42, 98), (42, -98)), '1_1': ((-98, -42), (98, 42)),
         '2_2': ((42, -98), (42, 70)), '1_2': ((98, 42), (-70, 42)),
         '2_3': ((-42, 98), (-42, -70)), '1_3': ((-98, -42), (70, -42))}
STRETCHED = {'2_1': ((-28, 56), (28, -56)), '1_1': ((-56, -28), (56, 28)),
             '2_2': ((28, -56), (28, 112)), '1_2': ((56, 28), (-112, 28)),
             '2_3': ((-28, 56), (-28, -112)), '1_3': ((-56, -28), (112, -28))}
MAINS, ARMS = ('2_1', '1_1'), ('2_2', '1_2', '2_3', '1_3')


class Strand:
    """One straight strand: where it starts, its direction (radians), length and set (1 or 2)."""
    __slots__ = ('x', 'y', 'dir', 'len', 'set')

    def __init__(self, x, y, direction, length, set_number):
        self.x, self.y, self.dir, self.len, self.set = x, y, direction, length, set_number

    @classmethod
    def between(cls, name, a, b):
        return cls(a[0], a[1], math.atan2(b[1] - a[1], b[0] - a[0]), math.dist(a, b), int(name[0]))

    def end(self):
        return self.x + math.cos(self.dir) * self.len, self.y + math.sin(self.dir) * self.len


class Level:
    """Four strands round the centre, in order. hand: 1 right, -1 left. k: how it was made
    (None for the starting stitch's arms)."""
    __slots__ = ('strands', 'hand', 'k')

    def __init__(self, strands, hand, k):
        self.strands, self.hand, self.k = strands, hand, k


def _lerp(a, b, t):
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


class Stitch:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.queue = []      # the k of the levels to come, when asked for
        self.restart()

    def restart(self):
        """From scratch: the plus."""
        self.at = 0.0            # ms into the plus, the x, the attaching and the stretch
        self.mains = []          # 2_1 and 1_1
        self.levels = []         # oldest first; the last one is the newest
        self.next = None         # the level being tied
        self.t = 0.0             # how far it has got, 0 to 1
        self.history = []        # the k of the levels tied since the plus
        self.leaving = None      # ms left of letting go, before it starts again
        self.again = self.rng.randint(*AGAIN)
        self.rev = getattr(self, 'rev', 0) + 1  # goes up whenever the levels under the newest change
        self._intro()

    # ------------------------------------------------------------------ what is asked of it
    def flip_next(self):
        """The next level is k = 0: the hand switches. Once: asked again before then, it stays one."""
        if not self.queue:
            self.queue.append(0)

    def start_over(self):
        """Let go and tie again from the plus. Not while it is still being tied from the plus,
        nor right after: there would be nothing to let go of."""
        if self.leaving is None and self.at >= INTRO_MS and len(self.history) >= 2:
            self.leaving = float(LEAVE_MS)

    def hand(self):
        return (self.next or self.levels[-1]).hand if self.levels else 1

    def fade(self):
        """1 while it is there, down to 0 as it is let go."""
        return 1.0 if self.leaving is None else max(0.0, self.leaving / LEAVE_MS)

    # ------------------------------------------------------------------ time
    def advance(self, ms):
        """ms of the animation's own time go by."""
        while ms > 0:
            if self.leaving is not None:
                step = min(ms, self.leaving)
                self.leaving -= step
                ms -= step
                if self.leaving <= 1e-9:
                    queue = self.queue
                    self.restart()
                    self.queue = queue
                continue
            if self.at < INTRO_MS:
                step = min(ms, INTRO_MS - self.at)
                self.at += step
                ms -= step
                self._intro()
                if self.at >= INTRO_MS:
                    self.rev += 1
                continue
            if self.next is None:
                self._begin(self.choose())
            step = min(ms, (1 - self.t) * LEVEL_MS)
            self.t += step / LEVEL_MS
            ms -= step
            self._place()
            if self.t < 1 - 1e-9:
                break
            self.history.append(self.next.k)
            self.levels.append(self.next)
            self.next, self.t = None, 0.0
            self.rev += 1
            if len(self.levels) > KEEP:
                del self.levels[0]
                self.mains = []
            if len(self.history) >= self.again:
                self.leaving = float(LEAVE_MS)

    def choose(self):
        """The next level's k: the one asked for, else by lot, never more than SAME_RUN alike."""
        if self.queue:
            return self.queue.pop(0)
        last = self.history[-SAME_RUN:]
        if len(last) == SAME_RUN and len(set(last)) == 1:
            return 1 - last[0]
        return 0 if self.rng.random() < K0_SHARE else 1

    # ------------------------------------------------------------------ geometry
    def _intro(self):
        """The plus, the turn to an x, the attached strands, the stretch: where it is at self.at."""
        t = self.at
        if t < TURN_MS:
            f = t / TURN_MS
            geom = {}
            for name, rest in (('2_1', -math.pi / 2), ('1_1', 0.0)):
                a, b = START[name]
                half, to = math.dist(a, b) / 2, math.atan2(b[1] - a[1], b[0] - a[0])
                angle = rest + (to - rest) * f
                u = (math.cos(angle) * half, math.sin(angle) * half)
                geom[name] = ((-u[0], -u[1]), u)
        elif t < TURN_MS + ATTACH_MS:
            f = (t - TURN_MS) / ATTACH_MS
            geom = {name: START[name] for name in MAINS}
            # set 2 starts before set 1 ends: one motion
            for names, (a, b) in ((('1_2', '1_3'), (0.0, 0.62)), (('2_2', '2_3'), (0.38, 1.0))):
                u = min(max((f - a) / (b - a), 0.0), 1.0)
                for name in names:
                    geom[name] = (START[name][0], _lerp(*START[name], u))
        else:
            f = min(1.0, (t - TURN_MS - ATTACH_MS) / STRETCH_MS)
            geom = {name: (_lerp(START[name][0], STRETCHED[name][0], f), _lerp(START[name][1], STRETCHED[name][1], f))
                    for name in START}
        self.mains = [Strand.between(name, *geom[name]) for name in MAINS]
        arms = [Strand.between(name, *geom.get(name, (START[name][0], START[name][0]))) for name in ARMS]
        for arm, name in zip(arms, ARMS):
            if arm.len < 1e-6:  # not grown yet: it will leave its start this way
                arm.dir = math.atan2(START[name][1][1] - START[name][0][1], START[name][1][0] - START[name][0][0])
        self.levels = [Level(arms, 1, None)]

    def _begin(self, k):
        top = self.levels[-1]
        # k = 1: turned by TURN, the way of the hand. k = 0: straight back, and the hand switches.
        strands = [Strand(0.0, 0.0, s.dir + (top.hand * TURN if k == 1 else math.pi), 0.0, s.set)
                   for s in top.strands]
        self.next, self.t = Level(strands, -top.hand if k == 0 else top.hand, k), 0.0
        self._place()

    def _place(self):
        """The newest strands shorten and the new ones grow from their ends."""
        for parent, child in zip(self.levels[-1].strands, self.next.strands):
            parent.len = ARM + (SHORT - ARM) * self.t
            child.x, child.y = parent.end()
            child.len = ARM * self.t


# ---------------------------------------------------------------------- drawing
def strand_path(strand, half, length, grow=0.0):
    """The strand's body out to length and the joint's disc at its start, as one outline: the
    half behind the start and, while the strand is still shorter than the disc, the part of
    the disc ahead of its end (so a strand that has just begun is a round joint, with no
    notch between it and the end it grows from)."""
    from PyQt5.QtCore import QPointF
    from PyQt5.QtGui import QPainterPath, QPolygonF
    c, s = math.cos(strand.dir), math.sin(strand.dir)
    ox, oy = -s * half, c * half
    length = max(0.0, length + grow)
    bx, by = strand.x + c * length, strand.y + s * length

    def arc(a, b, steps):
        return [QPointF(strand.x + math.cos(strand.dir + a + (b - a) * i / steps) * half,
                        strand.y + math.sin(strand.dir + a + (b - a) * i / steps) * half) for i in range(steps + 1)]

    points = [QPointF(strand.x - ox, strand.y - oy), QPointF(bx - ox, by - oy)]
    if length < half:  # the disc reaches past the end
        reach = math.acos(length / half)
        points += arc(-reach, reach, 8)
    points.append(QPointF(bx + ox, by + oy))
    points += arc(math.pi / 2, 3 * math.pi / 2, 20)  # round behind the start, from one side to the other
    path = QPainterPath()
    path.addPolygon(QPolygonF(points))
    path.closeSubpath()
    return path


def flat_path(strand, half, inset=0.0):
    """A main strand: square at both ends."""
    from PyQt5.QtCore import QPointF
    from PyQt5.QtGui import QPainterPath, QPolygonF
    c, s = math.cos(strand.dir), math.sin(strand.dir)
    ox, oy = -s * half, c * half
    ax, ay = strand.x + c * inset, strand.y + s * inset
    bx, by = strand.x + c * (strand.len - inset), strand.y + s * (strand.len - inset)
    path = QPainterPath()
    path.addPolygon(QPolygonF([QPointF(ax - ox, ay - oy), QPointF(bx - ox, by - oy),
                               QPointF(bx + ox, by + oy), QPointF(ax + ox, ay + oy)]))
    path.closeSubpath()
    return path


LAP = 0.75  # the colour laps this far under the outline, so no ground shows between the two


def _fill(painter, outer, hole, inner, colour):
    """The outline as a ring round the colour (outer less hole), not black under it: painted
    again inside a clip (the over and under of a level), black under the whole colour would
    leave a hairline along the clip's edge."""
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QPainterPath
    ring = QPainterPath()  # odd-even
    ring.addPath(outer)
    ring.addPath(hole)
    painter.fillPath(ring, Qt.black)
    painter.fillPath(inner, colour)


def paint_strand(painter, strand, colours, joined):
    """joined: another strand starts at its end, so it has no end line there."""
    if strand.len < 0.5:
        return
    to = strand.len - (0 if joined else STROKE)
    _fill(painter, strand_path(strand, WIDTH / 2 + STROKE, strand.len),
          strand_path(strand, WIDTH / 2 - LAP, to - LAP), strand_path(strand, WIDTH / 2, to), colours[strand.set])


def paint_level(painter, level, colours, joined):
    """Right hand: each strand goes over the one before it round the centre. Left hand: the
    other way. So the first one drawn goes over the last: it is painted again inside the last
    one's shape (a little wider, so the clip's edge falls on its own colour)."""
    from PyQt5.QtCore import Qt
    strands = level.strands if level.hand > 0 else level.strands[::-1]
    for strand in strands:
        paint_strand(painter, strand, colours, joined)
    over, under = strands[0], strands[-1]
    if under.len < 0.5 or over.len < 0.5:
        return
    painter.save()
    painter.setClipPath(strand_path(under, WIDTH / 2 + STROKE + 1.5, under.len, grow=1.5), Qt.IntersectClip)
    paint_strand(painter, over, colours, joined)
    painter.restore()


def paint_stitch(painter, stitch, box, colours, part='all'):
    """The stitch as it is now, in the square box (a QRectF). colours: set number -> QColor.

    part: 'under' is what stays as it is until stitch.rev changes (the levels under the newest,
    and the mains once the stretch is done), 'top' is what moves (the newest level, the one being
    tied, and everything while the stitch is still tied from the plus), 'all' is both. A widget
    keeps 'under' as a picture and paints only 'top' each frame."""
    from PyQt5.QtGui import QPainter
    fade = stitch.fade()
    if fade <= 0.0:
        return
    tying = stitch.at < INTRO_MS  # from the plus to the stretch everything moves
    under, top = part in ('all', 'under'), part in ('all', 'top')
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.translate(box.center())
    scale = box.width() / (2 * VIEW) * (0.35 + 0.65 * fade)
    painter.scale(scale, scale)
    painter.setOpacity(painter.opacity() * fade)
    for main in (stitch.mains if (top if tying else under) else ()):  # square ends, till its arms are attached
        attached = any(s.set == main.set and s.len >= 0.5 for s in stitch.levels[0].strands)
        inset = 0 if attached else STROKE
        _fill(painter, flat_path(main, WIDTH / 2 + STROKE), flat_path(main, WIDTH / 2 - LAP, inset + LAP),
              flat_path(main, WIDTH / 2, inset), colours[main.set])
    last = len(stitch.levels) - 1
    for i, level in enumerate(stitch.levels):
        if top if i == last else under:
            paint_level(painter, level, colours, joined=i < last or stitch.next is not None)
    if stitch.next is not None and top:
        paint_level(painter, stitch.next, colours, joined=False)
    painter.restore()

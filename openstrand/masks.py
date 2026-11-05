"""Masks: what each one paints, what is wrong with it, and edits that fix it.

A mask (MaskedStrand) lifts its first strand over its second where the two
cross: it paints a piece of the first strand, its colour and outline, over
everything drawn before it. In a tight knot the parts of the cord touch, the
fitter's joints sit inside crossings, and a crossing's two strands are not the
only ones there, so a mask's piece can also land on a strand that should show
(the old "crowded crossing" warning), and one crossing can be drawn half one
way and half the other.

check() finds those places from the app's own drawing, not by guessing:

1. The design is loaded with the app's loader (load_strands_from_data) and
   the app's paths: what each strand paints (shader_utils._drawn_footprint)
   and what each mask paints (shader_utils._mask_footprint, clipped by
   _piece_keep exactly as MaskedStrand.draw clips it).
2. These are painted in the app's order (masks above the strands) into a
   paint map: for every pixel (SCALE per canvas unit), which strand or mask
   the person sees there. Around each mask it is painted again without that
   mask, to know what would show there without it.
3. Every crossing of the cords' centre lines says which part goes over: from
   the design when draw.build stored it (project key "design_crossings"),
   else as identify reads it: the crossing's own mask, else what most of the
   crossing shows. Near a crossing,
   within its reach along each cord, every pixel both parts cover must show
   the part on top.
4. Problems are the places, in canvas coordinates, where the paint map
   disagrees:
   - covers_strand: a mask's piece hides a strand that shows without it, and
     no crossing puts the mask's strand over that one there;
   - wrong_way: part of a crossing shows the part that should be under (a
     joint inside the crossing, a mask that does not reach, a mask lifting
     the wrong strand there);
   - two_crossings: the mask's two strands cross more than once, its piece
     covers both crossings, and one of them should be the other way round;
   - wrong_crossing: the crossing is drawn the other way round from the
     design at its very centre (as draw.wrong_crossings, read from the file).
   Each comes with the edit that fixes it.

Everything is worked out in small windows of the map (a strand's box, a
crossing's neighbourhood, a mask's piece), so a large mat or stitch is
checked as quickly as a knot.

edit() applies one edit with the app's own code on the loaded strands (erase
boxes stored by their corners as Edit Mask stores them, Reset Mask,
MaskedStrand for a new mask); repair() does the safe ones until nothing is
left to fix. An erase box is shaped by the tool: short quads along a strand,
so the piece ends on that strand's outline (see best_erase).

    from openstrand import masks
    report = masks.check(data)
    data, done, left = masks.repair(data)
"""
import copy
import math

import numpy as np

from . import identify, invariants

SCALE = 2.0             # paint-map pixels per canvas unit
MAX_PIXELS = 6_000_000  # the map is coarser for very large designs
MIN_AREA = 4.0          # canvas px²: smaller differences are antialiasing and rounding
MIN_THICK = 4.0         # canvas px: a thinner strip is where two strands of one cord barely differ
SAMPLE = 2.0            # canvas px between centre-line samples
CROSSING_STEP = 2       # crossings are found on every second sample (4 px)
ROUNDS = 8              # repair passes
CLEAN = 1.5             # canvas px²: the most an automatic erase may take of the piece that should stay
SHADOW_REACH = 6.0      # canvas px round a piece where its lift shadow shows a box's edge

KINDS = ('covers_strand', 'wrong_way', 'two_crossings', 'wrong_crossing')
CORNERS = ('top_left', 'top_right', 'bottom_right', 'bottom_left')
OPS = ('erase', 'reset', 'swap', 'delete', 'create')


class MaskError(ValueError):
    """An edit that cannot be done; the message says what to change."""


# ------------------------------------------------------------------ loading
class _Layers:
    """The canvas's layer order, as shader_utils reads it."""

    def __init__(self, strands):
        self.strands = strands
        self.layer_state = {}

    def getOrder(self):
        return [s.layer_name for s in self.strands]

    def getConnections(self):
        return {}

    def get_shadow_override(self, casting, receiving):
        return None

    def get_shadow_visibility(self, casting, receiving):
        return True

    def get_subtracted_layers(self, casting, receiving):
        return []


def _settings(data):
    block = data.get('project_settings') if isinstance(data, dict) else None
    out = dict(identify.DEFAULT_CURVE)
    if isinstance(block, dict):
        for key in out:
            if isinstance(block.get(key), (int, float)) and not isinstance(block.get(key), bool):
                out[key] = float(block[key])
    return out


def is_mask(item):
    return hasattr(item, 'get_mask_path') and hasattr(item, 'first_selected_strand')


class Design:
    """A project loaded with the app's own loader, its strands in the order
    the app draws them (masks above the strands, as apply_project_state).
    The data given is never changed: the loader shares lists with the dict it
    reads (a mask's erase boxes), so it reads a copy."""

    def __init__(self, data):
        from types import SimpleNamespace
        from .generators import application
        application()
        from save_load_manager import _with_masks_on_top, load_strands_from_data
        if not isinstance(data, dict) or not isinstance(data.get('strands'), list):
            raise MaskError('not an OpenStrand Studio project (it has no strands)')
        self.source = copy.deepcopy(data)
        self.curve = _settings(data)
        loader = SimpleNamespace(strands=[], groups={}, strand_colors={}, shadow_enabled=True,
                                 default_shadow_color=None, selected_strand=None,
                                 _suppress_layer_panel_refresh=True, _suppress_repaint=True,
                                 update=lambda: None, **self.curve)
        try:
            loaded = _with_masks_on_top(load_strands_from_data(copy.deepcopy(data), loader))
        except Exception as e:
            raise MaskError(f'the app cannot load the design: {type(e).__name__}: {e}') from None
        self.strands = [s for s in loaded[0] if s is not None]
        self.canvas = SimpleNamespace(strands=self.strands, shadow_enabled=True, shadow_selected_only=False,
                                      enable_third_control_point=False, selected_strand=None,
                                      default_shadow_color=None, strand_colors={},
                                      level_count=int(data.get('level_count', 0) or 0),
                                      level_colors=data.get('level_colors') or {},
                                      layer_state_manager=_Layers(self.strands), update=lambda: None,
                                      **self.curve)
        for s in self.strands:
            s.canvas = self.canvas
            for key, value in self.curve.items():
                setattr(s, key, value)
        for s in self.strands:
            if not is_mask(s):
                s.update_shape()

    # -- lookup
    def strand(self, name):
        for s in self.strands:
            if s.layer_name == str(name) and not is_mask(s):
                return s
        raise MaskError(f'there is no strand {name}; strands: {", ".join(self.names())}')

    def mask(self, name):
        name = str(name)
        for s in self.strands:
            if is_mask(s) and s.layer_name == name:
                return s
        raise MaskError(f'there is no mask {name}; masks: {", ".join(m.layer_name for m in self.masks()) or "none"}')

    def names(self):
        return [s.layer_name for s in self.strands if not is_mask(s)]

    def masks(self):
        return [s for s in self.strands if is_mask(s)]

    def find_mask(self, a, b):
        """The mask of strands a and b, either way round, or None."""
        for m in self.masks():
            if {m.first_selected_strand.layer_name, m.second_selected_strand.layer_name} == {a, b}:
                return m
        return None

    # -- saving
    def data(self):
        """The design as given, its strands and masks as the app saves them
        now: every other key (groups, colours, locks, levels, settings, the
        design's crossings) stays as it was, following the layers by name."""
        from save_load_manager import serialize_project_state
        out = copy.deepcopy(self.source)
        out['strands'] = serialize_project_state(self.strands, {}, self.canvas)['strands']
        before = [s.get('layer_name') for s in self.source['strands']]
        after = [s['layer_name'] for s in out['strands']]
        locked = {before[i] for i in self.source.get('locked_layers') or []
                  if isinstance(i, int) and 0 <= i < len(before)}
        if 'locked_layers' in out:
            out['locked_layers'] = [k for k, name in enumerate(after) if name in locked]
        if out.get('selected_strand_name') not in after:
            out['selected_strand_name'] = None
        gone = set(before) - set(after)
        for group in (out.get('groups') or {}).values():
            if not isinstance(group, dict):
                continue
            for key in ('strands', 'layers', 'main_strands'):
                if isinstance(group.get(key), list):
                    group[key] = [n for n in group[key] if n not in gone]
        return out


# ---------------------------------------------------------------- the grid
class Box:
    """A rectangle of the map's pixels: rows r0:r1, columns c0:c1."""
    __slots__ = ('r0', 'r1', 'c0', 'c1')

    def __init__(self, r0, r1, c0, c1):
        self.r0, self.r1, self.c0, self.c1 = int(r0), int(r1), int(c0), int(c1)

    @property
    def shape(self):
        return (max(0, self.r1 - self.r0), max(0, self.c1 - self.c0))

    @property
    def slice(self):
        return (slice(self.r0, self.r1), slice(self.c0, self.c1))

    def empty(self):
        return self.r1 <= self.r0 or self.c1 <= self.c0

    def intersect(self, other):
        return Box(max(self.r0, other.r0), min(self.r1, other.r1), max(self.c0, other.c0), min(self.c1, other.c1))

    def union(self, other):
        return Box(min(self.r0, other.r0), max(self.r1, other.r1), min(self.c0, other.c0), max(self.c1, other.c1))

    def local(self, other):
        """other's place inside this box, as slices of this box's arrays."""
        return (slice(other.r0 - self.r0, other.r1 - self.r0), slice(other.c0 - self.c0, other.c1 - self.c0))

    def contains(self, rows, cols):
        return (rows >= self.r0) & (rows < self.r1) & (cols >= self.c0) & (cols < self.c1)


def _of_pixels(rows, cols, grid, margin=0):
    return grid.clip(Box(rows.min() - margin, rows.max() + 1 + margin, cols.min() - margin, cols.max() + 1 + margin))


class Grid:
    """The canvas as pixels: x0, y0 in canvas units, scale pixels per unit."""

    def __init__(self, rect, scale):
        self.x0, self.y0 = math.floor(rect.left()) - 2, math.floor(rect.top()) - 2
        self.scale = scale
        self.w = max(1, int(math.ceil((rect.width() + 4) * scale)))
        self.h = max(1, int(math.ceil((rect.height() + 4) * scale)))

    def all(self):
        return Box(0, self.h, 0, self.w)

    def clip(self, box):
        return box.intersect(self.all())

    def box(self, rect, margin=0.0):
        """The pixels a canvas rectangle covers, grown by margin canvas units."""
        s = self.scale
        return self.clip(Box(math.floor((rect.top() - margin - self.y0) * s),
                             math.ceil((rect.bottom() + margin - self.y0) * s) + 1,
                             math.floor((rect.left() - margin - self.x0) * s),
                             math.ceil((rect.right() + margin - self.x0) * s) + 1))

    def around(self, x, y, radius):
        s = self.scale
        return self.clip(Box(math.floor((y - radius - self.y0) * s), math.ceil((y + radius - self.y0) * s) + 1,
                             math.floor((x - radius - self.x0) * s), math.ceil((x + radius - self.x0) * s) + 1))

    def canvas(self, col, row):
        """Canvas coordinates of a pixel's centre."""
        return self.x0 + (col + 0.5) / self.scale, self.y0 + (row + 0.5) / self.scale

    def pixel(self, x, y):
        return int((x - self.x0) * self.scale), int((y - self.y0) * self.scale)

    def centres(self, box):
        """Canvas x of each column and y of each row of a box."""
        cols = self.x0 + (np.arange(box.c0, box.c1) + 0.5) / self.scale
        rows = self.y0 + (np.arange(box.r0, box.r1) + 0.5) / self.scale
        return cols, rows

    def rect(self, rows, cols):
        """The canvas rectangle of some pixels: (x0, y0, x1, y1)."""
        return (self.x0 + cols.min() / self.scale, self.y0 + rows.min() / self.scale,
                self.x0 + (cols.max() + 1) / self.scale, self.y0 + (rows.max() + 1) / self.scale)


def paint(grid, box, items):
    """Paint (path, id) items in order over a box of the grid, no
    antialiasing: which id shows at each pixel (0 where nothing is)."""
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QColor, QImage, QPainter
    h, w = box.shape
    if h == 0 or w == 0:
        return np.zeros((h, w), dtype=np.int32)
    image = QImage(w, h, QImage.Format_RGB32)
    image.fill(0)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, False)
    painter.setPen(Qt.NoPen)
    painter.scale(grid.scale, grid.scale)
    painter.translate(-(grid.x0 + box.c0 / grid.scale), -(grid.y0 + box.r0 / grid.scale))
    for path, ident in items:
        if path is None or path.isEmpty():
            continue
        painter.setBrush(QColor((ident >> 16) & 255, (ident >> 8) & 255, ident & 255))
        painter.drawPath(path)
    painter.end()
    bits = image.constBits()
    bits.setsize(image.byteCount())
    raw = np.frombuffer(bits, dtype=np.uint32).reshape(h, image.bytesPerLine() // 4)[:, :w]
    return (raw & 0xFFFFFF).astype(np.int32)


def _filled(grid, box, path):
    return paint(grid, box, [(path, 1)]) == 1


class Scene:
    """What the app paints for a loaded design, as a paint map."""

    def __init__(self, design):
        import shader_utils
        self.design = design
        self.su = shader_utils
        self.cache = {}
        self.items = [s for s in design.strands if not getattr(s, 'is_hidden', False)]
        self.paths = {id(s): self.painted(s) for s in self.items}
        self.footprints = {id(s): self.su._drawn_footprint(s) for s in self.items if not is_mask(s)}
        bounds = None
        for path in list(self.paths.values()) + list(self.footprints.values()):
            if path is not None and not path.isEmpty():
                r = path.boundingRect()
                bounds = r if bounds is None else bounds.united(r)
        if bounds is None:
            raise MaskError('the design paints nothing')
        scale = SCALE
        if bounds.width() * bounds.height() * scale * scale > MAX_PIXELS:
            scale = math.sqrt(MAX_PIXELS / max(1.0, bounds.width() * bounds.height()))
        self.grid = Grid(bounds, scale)
        self.ids = {id(s): k + 1 for k, s in enumerate(self.items)}
        self.by_id = {k + 1: s for k, s in enumerate(self.items)}
        self.boxes = {}
        for s in self.items:
            path = self.footprints.get(id(s)) if not is_mask(s) else self.paths[id(s)]
            if path is not None and not path.isEmpty():
                self.boxes[id(s)] = self.grid.box(path.boundingRect(), margin=1.0)
        self.top = paint(self.grid, self.grid.all(),
                         [(self.paths[id(s)], self.ids[id(s)]) for s in self.items])
        self._cover = {}

    @property
    def window(self):
        return self.grid

    def painted(self, item):
        """What the item paints solidly, as the app draws it."""
        su = self.su
        if is_mask(item):
            if getattr(item, 'shadow_only', False):
                return None
            piece = su._mask_footprint(item)
            keep = su._piece_keep(item, self.cache)
            return piece.intersected(keep) if keep is not None else piece
        return su._opaque_cover(item, su._drawn_footprint(item))

    def pixel_area(self):
        return 1.0 / (self.grid.scale ** 2)

    def box_of(self, item):
        return self.boxes.get(id(item), Box(0, 0, 0, 0))

    # -- one strand's footprint, in its own box
    def cover(self, strand):
        key = id(strand)
        if key not in self._cover:
            box = self.box_of(strand)
            path = self.footprints.get(key)
            arr = _filled(self.grid, box, path) if path is not None and not box.empty() else np.zeros(box.shape, bool)
            self._cover[key] = (box, arr)
        return self._cover[key]

    def cover_in(self, strand, box):
        own, arr = self.cover(strand)
        out = np.zeros(box.shape, dtype=bool)
        both = own.intersect(box)
        if not both.empty():
            out[box.local(both)] = arr[own.local(both)]
        return out

    def cover_at(self, strand, rows, cols):
        own, arr = self.cover(strand)
        out = np.zeros(len(rows), dtype=bool)
        k = own.contains(rows, cols)
        out[k] = arr[rows[k] - own.r0, cols[k] - own.c0]
        return out

    def near(self, box):
        """The items whose boxes meet a box."""
        return [s for s in self.items if not self.box_of(s).intersect(box).empty()]

    def ids_without(self, mask, box):
        """What shows over a box were the mask not there."""
        return paint(self.grid, box, [(self.paths[id(s)], self.ids[id(s)]) for s in self.near(box) if s is not mask])

    def edges_in(self, box):
        """Pixels on or just inside a strand's outline, and just outside it:
        where a mask's piece may end without showing a cut."""
        edges = np.zeros(box.shape, dtype=bool)
        for s in self.near(box):
            if is_mask(s):
                continue
            cover = self.cover_in(s, box)
            if not cover.any():
                continue
            k = max(2, int(round((getattr(s, 'stroke_width', 2) + 1.5) * self.grid.scale)))
            edges |= cover & ~_shrink(cover, k)
            edges |= _grow(cover, 2) & ~cover
        return edges

    def bodies_in(self, box):
        bodies = np.zeros(box.shape, dtype=bool)
        for s in self.near(box):
            if not is_mask(s):
                bodies |= self.cover_in(s, box)
        return bodies


# ------------------------------------------------------------------- cords
class Cords:
    """The cords' centre lines from the app's paths, which strand draws each
    part, and where along its cord each pixel of a strand lies."""

    def __init__(self, design, scene):
        self.design, self.scene = design, scene
        plain = [s for s in design.source['strands'] if s.get('type') != 'MaskedStrand']
        by_name = {s.layer_name: s for s in design.strands if not is_mask(s)}
        self.lines, self.owners, self.closed, self.arcs = [], [], [], []
        self.where = {}        # strand name -> (cord, samples (n, 2), arc positions (n,))
        for chain in identify._chains(plain):
            pts, own = [], []
            for strand_data, forward in chain:
                strand = by_name.get(strand_data['layer_name'])
                if strand is None:
                    continue
                piece = self._samples(strand)
                if not forward:
                    piece = piece[::-1]
                if pts and math.dist(pts[-1], piece[0]) < 1.0:
                    piece = piece[1:]
                pts += piece
                own += [strand.layer_name] * len(piece)
            if len(pts) < 2:
                continue
            closed = len(chain) > 1 and math.dist(pts[0], pts[-1]) < 1.0
            if closed:
                pts, own = pts[:-1], own[:-1]
            line = np.array(pts, dtype=float)
            arc = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(line, axis=0).T))])
            c = len(self.lines)
            self.lines.append(line)
            self.owners.append(own)
            self.closed.append(bool(closed))
            self.arcs.append(arc)
            names = np.array(own)
            for name in dict.fromkeys(own):
                k = names == name
                self.where[name] = (c, line[k], arc[k])
        self.length = [a[-1] + (math.dist(l[0], l[-1]) if cl else 0.0)
                       for a, l, cl in zip(self.arcs, self.lines, self.closed)]
        self._along = {}

    @staticmethod
    def _samples(strand):
        path = strand.get_path()
        n = max(8, int(path.length() / SAMPLE))
        return [(path.pointAtPercent(k / n).x(), path.pointAtPercent(k / n).y()) for k in range(n + 1)]

    def cord_of(self, name):
        return self.where[name][0] if name in self.where else None

    def on(self, cord):
        """The strands of a cord."""
        if not hasattr(self, '_on'):
            self._on = {}
            for name, (k, _, _) in self.where.items():
                self._on.setdefault(k, []).append(name)
        return self._on.get(cord, [])

    def gap(self, cord, a, b):
        """Distance along a cord between arc positions (arrays welcome)."""
        d = np.abs(a - b)
        if self.closed[cord]:
            d = np.minimum(d, self.length[cord] - d)
        return d

    def along(self, strand):
        """(box, arc position along its cord of every pixel of the strand's
        footprint in its box, NaN elsewhere)."""
        key = strand.layer_name
        if key not in self._along:
            box, cover = self.scene.cover(strand)
            out = np.full(box.shape, np.nan)
            if key in self.where and cover.any():
                _, pts, arc = self.where[key]
                rows, cols = np.nonzero(cover)
                xs, ys = self.scene.grid.centres(box)
                out[rows, cols] = arc[_nearest(pts, xs[cols], ys[rows])]
            self._along[key] = (box, out)
        return self._along[key]

    def along_in(self, strand, box):
        own, arr = self.along(strand)
        out = np.full(box.shape, np.nan)
        both = own.intersect(box)
        if not both.empty():
            out[box.local(both)] = arr[own.local(both)]
        return out

    def along_at(self, strand, rows, cols):
        own, arr = self.along(strand)
        out = np.full(len(rows), np.nan)
        k = own.contains(rows, cols)
        out[k] = arr[rows[k] - own.r0, cols[k] - own.c0]
        return out

    def crossings(self):
        """Where the centre lines cross: each cord with itself, and each pair
        of cords whose outlines meet, on lines thinned to every
        CROSSING_STEP-th sample (positions given on the full lines)."""
        thin, maps = [], []
        for line, arc, closed in zip(self.lines, self.arcs, self.closed):
            k = np.arange(0, len(line), CROSSING_STEP)
            if k[-1] != len(line) - 1:
                k = np.append(k, len(line) - 1)
            t = line[k]
            ta = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(t, axis=0).T))])
            fa = arc[k]
            if closed:
                ta = np.append(ta, ta[-1] + math.dist(t[-1], t[0]))
                fa = np.append(fa, fa[-1] + math.dist(line[-1], line[0]))
            thin.append(t)
            maps.append((ta, fa))
        lo = [t.min(axis=0) for t in thin]
        hi = [t.max(axis=0) for t in thin]
        found = []

        def keep(hits, which):
            for h in hits:
                a, b = (which[h['cords'][0]], which[h['cords'][1]])
                if len(which) == 2 and a == b:
                    continue            # a cord with itself: done on its own
                pa = float(np.interp(h['positions'][0], *maps[a]))
                pb = float(np.interp(h['positions'][1], *maps[b]))
                found.append(dict(point=h['point'], cords=(a, b), positions=(pa, pb), angle=h['angle']))
        for a in range(len(thin)):
            keep(invariants.crossings([thin[a]], [self.closed[a]]), [a])
        for a in range(len(thin)):
            for b in range(a + 1, len(thin)):
                if np.all(lo[a] <= hi[b] + 1) and np.all(lo[b] <= hi[a] + 1):
                    keep(invariants.crossings([thin[a], thin[b]], [self.closed[a], self.closed[b]]), [a, b])
        return found


def _nearest(pts, px, py, step=8):
    """For each point (px, py), the index of the nearest of pts (a dense
    polyline): first among every step-th, then among its neighbours."""
    out = np.empty(len(px), dtype=np.int64)
    coarse = pts[::step]
    reach = np.arange(-step, step + 1)
    for lo in range(0, len(px), 8192):
        x, y = px[lo:lo + 8192], py[lo:lo + 8192]
        k0 = np.argmin((x[:, None] - coarse[None, :, 0]) ** 2 + (y[:, None] - coarse[None, :, 1]) ** 2, axis=1)
        idx = np.clip(k0[:, None] * step + reach[None, :], 0, len(pts) - 1)
        d = (x[:, None] - pts[idx, 0]) ** 2 + (y[:, None] - pts[idx, 1]) ** 2
        out[lo:lo + 8192] = idx[np.arange(len(x)), np.argmin(d, axis=1)]
    return out


# ---------------------------------------------------------------- crossings
def _owner(cords, c, position):
    arc, own = cords.arcs[c], cords.owners[c]
    k = int(np.clip(np.searchsorted(arc, position), 0, len(own) - 1))
    return own[k]


def _reach(width, angle):
    """How far along each cord a crossing's overlap reaches from its centre."""
    half = width / 2.0
    theta = math.radians(max(15.0, min(90.0, angle)))
    return min(3.0 * width, half / math.tan(theta / 2) * 1.15 + half * 0.5 + 2.0)


class Crossing:
    def __init__(self, k, hit, cords, design, grid):
        self.index = k
        self.point = tuple(float(v) for v in hit['point'][:2])
        self.cords = tuple(hit['cords'])
        self.positions = tuple(float(p) for p in hit['positions'])
        self.angle = float(hit.get('angle', 90.0))
        self.strands = (_owner(cords, self.cords[0], self.positions[0]),
                        _owner(cords, self.cords[1], self.positions[1]))
        widths = [design.strand(n).width + 2 * design.strand(n).stroke_width for n in self.strands]
        self.width = max(widths)
        self.reach = _reach(self.width, self.angle)
        self.box = grid.around(self.point[0], self.point[1], self.reach + self.width + 4)
        self.over = None       # 0 or 1: which side goes over
        self.source = None     # 'design' or 'drawing'


def _stored_intent(design, crossings, cords):
    """Over and under from the design's stored crossings, where they match."""
    stored = design.source.get('design_crossings') or []
    for c in crossings:
        best = None
        for entry in stored:
            try:
                x, y = entry['point']
                over, under = str(entry['over']), str(entry['under'])
            except (KeyError, TypeError, ValueError):
                continue
            d = math.dist((float(x), float(y)), c.point)
            if d <= 0.6 * c.width and (best is None or d < best[0]):
                best = (d, over, under)
        if best is None:
            continue
        _, over, under = best
        side = _side_of(cords, c, over, under)
        if side is not None:
            c.over, c.source = side, 'design'


def _side_of(cords, c, over, under):
    """Which side of the crossing the stored over strand is on."""
    if c.strands == (over, under) or (c.strands[0] == over and c.strands[1] != over):
        return 0
    if c.strands == (under, over) or (c.strands[1] == over and c.strands[0] != over):
        return 1
    if over in cords.where:
        oc, _, arc = cords.where[over]
        dist = []
        for side in (0, 1):
            if c.cords[side] != oc:
                dist.append(math.inf)
            else:
                dist.append(float(np.min(cords.gap(oc, arc, c.positions[side]))))
        if min(dist) < math.inf and dist[0] != dist[1]:
            return 0 if dist[0] < dist[1] else 1
    return None


# ----------------------------------------------------------------- analysis
class Analysis:
    """The paint map of a design checked against its crossings."""

    def __init__(self, data):
        self.design = Design(data)
        self.scene = Scene(self.design)
        self.cords = Cords(self.design, self.scene)
        self.crossings = [Crossing(k, h, self.cords, self.design, self.scene.grid)
                          for k, h in enumerate(self.cords.crossings())]
        _stored_intent(self.design, self.crossings, self.cords)
        self.lifted = {}           # strand name -> the masks that lift it
        for m in self.design.masks():
            self.lifted.setdefault(m.first_selected_strand.layer_name, []).append(m)
        self._parts = {}
        self._problems = None
        self._unsure = []
        self._decide()

    # -- the two sides of a crossing, in its box
    def part(self, c, side):
        """Pixels of the crossing's box the cord covers near the crossing on
        one side, and the strands drawing it there."""
        key = (c.index, side)
        if key not in self._parts:
            cord, at = c.cords[side], c.positions[side]
            region = np.zeros(c.box.shape, dtype=bool)
            names = []
            for name in self.cords.on(cord):
                _, _, arc = self.cords.where[name]
                if float(np.min(self.cords.gap(cord, arc, at))) > c.reach + c.width:
                    continue
                along = self.cords.along_in(self.design.strand(name), c.box)
                ok = ~np.isnan(along)
                if not ok.any():
                    continue
                near = np.zeros_like(region)
                near[ok] = self.cords.gap(cord, along[ok], at) <= c.reach
                if near.any():
                    region |= near
                    names.append(name)
            self._parts[key] = (region, names)
        return self._parts[key]

    def _cost(self, c):
        """For each pixel of the crossing's box both sides cover: how far it
        lies from the crossing, along each cord, summed (inf elsewhere)."""
        key = ('cost', c.index)
        if key not in self._parts:
            total = np.zeros(c.box.shape)
            for side in (0, 1):
                region, names = self.part(c, side)
                best = np.full(c.box.shape, np.inf)
                for name in names:
                    along = self.cords.along_in(self.design.strand(name), c.box)
                    ok = ~np.isnan(along)
                    gap = np.full(c.box.shape, np.inf)
                    gap[ok] = self.cords.gap(c.cords[side], along[ok], c.positions[side])
                    best = np.minimum(best, gap)
                total += np.where(region, best, np.inf)
            self._parts[key] = total
            rows, cols = np.nonzero(np.isfinite(total))
            # The tight box of the crossing's own pixels, for finding the crossings it meets.
            self._parts[('tight', c.index)] = (Box(rows.min() + c.box.r0, rows.max() + 1 + c.box.r0,
                                                    cols.min() + c.box.c0, cols.max() + 1 + c.box.c0)
                                                if len(rows) else Box(0, 0, 0, 0))
        return self._parts[key]

    def _tight(self, c):
        self._cost(c)
        return self._parts[('tight', c.index)]

    def claimed(self, c):
        """The pixels of the crossing: both sides cover them, and no other
        crossing they also belong to is nearer along the cords. Where the same
        cords cross several times close together (a fold, a tight turn), each
        pixel is held to one crossing."""
        key = ('claimed', c.index)
        if key not in self._parts:
            mine = self._cost(c)
            out = np.isfinite(mine)
            if not hasattr(self, '_tight_array'):
                tight = [self._tight(d) for d in self.crossings]
                self._tight_array = np.array([[b.r0, b.r1, b.c0, b.c1] for b in tight] or np.zeros((0, 4)))
            b, own = self._tight_array, self._tight(c)
            near = np.nonzero((b[:, 0] < own.r1) & (b[:, 1] > own.r0) & (b[:, 2] < own.c1) & (b[:, 3] > own.c0))[0]
            for k in near:
                d = self.crossings[k]
                if d is c:
                    continue
                both = own.intersect(self._tight(d))
                if both.empty():
                    continue
                theirs = self._cost(d)[d.box.local(both)]
                here = mine[c.box.local(both)]
                nearer = theirs < here - 1e-6
                if nearer.any():
                    sub = out[c.box.local(both)]
                    sub &= ~nearer
                    out[c.box.local(both)] = sub
            self._parts[key] = out
        return self._parts[key]

    def _items_of(self, name):
        strand = self.design.strand(name)
        return [strand] + self.lifted.get(name, [])

    def shown(self, ids, c, side):
        """Where, in the crossing's box, the side of the crossing is what
        shows, in a paint map of the box (ids)."""
        _, names = self.part(c, side)
        out = np.zeros(c.box.shape, dtype=bool)
        for name in names:
            along = self.cords.along_in(self.design.strand(name), c.box)
            for item in self._items_of(name):
                ident = self.scene.ids.get(id(item))
                if ident is None:
                    continue
                here = (ids == ident) & ~np.isnan(along)
                if here.any():
                    close = np.zeros_like(here)
                    close[here] = self.cords.gap(c.cords[side], along[here], c.positions[side]) <= c.reach
                    out |= close
        return out

    def shown_at(self, values, rows, cols, c, side):
        """The same for some pixels, given what shows at each (values)."""
        _, names = self.part(c, side)
        out = np.zeros(len(rows), dtype=bool)
        for name in names:
            along = self.cords.along_at(self.design.strand(name), rows, cols)
            for item in self._items_of(name):
                ident = self.scene.ids.get(id(item))
                here = (values == ident) & ~np.isnan(along)
                if here.any():
                    out[here] |= self.cords.gap(c.cords[side], along[here], c.positions[side]) <= c.reach
        return out

    def _decide(self):
        """Over and under for crossings the design does not say, as identify
        reads them: the crossing's own mask (its two strands' mask, unless it
        is erased there), else what most of the crossing shows, else what its
        centre shows."""
        grid = self.scene.grid
        for c in self.crossings:
            if c.over is not None:
                continue
            mask = self.design.find_mask(*c.strands) if c.strands[0] != c.strands[1] else None
            if mask is not None and not any(identify._inside(c.point, box) for box in
                                            (identify._corners(r) for r in mask.deletion_rectangles or []) if box):
                first = mask.first_selected_strand.layer_name
                c.over, c.source = (0 if c.strands[0] == first else 1), 'mask'
                continue
            top = self.scene.top[c.box.slice]
            shows = (self.shown(top, c, 0), self.shown(top, c, 1))
            both = self.claimed(c)
            a, b = int((shows[0] & both).sum()), int((shows[1] & both).sum())
            if abs(a - b) <= 0.1 * max(a, b, 1):
                # About even: what its centre shows decides.
                cols, rows = grid.centres(c.box)
                near = (((cols[None, :] - c.point[0]) ** 2 + (rows[:, None] - c.point[1]) ** 2)
                        <= (c.width / 4.0) ** 2)
                a, b = int((shows[0] & near).sum()), int((shows[1] & near).sum())
            c.over, c.source = (0 if a >= b else 1), 'drawing'

    # -- the problems
    def problems_cache(self):
        return self.problems()

    def problems(self):
        """Every problem, biggest first within each kind (see the module text)."""
        if self._problems is not None:
            return self._problems
        scene = self.scene
        area = scene.pixel_area()
        found = []
        for c in self.crossings:
            o, u = c.over, 1 - c.over
            both = self.claimed(c)
            if not both.any():
                continue
            top = scene.top[c.box.slice]
            bad = self.shown(top, c, u) & both & ~self.shown(top, c, o)
            if bad.sum() * area < MIN_AREA:
                continue
            for rows, cols in _components(_solid(bad)):
                if len(rows) * area >= MIN_AREA and _thick(rows, cols, scene.grid):
                    found.append(self._wrong_way(c, rows + c.box.r0, cols + c.box.c0))
        for mask in self.design.masks():
            found += self._covers(mask)
        found += self._two_crossings()
        order = {k: n for n, k in enumerate(KINDS)}
        found = [f for f in found if f is not None]
        found.sort(key=lambda f: (order[f['kind']], -f['area']))
        # Where nothing says which strand goes over (no design crossings, no
        # mask of the two strands), the crossing is read from the drawing
        # itself: a guess, so such places are listed apart, not as problems.
        self._unsure = [f for f in found if f.get('source') == 'drawing' and f['kind'] in ('wrong_way', 'wrong_crossing')]
        found = [f for f in found if f not in self._unsure]
        self._problems = found
        # Suggest an erase only where one fits: shaped boxes that take the
        # place out without cutting into the rest of the piece.
        for p in found:
            fix = p.get('fix') or {}
            if fix.get('op') == 'erase' and not self._erase_fits(p):
                p['fix'] = None
                p['text'] = _say(p)
        return found

    def _erase_fits(self, p):
        mask = self.design.mask(p['fix']['mask'])
        strands = [self.design.strand(n) for n in (p.get('strand'), p.get('should_show'))
                   if n and n in self.design.names()]
        strands += [mask.first_selected_strand, mask.second_selected_strand]
        quads, _, _ = best_erase(self, mask, p['fix']['region'], _keep_for(self, mask), strands=strands)
        return bool(quads)

    def _ident_strand(self, ident):
        item = self.scene.by_id.get(int(ident))
        if item is None:
            return None, None
        if is_mask(item):
            return item.first_selected_strand, item
        return item, None

    def _place(self, rows, cols):
        x0, y0, x1, y1 = self.scene.grid.rect(rows, cols)
        return (round((x0 + x1) / 2, 1), round((y0 + y1) / 2, 1)), [round(v, 1) for v in (x0, y0, x1, y1)]

    def _wrong_way(self, c, rows, cols):
        scene, design = self.scene, self.design
        o, u = c.over, 1 - c.over
        idents, counts = np.unique(scene.top[rows, cols], return_counts=True)
        shown, mask = self._ident_strand(idents[np.argmax(counts)])
        # The strand of the side on top that covers most of the place.
        best, should = 0, None
        for name in self.part(c, o)[1]:
            n = int(scene.cover_at(design.strand(name), rows, cols).sum())
            if n > best:
                best, should = n, name
        at, box = self._place(rows, cols)
        problem = dict(kind='wrong_crossing' if _contains(scene, rows, cols, c.point) and c.source == 'design'
                       else 'wrong_way', at=at, box=box, area=round(len(rows) * scene.pixel_area(), 1),
                       crossing=[round(c.point[0], 1), round(c.point[1], 1)],
                       shows=shown.layer_name if shown is not None else None, should_show=should,
                       mask=mask.layer_name if mask is not None else None, source=c.source)
        fix = None
        if mask is not None:
            # Without this mask, does the right side show there?
            place = _of_pixels(rows, cols, scene.grid)
            under = scene.ids_without(mask, place)[rows - place.r0, cols - place.c0]
            if self.shown_at(under, rows, cols, c, o).mean() > 0.8:
                fix = dict(op='erase', mask=mask.layer_name, region=(rows, cols))
            elif mask.second_selected_strand.layer_name == should:
                fix = dict(op='swap', mask=mask.layer_name)
        if fix is None and should and shown is not None and shown.layer_name != should:
            existing = design.find_mask(should, shown.layer_name)
            if existing is None:
                fix = dict(op='create', first=should, second=shown.layer_name)
        if c.source == 'drawing':
            # Which side goes over is only read from the drawing: a fix made
            # from that guess would make itself right (a new mask becomes the
            # crossing's own mask), so none is offered.
            fix = None
        problem['fix'] = fix
        problem['region'] = (rows, cols)
        problem['text'] = _say(problem)
        return problem

    def _covers(self, mask):
        """Where the mask's piece hides a strand that shows without it."""
        scene = self.scene
        ident = scene.ids.get(id(mask))
        box = scene.box_of(mask)
        if ident is None or box.empty():
            return []
        mine = scene.top[box.slice] == ident
        if not mine.any():
            return []
        under = scene.ids_without(mask, box)
        first, second = mask.first_selected_strand, mask.second_selected_strand
        out = []
        for other_ident in np.unique(under[mine]):
            other, via = self._ident_strand(other_ident)
            if other is None or other is first or other is second:
                continue
            if scene.su._joined(other, (first,)):
                continue        # it continues the strand on top: the piece hides the joint, as the app means it to
            hidden = mine & (under == other_ident)
            for c in self.crossings:
                both = c.box.intersect(box)
                if both.empty():
                    continue
                for side in (0, 1):
                    names, others = self.part(c, side)[1], self.part(c, 1 - side)[1]
                    region = self.part(c, side)[0]
                    if other.layer_name in names and first.layer_name in names:
                        # Both on the same side of a crossing: either may show.
                        hidden[box.local(both)] &= ~region[c.box.local(both)]
                    if side == c.over and other.layer_name in others and \
                            (first.layer_name in names or second.layer_name in names):
                        # The crossing puts the mask's strand over the hidden one here.
                        where = self.claimed(c)
                        hidden[box.local(both)] &= ~where[c.box.local(both)]
            if hidden.sum() * scene.pixel_area() < MIN_AREA:
                continue
            for rows, cols in _components(_solid(hidden)):
                a = len(rows) * scene.pixel_area()
                if a < MIN_AREA or not _thick(rows, cols, scene.grid):
                    continue
                rows, cols = rows + box.r0, cols + box.c0
                at, rect = self._place(rows, cols)
                problem = dict(kind='covers_strand', mask=mask.layer_name, strand=other.layer_name,
                               via=via.layer_name if via is not None else None, at=at, box=rect,
                               area=round(a, 1), fix=dict(op='erase', mask=mask.layer_name, region=(rows, cols)),
                               region=(rows, cols))
                problem['text'] = _say(problem)
                out.append(problem)
        return out

    def pieces(self, mask, erased=False):
        """The mask's pieces, one per crossing of its two strands, as pixel
        components of what it paints (all of it, erase boxes left out, unless
        erased: then as drawn)."""
        key = ('pieces', id(mask), erased)
        if key not in self._parts:
            self._parts[key] = self._pieces(mask, erased)
        return self._parts[key]

    def _pieces(self, mask, erased):
        if erased:
            path = self.scene.paths.get(id(mask))
        else:
            boxes = mask.deletion_rectangles
            mask.deletion_rectangles = []
            try:
                path = self.scene.su._mask_footprint(mask)   # strands above do not split a crossing
            finally:
                mask.deletion_rectangles = boxes
        if path is None or path.isEmpty():
            return []
        box = self.scene.grid.box(path.boundingRect(), margin=1.0)
        drawn = _filled(self.scene.grid, box, path)
        return [(r + box.r0, c + box.c0) for r, c in _components(drawn)
                if len(r) * self.scene.pixel_area() >= MIN_AREA]

    def _two_crossings(self):
        scene = self.scene
        out = []
        for mask in self.design.masks():
            a, b = mask.first_selected_strand.layer_name, mask.second_selected_strand.layer_name
            pieces = self.pieces(mask)
            if len(pieces) < 2:
                continue
            path = scene.paths.get(id(mask))
            for rows, cols in pieces:
                c = self._crossing_in(rows, cols, a, b)
                if c is None or c.source != 'design' or not self._on_top(c, b):
                    continue
                place = _of_pixels(rows, cols, scene.grid)
                drawn = _filled(scene.grid, place, path) if path is not None else np.zeros(place.shape, bool)
                if drawn[rows - place.r0, cols - place.c0].mean() < 0.2:
                    continue            # erased already
                at, rect = self._place(rows, cols)
                problem = dict(kind='two_crossings', mask=mask.layer_name, first=a, second=b,
                               crossings=len(pieces), at=(round(c.point[0], 1), round(c.point[1], 1)),
                               box=rect, area=round(len(rows) * scene.pixel_area(), 1),
                               fix=dict(op='erase', mask=mask.layer_name, region=(rows, cols)),
                               region=(rows, cols))
                problem['text'] = _say(problem)
                out.append(problem)
        return out

    def _on_top(self, c, name):
        """Whether the strand is on the crossing's over side."""
        return name in self.part(c, c.over)[1] and name not in self.part(c, 1 - c.over)[1]

    def _crossing_in(self, rows, cols, a, b):
        best = None
        for c in self.crossings:
            n0, n1 = self.part(c, 0)[1], self.part(c, 1)[1]
            if not ((a in n0 and b in n1) or (a in n1 and b in n0)):
                continue
            px, py = self.scene.grid.pixel(*c.point)
            d = float(np.min(np.hypot(cols - px, rows - py))) / self.scene.grid.scale
            if d <= c.width and (best is None or d < best[0]):
                best = (d, c)
        return best[1] if best else None

    # -- the report
    def masks_list(self):
        out = []
        for mask in self.design.masks():
            a, b = mask.first_selected_strand, mask.second_selected_strand
            path = self.scene.paths.get(id(mask))
            r = path.boundingRect() if path is not None and not path.isEmpty() else None
            centre = (round(r.center().x(), 1), round(r.center().y(), 1)) if r is not None else None
            boxes = [_box_of(rect) for rect in mask.deletion_rectangles or []]
            out.append(dict(name=mask.layer_name, on_top=a.layer_name, under=b.layer_name, centre=centre,
                            boxes=boxes, crossings=len(self.pieces(mask)),
                            hidden=bool(getattr(mask, 'is_hidden', False))))
        return out


def _box_of(rect):
    try:
        xs = [float(rect[k][0]) for k in CORNERS if k in rect]
        ys = [float(rect[k][1]) for k in CORNERS if k in rect]
        if xs:
            return [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)]
        return [round(rect['x'], 1), round(rect['y'], 1), round(rect['x'] + rect['width'], 1),
                round(rect['y'] + rect['height'], 1)]
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def _contains(scene, rows, cols, point):
    px, py = scene.grid.pixel(*point)
    near = (np.abs(rows - py) <= 2) & (np.abs(cols - px) <= 2)
    return bool(near.any())


def _grow(mask, k):
    """The map grown by k pixels (a square around each)."""
    out = mask.copy()
    for _ in range(k):
        step = out.copy()
        step[1:, :] |= out[:-1, :]
        step[:-1, :] |= out[1:, :]
        step[:, 1:] |= out[:, :-1]
        step[:, :-1] |= out[:, 1:]
        out = step
    return out


def _shrink(mask, k):
    return ~_grow(~mask, k)


def _thick(rows, cols, grid, thickness=MIN_THICK):
    """Whether some part of the pixels is thickness canvas px across."""
    k = max(1, int(round(thickness / 2 * grid.scale)))
    r0, c0 = rows.min(), cols.min()
    m = np.zeros((rows.max() - r0 + 3, cols.max() - c0 + 3), dtype=bool)
    m[rows - r0 + 1, cols - c0 + 1] = True
    return bool(_shrink(m, k).any())


def _solid(mask):
    """The map without its hairlines: pixels of lines one pixel thin (the
    antialiased rims where two paths almost meet) are dropped, and what is
    left grown back by a pixel inside the map."""
    core = mask.copy()
    core[1:, :] &= mask[:-1, :]
    core[:-1, :] &= mask[1:, :]
    core[:, 1:] &= mask[:, :-1]
    core[:, :-1] &= mask[:, 1:]
    return _grow(core, 1) & mask


def _components(mask):
    """Connected parts of a boolean map (8-neighbours): [(rows, cols)].
    Labelled by runs along each row, so a large piece costs its rows, not
    its pixels."""
    if not mask.any():
        return []
    h, w = mask.shape
    padded = np.zeros((h, w + 2), dtype=np.int8)
    padded[:, 1:-1] = mask
    edges = np.diff(padded, axis=1)
    sr, sc = np.nonzero(edges == 1)        # run starts (row, first column)
    er, ec = np.nonzero(edges == -1)       # run ends (row, column after the last)
    starts, ends, rows_of = sc, ec - 1, sr  # both come out row by row, left to right
    n = len(starts)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    first = np.searchsorted(rows_of, np.arange(h + 1))
    for r in range(1, h):
        a0, a1 = first[r - 1], first[r]
        b0, b1 = first[r], first[r + 1]
        if a0 == a1 or b0 == b1:
            continue
        i = a0
        for j in range(b0, b1):
            # Runs of the row above that touch this one, diagonals included.
            while i < a1 and ends[i] < starts[j] - 1:
                i += 1
            k = i
            while k < a1 and starts[k] <= ends[j] + 1:
                ri, rj = find(k), find(j)
                if ri != rj:
                    parent[max(ri, rj)] = min(ri, rj)
                k += 1
    roots = np.array([find(i) for i in range(n)])
    out = []
    for root in np.unique(roots):
        runs = np.nonzero(roots == root)[0]
        lengths = ends[runs] - starts[runs] + 1
        rows = np.repeat(rows_of[runs], lengths)
        offsets = np.arange(lengths.sum()) - np.repeat(np.cumsum(lengths) - lengths, lengths)
        cols = np.repeat(starts[runs], lengths) + offsets
        out.append((rows, cols))
    return out


def _say(p):
    x, y = p['at']
    where = f'at ({x:.0f}, {y:.0f})'
    size = f"{p['area']:.0f} px²"
    fix = p.get('fix') or {}
    if p['kind'] == 'covers_strand':
        via = f" (where mask {p['via']} lifts it)" if p.get('via') else ''
        return (f"mask {p['mask']} paints over strand {p['strand']}{via} {where}, {size}: "
                f"{p['strand']} should show there. Fix: edit_mask erase, mask {p['mask']}, covers {p['strand']}.")
    if p['kind'] in ('wrong_way', 'wrong_crossing'):
        what = ('the crossing is drawn the other way round from the design'
                if p['kind'] == 'wrong_crossing' else 'part of the crossing shows the wrong strand on top')
        cause = f" (mask {p['mask']} paints it)" if p.get('mask') else ' (by layer order: no mask there)'
        text = (f"{what} {where}, {size}, crossing at ({p['crossing'][0]:.0f}, {p['crossing'][1]:.0f}): "
                f"{p['shows']} shows{cause}, {p['should_show']} should be on top.")
        if fix.get('op') == 'erase':
            text += f" Fix: edit_mask erase, mask {fix['mask']}, at [{x:.0f}, {y:.0f}]."
        elif fix.get('op') == 'create':
            text += f" Fix: edit_mask create, first {fix['first']}, second {fix['second']}."
        elif fix.get('op') == 'swap':
            text += f" Fix: edit_mask swap, mask {fix['mask']} (preview it: the mask may cover another crossing)."
        elif p.get('mask'):
            text += (f" No single mask edit fixes it cleanly: mask {p['mask']} is right next to here and an erase "
                     'would cut into it. Leave it, or move the strands apart.')
        else:
            text += ' No single mask edit fixes it: the strands lie too close there.'
        if p.get('source') == 'drawing':
            text = text.split(' No single mask edit')[0]
            text += (' Neither the design nor a mask of these two strands says which goes over here (this reads it '
                     'from what most of the crossing shows), so no edit is offered: render and look, and fix it by '
                     'hand only if the picture is wrong.')
        return text
    return (f"mask {p['mask']} covers {p['crossings']} crossings of {p['first']} and {p['second']}; "
            f"the one {where} should have {p['second']} on top but the mask draws {p['first']} there. "
            f"Fix: edit_mask erase, mask {p['mask']}, around [{x:.0f}, {y:.0f}] (its whole piece there).")


# ----------------------------------------------------------- the check
def check(data):
    """Every mask and every mask problem of a design:
    dict(masks=[...], problems=[...], crossings=n, intent=[...], text=...)."""
    return _report(Analysis(data))


def _report(analysis):
    problems = _plain(analysis.problems())
    unsure = _plain(analysis._unsure)
    masks = analysis.masks_list()
    return dict(masks=masks, problems=problems, unsure=unsure, crossings=len(analysis.crossings),
                intent=sorted({c.source for c in analysis.crossings}), text=summary(masks, problems, unsure=unsure))


def summary(masks, problems, limit=30, unsure=()):
    lines = [f'{len(masks)} masks:']
    for m in masks:
        boxes = '; '.join(f'({b[0]:.0f}, {b[1]:.0f})-({b[2]:.0f}, {b[3]:.0f})' for b in m['boxes'] if b) or 'none'
        centre = f"({m['centre'][0]:.0f}, {m['centre'][1]:.0f})" if m['centre'] else 'nothing painted'
        more = f", covers {m['crossings']} crossings" if m['crossings'] > 1 else ''
        lines.append(f"  {m['name']}: {m['on_top']} over {m['under']}, centre {centre}{more}, erase boxes: {boxes}")
    if not problems:
        lines.append('no mask problems: every crossing shows the strand on top all over, and no mask hides a '
                     'strand that should show.')
    else:
        lines.append(f'{len(problems)} problems:')
        for p in problems[:limit]:
            lines.append('  ' + p['text'])
        if len(problems) > limit:
            lines.append(f'  … and {len(problems) - limit} more')
    if unsure:
        places = '; '.join(f"({p['at'][0]:.0f}, {p['at'][1]:.0f}) {p['shows']} on top" for p in unsure[:12])
        more = f' and {len(unsure) - 12} more' if len(unsure) > 12 else ''
        lines.append(f'{len(unsure)} place{"s" if len(unsure) != 1 else ""} it cannot judge: neither the design nor a '
                     'mask of the two strands says which goes over there, and the crossing shows both ways. Look at '
                     f'them on the render before changing anything: {places}{more}.')
    return '\n'.join(lines)


def _plain(problems):
    """Problems as plain data: without the pixel regions the fixes use."""
    out = []
    for p in problems:
        p = {k: v for k, v in p.items() if k != 'region'}
        if p.get('fix') and 'region' in p['fix']:
            p['fix'] = {k: v for k, v in p['fix'].items() if k != 'region'}
        p['at'] = [float(v) for v in p['at']]
        p['box'] = [float(v) for v in p['box']]
        out.append(p)
    return out


# -------------------------------------------------------------- erase boxes
# An erase box is stored by its four corners, so it can lie at any angle (the
# app's own boxes turn when they follow their crossing). A box with straight
# sides along the canvas cuts a diagonal strand in steps, so the boxes made
# here follow a strand: short quads along its centre line, as wide as the
# strand, which uncover it with its own outline. Several shapes are tried
# and measured on the paint map: the one that erases the place, takes least
# of the piece that should stay and leaves the fewest visible cut edges wins.

def _quad_path(quads):
    from PyQt5.QtCore import QPointF, Qt
    from PyQt5.QtGui import QPainterPath, QPolygonF
    path = QPainterPath()
    path.setFillRule(Qt.WindingFill)   # the app takes each box out on its own: overlaps erase too
    for quad in quads:
        piece = QPainterPath()
        piece.addPolygon(QPolygonF([QPointF(x, y) for x, y in quad]))
        piece.closeSubpath()
        path = path.united(piece)
    return path


def _along_quads(cords, strand, region, grid, pad=0.3, step=6.0, reach_samples=None):
    """Quads along the strand's centre line, as wide as the strand, over the
    part of it that touches the region (and a little past it)."""
    name = strand.layer_name
    if name not in cords.where:
        return []
    _, pts, _arc = cords.where[name]
    rows, cols = region
    px = grid.x0 + (cols + 0.5) / grid.scale
    py = grid.y0 + (rows + 0.5) / grid.scale
    half = strand.width / 2.0 + strand.stroke_width + pad
    near = np.zeros(len(pts), dtype=bool)
    for lo in range(0, len(px), 4096):
        d = (px[lo:lo + 4096, None] - pts[None, :, 0]) ** 2 + (py[lo:lo + 4096, None] - pts[None, :, 1]) ** 2
        near |= d.min(axis=0) <= (half + 1.0) ** 2
    if not near.any():
        return []
    k = np.nonzero(near)[0]
    runs, start = [], k[0]
    for a, b in zip(k, k[1:]):
        if b != a + 1:
            runs.append((start, a))
            start = b
    runs.append((start, k[-1]))
    reach = reach_samples or max(1, int(math.ceil(half / SAMPLE)))
    quads = []
    for i, j in runs:
        # Past the region along the strand, so the box ends where the piece does.
        i, j = max(0, i - reach), min(len(pts) - 1, j + reach)
        idx, travelled = [i], 0.0
        for n in range(i + 1, j + 1):
            travelled += math.dist(pts[n - 1], pts[n])
            if travelled >= step or n == j:
                idx.append(n)
                travelled = 0.0
        for a, b in zip(idx, idx[1:]):
            p0, p1 = pts[a], pts[b]
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            length = math.hypot(dx, dy)
            if length < 1e-6:
                continue
            ux, uy = dx / length, dy / length
            # The chord strays from the curve between its ends: widen by that.
            sag = max((abs((q[0] - p0[0]) * uy - (q[1] - p0[1]) * ux) for q in pts[a:b + 1]), default=0.0)
            w = half + sag
            # Past the strand's own ends, reach over its round cap too.
            e0 = half if a == 0 else 0.6
            e1 = half if b == len(pts) - 1 else 0.6
            a0 = (p0[0] - ux * e0, p0[1] - uy * e0)
            a1 = (p1[0] + ux * e1, p1[1] + uy * e1)
            nx, ny = -uy * w, ux * w
            quads.append([(a0[0] + nx, a0[1] + ny), (a1[0] + nx, a1[1] + ny),
                          (a1[0] - nx, a1[1] - ny), (a0[0] - nx, a0[1] - ny)])
    return quads


def _square(grid, region, margin=1.0):
    x0, y0, x1, y1 = grid.rect(*region)
    x0, y0, x1, y1 = x0 - margin, y0 - margin, x1 + margin, y1 + margin
    return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]


def _split_quad(grid, region, stay_rows, stay_cols, margin=0.75):
    """A box turned to the angle that best splits the region off from the
    pixels that stay: its near side runs between the two, its other sides
    reach round the region. None when nothing stays nearby."""
    if not len(stay_rows):
        return None
    rows, cols = region
    rx, ry = grid.x0 + (cols + 0.5) / grid.scale, grid.y0 + (rows + 0.5) / grid.scale
    kx, ky = grid.x0 + (stay_cols + 0.5) / grid.scale, grid.y0 + (stay_rows + 0.5) / grid.scale
    best = None
    for degrees in range(0, 180, 6):
        a = math.radians(degrees)
        nx, ny = math.cos(a), math.sin(a)
        for sign in (1, -1):
            pr = (rx * nx + ry * ny) * sign
            pk = (kx * nx + ky * ny) * sign
            edge = float(np.min(pk)) - margin       # the side towards what stays
            cut = float(np.mean(pr > edge))           # of the region, left out
            if best is None or cut < best[0]:
                best = (cut, nx * sign, ny * sign, edge)
    cut, nx, ny, edge = best
    if cut > 0.25:
        return None
    tx, ty = -ny, nx
    pr = rx * nx + ry * ny
    pt = rx * tx + ry * ty
    lo, hi = float(pr.min()) - 2.0, edge
    t0, t1 = float(pt.min()) - 2.0, float(pt.max()) + 2.0
    if hi <= lo:
        return None
    corner = lambda u, v: (u * nx + v * tx, u * ny + v * ty)
    return [[corner(lo, t0), corner(lo, t1), corner(hi, t1), corner(hi, t0)]]


def _main(stay, area):
    """The parts of the piece that stay and matter: specks along a place's
    edge (its antialiased rim) do not."""
    out = np.zeros_like(stay)
    for r, c in _components(stay):
        if len(r) * area >= MIN_AREA:
            out[r, c] = True
    return out


def _bounds(quads):
    from PyQt5.QtCore import QRectF
    xs = [x for q in quads for x, _ in q]
    ys = [y for q in quads for _, y in q]
    return QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def best_erase(analysis, mask, region, keep, strands=(), strict=0.0):
    """The erase boxes that take the region (global pixels) out of the mask's
    piece and as little as possible of keep (a function: box -> the pixels of
    the piece that should go on painting there). Returns (quads, missed px²,
    harmed px²); quads is empty when nothing fits well enough: with strict,
    at most strict px² (or a tenth of the region) of keep may go."""
    scene, grid = analysis.scene, analysis.scene.grid
    path = scene.paths.get(id(mask))
    rows, cols = region
    if path is None or path.isEmpty() or not len(rows):
        return [], 0.0, 0.0
    tried = [_square(grid, region)]
    for strand in strands:
        quads = _along_quads(analysis.cords, strand, region, grid)
        if quads:
            tried.append(quads)
        short = _along_quads(analysis.cords, strand, region, grid, reach_samples=1)
        if short:
            tried.append(short)
    box = _of_pixels(rows, cols, grid)
    for quads in tried:
        box = box.union(grid.box(_bounds(quads), margin=SHADOW_REACH + 2))
    box = grid.clip(box)
    drawn = _filled(grid, box, path)
    want = np.zeros(box.shape, dtype=bool)
    want[rows - box.r0, cols - box.c0] = True
    want &= drawn
    if not want.any():
        return [], 0.0, 0.0
    stay = keep(box) & drawn & ~want
    area = scene.pixel_area()
    stay = _main(stay, area)
    sr, sc = np.nonzero(stay)
    split = _split_quad(grid, region, sr + box.r0, sc + box.c0)
    if split is not None:
        tried.append(split)
        grown = grid.clip(box.union(grid.box(_bounds(split), margin=SHADOW_REACH + 2)))
        if (grown.r0, grown.r1, grown.c0, grown.c1) != (box.r0, box.r1, box.c0, box.c1):
            # The turned box reaches further: measure everything over its box too.
            box = grown
            drawn = _filled(grid, box, path)
            want = np.zeros(box.shape, dtype=bool)
            want[rows - box.r0, cols - box.c0] = True
            want &= drawn
            stay = _main(keep(box) & drawn & ~want, area)
    edges, bodies = scene.edges_in(box), scene.bodies_in(box)
    shadow = max(2, int(round(SHADOW_REACH * grid.scale)))
    # Trimmed versions: only the quads that touch the place.
    for quads in list(tried[1:]):
        touching = [q for q in quads if (_filled(grid, box, _quad_path([q])) & want).any()]
        if touching and len(touching) < len(quads):
            tried.append(touching)
    best = None
    for n, quads in enumerate(tried):
        gone = _filled(grid, box, _quad_path(quads))
        missed = float((want & ~gone).sum()) * area
        harmed = float((stay & gone).sum()) * area
        if n == 0 and harmed > CLEAN:
            continue                # a plain box cutting into what stays shows its straight sides
        # A new edge of the piece shows as a cut unless it runs along a
        # strand's outline; so do the box's own edges near what stays, where
        # the piece's lift shadow ends with the box.
        stays = drawn & ~gone
        seam = _grow(gone, 1) & stays & ~edges
        seam |= gone & ~_shrink(gone, 1) & bodies & ~edges & _grow(stays, shadow)
        # On a tie, boxes that follow a strand win: their edges are its outline.
        score = (harmed * 2.0 + missed + float(seam.sum()) / grid.scale + 0.05 * len(quads)
                 + (2.0 if n == 0 else 0.0))
        if best is None or score < best[0]:
            best = (score, quads, missed, harmed)
    if best is None:
        return [], float(want.sum()) * area, 0.0
    _, quads, missed, harmed = best
    total = float(want.sum()) * area
    kept = float(stay.sum()) * area
    # What may go of the piece that should stay: a little of it, never all
    # of a small part that is there for a reason, never more than half as
    # much as the place itself.
    limit = (min(max(strict, 0.1 * total), max(strict, 0.25 * kept)) if strict
             else max(MIN_AREA, min(0.25 * kept, 0.5 * total)))
    if missed > max(MIN_AREA, 0.25 * total) or harmed > limit:
        return [], missed, harmed
    return [[(round(x, 2), round(y, 2)) for x, y in q] for q in quads], missed, harmed


def _keep_for(analysis, mask):
    """A keep function for best_erase: the mask's pixels that are right as
    they are, where it shows, minus every place a problem names for it."""
    scene = analysis.scene
    ident = scene.ids.get(id(mask))
    places = [p['region'] for p in analysis.problems() if p.get('mask') == mask.layer_name and 'region' in p]

    rim = max(1, int(round(2.0 * scene.grid.scale)))

    def keep(box):
        mine = scene.top[box.slice] == ident if ident is not None else np.zeros(box.shape, dtype=bool)
        named = np.zeros(box.shape, dtype=bool)
        for rows, cols in places:
            k = box.contains(rows, cols)
            named[rows[k] - box.r0, cols[k] - box.c0] = True
        # A place's thin rim (left out of it as antialiasing) goes with it.
        return mine & ~_grow(named, rim) if named.any() else mine
    return keep


# ------------------------------------------------------------------- edits
def corner_box(box):
    """An erase box as Edit Mask stores it, by its four corners: from
    [x0, y0, x1, y1] or from four [x, y] corners in order round it."""
    if not isinstance(box, (list, tuple)):
        raise MaskError('an erase box is [x0, y0, x1, y1] or four [x, y] corners')
    if len(box) == 4 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in box):
        x0, x1 = sorted((float(box[0]), float(box[2])))
        y0, y1 = sorted((float(box[1]), float(box[3])))
        if not (x1 - x0 > 0.1 and y1 - y0 > 0.1):
            raise MaskError('an erase box needs a width and a height: [x0, y0, x1, y1]')
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    else:
        try:
            corners = [(float(p[0]), float(p[1])) for p in box]
        except (TypeError, ValueError, IndexError):
            corners = []
        if len(corners) != 4 or not all(math.isfinite(v) for p in corners for v in p):
            raise MaskError('an erase box is [x0, y0, x1, y1] or four [x, y] corners')
    if not all(math.isfinite(v) for p in corners for v in p):
        raise MaskError('an erase box needs finite numbers')
    return {name: corners[k] for k, name in enumerate(CORNERS)}


def erase(design, mask, boxes):
    """Add erase boxes to a mask, as Edit Mask does when a box is dragged:
    stored by corners, the mask's path rebuilt without them."""
    made = [corner_box(b) for b in boxes]
    if not made:
        raise MaskError('no erase box given')
    mask.deletion_rectangles.extend(made)
    mask.set_custom_mask(mask.get_mask_path())
    return made


def reset(design, mask):
    """Reset Mask: back to the whole crossing, every erase box gone."""
    mask.reset_mask()


def delete(design, mask):
    """Delete the masked layer."""
    design.strands.remove(mask)


def create(design, first, second):
    """A mask with first on top of second, as canvas.create_masked_layer
    makes it: only for two strands that overlap, added above the others."""
    from PyQt5.QtGui import QColor
    from masked_strand import MaskedStrand
    if first is second:
        raise MaskError('a mask needs two different strands')
    existing = design.find_mask(first.layer_name, second.layer_name)
    if existing is not None:
        raise MaskError(f'{first.layer_name} and {second.layer_name} already have mask {existing.layer_name}; '
                        'swap it or delete it first')
    mask = MaskedStrand(first, second)
    if mask.get_stroked_path_for_strand(first).intersected(mask.get_stroked_path_for_strand(second)).isEmpty():
        raise MaskError(f'{first.layer_name} and {second.layer_name} do not overlap: there is nothing to mask')
    mask.shadow_color = QColor(0, 0, 0, 150)
    mask.canvas = design.canvas
    for key, value in design.curve.items():
        setattr(mask, key, value)
    design.strands.append(mask)
    return mask


def swap(design, mask):
    """The other strand on top: delete the mask and create it reversed."""
    first, second = mask.first_selected_strand, mask.second_selected_strand
    delete(design, mask)
    return create(design, second, first)


def edit(data, op, mask=None, first=None, second=None, box=None, covers=None, around=None, at=None,
         trim=True):
    """One mask edit, done with the app's own code on a copy of the design.
    Returns (new data, what was done); data is left as it is.

    erase takes one of: at [x, y] (the place a problem of this mask was
    listed at: just that place is erased), covers (a strand: the mask is
    erased where it paints over it), around [x, y] (the mask's whole piece at
    that crossing), box ([x0, y0, x1, y1] or four corners). create and swap
    make a mask that covers every overlap of its two strands; with trim it is
    erased at once wherever the check then finds it painting the wrong way."""
    if op not in OPS:
        raise MaskError(f'op is one of {", ".join(OPS)}')
    if op == 'create':
        if not first or not second:
            raise MaskError('create needs first (the strand on top) and second (the one under)')
        design = Design(data)
        made = create(design, design.strand(first), design.strand(second))
        return _trimmed(design.data(), made.layer_name, f'made mask {made.layer_name}: {first} over {second}',
                        trim)
    if not mask:
        raise MaskError(f'{op} needs the mask name (check_masks lists them)')
    if op == 'erase':
        if sum(x is not None for x in (box, covers, around, at)) != 1:
            raise MaskError('erase needs one of at [x, y] (a problem check_masks listed), covers (a strand), '
                            'around [x, y] (a crossing) or box [x0, y0, x1, y1]')
        if box is not None:
            design = Design(data)
            target = design.mask(mask)
            quads = [[corner_box(box)[c] for c in CORNERS]]
        else:
            analysis = Analysis(data)
            design = analysis.design
            target = design.mask(mask)
            if covers is not None:
                quads = covers_quads(analysis, target, design.strand(covers))
            elif at is not None:
                quads = at_quads(analysis, target, at)
            else:
                quads = around_quads(analysis, target, around)
        erase(design, target, quads)
        return design.data(), f'erased mask {mask} with {len(quads)} box{"es" if len(quads) != 1 else ""}'
    design = Design(data)
    target = design.mask(mask)
    if op == 'reset':
        count = len(target.deletion_rectangles)
        reset(design, target)
        return design.data(), f'reset mask {mask}: {count} erase box{"es" if count != 1 else ""} removed'
    if op == 'delete':
        delete(design, target)
        return design.data(), f'deleted mask {mask}'
    count = len(target.deletion_rectangles)
    made = swap(design, target)
    lost = f'; its {count} erase boxes went with it' if count else ''
    return _trimmed(design.data(), made.layer_name, f'swapped mask {mask}: now {made.layer_name}, '
                    f'{made.first_selected_strand.layer_name} on top{lost}', trim)


def _trimmed(data, name, done, trim):
    """A new mask, erased where it paints the wrong way, when trim is on."""
    if not trim:
        return data, done
    trimmed = _trim(data, name)
    if trimmed is None:
        return data, done
    data, boxes = trimmed
    return data, done + f'; erased it with {boxes} box{"es" if boxes != 1 else ""} where it would paint the wrong way'


def at_quads(analysis, mask, at):
    """Erase boxes for the place a problem of this mask was found at."""
    try:
        x, y = (float(v) for v in at)
    except (TypeError, ValueError):
        raise MaskError('at is [x, y], where check_masks listed the problem') from None
    found = [p for p in analysis.problems() if p.get('mask') == mask.layer_name and 'region' in p]
    if not found:
        raise MaskError(f'check_masks finds no problem of mask {mask.layer_name}; give covers, around or a box')
    grid = analysis.scene.grid
    px, py = grid.pixel(x, y)
    distance = lambda p: float(np.min(np.hypot(p['region'][1] - px, p['region'][0] - py))) / grid.scale
    p = min(found, key=distance)
    if distance(p) > 12:
        places = '; '.join(f"({q['at'][0]:.0f}, {q['at'][1]:.0f})" for q in found)
        raise MaskError(f'mask {mask.layer_name} has no problem at ({x:.0f}, {y:.0f}); its problems are at {places}')
    design = analysis.design
    strands = [design.strand(n) for n in (p.get('strand'), p.get('should_show')) if n and n in design.names()]
    strands += [mask.first_selected_strand, mask.second_selected_strand]
    quads, _, _ = best_erase(analysis, mask, p['region'], _keep_for(analysis, mask), strands=strands)
    if not quads:
        raise MaskError(f'no erase box takes mask {mask.layer_name} off the place at ({x:.0f}, {y:.0f}) without '
                        'cutting into the rest of its piece; give a box yourself')
    return quads


def covers_quads(analysis, mask, strand):
    """Erase boxes for where the mask paints over the strand."""
    scene = analysis.scene
    places = [p['region'] for p in analysis.problems() if p['kind'] == 'covers_strand'
              and p['mask'] == mask.layer_name and p['strand'] == strand.layer_name]
    if places:
        rows = np.concatenate([r for r, _ in places])
        cols = np.concatenate([c for _, c in places])
    else:                       # not a problem the check found: all of the overlap
        path = scene.paths.get(id(mask))
        if path is None or path.isEmpty():
            raise MaskError(f'mask {mask.layer_name} paints nothing')
        box = scene.box_of(mask)
        region = _filled(scene.grid, box, path) & scene.cover_in(strand, box)
        rows, cols = np.nonzero(region)
        rows, cols = rows + box.r0, cols + box.c0
    if len(rows) * scene.pixel_area() < 0.5:
        raise MaskError(f'mask {mask.layer_name} does not cover strand {strand.layer_name}')
    base = _keep_for(analysis, mask)

    def keep(box):
        out = base(box)
        k = box.contains(rows, cols)
        out[rows[k] - box.r0, cols[k] - box.c0] = False
        return out
    quads, _, _ = best_erase(analysis, mask, (rows, cols), keep,
                             strands=(strand, mask.first_selected_strand, mask.second_selected_strand))
    if not quads:
        raise MaskError(f'no erase box takes mask {mask.layer_name} off {strand.layer_name} without cutting '
                        'into the rest of the piece; give a box yourself')
    return quads


def around_quads(analysis, mask, around):
    """Erase boxes for the mask's piece at the crossing nearest (x, y)."""
    try:
        x, y = (float(v) for v in around)
    except (TypeError, ValueError):
        raise MaskError('around is [x, y], the crossing to erase') from None
    pieces = analysis.pieces(mask, erased=True)
    if not pieces:
        raise MaskError(f'mask {mask.layer_name} paints nothing')
    grid = analysis.scene.grid
    px, py = grid.pixel(x, y)
    distance = lambda p: float(np.min(np.hypot(p[1] - px, p[0] - py))) / grid.scale
    best = min(pieces, key=distance)
    if distance(best) > 40:
        raise MaskError(f'mask {mask.layer_name} has no piece near ({x:.0f}, {y:.0f})')
    others = [p for p in pieces if p is not best]
    if others:
        def keep(box):
            out = np.zeros(box.shape, dtype=bool)
            for rows, cols in others:
                k = box.contains(rows, cols)
                out[rows[k] - box.r0, cols[k] - box.c0] = True
            return out
        region = best
    else:
        # One piece over several crossings: erase the part nearest the point.
        region, keep = _near_crossing(analysis, mask, best, (x, y))
    quads, _, _ = best_erase(analysis, mask, region, keep,
                             strands=(mask.first_selected_strand, mask.second_selected_strand))
    if not quads:
        raise MaskError(f'no erase box takes out the piece of {mask.layer_name} near ({x:.0f}, {y:.0f}) alone; '
                        'give a box yourself')
    return quads


def _near_crossing(analysis, mask, piece, point):
    """For a piece over more than one crossing: the part of it nearest the
    point, and a keep function for the rest."""
    a, b = mask.first_selected_strand.layer_name, mask.second_selected_strand.layer_name
    own = [c for c in analysis.crossings
           if {a, b} & set(analysis.part(c, 0)[1]) and {a, b} & set(analysis.part(c, 1)[1])]
    rows, cols = piece
    if len(own) < 2:
        return piece, lambda box: np.zeros(box.shape, dtype=bool)
    grid = analysis.scene.grid
    xs = grid.x0 + (cols + 0.5) / grid.scale
    ys = grid.y0 + (rows + 0.5) / grid.scale
    target = min(own, key=lambda c: math.dist(c.point, point))
    d_target = np.hypot(xs - target.point[0], ys - target.point[1])
    d_other = np.min([np.hypot(xs - c.point[0], ys - c.point[1]) for c in own if c is not target], axis=0)
    mine = d_other >= d_target
    kr, kc = rows[~mine], cols[~mine]

    def keep(box):
        out = np.zeros(box.shape, dtype=bool)
        k = box.contains(kr, kc)
        out[kr[k] - box.r0, kc[k] - box.c0] = True
        return out
    return (rows[mine], cols[mine]), keep


# ------------------------------------------------------------------ repair
def repair(data, create_masks=False, rounds=ROUNDS):
    """Fix what is safe, pass after pass until nothing changes:
    - erase a mask where it hides a strand that should show, or where,
      without it, the part that should be on top shows; only when the erase
      takes (almost) nothing else and leaves no cut edge (CLEAN);
    - with create_masks, where a crossing's strands have no mask and the
      design (its stored crossings) says which goes over: make that mask,
      and erase it at once wherever else it would paint the wrong way.
    Every edit is kept only when the next check is better. Returns
    (data, done: [text], left: [problem]); data is a new design."""
    done = []
    tried = set()
    analysis = Analysis(data)
    problems = analysis.problems()
    for _ in range(rounds):
        if not problems:
            break
        score = _badness(problems)
        progress = False
        for p in problems:
            fix = p.get('fix') or {}
            key = (p['kind'], fix.get('op'), fix.get('mask'), fix.get('first'), fix.get('second'),
                   tuple(round(v / 4) for v in p['at']))
            if key in tried or fix.get('op') not in ('erase', 'create'):
                continue
            if fix['op'] == 'create' and not (create_masks and p.get('source') == 'design'):
                continue
            tried.add(key)
            attempt = _apply(analysis, p, fix)
            if attempt is None:
                continue
            new_data, text = attempt
            new = Analysis(new_data)
            if _badness(new.problems()) < score - 1e-6:
                data, analysis, problems = new_data, new, new.problems()
                done.append(text)
                progress = True
                break
        if not progress:
            break
    return (data if done else copy.deepcopy(data)), done, _plain(problems)


def _badness(problems):
    return sum(p['area'] for p in problems)


def _apply(analysis, p, fix):
    """One fix on a fresh copy of the design: (data, what was done) or None."""
    design = analysis.design
    if fix['op'] == 'erase':
        mask = design.mask(fix['mask'])
        strands = [design.strand(n) for n in (p.get('strand'), p.get('should_show'))
                   if n and n in design.names()]
        strands += [mask.first_selected_strand, mask.second_selected_strand]
        quads, _, _ = best_erase(analysis, mask, fix['region'], _keep_for(analysis, mask),
                                 strands=strands, strict=CLEAN)
        if not quads:
            return None
        fresh = Design(design.data())
        erase(fresh, fresh.mask(fix['mask']), quads)
        what = {'covers_strand': f"where it hid {p.get('strand')}",
                'two_crossings': 'at its other crossing'}.get(p['kind'], f"where {p.get('should_show')} belongs on top")
        return fresh.data(), (f"erased mask {fix['mask']} at ({p['at'][0]:.0f}, {p['at'][1]:.0f}) {what} "
                              f"({len(quads)} box{'es' if len(quads) != 1 else ''}, {p['area']:.0f} px²)")
    first, second = fix['first'], fix['second']
    fresh = Design(design.data())
    try:
        made = create(fresh, fresh.strand(first), fresh.strand(second))
    except MaskError:
        return None
    text = (f"made mask {made.layer_name} ({first} over {second}) for the crossing at "
            f"({p['crossing'][0]:.0f}, {p['crossing'][1]:.0f})")
    data = fresh.data()
    trimmed = _trim(data, made.layer_name)
    if trimmed is not None:
        data, boxes = trimmed
        text += f', erased where {second} belongs on top ({boxes} box{"es" if boxes != 1 else ""})'
    return data, text


def _trim(data, name):
    """Erase a new mask wherever the check finds it painting the wrong way."""
    analysis = Analysis(data)
    mask = analysis.design.mask(name)
    wrong = [p for p in analysis.problems() if p.get('mask') == name and (p.get('fix') or {}).get('op') == 'erase']
    if not wrong:
        return None
    rows = np.concatenate([p['fix']['region'][0] for p in wrong])
    cols = np.concatenate([p['fix']['region'][1] for p in wrong])
    quads, _, _ = best_erase(analysis, mask, (rows, cols), _keep_for(analysis, mask),
                             strands=[mask.first_selected_strand, mask.second_selected_strand])
    if not quads:
        return None
    erase(analysis.design, mask, quads)
    return analysis.design.data(), len(quads)

"""A cord that behaves like a real one, for knots pulled tight.

The cord is a tube of fixed thickness lying on a table. Pulling its two ends
draws it along the shortest path its thickness allows: loose loops shrink,
and the knot closes until the cord jams against itself. That is the tight,
"stretched" knot, with no air between the parts that touch.

The pull is modelled as curve shortening: every point moves toward the middle
of its neighbours, which is what tension does to a curved cord. The cord is
resampled as it gets shorter. The held ends stay put, so the tails end up
straight.

The knot never changes on the way:

- Where two parts cross in the picture, the over part is lifted a full width
  above the under part. Which one is on top comes from the knot's crossing
  code (the order of overs and unders along the cord), never from the
  current heights, so a crossing cannot flip.
- Close to a crossing the two parts are seen in 3D, so the over part can rise
  over the under part.
- Everywhere else, parts keep a width apart in the picture. They lie side by
  side on the table, never on top of each other, so no new crossing can
  appear and the drawing stays readable.
- After every step the crossing code is compared with the knot's. If a step
  went wrong, the cord goes back to the last good state and moves in smaller
  steps.

Positions are (x, y, height): x and y as on the canvas, height above the
table. Where two parts cross in the picture, the higher one is on top.

    from openstrand import simulate
    cords, info = simulate.tighten([points], width=26, pulls=[(0, 0, (-1, 0)), (0, 1, (1, 0))])
"""
import math

import numpy as np

MIN_BEND = 0.5          # tightest bend: centreline radius in cord widths
SPACING = 1 / 3         # points along the cord, in cord widths
LEVEL = 0.55            # height of an over-pass above the table, in widths (for drawn heights)
HUMP = 1.5              # along each part, how far from a crossing the parts are seen in 3D (widths)
GRAVITY = 0.03          # how far an unsupported part sinks per step (widths)


class SimulationError(ValueError):
    pass


def resample(points, spacing, closed=False):
    """The polyline resampled every spacing (measured in the picture), every
    column (height too) interpolated."""
    p = np.asarray(points, dtype=float)
    if closed:
        p = np.vstack([p, p[:1]])
    step = np.hypot(*(p[1:, :2] - p[:-1, :2]).T)
    keep = np.concatenate([[True], step > 1e-9])
    p, s = p[keep], np.concatenate([[0.0], np.cumsum(step[step > 1e-9])])
    total = s[-1]
    if total <= 0:
        raise SimulationError('the cord has no length')
    n = max(2, int(round(total / spacing)) + (0 if closed else 1))
    targets = np.linspace(0, total, n, endpoint=not closed)
    return np.column_stack([np.interp(targets, s, p[:, k]) for k in range(p.shape[1])])


def length(points, closed=False):
    p = np.asarray(points, dtype=float)
    if closed:
        p = np.vstack([p, p[:1]])
    return float(np.hypot(*(p[1:, :2] - p[:-1, :2]).T).sum())


def heights_from_pattern(poly, pattern, width, closed=False):
    """Heights for a drawn cord so its crossings go over (O) and under (U) in
    the order given, walking the cord from its start.

    Every crossing is passed twice; pattern has one letter per pass, and the
    two passes of a crossing must differ. Returns (heights in px, visits).
    """
    from .invariants import crossings
    poly = np.asarray(poly, dtype=float)[:, :2]
    found = [c for c in crossings([poly], [closed]) if c['cords'] == (0, 0)]
    visits = sorted((s, k) for k, c in enumerate(found) for s in c['positions'])
    pattern = [ch for ch in str(pattern).upper() if ch in 'OU']
    if len(pattern) != len(visits):
        raise SimulationError(f'the cord passes {len(visits)} crossings ({len(found)} crossings, each '
                              f'twice) but the pattern has {len(pattern)} letters')
    given = {}
    for (s, k), ch in zip(visits, pattern):
        given.setdefault(k, []).append(ch)
    for k, letters in given.items():
        if sorted(letters) != ['O', 'U']:
            x, y = found[k]['point']
            raise SimulationError(f'the crossing at ({x:.0f}, {y:.0f}) is passed {"".join(letters)}: '
                                  'one pass must go over (O) and the other under (U)')
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(poly, axis=0).T))])
    z = profile(s, [v[0] for v in visits], [LEVEL if ch == 'O' else -LEVEL for ch in pattern], width)
    return z * width, [dict(position=v[0], crossing=v[1], over=ch == 'O', point=found[v[1]]['point'])
                       for v, ch in zip(visits, pattern)]


def profile(s, at, levels, width):
    """A smooth height along the cord through the given levels (in widths),
    back to the table before the first and after the last."""
    z = np.zeros(len(s))
    if not len(at):
        return z
    reach = 2.5 * width
    xs = [at[0] - reach] + list(at) + [at[-1] + reach]
    zs = [0.0] + list(levels) + [0.0]
    for a in range(len(xs) - 1):
        inside = (s >= xs[a]) & (s <= xs[a + 1])
        if not inside.any():
            continue
        u = (s[inside] - xs[a]) / max(xs[a + 1] - xs[a], 1e-9)
        u = u * u * (3 - 2 * u)
        z[inside] = zs[a] + (zs[a + 1] - zs[a]) * u
    return z


def _intersect(P, A, B, i, j):
    """Which segment pairs (i, j) cross in the picture, and where along each (t, u)."""
    p, r = P[A[i], :2], P[B[i], :2] - P[A[i], :2]
    q, d = P[A[j], :2], P[B[j], :2] - P[A[j], :2]
    denom = r[:, 0] * d[:, 1] - r[:, 1] * d[:, 0]
    qp = q - p
    with np.errstate(divide='ignore', invalid='ignore'):
        t = (qp[:, 0] * d[:, 1] - qp[:, 1] * d[:, 0]) / denom
        u = (qp[:, 0] * r[:, 1] - qp[:, 1] * r[:, 0]) / denom
    hit = (np.abs(denom) > 1e-12) & (t >= 0) & (t < 1) & (u >= 0) & (u < 1)
    return hit, np.where(hit, t, 0.0), np.where(hit, u, 0.0)


class Rope:
    """Cords as one set of points, with the rules between them.

    reference: the knot's crossing code, per cord the crossings it passes in
    order as (crossing number, over); read from the heights when not given.
    """

    def __init__(self, cords, width, closed=None, spacing=None, pins=None, reference=None):
        self.width = float(width)
        self.h = float(spacing or self.width * SPACING)
        self.closed = list(closed) if closed is not None else [False] * len(cords)
        self.pins = dict(pins or {})          # (cord, end) -> position
        parts, self.ranges, start = [], [], 0
        for c, cord in enumerate(cords):
            p = np.asarray(cord, dtype=float)
            if p.shape[1] == 2:
                p = np.hstack([p, np.zeros((len(p), 1))])
            p = resample(p, self.h, self.closed[c])
            parts.append(p)
            self.ranges.append((start, start + len(p)))
            start += len(p)
        self.P = np.vstack(parts)
        seg_a, seg_b, seg_c, seg_k, tri = [], [], [], [], []
        self.seg_ranges, first = [], 0
        for c, (lo, hi) in enumerate(self.ranges):
            n = hi - lo
            idx = np.arange(lo, hi)
            a, b = idx[:-1], idx[1:]
            if self.closed[c]:
                a, b = np.append(a, hi - 1), np.append(b, lo)
            seg_a.append(a)
            seg_b.append(b)
            seg_c.append(np.full(len(a), c))
            seg_k.append(np.arange(len(a)))
            self.seg_ranges.append((first, first + len(a)))
            first += len(a)
            for k in range(n if self.closed[c] else n - 2):
                tri.append((lo + k, lo + (k + 1) % n, lo + (k + 2) % n))
        self.A, self.B = np.concatenate(seg_a), np.concatenate(seg_b)
        self.seg_cord, self.seg_local = np.concatenate(seg_c), np.concatenate(seg_k)
        self.seg_count = np.array([hi - lo for lo, hi in self.seg_ranges])
        self.tri = np.array(tri, dtype=int).reshape(-1, 3)
        self.free = np.ones(len(self.P), dtype=bool)
        for (c, end) in self.pins:
            self.free[self.end_index(c, end)] = False
        self.inv = self.free.astype(float)    # how easily each point moves (0: held)
        self.rest = self.segment_lengths()    # the cord cannot stretch beyond these
        self._pairs = None
        self._plan = None
        self.reference = reference if reference is not None else self.read_code()

    @property
    def window(self):
        """Segments either side of a crossing where its two parts are seen in 3D."""
        return max(2, int(math.ceil(HUMP * self.width / self.h)))

    # ---------------------------------------------------------------- views
    def cords(self):
        return [self.P[lo:hi].copy() for lo, hi in self.ranges]

    def end_index(self, cord, end):
        lo, hi = self.ranges[cord]
        return lo if end == 0 else hi - 1

    def length(self):
        return sum(length(self.P[lo:hi], self.closed[c]) for c, (lo, hi) in enumerate(self.ranges))

    def resampled(self):
        """The same cords with evenly spaced points again (they bunch as the cord shortens)."""
        return Rope(self.cords(), self.width, self.closed, self.h, self.pins, self.reference)

    # ------------------------------------------------------ crossing code
    def _crossings(self):
        """Segment pairs that cross in the picture: (i, j, t, u)."""
        if self._pairs is None:
            self.find_pairs()
        i, j = self._pairs
        hit, t, u = _intersect(self.P, self.A, self.B, i, j)
        return i[hit], j[hit], t[hit], u[hit]

    def _passes(self, i, j, t, u):
        """Per cord, its crossing passes in order: (position, crossing, side)."""
        P = self.P
        seglen = np.hypot(*(P[self.B, :2] - P[self.A, :2]).T)
        s0 = np.zeros(len(seglen))
        for lo, hi in self.seg_ranges:
            s0[lo:hi] = np.concatenate([[0.0], np.cumsum(seglen[lo:hi])[:-1]])
        sa, sb = s0[i] + t * seglen[i], s0[j] + u * seglen[j]
        per = [[] for _ in self.ranges]
        for k in range(len(i)):
            per[self.seg_cord[i[k]]].append((sa[k], k, 0))
            per[self.seg_cord[j[k]]].append((sb[k], k, 1))
        for p in per:
            p.sort()
        return per

    def read_code(self):
        """The crossing code of the cords as they are, over and under read from the heights."""
        i, j, t, u = self._crossings()
        P = self.P
        za = P[self.A[i], 2] + t * (P[self.B[i], 2] - P[self.A[i], 2])
        zb = P[self.A[j], 2] + u * (P[self.B[j], 2] - P[self.A[j], 2])
        if np.any(np.abs(za - zb) < 1e-6 * self.width):
            raise SimulationError('two parts cross at the same height: give the over part more height')
        number, code = {}, []
        for passes in self._passes(i, j, t, u):
            row = []
            for _, k, side in passes:
                over = (za[k] > zb[k]) == (side == 0)
                row.append((number.setdefault(k, len(number)), bool(over)))
            code.append(row)
        return code

    def _align(self, per):
        """The current crossings matched to the knot's code: for each current
        crossing, the side that goes over (0 or 1). None when they no longer
        match: the cord passed through itself or a crossing slipped."""
        ref = self.reference
        if [len(p) for p in per] != [len(r) for r in ref]:
            return None
        to_ref, from_ref, over = {}, {}, {}
        for c, (cur, row) in enumerate(zip(per, ref)):
            n = len(cur)
            shifts = range(n) if (self.closed[c] and n) else [0]
            for shift in shifts:
                a, b, o, ok = dict(to_ref), dict(from_ref), dict(over), True
                for idx in range(n):
                    _, k, side = cur[(idx + shift) % n]
                    rid, is_over = row[idx]
                    if a.setdefault(k, rid) != rid or b.setdefault(rid, k) != k:
                        ok = False
                        break
                    if is_over:
                        if o.setdefault(k, side) != side:
                            ok = False
                            break
                if ok:
                    to_ref, from_ref, over = a, b, o
                    break
            else:
                return None
        if len(over) != len(to_ref):
            return None
        return over

    def code_matches(self):
        i, j, t, u = self._crossings()
        return self._align(self._passes(i, j, t, u)) is not None

    def segment_lengths(self):
        return np.linalg.norm(self.P[self.B] - self.P[self.A], axis=1)

    def strain(self):
        """How much longer the cord is than it may be (0.01: one percent)."""
        return float(self.segment_lengths().sum() / self.rest.sum() - 1)

    # ---------------------------------------------------------- the rules
    def stretch(self, limit=0.1):
        """The cord cannot stretch: every piece back to its rest length, solved
        for each cord at once (one Newton step on its chain of lengths), so a
        pull at one end is felt all the way along, as tension is."""
        P, cap = self.P, limit * self.width
        for c, (lo, hi) in enumerate(self.ranges):
            if self.closed[c] or hi - lo < 2:
                continue
            s0, s1 = self.seg_ranges[c]
            x = P[lo:hi]
            d = x[1:] - x[:-1]
            L = np.linalg.norm(d, axis=1) + 1e-12
            u = d / L[:, None]
            C = L - self.rest[s0:s1]
            w = self.inv[lo:hi]
            diag = w[:-1] + w[1:]
            off = -w[1:-1] * (u[:-1] * u[1:]).sum(1)
            lam = _tridiagonal(off, diag + 1e-9, off, -C)
            move = np.zeros_like(x)
            move[1:] += (w[1:] * lam)[:, None] * u
            move[:-1] -= (w[:-1] * lam)[:, None] * u
            size = np.linalg.norm(move, axis=1)
            big = size > cap
            move[big] *= (cap / size[big])[:, None]
            P[lo:hi] = x + move

    def shorten(self, k=0.3):
        """Tension: every point moves toward the middle of its neighbours,
        which shrinks loops and straightens tails (curve shortening)."""
        if not len(self.tri):
            return
        P = self.P
        a, b, c = self.tri.T
        move = np.zeros_like(P)
        move[b] = ((P[a] + P[c]) / 2 - P[b]) * k
        move[~self.free] = 0
        P += move

    def smooth(self, passes=2):
        """Stiffness: wobbles where contacts pushed single points are evened
        out along the cord, without shrinking it (Taubin smoothing)."""
        for _ in range(passes):
            self.shorten(0.5)
            self.shorten(-0.53)

    def shorten_implicit(self, lam=6.0, limit=0.15):
        """Tension, solved for the whole cord at once: (1 + lam L) x = x_old
        with the held ends fixed, so long tails straighten in a few steps
        instead of thousands. No point moves more than limit widths a step,
        so nothing can jump through another part."""
        P = self.P
        cap = limit * self.width
        for c, (lo, hi) in enumerate(self.ranges):
            if self.closed[c] or hi - lo < 3:
                continue
            old = P[lo:hi].copy()
            fixed = ~self.free[lo:hi]
            move = _smooth_chain(old, fixed, lam) - old
            size = np.linalg.norm(move, axis=1)
            big = size > cap
            move[big] *= (cap / size[big])[:, None]
            move[fixed] = 0
            P[lo:hi] = old + move

    def settle(self, g=GRAVITY):
        """Gravity: parts that nothing holds up sink back to the table."""
        z = self.P[:, 2]
        z[self.free] -= g * self.width
        np.maximum(z, 0.0, out=z)

    def bend(self):
        """No bend tighter than the cord's thickness allows (in the picture)."""
        if not len(self.tri):
            return
        P = self.P
        a, c = self.tri[:, 0], self.tri[:, 2]
        alpha = min(self.h / (MIN_BEND * self.width), math.pi * 0.9)
        need = 2 * self.h * math.cos(alpha / 2) * 0.98
        d = P[c, :2] - P[a, :2]
        L = np.linalg.norm(d, axis=1) + 1e-12
        short = L < need
        if not short.any():
            return
        a, c, d, L = a[short], c[short], d[short], L[short]
        corr = ((need - L) / L * 0.25)[:, None] * d
        acc = np.zeros((len(P), 2))
        np.add.at(acc, a, -corr)
        np.add.at(acc, c, corr)
        acc[~self.free] = 0
        P[:, :2] += acc

    def _gap(self, x, y):
        """Segments apart along their cord (around it when closed); a large
        number for segments of different cords. Broadcasts."""
        same = self.seg_cord[x] == self.seg_cord[y]
        g = np.abs(self.seg_local[x] - self.seg_local[y])
        count = self.seg_count[self.seg_cord[x]]
        ring = np.array(self.closed)[self.seg_cord[x]]
        g = np.where(ring, np.minimum(g, count - g), g)
        return np.where(same, g, 1 << 30)

    def find_pairs(self):
        """Pieces of cord close enough to touch soon, other than near neighbours."""
        P = self.P
        mid = (P[self.A, :2] + P[self.B, :2]) / 2
        reach = 1.6 * self.width + 2 * self.h
        diff = mid[:, None, :] - mid[None, :, :]
        near = (diff ** 2).sum(-1) < reach * reach
        i, j = np.nonzero(np.triu(near, 1))
        skip = int(math.ceil(math.pi * MIN_BEND * self.width / self.h)) + 1
        keep = self._gap(i, j) > skip
        self._pairs = (i[keep], j[keep])
        self._plan = None

    def plan_contacts(self):
        """Sort the close pairs into crossings, parts near a crossing, and the
        rest, with which side is on top. False when the crossings no longer
        match the knot's code."""
        if self._pairs is None:
            self.find_pairs()
        i, j = self._pairs
        hit, t, u = _intersect(self.P, self.A, self.B, i, j)
        ci, cj = i[hit], j[hit]
        over = self._align(self._passes(ci, cj, t[hit], u[hit]))
        if over is None:
            return False
        c_over = np.array([over[k] == 0 for k in range(len(ci))], dtype=bool)  # True: segment ci on top
        ni, nj = i[~hit], j[~hit]
        near = np.zeros(len(ni), dtype=bool)
        n_over = np.zeros(len(ni), dtype=bool)
        if len(ci) and len(ni):
            W = self.window
            direct = np.maximum(self._gap(ni[:, None], ci[None, :]), self._gap(nj[:, None], cj[None, :]))
            swapped = np.maximum(self._gap(ni[:, None], cj[None, :]), self._gap(nj[:, None], ci[None, :]))
            best_d, best_s = direct.min(1), swapped.min(1)
            use_d = best_d <= best_s
            k_d, k_s = direct.argmin(1), swapped.argmin(1)
            near = np.minimum(best_d, best_s) <= W
            n_over = np.where(use_d, c_over[k_d], ~c_over[k_s])
        self._plan = dict(ci=ci, cj=cj, c_over=c_over,
                          ni=ni[near], nj=nj[near], n_over=n_over[near],
                          oi=ni[~near], oj=nj[~near])
        return True

    def collide(self):
        """The cord cannot pass through itself. Returns the deepest overlap (px)."""
        if self._plan is None and not self.plan_contacts():
            raise SimulationError('the crossings no longer match the knot')
        plan, P, w, A, B = self._plan, self.P, self.width, self.A, self.B
        parts = []                       # (i, j, s, t, normal, depth)

        # Crossings: the over part a width above the under part.
        ci, cj, c_over = plan['ci'], plan['cj'], plan['c_over']
        if len(ci):
            _, t, u = _intersect(P, A, B, ci, cj)
            za = P[A[ci], 2] + t * (P[B[ci], 2] - P[A[ci], 2])
            zb = P[A[cj], 2] + u * (P[B[cj], 2] - P[A[cj], 2])
            sign = np.where(c_over, 1.0, -1.0)
            depth = w - sign * (za - zb)
            deep = depth > 0
            if deep.any():
                normal = np.zeros((int(deep.sum()), 3))
                normal[:, 2] = sign[deep]
                parts.append((ci[deep], cj[deep], t[deep], u[deep], normal, depth[deep]))

        # Near a crossing: in 3D, the over side kept on top.
        ni, nj, n_over = plan['ni'], plan['nj'], plan['n_over']
        if len(ni):
            s, t, c1, c2 = _closest(P[A[ni]], P[B[ni]], P[A[nj]], P[B[nj]])
            diff = c1 - c2
            sign = np.where(n_over, 1.0, -1.0)
            diff[:, 2] = sign * np.abs(diff[:, 2])
            dist = np.sqrt((diff * diff).sum(1))
            deep = dist < w
            if deep.any():
                d, dd = diff[deep], dist[deep]
                normal = d / np.maximum(dd, 1e-9)[:, None]
                tiny = dd <= 1e-9
                normal[tiny] = 0.0
                normal[tiny, 2] = sign[deep][tiny]
                parts.append((ni[deep], nj[deep], s[deep], t[deep], normal, w - dd))

        # Everywhere else: a width apart in the picture, side by side.
        oi, oj = plan['oi'], plan['oj']
        if len(oi):
            p1, q1 = P[A[oi], :2], P[B[oi], :2]
            s, t, c1, c2 = _closest(p1, q1, P[A[oj], :2], P[B[oj], :2])
            diff = c1 - c2
            dist = np.sqrt((diff * diff).sum(1))
            deep = dist < w
            if deep.any():
                d, dd = diff[deep], dist[deep]
                normal = np.zeros((len(dd), 3))
                normal[:, :2] = d / np.maximum(dd, 1e-9)[:, None]
                tiny = dd <= 1e-9
                if tiny.any():
                    seg = (q1 - p1)[deep][tiny]
                    side = np.column_stack([-seg[:, 1], seg[:, 0]])
                    normal[tiny, :2] = side / (np.sqrt((side * side).sum(1))[:, None] + 1e-12)
                parts.append((oi[deep], oj[deep], s[deep], t[deep], normal, w - dd))

        if not parts:
            return 0.0
        i = np.concatenate([p[0] for p in parts])
        j = np.concatenate([p[1] for p in parts])
        s = np.concatenate([p[2] for p in parts])
        t = np.concatenate([p[3] for p in parts])
        normal = np.concatenate([p[4] for p in parts])
        depth = np.concatenate([p[5] for p in parts])
        ia, ib, ja, jb = A[i], B[i], A[j], B[j]
        inv = self.inv
        wa0, wa1 = (1 - s) * inv[ia], s * inv[ib]
        wb0, wb1 = (1 - t) * inv[ja], t * inv[jb]
        # The table holds up a part pushed down onto it: the other part moves instead.
        z = P[:, 2]
        up, down = normal[:, 2] > 0.5, normal[:, 2] < -0.5
        wb0 = np.where(up & (z[ja] <= 1e-6), 0.0, wb0)
        wb1 = np.where(up & (z[jb] <= 1e-6), 0.0, wb1)
        wa0 = np.where(down & (z[ia] <= 1e-6), 0.0, wa0)
        wa1 = np.where(down & (z[ib] <= 1e-6), 0.0, wa1)
        norm = wa0 * wa0 + wa1 * wa1 + wb0 * wb0 + wb1 * wb1
        k = np.where(norm > 1e-12, depth / np.maximum(norm, 1e-12), 0.0)
        idx = np.concatenate([ia, ib, ja, jb])
        coef = np.concatenate([k * wa0, k * wa1, -k * wb0, -k * wb1])
        nrm = np.concatenate([normal, normal, normal, normal])
        used = np.concatenate([wa0, wa1, wb0, wb1]) > 0
        n = len(P)
        count = np.bincount(idx, used.astype(float), minlength=n)
        moved = count > 0
        for axis in range(3):
            acc = np.bincount(idx, coef * nrm[:, axis], minlength=n)
            P[moved, axis] += acc[moved] / count[moved]
        np.maximum(P[:, 2], 0.0, out=P[:, 2])
        return float(depth.max())

    def hold_pins(self):
        for (c, end), position in self.pins.items():
            self.P[self.end_index(c, end)] = position

    def overlap(self):
        """Deepest overlap between parts by the rules above, in widths."""
        self.find_pairs()
        if not self.plan_contacts():
            return float('inf')
        P0 = self.P.copy()
        worst = self.collide()
        self.P = P0
        return worst / self.width

    def clearance(self):
        """Smallest gap in the picture between two parts that do not cross,
        in widths (1.0: touching)."""
        self.find_pairs()
        if not self.plan_contacts():
            return 0.0
        oi, oj = self._plan['oi'], self._plan['oj']
        if not len(oi):
            return float('inf')
        P = self.P.copy()
        P[:, 2] = 0
        _, _, c1, c2 = _closest(P[self.A[oi]], P[self.B[oi]], P[self.A[oj]], P[self.B[oj]])
        return float(np.linalg.norm(c1 - c2, axis=1).min() / self.width)

    def core(self):
        """Middle of the knot: the mean of its crossings in the picture, or None."""
        i, j, t, u = self._crossings()
        if not len(i):
            return None
        P = self.P
        a = P[self.A[i], :2] + t[:, None] * (P[self.B[i], :2] - P[self.A[i], :2])
        return a.mean(0)

    def crossing_list(self):
        """The crossings now: point, cords, positions along them, which side is on top."""
        i, j, t, u = self._crossings()
        per = self._passes(i, j, t, u)
        over = self._align(per)
        where = {}
        for c, passes in enumerate(per):
            for s, k, side in passes:
                where.setdefault(k, {})[side] = (c, s)
        out = []
        P = self.P
        for k in range(len(i)):
            a = P[self.A[i[k]], :2] + t[k] * (P[self.B[i[k]], :2] - P[self.A[i[k]], :2])
            out.append(dict(point=(float(a[0]), float(a[1])),
                            cords=(int(where[k][0][0]), int(where[k][1][0])),
                            positions=(float(where[k][0][1]), float(where[k][1][1])),
                            over=None if over is None else int(over[k])))
        return out


def _tridiagonal(a, b, c, d):
    """Solve a tridiagonal system: a below the diagonal (n-1), b on it (n),
    c above it (n-1), right-hand side d (Thomas algorithm)."""
    n = len(b)
    if n == 0:
        return np.zeros(0)
    a, b, c, d = a.tolist(), b.tolist(), c.tolist(), d.tolist()
    cp, dp = [0.0] * n, [0.0] * n
    cp[0] = c[0] / b[0] if n > 1 else 0.0
    dp[0] = d[0] / b[0]
    for k in range(1, n):
        m = b[k] - a[k - 1] * cp[k - 1]
        cp[k] = c[k] / m if k < n - 1 else 0.0
        dp[k] = (d[k] - a[k - 1] * dp[k - 1]) / m
    y = [0.0] * n
    y[-1] = dp[-1]
    for k in range(n - 2, -1, -1):
        y[k] = dp[k] - cp[k] * y[k + 1]
    return np.array(y)


def _smooth_chain(x, fixed, lam):
    """Solve (1 + lam L) y = x along an open chain (Thomas algorithm), with the
    fixed points held and the free ends free."""
    n = len(x)
    a = np.full(n, -lam)        # below the diagonal
    b = np.full(n, 1 + 2 * lam)
    c = np.full(n, -lam)        # above the diagonal
    d = x.copy()
    b[0] = b[-1] = 1 + lam      # a free end has one neighbour
    for k in np.nonzero(fixed)[0]:
        a[k], b[k], c[k] = 0.0, 1.0, 0.0
    a[0] = 0.0
    c[-1] = 0.0
    cp = np.zeros(n)
    dp = np.zeros_like(d)
    cp[0] = c[0] / b[0]
    dp[0] = d[0] / b[0]
    for k in range(1, n):
        m = b[k] - a[k] * cp[k - 1]
        cp[k] = c[k] / m
        dp[k] = (d[k] - a[k] * dp[k - 1]) / m
    y = np.zeros_like(d)
    y[-1] = dp[-1]
    for k in range(n - 2, -1, -1):
        y[k] = dp[k] - cp[k] * y[k + 1]
    return y


def _closest(p1, q1, p2, q2):
    """Closest points between segments p1-q1 and p2-q2 (vectorised)."""
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a = (d1 * d1).sum(1)
    e = (d2 * d2).sum(1)
    f = (d2 * r).sum(1)
    c = (d1 * r).sum(1)
    b = (d1 * d2).sum(1)
    denom = a * e - b * b
    s = np.where(denom > 1e-12, np.clip((b * f - c * e) / np.maximum(denom, 1e-12), 0, 1), 0.0)
    t = (b * s + f) / np.maximum(e, 1e-12)
    low, high = t < 0, t > 1
    t = np.clip(t, 0, 1)
    s = np.where(low, np.clip(-c / np.maximum(a, 1e-12), 0, 1), s)
    s = np.where(high, np.clip((b - c) / np.maximum(a, 1e-12), 0, 1), s)
    return s, t, p1 + d1 * s[:, None], p2 + d2 * t[:, None]


def extend(cord, end, direction, reach):
    """The cord with a straight extension of length reach at one end (0 its
    start, 1 its end), heading the given way."""
    p = np.asarray(cord, dtype=float)
    d = np.array([direction[0], direction[1]], dtype=float)
    d /= np.linalg.norm(d) or 1.0
    tip = p[0] if end == 0 else p[-1]
    steps = max(2, int(reach // 4))
    line = np.array([[tip[0] + d[0] * reach * k / steps, tip[1] + d[1] * reach * k / steps]
                     + ([0.0] if p.shape[1] == 3 else []) for k in range(1, steps + 1)])
    return np.vstack([line[::-1], p]) if end == 0 else np.vstack([p, line])


def tighten(cords, width, pulls, closed=None, max_steps=2500, reach=None, keep_every=10,
            patience=100, grow_from=None, ramp=300, relax=None):
    """Pull the given ends until the knot jams, as a person tightens a knot.

    cords: polylines of (x, y, height) with heights in px (an over-part higher
    than the under-part where they cross). pulls: (cord, end, direction): end
    0 is the cord's start, 1 its end. Each pulled end is drawn off the given
    way (reach px, 6 widths by default) and held, in line with the knot as a
    hand pulls; the cord then draws itself tight between the held ends until
    the knot will give no more.

    Returns (cords, info). info: steps, jammed, start_length and end_length
    of the cord, clearance (smallest gap between parts that do not cross, in
    widths, 1.0 touching), overlap (deepest overlap in widths), crossings,
    retries (steps taken again more gently) and history: (length, cords)
    every keep_every steps, from loose to tight.

    grow_from: start with a cord this thick and thicken it to width over ramp
    steps. With width a few times the real cord's, a rough layout comes out
    evenly spaced and rounded, the same knot (dress()).
    """
    width = float(width)
    start_width = float(grow_from) if grow_from else width
    spacing = start_width * SPACING
    cords = [np.asarray(c, dtype=float) for c in cords]
    cords = [np.hstack([c, np.zeros((len(c), 1))]) if c.shape[1] == 2 else c.copy() for c in cords]
    closed = list(closed) if closed is not None else [False] * len(cords)
    reach = 6 * width if reach is None else reach
    ways = {}
    for cord, end, direction in pulls:
        if closed[cord]:
            raise SimulationError('a closed cord has no ends to pull')
        d = np.array([direction[0], direction[1]], dtype=float)
        if not np.linalg.norm(d):
            raise SimulationError('a pull needs a direction')
        ways[(cord, end)] = d / np.linalg.norm(d)
        cords[cord] = extend(cords[cord], end, d, reach)
    floor = min(c[:, 2].min() for c in cords)
    for c in cords:                     # under-parts on the table, over-parts above
        c[:, 2] -= floor
    pins = {key: (cords[key[0]][0] if key[1] == 0 else cords[key[0]][-1]).copy() for key in ways}
    rope = Rope(cords, start_width, closed, spacing=spacing, pins=pins)
    rope.hold_pins()
    for _ in range(40):                 # lift every over-part clear first
        rope.find_pairs()
        if not rope.plan_contacts():
            raise SimulationError('the cord touches itself where it should cross')
        for _ in range(3):
            rope.collide()
    reference = rope.reference
    start = rope.length()
    history = [(start, rope.cords())]
    good = (rope.cords(), dict(rope.pins), 0)
    gentle, retries, steps, calm_steps = 1.0, 0, 0, 0
    best, since, jammed = start, 0, False
    while steps < max_steps:
        steps += 1
        if start_width != width:
            rope.width = start_width + (width - start_width) * min(1.0, steps / ramp)
        rope.shorten_implicit(6.0 * gentle, 0.15 * gentle)
        rope.shorten(0.3 * gentle)
        rope.settle()
        rope.bend()
        centre = rope.core()
        if centre is not None:          # hands pull in line through the knot, not beside it
            for key, way in ways.items():
                pin = rope.pins[key]
                off = pin[:2] - centre
                side = off - (off @ way) * way
                rope.pins[key] = pin - np.r_[np.clip(0.1 * side, -0.1 * width, 0.1 * width), 0.0]
        rope.hold_pins()
        if steps % 3 == 0 or rope._pairs is None:
            rope.find_pairs()
        ok = rope.plan_contacts()
        if ok:
            for _ in range(3):
                rope.collide()
            rope.smooth()
            rope.collide()
            rope.hold_pins()
            if steps % 6 == 0:
                rope = rope.resampled()
            ok = rope.code_matches()
        if not ok:
            # Something passed through: back to the last good state, gentler.
            retries += 1
            if retries > 30:
                break
            cords_, pins_, steps = good
            rope = Rope(cords_, rope.width, closed, spacing=spacing, pins=pins_, reference=reference)
            gentle, calm_steps = max(gentle * 0.5, 1 / 32), 0
            continue
        calm_steps += 1
        if calm_steps >= 60 and gentle < 1.0:
            gentle, calm_steps = min(1.0, gentle * 2), 0
        total = rope.length()
        if total < best * (1 - 0.001) or steps < (ramp if start_width != width else 0):
            best, since = min(best, total), 0
        else:
            since += 1
            if since > patience:
                jammed = True
                break
        if steps % 10 == 0:
            good = (rope.cords(), dict(rope.pins), steps)
        if steps % keep_every == 0:
            history.append((total, rope.cords()))
    # Let the last contacts settle with no more pull; a cord laid out loose
    # (grown) relaxes longer, so no wobble is left where contacts pushed it.
    for k in range(relax if relax is not None else (120 if start_width != width else 30)):
        if k % 3 == 0:
            rope.find_pairs()
        if not rope.plan_contacts():
            break
        rope.smooth(3 if start_width != width else 2)
        for _ in range(3):
            rope.collide()
        rope.bend()
        rope.hold_pins()
        if k % 10 == 9:
            if rope.code_matches():
                good = (rope.cords(), dict(rope.pins), steps)
            else:
                break
    if not rope.code_matches():
        rope = Rope(good[0], rope.width, closed, spacing=spacing, pins=good[1], reference=reference)
    history.append((rope.length(), rope.cords()))
    info = dict(steps=steps, jammed=jammed, start_length=start, end_length=rope.length(),
                clearance=rope.clearance(), overlap=rope.overlap(), crossings=rope.crossing_list(),
                retries=retries, history=history)
    return rope.cords(), info


def snug(info, fraction):
    """From a tighten() history, the cords part of the way from loose (0) to
    tight (1), by how much cord the knot has given up."""
    history = info['history']
    if not history:
        raise SimulationError('there is no history to pick from')
    start, end = info['start_length'], info['end_length']
    target = start - fraction * (start - end)
    return min(history, key=lambda h: abs(h[0] - target))[1]

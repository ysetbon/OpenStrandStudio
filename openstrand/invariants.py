"""Which knot is this? Crossings of a drawn cord and its knot type.

A cord is a polyline of (x, y, height): the height says which part is on top
where two parts cross in the picture. From that, crossings() lists every
crossing with its over and under, and alexander() gives the cord's Alexander
polynomial: the same for every drawing of the same knot, however it is
moved, loosened or pulled tight. name() turns it into a name ("trefoil" for
an overhand knot, "figure-eight"). An open cord is closed first by joining
its two ends with an arc high above everything, the way a knot tied in a
rope is defined.

Only the standard library and numpy are used; the polynomial is computed
exactly with integers.
"""
import math
from bisect import bisect_right
from fractions import Fraction

import numpy as np

# Normalised Alexander polynomials (lowest power first, first coefficient
# positive) of the knots the tools use, with the knots people tie that close
# into them. Mirror images share a polynomial, as do the square and granny knots.
KNOTS = {
    (1,): ('unknot', 'no knot: the cord would slip free'),
    (1, -1, 1): ('trefoil', 'overhand knot (3_1)'),
    (1, -3, 1): ('figure-eight', 'figure eight knot (4_1)'),
    (1, -1, 1, -1, 1): ('cinquefoil', 'double overhand knot (5_1)'),
    (2, -3, 2): ('three-twist', 'three-twist knot (5_2)'),
    (2, -5, 2): ('stevedore', 'stevedore knot (6_1)'),
    (1, -3, 3, -3, 1): ('6_2', '6_2'),
    (1, -3, 5, -3, 1): ('6_3', '6_3'),
    (1, -1, 1, -1, 1, -1, 1): ('7_1', 'triple overhand knot (7_1)'),
    (3, -5, 3): ('7_2', '7_2'),
    (1, -2, 3, -2, 1): ('square or granny', 'two overhand knots, as in a square or granny knot'),
    (1, -4, 5, -4, 1): ('trefoil + figure-eight', 'an overhand and a figure eight knot together'),
    (1, -6, 11, -6, 1): ('two figure-eights', 'two figure eight knots together'),
}


def _segments(cord, closed):
    """Start points, end points and the arc length at each vertex."""
    p = np.asarray(cord, dtype=float)
    if p.shape[1] == 2:
        p = np.hstack([p, np.zeros((len(p), 1))])
    q = np.vstack([p, p[:1]]) if closed else p
    a, b = q[:-1], q[1:]
    lengths = np.hypot(*(b - a)[:, :2].T)
    s = np.concatenate([[0.0], np.cumsum(lengths)])
    return a, b, s


def box_pairs(lo, hi, block=512):
    """Pairs i < j of boxes (lower and upper corners) that overlap, in (i, j)
    order. Worked out a block of rows at a time: a long cord has millions of
    pairs, too many to list all at once."""
    m = len(lo)
    found_i, found_j = [np.zeros(0, dtype=np.intp)], [np.zeros(0, dtype=np.intp)]
    for start in range(0, m - 1, block):
        rows = np.arange(start, min(m, start + block))
        cols = np.arange(start + 1, m)
        hit = ((lo[rows, None, 0] <= hi[None, cols, 0]) & (lo[None, cols, 0] <= hi[rows, None, 0])
               & (lo[rows, None, 1] <= hi[None, cols, 1]) & (lo[None, cols, 1] <= hi[rows, None, 1])
               & (cols[None, :] > rows[:, None]))
        r, c = np.nonzero(hit)
        found_i.append(rows[r])
        found_j.append(cols[c])
    return np.concatenate(found_i), np.concatenate(found_j)


def crossings(cords, closed=None):
    """Every place where two parts of the cords cross in the picture.

    cords: polylines of (x, y) or (x, y, height); closed: one flag per cord.
    Returns dicts with point, cords (a, b), positions (arc length along each
    from its start), over (0 when cord a's part is on top, 1 when b's), the
    heights and the angle between the two parts in degrees.
    """
    closed = list(closed) if closed is not None else [False] * len(cords)
    starts, ends, owner, index, s0, s1 = [], [], [], [], [], []
    for c, cord in enumerate(cords):
        a, b, s = _segments(cord, closed[c])
        starts.append(a)
        ends.append(b)
        owner.append(np.full(len(a), c))
        index.append(np.arange(len(a)))
        s0.append(s[:-1])
        s1.append(s[1:])
    if not starts:
        return []
    A, B = np.vstack(starts), np.vstack(ends)
    own, idx = np.concatenate(owner), np.concatenate(index)
    S0, S1 = np.concatenate(s0), np.concatenate(s1)
    counts = {c: int((own == c).sum()) for c in range(len(cords))}
    lo, hi = np.minimum(A[:, :2], B[:, :2]), np.maximum(A[:, :2], B[:, :2])
    i, j = box_pairs(lo, hi)
    same = own[i] == own[j]
    gap = np.abs(idx[i] - idx[j])
    wrap = np.array([closed[c] for c in own[i]], dtype=bool) & (gap == np.array([counts[c] for c in own[i]]) - 1)
    keep = ~(same & ((gap <= 1) | wrap))
    i, j = i[keep], j[keep]
    p, r = A[i, :2], (B - A)[i, :2]
    q, d = A[j, :2], (B - A)[j, :2]
    denom = r[:, 0] * d[:, 1] - r[:, 1] * d[:, 0]
    ok = np.abs(denom) > 1e-12
    qp = q - p
    with np.errstate(divide='ignore', invalid='ignore'):
        t = (qp[:, 0] * d[:, 1] - qp[:, 1] * d[:, 0]) / denom
        u = (qp[:, 0] * r[:, 1] - qp[:, 1] * r[:, 0]) / denom
    hit = ok & (t >= 0) & (t < 1) & (u >= 0) & (u < 1)
    out = []
    for k in np.nonzero(hit)[0]:
        a_seg, b_seg, ta, ub = i[k], j[k], t[k], u[k]
        za = A[a_seg, 2] + ta * (B[a_seg, 2] - A[a_seg, 2])
        zb = A[b_seg, 2] + ub * (B[b_seg, 2] - A[b_seg, 2])
        ra, rb = r[k], d[k]
        cosine = abs(ra @ rb) / (np.hypot(*ra) * np.hypot(*rb) + 1e-12)
        out.append(dict(
            point=(float(p[k, 0] + ta * ra[0]), float(p[k, 1] + ta * ra[1])),
            cords=(int(own[a_seg]), int(own[b_seg])),
            positions=(float(S0[a_seg] + ta * (S1[a_seg] - S0[a_seg])),
                       float(S0[b_seg] + ub * (S1[b_seg] - S0[b_seg]))),
            heights=(float(za), float(zb)),
            over=0 if za >= zb else 1,
            angle=float(math.degrees(math.acos(min(1.0, cosine)))),
            directions=(ra / (np.hypot(*ra) + 1e-12), rb / (np.hypot(*rb) + 1e-12)),
        ))
    return out


def closed_up(cord, lift=None):
    """An open cord closed by joining its ends with a straight arc high above
    everything: the knot a tied rope is said to have."""
    p = np.asarray(cord, dtype=float)
    if p.shape[1] == 2:
        p = np.hstack([p, np.zeros((len(p), 1))])
    lift = lift if lift is not None else float(np.abs(p[:, 2]).max() + 1.0) * 1000 + 1000
    end, start = p[-1].copy(), p[0].copy()
    up_end, up_start = end.copy(), start.copy()
    up_end[2] = up_start[2] = lift
    return np.vstack([p, up_end, up_start])


def _bareiss_det(matrix):
    """Exact determinant of an integer matrix (Bareiss, fraction free)."""
    m = [list(map(int, row)) for row in matrix]
    n = len(m)
    if n == 0:
        return 1
    sign, prev = 1, 1
    for k in range(n - 1):
        if m[k][k] == 0:
            for r in range(k + 1, n):
                if m[r][k] != 0:
                    m[k], m[r] = m[r], m[k]
                    sign = -sign
                    break
            else:
                return 0
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                m[i][j] = (m[i][j] * m[k][k] - m[i][k] * m[k][j]) // prev
        prev = m[k][k]
    return sign * m[n - 1][n - 1]


def alexander(cord, closed=False):
    """The Alexander polynomial of one cord, as integer coefficients from the
    lowest power up, normalised: no zero ends, first coefficient positive."""
    poly = np.asarray(cord, dtype=float)
    if not closed:
        poly = closed_up(poly)
    found = [c for c in crossings([poly], [True]) if c['cords'] == (0, 0)]
    return alexander_from_crossings(found, _segments(poly, True)[2][-1])


def alexander_from_crossings(found, total):
    n = len(found)
    if n < 2:
        return (1,)
    # Under-passes split the cord into n arcs.
    unders = sorted(c['positions'][1 - c['over']] for c in found)
    rows = []
    for c in found:
        over_side = c['over']
        under_side = 1 - over_side
        s_over, s_under = c['positions'][over_side], c['positions'][under_side]
        k_out = unders.index(s_under)
        k_in = (k_out - 1) % n
        k_over = (bisect_right(unders, s_over) - 1) % n
        o, u = c['directions'][over_side], c['directions'][under_side]
        # Which side of the over-part the incoming under-arc lies on.
        left = (o[0] * (-u[1]) - o[1] * (-u[0])) > 0
        row = {}
        add = lambda col, coeff: row.__setitem__(col, tuple(x + y for x, y in zip(row.get(col, (0, 0)), coeff)))
        # Coefficients as (constant, multiple of t).
        add(k_over, (1, -1))                       # 1 - t on the over-arc
        add(k_in if left else k_out, (-1, 0))      # -1 on the under-arc to its left
        add(k_out if left else k_in, (0, 1))       # t on the under-arc to its right
        rows.append(row)
    size = n - 1

    def det_at(t):
        m = [[0] * size for _ in range(size)]
        for r in range(size):
            for col, (const, lin) in rows[r].items():
                if col < size:
                    m[r][col] += const + lin * t
        return _bareiss_det(m)
    xs = list(range(size + 1))
    ys = [det_at(x) for x in xs]
    coeffs = _interpolate(xs, ys)
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs.pop()
    while len(coeffs) > 1 and coeffs[0] == 0:
        coeffs.pop(0)
    if coeffs and coeffs[0] < 0:
        coeffs = [-x for x in coeffs]
    return tuple(coeffs) if coeffs else (0,)


def _interpolate(xs, ys):
    """Integer coefficients of the polynomial through the points (exact)."""
    n = len(xs)
    coeffs = [Fraction(0)] * n
    for i in range(n):
        basis = [Fraction(1)]
        denom = Fraction(1)
        for j in range(n):
            if j == i:
                continue
            basis = [Fraction(0)] + basis  # multiply by t
            for k in range(len(basis) - 1):
                basis[k] -= xs[j] * basis[k + 1]
            denom *= xs[i] - xs[j]
        for k in range(len(basis)):
            coeffs[k] += ys[i] * basis[k] / denom
    out = []
    for c in coeffs:
        if c.denominator != 1:
            raise ArithmeticError('the polynomial did not come out whole')
        out.append(int(c))
    return out


def name(coefficients):
    """('trefoil', 'overhand knot (3_1)'), or (None, None) for a knot not in the table."""
    return KNOTS.get(tuple(coefficients), (None, None))


# ------------------------------------------------------ the crossing code
# A knot that joins two cords (a bend), or makes a loop, cannot be named from
# one cord at a time: each cord of a square knot is unknotted on its own. What
# says which knot a drawing shows is its crossing code: for every cord, the
# crossings it passes in order, whether it goes over or under at each, and each
# crossing's hand (the way the upper part turns towards the lower one). Two
# drawings with the same code are the same knot, laid the same way.
def code(found, count, closed=None):
    """The crossing code of a drawing, from its crossings (as crossings()
    lists them, with over and directions) and the number of cords:

    passes   per cord, in order along it: (crossing number, on top there)
    hand     per crossing: +1 or -1, the turn from the upper part to the lower
    between  per crossing: the two cords, the upper part's first
    points   per crossing: where it is
    at       per crossing: its position along the upper part and the lower part
    closed   per cord
    """
    closed = list(closed) if closed is not None else [False] * count
    visits = [[] for _ in range(count)]
    hand, between, points, at = [], [], [], []
    for k, c in enumerate(found):
        over = int(c['over'])
        o, u = c['directions'][over], c['directions'][1 - over]
        hand.append(1 if o[0] * u[1] - o[1] * u[0] > 0 else -1)
        between.append((c['cords'][over], c['cords'][1 - over]))
        points.append((float(c['point'][0]), float(c['point'][1])))
        at.append((float(c['positions'][over]), float(c['positions'][1 - over])))
        for side in (0, 1):
            visits[c['cords'][side]].append((c['positions'][side], k, side == over))
    passes = [[(k, top) for _, k, top in sorted(v)] for v in visits]
    return dict(passes=passes, hand=hand, between=between, points=points, at=at, closed=closed)


def code_of(cords, closed=None):
    """The crossing code of cords given as (x, y, height) polylines."""
    closed = list(closed) if closed is not None else [False] * len(cords)
    return code(crossings(cords, closed), len(cords), closed)


def pattern(a_code, cord):
    """A cord's crossings as letters, in order along it: O over, U under."""
    return ''.join('O' if top else 'U' for _, top in a_code['passes'][cord])


def sub_code(a_code, keep):
    """The code of some of the cords alone (keep: their numbers, in the new
    order): what is left of a drawing when the other cords are taken away."""
    index = {c: n for n, c in enumerate(keep)}
    kept = [k for k, (a, b) in enumerate(a_code['between']) if a in index and b in index]
    number = {k: n for n, k in enumerate(kept)}
    return dict(passes=[[(number[k], top) for k, top in a_code['passes'][c] if k in number] for c in keep],
                hand=[a_code['hand'][k] for k in kept],
                between=[tuple(index[c] for c in a_code['between'][k]) for k in kept],
                points=[a_code['points'][k] for k in kept], at=[a_code['at'][k] for k in kept],
                closed=[a_code['closed'][c] for c in keep])


def compare(mine, other):
    """How the drawing with code mine relates to the one with code other.

    None when they are laid differently (their cords do not pass the same
    crossings in the same order, whichever way the cords are numbered and run).
    Else a dict: flipped, the crossings of mine (their numbers) that go the
    other way round from other; mirror, whether mine is other's mirror image;
    cords, for each cord of other the cord of mine that it is; and backwards,
    the cords of mine that run the other way. With no crossing flipped the two
    are the same knot (or mirror images of each other, which have the same
    name). A drawing seen from the back, every crossing turned over, is the
    same knot: it counts as nothing flipped.
    """
    import itertools
    n = len(other['passes'])
    if len(mine['passes']) != n or len(mine['hand']) != len(other['hand']):
        return None
    best = None
    for order in itertools.permutations(range(n)):
        if any(len(mine['passes'][order[i]]) != len(other['passes'][i])
               or bool(mine['closed'][order[i]]) != bool(other['closed'][i]) for i in range(n)):
            continue
        turns = [range(len(other['passes'][i])) if other['closed'][i] and other['passes'][i] else (0,)
                 for i in range(n)]
        for backwards in itertools.product((False, True), repeat=n):
            for shifts in itertools.product(*turns):
                found = _aligned(mine, other, order, backwards, shifts)
                if found is None:
                    continue
                flipped, mirror = found
                total = len(mine['hand'])
                if len(flipped) * 2 > total:      # seen from the back: the rest are the ones that differ
                    flipped, mirror = sorted(set(range(total)) - set(flipped)), not mirror
                key = (len(flipped), mirror, order != tuple(range(n)), any(backwards))
                if best is None or key < best[0]:
                    best = (key, dict(flipped=flipped, mirror=mirror, cords=list(order),
                                      backwards=[order[i] for i in range(n) if backwards[i]]))
    return best[1] if best else None


def _aligned(mine, other, order, backwards, shifts):
    """mine against other with other's cord i taken as mine's cord order[i],
    run backwards where asked and (closed cords) started shifts[i] passes on:
    (crossings of mine that are the other way round, mirror image), or None."""
    to_mine, to_other, flipped = {}, {}, set()
    for i, row in enumerate(other['passes']):
        own = mine['passes'][order[i]]
        size = len(row)
        for j, (k, top) in enumerate(row):
            at = (size - 1 - j if backwards[i] else j)
            at = (at + shifts[i]) % size if size else at
            k_mine, top_mine = own[at]
            if to_mine.setdefault(k, k_mine) != k_mine or to_other.setdefault(k_mine, k) != k:
                return None
            if top_mine != top:
                flipped.add(k_mine)
    place = {c: i for i, c in enumerate(order)}
    mirror = None
    for k, k_mine in to_mine.items():
        a, b = other['between'][k]
        # A crossing's hand turns over when one of its two cords runs the other
        # way (not when both do, as for a cord crossing itself) and when the
        # crossing is flipped.
        turned = (backwards[a] != backwards[b]) != (k_mine in flipped)
        same = (mine['hand'][k_mine] == other['hand'][k]) != turned
        if mirror is None:
            mirror = not same
        elif mirror != (not same):
            return None
    # The two cords of each crossing must be the matching ones.
    for k, k_mine in to_mine.items():
        if sorted(place[c] for c in mine['between'][k_mine]) != sorted(other['between'][k]):
            return None
    return sorted(flipped), bool(mirror)


JONES_CROSSINGS = 16        # the Jones polynomial is worked out for drawings of up to this many crossings


def jones(a_code):
    """The Jones polynomial of closed cords, from their crossing code, as
    {power of t in quarters: coefficient} (so {4: 1, 12: 1, 16: -1} is
    t + t^3 - t^4, a trefoil). It tells a knot from its mirror image, which
    the Alexander polynomial cannot: a square knot's polynomial reads the same
    with t turned into 1/t, a granny knot's does not. Worked out from the
    Kauffman bracket, one state for each way of opening every crossing, so
    only for drawings of up to JONES_CROSSINGS crossings (else None)."""
    total = len(a_code['hand'])
    if total > JONES_CROSSINGS:
        return None
    # The four ends at crossing k: 0 over in, 1 over out, 2 under in, 3 under out.
    link = {}
    loose = 0
    for row in a_code['passes']:
        if not row:
            loose += 1                      # a cord that crosses nothing is a loop of its own
        for i, (k, top) in enumerate(row):
            k2, top2 = row[(i + 1) % len(row)]
            a, b = (k, 1 if top else 3), (k2, 0 if top2 else 2)
            link[a], link[b] = b, a
    bracket = {}
    for state in range(1 << total):
        pair = {}
        for k in range(total):
            # Opening a crossing one way joins the over part's far end to the
            # under part's near end; the other way, the two far ends.
            if (a_code['hand'][k] > 0) == bool((state >> k) & 1):
                joins = ((1, 2), (3, 0))
            else:
                joins = ((1, 3), (0, 2))
            for x, y in joins:
                pair[(k, x)], pair[(k, y)] = (k, y), (k, x)
        seen, loops = set(), loose
        for start in pair:
            if start in seen:
                continue
            loops += 1
            node = start
            while node not in seen:
                seen.add(node)
                seen.add(pair[node])
                node = link[pair[node]]
        ones = bin(state).count('1')
        term = {2 * ones - total: 1}
        for _ in range(loops - 1):          # each further loop: times -A^2 - A^-2
            grown = {}
            for power, c in term.items():
                grown[power + 2] = grown.get(power + 2, 0) - c
                grown[power - 2] = grown.get(power - 2, 0) - c
            term = grown
        for power, c in term.items():
            bracket[power] = bracket.get(power, 0) + c
    writhe = sum(a_code['hand'])
    out = {}
    for power, c in bracket.items():        # times (-A^3)^-writhe, then t = A^-4
        key = 3 * writhe - power
        out[key] = out.get(key, 0) + (-c if writhe % 2 else c)
    return dict(sorted((power, c) for power, c in out.items() if c))


def through(a_code, loop_of, other):
    """How many times cord other passes through each loop of cord loop_of.

    A loop is the part of a cord between its two passes of one of its own
    crossings. A cord that goes over one side of a loop and under the other
    has passed through it (once: 1.0, or -1.0 the other way); a cord that goes
    over both sides, or under both, has not (0.0). A half means one of the
    cord's ends lies inside the loop. Returns {crossing number: times}.
    """
    out = {}
    passes = a_code['passes'][loop_of]
    for k, (a, b) in enumerate(a_code['between']):
        if a != loop_of or b != loop_of:
            continue
        first, last = [n for n, (c, _) in enumerate(passes) if c == k]
        inside = {c for c, _ in passes[first + 1:last]}
        # Half the sum of the hands of the crossings the other cord makes with
        # the loop: the linking number of the two, as for two closed curves.
        total = sum(a_code['hand'][c] for c in inside if sorted(a_code['between'][c]) == sorted((loop_of, other))
                    and loop_of != other)
        out[k] = total / 2
    return out


def describe(cord, closed=False):
    """Crossings, polynomial and name of one cord, for reports."""
    poly = np.asarray(cord, dtype=float)
    count = len([c for c in crossings([poly], [closed]) if c['cords'] == (0, 0)])
    coeffs = alexander(poly, closed)
    short, long = name(coeffs)
    return dict(crossings=count, alexander=coeffs, knot=short, meaning=long)

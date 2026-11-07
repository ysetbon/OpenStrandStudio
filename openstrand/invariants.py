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
    (1, -1, 1, -1, 1): ('cinquefoil', '5_1, the double coin family'),
    (2, -3, 2): ('three-twist', 'double overhand knot (5_2)'),
    (2, -5, 2): ('stevedore', 'stevedore knot (6_1)'),
    (1, -3, 3, -3, 1): ('6_2', '6_2'),
    (1, -3, 5, -3, 1): ('6_3', '6_3'),
    (1, -1, 1, -1, 1, -1, 1): ('7_1', '7_1'),
    (3, -5, 3): ('7_2', 'triple overhand knot (7_2)'),
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
    m = len(A)
    i, j = np.triu_indices(m, 1)
    box = ((lo[i, 0] <= hi[j, 0]) & (lo[j, 0] <= hi[i, 0]) & (lo[i, 1] <= hi[j, 1]) & (lo[j, 1] <= hi[i, 1]))
    i, j = i[box], j[box]
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


def describe(cord, closed=False):
    """Crossings, polynomial and name of one cord, for reports."""
    poly = np.asarray(cord, dtype=float)
    count = len([c for c in crossings([poly], [closed]) if c['cords'] == (0, 0)])
    coeffs = alexander(poly, closed)
    short, long = name(coeffs)
    return dict(crossings=count, alexander=coeffs, knot=short, meaning=long)

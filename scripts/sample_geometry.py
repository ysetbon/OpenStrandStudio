"""Curve design, native-curve fitting and crossing masks for generated samples.

Designs are drawn as smooth dense centerlines. They are split into the fewest
attached strands whose native two-handle curves stay within a tolerance of the
centerline, with the design's own tangents at every join. Over/under order is
then decided per crossing and realised with MaskedStrand layers; every stroke
overlap is assigned to a crossing, so no overlap is left to layer order by
accident.
"""
import math

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainterPathStroker


# --------------------------------------------------------------------------
# Plain point helpers (tuples keep the fitting loops fast)

def add(a, b): return (a[0]+b[0], a[1]+b[1])
def sub(a, b): return (a[0]-b[0], a[1]-b[1])
def mul(a, k): return (a[0]*k, a[1]*k)
def dot(a, b): return a[0]*b[0]+a[1]*b[1]
def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])


def unit(v):
    n = math.hypot(*v)
    return (v[0]/n, v[1]/n) if n > 1e-12 else (1.0, 0.0)


def segment_distance(q, a, b):
    d = sub(b, a)
    n = dot(d, d)
    t = min(1.0, max(0.0, dot(sub(q, a), d)/n)) if n else 0.0
    return dist(q, add(a, mul(d, t)))


def lerp(a, b, t): return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)


def resample(poly, spacing):
    """Uniform arc-length samples of a polyline, keeping both ends."""
    lengths = [0.0]
    for a, b in zip(poly, poly[1:]):
        lengths.append(lengths[-1]+dist(a, b))
    total = lengths[-1]
    count = max(2, round(total/spacing)+1)
    out, j = [], 0
    for k in range(count):
        s = total*k/(count-1)
        while j < len(poly)-2 and lengths[j+1] < s:
            j += 1
        span = lengths[j+1]-lengths[j]
        out.append(lerp(poly[j], poly[j+1], (s-lengths[j])/span if span else 0))
    return out


def spline(points, closed=False, spacing=2.0):
    """Centripetal Catmull-Rom curve through design landmarks.

    Closed curves are returned with the first sample repeated at the end.
    """
    pts = [tuple(map(float, p)) for p in points]
    if closed:
        ext = [pts[-1]]+pts+[pts[0], pts[1]]
    else:
        ext = [sub(mul(pts[0], 2), pts[1])]+pts+[sub(mul(pts[-1], 2), pts[-2])]
    dense = [pts[0]]
    for i in range(1, len(ext)-2):
        p0, p1, p2, p3 = ext[i-1:i+3]
        t0 = 0.0
        t1 = t0+max(dist(p0, p1), 1e-6)**.5
        t2 = t1+max(dist(p1, p2), 1e-6)**.5
        t3 = t2+max(dist(p2, p3), 1e-6)**.5
        steps = max(8, int(dist(p1, p2)/2))
        for k in range(1, steps+1):
            t = t1+(t2-t1)*k/steps
            a1 = add(mul(p0, (t1-t)/(t1-t0)), mul(p1, (t-t0)/(t1-t0)))
            a2 = add(mul(p1, (t2-t)/(t2-t1)), mul(p2, (t-t1)/(t2-t1)))
            a3 = add(mul(p2, (t3-t)/(t3-t2)), mul(p3, (t-t2)/(t3-t2)))
            b1 = add(mul(a1, (t2-t)/(t2-t0)), mul(a2, (t-t0)/(t2-t0)))
            b2 = add(mul(a2, (t3-t)/(t3-t1)), mul(a3, (t-t1)/(t3-t1)))
            dense.append(add(mul(b1, (t2-t)/(t2-t1)), mul(b2, (t-t1)/(t2-t1))))
    return resample(dense, spacing)


def parametric(fn, t0, t1, closed=False, spacing=2.0, steps=4000):
    poly = [fn(t0+(t1-t0)*k/steps) for k in range(steps+1)]
    if closed:
        poly[-1] = poly[0]
    return resample(poly, spacing)


def offset(poly, d, closed=False):
    """Parallel curve at signed distance d (positive = left of travel)."""
    n = len(poly)
    out = []
    for k in range(n):
        if closed:
            a, b = poly[(k-1) % (n-1)], poly[(k+1) % (n-1)]
        else:
            a, b = poly[max(k-1, 0)], poly[min(k+1, n-1)]
        tx, ty = unit(sub(b, a))
        out.append((poly[k][0]-ty*d, poly[k][1]+tx*d))
    if closed:
        out[-1] = out[0]
    return out


def tangents(poly, closed):
    n = len(poly)
    out = []
    for k in range(n):
        if closed:
            a, b = poly[(k-2) % (n-1)], poly[(k+2) % (n-1)]
        else:
            a, b = poly[max(k-2, 0)], poly[min(k+2, n-1)]
        out.append(unit(sub(b, a)))
    return out


def arc_lengths(poly):
    out = [0.0]
    for a, b in zip(poly, poly[1:]):
        out.append(out[-1]+dist(a, b))
    return out


def polyline_crossings(a, b, same=False, gap=0):
    """Centerline intersections as (index_a + fraction, index_b + fraction, point)."""
    cell = 24.0
    grid = {}
    for j in range(len(b)-1):
        x0, x1 = sorted((b[j][0], b[j+1][0]))
        y0, y1 = sorted((b[j][1], b[j+1][1]))
        for gx in range(int(x0//cell), int(x1//cell)+1):
            for gy in range(int(y0//cell), int(y1//cell)+1):
                grid.setdefault((gx, gy), []).append(j)
    hits = []
    for i in range(len(a)-1):
        p, q = a[i], a[i+1]
        seen = set()
        for gx in range(int(min(p[0], q[0])//cell), int(max(p[0], q[0])//cell)+1):
            for gy in range(int(min(p[1], q[1])//cell), int(max(p[1], q[1])//cell)+1):
                for j in grid.get((gx, gy), ()):
                    if j in seen or (same and j <= i+gap):
                        continue
                    seen.add(j)
                    r, s = b[j], b[j+1]
                    d1, d2 = sub(q, p), sub(s, r)
                    den = d1[0]*d2[1]-d1[1]*d2[0]
                    if abs(den) < 1e-12:
                        continue
                    w = sub(r, p)
                    u = (w[0]*d2[1]-w[1]*d2[0])/den
                    v = (w[0]*d1[1]-w[1]*d1[0])/den
                    if 0 <= u < 1 and 0 <= v < 1:
                        hits.append((i+u, j+v, add(p, mul(d1, u))))
    return hits


def _least_squares(rows, rhs):
    """Solve the normal equations of a small dense system; None if singular."""
    n = len(rows[0])
    m = [[sum(r[i]*r[j] for r in rows) for j in range(n)]+[sum(r[i]*y for r, y in zip(rows, rhs))]
         for i in range(n)]
    scale = max(abs(m[i][i]) for i in range(n)) or 1.0
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12*scale:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        for r in range(n):
            if r != col:
                f = m[r][col]/m[col][col]
                m[r] = [x-f*y for x, y in zip(m[r], m[col])]
    return [m[i][n]/m[i][i] for i in range(n)]


# --------------------------------------------------------------------------
# The application's two-handle curve (AttachedStrand.get_path without a
# locked centre point): two cubic halves around the implied handle midpoint.

class NativeCurve:
    def __init__(self, base=1.0, boost=2.0, exponent=2.0):
        self.f1 = ((.1+base*.2)*boost)**(1/exponent)
        self.f2 = ((.05+base*.1)*boost)**(1/exponent)

    def weights(self, t):
        f1, f2 = self.f1, self.f2
        if t <= .5:
            v = 2*t; u = 1-v
            return (u**3+3*u*u*v*(1-f1),
                    3*u*u*v*f1+3*u*v*v*(1+f2)/2+v**3/2,
                    3*u*v*v*(1-f2)/2+v**3/2, 0.0)
        v = 2*t-1; u = 1-v
        return (0.0, u**3/2+3*u*u*v*(1-f2)/2,
                u**3/2+3*u*u*v*(1+f2)/2+3*u*v*v*f2,
                3*u*v*v*(1-f2)+v**3)

    def point(self, c, t):
        w = self.weights(t)
        return (sum(p[0]*k for p, k in zip(c, w)), sum(p[1]*k for p, k in zip(c, w)))

    def fit_span(self, samples, t1, t2, headings=None):
        """Handles for one span; returns (curve, max deviation, max turn error).

        t1/t2 fix the handle directions at the ends (lengths are free); None
        leaves that handle free, for a cord's loose end. With headings (the
        design's unit tangents at the samples), the third value is the
        largest angle, in degrees, between the curve and the design: a curve
        can stay close yet bend unevenly, which shows as flat spots.
        """
        a, b = samples[0], samples[-1]
        lengths = arc_lengths(samples)
        total = lengths[-1]
        if total < 1e-6:
            return None, math.inf, math.inf
        ts = [s/total for s in lengths]
        curve = None
        for iteration in range(6):
            # Least squares: p - a*w0 - b*w3 = w1*cp1 + w2*cp2 per sample.
            rows, rhs = [], []
            for p, t in zip(samples, ts):
                w0, w1, w2, w3 = self.weights(t)
                r = sub(p, add(mul(a, w0+(w1 if t1 else 0)), mul(b, w3+(w2 if t2 else 0))))
                for axis in (0, 1):
                    row = []
                    row += [w1*t1[axis]] if t1 else [w1*(axis == 0), w1*(axis == 1)]
                    row += [-w2*t2[axis]] if t2 else [w2*(axis == 0), w2*(axis == 1)]
                    rows.append(row)
                    rhs.append(r[axis])
            x = _least_squares(rows, rhs)
            if x is None:
                return None, math.inf, math.inf
            if t1:
                cp1, x = add(a, mul(t1, x[0])), x[1:]
            else:
                cp1, x = (x[0], x[1]), x[2:]
            cp2 = sub(b, mul(t2, x[0])) if t2 else (x[0], x[1])
            h1, h2 = dist(a, cp1), dist(b, cp2)
            if t1 and dot(sub(cp1, a), t1) <= total*.02 or t2 and dot(sub(b, cp2), t2) <= total*.02:
                return None, math.inf, math.inf
            if max(h1, h2) > total*1.4:
                return None, math.inf, math.inf
            curve = (a, cp1, cp2, b)
            if iteration == 5:
                break
            updated = [0.0]
            for p, t in zip(samples[1:-1], ts[1:-1]):
                e = 1e-4
                here = self.point(curve, t)
                ahead, behind = self.point(curve, min(1, t+e)), self.point(curve, max(0, t-e))
                d = mul(sub(ahead, behind), 1/(2*e))
                dd = mul(add(sub(ahead, mul(here, 2)), behind), 1/(e*e))
                r = sub(here, p)
                den = dot(d, d)+dot(r, dd)
                updated.append(min(1.0, max(0.0, t-dot(r, d)/den if abs(den) > 1e-9 else t)))
            updated.append(1.0)
            if any(x >= y for x, y in zip(updated, updated[1:])):
                break
            ts = updated
        # Deviation both ways: samples to curve and curve to samples.
        error = max(dist(self.point(curve, t), p) for p, t in zip(samples, ts))
        probe = [self.point(curve, k/24) for k in range(25)]
        for q in probe:
            error = max(error, min(segment_distance(q, p, r) for p, r in zip(samples, samples[1:])))
        turn = 0.0
        if headings:
            for h, t in zip(headings, ts):
                e = 1e-4
                d = unit(sub(self.point(curve, min(1, t+e)), self.point(curve, max(0, t-e))))
                turn = max(turn, math.degrees(math.acos(max(-1.0, min(1.0, dot(d, h))))))
        return curve, error, turn

    def fit(self, poly, closed, tolerance, forced=(), avoid=(), step=4, max_length=900, min_length=0,
            max_turn=math.radians(150), max_bend_error=6.0, bend_length=150, free_ends=False, cost=None):
        """Fewest spans within tolerance, so each strand's control points
        carry as much of the design as they can.

        A span must stay within tolerance of the design and follow its
        direction within max_bend_error degrees everywhere (more on spans
        shorter than bend_length): a long native curve can stay close yet
        bend unevenly, which shows as flat spots on wide arcs. max_turn caps
        the total turn of one span.

        Joins keep the design's tangent; with free_ends an open cord's two
        loose ends may pick their own handle direction.
        Forced sample indices stay joins; avoided ones (crossings) never are.
        cost(index) adds to a join's price in spans, so crowded joins are
        used only when they save a strand.
        """
        n = len(poly)
        tang = tangents(poly, closed)
        lengths = arc_lengths(poly)
        turning = [0.0]
        for a, b in zip(tang, tang[1:]):
            turning.append(turning[-1]+abs(math.atan2(a[0]*b[1]-a[1]*b[0], dot(a, b))))
        forced = set(forced)
        avoid = set(avoid)-forced
        candidates = sorted((set(range(0, n-1, step))-avoid) | {0, n-1} | forced)
        loose = {0, n-1} if free_ends and not closed else set()
        best = {0: (0, 0.0, None, None)}
        for jj in range(1, len(candidates)):
            j = candidates[jj]
            options = []
            for ii in range(jj-1, -1, -1):
                i = candidates[ii]
                span = lengths[j]-lengths[i]
                if ii < jj-1 and (candidates[ii+1] in forced or span > max_length
                                  or turning[j]-turning[i] > max_turn):
                    break
                stride = max(1, (j-i)//48)
                picks = list(range(i, j+1, stride))
                if picks[-1] != j:
                    picks.append(j)
                curve, error, bend = self.fit_span([poly[k] for k in picks],
                                                   None if i in loose else tang[i],
                                                   None if j in loose else tang[j],
                                                   [tang[k] for k in picks])
                if curve is None and ii == jj-1:
                    curve = (poly[i], lerp(poly[i], poly[j], 1/3), lerp(poly[i], poly[j], 2/3), poly[j])
                    error = bend = 0.0
                if curve is None:
                    continue
                short = lengths[j]-lengths[i] < min_length and not (i in forced and j in forced)
                # Flat spots show on long, wide arcs; a short tight bend may
                # stray further in direction without showing it.
                bend_limit = max_bend_error*max(1.0, bend_length/max(span, 1e-6))
                if (error <= tolerance and bend <= bend_limit and not short) or ii == jj-1:
                    count, total, _, _ = best[i]
                    # Short spans only as a last resort: they make tiny strands.
                    price = cost(j) if cost and j != n-1 else 0.0
                    options.append((count+1+(short*.5)+price, total+error, i, curve))
            best[j] = min(options, key=lambda o: o[:2])
        spans, j = [], n-1
        while j:
            _, _, i, curve = best[j]
            spans.append((i, j, curve))
            j = i
        return spans[::-1]


def stroke(path, width):
    stroker = QPainterPathStroker()
    stroker.setWidth(width)
    stroker.setCapStyle(Qt.FlatCap)
    stroker.setJoinStyle(Qt.RoundJoin)
    return stroker.createStroke(path)

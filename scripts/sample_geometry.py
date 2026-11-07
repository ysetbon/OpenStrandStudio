"""Curve design, native-curve fitting and crossing masks for generated samples.

Designs are drawn as smooth dense centerlines. They are split into the fewest
attached strands whose native two-handle curves stay within a tolerance of the
centerline, with the design's own tangents at every join. Over/under order is
then decided per crossing and realised with MaskedStrand layers; every stroke
overlap is assigned to a crossing, so no overlap is left to layer order by
accident.
"""
import math

import numpy as np
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


def _solve_normal(m, rhs):
    """Solve a small least-squares system from its normal equations (m is
    the n x n matrix, n <= 4, rhs its right-hand side), Gauss-Jordan with
    partial pivoting; None if singular."""
    n = len(rhs)
    m = [list(map(float, row))+[float(y)] for row, y in zip(m, rhs)]
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


def _solve_normal_batch(M, v):
    """_solve_normal for many systems at once: M (S, n, n), v (S, n) ->
    (x (S, n), ok (S,)), the same pivoting and singular test per system."""
    S, n = v.shape
    rows = np.arange(S)
    aug = np.concatenate([M, v[:, :, None]], axis=2)
    scale = np.abs(np.diagonal(M, axis1=1, axis2=2)).max(1)
    scale = np.where(scale == 0, 1.0, scale)
    ok = np.ones(S, dtype=bool)
    for col in range(n):
        pivot = col+np.argmax(np.abs(aug[:, col:, col]), axis=1)
        ok &= ~(np.abs(aug[rows, pivot, col]) < 1e-12*scale)
        top = aug[rows, col].copy()
        aug[rows, col] = aug[rows, pivot]
        aug[rows, pivot] = top
        head = np.where(ok, aug[:, col, col], 1.0)
        for r in range(n):
            if r != col:
                f = aug[:, r, col]/head
                aug[:, r] = aug[:, r]-f[:, None]*aug[:, col]
    diag = np.diagonal(aug[:, :, :n], axis1=1, axis2=2)
    return aug[:, :, n]/np.where(ok[:, None], diag, 1.0), ok


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

    def weights_array(self, t):
        """weights() for an array of t at once: shape t.shape + (4,)."""
        t = np.asarray(t, dtype=float)
        f1, f2 = self.f1, self.f2
        lo = t <= .5
        v = np.where(lo, 2*t, 2*t-1)
        u = 1-v
        u3, v3 = u**3, v**3
        uuv, uvv = 3*u*u*v, 3*u*v*v
        w = np.empty(t.shape+(4,))
        w[..., 0] = np.where(lo, u3+uuv*(1-f1), 0.0)
        w[..., 1] = np.where(lo, uuv*f1+uvv*(1+f2)/2+v3/2, u3/2+uuv*(1-f2)/2)
        w[..., 2] = np.where(lo, uvv*(1-f2)/2+v3/2, u3/2+uuv*(1+f2)/2+uvv*f2)
        w[..., 3] = np.where(lo, 0.0, uvv*(1-f2)+v3)
        return w

    def points_array(self, curves, t):
        """point() for many curves at once: curves (..., 4, 2), t (..., k)
        -> (..., k, 2)."""
        return self.weights_array(t) @ curves

    def fit_span(self, samples, t1, t2, headings=None):
        """Handles for one span; returns (curve, max deviation, max turn error).

        t1/t2 fix the handle directions at the ends (lengths are free); None
        leaves that handle free, for a cord's loose end. With headings (the
        design's unit tangents at the samples), the third value is the
        largest angle, in degrees, between the curve and the design: a curve
        can stay close yet bend unevenly, which shows as flat spots.
        """
        P = np.asarray(samples, dtype=float)[None, :, :2]
        H = None if not headings else np.asarray(headings, dtype=float)[None, :, :2]
        return self.fit_spans(P, np.array([len(samples)]), [t1], [t2], H)[0]

    # Spans fitted per batch: samples x spans, so a batch stays a few MB.
    BATCH = 24000

    def fit_spans(self, P, m, t1s, t2s, H=None):
        """fit_span for many spans at once, the same arithmetic on whole
        arrays: drawing one design fits tens of thousands of spans, which
        took minutes one sample at a time.

        P (S, K, 2): each span's samples, the first m[s] used (the rest is
        padding); t1s, t2s: each span's end directions, or None; H (S, K, 2):
        headings, or None. Returns [(curve, error, turn)] as fit_span does.
        """
        P = np.asarray(P, dtype=float)
        m = np.asarray(m, dtype=int)
        S, K = P.shape[:2]
        out = [None]*S
        per = max(1, self.BATCH//max(K, 1))
        for lo in range(0, S, per):
            hi = min(S, lo+per)
            curves, errors, turns, ok = self._fit_batch(
                P[lo:hi], m[lo:hi], t1s[lo:hi], t2s[lo:hi], None if H is None else H[lo:hi])
            for k in range(hi-lo):
                if ok[k]:
                    out[lo+k] = (tuple((float(x), float(y)) for x, y in curves[k]),
                                 float(errors[k]), float(turns[k]))
                else:
                    out[lo+k] = (None, math.inf, math.inf)
        return out

    def _fit_batch(self, P, m, t1s, t2s, H):
        S, K = P.shape[:2]
        rows = np.arange(S)
        valid = np.arange(K)[None, :] < m[:, None]
        a, b = P[:, 0], P[rows, m-1]
        has1 = np.array([bool(t) for t in t1s])
        has2 = np.array([bool(t) for t in t2s])
        T1 = np.array([t[:2] if t else (0.0, 0.0) for t in t1s], dtype=float).reshape(S, 2)
        T2 = np.array([t[:2] if t else (0.0, 0.0) for t in t2s], dtype=float).reshape(S, 2)
        step = np.hypot(P[:, 1:, 0]-P[:, :-1, 0], P[:, 1:, 1]-P[:, :-1, 1])
        lengths = np.concatenate([np.zeros((S, 1)), np.cumsum(np.where(valid[:, 1:], step, 0.0), axis=1)], axis=1)
        total = lengths[rows, m-1]
        ok = total >= 1e-6
        ts = np.where(valid, lengths/np.where(ok, total, 1.0)[:, None], 1.0)
        curves = np.zeros((S, 4, 2))
        curves[:, 0], curves[:, 3] = a, b
        active = ok.copy()
        e = 1e-4
        for iteration in range(6):
            for kind in ((True, True), (True, False), (False, True), (False, False)):
                idx = np.nonzero(active & (has1 == kind[0]) & (has2 == kind[1]))[0]
                if len(idx):
                    ok[idx], curves[idx, 1], curves[idx, 2] = self._solve_handles(
                        P[idx], valid[idx], ts[idx], a[idx], b[idx], T1[idx], T2[idx], total[idx], *kind)
            active &= ok
            if iteration == 5 or not active.any():
                break
            idx = np.nonzero(active)[0]
            t = ts[idx]
            inner = valid[idx] & (np.arange(K)[None, :] > 0) & (np.arange(K)[None, :] < m[idx, None]-1)
            c = curves[idx]
            here = self.points_array(c, t)
            ahead = self.points_array(c, np.minimum(1, t+e))
            behind = self.points_array(c, np.maximum(0, t-e))
            d = (ahead-behind)*(1/(2*e))
            dd = (ahead-here*2+behind)*(1/(e*e))
            r = here-P[idx]
            den = (d[..., 0]*d[..., 0]+d[..., 1]*d[..., 1])+(r[..., 0]*dd[..., 0]+r[..., 1]*dd[..., 1])
            usable = np.abs(den) > 1e-9
            moved = t-(r[..., 0]*d[..., 0]+r[..., 1]*d[..., 1])/np.where(usable, den, 1.0)
            updated = np.where(inner, np.minimum(1.0, np.maximum(0.0, np.where(usable, moved, t))), t)
            updated[:, 0] = 0.0
            updated[np.arange(len(idx)), m[idx]-1] = 1.0
            pair = valid[idx][:, 1:]
            stuck = (pair & (updated[:, :-1] >= updated[:, 1:])).any(1)
            ts[idx[~stuck]] = updated[~stuck]
            active[idx[stuck]] = False
        # Deviation both ways: samples to curve and curve to samples.
        on = self.points_array(curves, ts)-P
        error = np.where(valid, np.hypot(on[..., 0], on[..., 1]), -np.inf).max(1)
        probe = self.points_array(curves, np.broadcast_to(np.arange(25)/24, (S, 25)))
        # Each probe's distance to the nearest piece of the samples' polyline.
        ax, ay = P[:, None, :-1, 0], P[:, None, :-1, 1]
        sx, sy = P[:, None, 1:, 0]-ax, P[:, None, 1:, 1]-ay
        n = sx*sx+sy*sy
        live = valid[:, None, 1:] & (n > 0)
        rx, ry = probe[:, :, None, 0]-ax, probe[:, :, None, 1]-ay
        u = np.clip((rx*sx+ry*sy)/np.where(live, n, 1.0), 0.0, 1.0)
        u = np.where(live, u, 0.0)
        gx, gy = rx-sx*u, ry-sy*u
        far = np.where(valid[:, None, 1:], gx*gx+gy*gy, np.inf).min(2)
        error = np.maximum(error, np.sqrt(far.max(1)))
        turn = np.zeros(S)
        if H is not None:
            d = self.points_array(curves, np.minimum(1, ts+e))-self.points_array(curves, np.maximum(0, ts-e))
            size = np.hypot(d[..., 0], d[..., 1])
            big = size > 1e-12
            ux = np.where(big, d[..., 0]/np.where(big, size, 1.0), 1.0)
            uy = np.where(big, d[..., 1]/np.where(big, size, 1.0), 0.0)
            cosine = np.maximum(-1.0, np.minimum(1.0, ux*H[..., 0]+uy*H[..., 1]))
            turn = np.where(valid, np.degrees(np.arccos(cosine)), 0.0).max(1)
        return curves, error, turn, ok

    def _solve_handles(self, P, valid, ts, a, b, T1, T2, total, fixed1, fixed2):
        """One least-squares round for spans of one kind (which ends have a
        fixed direction): (ok, cp1, cp2), as fit_span's round, with
        _solve_normal's pivoting and singular test."""
        w = self.weights_array(ts)*valid[..., None]
        w0, w1, w2, w3 = w[..., 0], w[..., 1], w[..., 2], w[..., 3]
        base = (a[:, None, :]*(w0+(w1 if fixed1 else 0))[..., None]
                + b[:, None, :]*(w3+(w2 if fixed2 else 0))[..., None])
        r = (P-base)*valid[..., None]
        zero = np.zeros_like(w1)
        X = [w1*T1[:, 0:1]] if fixed1 else [w1, zero]
        Y = [w1*T1[:, 1:2]] if fixed1 else [zero, w1]
        X += [-w2*T2[:, 0:1]] if fixed2 else [w2, zero]
        Y += [-w2*T2[:, 1:2]] if fixed2 else [zero, w2]
        X, Y = np.stack(X, -1), np.stack(Y, -1)
        M = np.einsum('ski,skj->sij', X, X)+np.einsum('ski,skj->sij', Y, Y)
        v = np.einsum('ski,sk->si', X, r[..., 0])+np.einsum('ski,sk->si', Y, r[..., 1])
        x, ok = _solve_normal_batch(M, v)
        if fixed1:
            cp1, x = a+T1*x[:, 0:1], x[:, 1:]
        else:
            cp1, x = x[:, :2], x[:, 2:]
        cp2 = b-T2*x[:, 0:1] if fixed2 else x[:, :2]
        d1, d2 = cp1-a, b-cp2
        if fixed1:
            ok &= ~(d1[:, 0]*T1[:, 0]+d1[:, 1]*T1[:, 1] <= total*.02)
        if fixed2:
            ok &= ~(d2[:, 0]*T2[:, 0]+d2[:, 1]*T2[:, 1] <= total*.02)
        ok &= ~(np.maximum(np.hypot(d1[:, 0], d1[:, 1]), np.hypot(d2[:, 0], d2[:, 1])) > total*1.4)
        return ok, cp1, cp2

    def _fit_jobs(self, poly, tang, jobs):
        """fit_span for each job (sample indices, t1, t2) of one design, with
        its tangents as headings; jobs of a similar sample count share a batch."""
        if not jobs:
            return []
        poly, tang = np.asarray(poly, dtype=float)[:, :2], np.asarray(tang, dtype=float)
        order = sorted(range(len(jobs)), key=lambda k: len(jobs[k][0]))
        out = [None]*len(jobs)
        start = 0
        while start < len(order):
            # As many as fit in a batch, padded to the longest of them.
            end = start+1
            while end < len(order) and (end+1-start)*len(jobs[order[end]][0]) <= self.BATCH:
                end += 1
            group = order[start:end]
            K = len(jobs[group[-1]][0])
            index = np.array([jobs[k][0]+[jobs[k][0][-1]]*(K-len(jobs[k][0])) for k in group])
            fits = self.fit_spans(poly[index], np.array([len(jobs[k][0]) for k in group]),
                                  [jobs[k][1] for k in group], [jobs[k][2] for k in group], tang[index])
            for k, f in zip(group, fits):
                out[k] = f
            start = end
        return out

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
        # Every span the search below may use: which ones depends only on
        # the design (length, turn, forced joins), so they are all fitted
        # first, together (fit_spans), and the search reads the results.
        tried, jobs = {}, []
        for jj in range(1, len(candidates)):
            j = candidates[jj]
            tried[jj] = []
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
                tried[jj].append((ii, len(jobs)))
                jobs.append((picks, None if i in loose else tang[i], None if j in loose else tang[j]))
        fits = self._fit_jobs(poly, tang, jobs)
        best = {0: (0, 0.0, None, None)}
        for jj in range(1, len(candidates)):
            j = candidates[jj]
            options = []
            for ii, job in tried[jj]:
                i = candidates[ii]
                span = lengths[j]-lengths[i]
                curve, error, bend = fits[job]
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

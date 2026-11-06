"""The curve fitter works on whole arrays (numpy): drawing one design fits tens
of thousands of spans, which took minutes one sample at a time. It must give
what the plain version below gives (the fitter as it was), span for span."""
import math
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sample_geometry as sg  # noqa: E402
from sample_geometry import add, dist, dot, mul, segment_distance, sub, unit  # noqa: E402


def least_squares(rows, rhs):
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


def plain_fit_span(curve, samples, t1, t2, headings=None):
    """NativeCurve.fit_span one sample at a time, as it was before numpy."""
    a, b = samples[0], samples[-1]
    lengths = sg.arc_lengths(samples)
    total = lengths[-1]
    if total < 1e-6:
        return None, math.inf, math.inf
    ts = [s/total for s in lengths]
    fitted = None
    for iteration in range(6):
        rows, rhs = [], []
        for p, t in zip(samples, ts):
            w0, w1, w2, w3 = curve.weights(t)
            r = sub(p, add(mul(a, w0+(w1 if t1 else 0)), mul(b, w3+(w2 if t2 else 0))))
            for axis in (0, 1):
                row = [w1*t1[axis]] if t1 else [w1*(axis == 0), w1*(axis == 1)]
                row += [-w2*t2[axis]] if t2 else [w2*(axis == 0), w2*(axis == 1)]
                rows.append(row)
                rhs.append(r[axis])
        x = least_squares(rows, rhs)
        if x is None:
            return None, math.inf, math.inf
        if t1:
            cp1, x = add(a, mul(t1, x[0])), x[1:]
        else:
            cp1, x = (x[0], x[1]), x[2:]
        cp2 = sub(b, mul(t2, x[0])) if t2 else (x[0], x[1])
        if t1 and dot(sub(cp1, a), t1) <= total*.02 or t2 and dot(sub(b, cp2), t2) <= total*.02:
            return None, math.inf, math.inf
        if max(dist(a, cp1), dist(b, cp2)) > total*1.4:
            return None, math.inf, math.inf
        fitted = (a, cp1, cp2, b)
        if iteration == 5:
            break
        updated = [0.0]
        for p, t in zip(samples[1:-1], ts[1:-1]):
            e = 1e-4
            here = curve.point(fitted, t)
            ahead, behind = curve.point(fitted, min(1, t+e)), curve.point(fitted, max(0, t-e))
            d = mul(sub(ahead, behind), 1/(2*e))
            dd = mul(add(sub(ahead, mul(here, 2)), behind), 1/(e*e))
            r = sub(here, p)
            den = dot(d, d)+dot(r, dd)
            updated.append(min(1.0, max(0.0, t-dot(r, d)/den if abs(den) > 1e-9 else t)))
        updated.append(1.0)
        if any(x >= y for x, y in zip(updated, updated[1:])):
            break
        ts = updated
    error = max(dist(curve.point(fitted, t), p) for p, t in zip(samples, ts))
    for q in [curve.point(fitted, k/24) for k in range(25)]:
        error = max(error, min(segment_distance(q, p, r) for p, r in zip(samples, samples[1:])))
    turn = 0.0
    if headings:
        for h, t in zip(headings, ts):
            e = 1e-4
            d = unit(sub(curve.point(fitted, min(1, t+e)), curve.point(fitted, max(0, t-e))))
            turn = max(turn, math.degrees(math.acos(max(-1.0, min(1.0, dot(d, h))))))
    return fitted, error, turn


def design():
    """A wavy open cord, the kind a knot's steps are drawn from."""
    points = [(100+60*k, 300+90*math.sin(k*0.9)+40*math.cos(k*2.1)) for k in range(16)]
    return sg.spline(points, spacing=4.0)


def test_numpy_spans_match_the_plain_fitter():
    curve = sg.NativeCurve(1.0, 2.0, 2.0)
    poly = design()
    tang = sg.tangents(poly, False)
    random.seed(7)
    failed = worst = 0
    for _ in range(400):
        i = random.randrange(len(poly)-3)
        j = min(len(poly)-1, i+random.randrange(2, 230))
        picks = list(range(i, j+1, max(1, (j-i)//48)))
        if picks[-1] != j:
            picks.append(j)
        t1 = None if random.random() < 0.15 else tang[i]
        t2 = None if random.random() < 0.15 else tang[j]
        args = ([poly[k] for k in picks], t1, t2, [tang[k] for k in picks])
        new, old = curve.fit_span(*args), plain_fit_span(curve, *args)
        assert (new[0] is None) == (old[0] is None)
        if new[0] is None:
            failed += 1
            continue
        worst = max(worst, max(dist(p, q) for p, q in zip(new[0], old[0])), abs(new[1]-old[1]))
        assert abs(new[2]-old[2]) < 1e-3  # degrees: acos is steep next to 0
    assert worst < 1e-6 and failed < 400


def test_fit_picks_the_same_joins_as_one_span_at_a_time(monkeypatch):
    poly = design()
    batched = sg.NativeCurve(1.0, 2.0, 2.0).fit(poly, False, 1.5, min_length=36, free_ends=True)
    plain = sg.NativeCurve(1.0, 2.0, 2.0)
    monkeypatch.setattr(sg.NativeCurve, "_fit_jobs", lambda self, poly, tang, jobs: [
        plain_fit_span(self, [poly[k] for k in picks], t1, t2, [tang[k] for k in picks]) for picks, t1, t2 in jobs])
    one_by_one = plain.fit(poly, False, 1.5, min_length=36, free_ends=True)
    assert [(i, j) for i, j, _ in batched] == [(i, j) for i, j, _ in one_by_one]
    for (_, _, a), (_, _, b) in zip(batched, one_by_one):
        assert max(dist(p, q) for p, q in zip(a, b)) < 1e-6

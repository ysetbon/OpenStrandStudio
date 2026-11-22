"""smooth.py <design.json> <out.json> [sigma_px]: smooth each traced cord (from trace.py) before `openstrand draw`.

Each cord's polyline is resampled to 1 px, smoothed with a Gaussian of sigma_px along its length
(default 3) and thinned to evenly spaced points about 12 px apart (further apart for a very long
cord: the fitter takes at most 400 points per cord). An open cord keeps its two ends. A closed cord
is treated as a ring, so the place where it closes is spaced like every other point.
"""
import json
import sys

import numpy as np
from scipy.ndimage import gaussian_filter1d

d = json.load(open(sys.argv[1]))
sig = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
out = []
for c in d['cords']:
    p = np.array(c['points'], float)
    if len(p) < 3:
        continue
    closed = bool(c.get('closed'))
    if closed:
        p = np.vstack([p, p[:1]])                       # walk the closing segment too
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    t = np.arange(0, seg[-1], 1.0)
    q = np.c_[np.interp(t, seg, p[:, 0]), np.interp(t, seg, p[:, 1])]
    mode = 'wrap' if closed else 'nearest'
    q = np.c_[gaussian_filter1d(q[:, 0], sig, mode=mode), gaussian_filter1d(q[:, 1], sig, mode=mode)]
    n = int(min(390, max(4, round(len(q) / 12))))
    if closed:
        idx = np.round(np.arange(n) * len(q) / n).astype(int)      # n points evenly round the ring
        q = q[idx]
    else:
        idx = np.round(np.linspace(0, len(q) - 1, n + 1)).astype(int)
        q = q[idx]
        q[0], q[-1] = p[0], p[-1]
    c['points'] = [[round(x), round(y)] for x, y in q]
    if not c.get('pattern'):
        c.pop('pattern', None)
    out.append(c)
d['cords'] = out[:12]
json.dump(d, open(sys.argv[2], 'w'))
print(len(out), 'cords')

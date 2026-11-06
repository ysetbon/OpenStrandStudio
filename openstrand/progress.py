"""How far a long tool call has got, for the person watching it.

A tool that takes a while (tie_knot, draw_design) is handed a Progress and
calls it as it works:

    progress(0.4, 'draw_step', frame=picture, step=3, steps=6)

with the fraction of the whole call done (0 to 1, or None when it cannot
tell; it never goes back), the
stage it is in (a short key the app translates, with its numbers) and, when
it has one, the cords it is working on. Progress turns that into
'tool_progress' events: at most one every EVERY seconds (at once when the
stage changes), with a picture of the cords at most once every FRAME_EVERY
seconds, so the person sees the knot laid out, pulled tight and drawn step by
step instead of a clock that only counts.
"""
import math
import time

import numpy as np

EVERY = 0.25          # seconds between events
FRAME_EVERY = 1.0     # seconds between pictures
POINTS = 160          # points kept per cord in a picture
OVER_REACH = 1.3      # widths of the over-part redrawn either side of a crossing


class Progress:
    """Reports progress through emit(event). Calls are cheap: a picture is
    only made when one is due, so frame may be a function giving it."""

    def __init__(self, emit, clock=time.monotonic):
        self.emit = emit
        self.clock = clock
        self.fraction = None  # None until the tool can tell: the bar then just shows it is working
        self.stage, self.numbers = None, {}
        self.sent = self.framed = None

    def __call__(self, fraction=None, stage=None, frame=None, **numbers):
        """fraction: of the whole call; stage and numbers: what it is doing;
        frame: a picture (see picture()) or a function giving one."""
        now = self.clock()
        if fraction is not None and math.isfinite(fraction):
            self.fraction = max(self.fraction or 0.0, min(1.0, max(0.0, float(fraction))))
        changed = stage is not None and (stage, numbers) != (self.stage, self.numbers)
        if stage is not None:
            self.stage, self.numbers = stage, dict(numbers)
        if not changed and self.sent is not None and now - self.sent < EVERY:
            return
        event = {'type': 'tool_progress', 'stage': self.stage, **self.numbers,
                 'fraction': None if self.fraction is None else round(self.fraction, 4)}
        if frame is not None and (changed or self.framed is None or now - self.framed >= FRAME_EVERY):
            made = frame() if callable(frame) else frame
            if made:
                event['frame'] = made
                self.framed = now
        self.sent = now
        self.emit(event)

    def part(self, start, end, stage=None, **numbers):
        """A piece of the bar, from start to end: a function taking the
        fraction of that piece done (and a frame), for the code doing it."""
        def report(fraction=0.0, frame=None):
            self(start + (end - start) * fraction, stage, frame, **numbers)
        return report


def picture(cords, width, color, closed=None):
    """A small picture of cords, as the app's progress row draws it: each
    cord's centerline (at most POINTS points, rounded to 0.1 px) with its
    color (color: one for all, or one per cord) and whether it is closed,
    and, where the cords carry heights (x, y, height), the over part of
    every crossing, redrawn on top. None when there is nothing to draw."""
    colors = [color] * len(cords) if isinstance(color, str) else list(color)
    flags = list(closed) if closed is not None else [False] * len(cords)
    lines = []
    for cord, hue, ring in zip(cords, colors, flags):
        c = np.asarray(cord, dtype=float)
        if c.ndim != 2 or len(c) < 2:
            continue
        step = max(1, int(math.ceil(len(c) / POINTS)))
        kept = c[::step]
        if step > 1 and not np.array_equal(kept[-1], c[-1]):
            kept = np.vstack([kept, c[-1]])
        lines.append((kept, hue, bool(ring)))
    if not lines:
        return None
    overs = []
    if all(c.shape[1] >= 3 for c, _, _ in lines):
        from .invariants import crossings
        shown = [c for c, _, _ in lines]
        arcs = [np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(c[:, :2], axis=0).T))]) for c in shown]
        reach = OVER_REACH * float(width)
        for x in crossings(shown, [ring for _, _, ring in lines]):
            k = x['cords'][x['over']]
            at, s = x['positions'][x['over']], arcs[k]
            inside = (s > at - reach) & (s < at + reach)
            ends = [np.array([np.interp(v, s, shown[k][:, i]) for i in (0, 1)])
                    for v in (max(at - reach, 0.0), min(at + reach, s[-1]))]
            piece = np.vstack([ends[0], shown[k][inside, :2], ends[1]])
            overs.append({'cord': int(k), 'points': np.round(piece, 1).tolist()})
    return {'cords': [{'points': np.round(c[:, :2], 1).tolist(), 'color': hue, 'closed': ring}
                      for c, hue, ring in lines],
            'overs': overs, 'width': round(float(width), 1)}

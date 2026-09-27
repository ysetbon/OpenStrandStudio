"""Rebuild the additional samples using the application's own serializer.

Run from any directory: python scripts/generate_creative_samples.py
Optional --preview DIR renders the reloaded projects and a contact sheet.
"""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from PyQt5.QtCore import QPointF, QLineF, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication
from strand import Strand
from attached_strand import AttachedStrand
from masked_strand import MaskedStrand
from save_load_manager import serialize_project_state, load_strands_from_data
sys.path.insert(0, str(ROOT / 'scripts'))
from sample_geometry import (NativeCurve, spline, parametric, resample, dist,
                             polyline_crossings, stroke, arc_lengths, tangents)

TAU = math.tau
PALETTE = ['#257d98', '#e5a13b', '#d56272', '#6554a4', '#399780', '#b76c40']
# Match StrandDrawingCanvas's live defaults, which overwrite Strand's older
# constructor defaults when a project is loaded in the application.
CURVE_SETTINGS = dict(control_point_base_fraction=1.0, distance_multiplier=2.0,
                      curve_response_exponent=2.0)
_CURVE_FITS = {}
NATIVE = NativeCurve(CURVE_SETTINGS['control_point_base_fraction'],
                     CURVE_SETTINGS['distance_multiplier'],
                     CURVE_SETTINGS['curve_response_exponent'])


def fit_cubics(points, tolerance=9, protected=()):
    """Minimum number of cubic spans at the supplied design landmarks.

    Fit the original native curves with freely placed start/end handles and a
    bounded approximation error. Dynamic programming avoids extra attachments.
    The color-change landmark remains an endpoint.
    """
    points = [QPointF(*p) for p in points]
    cache_key = tuple((p.x(),p.y()) for p in points)
    original = []
    for i, (a, b) in enumerate(zip(points, points[1:])):
        before = points[i-1] if i else a
        after = points[i+2] if i+2 < len(points) else b
        original.append((a, a+(b-before)/6, b-(after-a)/6, b))
    if tolerance == 0:
        return [(curve,i,i+1) for i,curve in enumerate(original)]

    def dot(a, b):
        return a.x()*b.x()+a.y()*b.y()

    # AttachedStrand.get_path uses two cubic halves with an implicit center
    # between the handles, not the usual one-cubic Bernstein interpretation.
    base = CURVE_SETTINGS['control_point_base_fraction']
    boost = CURVE_SETTINGS['distance_multiplier']
    exponent = CURVE_SETTINGS['curve_response_exponent']
    f1 = ((.1+base*.2)*boost)**(1/exponent)
    f2 = ((.05+base*.1)*boost)**(1/exponent)

    def weights(t):
        if t <= .5:
            v = 2*t; u = 1-v
            return (u**3+3*u*u*v*(1-f1),
                    3*u*u*v*f1+3*u*v*v*(1+f2)/2+v**3/2,
                    3*u*v*v*(1-f2)/2+v**3/2, 0)
        v = 2*t-1; u = 1-v
        return (0,u**3/2+3*u*u*v*(1-f2)/2,
                u**3/2+3*u*u*v*(1+f2)/2+3*u*v*v*f2,
                3*u*v*v*(1-f2)+v**3)

    def value(c, t):
        return sum((p*w for p,w in zip(c,weights(t))),QPointF())

    def fit(lo, hi):
        if hi == lo+1:
            return original[lo], 0
        if any(i in protected for i in range(lo,hi)):
            return None, math.inf
        key = (cache_key,lo,hi)
        if key in _CURVE_FITS:
            return _CURVE_FITS[key]
        samples = [value(c, k/12) for c in original[lo:hi] for k in range(12)] + [points[hi]]
        distances = [0]
        for a, b in zip(samples, samples[1:]):
            distances.append(distances[-1]+math.hypot(b.x()-a.x(), b.y()-a.y()))
        ts = [d/distances[-1] for d in distances]
        a, b = points[lo], points[hi]
        tangent1 = original[lo][1]-a
        tangent2 = b-original[hi-1][2]
        tangent1 /= math.hypot(tangent1.x(),tangent1.y())
        tangent2 /= math.hypot(tangent2.x(),tangent2.y())
        for iteration in range(5):
            aa = ab = bb = 0
            ar = br = 0
            for p, t in zip(samples, ts):
                w0,w1,w2,w3 = weights(t)
                residual = p-a*(w0+w1)-b*(w2+w3)
                u,v = tangent1*w1,-tangent2*w2
                aa += dot(u,u); ab += dot(u,v); bb += dot(v,v)
                ar += dot(residual,u); br += dot(residual,v)
            det = aa*bb-ab*ab
            if abs(det) < 1e-9:
                return None, math.inf
            alpha,beta = (ar*bb-br*ab)/det,(br*aa-ar*ab)/det
            if min(alpha,beta) <= 0:
                return None, math.inf
            cp1, cp2 = a+tangent1*alpha,b-tangent2*beta
            if max(math.hypot((cp1-a).x(),(cp1-a).y()),
                   math.hypot((cp2-b).x(),(cp2-b).y())) > distances[-1]*1.5:
                return None, math.inf
            curve = (a,cp1,cp2,b)
            if iteration < 4:
                updated = [0]
                for p,t in zip(samples[1:-1],ts[1:-1]):
                    epsilon = .0001
                    here = value(curve,t)
                    ahead, behind = value(curve,t+epsilon),value(curve,t-epsilon)
                    d = (ahead-behind)/(2*epsilon)
                    dd = (ahead-here*2+behind)/(epsilon*epsilon)
                    residual = value(curve,t)-p
                    denom = dot(d,d)+dot(residual,dd)
                    tnew = t-dot(residual,d)/denom if abs(denom)>1e-9 else t
                    updated.append(max(0,min(1,tnew)))
                updated.append(1)
                if any(x>=y for x,y in zip(updated,updated[1:])):
                    break
                ts = updated
        error = max(math.hypot((value(curve,t)-p).x(),(value(curve,t)-p).y()) for p,t in zip(samples,ts))
        _CURVE_FITS[key] = (curve,error)
        return curve,error

    result = []
    midpoint = len(original)//2
    for begin,end in [(0,midpoint),(midpoint,len(original))]:
        best = {begin:(0,0,[])}
        for hi in range(begin+1,end+1):
            options = []
            for lo in range(begin,hi):
                curve,error = fit(lo,hi)
                if error <= tolerance:
                    count,total,curves = best[lo]
                    options.append((count+1,total+error,curves+[(curve,lo,hi)]))
            best[hi] = min(options,key=lambda item:item[:2])
        result.extend(best[end][2])
    return result


class Scene:
    def __init__(self, name):
        self.name, self.strands, self.groups = name, [], {}
        self.set_count = 0
        self.explicit_crossings = False
        self.cords, self.hits, self.warnings = [], [], []

    def chain(self, points, color, group, width=24, closed=False, angular=False, cubics=None):
        """A smooth interpolating spline, split into real attached strands."""
        self.set_count += 1
        points = [QPointF(*p) for p in points]
        if closed:
            points.append(QPointF(points[0]))
        chain = []
        for i, (start, end) in enumerate(zip(points, points[1:])):
            if chain:
                strand = AttachedStrand(chain[-1], start, 1)
                strand.start, strand.end = QPointF(start), QPointF(end)
                chain[-1].attached_strands.append(strand)
                chain[-1].has_circles[1] = True
                chain[-1].end_attached = True
            else:
                strand = Strand(start, end, width, QColor(color), QColor('#263446'),
                                2, self.set_count)
                strand.is_first_strand = True
            strand.layer_name = f'{self.set_count}_{i + 1}'
            before = points[i - 1] if i else (points[-2] if closed else start)
            after = points[i + 2] if i + 2 < len(points) else (points[1] if closed else end)
            strand.control_point1 = start + ((end - start) / 3 if angular else (end - before) / 6)
            strand.control_point2 = end - ((end - start) / 3 if angular else (after - start) / 6)
            if cubics is not None:
                strand.control_point1 = QPointF(cubics[i][1])
                strand.control_point2 = QPointF(cubics[i][2])
            strand.control_point2_activated = True
            strand.control_point2_shown = True
            strand.control_point_center_locked = False
            for key,value in CURVE_SETTINGS.items():
                setattr(strand,key,value)
            strand.triangle_has_moved = True
            strand.start_circle_stroke_color = QColor(0,0,0,0)
            strand.end_circle_stroke_color = QColor(0,0,0,0)
            if isinstance(strand, AttachedStrand):
                strand.update_angle_length_from_geometry()
            strand.update_shape()
            strand.update_side_line()
            chain.append(strand)
        if closed:
            first, last = chain[0], chain[-1]
            first.closed_connections = [True, False]
            last.closed_connections = [False, True]
            first.has_circles[0] = last.has_circles[1] = True
            first.knot_connections = {'start': dict(connected_strand=last, connected_end='end', is_closing_strand=False)}
            last.knot_connections = {'end': dict(connected_strand=first, connected_end='start', is_closing_strand=True)}
        self.strands.extend(chain)
        entry = self.groups.setdefault(group, dict(layers=[], main_strands=[], strands=[], control_points={}))
        entry['main_strands'].append(chain[0])
        entry['strands'].extend(chain)
        entry['layers'].extend(s.layer_name for s in chain)
        for s in chain:
            entry['control_points'][s.layer_name] = dict(control_point1=s.control_point1, control_point2=s.control_point2)
        return chain

    def knot(self, points, width=26, tolerance=None, expected=None, protected=None,
             second_color='#e8ac45'):
        """One continuous editable cord with explicit over/under crossing masks.

        Locate centerline crossings in traversal order, not by layer parity.
        This also handles crossings between attachments in the same set.
        """
        if tolerance is None:
            reference = Scene(self.name)
            reference.knot(points,width,tolerance=0,expected=False,second_color=second_color)
            protected = {i for c in reference.crossings for i in c[2:4]}
            candidates = [reference]
            for protection in [(),protected]:
                for fraction in [.9,.6,.45,.3,.225]:
                    candidate = Scene(self.name)
                    try:
                        candidate.knot(points,width,tolerance=width*fraction,
                                       expected=False,protected=protection,
                                       second_color=second_color)
                    except AssertionError:
                        continue
                    if candidate.crossing_signature == reference.crossing_signature:
                        candidates.append(candidate)
            best = min(candidates,key=lambda s:sum(not isinstance(x,MaskedStrand) for x in s.strands))
            self.__dict__.update(best.__dict__)
            attachments = sum(isinstance(x,AttachedStrand) for x in self.strands)
            print(f'{self.name}: {len(points)-2} -> {attachments} attachments; crossing order preserved',flush=True)
            return
        spans = fit_cubics(points, tolerance=tolerance, protected=protected or ())
        cubics = [c for c,_,_ in spans]
        endpoints = [cubics[0][0]]+[c[3] for c in cubics]
        chain = self.chain([(p.x(),p.y()) for p in endpoints], '#c83e4d',
                           'Complete knot', width, cubics=cubics)
        self.explicit_crossings = True
        # A second color marks the returning half without breaking attachment.
        for i, strand in enumerate(chain):
            strand.triangle_has_moved = True
            strand.start_circle_stroke_color = QColor(0, 0, 0, 0)
            strand.end_circle_stroke_color = QColor(0, 0, 0, 0)
            if spans[i][1] >= (len(points)-1)//2:
                strand.color = QColor(second_color)
            strand.update_shape()
            strand.update_side_line()
        paths = [s.get_path() for s in chain]
        sampled = [[p.pointAtPercent(k / 40) for k in range(41)] for p in paths]
        crossings = []
        for i in range(len(chain)):
            for j in range(i + 1, len(chain)):
                if not paths[i].boundingRect().intersects(paths[j].boundingRect()):
                    continue
                hits = []
                for a in range(40):
                    for b in range(40):
                        hit = QPointF()
                        kind = QLineF(sampled[i][a], sampled[i][a+1]).intersect(
                            QLineF(sampled[j][b], sampled[j][b+1]), hit)
                        if kind == QLineF.BoundedIntersection and not any(
                            math.hypot(hit.x()-h.x(), hit.y()-h.y()) < 4 for _, _, h in hits):
                            if j == i+1 and math.hypot(hit.x()-chain[i].end.x(),hit.y()-chain[i].end.y()) < width:
                                continue
                            def fraction(start,end):
                                distance = math.hypot(end.x()-start.x(),end.y()-start.y())
                                return math.hypot(hit.x()-start.x(),hit.y()-start.y())/distance if distance else 0
                            hits.append(((a+fraction(sampled[i][a],sampled[i][a+1]))/40,
                                         (b+fraction(sampled[j][b],sampled[j][b+1]))/40, hit))
                for a, b, hit in hits:
                    crossings.append((i+a, j+b, i, j, hit))
        visits = sorted((position, index, side) for index, c in enumerate(crossings)
                        for side, position in enumerate(c[:2]))
        first_over = {}
        for order, (_, index, side) in enumerate(visits):
            is_over = order % 2 == 0
            if index not in first_over:
                first_over[index] = side if is_over else 1-side
        self.crossings = crossings
        ids = {}
        self.crossing_signature = []
        for _, index, side in visits:
            ids.setdefault(index, len(ids))
            self.crossing_signature.append((ids[index], first_over[index] == side))
        masks = set()
        clear_crossings = {}
        for index, (_, _, i, j, _) in enumerate(crossings):
            over, under = (i, j) if first_over[index] == 0 else (j, i)
            # Later strands are already above earlier ones in the layer stack.
            if over < under:
                masks.add((over, under))
            else:
                clear_crossings.setdefault((under,over),[]).append(crossings[index][4])
        built_masks = {}
        for over, under in sorted(masks):
            mask = MaskedStrand(chain[over], chain[under])
            # The same two long curves can cross with opposite ordering. Erase
            # only the other crossing from this mask, preserving the long curves.
            # Erase the whole overlap component, including its stroke margin.
            # A fixed square centered on a shallow crossing truncates ribbons.
            components = mask.get_mask_path().toSubpathPolygons()
            rectangles = []
            for hit in clear_crossings.get((over,under),[]):
                component = next((p for p in components if p.containsPoint(hit,Qt.OddEvenFill)),None)
                assert component is not None, 'Cannot isolate crossing'
                r = component.boundingRect().adjusted(-4,-4,4,4)
                rectangles.append(dict(top_left=[r.left(),r.top()],top_right=[r.right(),r.top()],
                                       bottom_left=[r.left(),r.bottom()],bottom_right=[r.right(),r.bottom()]))
            mask.deletion_rectangles = rectangles
            assert not mask.get_mask_path().isEmpty(), (self.name, over, under)
            self.strands.append(mask)
            built_masks[(over,under)] = mask
        for index, (_,_,i,j,hit) in enumerate(crossings):
            if first_over[index] == 0:
                assert built_masks[(i,j)].get_mask_path().contains(hit), (self.name,'missing overpass',i,j)
            elif (i,j) in built_masks:
                assert not built_masks[(i,j)].get_mask_path().contains(hit), (self.name,'covered underpass',i,j)
        assert masks, 'A knot diagram must include real crossing masks'
        if expected is not False:
            print(f'{self.name}: {len(points)-2} -> {len(chain)-1} attachments; crossing order preserved', flush=True)

    def cord(self, poly, color, group, width, closed=False, tolerance=None,
             second_color=None, split=None, hidden_ends=()):
        """Register a designed centerline; fit() turns it into one attached chain.

        With second_color, samples after index split use that color; the
        split is a forced join so the color change sits exactly at a join.
        split='auto' and closed cords place the color change and the closing
        join under a crossing (see plan), where the attachment circle and the
        closing end line cannot show.
        """
        self.cords.append(dict(poly=poly, color=color, group=group, width=width, closed=closed,
                               tolerance=min(width*.12, .8) if tolerance is None else tolerance,
                               second_color=second_color, split=split, chain=None,
                               hidden_ends=hidden_ends))

    def dense_crossings(self):
        """Crossings of the designed centerlines, positioned by sample index."""
        hits = []
        for a, first in enumerate(self.cords):
            for b in range(a, len(self.cords)):
                second = self.cords[b]
                gap = int(first['width']/(arc_lengths(first['poly'])[-1]/(len(first['poly'])-1)))
                for u, v, point in polyline_crossings(first['poly'], second['poly'], same=a == b, gap=gap):
                    hits.append(dict(point=point, cords=(a, b), positions=(u, v)))
        return hits

    def covered_points(self, rule, c):
        """Positions where cord c passes under something, with the covering side."""
        hits = self.dense_crossings()
        out = []
        for h, first_over in zip(hits, rule(self, hits)):
            for side in (0, 1):
                if h['cords'][side] == c and first_over == (side == 1):
                    out.append((h['positions'][side], h['cords'][1-side], h['positions'][1-side], h['point']))
        return out, hits

    def plan(self, rule):
        """Hide closing joins and color changes under crossings."""
        for c, cord in enumerate(self.cords):
            if cord['closed']:
                under, hits = self.covered_points(rule, c)
                assert under, (self.name, 'a closed cord needs a crossing to hide its join under')
                # Keep the join away from its neighbours' crossings.
                def room(item):
                    return min((dist(item[3], h['point']) for h in hits if dist(item[3], h['point']) > 1), default=1e9)
                position = max(under, key=room)[0]
                poly = cord['poly'][:-1]
                k = int(round(position)) % len(poly)
                cord['poly'] = poly[k:]+poly[:k]+[poly[k]]
            if cord['split'] == 'auto':
                under, _ = self.covered_points(rule, c)
                middle = (len(cord['poly'])-1)/2
                # The covering mask includes the attachment circle, so any
                # covered crossing works; the one nearest the middle balances colors.
                cord['split'] = int(round(min(under, key=lambda u: abs(u[0]-middle))[0]))

    def fit(self):
        """Fit every registered cord, keeping joins out of all crossings."""
        for c, cord in enumerate(self.cords):
            if cord['chain'] is not None:
                continue
            poly, width = cord['poly'], cord['width']
            spacing = arc_lengths(poly)[-1]/(len(poly)-1)
            avoid = set()
            for other in self.cords:
                same = other is cord
                heading = tangents(other['poly'], other['closed'])
                own = tangents(poly, cord['closed'])
                for u, v, _ in polyline_crossings(poly, other['poly'], same=same, gap=int(width/spacing)):
                    # Overlapping strokes reach further along both strands at a
                    # shallow crossing; keep joins clear of the whole overlap.
                    a, b = own[int(u)], heading[int(v)]
                    sine = abs(a[0]*b[1]-a[1]*b[0])
                    cosine = abs(a[0]*b[0]+a[1]*b[1])
                    half = (max(width, other['width'])+8)/2
                    reach = min(half*(cosine+1)/max(sine, .2)+6, width*4)
                    for k in ([u, v] if same else [u]):
                        avoid.update(range(int(k-reach/spacing), int(k+reach/spacing)+2))
            split = cord['split']
            spans = NATIVE.fit(poly, cord['closed'], cord['tolerance'],
                               forced={split} if split is not None else (), avoid=avoid,
                               min_length=width*1.5)
            cubics = [tuple(QPointF(*p) for p in curve) for _, _, curve in spans]
            ends = [cubics[0][0]]+[q[3] for q in cubics]
            # A closed design is built as a chain whose ends meet under a
            # crossing: the covering mask hides a flat, line-free join, whereas
            # a closed attachment would draw its closing circle above the mask.
            chain = self.chain([(p.x(), p.y()) for p in ends], cord['color'], cord['group'], width,
                               cubics=cubics)
            if cord['closed']:
                chain[0].start_line_visible = False
                chain[-1].end_line_visible = False
            for side in cord['hidden_ends']:
                if side == 0:
                    chain[0].start_line_visible = False
                else:
                    chain[-1].end_line_visible = False
            for strand, (i, _, _) in zip(chain, spans):
                if cord['second_color'] and i >= split:
                    strand.color = QColor(cord['second_color'])
                strand.update_shape()
                strand.update_side_line()
            cord['chain'] = chain
            cord['spans'] = [(i, j) for i, j, _ in spans]

    def cord_of(self, strand):
        for c, cord in enumerate(self.cords):
            for k, member in enumerate(cord['chain']):
                if member is strand:
                    return c, k
        raise KeyError(strand.layer_name)

    def adjacent(self, a, b):
        (ca, ia), (cb, ib) = self.cord_of(a), self.cord_of(b)
        if ca != cb:
            return False
        n = len(self.cords[ca]['chain'])
        return abs(ia-ib) == 1 or (self.cords[ca]['closed'] and abs(ia-ib) == n-1)

    def find_crossings(self):
        """Centerline crossings of the fitted native curves, with cord positions."""
        regular = [s for s in self.strands if not isinstance(s, MaskedStrand)]
        paths = {id(s): s.get_path() for s in regular}
        samples = {id(s): [paths[id(s)].pointAtPercent(k/80) for k in range(81)] for s in regular}
        hits = []
        for x, a in enumerate(regular):
            for b in regular[x+1:]:
                if not paths[id(a)].boundingRect().adjusted(-2, -2, 2, 2).intersects(
                        paths[id(b)].boundingRect().adjusted(-2, -2, 2, 2)):
                    continue
                pa = [(p.x(), p.y()) for p in samples[id(a)]]
                pb = [(p.x(), p.y()) for p in samples[id(b)]]
                for u, v, point in polyline_crossings(pa, pb):
                    if self.adjacent(a, b):
                        joint = a.end if self.cord_of(a)[1]+1 == self.cord_of(b)[1] else a.start
                        if dist(point, (joint.x(), joint.y())) < a.width:
                            continue
                    if any(dist(point, h['point']) < 3 for h in hits):
                        continue
                    (ca, ia), (cb, ib) = self.cord_of(a), self.cord_of(b)
                    hits.append(dict(point=point, cords=(ca, cb),
                                     positions=(ia+u/80, ib+v/80), strands=(a, b)))
        return hits

    def interlace(self, rule):
        """Mask every stroke overlap so the crossing's chosen strand is on top.

        rule(scene, hits) returns, for each hit, True when its first side is over.
        """
        if any(cord['chain'] is None for cord in self.cords):
            self.plan(rule)
            self.fit()
        hits = self.find_crossings()
        over_first = rule(self, hits)
        for h, flag in zip(hits, over_first):
            h['over'] = flag
        self.hits = hits
        regular = [s for s in self.strands if not isinstance(s, MaskedStrand)]
        order = {id(s): k for k, s in enumerate(regular)}
        outlines = {id(s): stroke(s.get_path(), s.width+2*s.stroke_width) for s in regular}
        wanted, natural = {}, {}
        self.warnings = []
        for x, a in enumerate(regular):
            for b in regular[x+1:]:
                shared = outlines[id(a)].intersected(outlines[id(b)])
                if shared.isEmpty():
                    continue
                for polygon in shared.toSubpathPolygons():
                    if polygon.boundingRect().width() < 1 or polygon.boundingRect().height() < 1:
                        continue
                    centre = polygon.boundingRect().center()
                    near = [h for h in hits if polygon.containsPoint(QPointF(*h['point']), Qt.OddEvenFill)]
                    if not near:
                        near = [h for h in hits if dist(h['point'], (centre.x(), centre.y())) < a.width*1.4]
                    if not near:
                        if not self.adjacent(a, b):
                            self.warnings.append(('overlap without crossing', a.layer_name, b.layer_name,
                                                  round(centre.x()), round(centre.y())))
                        continue
                    h = min(near, key=lambda h: dist(h['point'], (centre.x(), centre.y())))
                    (ca, ia), (cb, ib) = self.cord_of(a), self.cord_of(b)

                    def gap(cord, index, side):
                        if h['cords'][side] != cord:
                            return math.inf
                        p = h['positions'][side]
                        count = len(self.cords[cord]['chain'])
                        shifts = (-count, 0, count) if self.cords[cord]['closed'] else (0,)
                        return min(0 if index <= p+d <= index+1 else min(abs(p+d-index), abs(p+d-index-1))
                                   for d in shifts)
                    a_is_first = gap(ca, ia, 0)+gap(cb, ib, 1) <= gap(ca, ia, 1)+gap(cb, ib, 0)
                    a_over = h['over'] if a_is_first else not h['over']
                    key = (id(a), id(b))
                    (wanted if a_over else natural).setdefault(key, []).append(polygon)
        for key, polygons in sorted(wanted.items(), key=lambda kv: order[kv[0][1]]):
            over = next(s for s in regular if id(s) == key[0])
            under = next(s for s in regular if id(s) == key[1])
            mask = MaskedStrand(over, under)
            rectangles = []
            components = mask.get_mask_path().toSubpathPolygons()
            for polygon in natural.get(key, []):
                centre = polygon.boundingRect().center()
                component = next((c for c in components if c.containsPoint(centre, Qt.OddEvenFill)), polygon)
                r = component.boundingRect().united(polygon.boundingRect()).adjusted(-3, -3, 3, 3)
                for keep in polygons:
                    assert not r.contains(keep.boundingRect().center()), (self.name, 'mask conflict', over.layer_name, under.layer_name)
                rectangles.append(dict(top_left=[r.left(), r.top()], top_right=[r.right(), r.top()],
                                       bottom_left=[r.left(), r.bottom()], bottom_right=[r.right(), r.bottom()]))
            mask.deletion_rectangles = rectangles
            assert not mask.get_mask_path().isEmpty(), (self.name, over.layer_name, under.layer_name)
            self.strands.append(mask)
        # A mask is painted above everything; nothing else may pass through it.
        masks = [s for s in self.strands if isinstance(s, MaskedStrand)]
        for mask in masks:
            region = mask.get_mask_path()
            for s in regular:
                if s in (mask.first_selected_strand, mask.second_selected_strand):
                    continue
                if self.adjacent(s, mask.first_selected_strand) or self.adjacent(s, mask.second_selected_strand):
                    continue
                if not region.intersected(outlines[id(s)]).isEmpty():
                    c = region.boundingRect().center()
                    self.warnings.append(('crowded crossing', mask.layer_name, s.layer_name, round(c.x()), round(c.y())))
        return hits


RED, GOLD = '#c83e4d', '#e8ac45'


def knot_cord(scene, poly, width, colors=(RED, GOLD), group='Complete knot', closed=False):
    """One woven cord; a two-color cord changes color under a crossing."""
    two = colors[1] != colors[0]
    scene.cord(poly, colors[0], group, width, closed=closed,
               second_color=colors[1] if two else None, split='auto' if two else None)


def rolling_waves(x0, y0, step=44, reach=95, crests=4):
    """A row of breaking crests: a looped trochoid, one loop between crests.

    Rows placed half a wave apart and 1.45*reach lower thread each crest
    through the loops of the row above.
    """
    start, end = math.pi/2, 3*math.pi/2+math.tau*(crests-1)
    return parametric(lambda t: (x0+step*t-reach*math.sin(t), y0+reach*math.cos(t)), start, end,
                      steps=6000)


def woven(start_over=True, tucked=()):
    """Alternate over/under along every cord at once, as parity constraints.

    Crossing k has one unknown: whether its first side is over. Consecutive
    visits along a cord must differ, which fixes the parity between their
    crossings; hidden ends and closing joins must be under. The constraints
    are solved together (union-find with parity), so cords agree with each
    other; a constraint that contradicts earlier ones is the only place a cord
    may repeat over or under. Unconstrained groups start with an over-pass.
    Cords listed in tucked pass under everything and are left out of the
    other cords' alternation.
    """
    def rule(scene, hits):
        parent = list(range(len(hits)+1))       # the last node is "under"
        parity = [0]*(len(hits)+1)
        ground = len(hits)

        def find(k):
            if parent[k] == k:
                return k, 0
            root, p = find(parent[k])
            parent[k], parity[k] = root, parity[k] ^ p
            return root, parity[k]

        def join(a, b, relation):
            (ra, pa), (rb, pb) = find(a), find(b)
            if ra == rb:
                return (pa ^ pb) == relation
            if rb == ground:
                ra, rb, pa, pb = rb, ra, pb, pa
            parent[rb], parity[rb] = ra, pa ^ pb ^ relation
            return True

        visits = {}
        for k, h in enumerate(hits):
            tuck = [side for side in (0, 1) if h['cords'][side] in tucked]
            if tuck:
                join(k, ground, tuck[0])       # the tucked side is under
                continue
            for side in (0, 1):
                visits.setdefault(h['cords'][side], []).append((h['positions'][side], k, side))
        for c in visits:
            visits[c].sort()
        # Anchors first: hidden starts, hidden ends and closing joins pass under.
        for c, cord in enumerate(scene.cords):
            if c not in visits:
                continue
            ends = set(cord.get('hidden_ends', ()))
            if 0 in ends:
                _, k, side = visits[c][0]
                join(k, ground, side)
            if 1 in ends:
                _, k, side = visits[c][-1]
                join(k, ground, side)
        scene.woven_conflicts = 0
        for c in sorted(visits):
            seq = visits[c]
            pairs = list(zip(seq, seq[1:]))
            if scene.cords[c]['closed'] and len(seq) > 1:
                pairs.append((seq[-1], seq[0]))
            for (_, k1, s1), (_, k2, s2) in pairs:
                if k1 != k2 and not join(k1, k2, 1 ^ s1 ^ s2):
                    scene.woven_conflicts += 1
        # Closing joins last: plan() moves a join to a crossing its cord passes
        # under, so this only picks the phase of an otherwise free cord.
        for c, cord in enumerate(scene.cords):
            if cord['closed'] and c in visits:
                length = len(cord['chain']) if cord.get('chain') else len(cord['poly'])-1
                _, k, side = min(visits[c], key=lambda v: min(v[0], length-v[0]))
                join(k, ground, side)          # over = x ^ side should be 0
        # x_k = parity to its root; roots other than ground are free: orient
        # each free group so the first visit of its lowest cord is over.
        values = {}
        for c in sorted(visits):
            _, k, side = visits[c][0]
            root, p = find(k)
            if root != ground and root not in values:
                values[root] = (1 ^ side ^ p) if start_over else (side ^ p)
        values[ground] = 0
        out = []
        for k in range(len(hits)):
            root, p = find(k)
            # ground carries "under"; x relative to ground: over-first = p ^ value
            out.append(bool(p ^ values.get(root, 0)))
        return out
    return rule


def checkerboard(laces):
    """Each lace alternates over/under; neighbouring laces start opposite."""
    def rule(scene, hits):
        over = [None]*len(hits)
        for order, lace in enumerate(laces):
            mine = sorted((h['positions'][side], k, side) for k, h in enumerate(hits)
                          for side in (0, 1) if h['cords'][side] == lace)
            for n, (_, k, side) in enumerate(mine):
                lace_over = (order+n) % 2 == 0
                over[k] = lace_over if side == 0 else not lace_over
        return [bool(o) for o in over]
    return rule


def mirror_knot(half, centre_x):
    """A symmetric cord: the half, then its mirror image traversed backwards."""
    mirrored = [(2*centre_x-x, y) for x, y in reversed(half)]
    return half+mirrored[1:]


def polar(centre, radius, degrees):
    a = math.radians(degrees)
    return centre[0]+radius*math.cos(a), centre[1]+radius*math.sin(a)


def eared_knot(centre, base, ears, tail, spread=16, step=3, tail_gap=22):
    """Ears around a star-woven centre; position 0 (straight down) holds the tails.

    ears maps a position (0..n-1, clockwise from the bottom) to its ear length.
    The cord visits positions in star order, so the chords between ears weave
    through the centre, and each ear ends in a round bulb.
    """
    n = len(ears)+1
    angle = lambda k: 90+360*k/n
    cx, cy = centre
    points = [(cx-tail_gap, cy+base+tail), (cx-tail_gap, cy+base+tail*.55),
              polar(centre, base*1.05, angle(0)+spread)]
    for k in [(i*step) % n for i in range(1, n)]:
        length, theta = ears[k], angle(k)
        # A round bulb at the ear's end, entered and left through the base.
        bulb = min(length*.42, 80)
        middle = polar(centre, base+length-bulb, theta)
        points.append(polar(centre, base, theta-spread))
        for turn in (-115, -60, 0, 60, 115):
            points.append(polar(middle, bulb, theta+turn))
        points.append(polar(centre, base, theta+spread))
    points += [polar(centre, base*1.05, angle(0)-spread),
               (cx+tail_gap, cy+base+tail*.55), (cx+tail_gap, cy+base+tail)]
    return spline(points)


def heart_outline(centre, offset_by=0.0, lobe_gap=125, lobe=135, depth=320, tip=78, dip=74):
    """A heart built from arcs and tangent lines, grown outward by offset_by.

    Two lobe circles, a rounded tip below and a fillet in the top notch. Every
    radius changes by the offset (the fillet in the opposite sense), so hearts
    with different offsets are exactly parallel ribbons.
    """
    cx, cy = centre
    r1, r2, rf = lobe+offset_by, tip+offset_by, dip-offset_by
    right, low = (cx+lobe_gap, cy), (cx, cy+depth)
    # Outer tangent between the right lobe and the tip circle.
    dx, dy = right[0]-low[0], right[1]-low[1]
    length = math.hypot(dx, dy)
    phi, theta = math.atan2(dy, dx), math.acos((r2-r1)/length)
    normal = max(((math.cos(phi+sg*theta), math.sin(phi+sg*theta)) for sg in (1, -1)),
                 key=lambda n: n[0])
    side = math.atan2(normal[1], normal[0])              # angle on both circles
    fy = cy-math.sqrt((r1+rf)**2-lobe_gap**2)             # fillet centre
    notch = math.atan2(fy-cy, cx-right[0])                # right lobe meets fillet
    points = []

    def arc(centre, radius, a0, a1, steps=90):
        points.extend((centre[0]+radius*math.cos(a0+(a1-a0)*k/steps),
                       centre[1]+radius*math.sin(a0+(a1-a0)*k/steps)) for k in range(steps+1))
    # Clockwise on screen from the tip: right side, right lobe, notch, left lobe, left side.
    arc(low, r2, math.pi/2, side)
    arc(right, r1, side, notch+(-math.tau if notch > side else 0))
    fillet_a = math.atan2(cy-fy, right[0]-cx)
    arc((cx, fy), rf, fillet_a, math.pi/2)
    # The left half mirrors the right half; the ring ends where it began.
    ring = points+[(2*cx-x, y) for x, y in reversed(points[:-1])]
    return resample(ring, 2.0)


def four_leaf_clover(centre, radius, ratio=.6, dent=.2, width=.3):
    """Four interlocking leaves (a closed curve with eight crossings).

    E^(3it) + ratio*E^(-it) gives four round lobes that each pass through both
    neighbours; each lobe tip is pulled in to make a heart-shaped leaf.
    """
    ring = []
    for k in range(2400):
        t = math.tau*k/2400
        z = (complex(math.cos(3*t), math.sin(3*t))+ratio*complex(math.cos(t), -math.sin(t)))
        z *= complex(math.cos(math.pi/4), math.sin(math.pi/4))
        phase = math.atan2(z.imag, z.real)
        off_axis = min(abs((phase-math.radians(a)+math.pi) % math.tau-math.pi) for a in (45, 135, 225, 315))
        z *= 1-dent*math.exp(-(off_axis/width)**2)*(abs(z)/(1+ratio))**6
        ring.append(z)
    scale = radius/max(abs(z) for z in ring)
    ring = [(centre[0]+z.real*scale, centre[1]+z.imag*scale) for z in ring]
    return resample(ring+[ring[0]], 2.0)


def scenes(only=None):
    def wanted(name):
        return only is None or name in only

    if wanted('woven_heart'):
        s = Scene('woven_heart')
        centre = (600, 300)
        for offset_by, color in [(42, '#cc526c'), (0, '#e799a5'), (-42, '#934e83')]:
            s.cord(heart_outline(centre, offset_by), color, 'Heart ribbons', 24, closed=True)
        laces = []
        for y in (330, 430, 530):
            laces.append(len(s.cords))
            s.cord(spline([(220, y+38), (450, y-12), (750, y+12), (980, y-38)]),
                   PALETTE[1], 'Gold lacing', 18)
        s.interlace(checkerboard(laces))
        yield s

    if wanted('tidal_waves'):
        s = Scene('tidal_waves')
        # The sun rises behind the top row, crossing its third crest.
        s.cord(parametric(lambda t: (751+110*math.cos(t), 180+110*math.sin(t)), 0, math.tau,
                          closed=True), GOLD, 'Sun', 26, closed=True)
        for n, color in enumerate(['#205f88', '#278baa', '#49b4b7']):
            s.cord(rolling_waves(60+n*44*math.pi, 330+n*1.45*95), color, f'Wave row {n+1}', 26)
        s.interlace(woven())
        yield s

    if wanted('chinese_double_coin'):
        s = Scene('chinese_double_coin')
        cx, cy = 600, 470
        half = [(-205, 330), (-150, 205), (-55, 75), (70, -15), (205, -25),
                (300, 45), (305, 160), (215, 235), (80, 235), (-45, 160),
                (-125, 40), (-150, -80), (-122, -180), (-55, -236), (0, -246)]
        points = mirror_knot([(cx+x, cy+y) for x, y in half], cx)
        knot_cord(s, spline(points), 28)
        s.interlace(woven())
        yield s

    if wanted('chinese_cloverleaf'):
        s = Scene('chinese_cloverleaf')
        centre = (600, 400)
        leaves = four_leaf_clover(centre, 290)
        knot_cord(s, leaves, 24, colors=(RED, RED), group='Leaves', closed=True)
        # The gold stem starts hidden under the centre square and tucks
        # under the leaves wherever it meets them.
        edge = min((p for p in leaves if 440 < p[1] < 520), key=lambda p: dist(p, (590, 470)))
        # The bends make it cross each leaf strand at 50 degrees or more.
        stem = spline([(edge[0], edge[1]-7), (640, 570), (660, 690), (700, 820), (760, 880)])
        s.cord(stem, GOLD, 'Stem', 24, hidden_ends=(0,))
        s.interlace(woven(tucked={1}))
        yield s

    if wanted('chinese_pan_chang'):
        # Unchanged geometry from the first collection; the whole cord is red.
        s = Scene('chinese_pan_chang')
        s.knot([(300, 750), (310, 650), (350, 570), (830, 570),
                (910, 530), (830, 490), (370, 490), (290, 450),
                (370, 410), (830, 410), (910, 370), (830, 330), (440, 330),
                (350, 265), (370, 180), (440, 210),
                (440, 630), (480, 710), (520, 630), (520, 230),
                (560, 150), (600, 230), (600, 630), (640, 710), (680, 630),
                (680, 250), (690, 150), (750, 100)], 24, second_color=RED)
        yield s

    if wanted('chinese_good_luck'):
        s = Scene('chinese_good_luck')
        big, small = 235, 120
        # This base keeps crossings 50 apart and every other pass 40 apart.
        knot_cord(s, eared_knot((600, 400), 190, {1: small, 2: big, 3: small, 4: big,
                                                  5: small, 6: big, 7: small}, 260), 22)
        s.interlace(woven())
        yield s


def validate(data):
    curve_settings = CURVE_SETTINGS
    canvas = SimpleNamespace(default_shadow_color=None, shadow_enabled=False, _suppress_repaint=True,
                             **curve_settings,
                             update=lambda: None, selected_strand=None)
    loaded, groups, *_ = load_strands_from_data(data, canvas)
    assert len(loaded) == len(data['strands']) and all(loaded)
    assert len({s.layer_name for s in loaded}) == len(loaded)
    assert any(isinstance(s, AttachedStrand) for s in loaded)
    lookup = {s.layer_name: s for s in loaded}
    for s in loaded:
        if isinstance(s, AttachedStrand):
            assert s.start == (s.parent.start if s.attachment_side == 0 else s.parent.end)
            assert s in s.parent.attached_strands
            assert abs(s.length - math.hypot(s.end.x() - s.start.x(), s.end.y() - s.start.y())) < .001
        if isinstance(s, MaskedStrand):
            assert not s.get_mask_path().isEmpty()
    for g in groups.values():
        assert all(n in lookup for n in g['strands'] + g['main_strands'])
    for original, strand in zip(data['strands'], loaded):
        if original['type'] != 'MaskedStrand':
            for p, key in [(strand.start, 'start'), (strand.end, 'end')]:
                assert abs(p.x() - original[key]['x']) < .001 and abs(p.y() - original[key]['y']) < .001
            for p,saved in zip((strand.control_point1,strand.control_point2), original['control_points']):
                assert abs(p.x()-saved['x']) < .001 and abs(p.y()-saved['y']) < .001
    return loaded


class AppPreview:
    """Capture reloaded samples in an isolated real MainWindow (with shadows)."""

    def __init__(self):
        # Fresh settings: never read or write the user's own configuration.
        os.environ['APPDATA'] = tempfile.mkdtemp(prefix='oss_sample_preview_')
        cwd = os.getcwd()
        os.chdir(ROOT / 'src')
        try:
            from main_window import MainWindow
            self.window = MainWindow()
        finally:
            os.chdir(cwd)
        self.window.resize(1500, 1100)
        self.window.show()

    def capture(self, data, path):
        from save_load_manager import apply_project_state
        apply_project_state(self.window.canvas, data)
        canvas = self.window.canvas
        canvas.set_mode('view')
        canvas.show_grid = canvas.show_control_points = canvas.should_draw_names = False
        bounds = canvas.get_bounding_rect()
        canvas.zoom_factor = min((canvas.width()-60)/bounds.width(),
                                 (canvas.height()-60)/bounds.height(), 1.4)
        canvas.pan_offset_x = (canvas.width()/2-bounds.center().x())*canvas.zoom_factor
        canvas.pan_offset_y = (canvas.height()/2-bounds.center().y())*canvas.zoom_factor
        for _ in range(3):
            QApplication.processEvents()
        assert canvas.grab().save(str(path))

    def close(self):
        self.window._confirm_close_with_dirty_tabs = lambda *a, **k: True
        self.window.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--only', nargs='*')
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    canvas = SimpleNamespace(selected_strand=None, shadow_enabled=True, show_control_points=False)
    tiles, preview = [], None
    for scene in scenes(args.only):
        data = serialize_project_state(scene.strands, scene.groups, canvas)
        assert len(data['strands']) == len(scene.strands)
        path = ROOT / 'src' / 'samples' / (scene.name + '.json')
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        loaded = validate(json.loads(path.read_text(encoding='utf-8')))
        if args.preview:
            args.preview.mkdir(parents=True, exist_ok=True)
            preview = preview or AppPreview()
            preview.capture(json.loads(path.read_text(encoding='utf-8')), args.preview / (scene.name + '.png'))
            tiles.append(scene.name.replace('_', ' ').title())
        for warning in scene.warnings:
            print('  WARNING', *warning)
        print(f'{scene.name}: {len(loaded)} layers, {sum(isinstance(s, MaskedStrand) for s in loaded)} masks, {len(scene.groups)} groups')
    if preview:
        preview.close()
    if tiles:
        # Pillow also works on Qt offscreen installations without font support.
        from PIL import Image, ImageDraw, ImageFont
        sheet = Image.new('RGB', (1440, math.ceil(len(tiles)/3)*520), 'white')
        draw = ImageDraw.Draw(sheet)
        try:
            font = ImageFont.truetype('arial.ttf', 22)
        except OSError:
            font = ImageFont.load_default()
        for i, title in enumerate(tiles):
            x, y = (i % 3) * 480, (i // 3) * 520
            with Image.open(args.preview / (title.lower().replace(' ', '_') + '.png')) as tile:
                sheet.paste(tile.convert('RGB').resize((480, 480), Image.Resampling.LANCZOS), (x, y))
            draw.text((x + 240, y + 498), title, font=font, fill='#263446', anchor='mm')
        sheet.save(args.preview / 'contact_sheet.png')


if __name__ == '__main__':
    main()

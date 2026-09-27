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
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from PyQt5.QtCore import QPointF, QLineF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPathStroker
from PyQt5.QtWidgets import QApplication
from strand import Strand
from attached_strand import AttachedStrand
from masked_strand import MaskedStrand
from save_load_manager import serialize_project_state, load_strands_from_data

TAU = math.tau
PALETTE = ['#257d98', '#e5a13b', '#d56272', '#6554a4', '#399780', '#b76c40']
# Match StrandDrawingCanvas's live defaults, which overwrite Strand's older
# constructor defaults when a project is loaded in the application.
CURVE_SETTINGS = dict(control_point_base_fraction=1.0, distance_multiplier=2.0,
                      curve_response_exponent=2.0)
_CURVE_FITS = {}


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

    def knot(self, points, width=26, tolerance=None, expected=None, protected=None):
        """One continuous editable cord with explicit over/under crossing masks.

        Locate centerline crossings in traversal order, not by layer parity.
        This also handles crossings between attachments in the same set.
        """
        if tolerance is None:
            reference = Scene(self.name)
            reference.knot(points,width,tolerance=0,expected=False)
            protected = {i for c in reference.crossings for i in c[2:4]}
            candidates = [reference]
            for protection in [(),protected]:
                for fraction in [.9,.6,.45,.3,.225]:
                    candidate = Scene(self.name)
                    try:
                        candidate.knot(points,width,tolerance=width*fraction,
                                       expected=False,protected=protection)
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
                strand.color = QColor('#e8ac45')
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

    def weave(self):
        """Reverse alternating crossings, using only nonempty native mask paths."""
        if self.explicit_crossings:
            return
        regular = list(self.strands)
        outlines = []
        sampled = []
        for strand in regular:
            stroker = QPainterPathStroker()
            stroker.setWidth(strand.width)
            outlines.append(stroker.createStroke(strand.get_path()))
            sampled.append([strand.get_path().pointAtPercent(k/24) for k in range(25)])
        for i, a in enumerate(regular):
            for j in range(i + 1, len(regular)):
                b = regular[j]
                if a.set_number == b.set_number or (i + j) % 2:
                    continue
                if self.name == 'woven_heart' and a.set_number <= 3 and b.set_number <= 3:
                    continue
                intersection = outlines[i].intersected(outlines[j])
                if intersection.isEmpty():
                    continue
                # Nearby strokes and attachment caps alone are not crossings.
                if not any(QLineF(p,q).intersect(QLineF(r,t),QPointF()) == QLineF.BoundedIntersection
                           for p,q in zip(sampled[i],sampled[i][1:])
                           for r,t in zip(sampled[j],sampled[j][1:])):
                    continue
                rect = intersection.boundingRect()
                if min(rect.width(), rect.height()) < min(a.width, b.width) * .6:
                    continue
                mask = MaskedStrand(a, b)
                if not mask.get_mask_path().isEmpty():
                    self.strands.append(mask)


def polar(radius, angle, center=(600, 440)):
    return center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)


def ellipse(cx, cy, rx, ry, rotation=0, count=12):
    return [(cx + rx * math.cos(t) * math.cos(rotation) - ry * math.sin(t) * math.sin(rotation),
             cy + rx * math.cos(t) * math.sin(rotation) + ry * math.sin(t) * math.cos(rotation))
            for t in [TAU * i / count for i in range(count)]]


def scenes():
    s = Scene('woven_heart')
    for i in range(3):
        scale = 16 - 2.8 * i
        pts = []
        for j in range(24):
            t = TAU * j / 24
            pts.append((600 + scale * 16 * math.sin(t) ** 3,
                        420 - scale * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))))
        s.chain(pts, ['#cc526c', '#e799a5', '#934e83'][i], 'Heart ribbons', 20, True)
    for i in range(3):
        y = 345 + 85 * i
        s.chain([(300, y + 60), (500, y), (700, y), (900, y - 60)], PALETTE[1], 'Gold lacing', 15)
    yield s


    s = Scene('chinese_double_coin')
    s.knot([(380, 750), (440, 620), (540, 485), (730, 405),
            (850, 410), (915, 500), (870, 615), (745, 665),
            (610, 640), (500, 555), (425, 420), (420, 290),
            (485, 190), (600, 175), (685, 245), (695, 365),
            (655, 490), (560, 605), (450, 655), (335, 620),
            (300, 530), (340, 435), (440, 385), (565, 395),
            (690, 465), (805, 580), (890, 750)], 30)
    yield s

    s = Scene('chinese_cloverleaf')
    # Expanded version of the three locked bights, with both working ends free.
    points = [(0,40),(75,72),(105,97),(112,127),(125,131),(133,105),
              (126,50),(151,15),(199,5),(238,30),(240,52),(218,76),
              (160,90),(95,100),(45,123),(10,173),(15,210),(54,244),
              (83,240),(111,213),(131,170),(148,111),(150,89),(160,90),
              (164,109),(166,154),(191,177),(240,173),(273,149),
              (270,128),(241,110),(181,102),(126,112),(75,107),(0,121)]
    # Spread the small folds so their threading remains readable at strand width.
    def expand(v, lo, hi):
        return v + max(0, min(v-lo, hi-lo)) * 2
    s.knot([(220 + expand(x, 100, 170)*1.85,
             150 + expand(y, 85, 135)*1.85) for x,y in points], 20)
    yield s

    s = Scene('chinese_good_luck')
    s.knot([(570,790),(570,650),(570,430),(400,430),
            (330,320),(380,245),(460,330),(460,510),
            (820,510),(990,470),(1010,420),(960,375),(820,400),
            (540,400),(540,210),(570,110),(630,110),(660,210),
            (660,470),(400,470),(200,430),(200,370),(400,350),
            (720,350),(790,265),(860,300),(810,365),(640,365),
            (640,580),(750,640),(805,570),(720,540),
            (460,540),(370,670),(300,610),(400,590),(630,590),(630,790)], 22)
    yield s

    s = Scene('chinese_pan_chang')
    s.knot([(300,750),(310,650),(350,570),(830,570),
            (910,530),(830,490),(370,490),(290,450),
            (370,410),(830,410),(910,370),(830,330),(440,330),
            (350,265),(370,180),(440,210),
            (440,630),(480,710),(520,630),(520,230),
            (560,150),(600,230),(600,630),(640,710),(680,630),
            (680,250),(690,150),(750,100)], 24)
    yield s

    s = Scene('tidal_waves')
    for i in range(4):
        x, y = 280 + i * 155, 600 - i * 45
        s.chain([(x - 90, y + 85), (x - 20, y), (x + 20, y - 175), (x + 130, y - 210),
                 (x + 165, y - 110), (x + 85, y - 80), (x + 85, y - 135)],
                ['#205f88', '#278baa', '#49b4b7', '#8dccc3'][i], f'Wave {i + 1}', 30)
    s.chain([(220, 740), (450, 705), (710, 740), (990, 695)], PALETTE[1], 'Shoreline', 20)
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


def render(strands):
    image = QImage(1200, 900, QImage.Format_ARGB32_Premultiplied)
    image.fill(QColor('#faf8f3'))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    for s in strands:
        s.canvas = None
        s.draw(painter)
    painter.end()
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    canvas = SimpleNamespace(selected_strand=None, shadow_enabled=True, show_control_points=False)
    tiles = []
    for scene in scenes():
        scene.weave()
        data = serialize_project_state(scene.strands, scene.groups, canvas)
        assert len(data['strands']) == len(scene.strands)
        path = ROOT / 'src' / 'samples' / (scene.name + '.json')
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        loaded = validate(json.loads(path.read_text(encoding='utf-8')))
        if args.preview:
            args.preview.mkdir(parents=True, exist_ok=True)
            img = render(loaded)
            assert img.save(str(args.preview / (scene.name + '.png')))
            tiles.append((scene.name.replace('_', ' ').title(), img))
        print(f'{scene.name}: {len(loaded)} layers, {sum(isinstance(s, MaskedStrand) for s in loaded)} masks, {len(scene.groups)} groups')
    if tiles:
        # Pillow also works on Qt offscreen installations without font support.
        from PIL import Image, ImageDraw, ImageFont
        sheet = Image.new('RGB', (1440, math.ceil(len(tiles)/3)*400), '#faf8f3')
        draw = ImageDraw.Draw(sheet)
        try:
            font = ImageFont.truetype('arial.ttf', 22)
        except OSError:
            font = ImageFont.load_default()
        for i, (title, _img) in enumerate(tiles):
            x, y = (i % 3) * 480, (i // 3) * 400
            with Image.open(args.preview / (title.lower().replace(' ', '_') + '.png')) as tile:
                sheet.paste(tile.resize((480, 360), Image.Resampling.LANCZOS), (x, y))
            draw.text((x + 240, y + 378), title, font=font, fill='#263446', anchor='mm')
        sheet.save(args.preview / 'contact_sheet.png')


if __name__ == '__main__':
    main()

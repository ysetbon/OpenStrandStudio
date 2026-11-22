"""Prototype: knot diagram image -> cord centerline + crossings + over/under.

From the repo root:

    python scripts/knot_tracer/trace.py <image> <outdir>         writes report.json and design.json
    python scripts/knot_tracer/trace.py <image> <outdir> --fit   also smooths (smooth.py, next to this
                                                                 file), fits with `python -m openstrand draw`,
                                                                 redraws the fit and writes the final verdict

report.json carries "verdict": accepted | partial | rejected, with machine-readable reasons.
Needs numpy, pillow, scipy and scikit-image (the last two are not in requirements.txt).
Works on clean diagrams and simple renders; photos of real cord are rejected, not traced.
"""
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure, morphology

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
FIT = '--fit' in sys.argv
MODE = os.environ.get('KNOT_TRACE_MODE', 'auto')   # auto | solid | outline (set by the tracer itself)
SRC = ARGS[0] if ARGS else 'input.jpg'
OUT = ARGS[1] if len(ARGS) > 1 else '.'

im = Image.open(SRC)
if im.mode in ('RGBA', 'LA', 'PA') or 'transparency' in im.info:   # v3: transparent = white paper, not black
    im = im.convert('RGBA')
    white = Image.new('RGBA', im.size, (255, 255, 255, 255))
    white.alpha_composite(im)
    im = white
rgb = np.asarray(im.convert('RGB'))
g = rgb.astype(float).mean(2)
H, W = g.shape
report = {'image': [W, H]}

# ---------- 1. segment ----------
# v2: the background is the colour along the image border (works for light cords on dark
# cloth, coloured cords, grey render backgrounds); ink = far from that colour.
bw = max(4, min(H, W)//60)
ring = np.concatenate([rgb[:bw].reshape(-1, 3), rgb[-bw:].reshape(-1, 3), rgb[:, :bw].reshape(-1, 3), rgb[:, -bw:].reshape(-1, 3)]).astype(float)
bg = np.median(ring, 0)
cd = np.sqrt(((rgb.astype(float) - bg)**2).sum(2))
ring_cd = np.sqrt(((ring - bg)**2).sum(1))
from skimage.filters import threshold_otsu
thr = max(45.0, float(np.percentile(ring_cd, 75)) + 25, float(threshold_otsu(cd)))
ink = ndi.gaussian_filter(cd, 1.0) > thr
ink = morphology.remove_small_holes(ink, 60)
seg3 = {}
shadow = np.zeros_like(ink)
# v3: a coloured cord casts a grey shadow: drop ink that has no colour when most of the ink has
chroma = rgb.max(2).astype(float) - rgb.min(2)
if ink.sum() and np.median(chroma[ink]) > 60:
    shadow = ink & (ndi.gaussian_filter(chroma, 1.0) < 0.35*np.median(chroma[ink])) & (g < bg.mean() - 10)
    seg3['shadow_px_removed'] = int(shadow.sum())
    ink &= ~shadow
    ink = morphology.remove_small_holes(ink, 60)


def half_width(m):
    sk = morphology.skeletonize(m)
    d = ndi.distance_transform_edt(m)
    return float(np.median(d[sk])) if sk.any() else 1.0


# v3: bands drawn as two outlines (Celtic knots): fill the long thin regions the outlines enclose
stroke = half_width(ink)
holes = measure.label(~ink)
border = set(np.unique(np.concatenate([holes[0], holes[-1], holes[:, 0], holes[:, -1]])))
hd = ndi.distance_transform_edt(~ink)
strips = []
for r in measure.regionprops(holes):
    if r.label in border or r.area < 60:
        continue
    rad = float(hd[tuple(r.coords.T)].max())
    r.rad = rad
    if rad > 1.5*stroke and r.area/(rad*rad) > 7:
        strips.append(r)
outline_possible = bool(strips) and sum(r.area for r in strips) > 0.5*ink.sum()
if outline_possible and MODE == 'auto':
    # v4: long thin enclosed regions can be a band drawn as two outlines (a Celtic knot) or just the
    # paper between solid cords. Trace both readings, grade each, keep the cleaner one.
    graded = {}
    for mode in ('solid', 'outline'):
        sub = os.path.join(OUT, '_' + mode)
        os.makedirs(sub, exist_ok=True)
        subprocess.run([sys.executable, '-W', 'ignore', os.path.abspath(__file__), SRC, sub],
                       env=dict(os.environ, KNOT_TRACE_MODE=mode), capture_output=True, text=True)
        try:
            ck = json.load(open(os.path.join(sub, 'report.json')))['verdict']['checks']
            bad_ = ck['unresolved'] + ck['three_way'] + ck['not_twice'] + ck['stray_pieces']
            graded[mode] = (ck['crossings'] > 0 and bad_ == 0, -bad_/(ck['crossings'] + bad_ + 1), ck['mask_covered'])
        except Exception:
            graded[mode] = (False, -1.0, 0.0)
    choice = 'solid' if graded['solid'][0] or graded['solid'] >= graded['outline'] else 'outline'
    p = subprocess.run([sys.executable, '-W', 'ignore', os.path.abspath(__file__)] + sys.argv[1:],
                       env=dict(os.environ, KNOT_TRACE_MODE=choice))
    raise SystemExit(p.returncode)
seg3['reading'] = MODE if outline_possible else 'solid'
if outline_possible and MODE == 'outline':
    # the band is what the outlines enclose: every hole as wide as the long strips is a piece of band.
    # The outlines themselves are dropped, so a band passing under ends at the outline of the one above
    # (a gap, bridged below, which also says which one is on top).
    rb = float(np.median([r.rad for r in strips]))
    band = np.zeros_like(ink)
    n = 0
    for r in measure.regionprops(holes):
        if r.label in border or r.area < 60:
            continue
        rad = float(hd[tuple(r.coords.T)].max())
        if 0.75*rb <= rad <= 1.25*rb:
            band[tuple(r.coords.T)] = True
            n += 1
    ink = morphology.binary_dilation(band, morphology.disk(max(1, int(0.5*stroke))))
    seg3['outline_band_pieces'] = n
w0 = half_width(ink)
seg3['half_width'] = round(w0, 1)
report['segment_v3'] = seg3
lab = measure.label(ink)
regions = sorted(measure.regionprops(lab), key=lambda r: -r.area)
dist_ink = ndi.distance_transform_edt(ink)


def region_hw(r):
    return float(np.percentile(dist_ink[tuple(r.coords.T)], 90))


hw_main = region_hw(regions[0])
keep = [r for r in regions if r is regions[0] or (r.area >= 0.04*regions[0].area and 0.5*hw_main <= region_hw(r) <= 2.0*hw_main)]
cord_region = regions[0]
mask = np.isin(lab, [r.label for r in keep])
report['segment_v2'] = {'background_rgb': [round(v) for v in bg], 'threshold': round(thr), 'components_kept': len(keep)}
regions = keep + [r for r in regions if r not in keep]
labels = [{'bbox': [int(r.bbox[1]), int(r.bbox[0]), int(r.bbox[3]), int(r.bbox[2])],
           'center': [round(r.centroid[1]), round(r.centroid[0])], 'area': int(r.area)}
          for r in regions[len(keep):] if r.area > 150]
report['segment'] = {'cord_pixels': int(mask.sum()), 'labels_removed': labels}

# ---------- 2. skeleton ----------
OFFS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def neighbors(p, S):
    y, x = p
    return [(y+dy, x+dx) for dy, dx in OFFS if 0 <= y+dy < H and 0 <= x+dx < W and S[y+dy, x+dx]]


def build_graph(S):
    """Nodes: endpoints and junction clusters. Edges: pixel paths between them."""
    pts = list(zip(*np.nonzero(S)))
    deg = {p: len(neighbors(p, S)) for p in pts}
    jmask = np.zeros_like(S)
    for p, d in deg.items():
        if d >= 3:
            jmask[p] = True
    jl = measure.label(jmask, connectivity=2)
    node_of = {}
    nodes = []
    for r in measure.regionprops(jl):
        k = len(nodes)
        nodes.append({'pos': (r.centroid[0], r.centroid[1]), 'kind': 'junction'})
        for q in r.coords:
            node_of[tuple(q)] = k
    for p, d in deg.items():
        if d == 1:
            node_of[p] = len(nodes)
            nodes.append({'pos': p, 'kind': 'end'})
    edges, seen = [], set()
    for start, k in node_of.items():
        for nb in neighbors(start, S):
            if nb in node_of:
                if node_of[nb] != k and (start, nb) not in seen:
                    seen.add((start, nb)); seen.add((nb, start))
                    edges.append({'a': k, 'b': node_of[nb], 'path': [start, nb]})
                continue
            if (start, nb) in seen:
                continue
            path, prev, cur = [start, nb], start, nb
            seen.add((start, nb))
            while cur not in node_of:
                nxt = [q for q in neighbors(cur, S) if q != prev and q not in path[-3:]]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
                path.append(cur)
            if cur in node_of:
                seen.add((cur, path[-2]))
                edges.append({'a': k, 'b': node_of[cur], 'path': path})
    return nodes, edges


def plen(path):
    return sum(math.dist(a, b) for a, b in zip(path, path[1:]))


def skeleton_graph(mask):
    skel = morphology.skeletonize(mask)
    dist = ndi.distance_transform_edt(mask)
    raw_nodes, raw_edges = build_graph(skel)
    info = {'pixels': int(skel.sum()), 'raw_nodes': len(raw_nodes), 'raw_edges': len(raw_edges)}
    pruned = 0
    for _ in range(4):
        nodes, edges = build_graph(skel)
        changed = False
        for e in edges:
            ends = [n for n in (e['a'], e['b']) if nodes[n]['kind'] == 'end']
            other = [n for n in (e['a'], e['b']) if nodes[n]['kind'] == 'junction']
            jpt = e['path'][0] if nodes[e['a']]['kind'] == 'junction' else e['path'][-1]
            if len(ends) == 1 and other and plen(e['path']) < max(28, 2.2*dist[jpt] + 12):
                for q in e['path']:
                    if nodes[e['a']]['kind'] == 'junction' and q == e['path'][0]:
                        continue
                    if nodes[e['b']]['kind'] == 'junction' and q == e['path'][-1]:
                        continue
                    skel[q] = False
                pruned += 1
                changed = True
        skel = morphology.skeletonize(skel)
        if not changed:
            break
    nodes, edges = build_graph(skel)
    info.update({'spurs_pruned': pruned, 'nodes': len(nodes), 'edges': len(edges)})
    return skel, dist, nodes, edges, info


skel, dist, nodes, edges, info = skeleton_graph(mask)

# v3: bridge under-pass gaps. Two dead ends that face each other across a short gap with ink
# between them (the cord passing over) are one cord going under: join them, remember the bridge.
bridge = np.zeros((H, W), bool)
ends = []
for e in edges:
    for side in ('a', 'b'):
        if nodes[e[side]]['kind'] == 'end':
            p = e['path'] if side == 'a' else e['path'][::-1]
            hw = float(np.max([dist[q] for q in p[:120]] or [1]))   # tapered ends: use the cord's full width
            near = p[min(len(p)-1, int(1.5*hw))]
            back = p[min(len(p)-1, int(1.5*hw + max(12, 4*hw)))]
            v = np.array(near, float) - np.array(back, float)
            if np.linalg.norm(v) > 1:
                ends.append({'pos': np.array(p[0], float), 'dir': v/np.linalg.norm(v), 'hw': hw})
cands = []
for i in range(len(ends)):
    for j in range(i+1, len(ends)):
        a, b = ends[i], ends[j]
        d = b['pos'] - a['pos']
        L = float(np.linalg.norm(d))
        hw = max(a['hw'], b['hw'])
        if L < 2 or L > 11*hw + 12:
            continue
        u = d/L
        c1, c2 = float(np.dot(a['dir'], u)), float(np.dot(b['dir'], -u))
        if min(c1, c2) < (0.5 if L < 7*hw + 12 else 0.8):   # long gaps must line up well
            continue
        ts = np.linspace(0.15, 0.85, 25)
        inside = mask[np.round(a['pos'][0] + ts*d[0]).astype(int), np.round(a['pos'][1] + ts*d[1]).astype(int)].mean()
        if inside < 0.12:      # nothing passes over between them: two real cord ends
            continue
        cands.append((L*(2 - c1)*(2 - c2), i, j))
taken, bridges = set(), []
for cost, i, j in sorted(cands):
    if i in taken or j in taken:
        continue
    taken.update((i, j))
    a, b = ends[i], ends[j]
    n = int(np.linalg.norm(b['pos'] - a['pos'])) + 1
    ys = np.round(np.linspace(a['pos'][0], b['pos'][0], n)).astype(int)
    xs = np.round(np.linspace(a['pos'][1], b['pos'][1], n)).astype(int)
    bridge[ys, xs] = True
    bridges.append([[int(a['pos'][1]), int(a['pos'][0])], [int(b['pos'][1]), int(b['pos'][0])]])
    line_img = np.zeros((H, W), bool)
    line_img[ys, xs] = True
    mask |= ndi.distance_transform_edt(~line_img) <= 0.5*(a['hw'] + b['hw'])
# v3: rope texture: close the mask at a fraction of the cord width and fill texture holes
rad = int(max(1, round(0.15*w0)))
mask = morphology.binary_closing(np.pad(mask, rad), morphology.disk(rad))[rad:-rad, rad:-rad]
mask = morphology.remove_small_holes(mask, int(max(60, (1.2*w0)**2)))
mask = morphology.binary_opening(mask, morphology.disk(max(1, rad//2)))
skel, dist, nodes, edges, info = skeleton_graph(mask)
bridge_near = ndi.distance_transform_edt(~bridge) <= 3 if bridges else bridge
info['gaps_bridged'] = len(bridges)
report['bridges'] = bridges
report['skeleton'] = info

# ---------- 3. junctions -> crossings ----------
# A crossing shows in a skeleton as two 3-way junctions joined by a short link.
# Merge junctions joined by an edge shorter than the local cord width.
parent = list(range(len(nodes)))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


links = []
hw_typ = float(np.median([np.median([dist[q] for q in e['path']]) for e in edges])) if edges else 1.0
for i, e in enumerate(edges):
    if nodes[e['a']]['kind'] == nodes[e['b']]['kind'] == 'junction' and e['a'] != e['b']:
        mid = e['path'][len(e['path'])//2]
        # v4: two cords crossing at a shallow angle overlap for a long way. The skeleton runs down the
        # middle of the overlap, where the mask is wider than one cord: that stretch is one crossing.
        wide = float(np.median([dist[q] for q in e['path']])) > 1.25*hw_typ and plen(e['path']) < 10*hw_typ
        if plen(e['path']) < 2.2*dist[mid] + 12 or wide:
            parent[find(e['a'])] = find(e['b'])
            links.append(i)
groups = {}
for i, n in enumerate(nodes):
    if n['kind'] == 'junction':
        groups.setdefault(find(i), []).append(i)
crossings = []
cross_of = {}
for root, members in groups.items():
    k = len(crossings)
    ys = [nodes[m]['pos'][0] for m in members]
    xs = [nodes[m]['pos'][1] for m in members]
    crossings.append({'id': k, 'members': members, 'pos': (float(np.mean(ys)), float(np.mean(xs)))})
    for m in members:
        cross_of[m] = k
arms = {k: [] for k in range(len(crossings))}
cord_edges = [e for i, e in enumerate(edges) if i not in links]
# a short loop leaving and returning to the same junction is a filled blob (an arrowhead): drop it
blobs = [e for e in cord_edges if find(e['a']) == find(e['b']) and nodes[e['a']]['kind'] == 'junction'
         and plen(e['path']) < 120]
cord_edges = [e for e in cord_edges if not any(e is b for b in blobs)]
report['junctions_blob_loops_removed'] = [[int(e['path'][0][1]), int(e['path'][0][0])] for e in blobs]
for ei, e in enumerate(cord_edges):
    for side in ('a', 'b'):
        n = e[side]
        if n in cross_of:
            arms[cross_of[n]].append((ei, side))
for cr in crossings:
    cr['degree'] = len(arms[cr['id']])
report['junctions'] = {'raw_junctions': sum(1 for n in nodes if n['kind'] == 'junction'),
                       'merged_links': len(links),
                       'crossings': [{'id': c_['id'], 'at': [round(c_['pos'][1]), round(c_['pos'][0])],
                                      'degree': c_['degree'], 'merged_from': len(c_['members'])} for c_ in crossings]}


# ---------- 4. pair branches, walk the cord ----------
def arm_points(ei, side, reach=45):
    p = cord_edges[ei]['path']
    p = p if side == 'a' else p[::-1]
    out, total = [p[0]], 0.0
    for a, b in zip(p, p[1:]):
        total += math.dist(a, b)
        out.append(b)
        if total > reach:
            break
    return out


def arm_dir(ei, side, center):
    pts = arm_points(ei, side)
    far = np.array(pts[-1], float)
    near = np.array(pts[min(len(pts)-1, 8)], float)
    v = far - near
    if np.linalg.norm(v) < 1e-6:
        v = far - np.array(center)
    return v / (np.linalg.norm(v) + 1e-9)


pairs = {}
for cr in crossings:
    a = arms[cr['id']]
    if len(a) == 2:  # leftover junction pixel: the cord passes through
        pairs[(cr['id'], a[0])] = a[1]
        pairs[(cr['id'], a[1])] = a[0]
        cr['kind'] = 'pass-through'
        continue
    if len(a) == 3:  # a notch or stub: keep the straightest two arms
        dirs = [arm_dir(ei, s, cr['pos']) for ei, s in a]
        i, j = min([(0, 1), (0, 2), (1, 2)], key=lambda ij: float(np.dot(dirs[ij[0]], dirs[ij[1]])))
        pairs[(cr['id'], a[i])] = a[j]
        pairs[(cr['id'], a[j])] = a[i]
        cr['kind'] = 'stub (3-way, straightest two kept)'
        continue
    if len(a) != 4:
        cr['kind'] = f'unresolved ({len(a)}-way)'
        if len(a) > 4:   # v3: pair the straightest arms greedily so the walk can go on
            dirs = [arm_dir(ei, s, cr['pos']) for ei, s in a]
            order = sorted(((float(np.dot(dirs[i], dirs[j])), i, j) for i in range(len(a)) for j in range(i+1, len(a))))
            done = set()
            for sc, i, j in order:
                if i in done or j in done or sc > -0.5:
                    continue
                done.update((i, j))
                pairs[(cr['id'], a[i])] = a[j]
                pairs[(cr['id'], a[j])] = a[i]
        continue
    cr['kind'] = 'crossing'
    dirs = [arm_dir(ei, s, cr['pos']) for ei, s in a]
    best = None
    for p1, p2 in [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]:
        score = float(np.dot(dirs[p1[0]], dirs[p1[1]]) + np.dot(dirs[p2[0]], dirs[p2[1]]))
        if best is None or score < best[0]:
            best = (score, p1, p2)
    score, p1, p2 = best
    for i, j in (p1, p2):
        pairs[(cr['id'], a[i])] = a[j]
        pairs[(cr['id'], a[j])] = a[i]
    u1 = dirs[p1[0]] - dirs[p1[1]]
    u2 = dirs[p2[0]] - dirs[p2[1]]
    cosang = abs(float(np.dot(u1, u2))) / (np.linalg.norm(u1)*np.linalg.norm(u2) + 1e-9)
    cr['angle_deg'] = round(math.degrees(math.acos(min(1.0, cosang))))
    if cr['angle_deg'] < 25:   # v3: two passes running side by side (rope plies), not a crossing
        cr['kind'] = 'parallel (not a crossing)'
    cr['bend_deg'] = [round(math.degrees(math.acos(max(-1, min(1, -float(np.dot(dirs[i], dirs[j]))))))) for i, j in (p1, p2)]

end_edges = {}
for ei, e in enumerate(cord_edges):
    for side in ('a', 'b'):
        if nodes[e[side]]['kind'] == 'end':
            end_edges[e[side]] = (ei, side)


def end_width(n):
    ei, side = end_edges[n]
    p = cord_edges[ei]['path']
    p = p if side == 'a' else p[::-1]
    return float(np.median([dist[q] for q in p[5:40]] or [0]))


def walk_from(ei, side, used):
    line, visits, start_ei = [], [], ei
    closed = False
    while True:
        used.add(ei)
        p = cord_edges[ei]['path']
        p = p if side == 'a' else p[::-1]
        line.extend(p if not line else p[1:])
        far_side = 'b' if side == 'a' else 'a'
        n = cord_edges[ei][far_side]
        if nodes[n]['kind'] == 'end':
            break
        k = cross_of.get(n)
        key = (k, (ei, far_side))
        if key not in pairs:
            break
        if pairs[key][0] in used:
            closed = pairs[key][0] == start_ei
            if closed and crossings[k]['kind'] == 'crossing':
                visits.append({'crossing': k, 'index': len(line)-1})
            break
        if crossings[k]['kind'] == 'crossing':
            visits.append({'crossing': k, 'index': len(line)-1})
        ei, side = pairs[key]
    return line, visits, closed


used = set()
walks = []
for n in sorted(end_edges, key=end_width, reverse=True):
    ei, side = end_edges[n]
    if ei in used:
        continue
    walks.append(walk_from(ei, side, used))
for ei in range(len(cord_edges)):
    if ei not in used and plen(cord_edges[ei]['path']) > 4:
        walks.append(walk_from(ei, 'a', used))
# v3: a closed walk starts on a crossing; rotate it to start half-way along its longest
# crossing-free stretch, so the pattern's first letter is unambiguous
for wi, (line_, vis_, closed_) in enumerate(walks):
    if not closed_ or not vis_:
        continue
    n_ = len(line_)
    idx = sorted(v['index'] for v in vis_)
    gaps = [((idx[(j+1) % len(idx)] - idx[j]) % n_ or n_, idx[j]) for j in range(len(idx))]
    g_, at_ = max(gaps)
    r_ = (at_ + g_//2) % n_
    line2 = line_[r_:] + line_[:r_]
    for v in vis_:
        v['index'] = (v['index'] - r_) % n_
    vis_.sort(key=lambda v: v['index'])
    walks[wi] = (line2, vis_, closed_)
walks = [w for w in walks if plen(w[0]) > 60]
if not walks:
    raise SystemExit('nothing to walk')
walks.sort(key=lambda w: -plen(w[0]))
visits = []
for ci, (line_, vis_, closed_) in enumerate(walks):
    for v in vis_:
        v['cord'] = ci
        v['line'] = line_
        visits.append(v)
line = walks[0][0]
start = None
report['junctions']['kinds'] = {c_['id']: c_.get('kind') for c_ in crossings}
report['walk'] = {'start_end': [int(line[0][1]), int(line[0][0])],
                  'stop_end': [round(line[-1][1]), round(line[-1][0])],
                  'edges_used': len(used), 'edges_total': len(cord_edges),
                  'cords': len(walks), 'closed': [bool(w[2]) for w in walks],
                  'crossing_order': [v['crossing'] for v in visits],
                  'length_px': round(sum(plen(w[0]) for w in walks))}


# ---------- 5. over / under ----------
def profile_roughness(center, direction, half):
    """Sum of |intensity steps| sampled along a direction through the crossing."""
    cy, cx = center
    ts = np.linspace(-half, half, 2*int(half)+1)
    vals = ndi.map_coordinates(ndi.gaussian_filter(g, 1.2), [cy + ts*direction[0], cx + ts*direction[1]], order=1)
    return float((np.diff(vals)**2).sum()), vals


for v in visits:
    i, L = v['index'], v['line']
    kk = int(1.5*dist[tuple(np.round(L[i]).astype(int))] + 10)
    a, b = max(0, i-kk), min(len(L)-1, i+kk)
    d = np.array(L[b], float) - np.array(L[a], float)
    v['dir'] = d / (np.linalg.norm(d) + 1e-9)
    v['pos'] = L[i]
by_cross = {}
for vi, v in enumerate(visits):
    by_cross.setdefault(v['crossing'], []).append(vi)
for k, vis in by_cross.items():
    if len(vis) != 2:
        continue
    cr = crossings[k]
    center = np.mean([visits[vi]['pos'] for vi in vis], axis=0)
    widths = [float(dist[tuple(np.round(visits[vi]['pos']).astype(int))]) for vi in vis]
    half = 1.5*max(widths) + 6
    # v4.1: each pass's own half-width, measured away from the crossing (the mask is wider at the
    # crossing itself). When a thin cord crosses a wide one, side lines spaced by the wide cord's
    # width fall off the thin cord, which then looks rough and is wrongly called "under".
    own = []
    for vi in vis:
        L, i = visits[vi]['line'], visits[vi]['index']
        k1, k2 = int(2.5*max(widths)), int(5*max(widths))
        idx = [t for t in list(range(i-k2, i-k1)) + list(range(i+k1, i+k2)) if 0 <= t < len(L)]
        vals = [dist[tuple(np.round(L[t]).astype(int))] for t in idx]
        own.append(float(np.percentile(vals, 25)) if len(vals) >= 5 else max(widths))
    rough = []
    for vi, ow in zip(vis, own):   # v3: three parallel lines along the pass (centre and both sides), median
        dv = visits[vi]['dir']
        nv = np.array([-dv[1], dv[0]])
        side = max(widths) * min(1.0, ow/max(own))
        rough.append(float(np.median([profile_roughness(center + o*side*nv, dv, half)[0] for o in (-0.4, 0, 0.4)])))
    cr['own_half_width'] = [round(w_, 1) for w_ in own]
    top = int(np.argmin(rough))
    bf = []
    for vi in vis:
        L, i = visits[vi]['line'], visits[vi]['index']
        seg = L[max(0, i-int(half)):i+int(half)+1]
        bf.append(float(np.mean([bridge_near[q] for q in seg])) if bridges else 0.0)
    cr['by'] = 'brightness profile'
    if max(bf) > 0.4 and min(bf) < 0.2:   # v3: the pass drawn with a gap is the one underneath
        top = int(np.argmin(bf))
        cr['by'] = 'gap'
    for j, vi in enumerate(vis):
        visits[vi]['over'] = (j == top)
    cr['rough'] = rough
    cr['confidence'] = 1.0 if cr['by'] == 'gap' else round(abs(rough[0]-rough[1]) / (max(rough) + 1e-9), 2)
    cr['center'] = center
patterns = [''.join('O' if v.get('over') else 'U' for v in visits if v['cord'] == ci) for ci in range(len(walks))]
pattern = ' | '.join(patterns)
report['over_under'] = {'pattern_along_cord': pattern,
                        'crossings_visited_twice': sum(1 for vis in by_cross.values() if len(vis) == 2),
                        'crossings': [{'id': k, 'at': [round(crossings[k]['center'][1]), round(crossings[k]['center'][0])],
                                       'roughness': [round(r) for r in crossings[k]['rough']],
                                       'confidence': crossings[k]['confidence'], 'by': crossings[k].get('by')}
                                      for k, vis in by_cross.items() if 'rough' in crossings[k]]}
# v3: a skeleton shares a short link between the two passes of a crossing; straighten each pass
# through its crossings so the two cross at their real angle instead of running along each other
for line_, vis_, closed_ in walks:
    n_ = len(line_)
    for v in vis_:
        i = v['index']
        k_ = int(1.2*dist[tuple(np.round(line_[i]).astype(int))] + 4)
        a_, b_ = i - k_, i + k_
        if not closed_:
            a_, b_ = max(0, a_), min(n_-1, b_)
        pa, pb = np.array(line_[a_ % n_], float), np.array(line_[b_ % n_], float)
        for t in range(a_, b_+1):
            f = (t - a_)/max(1, b_ - a_)
            q = pa + f*(pb - pa)
            line_[t % n_] = (float(q[0]), float(q[1]))
report['visits'] = [{'n': i+1, 'cord': v['cord'], 'crossing': v['crossing'], 'over': bool(v.get('over')),
                     'at': [int(v['pos'][1]), int(v['pos'][0])],
                     'dir': [round(float(v['dir'][1]), 3), round(float(v['dir'][0]), 3)]} for i, v in enumerate(visits)]
report['line'] = [[int(q[1]), int(q[0])] for q in line[::3]]
report['lines'] = [[[int(q[1]), int(q[0])] for q in w[0][::3]] for w in walks]
report['skeleton_paths'] = [[[int(q[1]), int(q[0])] for q in e['path'][::3]] for e in cord_edges]

# ---------- outputs ----------
def steps(line):
    step = max(12.0, plen(line)/380)      # the fitter takes at most 400 points per cord
    step_pts, acc = [line[0]], 0.0
    for a, b in zip(line, line[1:]):
        acc += math.dist(a, b)
        if acc >= step:
            step_pts.append(b)
            acc = 0.0
    if step_pts[-1] != line[-1]:
        step_pts.append(line[-1])
    return step_pts


design = {'name': 'traced from image', 'cords': [{
    'points': [[int(p[1]), int(p[0])] for p in steps(w[0])],
    'smooth': True, 'closed': bool(w[2]), 'pattern': patterns[ci], 'width': 24, 'color': 'gray'}
    for ci, w in enumerate(walks)]}
json.dump(design, open(f'{OUT}/design.json', 'w'))

# ---------- v4: self-grading ----------
# Can this trace be trusted without a person looking? Reasons are machine-readable:
# {"code", "severity": "reject" | "partial", "detail"}.
reasons = []


def flag(code, severity, detail):
    reasons.append({'code': code, 'severity': severity, 'detail': detail})


kinds_ = [c_.get('kind') or '' for c_ in crossings]
n_cross = kinds_.count('crossing')
n_unres = sum(1 for k_ in kinds_ if k_.startswith('unres'))
n_stub = sum(1 for k_ in kinds_ if k_.startswith('stub'))
n_once = sum(1 for k_, c_ in zip(kinds_, crossings) if k_ == 'crossing' and len(by_cross.get(c_['id'], [])) != 2)
bad = n_unres + n_stub + n_once
if n_cross == 0:
    flag('no_crossings', 'reject', 'no 4-way crossing was found')
if bad:
    share = bad / max(1, n_cross + n_unres + n_stub)
    flag('unclean_junctions', 'reject' if share > 0.2 else 'partial',
         f'{n_unres} unresolved, {n_stub} three-way, {n_once} crossings not passed exactly twice (of {n_cross} crossings)')
dropped = [e for i, e in enumerate(cord_edges) if i not in used]
if dropped:
    flag('edges_not_walked', 'partial', f'{len(dropped)} skeleton edges were not walked')
strays = [ci for ci in range(len(walks)) if not any(v['cord'] == ci for v in visits)]
if strays and n_cross:
    flag('stray_pieces', 'reject' if len(strays) > 2 else 'partial', f'{len(strays)} walked pieces pass no crossing')
weak = [k for k, vis in by_cross.items() if 'rough' in crossings[k] and crossings[k]['confidence'] < 0.6]
if weak:
    flag('over_under_uncertain', 'partial',
         'low margin at crossings ' + ', '.join(f"{k} at ({round(crossings[k]['center'][1])}, {round(crossings[k]['center'][0])})" for k in weak))
# how much of the ink the trace explains: a band of the measured cord width along the walked lines
hw_med = float(np.median([dist[tuple(np.round(q).astype(int))] for w in walks for q in w[0][::5]]))
line_img = np.zeros((H, W), bool)
for w in walks:
    for q in w[0]:
        line_img[int(round(q[0])), int(round(q[1]))] = True
d_line, near_idx = ndi.distance_transform_edt(~line_img, return_indices=True)
# v4.1: the cord's half-width where it is, not one number for the whole picture: a cord that changes
# width (a wide band that becomes a thin line) was failing the coverage checks. The width along each
# walk is median-filtered over a long window so the wider mask at crossings does not count, and it is
# never taken below the global median, so a cord of one width is graded as before.
lw_img = np.zeros((H, W))
for w in walks:
    wl = np.array([dist[int(round(q[0])), int(round(q[1]))] for q in w[0]])
    wl = ndi.median_filter(wl, size=int(8*hw_med) | 1, mode='nearest') if len(wl) > 3 else wl
    for q, v_ in zip(w[0], wl):
        lw_img[int(round(q[0])), int(round(q[1]))] = max(hw_med, float(v_))
local_hw = lw_img[near_idx[0], near_idx[1]]
band = d_line <= np.maximum(2.0, local_hw)
cov_mask = float((mask & (d_line <= 1.6*local_hw + 2)).sum() / max(1, mask.sum()))
loose = (ndi.gaussian_filter(cd, 1.0) > max(25.0, 0.5*thr)) & ~shadow
loose = morphology.remove_small_objects(loose, 150)
unexplained = float((loose & (d_line > 2.5*local_hw + 4)).sum() / max(1, loose.sum()))
if cov_mask < 0.9:
    flag('mask_not_covered', 'reject' if cov_mask < 0.7 else 'partial', f'the walk covers {cov_mask:.2f} of the cord mask')
if unexplained > 0.12:
    flag('unexplained_ink', 'reject' if unexplained > 0.35 else 'partial',
         f'{unexplained:.2f} of the non-background ink is far from the traced cord (another cord, a label, a shadow)')
checks = {'crossings': n_cross, 'unresolved': n_unres, 'three_way': n_stub, 'not_twice': n_once,
          'cords': len(walks), 'stray_pieces': len(strays), 'min_over_under_margin': min([crossings[k]['confidence'] for k, vis in by_cross.items() if 'rough' in crossings[k]] or [0]),
          'mask_covered': round(cov_mask, 3), 'unexplained_ink': round(unexplained, 3), 'half_width_px': round(hw_med, 1),
          'half_width_range_px': [round(float(lw_img[lw_img > 0].min()), 1), round(float(lw_img.max()), 1)]}

# ---------- v4: fit and redraw (optional) ----------
fit = {'run': False}
if FIT and any(r_['severity'] == 'reject' for r_ in reasons):
    fit = {'run': False, 'skipped': 'trace already rejected'}
elif FIT:
    here = os.path.dirname(os.path.abspath(__file__))
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    sm = subprocess.run([sys.executable, os.path.join(here, 'smooth.py'), f'{OUT}/design.json', f'{OUT}/design_s.json', '3'],
                        capture_output=True, text=True)
    p = subprocess.run([sys.executable, '-m', 'openstrand', 'draw', f'{OUT}/design_s.json', '--out', f'{OUT}/fitted.json'],
                       capture_output=True, text=True, env=env, timeout=1500)
    txt = (p.stdout or '') + (p.stderr or '')
    open(f'{OUT}/fit.txt', 'w').write(sm.stdout + sm.stderr + txt)
    fit = {'run': True, 'ok': False}
    err = re.search(r'^error: (.*)$', txt, re.M)
    m = re.search(r'(\d+) crossings? in all.*?conflicts: (\d+)', txt)
    st = re.search(r'(\d+) strands', txt)
    if err or p.returncode or not os.path.exists(f'{OUT}/fitted.json') or not m:
        fit['error'] = (err.group(1) if err else txt.strip().split('\n')[-1])[:300]
        flag('fit_failed', 'reject', fit['error'])
    else:
        fit.update(ok=True, crossings=int(m.group(1)), conflicts=int(m.group(2)), strands=int(st.group(1)) if st else None,
                   mask_check_clean='mask check: no problems' in txt)
        if fit['crossings'] != n_cross:
            flag('fit_crossing_count', 'reject', f"the fitted design has {fit['crossings']} crossings, the trace {n_cross}")
        if fit['conflicts']:
            flag('fit_over_under_conflicts', 'partial', f"{fit['conflicts']} over/under conflicts in the fit")
        if not fit['mask_check_clean']:
            flag('fit_mask_problems', 'partial', 'the fit reports crossings drawn wrong')
        # redraw: the fitted strands' centrelines (cubic curves, image pixels) as a band of the measured
        # cord width, compared with the traced band and with the cord mask
        proj = json.load(open(f'{OUT}/fitted.json'))
        cps = {}
        for grp in proj.get('groups', {}).values():
            cps.update(grp.get('control_points', {}))
        fit_img = np.zeros((H, W), bool)
        ts = np.linspace(0, 1, 60)[:, None]
        n_drawn = 0
        for sd in proj.get('strands', []):
            cp = cps.get(sd.get('layer_name'))
            if not cp or 'start' not in sd or 'end' not in sd:
                continue
            P = [np.array([sd['start']['x'], sd['start']['y']]), None, None, np.array([sd['end']['x'], sd['end']['y']])]
            P[1] = np.array([cp['control_point1']['x'], cp['control_point1']['y']]) if cp.get('control_point1') else P[0]
            P[2] = np.array([cp['control_point2']['x'], cp['control_point2']['y']]) if cp.get('control_point2') else P[3]
            c_ = (1-ts)**3*P[0] + 3*(1-ts)**2*ts*P[1] + 3*(1-ts)*ts**2*P[2] + ts**3*P[3]
            for (x0, y0), (x1, y1) in zip(c_, c_[1:]):
                nn = int(max(abs(x1-x0), abs(y1-y0))) + 1
                xs = np.clip(np.round(np.linspace(x0, x1, nn)).astype(int), 0, W-1)
                ys = np.clip(np.round(np.linspace(y0, y1, nn)).astype(int), 0, H-1)
                fit_img[ys, xs] = True
            n_drawn += 1
        if n_drawn:
            d_fit = ndi.distance_transform_edt(~fit_img)
            fband = d_fit <= np.maximum(2.0, local_hw)
            iou = float((fband & band).sum() / max(1, (fband | band).sum()))
            mask_in_fit = float((mask & (d_fit <= 1.6*local_hw + 2)).sum() / max(1, mask.sum()))
            fit_in_mask = float((fit_img & ndi.binary_dilation(mask, iterations=int(0.6*hw_med) + 2)).sum() / max(1, fit_img.sum()))
            fit.update(redraw_iou=round(iou, 3), mask_covered_by_fit=round(mask_in_fit, 3), fit_inside_mask=round(fit_in_mask, 3))
            if min(mask_in_fit, fit_in_mask) < 0.85 or iou < 0.5:
                flag('redraw_mismatch', 'reject' if min(mask_in_fit, fit_in_mask) < 0.65 else 'partial',
                     f'redrawn fit vs image: IoU {iou:.2f}, mask covered {mask_in_fit:.2f}, fit inside mask {fit_in_mask:.2f}')
        else:
            flag('redraw_not_possible', 'partial', 'no strand geometry found in the fitted project')
else:
    flag('fit_not_run', 'partial', 'run with --fit for the final verdict')
verdict = 'rejected' if any(r_['severity'] == 'reject' for r_ in reasons) else 'partial' if reasons else 'accepted'
report['verdict'] = {'verdict': verdict, 'reasons': reasons, 'checks': checks, 'fit': fit}
json.dump(report, open(f'{OUT}/report.json', 'w'), default=str)
print(json.dumps({k: report[k] for k in ('segment', 'skeleton', 'walk')}, default=str)[:2000])
print('pattern', pattern)
print('verdict', verdict, '; '.join(f"{r_['code']}: {r_['detail']}" for r_ in reasons))

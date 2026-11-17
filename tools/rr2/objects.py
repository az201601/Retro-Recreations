"""Automatic OAM object segmentation + sprite catalog.

The trace records all 64 hardware sprites per frame, so the cleanest way to get
pixel-exact animation frames is to:

  1. cluster the visible hardware sprites of a frame into "objects" by spatial
     adjacency (a character is a group of 8x8 sprites that touch),
  2. describe every object by a normalised signature (relative offsets + tile +
     attributes + palette),
  3. dedupe signatures across the whole recording into a catalog,
  4. report which catalog entries follow each other -> animation clips.
"""
import numpy as np
from PIL import Image

from . import sprites as S


def cluster(rec, max_dx=16, max_dy=16, merge_gap=5):
    """Union-find over visible sprites, returns list of sprite lists."""
    vis = [s for s in rec.visible_sprites]
    n = len(vis)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    boxes = []
    h = 16 if rec.long_sprites else 8
    for s in vis:
        boxes.append((s['x'], s['y'], s['x'] + 8, s['y'] + h))
    for i in range(n):
        for j in range(i + 1, n):
            ax0, ay0, ax1, ay1 = boxes[i]
            bx0, by0, bx1, by1 = boxes[j]
            if ax0 - max_dx <= bx1 and bx0 - max_dx <= ax1 and \
               ay0 - max_dy <= by1 and by0 - max_dy <= ay1:
                union(i, j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(vis[i])
    out = []
    for g in groups.values():
        xs = [s['x'] for s in g]
        ys = [s['y'] for s in g]
        hh = 16 if rec.long_sprites else 8
        out.append(dict(sprites=g, x0=min(xs), y0=min(ys),
                        x1=max(xs) + 8, y1=max(ys) + hh))
    out.sort(key=lambda o: (o['y0'], o['x0']))
    if merge_gap <= 0:
        return out
    # second pass: glue boxes that nearly touch (a character is split over
    # several OAM entries with 1-4 px seams between the sprite groups)
    merged = True
    while merged:
        merged = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                a, b = out[i], out[j]
                if (a['x0'] - merge_gap <= b['x1'] and b['x0'] - merge_gap <= a['x1']
                        and a['y0'] - merge_gap <= b['y1']
                        and b['y0'] - merge_gap <= a['y1']):
                    a['sprites'] = a['sprites'] + b['sprites']
                    a['x0'] = min(a['x0'], b['x0'])
                    a['y0'] = min(a['y0'], b['y0'])
                    a['x1'] = max(a['x1'], b['x1'])
                    a['y1'] = max(a['y1'], b['y1'])
                    out.pop(j)
                    merged = True
                    break
            if merged:
                break
    out.sort(key=lambda o: (o['y0'], o['x0']))
    return out


def signature(rec, obj, mirror_normalise=True):
    """Pose signature: sprite list relative to the object's top-left corner."""
    x0, y0 = obj['x0'], obj['y0']
    items = []
    for s in obj['sprites']:
        items.append((s['x'] - x0, s['y'] - y0, s['tile'], s['attr'], s['pal']))
    items.sort()
    sig = (obj['x1'] - x0, obj['y1'] - y0, tuple(items))
    if mirror_normalise:
        # a mirrored pose folds onto the same signature (flips attr bit 6 and
        # mirrors the x offsets) so left/right share one catalog entry
        w = sig[0]
        mir = []
        for (dx, dy, t, a, p) in items:
            mir.append((w - dx - 8, dy, t, a ^ 0x40, p))
        mir.sort()
        msig = (w, sig[1], tuple(mir))
        return min(sig, msig), sig == sig
    return sig


def render_object(rec, chr_win, obj, pad=0):
    """Render one object (its sprites only) to RGBA."""
    w = obj['x1'] - obj['x0'] + pad * 2
    h = obj['y1'] - obj['y0'] + pad * 2
    canvas = np.zeros((h, w, 4), np.uint8)
    for s in sorted(obj['sprites'], key=lambda s: s['prio']):
        sp = S.render_sprite(rec, chr_win, s, None, rec.spr_page)
        sx = s['x'] - obj['x0'] + pad
        sy = s['y'] - obj['y0'] + pad
        sh, sw = sp.shape[:2]
        y1, x1 = min(h, sy + sh), min(w, sx + sw)
        src = sp[:y1 - sy, :x1 - sx]
        alpha = src[:, :, 3] > 0
        dst = canvas[sy:y1, sx:x1]
        for c in range(3):
            np.copyto(dst[:, :, c], src[:, :, c], where=alpha)
        np.copyto(dst[:, :, 3], src[:, :, 3], where=alpha)
    return canvas


def build_catalog(recs, chr_win_for, min_frames=2):
    """Return (catalog, per-frame object lists).

    catalog: list of dicts {sig, w, h, count, first_frame, example(rec,obj)}
    frames : list of (rec, [(catalog_index, obj)]) 
    """
    catalog = []
    index = {}
    frames = []
    for rec in recs:
        cw = chr_win_for(rec)
        objs = cluster(rec)
        tagged = []
        for o in objs:
            sig, _ = signature(rec, o)
            if sig not in index:
                index[sig] = len(catalog)
                catalog.append(dict(sig=sig, count=0, first=rec.frame,
                                    rec=rec, obj=o))
            i = index[sig]
            catalog[i]['count'] += 1
            tagged.append((i, o))
        frames.append((rec, tagged))
    return catalog, frames

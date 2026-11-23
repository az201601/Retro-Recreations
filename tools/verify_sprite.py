#!/usr/bin/env python3
"""Verify sprite (character) tiles against CHR using known background palettes.

For each cell on a candidate sprite grid:
  - bg colors (from neighboring verified bg cells' palettes) map to index 0 (transparent)
  - remaining colors map injectively to indices 1..3
  - lookup the resulting 64-index pattern in the CHR dump
"""
import sys, itertools, numpy as np
sys.path.insert(0, 'tools')
from verify_chr2 import load_ppm, match_cell_bg, TILE_DICT

def bg_palettes_near(frame, x, y, reach=48):
    """collect palettes of successfully matched bg cells around (x,y)"""
    pals = []
    for gy in range(max(0, y - reach), y + reach + 8, 8):
        for gx in range(max(0, x - reach), x + reach + 8, 8):
            m = match_cell_bg(frame[gy:gy+8, gx:gx+8])
            if m:
                pals.append(set(m[2]))
    return pals

def nearest_pal(pals, x, y, cx, cy):
    # palette of the bg cell nearest to sprite cell center
    best = None; bd = 1e9
    for i, p in enumerate(pals):
        # approximate: use index ordering — recompute positions lost; just return union of closest few
        pass
    return None

def try_cell(cell, bg_cols):
    """cell: 8x8x3; bg_cols: set of background colors. Return (bank,tile,map) or None."""
    colors = []
    for px in cell.reshape(-1, 3):
        t = (int(px[0]), int(px[1]), int(px[2]))
        if t not in colors:
            colors.append(t)
        if len(colors) > 6:
            return None
    sprite_cols = [c for c in colors if c not in bg_cols]
    other = [c for c in colors if c in bg_cols]
    if not sprite_cols or len(sprite_cols) > 3:
        return None
    flat = cell.reshape(-1, 3)
    for combo in itertools.permutations(range(1, 4), len(sprite_cols)):
        lut = {}
        for c, i in zip(sprite_cols, combo):
            lut[c] = i
        for c in other:
            lut[c] = 0
        target = np.zeros(64, dtype=np.uint8)
        ok = True
        for i in range(64):
            px = (int(flat[i, 0]), int(flat[i, 1]), int(flat[i, 2]))
            if px not in lut:
                ok = False; break
            target[i] = lut[px]
        if not ok:
            continue
        hit = TILE_DICT.get(tuple(target))
        if hit:
            return (hit[0], hit[1], tuple(colors), sprite_cols, combo)
    return None

def scan(frame, region, label, max_report=12):
    x0, y0, x1, y1 = region
    # precompute bg matches once for the expanded area (0-aligned bg grid)
    bgm = {}
    for ngy in range(max(0, y0 - 40), min(frame.shape[0], y1 + 40), 8):
        for ngx in range(max(0, x0 - 40), min(frame.shape[1], x1 + 40), 8):
            m = match_cell_bg(frame[ngy:ngy+8, ngx:ngx+8])
            if m:
                bgm[(ngx, ngy)] = set(m[2])
    results = []
    for oy in range(8):
        for ox in range(8):
            hits = []
            for gy in range((y0 + oy) // 8 * 8, y1 - 7, 8):
                for gx in range((x0 + ox) // 8 * 8, x1 - 7, 8):
                    cell = frame[gy:gy+8, gx:gx+8]
                    pals = [p for (ngx, ngy), p in bgm.items()
                            if abs(ngx - gx) <= 32 and abs(ngy - gy) <= 32]
                    if not pals:
                        continue
                    # union of palettes of the nearest matched cells (majority vote for bg colors)
                    from collections import Counter
                    cnt = Counter()
                    for p in pals:
                        for c in p:
                            cnt[c] += 1
                    bg_cols = {c for c, n in cnt.items() if n >= 2}
                    if not bg_cols:
                        continue
                    r = try_cell(cell, bg_cols)
                    if r:
                        hits.append((gx, gy, r))
            if hits:
                results.append(((ox, oy), hits))
    # report best origin (most hits)
    if not results:
        print(f"[{label}] no sprite-cell matches found")
        return None
    results.sort(key=lambda t: -len(t[1]))
    (ox, oy), hits = results[0]
    print(f"[{label}] best origin=({ox},{oy}) hits={len(hits)}")
    shown = 0
    for gx, gy, r in hits:
        b, t, colors, scols, combo = r
        print(f"   cell({gx},{gy}) bank{b} tile{t} sprite_cols={scols} idx={combo}")
        shown += 1
        if shown >= max_report:
            break
    return (ox, oy), hits

if __name__ == "__main__":
    play = load_ppm("tools/out/play4/j4200.ppm")
    scan(play, (8, 152, 64, 224), "chip-spawn(stage1)")

    title = load_ppm("tools/out/dense/f0960.ppm")
    scan(title, (160, 80, 240, 152), "dale(title-right)")
    scan(title, (40, 40, 112, 112), "chip(title-left)")

#!/usr/bin/env python3
"""Two-frame sprite extraction + verification.

For frame pairs with the same camera and a static background:
  - cell must match a bg tile in frame B (gives pure bg)
  - pixels equal in A and B -> sprite transparent (index 0)
  - pixels differing -> sprite opaque; colors mapped injectively to 1..3
  - lookup resulting pattern in CHR: exact match = verified sprite tile
"""
import sys, glob, os, itertools, numpy as np
sys.path.insert(0, 'tools')
from verify_chr2 import load_ppm, match_cell_bg, TILE_DICT, ALL_TILES

def sprite_cells(A, B, region):
    x0, y0, x1, y1 = region
    hits = []
    for gy in range(y0, y1 - 7, 8):
        for gx in range(x0, x1 - 7, 8):
            ca = A[gy:gy+8, gx:gx+8]; cb = B[gy:gy+8, gx:gx+8]
            if np.array_equal(ca, cb):
                continue
            m = match_cell_bg(cb)
            if not m:
                continue
            same = (ca == cb).all(axis=2)          # 8x8 bool: bg visible
            diff = ~same
            # sprite opaque colors
            scols = []
            ok = True
            for r in range(8):
                for c in range(8):
                    if diff[r, c]:
                        t = (int(ca[r,c,0]), int(ca[r,c,1]), int(ca[r,c,2]))
                        if t not in scols:
                            scols.append(t)
                            if len(scols) > 3:
                                ok = False; break
                if not ok: break
            if not ok or not scols:
                continue
            flat = ca.reshape(-1, 3)
            for combo in itertools.permutations(range(1, 4), len(scols)):
                lut = {s: i for s, i in zip(scols, combo)}
                target = np.zeros(64, dtype=np.uint8)
                good = True
                for i in range(64):
                    if same.reshape(-1)[i]:
                        target[i] = 0
                    else:
                        px = (int(flat[i,0]), int(flat[i,1]), int(flat[i,2]))
                        if px not in lut: good = False; break
                        target[i] = lut[px]
                if not good: continue
                hit = TILE_DICT.get(tuple(target))
                if hit:
                    hits.append(dict(x=gx, y=gy, bank=hit[0], tile=hit[1],
                                     sprite_cols=tuple(scols), combo=combo))
                    break
    return hits

def collect(pairs, region, label, limit_report=15):
    all_hits = []
    for (pa, pb) in pairs:
        A = load_ppm(pa); B = load_ppm(pb)
        h = sprite_cells(A, B, region)
        if h:
            all_hits.append((os.path.basename(pa), os.path.basename(pb), h))
    total = sum(len(h) for _, _, h in all_hits)
    uniq = {(r['bank'], r['tile']) for _, _, hs in all_hits for r in hs}
    print(f"[{label}] pairs_with_hits={len(all_hits)}/{len(pairs)} cell_hits={total} unique_tiles={len(uniq)}")
    shown = 0
    for fa, fb, h in all_hits[:4]:
        for r in h[:4]:
            print(f"   {fa} cell({r['x']},{r['y']}) bank{r['bank']} tile{r['tile']} cols={r['sprite_cols']} idx={r['combo']}")
            shown += 1
            if shown >= limit_report: break
        if shown >= limit_report: break
    return all_hits

if __name__ == "__main__":
    # ---- title/menu dancing characters (same camera) ----
    menu = sorted(glob.glob('tools/out/menu/*.ppm'), key=lambda p: int(os.path.basename(p)[1:-4]))
    pairs = [(menu[i], menu[i+1]) for i in range(len(menu)-1)]
    collect(pairs, (40, 40, 112, 112), "title-chip-left")
    collect(pairs, (160, 80, 232, 152), "title-dale-right")

    # ---- stage1: Chip jumping at spawn (walk run, dx=0 pairs) ----
    dxs = np.load('tools/out/walk_dx.npy')
    wf = sorted(glob.glob('tools/out/walk/*.ppm'), key=lambda p: int(os.path.basename(p)[1:-4]))
    wpairs = [(wf[i], wf[i+1]) for i in np.where((dxs[0]==0) & (dxs[1]>0.3) & (dxs[1]<15))[0] if int(i) >= 150]
    collect(wpairs, (8, 152, 72, 224), "stage1-chip", limit_report=10)

#!/usr/bin/env python3
"""Verify extracted CHR against game frames v2: scroll-offset search + sprite masking."""
import itertools, numpy as np

ROM = "Chip 'n Dale - Rescue Rangers 2 (USA).nes"
rom = open(ROM, "rb").read()
prg = rom[4] * 16384
CHR = rom[16 + prg:]
NBANKS = len(CHR) // 8192

def tile_indices(bank, t):
    o = bank * 8192 + t * 16
    lo = CHR[o:o + 8]; hi = CHR[o + 8:o + 16]
    out = np.zeros((8, 8), dtype=np.uint8)
    for r in range(8):
        for c in range(8):
            bit = 7 - c
            out[r, c] = ((lo[r] >> bit) & 1) | (((hi[r] >> bit) & 1) << 1)
    return out

ALL_TILES = [(b, t, tile_indices(b, t)) for b in range(NBANKS) for t in range(512)]
TILE_DICT = {}
for _b, _t, _ti in ALL_TILES:
    TILE_DICT.setdefault(tuple(_ti.flatten()), (_b, _t))

def load_ppm(p):
    with open(p, "rb") as f:
        assert f.readline().strip() == b"P6"
        w, h = map(int, f.readline().split()); f.readline()
        return np.frombuffer(f.read(), dtype=np.uint8).reshape(h, w, 3)

def match_cell_bg(cell):
    flat = cell.reshape(-1, 3)
    colors = []
    for px in flat:
        t = (int(px[0]), int(px[1]), int(px[2]))
        if t not in colors:
            colors.append(t)
        if len(colors) > 4:
            return None
    # injective maps from k colors to indices {0..3}: P(4,k)
    k = len(colors)
    for idx_tuple in itertools.permutations(range(4), k):
        lut = {colors[ci]: idx_tuple[ci] for ci in range(k)}
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
            return (hit[0], hit[1], tuple(colors), idx_tuple)
    return None

def verify(frameA, frameB, x0, y0, x1, y1, label):
    """Search 8x8 grid offset; mask cells that differ between A,B (sprites)."""
    best = None
    for sy in range(8):
        for sx in range(8):
            total = matched = sprite_masked = 0
            fails = []
            banks = {}
            for gy in range((y0 + sy) // 8 * 8, y1, 8):
                for gx in range((x0 + sx) // 8 * 8, x1, 8):
                    if gx < x0 or gy < y0 or gx + 8 > x1 or gy + 8 > y1:
                        continue
                    ca = frameA[gy:gy+8, gx:gx+8]
                    cb = frameB[gy:gy+8, gx:gx+8]
                    if np.abs(ca.astype(int) - cb.astype(int)).max() > 24:
                        sprite_masked += 1
                        continue
                    total += 1
                    m = match_cell_bg(ca)
                    if m:
                        matched += 1
                        banks[m[0]] = banks.get(m[0], 0) + 1
                    else:
                        fails.append((gx, gy))
            score = matched / max(total, 1)
            if best is None or score > best[0]:
                best = (score, sx, sy, total, matched, sprite_masked, fails, dict(sorted(banks.items())))
    score, sx, sy, total, matched, sm, fails, banks = best
    print(f"[{label}] offset=({sx},{sy}) bg_cells={total} matched={matched} ({100*score:.1f}%) sprite_masked={sm} banks={banks}")
    if fails:
        print(f"   fails({len(fails)}): {fails[:24]}")
    return best

if __name__ == "__main__":
    t1 = load_ppm("tools/out/dense/f0912.ppm")
    t2 = load_ppm("tools/out/dense/f0960.ppm")
    verify(t1, t2, 0, 0, 256, 240, "title-full")

    a = load_ppm("tools/out/play4/j4200.ppm")
    b = load_ppm("tools/out/play4/j5400.ppm")
    verify(a, b, 0, 0, 256, 176, "stage1-upper")
    verify(a, b, 0, 176, 256, 240, "stage1-lower(HUD)")

#!/usr/bin/env python3
"""Verify extracted CHR data against actual game frames.

Method: take 8x8 cells from a screenshot, find the palette permutation and the
CHR tile whose 2bpp indices reproduce the cell exactly. If every cell matches,
the CHR dump contains exactly the graphics the game renders.
"""
import sys, glob, itertools, numpy as np

ROM = "Chip 'n Dale - Rescue Rangers 2 (USA).nes"
rom = open(ROM, "rb").read()
prg = rom[4] * 16384
CHR = rom[16 + prg:]
NBANKS = len(CHR) // 8192

def tile_indices(bank, t):
    """Return 8x8 array of 0..3 indices for tile t in bank."""
    o = bank * 8192 + t * 16
    lo = CHR[o:o + 8]; hi = CHR[o + 8:o + 16]
    out = np.zeros((8, 8), dtype=np.uint8)
    for r in range(8):
        for c in range(8):
            bit = 7 - c
            out[r, c] = ((lo[r] >> bit) & 1) | (((hi[r] >> bit) & 1) << 1)
    return out

def load_ppm(p):
    with open(p, "rb") as f:
        assert f.readline().strip() == b"P6"
        w, h = map(int, f.readline().split()); f.readline()
        return np.frombuffer(f.read(), dtype=np.uint8).reshape(h, w, 3)

def cell_colors(cell):
    """unique colors of an 8x8 cell (as tuples)"""
    flat = cell.reshape(-1, 3)
    colors = []
    for px in flat:
        t = (int(px[0]), int(px[1]), int(px[2]))
        if t not in colors:
            colors.append(t)
    return colors

# precompute all tiles as index arrays + lookup dict by flattened tuple
ALL_TILES = [(b, t, tile_indices(b, t)) for b in range(NBANKS) for t in range(512)]
TILE_DICT = {}
for _b, _t, _ti in ALL_TILES:
    TILE_DICT.setdefault(tuple(_ti.flatten()), (_b, _t))

def match_cell_bg(cell):
    """Background cell: <=4 colors, try all permutations mapping colors->indices."""
    colors = cell_colors(cell)
    if len(colors) > 4:
        return None
    for perm in itertools.permutations(range(len(colors))):
        # perm[i] = palette index assigned to colors[i]
        lut = {}
        for ci, pi in enumerate(perm):
            lut[colors[ci]] = pi
        target = np.zeros((8, 8), dtype=np.uint8)
        ok = True
        for r in range(8):
            for c in range(8):
                px = (int(cell[r, c, 0]), int(cell[r, c, 1]), int(cell[r, c, 2]))
                if px not in lut:
                    ok = False; break
                target[r, c] = lut[px]
            if not ok: break
        if not ok:
            continue
        hit = TILE_DICT.get(tuple(target.flatten()))
        if hit:
            return (hit[0], hit[1], tuple(colors), perm)
    return None

def verify_region(frame, x0, y0, x1, y1, label, grid=8, report_fail_limit=20):
    """Verify all grid cells in region against CHR."""
    total = matched = 0
    fails = []
    used_banks = {}
    recon = np.zeros(((y1 - y0), (x1 - x0), 3), dtype=np.uint8)
    for gy in range(y0, y1, grid):
        for gx in range(x0, x1, grid):
            cell = frame[gy:gy + grid, gx:gx + grid]
            if cell.shape[0] < grid or cell.shape[1] < grid:
                continue
            total += 1
            m = match_cell_bg(cell)
            if m:
                matched += 1
                b, t, colors, perm = m
                used_banks[b] = used_banks.get(b, 0) + 1
                # rebuild cell from tile+palette
                ti = ALL_TILES[b * 512 + t][2]
                pal = [None] * 4
                for ci, pi in enumerate(perm):
                    pal[pi] = colors[ci]
                for r in range(grid):
                    for c in range(grid):
                        pal_i = ti[r, c]
                        if pal[pal_i] is not None:
                            recon[gy - y0 + r, gx - x0 + c] = pal[pal_i]
            else:
                fails.append((gx, gy))
    print(f"[{label}] cells={total} matched={matched} ({100.0*matched/max(total,1):.1f}%) banks={dict(sorted(used_banks.items()))}")
    if fails:
        print(f"  first fails ({min(len(fails), report_fail_limit)}): {fails[:report_fail_limit]}")
    return matched, total, fails, recon

if __name__ == "__main__":
    # ---- 1. title screen: logo + text region ----
    title = load_ppm("tools/out/dense/f0960.ppm")
    # whole screen except bottom text: try everything; report failures
    verify_region(title, 0, 0, 256, 192, "title-top")
    verify_region(title, 0, 192, 256, 240, "title-bottom(text+floor)")

    # ---- 2. gameplay starting screen: wallpaper/window/table ----
    play = load_ppm("tools/out/play4/j4200.ppm")
    verify_region(play, 0, 0, 256, 160, "stage1-upper-bg")
    verify_region(play, 0, 160, 256, 208, "stage1-mid-bg(may contain sprite)")
    verify_region(play, 0, 208, 256, 240, "stage1-bottom(HUD)")

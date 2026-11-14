#!/usr/bin/env python3
"""Step 11 (level 1, section 2: the kitchen): builds the kitchen's background and block map from the capture_kitchen.py
route recordings (kt_route0..3).
  recreation/11_level1_kitchen/assets/sprites/spr_lv1b_bg   9 screens of 256x240 in 7 brightness steps
        (sub-image = screen * 7 + step; screens 0-5: the lower floor from the left, 6-8: the upper floor, above
        screens 5, 6 and 7; steps 0-2 fade-in, 3 normal, 4-6 fade-out)
  .../spr_lv1b_hole    the wall around the exit hole, 48x64, 7 brightness steps (drawn over the player in the hole)
  work/kt_map.pkl      tiles, colour groups, the places that changed during the route (bonus boxes that were taken)
  work/kt_blocks.pkl   the 16x16 blocks, 128 columns x 30 rows (rows 0-14: the upper floor), and their class
  work/kt_tables.gml   the block map as GML text (pasted into obj_stage1 Create)
The section is 8 screens wide and 2 high; the game only ever shows the 9 screens above."""
import os, pickle
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
from ppu import tile, RGB
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'recreation', '11_level1_kitchen', 'assets')
K0 = 3732            # NES frame on which the kitchen's picture comes on (its level frame 0)
E0 = 6588            # NES frame on which the player goes into the exit
W, H = 256, 60
SCREENS = [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (5, 0), (6, 0), (7, 0)]      # (column, row) of the 9 screens

def cams(s):
    """camera (x, y) of the picture and of the game; y: 0 = upper floor, 240 = lower floor"""
    r = s['ram']; t = s['t']
    X = (t & 31) * 8 + s['x'] + ((t >> 10) & 1) * 256; Y = (((t >> 5) & 31) * 8 + (t >> 12)) % 240
    cam = int(r[0x10]) + 256 * int(r[0x13]); cy = int(r[0x19]) * 240 + int(r[0x16]) - 1440
    return cam - ((cam - X) % 512), cy + ((Y - cy) % 240), cam, cy

def build():
    tiles = np.full((H, W), -1, int); attr = np.full((H // 2, W // 2), -1, int); last = np.full((H, W), -1, int)
    bm = np.full((30, 128), -1, int); blast = bm.copy(); changes = []; bchanges = []; chr_ = None; pals = {}
    for part in range(4):
        d = load('kt_route%d' % part); f0 = d['f0']
        for i, s in enumerate(d['st']):
            f = f0 + i; r = s['ram']
            if f in (K0 + 5, K0 + 9, K0 + 13, K0 + 17, E0 + 5, E0 + 9, E0 + 13): pals[f] = s['pal'][:16].copy() & 0x3F
            if int(r[0x20]) != 1 or s['mask'] == 0 or f < K0 + 18 or f > E0: continue
            v = s['vram']; px, py, cam, cy = cams(s)
            if chr_ is None: chr_ = v[:0x2000].copy()
            assert np.array_equal(chr_, v[:0x2000]), 'tile graphics change during the section'
            # while the picture moves up, the game rewrites the rows at its edge: those are left out
            m = 0 if cy in (0, 240) and py == cy else 16
            for wr in range((py + m + 7) // 8, min((py + 240 - m) // 8, H)):
                for wc in range(px // 8, min((px + 255) // 8 + 1, W)):
                    nt = 0x2000 + ((wc // 32) & 1) * 0x400; rr = wr % 30; cc = wc % 32
                    tv = int(v[nt + rr * 32 + cc]); av = (int(v[nt + 0x3C0 + (rr // 4) * 8 + cc // 4]) >> (((rr >> 1) & 1) * 4 + ((cc >> 1) & 1) * 2)) & 3
                    if tiles[wr, wc] < 0: tiles[wr, wc] = tv
                    if attr[wr // 2, wc // 2] < 0: attr[wr // 2, wc // 2] = av
                    if last[wr, wc] >= 0 and last[wr, wc] != tv: changes.append((f, wc, wr))
                    last[wr, wc] = tv
            blk = r[0x43A:0x43A + 240].reshape(15, 16).astype(int); lo = (cam >> 4) + (1 if cam % 16 >= 8 else 0)
            for c in range(lo, min(lo + 16, 128)):
                for wr in range((cy + m + 15) // 16, min((cy + 240 - m) // 16, 30)):
                    b = blk[wr % 15, c % 16]
                    if bm[wr, c] < 0: bm[wr, c] = b
                    if blast[wr, c] >= 0 and blast[wr, c] != b: bchanges.append((f, c, wr, int(blast[wr, c]), int(b)))
                    blast[wr, c] = b
        del d
    for sx, sy in SCREENS:
        assert (tiles[sy * 30:sy * 30 + 30, sx * 32:sx * 32 + 32] >= 0).all(), ('screen not seen completely', sx, sy)
        assert (bm[sy * 15:sy * 15 + 15, sx * 16:sx * 16 + 16] >= 0).all(), ('blocks not seen completely', sx, sy)
    tt = np.where(tiles < 0, 0, tiles); pix = np.zeros((H * 8, W * 8), np.uint8)
    for r in range(H):
        for c in range(W): pix[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = tile(chr_, int(tt[r, c]) * 16)
    grp = np.kron(np.where(attr < 0, 0, attr), np.ones((16, 16), int)).astype(np.uint8)
    cls = np.where(bm < 0, 0, np.where((bm >= 0xD0) & (bm != 0xF9), 2, np.where((bm >= 0xA0) & (bm != 0xF9), 1, 0)))
    P = [pals[K0 + k] for k in (5, 9, 13, 17)] + [pals[E0 + k] for k in (5, 9, 13)]
    return dict(tiles=tiles, attr=attr, changes=changes, pix=pix, grp=grp, pal=P), dict(raw=bm, cls=cls, changes=bchanges)

if __name__ == '__main__':
    M, B = build()
    os.makedirs(OUT + '/sprites', exist_ok=True)
    strip = Image.new('RGB', (256 * 63, 240))
    for sub, pal in enumerate(M['pal']):
        img = RGB[np.where(M['pix'] > 0, pal[M['grp'] * 4 + M['pix']], pal[0])]
        for k, (sx, sy) in enumerate(SCREENS):
            im = Image.fromarray(img[sy * 240:sy * 240 + 240, sx * 256:sx * 256 + 256])
            im.save('%s/sprites/spr_lv1b_bg_%d.png' % (OUT, k * 7 + sub)); strip.paste(im, ((k * 7 + sub) * 256, 0))
        if sub == 3: Image.fromarray(img).save(os.path.join(WORK, 'kt_map_full.png'))
    strip.save('%s/sprites/spr_lv1b_bg_strip63.png' % OUT)
    # the wall around the hole of the exit, 48 x 64 pixels at (2000, 128): drawn again over the player while he is
    # behind the wall; the pixels of the backdrop colour are left out
    hole = np.zeros((64, 48 * 7, 4), np.uint8)
    for sub, pal in enumerate(M['pal']):
        img = RGB[np.where(M['pix'] > 0, pal[M['grp'] * 4 + M['pix']], pal[0])]
        hole[:, sub * 48:sub * 48 + 48, :3] = img[128:192, 2000:2048]; hole[:, sub * 48:sub * 48 + 48, 3] = np.where(M['pix'][128:192, 2000:2048] > 0, 255, 0)
    Image.fromarray(hole).save('%s/sprites/spr_lv1b_hole_strip7.png' % OUT)
    pickle.dump(M, open(os.path.join(WORK, 'kt_map.pkl'), 'wb')); pickle.dump(B, open(os.path.join(WORK, 'kt_blocks.pkl'), 'wb'))
    g = ['// the 16x16 blocks of the kitchen, 128 columns x 30 rows (rows 0-14: the upper floor): 0 = nothing, 1 = can be stood on, 2 = solid']
    for r in range(30): g.append('lv_map2[%d] = "%s";' % (r, ''.join(str(int(v)) for v in B['cls'][r])))
    open(os.path.join(WORK, 'kt_tables.gml'), 'w').write('\n'.join(g) + '\n')
    print('map %dx%d tiles, 9 screens; blocks that changed during the route (frame, column, row, from, to): %s' % (W, H, [(f, c, r, '%02X' % a, '%02X' % b) for f, c, r, a, b in B['changes']]))
    print('colours', [' '.join('%02X' % v for v in p[:4]) for p in M['pal']])

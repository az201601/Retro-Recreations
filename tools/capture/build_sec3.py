#!/usr/bin/env python3
"""Step 15 (level 1, section 3: the stove and the sink): builds the section's background and block map from the
capture_sec3.py recordings (s3_route0..2 and s3_p_exit1).
  recreation/15_level1_stove/assets/sprites/spr_lv1c_bg   7 screens of 256x240 in 7 brightness steps
        (sub-image = screen * 7 + step; steps 0-2 fade-in, 3 normal, 4-6 fade-out)
  .../spr_lv1c_front   the last 224 columns of the picture without the backdrop colour, 7 brightness steps (drawn over
        a player who is behind the picture: in the sink and in the exit)
  work/s3_map.pkl      tiles, colour groups, the places that changed during the route
  work/s3_blocks.pkl   the 16x16 blocks, 112 columns x 15 rows, and their class
  work/s3_tables.gml   the block map as GML text (pasted into obj_stage1 Create)"""
import os, pickle
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
from ppu import tile, RGB
import capture_sec3 as S3
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'recreation', '15_level1_stove', 'assets')
K0 = S3.K0
W, H = 224, 30

def build():
    tiles = np.full((H, W), -1, int); attr = np.full((H // 2, W // 2), -1, int); last = np.full((H, W), -1, int)
    bm = np.full((15, 112), -1, int); blast = bm.copy(); changes = []; bchanges = []; chr_ = None; pals = {}; chrch = []
    for part in range(3):
        d = load('s3_route%d' % part); f0 = d['f0']
        for i, s in enumerate(d['st']):
            f = f0 + i; r = s['ram']
            if f in (K0 + 5, K0 + 9, K0 + 13, K0 + 17): pals[f] = s['pal'][:16].copy() & 0x3F
            if s['mask'] == 0 or f < K0 + 18 or f > S3.SINK: continue
            v = s['vram']; t = s['t']
            cam = int(r[0x10]) + 256 * int(r[0x13]); X = (t & 31) * 8 + s['x'] + ((t >> 10) & 1) * 256; px = cam - ((cam - X) % 512)
            assert int(r[0x19]) * 240 + int(r[0x16]) == 1200 and (((t >> 5) & 31) * 8 + (t >> 12)) % 240 == 0, 'the camera moves up or down'
            if chr_ is None: chr_ = v[:0x2000].copy()
            if not np.array_equal(chr_, v[:0x2000]): chrch.append(f)
            assert (s['pal'][:16] & 0x3F == pals[K0 + 17]).all(), ('colours change during the section', f)
            for wr in range(H):
                for wc in range(px // 8, min((px + 255) // 8 + 1, W)):
                    nt = 0x2000 + ((wc // 32) & 1) * 0x400; cc = wc % 32
                    tv = int(v[nt + wr * 32 + cc]); av = (int(v[nt + 0x3C0 + (wr // 4) * 8 + cc // 4]) >> (((wr >> 1) & 1) * 4 + ((cc >> 1) & 1) * 2)) & 3
                    if tiles[wr, wc] < 0: tiles[wr, wc] = tv
                    if attr[wr // 2, wc // 2] < 0: attr[wr // 2, wc // 2] = av
                    if last[wr, wc] >= 0 and last[wr, wc] != tv: changes.append((f, wc, wr, int(last[wr, wc]), tv))
                    last[wr, wc] = tv
            blk = r[0x43A:0x43A + 240].reshape(15, 16).astype(int); lo = (cam >> 4) + (1 if cam % 16 >= 8 else 0)
            for c in range(lo, min(lo + 16, 112)):
                for wr in range(15):
                    b = blk[wr, c % 16]
                    if bm[wr, c] < 0: bm[wr, c] = b
                    if blast[wr, c] >= 0 and blast[wr, c] != b: bchanges.append((f, c, wr, int(blast[wr, c]), int(b)))
                    blast[wr, c] = b
        del d
    assert (tiles >= 0).all() and (bm >= 0).all(), 'not seen completely'
    # the fade-out: the three colour sets after the normal one, from a recording that reaches the exit
    d = load('s3_p_exit1'); seq = []
    for s in d['st']:
        p = s['pal'][:16].copy() & 0x3F
        if s['mask'] and (not seq or (seq[-1] != p).any()): seq.append(p)
    seq = seq[:4]; assert (seq[0] == pals[K0 + 17]).all() and (seq[3][1:4] == 15).all()      # (then the next area)
    pix = np.zeros((H * 8, W * 8), np.uint8)
    for r in range(H):
        for c in range(W): pix[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = tile(chr_, int(tiles[r, c]) * 16)
    grp = np.kron(attr, np.ones((16, 16), int)).astype(np.uint8)
    cls = np.where((bm >= 0xD0) & (bm != 0xF9), 2, np.where((bm >= 0xA0) & (bm != 0xF9), 1, 0))
    P = [pals[K0 + k] for k in (5, 9, 13, 17)] + seq[1:]
    return dict(tiles=tiles, attr=attr, changes=changes, pix=pix, grp=grp, pal=P, chr_changes=chrch), dict(raw=bm, cls=cls, changes=bchanges)

if __name__ == '__main__':
    M, B = build()
    os.makedirs(OUT + '/sprites', exist_ok=True)
    strip = Image.new('RGB', (256 * 49, 240))
    for sub, pal in enumerate(M['pal']):
        img = RGB[np.where(M['pix'] > 0, pal[M['grp'] * 4 + M['pix']], pal[0])]
        for k in range(7):
            im = Image.fromarray(img[:, k * 256:k * 256 + 256])
            im.save('%s/sprites/spr_lv1c_bg_%d.png' % (OUT, k * 7 + sub)); strip.paste(im, ((k * 7 + sub) * 256, 0))
        if sub == 3: Image.fromarray(img).save(os.path.join(WORK, 's3_map_full.png'))
    strip.save('%s/sprites/spr_lv1c_bg_strip49.png' % OUT)
    # the picture from x = 1568 on (the sink and the exit) without the backdrop colour: drawn again over a player
    # who is behind the picture
    front = np.zeros((240, 224 * 7, 4), np.uint8)
    for sub, pal in enumerate(M['pal']):
        img = RGB[np.where(M['pix'] > 0, pal[M['grp'] * 4 + M['pix']], pal[0])]
        front[:, sub * 224:sub * 224 + 224, :3] = img[:, 1568:1792]; front[:, sub * 224:sub * 224 + 224, 3] = np.where(M['pix'][:, 1568:1792] > 0, 255, 0)
    Image.fromarray(front).save('%s/sprites/spr_lv1c_front_strip7.png' % OUT)
    back = B['raw'] == 0x9F
    pickle.dump(M, open(os.path.join(WORK, 's3_map.pkl'), 'wb')); pickle.dump(B, open(os.path.join(WORK, 's3_blocks.pkl'), 'wb'))
    g = ['// the 16x16 blocks of the third section, 112 columns x 15 rows: 0 = nothing, 1 = can be stood on, 2 = solid']
    for r in range(15): g.append('lv_map3[%d] = "%s";' % (r, ''.join(str(int(v)) for v in B['cls'][r]) + '0' * 16))
    g.append('// 1 = a block in which the player is behind the picture (block $9F: the inside of the sink, the gap of the exit)')
    for r in range(15): g.append('lv_back3[%d] = "%s";' % (r, ''.join(str(int(v)) for v in back[r]) + '0' * 16))
    open(os.path.join(WORK, 's3_tables.gml'), 'w').write('\n'.join(g) + '\n')
    ch = {}
    for f, c, r, a, b in M['changes']: ch.setdefault((c, r), []).append((f, '%02X' % a, '%02X' % b))
    print('tiles that changed during the route: %d places' % len(ch))
    for k in sorted(ch)[:40]: print('  ', k, len(ch[k]), ch[k][:4])
    print('tile graphics changed on frames:', M['chr_changes'][:10], len(M['chr_changes']))
    print('blocks that changed (frame, column, row, from, to):', [(f, c, r, '%02X' % a, '%02X' % b) for f, c, r, a, b in B['changes']])
    print('colours', [' '.join('%02X' % v for v in p[:4]) for p in M['pal']])
    print('block values', sorted(set('%02X' % v for v in B['raw'].ravel())))

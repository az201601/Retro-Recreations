#!/usr/bin/env python3
"""Step 12: the kitchen's crates, bonus boxes and the hidden item.
  work/kt_boxes.pkl        cells: (column, row, kind, donor column, donor row); kind 1 crate, 2 crate with a bonus box
                           inside, 3 bonus box, 4 crate with the item inside.  The donor is a block of the kitchen
                           picture that looks like what the game puts where the box was.  box: a bonus box in the picture
  work/kt_box_tables.gml   the same as GML text (pasted into obj_stage1 Create)
  recreation/12_level1_kitchen_crates/assets/sprites/spr_item_strip7.png   the item (an acorn), 16x16, 7 brightness steps
  .../sprites/spr_lifestar_strip7.png, spr_1up_strip7.png   the star that gives a life and its sign (from kt_star)
  .../sounds/snd_extra_life.ogg                             the star's sound (from kt_fx_life_sq2)
What is behind a box comes from the ROM: each of the kitchen's 9 screens has a second copy without the boxes
(screen pointers at bank 0 $8000 / $8100); the copy is found by comparing all screens with the map of the recording.
Needs build_kitchen.py and the capture_kitchen.py recordings (kt_cr_e2: the item)."""
import os, pickle, sys
import numpy as np
from PIL import Image
from emu import WORK
from scenario import load
import ppu
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = ROOT + '/recreation/12_level1_kitchen_crates/assets'
ROM = open(os.path.join(ROOT, "Chip 'n Dale - Rescue Rangers 2 (USA).nes"), 'rb').read()[16:]
SCREENS = [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (5, 0), (6, 0), (7, 0)]
BOX = {0xF4: 1, 0xF5: 2, 0xF9: 3, 0xF6: 4}

def rd(bank, a): return ROM[bank * 0x4000 + (a - 0x8000)]
def screen(s):
    lo = rd(0, 0x8000 + s); hi = rd(0, 0x8100 + s); b = hi >> 6; a = ((hi & 0x3F) | 0x80) << 8 | lo
    if b * 0x4000 + a - 0x8000 + 240 > len(ROM): return None
    return np.array([rd(b, a + i) for i in range(240)]).reshape(15, 16)

def boxes():
    KB = pickle.load(open(os.path.join(WORK, 'kt_blocks.pkl'), 'rb')); raw = np.array(KB['raw']).astype(int)
    M = pickle.load(open(os.path.join(WORK, 'kt_map.pkl'), 'rb'))
    look = lambda c, r: (M['pix'][r * 16:r * 16 + 16, c * 16:c * 16 + 16].tobytes(), M['grp'][r * 16:r * 16 + 16, c * 16:c * 16 + 16].tobytes())
    sc = {s: screen(s) for s in range(160)}; behind = np.full((30, 128), -1)
    for sx, sy in SCREENS:
        m = raw[sy * 15:sy * 15 + 15, sx * 16:sx * 16 + 16]
        d, s = min((int(((q != m) & ~np.isin(m, list(BOX))).sum()), s) for s, q in sc.items() if q is not None)
        assert d == 0, (sx, sy, d)
        behind[sy * 15:sy * 15 + 15, sx * 16:sx * 16 + 16] = sc[s]
    donors = {}
    for r in range(30):
        for c in range(128):
            v = int(raw[r, c])
            if v < 0 or v in BOX: continue
            if v not in donors: donors[v] = (c, r)
            elif look(c, r) != look(*donors[v]): print('block %02X does not look the same everywhere' % v, (c, r), donors[v])
    cells = []
    for r in range(30):
        for c in range(128):
            v = int(raw[r, c])
            if v in BOX:
                u = int(behind[r, c]); assert u in donors, (c, r, hex(u)); cells.append((c, r, BOX[v], donors[u][0], donors[u][1]))
    box = next((c, r) for r in range(30) for c in range(128) if raw[r, c] == 0xF9)
    return cells, box

def item():
    """the item's four 8x8 sprites, from the frame of kt_cr_e2 on which it is first complete: tiles (dx, dy, tile, attribute)
    relative to the object's position, in the order of the NES sprite list"""
    import capture_kitchen as CK, build_player as BP
    for fn in CK.files('cr_e2'):
        d = load(fn)
        for k, S in enumerate(d['st']):
            r = S['ram']
            for j in range(3, 12):
                if (r[0x2F0 + j] & 15) == 0x0A and not r[0x2F0 + j] & 0x80 and S['mask'] & 0x10:
                    o = S['oam'].reshape(64, 4).astype(int); x = int(r[0x314 + j]); y = int(r[0x2FC + j])
                    t = [(int(q[3]) - x, int(q[0]) - y, int(q[1]), int(q[2])) for q in o if q[0] < 0xEF and q[1] in (0x9B, 0x9D, 0x9F)]
                    if len(t) != 4: continue
                    if t[0][0] > t[-1][0]: t.reverse()
                    assert [(a, b) for a, b, c, e in t] == [(-8, -16), (-8, -8), (0, -16), (0, -8)], t
                    pal = BP.palettes(); chr_ = next(q['vram'] for q in d['st'][k:] if q['vram'] is not None)[0x1000:0x2000]      # (stored every 16th frame)
                    im = Image.new('RGBA', (7 * 16, 16), (0, 0, 0, 0)); px = im.load()
                    for dx, dy, tl, at in t:
                        m = ppu.tile(chr_, tl * 16)
                        if at & 0x40: m = m[:, ::-1]
                        for b in range(7):
                            for yy in range(8):
                                for xx in range(8):
                                    if m[yy, xx]: px[b * 16 + dx + 8 + xx, dy + 16 + yy] = tuple(int(v) for v in ppu.RGB[pal[b][(at & 3) * 4 + m[yy, xx]] & 63]) + (255,)
                    return im, t
    raise Exception('item not found')

def star():
    """the star on the shelf above the exit (tiles $A0, $A2 and their mirror image) and the sign that rises from it when it
    is taken (tiles $A4, $A6), from kt_star: (16 x 16 strip, 16 x 8 strip), each in the 7 brightness steps"""
    import build_player as BP
    d = load('kt_star'); pal = BP.palettes(); out = []
    for want, h in (((0xA0, 0xA2), 16), ((0xA4, 0xA6), 8)):
        for k, S in enumerate(d['st']):
            o = S['oam'].reshape(64, 4).astype(int); t = [q for q in o if q[0] < 0xEF and q[1] in want]
            if len(t) != 2 * h // 8 or not S['mask'] & 0x10: continue
            x0 = min(q[3] for q in t); y0 = min(q[0] for q in t)
            chr_ = next(q['vram'] for q in d['st'][k:] if q['vram'] is not None)[0x1000:0x2000]
            im = Image.new('RGBA', (7 * 16, h), (0, 0, 0, 0)); px = im.load()
            for y, tl, at, x in t:
                m = ppu.tile(chr_, tl * 16)
                if at & 0x40: m = m[:, ::-1]
                for b in range(7):
                    for yy in range(8):
                        for xx in range(8):
                            if m[yy, xx]: px[b * 16 + x - x0 + xx, y - y0 + yy] = tuple(int(v) for v in ppu.RGB[pal[b][(at & 3) * 4 + m[yy, xx]] & 63]) + (255,)
            out.append(im); break
    return out

if __name__ == '__main__':
    os.makedirs(OUT + '/sprites', exist_ok=True)
    im, t = item(); im.save(OUT + '/sprites/spr_item_strip7.png'); print('item tiles', t)
    a, b = star(); a.save(OUT + '/sprites/spr_lifestar_strip7.png'); b.save(OUT + '/sprites/spr_1up_strip7.png')
    # the extra-life sound: 32 sounding frames and 2 silent ones on the 2nd square channel (asked for on frame 1500)
    import build_crates as BC
    d = load('kt_fx_life_sq2'); W = lambda f: [tuple(q) for q in d['apu'][f]]
    assert (0x4006, 0xC4) in W(1501) and (0x4004, 0xFF) in W(1532) and (0x4004, 0xF0) in W(1533), 'extra-life sound not where expected'
    BC.OUT = OUT; BC.sound('kt_fx_life_sq2', 1501, 34, 'snd_extra_life')
    cells, box = boxes()
    print('%d crates, %d crates with a bonus box, %d bonus boxes, %d crates with the item' % tuple(sum(1 for q in cells if q[2] == k) for k in (1, 2, 3, 4)))
    pickle.dump(dict(cells=cells, box=box), open(os.path.join(WORK, 'kt_boxes.pkl'), 'wb'))
    g = ['// the kitchen\'s crates and bonus boxes: column, row (0-29), kind (1 crate, 2 crate with a bonus box inside, 3 bonus box,',
         '// 4 crate with the item inside), and the column / row of a block of the kitchen picture that looks like what is behind it']
    g.append('lv_box2_n = %d;' % len(cells))
    for i, q in enumerate(cells): g.append('lv_bc2[%d] = %d; lv_br2[%d] = %d; lv_bk2[%d] = %d; lv_bdc2[%d] = %d; lv_bdr2[%d] = %d;' % (i, q[0], i, q[1], i, q[2], i, q[3], i, q[4]))
    g.append('lv_rbox2_c = %d; lv_rbox2_r = %d;    // a bonus box in the kitchen picture (shown where a crate had one inside)' % box)
    open(os.path.join(WORK, 'kt_box_tables.gml'), 'w').write('\n'.join(g) + '\n')

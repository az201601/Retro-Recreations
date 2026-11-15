#!/usr/bin/env python3
"""Step 14 (level 1, section 2: the bottle caps of the kitchen): builds
  recreation/14_level1_kitchen_caps/assets/sprites/spr_enemy_strip<N>.png
        the strip of step 13 with the tiles of the bottle cap added at its end; sub-image =
        (tile * 2 + (0 as stored, 1 mirrored)) * 7 + brightness
  recreation/14_level1_kitchen_caps/assets/sounds/snd_cap.ogg
  work/cp_tables.pkl      the picture tables of all enemies and of the cap (used by sim_caps.py)
  work/cap_tables.gml     the cap's pictures as GML text (pasted into obj_stage1 Create)
The cap's four pictures (on the bottle, pressed once, pressed twice, flying) are pictures 0-3 of object type 5 in
the ROM (see build_enemies.py); here they get the numbers 80-83.  The tile graphics come from the recording
cp_pop.  Needs build_mice.py and capture_caps.py to have run."""
import os, pickle, sys
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
import ppu, build_player as BP, build_crates as BC, build_enemies as BE
ROOT = BP.ROOT
OUT = os.path.join(ROOT, 'recreation', '14_level1_kitchen_caps', 'assets')
CELS = [0, 1, 2, 3]; FIRST = 80

if __name__ == '__main__':
    os.makedirs(OUT + '/sprites', exist_ok=True); os.makedirs(OUT + '/sounds', exist_ok=True)
    old = pickle.load(open(os.path.join(WORK, 'mi_tables.pkl'), 'rb'))
    src = Image.open('%s/recreation/13_level1_kitchen_mice/assets/sprites/spr_enemy_strip%d.png' % (ROOT, old['n'])).convert('RGBA')
    d = load('pl_basic'); pal = [bytes(d['st'][1364 + lt - d['f0']]['pal'][16:32]) for lt in (5, 9, 13, 17)]
    d = load('lv1_route2'); pal += [bytes(d['st'][3701 + k - d['f0']]['pal'][16:32]) for k in (5, 9, 13)]
    d = load('cp_pop_c'); chr_ = next(q['vram'] for q in d['st'][6400 - d['f0']:] if q['vram'] is not None)[0x1000:0x2000].copy()
    assert bytes(d['st'][6400 - d['f0']]['pal'][16:32]) == pal[3], 'the kitchen has other sprite colours'
    del d
    uniq = []; tab = dict(old['tab'])
    for c in CELS:
        for dx, dy, t, a in BE.cel(5, c):
            if (t, a) not in uniq: uniq.append((t, a))
        tab[FIRST + c] = [(dx, dy, old['n'] // 14 + uniq.index((t, a))) for dx, dy, t, a in BE.cel(5, c)]
    n = old['n'] + len(uniq) * 14; strip = Image.new('RGBA', (n * 8, 8), (0, 0, 0, 0)); strip.paste(src, (0, 0)); px = strip.load()
    for u, (t, a) in enumerate(uniq):
        assert a & 0x3C == 0, hex(a)
        m = ppu.tile(chr_, t * 16)
        if a & 0x40: m = m[:, ::-1]
        if a & 0x80: m = m[::-1, :]
        for right in (0, 1):
            mm = m[:, ::-1] if right else m
            for b in range(7):
                for yy in range(8):
                    for xx in range(8):
                        if mm[yy, xx]: px[old['n'] * 8 + ((u * 2 + right) * 7 + b) * 8 + xx, yy] = tuple(int(v) for v in ppu.RGB[pal[b][(a & 3) * 4 + mm[yy, xx]] & 63]) + (255,)
    for f in os.listdir(OUT + '/sprites'):
        if f.startswith('spr_enemy'): os.remove(os.path.join(OUT, 'sprites', f))
    strip.save('%s/sprites/spr_enemy_strip%d.png' % (OUT, n))
    print('%d new tiles, strip of %d sub-images' % (len(uniq), n))
    for c in CELS: print(FIRST + c, tab[FIRST + c])
    pickle.dump(dict(tab=tab, n=n, pieces=old['pieces']), open(os.path.join(WORK, 'cp_tables.pkl'), 'wb'))
    g = ['// the pictures of the bottle cap: 80 on the bottle, 81 pressed once, 82 pressed twice, 83 flying', '// (same layout as the tables of step 09; the tile numbers go on from those of step 13)']
    for c in CELS:
        c += FIRST
        g.append('en_tn[%d] = %d;' % (c, len(tab[c])))
        g.append(' '.join('en_tdx[%d,%d] = %d; en_tdy[%d,%d] = %d; en_tim[%d,%d] = %d;' % (c, j, dx, c, j, dy, c, j, u) for j, (dx, dy, u) in enumerate(tab[c])))
    open(os.path.join(WORK, 'cap_tables.gml'), 'w').write('\n'.join(g) + '\n')
    # the sound, from the recording in which only it was asked for (on frame 1500; it starts a frame later): 5 frames
    # of the 2nd square channel (two short notes); the noise channel is not used
    BC.OUT = OUT
    def W(run, f): return [tuple(q) for q in load(run)['apu'][f]]
    assert (0x4005, 0x8B) in W('cp_fx_cap_sq2', 1501) and (0x4005, 0x83) in W('cp_fx_cap_sq2', 1503) and (0x4004, 0xB0) in W('cp_fx_cap_sq2', 1505), 'cap sound not where expected'
    assert not any(a in (0x400E, 0x400F) for a, v in W('cp_fx_cap_noi', 1501)), 'the cap sound uses the noise channel'
    BC.sound('cp_fx_cap_sq2', 1501, 5, 'snd_cap')

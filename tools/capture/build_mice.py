#!/usr/bin/env python3
"""Step 13 (level 1, section 2: the mice of the kitchen): builds
  recreation/13_level1_kitchen_mice/assets/sprites/spr_enemy_strip<N>.png
        the strip of step 09 with the tiles of the two mice added at its end; sub-image =
        (tile * 2 + (0 as stored = facing left, 1 mirrored)) * 7 + brightness
  recreation/13_level1_kitchen_mice/assets/sounds/snd_mouse_stun.ogg, snd_mouse_swat.ogg, snd_mouse_jump.ogg
  work/mi_tables.pkl      the picture tables of all enemies (used by sim_mice.py)
  work/mouse_tables.gml   the new pictures as GML text (pasted into obj_stage1 Create)
The pictures come from the ROM (see build_enemies.py); the tile graphics from the kitchen route recording.
Needs build_enemies.py, capture_kitchen.py and capture_mice.py to have run."""
import os, pickle, sys
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
import ppu, build_player as BP, build_crates as BC, build_enemies as BE
ROOT = BP.ROOT
OUT = os.path.join(ROOT, 'recreation', '13_level1_kitchen_mice', 'assets')
CELS = [0, 1, 2, 3, 4, 5, 6, 15, 16, 17, 18, 19, 20, 21, 76]  # the mouse with the spoon 0-6; the mouse under a crate 76 (hidden), 15-21

if __name__ == '__main__':
    os.makedirs(OUT + '/sprites', exist_ok=True)
    old = pickle.load(open(os.path.join(WORK, 'en_tables.pkl'), 'rb'))
    src = Image.open('%s/recreation/09_level1_enemies/assets/sprites/spr_enemy_strip%d.png' % (ROOT, old['n'])).convert('RGBA')
    d = load('pl_basic'); pal = [bytes(d['st'][1364 + lt - d['f0']]['pal'][16:32]) for lt in (5, 9, 13, 17)]
    d = load('lv1_route2'); pal += [bytes(d['st'][3701 + k - d['f0']]['pal'][16:32]) for k in (5, 9, 13)]
    d = load('kt_route0'); chr_ = next(q['vram'] for q in d['st'][200:] if q['vram'] is not None)[0x1000:0x2000].copy(); del d
    uniq = []; tab = dict(old['tab'])
    for c in CELS:
        for dx, dy, t, a in BE.cel(7, c):
            if (t, a) not in uniq: uniq.append((t, a))
        tab[c] = [(dx, dy, old['n'] // 14 + uniq.index((t, a))) for dx, dy, t, a in BE.cel(7, c)]
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
    print('%d new tiles, strip of %d sub-images; new pictures %s' % (len(uniq), n, CELS))
    for c in CELS: print(c, [(dx, dy) for dx, dy, u in tab[c]])
    pickle.dump(dict(tab=tab, n=n, pieces=old['pieces']), open(os.path.join(WORK, 'mi_tables.pkl'), 'wb'))
    g = ['// the pictures of the mice (same layout as the tables of step 09; the tile numbers go on from there)']
    for c in CELS:
        g.append('en_tn[%d] = %d;' % (c, len(tab[c])))
        g.append(' '.join('en_tdx[%d,%d] = %d; en_tdy[%d,%d] = %d; en_tim[%d,%d] = %d;' % (c, j, dx, c, j, dy, c, j, u) for j, (dx, dy, u) in enumerate(tab[c])))
    open(os.path.join(WORK, 'mouse_tables.gml'), 'w').write('\n'.join(g) + '\n')
    # the sounds, from the recordings in which only they were asked for (on frame 1500; they start a frame later):
    # stunned mouse 58 frames and the swing of the spoon 19 frames of the 2nd square channel; the mouse that gets up
    # from under its crate 12 frames of the 2nd square channel and of the noise channel together
    BC.OUT = OUT
    def W(run, f): return [tuple(q) for q in load(run)['apu'][f]]
    assert (0x4006, 0x54) in W('mi_fx_stun_sq2', 1501) and (0x4004, 0xF0) in W('mi_fx_stun_sq2', 1558), 'stun sound not where expected'
    assert (0x4006, 0xDA) in W('mi_fx_swat_sq2', 1501) and (0x4004, 0xB0) in W('mi_fx_swat_sq2', 1519), 'swat sound not where expected'
    assert (0x4006, 0xFC) in W('mi_fx_wake_sq2', 1501) and (0x4004, 0xB0) in W('mi_fx_wake_sq2', 1512) and (0x400C, 0xF0) in W('mi_fx_wake_noi', 1512), 'wake sound not where expected'
    BC.sound('mi_fx_stun_sq2', 1501, 58, 'snd_mouse_stun'); BC.sound('mi_fx_swat_sq2', 1501, 19, 'snd_mouse_swat')
    import soxr
    def part(run, n):
        s = load(run); x = s['aud'][s['cnt'][1500]:s['cnt'][1500 + n]].astype(np.float64) / 32768
        y = soxr.resample(x, len(x) * 60.0 / n, 48000, quality='VHQ'); y = y[:n * 800]
        return np.concatenate([y, np.zeros(12 * 800 - len(y))])
    BC.ogg(part('mi_fx_wake_sq2', 12) + part('mi_fx_wake_noi', 12), 'snd_mouse_wake')

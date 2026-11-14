#!/usr/bin/env python3
"""Deliverable 9 (level 1, section 1: enemies): builds
  recreation/09_level1_enemies/assets/sprites/spr_enemy_strip<N>.png
        the 8x8 sprite tiles of the flyer, what it drops, the cook and its fork; sub-image =
        (tile * 2 + (0 as stored = facing left, 1 mirrored)) * 7 + brightness
  recreation/09_level1_enemies/assets/sounds/snd_buzz.ogg, snd_cook_throw.ogg, snd_enemy_hit.ogg
  work/en_tables.pkl      the picture tables (used by sim_enemies.py)
  work/enemy_tables.gml   the same as GML text (pasted into obj_stage1 Create)
The pictures come from the ROM: bank 5, pointer table $8000 + 2 * object type -> per picture a list of groups
(count | $80 = downwards, dx, dy, then count pairs tile, attribute), end 0.  sim_enemies.py checks every sprite of
every frame against the recordings.  The tile graphics and colours come from the capture_enemies.py recordings.
usage: build_enemies.py"""
import os, pickle
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
import ppu, build_player as BP, build_crates as BC
ROOT = BP.ROOT
OUT = os.path.join(ROOT, 'recreation', '09_level1_enemies', 'assets')
ROM = BC.ROM
CELS = [7, 8, 9, 10, 12, 13, 14, 22, 23, 24, 25, 26, 27, 28]     # object type 7: cook 7-13, fork 14, flyer 22-27, dropped thing 28
PIECES = [3, 4, 5, 6, 7]                                         # object type 3: the four quarters of a crate flying apart

def rd(a): return ROM[5 * 0x4000 + (a - 0x8000)]
def cel(typ, n):
    """sprites of picture n of object type typ as stored (facing left): (dx, dy, tile, attribute), in ROM order"""
    t = rd(0x8000 + typ * 2) | rd(0x8001 + typ * 2) << 8; p = rd(t + n * 2) | rd(t + n * 2 + 1) << 8; out = []
    while True:
        c = rd(p); p += 1
        if c == 0: return out
        dx = rd(p); dy = rd(p + 1); p += 2; dx = dx - 256 if dx > 127 else dx; dy = dy - 256 if dy > 127 else dy
        for i in range(c & 0x7F):
            out.append((dx, dy, rd(p), rd(p + 1))); p += 2
            if c & 0x80: dy += 8
            else: dx += 8

def sounds():
    def W(d, f): return [tuple(q) for q in d['apu'][f - d['f0']]]
    def first(d, test, lo, hi): return next(f for f in range(lo, hi) if test(W(d, f)))
    # the flyer's buzz: 2 frames of a low note, 2 silent frames (taken while the flyer hovers; while it flies the next
    # buzz cuts it short)
    d = load('en_hide')
    S = first(d, lambda w: (0x4006, 0x3A) in w and (0x4007, 0xFA) in w and (0x4004, 0x3F) in w, 1845, 1880)
    assert (0x4004, 0x3F) in W(d, S + 1) and (0x4004, 0x30) in W(d, S + 2) and (0x4006, 0x3A) in W(d, S + 4), 'buzz not where expected'
    BC.sound('en_hide_sq2', S, 4, 'snd_buzz')
    # the cook's throw: two notes of 4 frames, 2 silent frames
    d = load('en_cook')
    S = first(d, lambda w: (0x4006, 0xFD) in w and (0x4004, 0xBF) in w, 2100, 2140)
    assert (0x4006, 0xAB) in W(d, S + 4) and (0x4004, 0xB0) in W(d, S + 8) and (0x4004, 0xF0) in W(d, S + 10), 'cook sound not where expected'
    BC.sound('en_cook_sq2', S, 10, 'snd_cook_throw')
    # an enemy is hit: 2nd square channel for 17 frames (16 sounding), noise for the first 9 (8 sounding)
    d = load('en_cook2')
    S = first(d, lambda w: (0x4005, 0x9D) in w and (0x4004, 0x3C) in w, 2100, 2140)
    assert (0x400C, 0x3F) in W(d, S) and (0x400C, 0x30) in W(d, S + 8) and (0x400E, 0x00) in W(d, S + 8) and (0x4004, 0x30) in W(d, S + 16), 'hit sound not where expected'
    import soxr
    def part(run, n):
        s = load(run); x = s['aud'][s['cnt'][S - 1]:s['cnt'][S - 1 + n]].astype(np.float64) / 32768
        y = soxr.resample(x, len(x) * 60.0 / n, 48000, quality='VHQ'); y = y[:n * 800]
        return np.concatenate([y, np.zeros(17 * 800 - len(y))])
    BC.ogg(part('en_cook2_sq2', 17) + part('en_cook2_noi', 9), 'snd_enemy_hit')

if __name__ == '__main__':
    BC.OUT = OUT
    os.makedirs(OUT + '/sprites', exist_ok=True)
    # all four sprite palettes on the 4 fade-in steps and the 3 fade-out steps (the frames build_player.py uses)
    d = load('pl_basic'); pal = [bytes(d['st'][1364 + lt - d['f0']]['pal'][16:32]) for lt in (5, 9, 13, 17)]
    d = load('lv1_route2'); pal += [bytes(d['st'][3701 + k - d['f0']]['pal'][16:32]) for k in (5, 9, 13)]
    d = load('en_cook'); chr_ = d['st'][2130 - d['f0']]['vram'][0x1000:0x2000].copy(); del d
    uniq = []; tab = {}
    for c in CELS:
        for dx, dy, t, a in cel(7, c):
            if (t, a) not in uniq: uniq.append((t, a))
        tab[c] = [(dx, dy, uniq.index((t, a))) for dx, dy, t, a in cel(7, c)]
    n = len(uniq) * 14; strip = Image.new('RGBA', (n * 8, 8), (0, 0, 0, 0)); px = strip.load()
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
                        if mm[yy, xx]: px[((u * 2 + right) * 7 + b) * 8 + xx, yy] = tuple(int(v) for v in ppu.RGB[pal[b][(a & 3) * 4 + mm[yy, xx]] & 63]) + (255,)
    for old in os.listdir(OUT + '/sprites'):
        if old.startswith('spr_enemy'): os.remove(os.path.join(OUT, 'sprites', old))
    strip.save('%s/sprites/spr_enemy_strip%d.png' % (OUT, n))
    pieces = {}
    for c in PIECES:
        q = cel(3, c); assert [t for dx, dy, t, a in q] == [0x8C, 0x8E, 0x8D, 0x8F] and all(a == 0 for dx, dy, t, a in q), q
        pieces[c] = [(dx, dy, t - 0x8C) for dx, dy, t, a in q]
    print('%d different tiles, strip of %d sub-images; pictures %s' % (len(uniq), n, CELS))
    pickle.dump(dict(tab=tab, n=n, pieces=pieces), open(os.path.join(WORK, 'en_tables.pkl'), 'wb'))
    g = ['// enemy pictures (the numbers are the original picture numbers): tile i of picture c is drawn at',
         '// (x + en_tdx, y + en_tdy + 1) facing left, (x - en_tdx - 8, ...) facing right; sub-image (en_tim * 2 + facing) * 7 + brightness.',
         '// The tiles are in the order of the NES sprite list.']
    for c in CELS:
        g.append('en_tn[%d] = %d;' % (c, len(tab[c])))
        g.append(' '.join('en_tdx[%d,%d] = %d; en_tdy[%d,%d] = %d; en_tim[%d,%d] = %d;' % (c, j, dx, c, j, dy, c, j, u) for j, (dx, dy, u) in enumerate(tab[c])))
    g.append('// a crate that hit an enemy flies apart: its quarters (0 top left, 1 bottom left, 2 top right, 3 bottom right) on the')
    g.append('// frames 2..6 after the hit, relative to the crate (x, y)')
    for c in PIECES:
        g.append(' '.join('cr_pdx[%d,%d] = %d; cr_pdy[%d,%d] = %d; cr_pq[%d,%d] = %d;' % (c, j, dx, c, j, dy, c, j, q) for j, (dx, dy, q) in enumerate(pieces[c])))
    open(os.path.join(WORK, 'enemy_tables.gml'), 'w').write('\n'.join(g) + '\n')
    sounds()

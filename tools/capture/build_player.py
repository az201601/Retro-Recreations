#!/usr/bin/env python3
"""Deliverable 6 (level 1, section 1: the player): builds, from the capture_level1.py and capture_player.py recordings,
  recreation/06_level1_player/assets/sprites/spr_chip_strip<N>.png   Chip's 8x8 sprite tiles
  recreation/07_level1_dale/assets/sprites/spr_dale_strip<N>.png     Dale's
  recreation/06_level1_player/assets/sounds/snd_land.ogg             the landing sound
  work/lv1_blocks.pkl     the section's 16x16 blocks (NES RAM $043A.. as seen during the route) and their class
  work/pl_tables.pkl      the sprite tables (used by sim_player.py)
  work/player_tables.gml  the same tables and the block map as GML text (pasted into obj_player / obj_stage1 Create)
usage: build_player.py"""
import os, pickle, collections
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
import ppu
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'recreation', '06_level1_player', 'assets')
FRAMES = [0, 1, 2, 3, 4, 5, 23]          # NES frame numbers ($0338) in table order: stand, walk 1-3, crouch, jump, blink
HUD = (0x87, 0x88, 0x89)                  # sprite tiles of the heart display (Chip's, the hearts, Dale's)
OUT7 = os.path.join(ROOT, 'recreation', '07_level1_dale', 'assets')

def blocks():
    W = 128; bm = np.full((15, W), -1, int)
    for part in range(3):
        d = load('lv1_route%d' % part)
        for s in d['st']:
            r = s['ram']; cam = int(r[0xAC]) + 256 * int(r[0xAE]); m = r[0x43A:0x43A + 240].reshape(15, 16).astype(int)
            lo = (cam >> 4) + (1 if cam % 16 >= 8 else 0)
            for c in range(lo, min(lo + 16, W)):
                if bm[0, c] < 0: bm[:, c] = m[:, c % 16]
        del d
    assert (bm >= 0).all()
    cls = np.where((bm >= 0xD0) & (bm != 0xF9), 2, np.where((bm >= 0xA0) & (bm != 0xF9), 1, 0))
    return bm, cls

def layouts(run='pl_basic'):
    seen = collections.defaultdict(collections.Counter); chr_ = None
    d = load(run); st = d['st']
    for i in range(1384 - d['f0'], len(st)):          # from the second frame the game runs on
        r = st[i - 1]['ram']
        if st[i]['mask'] == 0 or r[0x308] or r[0x320]: continue
        if chr_ is None: chr_ = st[i]['vram'][0x1000:0x2000].copy()
        o = bytes(st[i]['oam']); x = int(r[0x314]); y = int(r[0x2FC])
        rel = tuple(sorted((o[k + 3] - x, o[k] - y, o[k + 1], o[k + 2]) for k in range(0, 256, 4) if o[k] < 0xEF and o[k + 1] not in HUD))
        if rel: seen[(int(r[0x338]), (int(r[0x344]) >> 6) & 1)][rel] += 1
    lay = {}
    for k, c in seen.items():
        assert len(c) == 1, ('more than one layout', k)
        lay[k] = list(c)[0]
    out = {}
    for f in FRAMES:                      # facing left is the mirror image of facing right
        rt = sorted((dx, dy, t, a & 3) for dx, dy, t, a in lay[(f, 1)]) if (f, 1) in lay else None
        lf = sorted((-dx - 8, dy, t, a & 3) for dx, dy, t, a in lay[(f, 0)]) if (f, 0) in lay else None
        assert rt == lf or rt is None or lf is None, f
        if rt is None or lf is None: print('picture %d: only seen facing %s' % (f, 'left' if rt is None else 'right'))
        out[f] = rt or lf
    return out, chr_

def palettes():
    d = load('pl_basic'); f0 = d['f0']; p = [bytes(d['st'][1364 + lt - f0]['pal'][16:24]) for lt in (5, 9, 13, 17)]
    d = load('lv1_route2'); f0 = d['f0']; p += [bytes(d['st'][3701 + k - f0]['pal'][16:24]) for k in (5, 9, 13)]
    return p

def ogg(y, name):
    import soundfile as sf
    os.makedirs(OUT + '/sounds', exist_ok=True); p = '%s/sounds/%s.ogg' % (OUT, name)
    with sf.SoundFile(p, 'w', samplerate=48000, channels=1, format='OGG', subtype='VORBIS') as f:
        for i in range(0, len(y), 2048): f.write(y[i:i + 2048].astype(np.float32))
    print('%-10s %.3f s  peak %.3f' % (name, len(y) / 48000, np.abs(y).max()))

def land_sound():
    import soxr
    d = load('pl_basic'); f0 = d['f0']
    L = next(f0 + i for i in range(1, len(d['st'])) if d['st'][i]['ram'][0xB8] == 2 and d['st'][i - 1]['ram'][0xB8] == 1)
    w = [[tuple(x) for x in d['apu'][L + k - f0]] for k in range(9)]
    assert w[1][0] == (0x400C, 0xF0) and (0x4006, 0x70) in w[2] and (0x4004, 0xB0) in w[7], 'landing sound not where expected'
    s = load('pl_land_sq2'); n = 6                                        # audible on frames L+2 .. L+6, channel silent on L+7
    x = s['aud'][s['cnt'][L + 1]:s['cnt'][L + 1 + n]].astype(np.float64) / 32768
    y = soxr.resample(x, len(x) * 60.0 / n, 48000, quality='VHQ'); N = n * 800
    ogg(y[:N] if len(y) >= N else np.concatenate([y, np.zeros(N - len(y))]), 'snd_land')
    print('landing on NES frame %d, sound on frames +2 .. +7' % L)

if __name__ == '__main__':
    bm, cls = blocks()
    pickle.dump(dict(raw=bm, cls=cls), open(os.path.join(WORK, 'lv1_blocks.pkl'), 'wb'))
    pal = palettes(); g = []; tabs = {}; strips = {}
    for who, run, out in (('chip', 'pl_basic', OUT), ('dale', 'dl_basic', OUT7)):
        lay, chr_ = layouts(run)
        uniq = []
        for f in FRAMES:
            for dx, dy, t, a in lay[f]:
                if (t, a) not in uniq: uniq.append((t, a))
        n = len(uniq) * 14; strip = Image.new('RGBA', (n * 8, 8), (0, 0, 0, 0)); px = strip.load()
        for u, (t, a) in enumerate(uniq):
            im = ppu.tile(chr_, t * 16)
            for left in (0, 1):
                m = im if left else im[:, ::-1]
                for b in range(7):
                    k = (u * 2 + left) * 7 + b
                    for yy in range(8):
                        for xx in range(8):
                            if m[yy, xx]: px[k * 8 + xx, yy] = tuple(int(v) for v in ppu.RGB[pal[b][a * 4 + m[yy, xx]] & 63]) + (255,)
        os.makedirs(out + '/sprites', exist_ok=True)
        for old in os.listdir(out + '/sprites'): os.remove(os.path.join(out, 'sprites', old))
        strip.save('%s/sprites/spr_%s_strip%d.png' % (out, who, n))
        tab = {f: [(dx, dy, uniq.index((t, a))) for dx, dy, t, a in lay[f]] for f in FRAMES}
        tabs[who] = dict(frames=FRAMES, tab=tab, n=n); strips[who] = strip
        g.append('// %s: tile i of picture f is drawn at (x + p_tdx, y + p_tdy + 1) facing right, (x - p_tdx - 8, ...) facing left' % who)
        for i, f in enumerate(FRAMES):
            g.append('p_tn[%d] = %d;' % (i, len(tab[f])))
            g.append(' '.join('p_tdx[%d,%d] = %d; p_tdy[%d,%d] = %d; p_tim[%d,%d] = %d;' % (i, j, dx, i, j, dy, i, j, u) for j, (dx, dy, u) in enumerate(tab[f])))
        g.append('')
        print('%s: %d different tiles, strip of %d sub-images' % (who, len(uniq), n))
    pickle.dump(dict(tabs['chip'], dale=tabs['dale']), open(os.path.join(WORK, 'pl_tables.pkl'), 'wb'))
    g.append('// the 16x16 blocks of the section, 128 columns x 15 rows: 0 = nothing, 1 = can be stood on, 2 = solid')
    for r in range(15): g.append('lv_map[%d] = "%s";' % (r, ''.join(str(int(v)) for v in cls[r])))
    open(os.path.join(WORK, 'player_tables.gml'), 'w').write('\n'.join(g) + '\n')
    # preview of the 7 pictures, both directions, both characters (not an asset)
    pv = Image.new('RGBA', (7 * 40, 160), (90, 90, 90, 255))
    for w, who in enumerate(('chip', 'dale')):
        for i, f in enumerate(FRAMES):
            for left in (0, 1):
                for dx, dy, u in tabs[who]['tab'][f]:
                    k = (u * 2 + left) * 7 + 3; t = strips[who].crop((k * 8, 0, k * 8 + 8, 8))
                    pv.alpha_composite(t, (i * 40 + 20 + (-dx - 8 if left else dx), w * 80 + left * 40 + 30 + dy + 1))
    os.makedirs(os.path.join(ROOT, '_scratch'), exist_ok=True); pv.resize((7 * 160, 640), Image.NEAREST).save(os.path.join(ROOT, '_scratch', 'preview.png'))
    land_sound()

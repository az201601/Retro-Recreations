#!/usr/bin/env python3
"""Deliverable 8 (level 1, section 1: crates and bonus boxes): builds, from the capture_crates.py recordings,
  recreation/08_level1_crates/assets/sprites/spr_chip_strip<N>.png, spr_dale_strip<N>.png
        the 8x8 sprite tiles of both characters, now with the pictures for carrying and throwing
  recreation/08_level1_crates/assets/sprites/spr_crate_strip14.png     the crate, 16x16: 7 brightness steps, normal and flashing
  recreation/08_level1_crates/assets/sounds/snd_pick.ogg, snd_throw.ogg, snd_throw_far.ogg, snd_bonus.ogg
  work/cr_tables.pkl      the sprite tables and the list of crates / bonus boxes (used by sim_crates.py)
  work/crate_tables.gml   the same as GML text (pasted into obj_player Create and obj_stage1 Create)
Needs work/lv1_blocks.pkl (build_player.py).    usage: build_crates.py"""
import os, pickle, collections
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
import ppu, build_player as BP
ROOT = BP.ROOT
OUT = os.path.join(ROOT, 'recreation', '08_level1_crates', 'assets')
ROM = open(os.path.join(ROOT, "Chip 'n Dale - Rescue Rangers 2 (USA).nes"), 'rb').read()[16:]
# NES picture numbers ($0338) in table order: 0-6 as in step 6; 7 standing with a crate, 8-10 walking with it,
# 11 in the air with it, 12-13 throwing
FRAMES = [0, 1, 2, 3, 4, 5, 23, 22, 6, 7, 8, 11, 9, 10]
CRATE_TILES = (0x8C, 0x8D, 0x8E, 0x8F)
RUNS = {'chip': ['pl_basic', 'cr_carry', 'cr_power', 'cr_rnd1', 'cr_rnd3', 'cr_rnd4'], 'dale': ['dl_basic', 'dl_cr_carry', 'dl_cr_power', 'dl_cr_rnd1', 'dl_cr_rnd4']}

def rd(bank, a): return ROM[bank * 0x4000 + (a - 0x8000)]
def behind(col, row):
    """the block the game puts where a crate or bonus box was: the section's second block layer in the ROM
    (screen list at bank 3 $9E6A + 16, screen pointers at bank 0 $8000 / $8100)"""
    s = rd(3, 0x9E6A + 16 + (col >> 4)) - 1
    lo = rd(0, 0x8000 + s); hi = rd(0, 0x8100 + s)
    return rd(hi >> 6, (((hi & 0x3F) | 0x80) << 8 | lo) + row * 16 + (col & 15))

def only_crates(r):
    for j in range(3, 8):                 # (slots 1 and 2 are the other player and the heart display)
        if r[0x2F0 + j] == 0: continue
        if r[0x32C + j] != 3: return False
        if r[0x32C + j] == 3 and (int(r[0x2F0 + j]) & 0x0F) not in (3, 9): return False
    return True

def layouts(runs):
    seen = collections.defaultdict(collections.Counter); chr_ = None
    for run in runs:
        d = load(run); st = d['st']
        for i in range(max(1384 - d['f0'], 1), len(st)):
            r = st[i - 1]['ram']
            if st[i]['mask'] == 0 or r[0x308] or r[0x320] or r[0xB8] == 23 or r[0x338] >= 128 or r[0x2FC] < 48: continue
            if not only_crates(r) or not only_crates(st[i]['ram']): continue
            if chr_ is None: chr_ = st[i]['vram'][0x1000:0x2000].copy()
            o = bytes(st[i]['oam']); x = int(r[0x314]); y = int(r[0x2FC])
            ks = [k for k in range(0, 256, 4) if o[k] < 0xEF]
            if ks and ks[0] >= 128: ks.reverse()          # the NES fills its sprite list backwards on every other frame
            rel = tuple((o[k + 3] - x, o[k] - y, o[k + 1], o[k + 2]) for k in ks if o[k + 1] not in BP.HUD and o[k + 1] not in CRATE_TILES)
            if rel: seen[(int(r[0x338]), (int(r[0x344]) >> 6) & 1)][rel] += 1
        del d
    out = {}
    for f in FRAMES:
        both = []
        for face in (1, 0):
            c = seen.get((f, face))
            if not c: both.append(None); continue
            lay, n = c.most_common(1)[0]
            assert n >= 0.9 * sum(c.values()), ('more than one layout', f, face, c.most_common(3))
            both.append([(dx, dy, t, a & 3) if face else (-dx - 8, dy, t, a & 3) for dx, dy, t, a in lay])
        assert both[0] == both[1] or None in both, f
        assert both != [None, None], ('never seen', f)
        if None in both: print('picture %d: only seen facing %s' % (f, 'left' if both[0] is None else 'right'))
        out[f] = both[0] or both[1]
    return out, chr_

def crate_layout():
    """the crate's four tiles relative to its position, and the frames of a far throw on which it flashes"""
    d = load('cr_power'); st = d['st']; f0 = d['f0']; rel = collections.Counter(); fl = []
    for i in range(1, len(st)):
        r = st[i - 1]['ram']; o = bytes(st[i]['oam'])
        for j in range(1, 8):
            if r[0x32C + j] == 3 and (int(r[0x2F0 + j]) & 0x8F) in (3, 9) and not r[0x320 + j] and not r[0x308 + j]:
                x = int(r[0x314 + j]); y = int(r[0x2FC + j])
                t = tuple(sorted((o[k + 3] - x, o[k] - y, o[k + 1], o[k + 2] & 0xE3) for k in range(0, 256, 4) if o[k] < 0xEF and o[k + 1] in CRATE_TILES))
                if len(t) == 4: rel[t] += 1
    return rel.most_common(3), st[1700 - f0]['vram'][0x1000:0x2000].copy()

def ogg(y, name):
    import soundfile as sf
    os.makedirs(OUT + '/sounds', exist_ok=True); p = '%s/sounds/%s.ogg' % (OUT, name)
    with sf.SoundFile(p, 'w', samplerate=48000, channels=1, format='OGG', subtype='VORBIS') as f:
        for i in range(0, len(y), 2048): f.write(y[i:i + 2048].astype(np.float32))
    print('%-14s %.3f s  peak %.3f' % (name, len(y) / 48000, np.abs(y).max()))

def sound(run, first, n, name):
    """NES frames first .. first+n-1 of a one-channel recording, stretched from 60.1 to 60 frames per second"""
    import soxr
    s = load(run); x = s['aud'][s['cnt'][first - 1]:s['cnt'][first - 1 + n]].astype(np.float64) / 32768
    y = soxr.resample(x, len(x) * 60.0 / n, 48000, quality='VHQ'); N = n * 800
    ogg(y[:N] if len(y) >= N else np.concatenate([y, np.zeros(N - len(y))]), name)

def sounds():
    d = load('cr_power'); f0 = d['f0']; W = lambda f: [tuple(q) for q in d['apu'][f - f0]]
    # the frames below are the frames of cr_power on which the port reports the event (sim_crates.py checks every event)
    P, T, TF = 1892, 1770, 1650
    assert (0x4005, 0x94) in W(P + 2) and (0x4006, 0x00) in W(P + 15), 'pick sound not where expected'
    assert (0x4005, 0x93) in W(T + 2) and (0x4004, 0x30) in W(T + 26), 'throw sound not where expected'
    assert (0x400C, 0xBF) in W(TF + 2) and (0x400C, 0xBF) in W(TF + 73) and (0x400C, 0xB0) in W(TF + 74), 'far throw sound not where expected'
    sound('cr_power_sq2', P + 2, 14, 'snd_pick'); sound('cr_power_sq2', T + 2, 25, 'snd_throw'); sound('cr_power_noi', TF + 2, 73, 'snd_throw_far')
    d = load('cr_boxes'); f0 = d['f0']; F = 1513
    assert (0x4006, 0x6A) in W(F + 2) and (0x4004, 0xF0) in W(F + 5), 'bonus sound not where expected'
    sound('cr_boxes_sq2', F + 2, 4, 'snd_bonus')

if __name__ == '__main__':
    BL = pickle.load(open(os.path.join(WORK, 'lv1_blocks.pkl'), 'rb')); raw = BL['raw']
    pal = BP.palettes(); g = []; tabs = {}
    os.makedirs(OUT + '/sprites', exist_ok=True)
    for old in os.listdir(OUT + '/sprites'): os.remove(os.path.join(OUT, 'sprites', old))
    def paint(px, k, m, a, w=8):
        for b in range(7):
            for yy in range(8):
                for xx in range(8):
                    if m[yy, xx]: px[(k + b) * w + xx, yy] = tuple(int(v) for v in ppu.RGB[pal[b][a * 4 + m[yy, xx]] & 63]) + (255,)
    for who in ('chip', 'dale'):
        lay, chr_ = layouts(RUNS[who]); uniq = []
        for f in FRAMES:
            for dx, dy, t, a in lay[f]:
                if (t, a) not in uniq: uniq.append((t, a))
        n = len(uniq) * 14; strip = Image.new('RGBA', (n * 8, 8), (0, 0, 0, 0)); px = strip.load()
        for u, (t, a) in enumerate(uniq):
            im = ppu.tile(chr_, t * 16)
            for left in (0, 1): paint(px, (u * 2 + left) * 7, im if left else im[:, ::-1], a)
        strip.save('%s/sprites/spr_%s_strip%d.png' % (OUT, who, n))
        tab = {f: [(dx, dy, uniq.index((t, a))) for dx, dy, t, a in lay[f]] for f in FRAMES}
        tabs[who] = dict(frames=FRAMES, tab=tab, n=n)
        g.append('// %s: tile i of picture f is drawn at (x + p_tdx, y + p_tdy + 1) facing right, (x - p_tdx - 8, ...) facing left;' % who)
        g.append('// the tiles are in the order of the NES sprite list (tile 0 is in front on even frames, the last one on odd frames)')
        for i, f in enumerate(FRAMES):
            g.append('p_tn[%d] = %d;' % (i, len(tab[f])))
            g.append(' '.join('p_tdx[%d,%d] = %d; p_tdy[%d,%d] = %d; p_tim[%d,%d] = %d;' % (i, j, dx, i, j, dy, i, j, u) for j, (dx, dy, u) in enumerate(tab[f])))
        g.append('')
        print('%s: %d different tiles, strip of %d sub-images' % (who, len(uniq), n))
    # the crate: sub-image = flashing * 7 + brightness
    cl, chr_ = crate_layout(); print('crate tiles (dx, dy, tile, palette), most common first:', cl)
    base = [q for q in cl if all(t[3] == 0 for t in q[0])][0][0]
    assert sorted((dx, dy) for dx, dy, t, a in base) == [(-8, -17), (-8, -9), (0, -17), (0, -9)], base
    cs = Image.new('RGBA', (14 * 16, 16), (0, 0, 0, 0)); px = cs.load()
    for fl in (0, 1):
        for dx, dy, t, a in base:
            m = ppu.tile(chr_, t * 16)
            for b in range(7):
                for yy in range(8):
                    for xx in range(8):
                        if m[yy, xx]: px[(fl * 7 + b) * 16 + dx + 8 + xx, dy + 17 + yy] = tuple(int(v) for v in ppu.RGB[pal[b][fl * 4 + m[yy, xx]] & 63]) + (255,)
    cs.save(OUT + '/sprites/spr_crate_strip14.png')
    # crates and bonus boxes: where, and a place in the background picture that looks like what is behind them
    donors = {}
    for r in range(15):
        for c in range(1, 127):
            v = int(raw[r, c])
            if v not in (0xF4, 0xF5, 0xF9) and v not in donors: donors[v] = (c, r)
    box = next((c, r) for r in range(15) for c in range(128) if raw[r, c] == 0xF9)
    cells = []
    for r in range(15):
        for c in range(128):
            v = int(raw[r, c])
            if v in (0xF4, 0xF5, 0xF9):
                u = behind(c, r); assert u in donors, (c, r, hex(u))
                cells.append((c, r, {0xF4: 1, 0xF5: 2, 0xF9: 3}[v], donors[u][0], donors[u][1]))
    print('%d crates, %d crates with a bonus, %d bonus boxes' % tuple(sum(1 for q in cells if q[2] == k) for k in (1, 2, 3)))
    patch = {(c, r): (dc, dr) for c, r, k, dc, dr in cells}
    pickle.dump(dict(chip=tabs['chip'], dale=tabs['dale'], patch=patch, box=box, cells=cells, patch_delay=1), open(os.path.join(WORK, 'cr_tables.pkl'), 'wb'))
    g.append('// crates and bonus boxes: column, row, kind (1 crate, 2 crate with a bonus box inside, 3 bonus box),')
    g.append('// and the column / row of a block of the background picture that looks like what is behind it')
    g.append('lv_box_n = %d;' % len(cells))
    for i, q in enumerate(cells): g.append('lv_bc[%d] = %d; lv_br[%d] = %d; lv_bk[%d] = %d; lv_bdc[%d] = %d; lv_bdr[%d] = %d;' % (i, q[0], i, q[1], i, q[2], i, q[3], i, q[4]))
    g.append('lv_rbox_c = %d; lv_rbox_r = %d;      // a bonus box in the background picture (shown where a crate had one inside)' % box)
    open(os.path.join(WORK, 'crate_tables.gml'), 'w').write('\n'.join(g) + '\n')
    sounds()

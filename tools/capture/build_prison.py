#!/usr/bin/env python3
"""Build the graphics and the sound of deliverable 3 from the capture_prison.py runs -> recreation/03_night_scene/assets"""
import os
import numpy as np, soxr, soundfile as sf
from PIL import Image
from scenario import load
from ppu import RGB, tile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'recreation', '03_night_scene', 'assets')
os.makedirs(OUT + '/sprites', exist_ok=True); os.makedirs(OUT + '/sounds', exist_ok=True)
d = load('prison_idle'); F0 = d['f0']
S = lambda f: d['st'][f - F0]

def fade(c, level):
    """the game's fade-out: every step lowers the brightness row of a colour by one; below the darkest row -> black"""
    c = int(c) & 0x3F
    return c - 0x10 * level if c - 0x10 * level >= 0 else 0x0F

def save(imgs, name):
    for i, x in enumerate(imgs): Image.fromarray(x).save('%s/sprites/%s_%d.png' % (OUT, name, i))
    Image.fromarray(np.hstack(imgs)).save('%s/sprites/%s_strip%d.png' % (OUT, name, len(imgs)))
    print('%-18s %d sub-images of %dx%d' % (name, len(imgs), imgs[0].shape[1], imgs[0].shape[0]))

# ---------------------------------------------------------------- background: both nametables side by side (512x240)
def nt_entries(p):
    """palette entry (0 = backdrop, else palette*4 + pixel) of every pixel of nametables 0 and 1"""
    v = p['vram']; base = 0x1000 if p['ctrl'] & 0x10 else 0
    full = np.zeros((240, 512), np.uint8)
    for q in range(2):
        b = 0x2000 + q * 0x400
        for r in range(30):
            for c in range(32):
                ti = int(v[b + r * 32 + c]); a = int(v[b + 0x3C0 + (r // 4) * 8 + c // 4]); sh = ((r >> 1) & 1) * 4 + ((c >> 1) & 1) * 2
                t = tile(v, base + ti * 16)
                full[r * 8:r * 8 + 8, q * 256 + c * 8:q * 256 + c * 8 + 8] = np.where(t > 0, ((a >> sh) & 3) * 4 + t, 0)
    return full
ENT = nt_entries(S(1300))
for f in (1242, 1600, 2000, 2290): assert (nt_entries(S(f)) == ENT).all()      # the nametables never change
assert (ENT[178] == 0).all() or len(set(ENT[178])) == 1                         # row 178 (where the split happens) is one flat colour
PAL_IN = [S(f)['pal'] & 0x3F for f in (1242, 1246, 1250, 1254)]                 # fade-in steps, the last one is the full palette
FULL = PAL_IN[3]
assert (S(1766)['pal'] & 0x3F == FULL).all()
bgpals = PAL_IN + [np.array([fade(c, L) for c in FULL], np.uint8) for L in (1, 2)]     # sub-images 0-3 fade-in, 4-5 fade-out
assert all(fade(c, 3) == 0x0F for c in FULL[:16])                               # third fade-out step: everything black (beams excepted)
def rgb(ent, pal): return RGB[pal[ent]]
save([rgb(ENT[:178], p) for p in bgpals], 'spr_prison_far')
save([rgb(ENT[179:240], p) for p in bgpals], 'spr_prison_fence')
assert set(np.unique(ENT[178])) <= {0} or (rgb(ENT[178:179], FULL) == 0).all()

# searchlight beams: palette entries 15 (beam A, lit first) and 14 (beam B); colour $38 when lit, sky colour otherwise
assert FULL[13] == FULL[14] == FULL[15] == FULL[1]
info = {}
for name, e in (('spr_prison_beam_a', 15), ('spr_prison_beam_b', 14)):
    ys, xs = np.where(ENT[:178] == e); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    assert x0 >= 256                                                             # only on the second screen (scroll has ended by then)
    m = ENT[y0:y1, x0:x1] == e; imgs = []
    for col in [fade(0x38, L) for L in range(4)] + [int(FULL[1])]:           # sub-images 0-3: lit and its fade-out, 4: sky colour
        im = np.zeros(m.shape + (4,), np.uint8); im[m, :3] = RGB[col]; im[m, 3] = 255; imgs.append(im)
    save(imgs, name); info[name] = (int(x0) - 256, int(y0)); print('   screen position', info[name])
assert (S(1768)['pal'][13:16] & 0x3F == (0x01, 0x01, 0x38)).all() and (S(1832)['pal'][13:16] & 0x3F == (0x01, 0x38, 0x01)).all()

# ---------------------------------------------------------------- blimp: 11 sprites, 40x24
def blimp(p, pal, level):
    o = p['oam'].reshape(64, 4); sp = [(int(r[3]), int(r[0]) + 1, int(r[1]), int(r[2])) for r in o if r[0] < 239 and r[1] != 128]
    assert len(sp) == 11
    ax = max(s[0] for s in sp) - 32; ay = min(s[1] for s in sp)
    im = np.zeros((24, 40, 4), np.uint8)
    for x, y, t, a in reversed(sp):
        tl = tile(p['vram'], (0x1000 if p['ctrl'] & 8 else 0) + t * 16)
        if a & 0x40: tl = tl[:, ::-1]
        if a & 0x80: tl = tl[::-1]
        assert not a & 0x20
        m = tl > 0; col = np.array([fade(pal[16 + (a & 3) * 4 + i], level) for i in range(4)])[tl]
        reg = im[y - ay:y - ay + 8, x - ax:x - ax + 8]; reg[m, :3] = RGB[col[m]]; reg[m, 3] = 255
    return im
DARK = S(1400)['pal'] & 0x3F; LIT = S(1800)['pal'] & 0x3F
fa = next(f for f in range(1400, 1420) if any(r[1] == 192 and r[2] == 194 for r in S(f)['oam'].reshape(64, 4)))     # propeller frame 0
fb = next(f for f in range(1400, 1420) if any(r[1] == 192 and r[2] == 66 for r in S(f)['oam'].reshape(64, 4)))      # propeller frame 1
save([blimp(S(f), pal, L) for pal in (DARK, LIT) for L in range(4) for f in (fa, fb)], 'spr_prison_blimp')   # index = lit*8 + fade*2 + propeller

# ---------------------------------------------------------------- sound: the alarm, one 49-frame cycle (it is restarted every 49 frames)
def piece(f0, n, name):
    a = d['aud'].astype(np.float64) / 32768; c = d['cnt']
    x = a[c[f0 - 1]:c[f0 + n - 1]]; N = n * 800
    y = soxr.resample(x, len(x) * 60.0 / n, 48000, quality='VHQ')
    y = y[:N] if len(y) >= N else np.concatenate([y, np.zeros(N - len(y))])
    with sf.SoundFile('%s/sounds/%s.ogg' % (OUT, name), 'w', samplerate=48000, channels=1, format='OGG', subtype='VORBIS') as f:
        for i in range(0, len(y), 2048): f.write(y[i:i + 2048].astype(np.float32))
    print('%-18s frames %d samples %d peak %.3f' % (name, n, len(y), np.abs(y).max()))
    return y
c1 = piece(1768 + 49, 49, 'snd_prison_alarm')          # 2nd cycle (the first one starts from silence)
a = d['aud'].astype(np.float64) / 32768; c = d['cnt']
env = lambda f0: np.array([np.sqrt((a[c[f - 1]:c[f]] ** 2).mean()) for f in range(f0, f0 + 49)])
print('cycle envelopes: 1st vs 2nd corr %.4f, 2nd vs 5th corr %.4f' % (np.corrcoef(env(1768), env(1817))[0, 1], np.corrcoef(env(1817), env(1964))[0, 1]))
# loudness of the channel for each volume step 15..1 (used for the fade-out): measured on the natural fade at the end of the scene
ref = np.sqrt((a[c[2100]:c[2140]] ** 2).mean())
print('gain per volume (measured, frame 2249 + 4k has volume 14 - k):')
print('  ', [round(float(np.sqrt((a[c[2249 + 4 * k]:c[2253 + 4 * k]] ** 2).mean()) / ref), 3) for k in range(0, 12)])
print('   pulse DAC formula:', [round((95.88 / (8128 / v + 100)) / (95.88 / (8128 / 15 + 100)), 3) for v in range(14, 2, -1)])

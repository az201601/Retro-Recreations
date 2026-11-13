#!/usr/bin/env python3
"""Build the graphics and sounds of deliverable 2 from the capture_menu.py runs -> recreation/02_title_menu/assets"""
import os
import numpy as np, soxr, soundfile as sf
from PIL import Image
from scenario import load
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'recreation', '02_title_menu', 'assets')
os.makedirs(OUT + '/sprites', exist_ok=True); os.makedirs(OUT + '/sounds', exist_ok=True)
PX, PY, PW, PH = 48, 188, 160, 32          # menu panel rectangle on the 256x240 screen

# ---------------------------------------------------------------- graphics
R = {k: load('menu_' + k) for k in 'abcge'}
F = lambda k, f: R[k]['frames'][f - R[k]['f0']]
def par(k, f, p):      # frame f or f+1, whichever has NES frame parity p
    return F(k, f if f % 2 == p else f + 1)
panel = [F('a', 1001), F('a', 1002), F('a', 1003), F('a', 1101), F('c', 1101)]          # 0-4
panel += [par('c', 1110, 0), par('c', 1110, 1), par('c', 1210, 0), par('c', 1210, 1)]   # 5-8  Chip even/odd, Dale even/odd
panel += [F('b', 1161 + 4 * (k + 1)) for k in range(3)]                                 # 9-11 "2players" fading out
panel += [par('e', 1202 + 4 * (k + 1), p) for k in range(3) for p in (0, 1)]            # 12-17 Chip fading out
panel += [par('g', 1301 + 4 * (k + 1), p) for k in range(3) for p in (0, 1)]            # 18-23 Dale fading out
title = F('a', 995)
for i, x in enumerate(panel):
    rest = x.copy(); rest[PY:PY + PH, PX:PX + PW] = 0
    ref = title.copy(); ref[PY:PY + PH, PX:PX + PW] = 0
    if i < 9: assert (rest == ref).all(), i          # outside the panel nothing but the title picture
imgs = [x[PY:PY + PH, PX:PX + PW] for x in panel]
for i, x in enumerate(imgs): Image.fromarray(x).save('%s/sprites/spr_menu_%02d.png' % (OUT, i))
Image.fromarray(np.hstack(imgs)).save('%s/sprites/spr_menu_strip%d.png' % (OUT, len(imgs)))
outs = []
for k in range(3):
    x = F('b', 1165 + 4 * k).copy(); x[PY:PY + PH, PX:PX + PW] = 0
    for kk, r in (('e', 1202), ('g', 1301)):
        for j in (0, 1):
            y = F(kk, r + 4 * (k + 1) + j).copy(); y[PY:PY + PH, PX:PX + PW] = 0; assert (x == y).all()
    outs.append(x); Image.fromarray(x).save('%s/sprites/spr_title_out_%d.png' % (OUT, k))
Image.fromarray(np.hstack(outs)).save('%s/sprites/spr_title_out_strip3.png' % OUT)
assert F('b', 1177).max() == 0
print('sprites:', len(imgs), 'menu panels,', len(outs), 'title fade-out steps')

# ---------------------------------------------------------------- sound
def piece(d, f0, n, name, fade_in=0, fade_out=0):
    """n NES frames starting at frame f0, retimed to exactly 800 samples per frame"""
    a = d['aud'].astype(np.float64) / 32768; c = d['cnt']
    x = a[c[f0 - 1]:c[f0 + n - 1]]; N = n * 800
    y = soxr.resample(x, len(x) * 60.0 / n, 48000, quality='VHQ')
    y = y[:N] if len(y) >= N else np.concatenate([y, np.zeros(N - len(y))])
    if fade_in: y[:fade_in] *= np.linspace(0, 1, fade_in)
    if fade_out: y[-fade_out:] *= np.linspace(1, 0, fade_out)
    with sf.SoundFile('%s/sounds/%s.ogg' % (OUT, name), 'w', samplerate=48000, channels=1, format='OGG', subtype='VORBIS') as f:
        for i in range(0, len(y), 2048): f.write(y[i:i + 2048].astype(np.float32))
    chk, sr = sf.read('%s/sounds/%s.ogg' % (OUT, name))
    print('%-22s frames %4d  samples %7d  ogg %7d  peak %.3f' % (name, n, len(y), len(chk), np.abs(y).max()))
    return y
rest = piece(load('menu_aud_rest'), 326, 2880, 'snd_title_theme')        # everything except square 2
sq2 = piece(load('menu_aud_sq2'), 326, 2880, 'snd_title_theme_sq2')      # square 2 only
full = piece(load('menu_aud_full'), 326, 2880, '_full'); os.remove(OUT + '/sounds/_full.ogg')
err = full - (rest + sq2)
print('stems: rms full %.4f, rms (full - sum of stems) %.5f' % (np.sqrt((full ** 2).mean()), np.sqrt((err ** 2).mean())))
s = load('menu_aud_sfx')
piece(s, 1002, 12, 'snd_menu_select', fade_in=48, fade_out=48)   # square 2 carries the effect on frames +1..+12 after the reaction frame
piece(s, 1102, 10, 'snd_menu_move', fade_in=48, fade_out=48)     # +1..+10

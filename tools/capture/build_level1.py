#!/usr/bin/env python3
"""Deliverable 5 (level 1, section 1: map and camera): builds the background of the section and the level music.
  recreation/05_level1_map/assets/sprites/spr_lv1a_bg   8 screens of 256x240 in 7 brightness steps (sub-image = screen * 7 + step)
  recreation/05_level1_map/assets/sounds/snd_lv1_music_a / _b   the music loop without / only the 2nd square channel
  work/lv1_map.pkl   the tile map, as first seen on screen, and where it changed later (crates that were picked up)
Needs the capture_level1.py runs."""
import os, pickle
import numpy as np, soxr, soundfile as sf
from PIL import Image
from scenario import load
from emu import WORK
from ppu import tile, RGB
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'recreation', '05_level1_map', 'assets')
D0 = 1357            # 'skip' run: frame on which the level's music is started; the level's frame L = NES frame - (D0 + 7)
E0 = 3701            # 'route' run: frame on which the player leaves the screen on the right
COLS = 256           # the section is 8 screens = 256 tile columns wide
CAM_MAX = 1792

def scroll(s): return (s['t'] & 31) * 8 + s['x'] + ((s['t'] >> 10) & 1) * 256      # picture scroll, 0..511

def build_map():
    tiles = np.full((30, COLS), -1, int); attr = np.full((15, COLS // 2), -1, int); last = np.full((30, COLS), -1, int)
    changes = []; chr_ = None; base = 0
    for part in range(3):
        d = load('lv1_route%d' % part); f0 = d['f0']
        for i, s in enumerate(d['st']):
            f = f0 + i
            if s['mask'] == 0 or f > E0 + 20: continue
            r = s['ram']; cam = int(r[0x10]) + 256 * int(r[0x13]); v = s['vram']
            if chr_ is None: chr_ = v[:0x2000].copy()
            assert np.array_equal(chr_, v[:0x2000]), 'tile graphics change during the section'
            for c in range(cam // 8, min(cam // 8 + 33, COLS)):
                b = 0x2000 + ((c // 32) & 1) * 0x400; col = v[b + c % 32:b + 960:32].astype(int)
                if tiles[0, c] < 0: tiles[:, c] = col
                if last[0, c] >= 0 and (col != last[:, c]).any(): changes.append((f, c, [int(x) for x in np.nonzero(col != last[:, c])[0]]))
                last[:, c] = col
                a = v[b + 0x3C0 + (c % 32) // 4:b + 0x400:8].astype(int); sh = ((c % 32) >> 1 & 1) * 2
                for rr in range(15):
                    if attr[rr, c // 2] < 0: attr[rr, c // 2] = (a[rr // 2] >> (sh + (rr & 1) * 4)) & 3
        del d
    assert (tiles >= 0).all() and (attr >= 0).all()
    pix = np.zeros((240, COLS * 8), np.uint8)           # 2-bit pixel value and palette group of every map pixel
    for r in range(30):
        for c in range(COLS): pix[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = tile(chr_, int(tiles[r, c]) * 16)
    grp = np.kron(attr, np.ones((16, 16), int)).astype(np.uint8)
    return dict(tiles=tiles, attr=attr, changes=changes, pix=pix, grp=grp)

def palettes():
    """the 7 brightness steps: 0-2 fade-in, 3 normal, 4-6 fade-out (16 NES colours each)"""
    a = load('lv1_skip'); P = [a['st'][D0 + 7 + k - a['f0']]['pal'][:16].copy() for k in (5, 9, 13, 17)]; del a
    b = load('lv1_route2'); P += [b['st'][E0 + k - b['f0']]['pal'][:16].copy() for k in (5, 9, 13)]
    assert np.array_equal(b['st'][E0 - b['f0']]['pal'][:16], P[3])
    return [p & 0x3F for p in P]

def colour(M, pal):
    idx = np.where(M['pix'] > 0, pal[M['grp'] * 4 + M['pix']], pal[0])
    return RGB[idx]

def ogg(y, name):
    os.makedirs(OUT + '/sounds', exist_ok=True); p = '%s/sounds/%s.ogg' % (OUT, name)
    with sf.SoundFile(p, 'w', samplerate=48000, channels=1, format='OGG', subtype='VORBIS') as f:
        for i in range(0, len(y), 2048): f.write(y[i:i + 2048].astype(np.float32))
    print('%-18s %6.2f s  peak %.3f  %d bytes' % (name, len(y) / 48000, np.abs(y).max(), os.path.getsize(p)))

def music():
    LOOP = 1920; M0 = D0 + 1
    d = load('lv1_music'); sig = [tuple(w) for w in d['apu']]
    assert all(sig[i] == sig[i + LOOP] for i in range(M0, len(sig) - LOOP)), 'the music does not loop every 1920 frames'
    assert not any(w and w[0] == (0x400C, 0xF0) for w in d['apu'][M0:]), 'another sound starts during the recording'
    for name, out in (('lv1_music_rest', 'snd_lv1_music_a'), ('lv1_music_sq2', 'snd_lv1_music_b')):
        d = load(name); a = M0 + LOOP                      # second pass of the loop: nothing left over from the previous screen
        x = d['aud'][d['cnt'][a - 1]:d['cnt'][a + LOOP - 1]].astype(np.float64) / 32768
        y = soxr.resample(x, len(x) * 60.0 / LOOP, 48000, quality='VHQ'); N = LOOP * 800
        ogg(y[:N] if len(y) >= N else np.concatenate([y, np.zeros(N - len(y))]), out)

if __name__ == '__main__':
    M = build_map(); P = palettes(); M['pal'] = P
    os.makedirs(OUT + '/sprites', exist_ok=True)
    strip = Image.new('RGB', (256 * 56, 240))
    for sub, pal in enumerate(P):
        img = colour(M, pal)
        for scr in range(8):
            im = Image.fromarray(img[:, scr * 256:scr * 256 + 256]); k = scr * 7 + sub
            im.save('%s/sprites/spr_lv1a_bg_%d.png' % (OUT, k)); strip.paste(im, (k * 256, 0))
        if sub == 3: Image.fromarray(img).save(os.path.join(WORK, 'lv1_map_full.png'))
    strip.save('%s/sprites/spr_lv1a_bg_strip56.png' % OUT)
    pickle.dump(M, open(os.path.join(WORK, 'lv1_map.pkl'), 'wb'))
    ch = sorted({(c // 2, r[0] // 2) for f, c, r in M['changes']})
    print('map %dx%d tiles, %d places changed during the route (16x16 blocks at column,row): %s' % (COLS, 30, len(ch), ch))
    music()

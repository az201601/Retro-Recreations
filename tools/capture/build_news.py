#!/usr/bin/env python3
"""Deliverable 4 graphics: background, font and object frames of the newscaster cutscene, each in the 7 palette
versions (0-2 fade-in, 3 normal, 4-6 fade-out), plus the model data (work/news_model.pkl, work/news_gfx.pkl) used by
sim_news.py and gen_news_gml.py.  Needs the capture_news.py runs."""
import os, pickle
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
from ppu import tile, RGB
from news_model import idle, run, learn_cels, build_model, cel_key, SPR0, BLANK, T0
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'recreation', '04_newscaster', 'assets', 'sprites'); os.makedirs(OUT, exist_ok=True)
def save(imgs, name):
    for i, x in enumerate(imgs): Image.fromarray(x).save('%s/%s_%d.png' % (OUT, name, i))
    Image.fromarray(np.hstack(imgs)).save('%s/%s_strip%d.png' % (OUT, name, len(imgs)))
    print('%-14s %3d sub-images of %dx%d' % (name, len(imgs), imgs[0].shape[1], imgs[0].shape[0]))

I = idle(); runs = [I, run('news_bmash', 2), run('news_bslow', 3)]
M = build_model(I); pickle.dump(M, open(os.path.join(WORK, 'news_model.pkl'), 'wb'))
d = load('news_idle0'); st = d['st'][2340 - d['f0']]; v = st['vram']
L = st['lines']                                  # per scanline: v low, v high, fine x, $2000, $2001, CHR checksum (3 bytes)
assert st['ctrl'] & 0x28 == 0x08 and st['ctrl'] & 0x10 == 0           # 8x8 sprites from $1000, background from $0000
# the game switches CHR banks at the split, and the capture only has the tiles of the lower part: the text box (lines
# 0-79) and the font are cut out of the emulator's pictures instead
assert len(set(map(tuple, L[:80, 5:]))) == 1 and len(set(map(tuple, L[80:, 5:]))) == 1 and L[0, 5:].tolist() != L[80, 5:].tolist()
# ---- palettes
PF = (2314, 2318, 2322, 2340, M['last_clear'] + 46, M['last_clear'] + 50, M['last_clear'] + 54)
PALS = [np.frombuffer(I[f]['pal'], np.uint8) for f in PF]
assert all(I[f]['pal'] == I[2400]['pal'] for f in range(2326, M['last_clear'] + 46)) and set(I[M['last_clear'] + 58]['pal']) == {0x0F}
# ---- background: text box (nametable 1, rows 0-9) above the studio (nametable 0, rows 10-29); the split is at line 80
def entries(r, c):
    b = 0x2000; a = int(v[b + 0x3C0 + (r // 4) * 8 + c // 4]); sh = ((r >> 1) & 1) * 4 + ((c >> 1) & 1) * 2
    px = tile(v, int(v[b + r * 32 + c]) * 16)
    return np.where(px > 0, ((a >> sh) & 3) * 4 + px, 0)
ENT = np.zeros((240, 256), np.uint8)
for r in range(10, 30):
    for c in range(32): ENT[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = entries(r, c)
d5 = load('news_idle5')
def picture(f): dd = d if f < d['f0'] + len(d['frames']) else d5; return dd['frames'][f - dd['f0']]
bg = []
for f, p in zip(PF, PALS):
    im = RGB[p[ENT]]; im[:80] = picture(f)[:80]; bg.append(im)       # the text box is empty on all these frames
    assert I[f]['txt'] == I[2340]['txt']
save(bg, 'spr_news_bg')
# ---- font: every tile that is ever typed (upper halves on rows 3/5/7, lower halves on rows 4/6/8), cut out of the
# pictures of the idle run.  The text cells use one background palette; find which, to make the other 6 versions
tiles = sorted({x for p in M['pages'] for k, r, c, t, b in p['ticks'] if k == 0 for x in (t, b) if x >= 0})
where = {}
for p in M['pages']:
    t = p['first']
    for k, r, c, tp, bt in p['ticks']:
        if k == 0:
            where.setdefault(tp, (p['end'], r, c))
            if bt >= 0: where.setdefault(bt, (p['end'], r + 1, c))
chunk = {}
def pic_any(f):
    i = (f - 2296) // 1430
    if i not in chunk: chunk.clear(); chunk[i] = load('news_idle%d' % i)
    return chunk[i]['frames'][f - chunk[i]['f0']]
crops = {t: pic_any(f)[r * 8:r * 8 + 8, c * 8:c * 8 + 8].copy() for t, (f, r, c) in sorted(where.items(), key=lambda x: x[1][0])}
cols = {tuple(px) for im in crops.values() for px in im.reshape(-1, 3)}
grp = [g for g in range(4) if cols <= {tuple(RGB[PALS[3][g * 4 + i]]) for i in range(4)}]
used = sorted({int(c) for c in PALS[3][:16] if tuple(RGB[c]) in cols})          # NES colours of the text cells
def version(p, c):                                                             # the same colour in another palette version
    alt = {int(p[j]) for j in range(16) if PALS[3][j] == c and j // 4 in grp and j % 4}
    assert len(alt) == 1; return alt.pop()
font = []
for t in tiles:
    for p in PALS:
        im = np.zeros((8, 8, 3), np.uint8)
        for c in used: im[(crops[t] == RGB[c]).all(axis=2)] = RGB[0x0F if c == 0x0F else version(p, c)]
        font.append(im)
print('   text colours:', ['$%02X' % c for c in used])
save(font, 'spr_news_font')
# ---- object frames.  A frame (cel) is a list of 8x8 sprites; they are kept as single pieces because the picture depends
# on the order of all sprites on screen (overlaps, and the NES limit of 8 sprites per line)
cels = learn_cels(runs)
keys = sorted(k for k in cels if cels[k])
order = {}
for recs in runs:                                                     # order inside a cel = OAM order on even frames (first = in front)
    for f in sorted(recs):
        if not recs[f]['obj'] or f < T0 + 16 or f % 2: continue           # (no alternation during the fade-in)
        S = [s for s in recs[f]['spr'] if s != SPR0]
        for o in recs[f]['obj']:
            k = cel_key(o)
            if k in order or k not in cels or not cels[k] or not 24 <= o[3] <= 224: continue
            idx = [S.index((o[3] + dx, o[4] + dy, t, a)) for dx, dy, t, a in cels[k]]
            order[k] = [p for _, p in sorted(zip(idx, cels[k]))]
kinds = sorted({(t, a) for k in keys for dx, dy, t, a in order[k]})
imgs = []
for t, a in kinds:
    assert not a & 0x20
    px = tile(v, 0x1000 + t * 16)
    if a & 0x40: px = px[:, ::-1]
    if a & 0x80: px = px[::-1]
    for p in PALS:
        im = np.zeros((8, 8, 4), np.uint8); im[px > 0, :3] = RGB[p[16 + (a & 3) * 4 + px[px > 0]]]; im[px > 0, 3] = 255; imgs.append(im)
save(imgs, 'spr_news_piece')
celp = [[(dx, dy + 1, kinds.index((t, a))) for dx, dy, t, a in order[k]] for k in keys]      # dy + 1: sprites show one line lower
print('   %d cels, %d sprites in all; cel order:' % (len(keys), sum(map(len, celp))), keys)
pickle.dump(dict(tiles=tiles, keys=keys, cels=celp), open(os.path.join(WORK, 'news_gfx.pkl'), 'wb'))

"""The status, GAME OVER and continue screens of deliverable 10 (part of build_hurt.py)."""
import os, zlib
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
import ppu, build_enemies as BE
T0 = 2667                                   # NES frame of the 3rd fall in the gover runs
PICS = [0, 1, 2, 3, 4, 5, 23, 22, 6, 7, 8, 11, 9, 10, 12, 13]      # the port's picture numbers -> NES picture numbers
PRESS_C, PRESS_E = T0 + 482, T0 + 445       # the frames of the A button in hu_gover / hu_gover_end

class Run:
    """a recording stored in parts"""
    def __init__(s, name):
        s.names = [name] + [name + '_' + c for c in 'bcdefg' if os.path.exists(os.path.join(WORK, name + '_' + c + '.pkl'))]; s.d = None
    def part(s, f):
        if s.d is None or not s.d['f0'] <= f < s.d['f0'] + len(s.d['st']):
            s.d = None
            for n in s.names:
                d = load(n)
                if d['f0'] <= f < d['f0'] + len(d['st']): s.d = d; break
            assert s.d is not None, f
        return s.d
    def pic(s, f): d = s.part(f); return np.frombuffer(zlib.decompress(d['zframes'][f - d['f0']]), np.uint8).reshape(240, 256, 3).copy()
    def st(s, f): d = s.part(f); return d['st'][f - d['f0']]
    def sprites(s, f): return [(int(q[3]), int(q[0]), int(q[1]), int(q[2])) for q in s.st(f)['oam'].reshape(64, 4) if q[0] < 0xEF]

def rgba(im, clear=None):
    a = np.zeros(im.shape[:2] + (4,), np.uint8); a[:, :, :3] = im
    a[:, :, 3] = np.where((im == 0).all(axis=2) if clear is None else clear, 0, 255); return a
def strip(ims): return np.concatenate(ims, axis=1)
def bbox(mask):
    ys, xs = np.nonzero(mask); return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1

def find_pic(typ, body):
    """the picture and position (facing right) whose tiles are exactly these sprites"""
    have = sorted((x, y, t) for x, y, t, a in body)
    for c in PICS:
        lay = BE.cel(typ, c)
        if len(lay) != len(body) or sorted(t for dx, dy, t, a in lay) != sorted(t for x, y, t in have): continue
        dx, dy, t, a = lay[0]
        for x, y, tt in have:
            if tt != t: continue
            X = x + dx + 8; Y = y - dy
            if sorted((X - ddx - 8, Y + ddy, t2) for ddx, ddy, t2, a2 in lay) == have: return PICS.index(c), X, Y
    raise AssertionError(('no picture for', body))

def screens(g, tabs, OUT):
    def save(im, name): Image.fromarray(im).save('%s/sprites/%s.png' % (OUT, name)); print('%-34s %d x %d' % (name, im.shape[1], im.shape[0]))
    # ---- the status screen: everything inside the frame is sprites; the numbers are left out
    both = []; cells = [(96, 153), (104, 153), (104, 177)]
    for run in ('hu_select', 'dl_hu_select'):
        r = Run(run); im = r.pic(1445); sp = r.sprites(1445)
        ox = 80 if run.startswith('dl_') else 0      # Dale's half is 80 pixels further right
        assert sorted((x, y + 1) for x, y, t, a in sp if 0x30 <= t <= 0x39) == [(104 + ox, 153), (104 + ox, 177)], sp
        if run == 'hu_select':
            zero = im[153:161, 104:112].copy(); v = r.st(1440)['vram']; pal = r.st(1445)['pal']
            base = next(b for b in (0, 0x1000) if (np.array([[ppu.RGB[pal[16 + m] & 63] if m else (0, 0, 0) for m in row] for row in ppu.tile(v, b + 0x30 * 16)]) == zero).all())
            digs = [np.array([[ppu.RGB[pal[16 + m] & 63] if m else (0, 0, 0) for m in row] for row in ppu.tile(v, base + (0x30 + k) * 16)], np.uint8) for k in range(10)]
            assert (digs[2] == im[177:185, 104:112]).all()
        # where sprites overlap, the first of the NES sprite list is in front; the list is written forwards or backwards
        # (as on the last frame of the level before), so there are two pictures of each: 3 pixels differ
        im2 = r.pic(1840); sp2 = r.sprites(1840)
        assert sorted(q[:2] for q in sp2) == sorted(q[:2] for q in sp) and [q[:2] for q in sp2] == [q[:2] for q in sp][::-1]
        for x, y in cells: im[y:y + 8, x + ox:x + ox + 8] = 0; im2[y:y + 8, x + ox:x + ox + 8] = 0
        print('status screen, %s: the two pictures differ in %d pixels' % (run, int((im != im2).any(axis=2).sum())))
        both += [im, im2]
    save(strip(both), 'spr_status_strip4'); save(rgba(strip(digs)), 'spr_status_digit_strip10')
    tabs['status_cells'] = cells
    # ---- GAME OVER: the words are sprites, 64 x 16, and go down from y 89 to 121
    r = Run('hu_gover'); bgs = []; txt = []
    for l, t in enumerate((90, 94, 98, 102)):
        im = r.pic(T0 + t); sp = r.sprites(T0 + t)
        assert min(x for x, y, tt, a in sp) == 96 and max(x for x, y, tt, a in sp) == 152 and sorted(set(y for x, y, tt, a in sp)) == [88, 96], sp
        txt.append(im[89:105, 96:160].copy()); im[89:105, 96:160] = 0; bgs.append(im)
    for t in (356, 360, 364):                                   # fading out: other colours than fading in
        im = r.pic(T0 + t); txt.append(im[121:137, 96:160].copy()); im[121:137, 96:160] = 0; bgs.append(im)
    assert not r.pic(T0 + 368).any() and not r.pic(T0 + 89).any()
    ys = [min(y for x, y, tt, a in r.sprites(T0 + t)) + 1 for t in range(85, 356)]
    assert ys == [89 + min(max((t - 102) // 4, 0), 32) for t in range(85, 356)], 'GAME OVER moves differently'
    save(strip(bgs), 'spr_gameover_bg_strip7'); save(rgba(strip(txt)), 'spr_gameover_text_strip7')
    # ---- the continue screen
    up = r.pic(T0 + 400); down = r.pic(T0 + 420); after = r.pic(PRESS_C + 110)
    ax0, ay0, ax1, ay1 = bbox((up != down).any(axis=2)[:120])
    assert (ax1 - ax0, ay1 - ay0) == (8, 24) or (ax1 - ax0) <= 8, (ax0, ay0, ax1, ay1)
    ax = ax0 // 8 * 8; arrow_y = [ay0 // 8 * 8, (ay1 - 1) // 8 * 8]
    d = (up != after).any(axis=2); d[:176] = False; dx0, dy0, dx1, dy1 = bbox(d); cx, cy = dx0 // 8 * 8, dy0 // 8 * 8
    assert dx1 - cx <= 8 and dy1 - cy <= 8, (dx0, dy0, dx1, dy1)
    WX, WY, WW, WH = 96, 120, 32, 48           # where the dizzy character and its star are
    for x, y, t, a in r.sprites(T0 + 400) + r.sprites(T0 + 410) + r.sprites(T0 + 418): assert WX <= x and x + 8 <= WX + WW and WY <= y + 1 and y + 9 <= WY + WH, (x, y)
    def clean(im, l=0):
        # (the character's place is cut out of the fade-in pictures only: there spr_continue_wake is drawn over it)
        im = im.copy(); im[cy:cy + 8, cx:cx + 8] = 0
        if l < 3: im[WY:WY + WH, WX:WX + WW] = 0
        if l == 3: im[WY:WY + WH, WX:WX + WW] = after[WY:WY + WH, WX:WX + WW]
        for y in arrow_y: im[y:y + 8, ax:ax + 8] = 0
        return im
    bgs = []; arrows = []; wake = {0: [], 1: []}; digit = {}
    rl = Run('hu_gover_last'); rd = Run('dl_hu_gover')
    for l, t in enumerate((381, 385, 389, 393)):
        im = r.pic(T0 + t); bgs.append(clean(im, l)); arrows.append(im[arrow_y[0]:arrow_y[0] + 8, ax:ax + 8].copy())
        if l < 3:
            wake[0].append(im[WY:WY + WH, WX:WX + WW].copy()); im2 = rd.pic(T0 + t); wake[1].append(im2[WY:WY + WH, WX:WX + WW].copy())
            assert (clean(im2, l) == bgs[l]).all()
        for c in range(3):                                      # hu_gover_last: a game over every 1760 frames, with 3, 2, 1 credits
            im3 = rl.pic(T0 + c * 1760 + t); assert (clean(im3, l) == bgs[l]).all()
            digit[(3 - c, l)] = im3[cy:cy + 8, cx:cx + 8].copy()
    assert not r.pic(T0 + 380).any()
    digit[(0, 3)] = rl.pic(T0 + 2 * 1760 + 463 + 60)[cy:cy + 8, cx:cx + 8].copy()
    for c in range(3):                                          # fading out after CONTINUE (A on frame 463 of each round): one credit less
        for l, k in ((4, 126), (5, 130), (6, 134)):
            im3 = rl.pic(T0 + c * 1760 + 463 + k)
            if c == 0: bgs.append(clean(im3, l)); arrows.append(im3[arrow_y[0]:arrow_y[0] + 8, ax:ax + 8].copy())
            assert (clean(im3, l) == bgs[l]).all()
            digit[(2 - c, l)] = im3[cy:cy + 8, cx:cx + 8].copy()
        assert not rl.pic(T0 + c * 1760 + 463 + 138).any()
    re_ = Run('hu_gover_end')
    for l, k in ((4, 66), (5, 70), (6, 74)):                    # END: the same fade, the number stays
        im3 = re_.pic(PRESS_E + k); assert (clean(im3, l) == bgs[l]).all(); digit[(3, l)] = im3[cy:cy + 8, cx:cx + 8].copy()
        assert (im3[arrow_y[1]:arrow_y[1] + 8, ax:ax + 8] == arrows[l]).all()
    for l in range(7): digit.setdefault((0, l), digit[(0, 3)])  # "0" is never seen fading in
    # the picture's background colour (black) is transparent: the character walks / falls behind the picture
    # (only above the ground: the black band below it hides the character that END throws out)
    allbg = strip(bgs); clear = (allbg == 0).all(axis=2); clear[168:] = False
    save(rgba(allbg, clear), 'spr_continue_bg_strip7'); save(rgba(strip(arrows)), 'spr_continue_arrow_strip7')
    save(rgba(strip([digit[(dg, l)] for dg in range(4) for l in range(7)])), 'spr_continue_digit_strip28')
    save(rgba(strip(wake[0] + wake[1])), 'spr_continue_wake_strip6')
    star = [q for q in r.sprites(T0 + 400) if q[2] == 0x5E][0]
    save(rgba(up[star[1] + 1:star[1] + 9, star[0]:star[0] + 8]), 'spr_continue_star')
    # the star: 7 places, 4 frames each, from frame 394 on (place 0 before)
    stars = []
    for t in range(394, 422, 4): q = [q for q in r.sprites(T0 + t) if q[2] == 0x5E][0]; stars.append((q[0], q[1]))
    for t in range(376, 482):
        q = [q for q in r.sprites(T0 + t) if q[2] == 0x5E][0]; assert (q[0], q[1]) == stars[((t - 394) // 4) % 7 if t >= 394 else 0], t
    # the character: dizzy at (112, 160); after the choice the pictures and places frame by frame (from 2 frames after the button)
    def anim(run, typ, press):
        out = []; k = 2
        while True:
            body = [q for q in run.sprites(press + k) if q[2] != 0x5E]
            if not body: break
            assert all(q[3] & 0x60 == 0x60 for q in body), body          # mirrored (facing right), behind the picture
            out.append(find_pic(typ, body)); k += 1
        assert not run.sprites(press + k + 1) and not run.sprites(press + k + 10)
        return out
    rde = Run('dl_hu_gover_end')
    for run, typ in ((r, 1), (rd, 2)):
        assert find_pic(typ, [q for q in run.sprites(T0 + 400) if q[2] != 0x5E]) == (15, 112, 160)
        assert sorted(q for q in run.sprites(PRESS_C + 1) if q[2] != 0x5E) == sorted(q for q in run.sprites(T0 + 400) if q[2] != 0x5E)
    ac = anim(r, 1, PRESS_C); ae = anim(re_, 1, PRESS_E)
    assert anim(rd, 2, PRESS_C) == ac and anim(rde, 2, PRESS_E) == ae, 'Dale moves differently'
    print('continue: arrow at x %d, y %s; credit digit at (%d, %d); CONTINUE %d frames, END %d frames' % (ax, arrow_y, cx, cy, len(ac), len(ae)))
    # the fades after the choice: 23 frames after the character has gone
    for run, press, n in ((r, PRESS_C, len(ac)), (re_, PRESS_E, len(ae))):
        k = press + 2 + n + 22
        assert (clean(run.pic(k - 1), 4) == clean(run.pic(press + 2 + n), 4)).all() and (clean(run.pic(k), 4) != clean(run.pic(k - 1), 4)).any(), 'fade after the choice'
    tabs.update(go_cont=ac, go_end=ae, go_star=stars, go_arrow=(ax, arrow_y), go_digit=(cx, cy), go_wake=(WX, WY))
    g.append('// the continue screen: the star goes round the head (7 places, 4 frames each)')
    g.append(' '.join('go_sx[%d] = %d; go_sy[%d] = %d;' % (i, x, i, y + 1) for i, (x, y) in enumerate(stars)))
    for nm, a, what in (('c', ac, 'CONTINUE: gets up with a jump, runs off to the right'), ('e', ae, 'END: thrown out to the lower left')):
        g.append('// %s.  Picture, x, y on the frames 2, 3, ... after the A button (%d frames)' % (what, len(a)))
        g.append('go_%sn = %d;' % (nm, len(a)))
        for i in range(0, len(a), 8):
            g.append(' '.join('go_%sp[%d] = %d; go_%sx[%d] = %d; go_%sy[%d] = %d;' % (nm, j, a[j][0], nm, j, a[j][1], nm, j, a[j][2]) for j in range(i, min(i + 8, len(a)))))
    g.append('')

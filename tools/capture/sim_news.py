#!/usr/bin/env python3
"""Python port of the newscaster part of obj_intro (section 6 of Step, last block of Draw), run on the same tables as
the GML (work/news_data.pkl) and compared with the capture_news.py recordings: every picture, and the frames on which
a typing sound starts.   Keep in sync with recreation/04_newscaster/gml/obj_intro_*.gml
usage: sim_news.py [run names]"""
import os, sys, pickle
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
from news_model import T0
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = pickle.load(open(os.path.join(WORK, 'news_data.pkl'), 'rb'))
PAGES = D['pages']; NP = len(PAGES); SEGS = D['segs']; TRK = D['trk']; BALL = D['ball']; STAR = D['spin']; NA = len(D['names'])
A = os.path.join(ROOT, 'recreation', '04_newscaster', 'assets', 'sprites') + '/'
def ld(name, n): return [np.array(Image.open('%s%s_%d.png' % (A, name, i)).convert('RGBA')) for i in range(n)]
BG = [x[..., :3] for x in ld('spr_news_bg', 7)]; FONT = [x[..., :3] for x in ld('spr_news_font', D['nglyph'] * 7)]
PIECE = ld('spr_news_piece', 7 * (1 + max(p[2] for c in D['cels'] for p in c)))
START_, B_ = 1, 32                                # pad bits of the GML code

class News:
    def __init__(s, pad_prev=0):
        s.t = -13; s.pad_prev = pad_prev; s.b_held_prev = 0; s.b_edge_prev = 0
        s.k = 0; s.mode = 0; s.g0 = 0; s.gstart = [0] + [-1] * NP          # page, 0 waiting / 1 typing / 2 standing
        s.ti = 0; s.next_tick = -1; s.fast = 0; s.end = -1; s.clear_t = -100; s.ncol = 0
        s.text = [0] * (9 * 32)                   # glyph + 1 of every text cell (rows 3-8)
        s.mouth = 0; s.mouth_shown = 0; s.speaker = -1
        s.seg = [-1] * NA; s.seg_t0 = [0] * NA; s.slot = [2] + [-1] * (NA - 1)
        s.ac = [0] * NA; s.ax = [0] * NA; s.ay = [0] * NA                  # this frame's cel + 1, x, y of every actor
        s.ball_left = -1; s.ball_y = 0
        s.exit_t = -1; s.fade_t0 = -1; s.fade_at1 = -1; s.fade_at2 = -1; s.skipped = False; s.lv = 0; s.quiet = 0
        s.done = False; s.snd_skip = -1
        s.type_at = -100; s.busy_until = -100; s.gate = 1; s.pend = 0
        s.type_log = []; s.gate_log = {}          # for the checks
    def actor(s, ai, t):                          # 6d: where an actor is on frame t -> (cel + 1, x, y)
        if s.seg[ai] < 0: return (0, 0, 0)
        i = t - s.seg_t0[ai]
        if ai == BALL['actor'] and i >= BALL['hover']:
            if s.ball_left >= 0:
                c, x, y = TRK[BALL['p0'] + min(t - s.ball_left, BALL['n'] - 1)]
                return (c, x, y - 128 + s.ball_y)
            c = (i - BALL['hover']) % 252
            return ((BALL['cel2'] if c >= 240 else BALL['cel']) + (c % 6) // 3, BALL['x'], BALL['hy'][c % 12])
        sg = SEGS[s.seg[ai]]
        return TRK[sg['p0'] + min(i, sg['n'] - 1)]
    def free_slot(s):
        n = 3
        while n in s.slot: n += 1
        return n
    def step(s, pad):
        s.t += 1; t = s.t
        pressed = pad & ~s.pad_prev; s.pad_prev = pad
        if s.done: return
        # ---- 6a) leaving (same mechanism as the night scene)
        if (pressed & START_) and t >= 13 and not s.skipped and (s.exit_t < 0 or t < s.exit_t + 55):
            s.skipped = True; s.fade_at1 = t + 34; s.snd_skip = t + 1
            if s.exit_t < 0: s.exit_t = t
        if s.fade_t0 >= 0 and t > s.fade_t0 and (t - s.fade_t0) % 4 == 0: s.lv = min(s.lv + 1, 4)
        if s.exit_t >= 0 and t > s.exit_t and (t - s.exit_t) % 4 == 0 and s.quiet < 11: s.quiet += 1
        if t == s.fade_at1 or t == s.fade_at2: s.fade_t0 = t
        if s.exit_t >= 0 and t == s.exit_t + 57: s.done = True; return
        # ---- 6b) text
        s.mouth_shown = s.mouth
        if s.mode == 0 and s.k < NP and t == s.g0 + PAGES[s.k]['pre']:
            s.mode = 1; s.ti = 0; s.next_tick = t; s.fast = 0; s.ncol = 0; s.speaker = PAGES[s.k]['speaker']
        if s.mode == 0 and s.k == NP and t == s.g0 + 8:                 # end of the script
            s.fade_at2 = t + 34
            if s.exit_t < 0: s.exit_t = t
        if s.mode == 1:
            if t == s.next_tick:
                kind, r, c, top, bot = PAGES[s.k]['ticks'][s.ti]; s.ti += 1
                if kind == 0:
                    s.text[r * 32 + c] = top
                    if bot: s.text[(r + 1) * 32 + c] = bot
                if kind == 2: s.ncol = 0; s.next_tick = t + 1
                else:
                    s.ncol += 1
                    if s.fast: s.next_tick = t + 1
                    else:
                        s.next_tick = t + 5
                        if t != s.snd_skip: s.type_at = t + 1
                s.mouth = (s.ncol >> 1) & 1
                if s.ti == len(PAGES[s.k]['ticks']): s.mode = 2; s.end = s.next_tick
            if s.b_held_prev: s.fast = 1
        elif s.mode == 2:
            if t == s.end + 120 or (t > s.end and s.b_edge_prev):
                s.clear_t = t; s.mouth = 0; s.k += 1; s.g0 = t; s.gstart[s.k] = t; s.mode = 0
        s.b_held_prev = pad & B_; s.b_edge_prev = pressed & B_
        for r, d in D['clear_at'].items():
            if t == s.clear_t + d:
                for c in range(32): s.text[r * 32 + c] = 0
        # ---- 6c) sound: typing sound, and the gate of the music's square-2 layer
        if t == s.type_at: s.type_log.append(t); s.gate = 0; s.pend = 0; s.busy_until = t + 3
        if t >= D['m0'] and ((t - D['m0']) % D['loop']) in NOTES: s.pend = 1
        if t > s.busy_until:
            if s.pend: s.gate = 1
            s.pend = 0
        s.gate_log[t] = s.gate
        # ---- 6d) actors
        for si, sg in enumerate(SEGS):
            if s.gstart[sg['gap']] >= 0 and t == s.gstart[sg['gap']] + sg['off']: s.seg[sg['actor']] = si; s.seg_t0[sg['actor']] = t
        bi = BALL['actor']                        # Zipper flies on at the start of a half loop once the script has released him
        if s.seg[bi] >= 0 and s.ball_left < 0 and s.gstart[BALL['rel_gap']] >= 0 and t >= s.gstart[BALL['rel_gap']] + BALL['rel_off']:
            i = t - s.seg_t0[bi] - BALL['hover']; c = i % 252
            if i > 0 and c % 6 == 0 and c > 0 and c < 240: s.ball_y = s.ay[bi]; s.ball_left = t
        for ai in range(NA): s.ac[ai], s.ax[ai], s.ay[ai] = s.actor(ai, t)
        for ai in range(1, NA):                   # object slots: lowest free one from 3 up (Chip has slot 2)
            if s.ac[ai] == 0: s.slot[ai] = -1
            elif s.slot[ai] < 0: s.slot[ai] = s.free_slot()
        si = STAR['actor']                        # the star shows a frame earlier when its slot comes after Dale's
        if s.seg[si] >= 0 and t - s.seg_t0[si] == STAR['first'] - 1 and s.free_slot() > s.slot[STAR['parent']]:
            s.seg_t0[si] -= 1; s.slot[si] = s.free_slot(); s.ac[si], s.ax[si], s.ay[si] = s.actor(si, t)
        if s.speaker >= 0 and s.mouth_shown and D['open'][s.ac[s.speaker]]: s.ac[s.speaker] = D['open'][s.ac[s.speaker]]
    def draw(s):
        scr = np.zeros((240, 256, 3), np.uint8); t = s.t
        sub = min(t // 4, 3) if s.lv == 0 else 3 + s.lv      # 0-2 fade-in, 3 normal, 4-6 fade-out
        if t < 0 or s.done or sub >= 7 or (s.exit_t >= 0 and t >= s.exit_t + 55): return scr
        scr[:] = BG[sub]
        for r in range(3, 9):
            for c in range(2, 29):
                g = s.text[r * 32 + c]
                if g: scr[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = FONT[(g - 1) * 7 + sub]
        # sprites: objects in slot order on even frames, the whole list reversed on odd ones; the first sprite is in
        # front, and only the first 8 sprites on a line are shown
        lst = []
        for slot in range(2, 2 + NA):
            for ai in range(NA):
                if s.slot[ai] == slot and s.ac[ai]:
                    lst += [(s.ax[ai] + dx, s.ay[ai] + dy, pi) for dx, dy, pi in D['cels'][s.ac[ai] - 1] if 0 <= s.ax[ai] + dx <= 255]
        if t & 1: lst = lst[::-1]
        cnt = [0] * 264; rows = []
        for x, y, pi in lst:
            assert 0 <= y <= 255, y              # the GML code indexes an array with it
            m = 0
            for r in range(8):
                cnt[y + r] += 1
                if cnt[y + r] <= 8: m |= 1 << r
            rows.append(m)
        for i in range(len(lst) - 1, -1, -1):
            x, y, pi = lst[i]; img = PIECE[pi * 7 + sub]
            for r in range(8):
                if rows[i] >> r & 1 and y + r < 240:
                    x1 = min(x + 8, 256); m = img[r, :x1 - x, 3] > 0
                    scr[y + r, x:x1][m] = img[r, :x1 - x, :3][m]
        scr[:, :8] = BG[sub][:, :8]                          # the NES hides sprites in the 8 left columns
        return scr
NOTES = set(D['notes'])

def pad_of(keys): return (START_ if 3 in keys else 0) | (B_ if 0 in keys else 0)

def check(name, chunks, sched):
    g = News(); bad = []; n = 0; f = T0 - 12; mk = []; span = []
    for ch in chunks:
        d = load(ch); f0 = d['f0']
        while f < f0 + len(d['frames']):
            g.step(pad_of(sched.get(f, ())))
            if g.done: break
            if f >= f0:
                n += 1; span.append(f)
                if not np.array_equal(g.draw(), d['frames'][f - f0]): bad.append(f)
                w = d['apu'][f - f0]
                if w and w[0] == (0x400C, 0xF0) and f > T0: mk.append(f + 1)      # sound driver starts a sound; audible a frame later
            f += 1
        del d
    snd = [x + T0 for x in g.type_log if span[0] < x + T0 <= span[-1]]; mk = [x for x in mk if x <= span[-1]]
    ok = mk == snd
    print('%-12s frames %5d  picture mismatches %3d %s | typing sounds %3d %s | ends t=%s' % (
        name, n, len(bad), bad[:6], len(snd), 'ok' if ok else 'DIFFER %s %s' % (sorted(set(mk) - set(snd))[:4], sorted(set(snd) - set(mk))[:4]),
        g.exit_t + 57 if g.exit_t >= 0 else None))
    return n, len(bad), 0 if ok else 1

if __name__ == '__main__':
    import capture_news as C
    groups = {}
    for j in C.JOBS:
        if j[0].startswith('news_aud'): continue
        base = j[0].rstrip('0123456789') if j[0].startswith(('news_idle', 'news_bmash', 'news_bslow')) else j[0]
        groups.setdefault(base, ([], j[1])); groups[base][0].append(j[0])
    tot = nb = sb = 0
    for name, (chunks, sched) in groups.items():
        if len(sys.argv) > 1 and name not in sys.argv[1:]: continue
        n, b, s_ = check(name, chunks, sched); tot += n; nb += b; sb += s_
    print('frames compared %d, picture mismatches %d, runs with a typing-sound difference %d' % (tot, nb, sb))

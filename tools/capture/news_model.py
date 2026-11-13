#!/usr/bin/env python3
"""Deliverable 4 (newscaster cutscene): turn the idle recording into the cutscene model
(text pages, script blocks, actor tracks, sprite cels).  Used by build_news.py and sim_news.py.
NES frame numbers of the idle run; scene frame t = NES frame - T0."""
import os, pickle, collections
import numpy as np
from scenario import load
from emu import WORK
T0 = 2314                      # first visible frame of the cutscene in the idle run
END = 10836                    # first black frame after the natural fade-out
NCH = 6                        # idle run is stored in 6 chunks: work/news_idle<i>.pkl

def obj_state(r, i):
    """object slot i from the game's object tables (RAM): frame id, flip, head/mouth variant, x, y, hidden"""
    x = int(r[0x314 + i]) + 256 * int(r[0x320 + i]); x = x - 65536 if x >= 32768 else x
    return (int(r[0x338 + i]), int(r[0x32C + i]), int(r[0x3A4 + i]), x, int(r[0x2FC + i]), int(r[0x2F0 + i]))

def compact(names, cache):
    """per-frame records of a run stored in chunks: sprites (OAM order), text nametable, palette, object slots, APU writes"""
    path = os.path.join(WORK, cache + '.pkl')
    if os.path.exists(path): return pickle.load(open(path, 'rb'))
    recs = {}; prev_ram = None
    for nm in names:
        d = load(nm); f0 = d['f0']
        for k, s in enumerate(d['st']):
            o = s['oam'].reshape(64, 4)
            recs[f0 + k] = dict(spr=[(int(r[3]), int(r[0]), int(r[1]), int(r[2])) for r in o if r[0] < 239],
                                txt=bytes(s['vram'][0x2400:0x27C0]), pal=bytes(s['pal'] & 0x3F), mask=int(s['mask']), apu=d['apu'][k],
                                obj=None if prev_ram is None else [obj_state(prev_ram, i) for i in range(12)])
            prev_ram = s['ram']
        del d
    pickle.dump(recs, open(path, 'wb'), protocol=4)
    return recs

def idle(): return compact(['news_idle%d' % i for i in range(NCH)], 'news_idle_compact')

def text_events(recs, a, b):
    """[(frame, [(row, col, tile), ...])] for every frame on which the text box changes"""
    out = []; prev = recs[a - 1]['txt']
    for f in range(a, b):
        nt = recs[f]['txt']
        if nt != prev:
            out.append((f, [(j // 32, j % 32, nt[j]) for j in range(0x3C0) if nt[j] != prev[j]]))
        prev = nt
    return out

BLANK = 0x40
SPR0 = (16, 77, 128, 32)                       # sprite 0 (split marker, invisible)
def pages(recs, a=T0, b=END):
    """split the text events into pages.  page = dict(clear=frame the box starts to clear (None for the first),
    ticks=[(frame, row, col, top tile, bottom tile or None)], lines=[[(col, top, bottom)]])"""
    ev = text_events(recs, a, b); out = []; cur = None; clear = None; last_clear = None
    for f, cells in ev:
        if all(t == BLANK for r, c, t in cells):
            if cur: out.append(cur); cur = None
            if last_clear is None or f - last_clear > 8: clear = f
            last_clear = f; continue
        if cur is None: cur = dict(clear=clear, ticks=[], clear_rows={})
        top = [x for x in cells if x[0] in (3, 5, 7)]; bot = [x for x in cells if x[0] in (4, 6, 8)]
        assert len(top) == 1 and len(bot) <= 1, (f, cells)
        cur['ticks'].append((f, top[0][0], top[0][1], top[0][2], bot[0][2] if bot else None))
    if cur: out.append(cur)
    return out, clear          # clear = start of the last clear (after the last page)

def tick_times(lines, t0, fast_from=None):
    """frames of every tick of a page typed at normal speed: returns [(frame, line, col or -1 for newline / -2 for end)]"""
    out = []; t = t0
    for li, ln in enumerate(lines):
        for col in range(2, ln[-1][0] + 1):
            out.append((t, li, col)); t += 5
        if li < len(lines) - 1: out.append((t, li, -1)); t += 1
    out.append((t, len(lines) - 1, -2))
    return out

def cel_key(o): return (o[0], o[1], o[2], o[5])
def learn_cels(runs, a=T0 + 1):
    """cel = the sprites of one object relative to its position.  key = (frame id, flip, variant, flags).
    Learned as the intersection over all frames in which the object is completely on screen; sprites of another
    object that always stands at the same distance are then removed (every sprite belongs to one object only)."""
    cand = {}
    frames = [(recs[f]['spr'], recs[f]['obj']) for recs in runs for f in sorted(recs) if f >= a and recs[f]['obj'] and recs[f]['mask']]
    for S, objs in frames:
        for o in objs:
            if not 24 <= o[3] <= 224 or o[5] != 1: continue
            rel = frozenset((sx - o[3], sy - o[4], t, at) for sx, sy, t, at in S if (sx, sy, t, at) != SPR0)
            k = cel_key(o); cand[k] = rel if k not in cand else cand[k] & rel
    cand = {k: set(v) for k, v in cand.items()}
    while True:
        alone = set(); shared = collections.defaultdict(set)
        for S, objs in frames:
            claim = collections.defaultdict(list)
            for o in objs:
                k = cel_key(o)
                for p in cand.get(k, ()):
                    claim[(o[3] + p[0], o[4] + p[1], p[2], p[3])].append((k, p))
            for sp, cl in claim.items():
                if len(set(cl)) == 1: alone.add(cl[0])
                else:
                    for c in cl: shared[c] |= set(cl) - {c}
        drop = [c for c in shared if c not in alone and any(o in alone for o in shared[c])]
        if not drop: break
        for k, p in drop: cand[k].discard(p)
    assert all(c in alone for c in shared)
    return {k: frozenset(v) for k, v in cand.items()}

def obj_sprites(o, cels):
    x, y = o[3], o[4]
    return [(x + dx, y + dy, t, at) for dx, dy, t, at in cels.get(cel_key(o), ()) if 0 <= x + dx <= 255]

def run(name, n): return compact(['%s%d' % (name, i) for i in range(n)], name + '_compact')

# ---------------------------------------------------------------------------------------------------------------------
# the model
# actors = objects of the idle run: (name, slot, first frame, last frame + 1)
ACTORS = [('chip', 2, T0, END), ('gadget', 3, 3833, 7515), ('monty', 4, 5453, 7912),
          ('zipper', 3, 7515, 8615), ('dale', 4, 7912, END), ('star', 3, 8615, END)]

def mouth_frames(ticks, t0):
    """frames on which the speaker's mouth changes: open = bit 1 of the number of ticks done in the current line,
    shown one frame after the tick"""
    out = []; t = t0; n = 0; m = 0
    for tk in ticks:
        n = 0 if tk[0] == 2 else n + 1
        if (n >> 1) & 1 != m: m ^= 1; out.append(t + 1)
        t += 1 if tk[0] == 2 else 5
    return out, t

def build_pages(recs):
    pg, last_clear = pages(recs); out = []
    for k, p in enumerate(pg):
        first = p['ticks'][0][0]; nxt = pg[k + 1]['clear'] if k + 1 < len(pg) else last_clear
        rows = {}
        for f, r, c, t, b in p['ticks']: rows.setdefault(r, []).append((f, c, t, b))
        ticks = []; t = first; lastrow = max(rows)
        for r in (3, 5, 7):
            if r > lastrow: break
            if r < min(rows): continue                      # the page starts lower down (no time passes)
            if r in rows:
                cells = {c: (f, tp, b) for f, c, tp, b in rows[r]}; last = max(cells)
                assert rows[r][0][1] == 2 or True
                for c in range(2, last + 1):
                    if c in cells:
                        assert cells[c][0] == t, (k, r, c, cells[c][0], t)
                        ticks.append((0, r, c, cells[c][1], cells[c][2] if cells[c][2] is not None else -1))
                    else: ticks.append((1, r, c, 0, 0))
                    t += 5
                # blank ticks at the end of the line (only visible as time)
                nr = min([x for x in rows if x > r], default=None)
                target = (rows[nr][0][0] - (nr - r) // 2) if nr else nxt - 120
                while t + 5 <= target: ticks.append((1, r, 0, 0, 0)); t += 5
            if r < lastrow: ticks.append((2, r, 0, 0, 0)); t += 1
        # the box is cleared 120 frames after the last tick, top row first (empty first row: visible 3 frames later)
        assert nxt - 120 - t == (min(rows) - 3) // 2 * 3, (k, nxt - 120 - t)
        out.append(dict(first=first, ticks=ticks, end=t, clear=t + 120))
    return out

CLEAR_AT = {3: 0, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6}       # text-box row -> frames after the clear starts

def build_model(recs):
    P = build_pages(recs); n = len(P)
    gaps = [T0] + [p['clear'] for p in P]                        # gap k = from the clear of page k-1 to the first tick of page k
    pre = [P[k]['first'] - gaps[k] for k in range(n)]
    # predicted mouth state per frame and page
    mouth = {}
    for k, p in enumerate(P):
        tg, _ = mouth_frames(p['ticks'], p['first']); tg = tg + ([p['clear'] + 1] if len(tg) % 2 else [])
        for a, b in zip(tg[0::2], tg[1::2]):
            for f in range(a, b): mouth[f] = k
    def state(slot, f):
        o = recs[f]['obj'][slot]
        if slot == 3 and f == 8747: o = o[:5] + (1,)             # drawn one frame longer than its flag says
        return o
    # speaker of each page: the actor whose frame changes exactly with the predicted mouth
    for k, p in enumerate(P):
        p['speaker'] = -1; p['open'] = {}
        tg, _ = mouth_frames(p['ticks'], p['first'])
        if not tg: continue
        for ai, (nm, slot, a, b) in enumerate(ACTORS):
            if all(a <= f < b and state(slot, f)[:3] != state(slot, f - 1)[:3] for f in tg): p['speaker'] = ai
        ai = p['speaker']
        if ai < 0: continue
        slot = ACTORS[ai][1]; closed = collections.Counter(); opn = collections.defaultdict(collections.Counter)
        # closed frame = most recent state while the mouth is predicted closed
        last = None
        for f in range(p['first'], p['clear'] + 2):
            st = state(slot, f)[:3]
            if f in mouth:
                if last is not None: opn[last][st] += 1
            else: last = st
        for c, cnt in opn.items():
            o = cnt.most_common(1)[0][0]
            if o != c: p['open'][c] = o
    # actor segments
    actors = []
    for ai, (nm, slot, a, b) in enumerate(ACTORS):
        def base(f):
            st = state(slot, f)
            if f in mouth and P[mouth[f]]['speaker'] == ai:
                inv = {v: c for c, v in P[mouth[f]]['open'].items()}
                if st[:3] in inv: st = inv[st[:3]] + st[3:]
            return st
        segs = []
        bounds = [g for g in gaps if a <= g < b]
        if not bounds or bounds[0] != a: bounds = [a] + bounds
        for i, g in enumerate(bounds):
            e = bounds[i + 1] if i + 1 < len(bounds) else b
            tr = [base(f) for f in range(g, e)]
            if segs and all(x == segs[-1]['track'][-1] for x in tr): continue          # nothing happens: no command
            gi = gaps.index(g) if g in gaps else max(j for j in range(len(gaps)) if gaps[j] <= g)
            segs.append(dict(gap=gi, off=g - gaps[gi], track=tr))
        # a segment runs until the next one of the same actor starts
        for i, sg in enumerate(segs):
            g0 = gaps[sg['gap']] + sg['off']
            e = gaps[segs[i + 1]['gap']] + segs[i + 1]['off'] if i + 1 < len(segs) else b
            tr = [base(f) for f in range(g0, e)]
            while len(tr) > 1 and tr[-1] == tr[-2]: tr.pop()
            sg['track'] = tr
        actors.append(dict(name=nm, segs=segs))
    # Zipper: flies in, then hovers on its own clock (6-frame half loops; after 40 of them 2 with other frames),
    # is released 9 frames after the clear of page 15 and flies on at the next half loop.  Heights after that are
    # relative to where the hover stopped.
    bi = [a[0] for a in ACTORS].index('zipper'); slot = ACTORS[bi][1]
    spawn = gaps[actors[bi]['segs'][0]['gap']] + actors[bi]['segs'][0]['off']
    hov = gaps[16] + 1 - 240; leave = gaps[16] + 19
    hy = [state(slot, hov + i)[4] for i in range(12)]
    for f in range(hov, leave):
        c = (f - hov) % 252
        assert state(slot, f) == ((52 if c >= 240 else 23) + (c % 6) // 3, 0, 0, 148, hy[c % 12], 1), f
    y0 = state(slot, leave - 1)[4]
    tr = [state(slot, f) for f in range(leave, ACTORS[bi][3])]
    while len(tr) > 1 and tr[-1] == tr[-2]: tr.pop()
    ball = dict(actor=bi, hover=hov - spawn, hy=hy, x=148, release=(16, 9), leave=[(o[0], o[1], o[2], o[3], o[4] - y0, o[5]) for o in tr])
    actors[bi]['segs'] = actors[bi]['segs'][:1]; actors[bi]['segs'][0]['track'] = actors[bi]['segs'][0]['track'][:hov - spawn]
    # the star is created by Dale; it shows one frame earlier when its object slot comes after his
    si = [a[0] for a in ACTORS].index('star'); tr = actors[si]['segs'][0]['track']
    spin = dict(actor=si, parent=[a[0] for a in ACTORS].index('dale'), first=min(i for i, o in enumerate(tr) if o[5] == 1))
    return dict(spin=spin, ball=ball, pages=P, gaps=gaps, pre=pre, actors=actors, last_clear=gaps[-1])

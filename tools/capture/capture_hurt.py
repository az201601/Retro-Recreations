#!/usr/bin/env python3
"""Emulator runs for deliverable 10 (level 1, section 1: getting hurt, hearts, lives, the status screen).
Results: work/hu_<name>.pkl
  route      level1_route.json: the walk through the whole section (hurt twice, stunned once, leaves at the right)
  death      the route up to NES frame 2440 (one heart left), then into the cook: the last heart, the fall, the restart
  under      stands under the first flyer: stunned by what it drops, hurt by the flyer
  cook       walks into the first cook with a crate in the hands
  rnd1..3    random buttons from the start of the level
  rnd4..13   the route up to five places, then random buttons that stay about there (9..13 with B)
  rnd14..17  with a crate on the window sill / on the table in front of the first cook, then random buttons
  select*    the status screen (SELECT): standing, in the air, among enemies, SELECT held, SELECT while hurt
  over       three falls into the first pit: the last life
  gover      ... then GAME OVER and the continue screen: the arrow moved, CONTINUE, the level again
  gover_end  ... END: back to the title screen
  gover_last four times three falls: after the last credit there is no continue screen
  dl_hu_*    route, death, rnd1, rnd7, select, gover, gover_end with Dale
  hu_fx_*  sound only: the two sound effects alone (2nd square channel or noise only), asked for by hand
A run of more than 1200 frames is stored in parts (<name>, <name>_b, ...); every part also holds the frame counter
($2D) of all frames before it, so that sim_hurt.py can leave out the frames the NES left out.
usage: capture_hurt.py [job ...]      list: capture_hurt.py --events   (what happens in each run, nothing stored)"""
import json, os, pickle, random, sys, zlib
import multiprocessing as mp
import numpy as np
from emu import START, SELECT, A, B, UP, DOWN, LEFT, RIGHT
from capture_player import sched, DALE, ROUTE, route_until, PIT
from capture_enemies import SILL, TABLE
N, R, L, D, U = [], [RIGHT], [LEFT], [DOWN], [UP]

def rnd(seed, chunks, b=False):
    r = random.Random(seed); out = []
    for _ in range(chunks):
        k = []; x = r.random()
        if x < 0.55: k.append(RIGHT)
        elif x < 0.8: k.append(LEFT)
        if r.random() < 0.3: k.append(A)
        if r.random() < 0.12: k.append(DOWN)
        if b and r.random() < 0.1: k.append(UP)
        out.append((k, r.randint(1, 25)))
        if b and r.random() < 0.35: out.append((k + [B], 2))
    return out

def cut(runs, n):
    out = []; t = 0
    for k, c in runs:
        c = min(c, n - t)
        if c <= 0: break
        out.append((k, c)); t += c
    return out

RUNS = {}           # name: (first frame of the inputs, inputs)
RUNS['route'] = (1700, ROUTE)
_r = random.Random(1); _k = []; _d = []
for _t in range(80):
    if _t % 12 == 0: _k = [_r.choice([LEFT, RIGHT, RIGHT])] + ([A] if _r.random() < .3 else [])
    _d.append((list(_k), 1))
RUNS['death'] = (1700, route_until(2439) + _d + [(N, 300), (R, 60), ([RIGHT, A], 20), (N, 40)])
RUNS['under'] = (1390, SILL + [([RIGHT, A], 12), (R, 98), (N, 700)])
RUNS['cook'] = (1390, TABLE[:-1] + [(R, 120), (N, 200)])
def near(seed, chunks, b=False):
    """random buttons that stay about where they start"""
    r = random.Random(seed); out = []
    for _ in range(chunks):
        k = []; x = r.random()
        if x < 0.4: k.append(RIGHT)
        elif x < 0.8: k.append(LEFT)
        if r.random() < 0.15: k.append(A)
        if r.random() < 0.15: k.append(DOWN)
        if b and r.random() < 0.1: k.append(UP)
        out.append((k, r.randint(1, 20)))
        if b and r.random() < 0.35: out.append((k + [B], 2))
    return out
for s_ in (1, 2, 3): RUNS['rnd%d' % s_] = (1390, cut(rnd(100 + s_, 400, b=s_ > 2), 1800))
_base = [route_until(2150), route_until(2400), route_until(2690), route_until(2950), route_until(3250)]
for s_ in range(4, 14): RUNS['rnd%d' % s_] = (1700, _base[s_ % 5] + cut(near(s_, 300, b=s_ > 8), 1500))
for s_ in range(14, 18): RUNS['rnd%d' % s_] = (1390, (TABLE if s_ % 2 else SILL) + cut(near(s_, 300, b=True), 1200))
RUNS['select'] = (1390, [(R, 40), ([SELECT], 2), (N, 120), (R, 20), ([A], 5), ([SELECT], 2), (N, 60), (R, 30), ([RIGHT, A], 8), ([RIGHT, SELECT], 1), (R, 90),
                         ([SELECT], 1), (R, 60), ([SELECT], 40), (N, 30), ([SELECT], 30), (N, 60)])
RUNS['select2'] = (1390, SILL + [([RIGHT, A], 12), (R, 60), ([SELECT], 2), (N, 100), ([SELECT], 2), (R, 38), (N, 60), ([SELECT], 1), (N, 50), ([SELECT, A], 1), (N, 200),
                                 ([SELECT], 3), (N, 3), ([SELECT], 3), (N, 80), ([START], 2), (N, 50), ([START], 2), (N, 60)])
RUNS['over'] = (1700, (PIT[:10] + [(N, 200)]) * 2 + PIT[:10] + [(N, 500)])
# game over (the 3rd fall is at NES frame 2667; the continue screen takes buttons from 394 frames after it)
_over = (PIT[:10] + [(N, 200)]) * 2 + PIT[:10] + [(N, 360)]
RUNS['gover'] = (1700, _over + [([A], 1), (N, 19), (D, 2), (N, 20), (U, 2), (N, 20), (D, 1), (N, 3), (U, 1), (N, 20), ([A], 2), (N, 330), (R, 60), ([RIGHT, A], 20), (R, 40)])
RUNS['gover_end'] = (1700, _over + [(N, 20), (D, 2), (N, 30), ([A], 2), (N, 10), (U, 2), (N, 250)])
_cyc = _over + [(N, 70), ([A], 2), (N, 328)]
RUNS['gover_last'] = (1700, _cyc * 3 + (PIT[:10] + [(N, 200)]) * 2 + PIT[:10] + [(N, 520)])

def total(first, runs): return first + sum(n for k, n in runs)
PART = 1200
JOBS = []           # (file name, schedule, frames, first frame kept, sound mask, whole run's name)
def add(name, base=None, pre=''):
    first, runs = RUNS[name]; s = sched(first, runs, base)[0] if base else sched(first, runs)[0]; n = total(first, runs); f = 1380; i = 0
    while f < n:
        JOBS.append((pre + 'hu_' + name + ('' if i == 0 else '_' + 'bcdefg'[i - 1]), s, min(n, f + PART), f, 0)); f += PART; i += 1
for name in RUNS: add(name)
for name in ('route', 'death', 'rnd1', 'rnd7', 'select', 'gover', 'gover_end'): add(name, DALE, 'dl_')
SOUND = []
# single sound effects: the game's sound request ($F0) is written by hand while Chip stands at the start of the level
# (frame 1500, no enemy near), and only the 2nd square channel or only the noise channel is recorded
FX = [('hu_fx_hurt_sq2', 0x25, 0x1D), ('hu_fx_hurt_noi', 0x25, 0x17), ('hu_fx_stun_sq2', 0x26, 0x1D)]

def _fx(args):
    import ctypes
    name, v, mute = args
    os.environ['MESEN_MUTE'] = str(mute)
    from emu import Emu, WORK
    e = Emu(); sc = sched(1390, [(N, 320)])[0]; apu = []; cnt = []
    for i in range(1700):
        if i == 1500: ctypes.memmove(e.lib.retro_get_memory_data(2) + 0xF0, bytes([v]), 1)
        e.step(sc.get(i, [])); apu.append(e.apu_writes()); cnt.append(sum(len(a) for a in e.audio))
    pickle.dump(dict(apu=apu, aud=np.concatenate(e.audio)[:, 0], cnt=np.array(cnt), f0=0), open(os.path.join(WORK, name + '.pkl'), 'wb'), protocol=4)
    return name

def _run(args):
    name, sc, n, keep_from, mute = args
    if mute: os.environ['MESEN_MUTE'] = str(mute)
    from emu import Emu, WORK
    e = Emu(); fr = []; st = []; apu = []; cnt = []; fc = []
    for i in range(n):
        f = e.step(sc.get(i, [])); w = e.apu_writes(); cnt.append(sum(len(a) for a in e.audio)); r = e.ram(); fc.append(int(r[0x2D]))
        if i >= keep_from - 1:
            apu.append(w)
            if mute: continue
            p = e.ppu(); fr.append(zlib.compress(f.tobytes(), 1))
            st.append(dict(ram=r.copy(), oam=p['oam'].copy(), pal=p['pal'].copy(), mask=p['mask'], vram=p['vram'].copy() if i % 16 == 0 else None))
    d = dict(apu=apu, aud=np.concatenate(e.audio)[:, 0], cnt=np.array(cnt), f0=keep_from - 1, fc=fc)
    if not mute: d.update(zframes=fr, st=st)        # zframes: zlib, 240 x 256 x 3 bytes each
    pickle.dump(d, open(os.path.join(WORK, name + '.pkl'), 'wb'), protocol=4)
    return name

def events(name):
    from emu import Emu
    first, runs = RUNS[name]; sc = sched(first, runs)[0]; e = Emu(); out = []; prev = None
    for i in range(total(first, runs)):
        e.step(sc.get(i, [])); r = e.ram(); k = (int(r[0xB8]), int(r[0x3D4]), int(r[0xA7]))
        if prev and k != prev:
            if k[0] == 10 and prev[0] != 10: out.append('%d hurt%s' % (i, ' (carrying)' if r[0x2E4] & 0x40 else ''))
            if k[0] == 15 and prev[0] != 15: out.append('%d stunned%s' % (i, ' (carrying)' if r[0x2E4] & 0x40 else ''))
            if k[0] == 23 and prev[0] != 23: out.append('%d gone, lives %d' % (i, k[2]))
            if k[0] not in (1, 2, 3, 5, 8, 10, 15, 20, 23) and k[0] != prev[0]: out.append('%d state %d' % (i, k[0]))
        prev = k
    return name + ': ' + ', '.join(out)

if __name__ == '__main__':
    if '--events' in sys.argv:
        with mp.Pool(3, maxtasksperchild=1) as p:
            for t in p.imap(events, [a for a in sys.argv[1:] if a != '--events'] or list(RUNS)): print(t)
        sys.exit()
    only = sys.argv[1:] or None
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_run, [j for j in JOBS + SOUND if only is None or j[0] in only], chunksize=1)
        p.map(_fx, [j for j in FX if only is None or j[0] in only], chunksize=1)
    print('done')

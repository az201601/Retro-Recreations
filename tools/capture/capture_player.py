#!/usr/bin/env python3
"""Emulator runs for deliverable 6 (level 1, section 1: the player).  Results: work/pl_<name>.pkl  (about 1 minute, 2 GB)
  basic        from the level's first frame: buttons held during the fade-in, walk, both screen edges, duck, short and
               full jumps, standing still (blinking), jumps onto the first table
  pit          into the first pit, the restart of the section, then moving again
  rnd7a, rnd7b random buttons (LEFT / RIGHT / A / DOWN) from NES frame 1700, 1811 frames: reaches the last screen
  rnd0         random buttons, ends in a pit and restarts
  exit9, exit19, exit23   level1_route.json up to NES frame 3632 (the last screen), then random buttons: three ways out
  stale0..3    like pit, with buttons held on the one frame of the restart whose buttons the game keeps (NES frame 1948),
               or one frame earlier
  land_sq2     like basic, sound only, 2nd square channel only (for the landing sound)
  dl_*         the same runs with Dale chosen in the menu
No run presses B."""
import json, os, random, sys
from scenario import run_many
from emu import START, SELECT, A, DOWN, LEFT, RIGHT
SKIP = {1000: [START], 1100: [START], 1200: [START], 1300: [START]}
R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'level1_route.json')))

def sched(start, runs, base=SKIP):
    s = dict(base); f = start
    for keys, n in runs:
        for i in range(n):
            if keys: s[f] = list(keys)
            f += 1
    return s, f

def rnd(seed, chunks=150):
    r = random.Random(seed); out = []
    for _ in range(chunks):
        k = []; x = r.random()
        if x < 0.6: k.append(RIGHT)
        elif x < 0.8: k.append(LEFT)
        if r.random() < 0.4: k.append(A)
        if r.random() < 0.1: k.append(DOWN)
        out.append((k, r.randint(1, 25)))
    return out

BASIC = [([A], 26), ([], 14), ([RIGHT], 40), ([], 10), ([LEFT], 60), ([], 5), ([DOWN], 10), ([DOWN, RIGHT], 10), ([DOWN, LEFT], 10),
         ([], 6), ([A], 2), ([], 40), ([A], 60), ([], 150), ([RIGHT], 20), ([RIGHT, A], 25), ([RIGHT], 60), ([LEFT, A], 30),
         ([LEFT], 40), ([], 20), ([RIGHT, A], 3), ([RIGHT], 50), ([DOWN], 5), ([DOWN, A], 3), ([], 40)]
PIT = [([RIGHT, A], 20), ([RIGHT], 20)] * 5 + [([], 280), ([RIGHT], 30), ([A], 20), ([], 30)]
ROUTE = [(k, n) for k, n in R['inputs']]

def route_until(frame):
    out = []; f = R['start_frame']
    for k, n in ROUTE:
        n = min(n, frame + 1 - f)
        if n <= 0: break
        out.append((k, n)); f += n
    return out

JOBS = [('pl_basic', sched(1360, BASIC)[0], 2100, 1340),
        ('pl_pit', sched(1700, PIT)[0], 2260, 1700),
        ('pl_rnd7a', sched(1700, rnd(7))[0], 2620, 1700), ('pl_rnd7b', sched(1700, rnd(7))[0], 3520, 2600),
        ('pl_rnd0', sched(1700, rnd(0))[0], 2800, 1700)]
# the pad is not read while the section restarts; the game's single run before the fade-in uses what was held
# 21 frames after the restart flag (NES frame 1948 here)
for i, keys in enumerate(([LEFT, A], [RIGHT, A], [DOWN], [RIGHT])):
    JOBS.append(('pl_stale%d' % i, sched(1700, PIT[:10] + [([], 48 - i % 2), (keys, 1 + 30 * (i > 1)), ([RIGHT], 150)])[0], 2090, 1900))
for seed in (9, 19, 23):
    JOBS.append(('pl_exit%d' % seed, sched(1700, route_until(3632) + rnd(seed))[0], 3800, 3600))
# the same runs with Dale: SELECT moves the cursor to Dale in the character menu
DALE = {**SKIP, 1150: [SELECT]}
JOBS += [('dl_basic', sched(1360, BASIC, DALE)[0], 2100, 1340),
         ('dl_pit', sched(1700, PIT, DALE)[0], 2260, 1700),
         ('dl_rnd7a', sched(1700, rnd(7), DALE)[0], 2620, 1700), ('dl_rnd7b', sched(1700, rnd(7), DALE)[0], 3520, 2600),
         ('dl_rnd0', sched(1700, rnd(0), DALE)[0], 2800, 1700),
         ('dl_stale2', sched(1700, PIT[:10] + [([], 48), ([DOWN], 31), ([RIGHT], 150)], DALE)[0], 2090, 1900)]
for seed in (9, 19, 23):
    JOBS.append(('dl_exit%d' % seed, sched(1700, route_until(3632) + rnd(seed), DALE)[0], 3800, 3600))
SOUND = [('pl_land_sq2', sched(1360, BASIC)[0], 2100, 0x1D), ('dl_land_sq2', sched(1360, BASIC, DALE)[0], 2100, 0x1D)]

if __name__ == '__main__':
    import multiprocessing as mp
    from capture_level1 import _sound
    only = sys.argv[1:] or None
    run_many(JOBS, only=only)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_sound, [j for j in SOUND if only is None or j[0] in only], chunksize=1)
    print('done')

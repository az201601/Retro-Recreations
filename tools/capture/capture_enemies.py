#!/usr/bin/env python3
"""Emulator runs for deliverable 9 (level 1, section 1: enemies).  Results: work/en_<name>.pkl
  flyer     walks right with the first crate, jumps and throws it up into the first flyer
  flyer2    the run "carry" of capture_crates.py, then a crate thrown forwards into the first flyer
  hide      hides under the crate below the first flyer: it flies over, drops things, leaves the screen at the left;
            the first cook walks to and fro at the right
  cook      carries a crate along the floor to the first cook and hides under it: the cook throws a fork (it flies
            over the crate), walks on into the crate and is flung away
  cook2     the same way; the crate is thrown at the cook while it throws
  fork      ... thrown 9 frames later: it hits the fork
  pit       walks into the first pit with a crate while the first flyer is above: the crate flies up into it; the
            section starts again without enemies
  rnd1..6   random buttons from the starting points of flyer (1-3) and cook (4-6)
  dl_en_*   flyer and cook2 with Dale
  en_hide_sq2, en_cook_sq2, en_cook2_sq2, en_cook2_noi   sound only: the 2nd square channel alone, the noise
            channel alone (the flyer's buzz, the cook's throw, the hit)
usage: capture_enemies.py [job ...]"""
import random, sys
from scenario import run_many
from emu import A, B, UP, DOWN, LEFT, RIGHT
from capture_player import sched, DALE
from capture_crates import CARRY, FLOOR, RUNS as CR
N, R, L, D, U = [], [RIGHT], [LEFT], [DOWN], [UP]
SILL = CARRY + [(R, 60), ([RIGHT, A], 24), (R, 80)]                 # with the crate, right of the window sill
TABLE = FLOOR + [(R, 150), ([RIGHT, A], 24), (R, 103), ([RIGHT, A], 23), (R, 29), ([RIGHT, A], 23), (R, 12), (N, 1)]   # with the crate, on the table in front of the first cook
RUNS = {
    'flyer': SILL + [([RIGHT, A], 12), (R, 36), (N, 8), ([UP, B], 2), (N, 90)],
    'flyer2': CR['carry'][:len(CARRY) + 24] + [(N, 9), (R, 9), ([RIGHT, A], 12), (N, 26), ([RIGHT, B], 2), (N, 90)],
    'hide': SILL + [([RIGHT, A], 12), (R, 98), (D, 3), ([DOWN, A], 3), (D, 330)],
    'cook': TABLE[:-1] + [(D, 150)],
    'cook2': TABLE + [([RIGHT, B], 2), (N, 70)],
    'fork': TABLE + [(N, 9), ([RIGHT, B], 2), (N, 70)],
    'pit': FLOOR + [(R, 150), ([RIGHT, A], 24), (R, 164), (D, 330)],
}

def rnd(seed, chunks=40):
    r = random.Random(seed); out = []
    for _ in range(chunks):
        k = []; x = r.random()
        if x < 0.5: k.append(RIGHT)
        elif x < 0.7: k.append(LEFT)
        if r.random() < 0.3: k.append(A)
        if r.random() < 0.15: k.append(DOWN)
        if r.random() < 0.15: k.append(UP)
        out.append((k, r.randint(1, 20)))
        if r.random() < 0.3: out.append((k + [B], 2))
    return out
for s_ in (1, 2, 3): RUNS['rnd%d' % s_] = SILL + rnd(s_)
for s_ in (4, 5, 6): RUNS['rnd%d' % s_] = TABLE + rnd(s_)

def total(runs): return 1390 + sum(n for k, n in runs)
JOBS = []
for name, runs in RUNS.items():
    JOBS.append(('en_' + name, sched(1390, runs)[0], total(runs), 1380))
    if name in ('flyer', 'cook2'): JOBS.append(('dl_en_' + name, sched(1390, runs, DALE)[0], total(runs), 1380))
# sound only: 0x1D = 2nd square channel only, 0x17 = noise channel only (see mesen_libretro_debug.patch)
SOUND = [('en_%s_%s' % (n_, c_), sched(1390, RUNS[n_])[0], total(RUNS[n_]), m_) for n_, c_, m_ in (('hide', 'sq2', 0x1D), ('cook', 'sq2', 0x1D), ('cook2', 'sq2', 0x1D), ('cook2', 'noi', 0x17))]

if __name__ == '__main__':
    import multiprocessing as mp
    from capture_level1 import _sound
    only = sys.argv[1:] or None
    run_many(JOBS, only=only)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_sound, [j for j in SOUND if only is None or j[0] in only], chunksize=1)
    print('done')

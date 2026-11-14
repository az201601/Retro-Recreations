#!/usr/bin/env python3
"""Emulator runs for step 11 (level 1, section 2: the kitchen).  Results: work/kt_<name>.pkl
  route0..3   level1_route.json, then level1_route2.json: the kitchen played from the end of section 1 to its exit
              and into the third section
  the RUNS    the route up to some frame, then other buttons: the exit reached in other ways, random buttons in the
              shaft, the top edge, the status screen, held buttons at the section change, a fall, lost lives up to
              GAME OVER and CONTINUE; three with Dale (dl_*).  Stored in parts of 1200 frames.
  CHECKS      what sim_kitchen.py compares: (name, recordings, buttons, first NES frame, start mode, last frame)
usage: capture_kitchen.py [job ...]     (everything: ~3 min)"""
import json, os, sys
from scenario import run_many
from capture_level1 import ROUTE
R2 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'level1_route2.json')))
ROUTE2 = dict(ROUTE); f = R2['start_frame']
for keys, n in R2['inputs']:
    for i in range(n): ROUTE2[f] = keys; f += 1
ROUTE2_END = f
CUTS = [3690, 4450, 5210, 5970, 6760]
JOBS = [('kt_route%d' % i, ROUTE2, CUTS[i + 1], CUTS[i]) for i in range(4)]
ROUTE_FILES = ['kt_route%d' % i for i in range(4)]
from emu import START, SELECT, A, B, UP, DOWN, LEFT, RIGHT
N = []; L = [LEFT]; R = [RIGHT]

def after(frame, runs, base=ROUTE2):
    """the route up to `frame` (not included), then the runs; returns (schedule, number of frames)"""
    sc = {f_: k for f_, k in base.items() if f_ < frame}; f_ = frame
    for keys, n in runs:
        for i in range(n): sc[f_] = keys; f_ += 1
    return sc, f_

def again(sc, at, n):
    """the kitchen has started again and the player can move on frame `at`: the route's first n frames once more
    (the mice do the same every time, so the route works again)"""
    for f_ in range(3732, 3732 + n): sc[at + 1 + f_ - 3732] = ROUTE2.get(f_, [])
    return sc

def rnd(seed, n=22):
    import random
    random.seed(seed); runs = []
    for i in range(n):
        k = random.choice([[LEFT], [RIGHT], [LEFT, A], [RIGHT, A], [A], [], [DOWN], [RIGHT, A], [LEFT, A]]); runs.append((k, random.randint(3, 28)))
    return runs

# further runs: name -> (schedule, frames, first frame kept).  All follow the route up to some frame.
RUNS = {}
RUNS['exit2'] = after(6560, [(R, 16), (N, 3), ([DOWN], 20), (R, 80)]) + (6550,)                    # walks into the exit
RUNS['exit3'] = after(6560, [(R, 27), ([RIGHT, A], 20), (R, 40), (L, 60)]) + (6550,)               # jumps over it, comes back
for s_ in (1, 2, 4, 6, 8): RUNS['shaft%d' % s_] = after(5300, rnd(s_) + [(N, 20)]) + (5290,)       # the shaft, random buttons
RUNS['top'] = after(5800, [([A], 30), (N, 30), ([RIGHT, A], 30), (N, 20), ([LEFT, A], 40), (N, 30)]) + (5790,)      # jumps out of the top of the picture
RUNS['select'] = after(5300, [(N, 5), ([SELECT], 2), (N, 60), ([SELECT], 2), (N, 40), ([LEFT, A], 20), (N, 30), ([SELECT], 2), (N, 30), ([SELECT], 2), (N, 40)]) + (5290,)
RUNS['hold'] = after(3690, [([RIGHT, A], 80), (N, 40)]) + (3680,)                                   # buttons held while the kitchen appears
RUNS['hold2'] = after(3690, [(N, 41), ([A], 3), (N, 40)]) + (3680,)
_sc, _n = after(5300, [(L, 70)]); again(_sc, 5447, 400)                                             # falls out of the shaft; the kitchen starts again
RUNS['fall'] = (_sc, 5447 + 402, 5290)
_sc, _n = after(5300, [(L, 70)]); again(_sc, 5447, 1569)                                            # ... three times: GAME OVER, CONTINUE: the dining room
for f_ in range(7016, 7086): _sc[f_] = L
again(_sc, 7163, 1569)
for f_ in range(8732, 8802): _sc[f_] = L
_sc[9272] = [A]; _sc[9273] = [A]
RUNS['over'] = (_sc, 9520, 7000)
ROUTE2D = {**ROUTE2, 1150: [SELECT]}                                                                 # the same with Dale
RUNS['dl_enter'] = after(3690, [(N, 42), (R, 60), ([RIGHT, A], 20), (N, 30)], ROUTE2D) + (3680,)
RUNS['dl_shaft2'] = after(5300, rnd(2) + [(N, 20)], ROUTE2D) + (5290,)
RUNS['dl_exit2'] = after(6560, [(R, 16), (N, 3), ([DOWN], 20), (R, 80)], ROUTE2D) + (6550,)
PART = 1200
JOBS2 = []
for name_, (sc_, n_, k_) in RUNS.items():
    f_ = k_; i_ = 0
    while f_ < n_:
        JOBS2.append(('kt_' + name_ + ('' if i_ == 0 else '_' + 'bcdefg'[i_ - 1]), sc_, min(n_, f_ + PART), f_, 0)); f_ += PART; i_ += 1
def files(name): return [j[0] for j in JOBS2 if j[0] == 'kt_' + name or j[0][:-2] == 'kt_' + name]

# what sim_kitchen.py compares: (name, recordings, schedule, first NES frame, how the port starts, last frame or None)
CHECKS = [('kt_enter', ROUTE_FILES, ROUTE2, 3695, 'dining', 3800),
          ('kt_route', ROUTE_FILES, ROUTE2, 3723, 'start', None),
          ('kt_hold', files('hold'), RUNS['hold'][0], 3695, 'dining', None),
          ('kt_hold2', files('hold2'), RUNS['hold2'][0], 3695, 'dining', None),
          ('kt_fall', files('fall'), RUNS['fall'][0], 5292, 'middle', None),
          ('kt_over', files('over'), RUNS['over'][0], 7002, 'middle', None)]
# (the others start in the middle of the kitchen: the port takes the place of the player and the camera from the NES)
for name_ in RUNS:
    if name_ == 'dl_enter': CHECKS.append(('kt_dl_enter', files(name_), RUNS[name_][0], 3695, 'dining', None))
    elif name_ not in ('hold', 'hold2', 'fall', 'over'): CHECKS.append(('kt_' + name_, files(name_), RUNS[name_][0], RUNS[name_][2] + 2, 'middle', None))

if __name__ == '__main__':
    import multiprocessing as mp
    from capture_hurt import _run
    only = sys.argv[1:] or None
    run_many(JOBS, only=only)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_run, [j for j in JOBS2 if only is None or j[0] in only], chunksize=1)
    print('done')

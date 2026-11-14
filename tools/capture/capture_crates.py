#!/usr/bin/env python3
"""Emulator runs for deliverable 8 (level 1, section 1: crates and bonus boxes).  Results: work/cr_<name>.pkl
  carry     picks up the first crate on the window sill, walks, jumps and ducks with it, throws it in every direction,
            picks up the next crates (also one of a stack of two) and throws them standing, ducking and in the air
  power, power2   throws while walking, after 30 frames or more of walking without a stop (the crate flies in a
            zig-zag) and after less
  floor     carries a crate down to the floor, throws it there; walks into bonus boxes
  boxes     no crate: falls off the bench through two bonus boxes, jumps into the next two
  pitcarry, pitquiet   falls into the first pit with a crate; the section starts again (all crates and boxes are back)
  rnd1..7   random buttons (LEFT / RIGHT / A / B / UP / DOWN): 1-3 after picking up the first crate, 4-5 after carrying
            it down to the floor, 6-7 from the bench without a crate
  eyes      hides under the first crate for 4 seconds, turning left and right
  snd_*     short runs for the order of the sounds: a bonus box collected just before / after / during a landing,
            a throw, a pick-up
  dl_cr_*   the same runs with Dale
  cr_power_sq2, cr_boxes_sq2, cr_power_noi   power and boxes again, sound only: the 2nd square channel alone, the
            noise channel alone (for the four new sounds)
usage: capture_crates.py [job ...]"""
import random, sys
from scenario import run_many
from emu import A, B, UP, DOWN, LEFT, RIGHT
from capture_player import sched, SKIP, DALE
N, R, L, D, U = [], [RIGHT], [LEFT], [DOWN], [UP]
CARRY = [(R, 20), ([RIGHT, A], 30), (N, 10), ([A], 30), (N, 30), ([A, RIGHT], 26), (N, 12), (R, 30), (N, 3), (R, 3), ([RIGHT, B], 4), (N, 30)]
BENCH = [(R, 20), ([RIGHT, A], 30), (R, 64)]
RUNS = {
    'carry': CARRY + [(N, 10), (L, 14), (R, 10), ([A], 20), (N, 25), (D, 30), (N, 8), (D, 14), ([DOWN, LEFT], 4), (D, 4), (N, 4), ([B], 2), (N, 40),
                      (R, 6), ([RIGHT, A], 24), (R, 6), (N, 10), (L, 14), ([LEFT, B], 2), (N, 10), ([UP, B], 2), (N, 50), (R, 52),
                      ([RIGHT, B], 2), (N, 10), (D, 6), ([DOWN, B], 2), (D, 10), (N, 30), ([RIGHT, B], 2), (N, 10), ([A], 12), ([A, B], 2), (N, 60),
                      (R, 60), (L, 20), ([LEFT, A], 30), (N, 30)],
    'power': CARRY + [(L, 14), (R, 18), ([RIGHT, B], 2), (N, 70), (R, 14), ([RIGHT, B], 2), (N, 4), (L, 14), (R, 14), ([RIGHT, B], 2), (N, 60),
                      (R, 60), ([RIGHT, B], 2), (N, 4), (L, 20), (R, 5), (L, 10), ([LEFT, B], 2), (N, 60),
                      (R, 40), ([RIGHT, B], 2), (N, 4), (L, 16), (R, 16), ([UP, RIGHT, B], 2), (N, 50)],
    'power2': CARRY + [(L, 14), (R, 15), ([RIGHT, B], 2), (N, 70), (R, 14), ([RIGHT, B], 2), (N, 4), (L, 14), (R, 16), ([RIGHT, B], 2), (N, 60),
                       (R, 60), ([RIGHT, B], 2), (N, 4), (L, 16), (R, 16), ([UP, B], 2), (N, 60),
                       (R, 40), ([RIGHT, B], 2), (N, 4), (L, 31), ([LEFT, A], 6), ([LEFT, B], 2), (N, 50)],
    'floor': CARRY + [(L, 70), (N, 10), (L, 40), (N, 10), ([B], 2), (N, 60), (R, 40), ([RIGHT, A], 30), (R, 90), (N, 20), (L, 30),
                      ([LEFT, A], 30), (L, 40), (R, 30), ([RIGHT, B], 3), (R, 60), ([B], 2), (N, 60)],
    'boxes': BENCH + [(R, 74), (N, 12), (L, 8), (N, 8), (R, 9), (N, 8), (R, 20), ([RIGHT, A], 30), (R, 6), (N, 20), (L, 10), ([A], 30),
                      (N, 20), (R, 16), ([A], 30), (N, 20), ([RIGHT, A], 30), (N, 30), ([LEFT, A], 30), (N, 40)],
}

def rnd(seed, chunks=70):
    r = random.Random(seed); out = []
    for _ in range(chunks):
        k = []; x = r.random()
        if x < 0.4: k.append(RIGHT)
        elif x < 0.8: k.append(LEFT)
        if r.random() < 0.2: k.append(A)
        if r.random() < 0.1: k.append(DOWN)
        if r.random() < 0.1: k.append(UP)
        out.append((k, r.randint(1, 30)))
        if r.random() < 0.5: out.append((k + [B], 2))
    return out
FLOOR = CARRY + [(L, 70), (N, 10), (L, 40), (N, 10)]
RUNS['pitcarry'] = FLOOR + [([RIGHT, A], 20), (R, 20)] * 4 + [(N, 270), (R, 60), ([RIGHT, A], 30), (N, 20)]
# hiding under the crate for a long time: the eyes appear, turn with LEFT / RIGHT, blink; throwing from under the crate
RUNS['eyes'] = CARRY + [(D, 40), ([DOWN, LEFT], 3), (D, 30), ([DOWN, RIGHT], 3), (D, 180), (N, 12), (D, 20), ([DOWN, B], 2), (D, 30), (N, 20)]
# the same pit after a wait: the repeating sound of the level, which hides the throw sound in pitcarry, is over by then
RUNS['pitquiet'] = FLOOR + [([RIGHT, A], 20), (R, 20)] * 3 + [(N, 458), (R, 25), (N, 150)]
for s_ in (1, 2, 3): RUNS['rnd%d' % s_] = CARRY + rnd(s_)
for s_ in (4, 5): RUNS['rnd%d' % s_] = FLOOR + rnd(s_)
for s_ in (6, 7): RUNS['rnd%d' % s_] = BENCH + rnd(s_)

# which sound wins on the shared channel: a bonus box next to a landing, a throw, a pick-up
PRE = CARRY[:-2]                                                    # in front of the first crate (it has a bonus inside)
BOX = PRE + [([RIGHT, B], 1), (N, 30), ([B], 2), (N, 100)]          # a 1-frame tap leaves the bonus box where the crate was
RUNS['snd_land'] = PRE + [([RIGHT, B], 4), (N, 8), ([A], 2), (N, 70)]               # landing during the bonus sound
RUNS['snd_land2'] = PRE + [([RIGHT, B], 4), (N, 36), ([A], 2), (N, 70)]             # ... in its last, silent frames
RUNS['snd_throw'] = PRE + [([RIGHT, B], 4), (N, 6), ([B], 2), (N, 60)]              # throw during the bonus sound
RUNS['snd_throw2'] = PRE + [([RIGHT, B], 1), (N, 30), ([B], 2), (N, 14), (R, 4), (N, 70)]   # bonus during the throw sound
RUNS['snd_pick'] = BOX + [(R, 7), ([RIGHT, B], 3), (N, 70)]                         # pick-up during the bonus sound
RUNS['snd_far'] = CARRY + [(L, 14), (R, 18), ([RIGHT, B], 2), (N, 5), ([A], 2), (N, 90)]         # landing during the far-throw sound
for k_ in (10, 11, 13): RUNS['snd_after%d' % k_] = BOX + [([A], 2), (N, k_ - 2), (R, 3), (N, 70)]      # bonus 1, 2, 4 frames after a landing
for k_ in (2, 4, 6): RUNS['snd_air%d' % k_] = BOX + [(L, k_), (N, 20), ([RIGHT, A], 2), (R, 12), (N, 70)]   # bonus in the air, landing 7, 5, 3 frames later

def total(runs): return 1390 + sum(n for k, n in runs)
JOBS = []
for name, runs in RUNS.items():
    JOBS.append(('cr_' + name, sched(1390, runs)[0], total(runs), 1380))
    if name in ('carry', 'power', 'boxes', 'rnd1', 'pitcarry', 'rnd4'): JOBS.append(('dl_cr_' + name, sched(1390, runs, DALE)[0], total(runs), 1380))
# sound only: 0x1D = 2nd square channel only, 0x17 = noise channel only (see mesen_libretro_debug.patch)
SOUND = [('cr_power_sq2', sched(1390, RUNS['power'])[0], total(RUNS['power']), 0x1D), ('cr_boxes_sq2', sched(1390, RUNS['boxes'])[0], total(RUNS['boxes']), 0x1D),
         ('cr_power_noi', sched(1390, RUNS['power'])[0], total(RUNS['power']), 0x17)]

if __name__ == '__main__':
    import multiprocessing as mp
    from capture_level1 import _sound
    only = sys.argv[1:] or None
    run_many(JOBS, only=only)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_sound, [j for j in SOUND if only is None or j[0] in only], chunksize=1)
    print('done')

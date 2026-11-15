#!/usr/bin/env python3
"""Emulator runs for step 13 (level 1, section 2: the mice of the kitchen).  Results: work/mi_<name>.pkl (+ _b, _c ...)
Every run is kept from frame 3680 (the end of the dining room) on, so that the port can be started at the
kitchen's entry and has to bring every mouse to the same place by itself.
  the step 11 runs again (exit2, exit3, top, select, shaft1-5, fall, dl_*), this time from frame 3680
  hurt      the first mouse (the one hiding under a crate) runs into the player: the last heart, the kitchen starts again; then the
            same with 3 hearts
  stun      a crate thrown at the back of the mouse with the spoon; it lies there, wakes up and walks on
  swat      a crate thrown at its front: it bats the crate back
  carry*    the stunned mouse picked up, carried, thrown (ahead, with UP held, in a jump)
  kill      the stunned mouse hit by a second crate
  thit, thit2   the carried mouse thrown at another mouse
  clong     carried for longer than the 600 frames it would lie
  cdie, churt   the last heart lost / hurt with the mouse on the head
  CHECKS3   what sim_mice.py compares: (name, recordings, buttons, first NES frame, start mode, last frame)
usage: capture_mice.py [job ...]"""
import os, sys
import capture_kitchen as CK
from capture_kitchen import after, ROUTE2, ROUTE2D, N, L, R
from emu import START, SELECT, A, B, UP, DOWN, LEFT, RIGHT
LA = [LEFT, A]; RA = [RIGHT, A]; RB = [RIGHT, B]; LB = [LEFT, B]; BB = [B]
RUNS = {}
for name_ in ('exit2', 'exit3', 'top', 'select', 'fall', 'dl_shaft2', 'dl_exit2') + tuple('shaft%d' % i for i in range(1, 6)):
    if name_ in CK.RUNS: RUNS[name_] = (CK.RUNS[name_][0], CK.RUNS[name_][1])
# a crate from the stack beside the second pot, carried over the pot and down to the floor in front of the mouse
PRE = [(L, 28), (N, 25), (R, 6), (RB, 2), (RA, 14), (R, 30), (N, 2), (R, 6), (N, 30)]          # 4072 .. 4214
STUN = PRE + [(N, 20), (BB, 2), (N, 45)]                                                        # .. 4281
CRATE2 = [(LA, 16), (L, 70), (N, 10), (R, 12), (RB, 2), (RA, 14), (R, 30), (N, 2), (R, 6), (N, 30)]
HURT = [(R, 60), (RA, 16), (R, 20), (N, 160)]
RUNS['hurt'] = after(3760, HURT + [(N, 120)] + HURT + [(L, 40), (N, 200), (R, 50), (N, 300)])
RUNS['stun'] = after(4072, STUN + [(N, 760)])
RUNS['swat'] = after(4072, PRE + [(N, 2), (BB, 2), (N, 300)])
RUNS['carry'] = after(4072, STUN + [(R, 50), (RB, 2), (R, 10), (N, 30), (L, 20), (LA, 12), (L, 20), (BB, 2), (N, 120)])
RUNS['carry2'] = after(4072, STUN + [(R, 50), (RB, 2), (N, 20), ([UP, B], 2), (N, 100), (R, 30), (N, 60)])
RUNS['carry3'] = after(4072, STUN + [(R, 50), (RB, 2), (N, 10), (RA, 10), (RB, 2), (R, 40), (N, 100)])
RUNS['carry4'] = after(4072, STUN + [(R, 50), (RB, 2), (N, 10), ([DOWN], 40), (N, 10), ([DOWN], 20), ([DOWN, B], 2), (N, 100)])
RUNS['kill'] = after(4072, STUN + CRATE2 + [(BB, 2), (N, 160)])
RUNS['wake'] = after(4072, STUN + [(R, 40), (N, 660), (L, 30), (N, 100)])
# the stunned mouse picked up and carried over the two crates to the floor beyond them
CARRY = STUN + [(R, 48), (RB, 2), (R, 8), (RA, 22), (R, 50)]                                    # .. 4411
UP2 = [(R, 146), ([A], 24)]                                                                     # up to the shelf below the next mouse with a spoon
RUNS['thit'] = after(4072, CARRY + [(RB, 2), (N, 80)])                                          # thrown at the mouse under the crate
RUNS['thit2'] = after(4072, CARRY + UP2 + [(N, 14), (BB, 2), (N, 100)])                         # thrown at a mouse with a spoon
RUNS['clong'] = after(4072, STUN + [(R, 48), (RB, 2), (N, 560), (L, 30), (N, 60), (LB, 2), (N, 60)])    # carried for longer than it would lie
RUNS['cdie'] = after(4072, CARRY + UP2 + [(N, 26), ([A], 24), (N, 250)])                        # the last heart lost with the mouse on the head
# with 3 hearts (the kitchen has started again; the mice do the same every time): hurt with the mouse on the head
_sc, _n = after(3760, HURT + [(N, 400)]); CK.again(_sc, 4021, 340)
_f = 4362
for _k, _c in CARRY + [(R, 14), (RA, 24), (N, 120), (BB, 2), (N, 60)]:
    for _i in range(_c): _sc[_f] = _k; _f += 1
RUNS['churt'] = ({f_: k_ for f_, k_ in _sc.items() if f_ < _f}, _f)
PART = 1200; KEEP = 3680
JOBS = []
for name_, (sc_, n_) in RUNS.items():
    f_ = KEEP; i_ = 0
    while f_ < n_:
        JOBS.append(('mi_' + name_ + ('' if i_ == 0 else '_' + 'bcdefg'[i_ - 1]), sc_, min(n_, f_ + PART), f_, 0)); f_ += PART; i_ += 1
def files(name): return [j[0] for j in JOBS if j[0] == 'mi_' + name or j[0][:-2] == 'mi_' + name]
# the mice's sounds alone, asked for by a write to $F0 (like the sounds of step 10): 2nd square channel only / noise only
FX = [('mi_fx_stun_sq2', 0x2E, 0x1D), ('mi_fx_swat_sq2', 0x5E, 0x1D), ('mi_fx_wake_sq2', 0x60, 0x1D), ('mi_fx_wake_noi', 0x60, 0x17), ('mi_fx_swat_noi', 0x5E, 0x17), ('mi_fx_stun_noi', 0x2E, 0x17)]
CHECKS3 = [('mi_' + name_, files(name_), RUNS[name_][0], 3695, 'dining', None) for name_ in RUNS]

if __name__ == '__main__':
    import multiprocessing as mp
    from capture_hurt import _run, _fx
    only = sys.argv[1:] or None
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_run, [j for j in JOBS if only is None or j[0] in only or j[0][:-2] in only], chunksize=1)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_fx, [j for j in FX if only is None or j[0] in only], chunksize=1)
    print('done')

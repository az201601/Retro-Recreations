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
  thit3     thrown at the face of a mouse with a spoon
  tv1-tv4   thrown at the limits of its reach up and down
  far, far2 a crate of a far throw at the mouse with the spoon
  acorn3    the acorn taken with 3 hearts (memory written)
  lives10, lives11  the star taken with 9 and with 10 lives (memory written)
  cleft     a crate thrown to the left at a stunned mouse
  mtop      a jump onto the stunned mouse; walking off it; pushing it to the left
  mtop2     a jump that comes down beside it
  push2     pushed left until the player is at the left edge of the picture
  mwake     crouching and jumping on it, and standing on it when it gets up
  cwall     a crate thrown through a solid block
  push      a stunned mouse pushed against a wall
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
# thrown at a mouse with a spoon that looks at it, from 60 pixels away: the spoon does not answer
RUNS['thit3'] = after(4072, CARRY + UP2 + [(N, 14), (L, 25), (N, 40), (RB, 2), (N, 80)])
# how far above / below the thrown mouse still meets another: thrown in a jump, 1 pixel inside and 1 outside each limit
_C2 = STUN + [(R, 48), (RB, 2), (R, 8), (RA, 22), (R, 44)]
RUNS['tv1'] = after(4072, _C2 + [([A], 7), (N, 9), (BB, 2), (N, 70)])                 # 15 above the mouse under the crate: met
RUNS['tv2'] = after(4072, _C2 + [([A], 4), (N, 2), (BB, 2), (N, 70)])                 # 16 above: not met
RUNS['tv3'] = after(4072, CARRY + [(R, 146), ([A], 10), (N, 4), (BB, 2), (N, 70)])    # 24 below the mouse with the spoon: met
RUNS['tv4'] = after(4072, CARRY + [(R, 146), ([A], 9), (N, 1), (BB, 2), (N, 70)])     # 25 below: not met
# a crate of a far throw at the mouse with the spoon: a crate from the high shelf, down to the mouse's shelf, a run-up
_FAR = [(R, 8), (RA, 20), (R, 36), ([A], 20), (N, 22), (R, 11), (RB, 2), (N, 2), (RA, 9), (R, 8), (N, 12), (R, 6), (N, 30)]
RUNS['far'] = after(4291, _FAR + [(R, 32), (RB, 2), (N, 90)])                         # the spoon swings in time: the crate is not turned
RUNS['far2'] = after(4291, _FAR + [(R, 44), (RB, 2), (N, 90)])                        # too late for the swing
# a second crate thrown to the left at the stunned mouse (from the right, off the step behind it): flung to the left
RUNS['cleft'] = after(4072, STUN + [(L, 36), (LB, 2), (R, 50), (RA, 20), (R, 40), (N, 16), (L, 20), (N, 8), (LB, 2), (N, 60)])
# jumping at the stunned mouse from the side and from above
RUNS['mtop'] = after(4072, STUN + [(R, 2), (RA, 20), (R, 60), (N, 20), (L, 30), (N, 10)])
RUNS['mtop2'] = after(4072, STUN + [(RA, 20), (R, 40), (N, 20)])
# onto the mouse, off it on the far side, and pushed left until the player is at the left edge of the picture
RUNS['push2'] = after(4072, STUN + [(R, 2), (RA, 20), (R, 60), (N, 10), (L, 200), (N, 10), (R, 4), (L, 20), (N, 10)])
# on the mouse: crouching, a jump straight up, and waiting there until it gets up
RUNS['mwake'] = after(4072, STUN + [(R, 2), (RA, 20), (R, 20), (N, 10), ([DOWN], 20), (N, 10), ([A], 3), (N, 700)])
# a crate thrown along the ground through a solid block: over the stunned mouse, the left one of the two crates
# beyond it picked up, and thrown from under it at the right one
RUNS['cwall'] = after(4072, STUN + [(R, 2), (RA, 20), (R, 60), (N, 6), (RB, 2), (N, 4), ([DOWN], 14), ([DOWN, RIGHT, B], 2), (N, 60)])
# the stunned mouse pushed along until it stands at a wall
RUNS['push'] = after(4072, STUN + [(R, 110), (N, 10), (L, 6), (R, 20), (N, 10)])
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
# recordings with memory written (name, buttons, frames, first frame kept, {frame: [(address, value)]}):
#   acorn3   the run cr_e2 of step 12 (it finds the acorn) with 3 hearts from the dining room's exit on: the acorn gives nothing
#   lives10  the star run of step 12 (the player is put on the star's shelf) with 9 lives: 10
#   lives11  ... with 10 lives: still 10
_E2 = CK.RUNS['cr_e2']
POKED = [('mi_acorn3', _E2[0], 4880, KEEP, {3690: [(0x3D4, 3), (0xA9, 3)]}), ('mi_acorn3_b', _E2[0], _E2[1], 4880, {3690: [(0x3D4, 3), (0xA9, 3)]}),
         ('mi_lives10', CK.STAR[0], CK.STAR[1], CK.STAR[2], {**CK.STAR[3], 6540: [(0xA7, 9)]}),
         ('mi_lives11', CK.STAR[0], CK.STAR[1], CK.STAR[2], {**CK.STAR[3], 6540: [(0xA7, 10)]})]
CHECKS3 += [('mi_acorn3', ['mi_acorn3', 'mi_acorn3_b'], _E2[0], 3695, 'dining', None),
            ('mi_lives10', ['mi_lives10'], CK.STAR[0], 6606, 'middle', None), ('mi_lives11', ['mi_lives11'], CK.STAR[0], 6606, 'middle', None)]

def _poked(args):
    import ctypes, pickle, zlib
    import numpy as np
    from emu import Emu, WORK
    name, sc, n, keep_from, pokes = args
    e = Emu(); fr = []; st = []; apu = []; cnt = []; fc = []
    for i in range(n):
        for a, v in pokes.get(i, []): ctypes.memmove(e.lib.retro_get_memory_data(2) + a, bytes([v]), 1)
        f = e.step(sc.get(i, [])); w = e.apu_writes(); cnt.append(sum(len(a) for a in e.audio)); r = e.ram(); fc.append(int(r[0x2D]))
        if i >= keep_from - 1:
            p = e.ppu(); apu.append(w); fr.append(zlib.compress(f.tobytes(), 1))
            st.append(dict(ram=r.copy(), oam=p['oam'].copy(), pal=p['pal'].copy(), mask=p['mask'], vram=p['vram'].copy() if i % 16 == 0 else None))
    pickle.dump(dict(apu=apu, aud=np.concatenate(e.audio)[:, 0], cnt=np.array(cnt), f0=keep_from - 1, fc=fc, zframes=fr, st=st), open(os.path.join(WORK, name + '.pkl'), 'wb'), protocol=4)
    return name

if __name__ == '__main__':
    import multiprocessing as mp
    from capture_hurt import _run, _fx
    only = sys.argv[1:] or None
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_run, [j for j in JOBS if only is None or j[0] in only or j[0][:-2] in only], chunksize=1)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_poked, [j for j in POKED if only is None or j[0] in only or j[0][:-2] in only], chunksize=1)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_fx, [j for j in FX if only is None or j[0] in only], chunksize=1)
    print('done')

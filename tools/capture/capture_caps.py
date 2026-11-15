#!/usr/bin/env python3
"""Emulator runs for step 14 (level 1, section 2: the bottle caps of the kitchen).  Results: work/cp_<name>.pkl (+ _b, _c ...)
Every run is the kitchen route of step 11 up to frame 6300 (Chip stands on the shelf to the left of the first bottle)
and is kept from frame 3680 (the end of the dining room) on, like the runs of step 13.
  pop       onto the first cap, two small jumps on it: it flies off with Chip, who stands still and drops off it
  quick     the same with the jumps pressed on the very frame after each landing
  ride      Chip walks along with the flying cap; when it comes down he drops off and lands on it again and again,
            and at the bottom the mouse with the spoon takes his last heart
  ride16    the same with fewer steps: he gets down hurt once
  half      one landing, back to the shelf, down on the cap again (the second landing), one jump (the third)
  star      the way the level means it: cap, cap, cap, the shelf with the star (an extra life)
  side      a jump from the first cap that comes down against the side of the second
  reland    off the second cap in its flight, landing on it twice more on the way down
  under     Chip on the floor where the second cap comes down: it lifts him as it falls through him
  again     the first cap sent off, the last heart lost to the mouse below: the kitchen starts again, the route
            once more, and the cap is back
  bump, bump96, bump95 (memory written)   a jump under the first cap, Chip's height written on one frame so that he
            rises into the cap: 20 and 0 pixels below its line (his head is stopped), 1 above (he is put on it)
  crate, crate_ride, crate_stand, crate_up, crate_down   with a crate from the ledge: thrown from the flying cap
            (standing, walking along), from the cap on its bottle (ahead, upwards, crouching)
  fsider, fsidel (memory written)   walking into the side of the flying cap
  edgel15 .. edger15 (memory written)   the fall onto the first cap with Chip's place written: how far to the side
            he still lands on it
  cp_fx_*   the cap's sound alone (written to $F0 by hand, like the sounds of step 10), one channel at a time
  CHECKS4   what sim_caps.py compares: (name, recordings, buttons, first NES frame, start mode, last frame)
usage: capture_caps.py [job ...]"""
import os, sys
import capture_kitchen as CK
import capture_mice as CM
from capture_kitchen import after, ROUTE2, N, L, R
from emu import A, B, UP, DOWN, LEFT, RIGHT
LA = [LEFT, A]; RA = [RIGHT, A]; AA = [A]
ON = [(R, 8), (RA, 12), (R, 23)]                                       # 6300 .. 6342: off the shelf onto the first cap
POP = ON + [(AA, 2), (N, 14), (AA, 2), (N, 12)]                         # .. 6372: the third landing was on 6369; the cap is in the air
def walk(n): return [(R, 1), (N, 1)] * n                               # a pixel a frame, like the cap
PEAK1 = POP + walk(9)                                                  # .. 6390: the cap is at its highest
POP2 = PEAK1 + [(RA, 20), (R, 28), (N, 5), (AA, 2), (N, 14), (AA, 2), (N, 9)]      # .. 6470: the second cap sent off
PEAK2 = POP2 + [(R, 15), (N, 1)] + walk(3)
POP3 = PEAK2 + [(RA, 20), (R, 27), (N, 5), (AA, 2), (N, 14), (AA, 2), (N, 9)]
PEAK3 = POP3 + [(R, 14), (N, 1)] + walk(3)
RUNS = {}
RUNS['pop'] = after(6300, ON + [(N, 12), (AA, 2), (N, 26), (AA, 2), (N, 140)])
RUNS['quick'] = after(6300, [(R, 8), (RA, 12), (R, 22), (AA, 2), (N, 9), (AA, 2), (N, 139)])
RUNS['ride'] = after(6300, ON + [(N, 12), (AA, 2), (N, 26), (AA, 2), (N, 10)] + walk(30) + [(N, 60)])
RUNS['ride16'] = after(6300, ON + [(N, 12), (AA, 2), (N, 26), (AA, 2), (N, 10)] + walk(16) + [(N, 120)])
RUNS['half'] = after(6300, ON + [(N, 10), (LA, 22), (L, 70), (N, 10)] + ON + [(N, 20), (AA, 2), (N, 150)])
RUNS['star'] = after(6300, PEAK3 + [(RA, 22), (R, 51), (N, 100)])
RUNS['side'] = after(6300, PEAK1 + [(RA, 16), (R, 50), (N, 30)])
RUNS['reland'] = after(6300, POP2 + [(R, 29), (N, 110)])
RUNS['under'] = after(6300, POP2 + [(R, 41), (N, 110)])
# the last heart lost with the first cap gone; Chip can move again on frame 6561: the route once more, the cap again
_sc, _n = after(6300, ON + [(N, 12), (AA, 2), (N, 26), (AA, 2), (N, 10), (R, 26), (N, 140)]); CK.again(_sc, 6560, 6300 - 3732)
_f = 6561 + 6300 - 3732
for _k, _c in ON + [(N, 12), (AA, 2), (N, 26), (AA, 2), (N, 150)]:
    for _i in range(_c): _sc[_f] = _k; _f += 1
RUNS['again'] = (_sc, _f)
# with a crate: Chip takes the crate next to him on the ledge first (11 frames), then the same way onto the cap
PICK = [(L, 4), ([LEFT, B], 2), (N, 4), (R, 1)]
POPS = ON + [(N, 12), (AA, 2), (N, 14), (AA, 2), (N, 12)]                # three landings, 12 frames apart from standing
RUNS['crate'] = after(6300, PICK + POPS + [(N, 14), ([B], 2), (N, 60)])
RUNS['crate_ride'] = after(6300, PICK + POPS + walk(16) + [([B], 2), (N, 100)])
RUNS['crate_two'] = after(6300, PICK + POP2 + [(N, 12), ([B], 2), (N, 60)])     # with the crate on to the second cap (the crate is before it in the object list)
RUNS['crate_stand'] = after(6300, PICK + ON + [(N, 12), ([B], 2), (N, 40), (AA, 2), (N, 60)])
RUNS['crate_up'] = after(6300, PICK + ON + [(N, 12), ([UP, B], 2), (N, 90)])
RUNS['crate_down'] = after(6300, PICK + ON + [(N, 12), ([DOWN], 6), ([DOWN, B], 2), (N, 60)])
PART = 1200; KEEP = 3680
JOBS = []
for name_, (sc_, n_) in RUNS.items():
    f_ = KEEP; i_ = 0
    while f_ < n_:
        JOBS.append(('cp_' + name_ + ('' if i_ == 0 else '_' + 'bcdefg'[i_ - 1]), sc_, min(n_, f_ + PART), f_, 0)); f_ += PART; i_ += 1
def files(name): return [j[0] for j in JOBS if j[0] == 'cp_' + name or (j[0][-2] == '_' and j[0][-1] in 'bcdefg' and j[0][:-2] == 'cp_' + name)]
CHECKS4 = [('cp_' + name_, files(name_), RUNS[name_][0], 3695, 'dining', None) for name_ in RUNS]
# memory written: Chip's height on frame 6361 of a jump straight up from the floor under the first cap (its line is
# y 96; he rises 4 pixels on that frame)
_UP = after(6300, [(R, 8), (RA, 2), (R, 33), (N, 10), (AA, 20), (N, 60)])
_M = [('bump', 120), ('bump96', 100), ('bump95', 99)]
POKED = []; PORT_POKES = {}
for name_, v_ in _M:
    nm_ = 'cp_p_' + name_; pk_ = {6361: [('py', v_)]}; PORT_POKES[nm_] = pk_
    parts_ = []; k_ = KEEP; i_ = 0
    while k_ < _UP[1]:
        pn_ = nm_ + ('' if i_ == 0 else '_' + 'bcdefgh'[i_ - 1]); parts_.append(pn_)
        POKED.append((pn_, _UP[0], min(_UP[1], k_ + PART), k_, pk_)); k_ += PART; i_ += 1
    CHECKS4.append((nm_, parts_, _UP[0], 3695, 'dining', None))
# memory written: Chip's place on frame 6339 of the fall onto the first cap (he has let go of RIGHT, the cap is at
# x 134 of the screen): 13, 14 and 15 pixels to either side of its middle.  He lands on it up to 14.
_DN = after(6300, [(R, 8), (RA, 12), (R, 17), (N, 40), (AA, 2), (N, 60)])
for d_ in (-15, -14, -13, 13, 14, 15):
    nm_ = 'cp_p_edge%s%d' % ('l' if d_ < 0 else 'r', abs(d_)); pk_ = {6339: [('px', 134 + d_)]}; PORT_POKES[nm_] = pk_
    parts_ = []; k_ = KEEP; i_ = 0
    while k_ < _DN[1]:
        pn_ = nm_ + ('' if i_ == 0 else '_' + 'bcdefgh'[i_ - 1]); parts_.append(pn_)
        POKED.append((pn_, _DN[0], min(_DN[1], k_ + PART), k_, pk_)); k_ += PART; i_ += 1
    CHECKS4.append((nm_, parts_, _DN[0], 3695, 'dining', None))
# memory written: Chip's place on frame 6410, falling next to the first cap in its flight (it is at x 150 of the screen,
# 5 pixels below his feet), and then walking into it: from 17 pixels left of its middle, from 27 right of it
for nm_, px_, key_ in (('cp_p_fsider', 133, R), ('cp_p_fsidel', 177, L)):
    rt_ = after(6300, POPS + [(N, 25), (key_, 10), (N, 60)]); pk_ = {6410: [('px', px_)]}; PORT_POKES[nm_] = pk_
    parts_ = []; k_ = KEEP; i_ = 0
    while k_ < rt_[1]:
        pn_ = nm_ + ('' if i_ == 0 else '_' + 'bcdefgh'[i_ - 1]); parts_.append(pn_)
        POKED.append((pn_, rt_[0], min(rt_[1], k_ + PART), k_, pk_)); k_ += PART; i_ += 1
    CHECKS4.append((nm_, parts_, rt_[0], 3695, 'dining', None))
# the cap's sound ($4A) alone: only the 1st square / 2nd square / triangle / noise channel
FX = [('cp_fx_cap_sq1', 0x4A, 0x1E), ('cp_fx_cap_sq2', 0x4A, 0x1D), ('cp_fx_cap_tri', 0x4A, 0x1B), ('cp_fx_cap_noi', 0x4A, 0x17)]

if __name__ == '__main__':
    import multiprocessing as mp
    from capture_hurt import _run, _fx
    only = sys.argv[1:] or None
    def want(n): return only is None or n in only or (n[-2] == '_' and n[:-2] in only)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_run, [j for j in JOBS if want(j[0])], chunksize=1)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(CM._poked, [j for j in POKED if want(j[0])], chunksize=1)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_fx, [j for j in FX if only is None or j[0] in only], chunksize=1)
    print('done')

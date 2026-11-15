#!/usr/bin/env python3
"""Emulator runs for step 15 (level 1, section 3: the stove and the sink).  Results: work/s3_<name>.pkl
  s3_route0..2  level1_route.json, level1_route2.json up to the kitchen's exit, then level1_route3.json: the third
                section played from its start to the sink (the whole way to its exit is in the json, the part in the
                sink needs things of later steps)
  the RUNS      the route up to some frame, then other buttons: a fall into a pit, lost lives up to GAME OVER and
                CONTINUE, random buttons on the first screen, the status screen, held buttons at the section
                change, three with Dale.  Stored in parts of 1200 frames.
  the POKED     the exit cannot be reached without the rising water of the sink (a later step), so in these the
                player is put into the sink and then next to the exit by writes into the game's memory
  CHECKS5       what sim_sec3.py compares: (name, recordings, buttons, first NES frame, how the port starts, last frame)
usage: capture_sec3.py [job ...]     (everything: ~4 min)"""
import json, os, sys
from scenario import run_many
import capture_kitchen as CK
from capture_kitchen import after, rnd
from emu import START, SELECT, A, B, UP, DOWN, LEFT, RIGHT
N = []; L = [LEFT]; R = [RIGHT]
R3 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'level1_route3.json')))
S0 = R3['start_frame']                               # 6841; the route was found from a start without buttons after 6600
ROUTE3 = {f_: k_ for f_, k_ in CK.ROUTE2.items() if f_ < 6600}; f = S0
for keys, n in R3['inputs']:
    for i in range(n): ROUTE3[f] = keys; f += 1
ROUTE3_END = f
K0 = 6619                                            # NES frame on which the section's picture comes on (its level frame 0)
SINK = 8076                                          # the route's last frame before the player lands in the sink
CUTS = [6540, 7060, 7580, 8100]
JOBS = [('s3_route%d' % i, ROUTE3, CUTS[i + 1], CUTS[i]) for i in range(3)]
ROUTE_FILES = ['s3_route%d' % i for i in range(3)]
KEEP = 6540                                          # every run is kept from here: the end of the kitchen

RUNS = {}
PIT = [(R, 90), ([RIGHT, A], 18), (R, 40)]           # over the first crates and into the first pit
RUNS['fall'] = after(S0, PIT + [(N, 109), (R, 60), ([RIGHT, A], 20), (N, 30)], ROUTE3)
RUNS['over'] = after(S0, PIT + [(N, 109)] + PIT + [(N, 109)] + PIT + [(N, 400), ([A], 2), (N, 250), (R, 30)], ROUTE3)    # three times: GAME OVER, CONTINUE: the dining room
for s_ in (1, 2, 3): RUNS['rnd%d' % s_] = after(6640, rnd(s_) + [(N, 20)], ROUTE3)
RUNS['select'] = after(6900, [(N, 5), ([SELECT], 2), (N, 60), ([SELECT], 2), (N, 40), ([LEFT, A], 20), (N, 30), ([SELECT], 2), (N, 30), ([SELECT], 2), (N, 40)], ROUTE3)
RUNS['select2'] = after(6660, [(R, 20), ([SELECT], 2), (N, 60), ([SELECT], 2), (N, 40)], ROUTE3)
RUNS['hold'] = after(6600, [([RIGHT, A], 120), (N, 40)], ROUTE3)          # buttons held while the section appears
RUNS['hold2'] = after(6600, [(N, 36), ([A], 3), (N, 40)], ROUTE3)
RUNS['top'] = after(S0, [(R, 90), ([RIGHT, A], 18), (N, 10), ([A], 30), (N, 40), ([LEFT, A], 30), (N, 40)], ROUTE3)      # jumps from the first shelf
ROUTE3D = {**ROUTE3, 1150: [SELECT]}                                      # the same with Dale
RUNS['dl_enter'] = after(6600, [(N, 40), (R, 60), ([RIGHT, A], 20), (N, 30)], ROUTE3D)
RUNS['dl_select'] = after(6900, [(N, 5), ([SELECT], 2), (N, 60), ([SELECT], 2), (N, 40)], ROUTE3D)
RUNS['dl_fall'] = after(S0, PIT + [(N, 109), (R, 60), ([RIGHT, A], 20), (N, 30)], ROUTE3D)
PART = 1200
JOBS2 = []
def parts(name, sc, n, extra):
    out = []; f_ = KEEP; i_ = 0
    while f_ < n:
        out.append(('s3_' + name + ('' if i_ == 0 else '_' + 'bcdefg'[i_ - 1]), sc, min(n, f_ + PART), f_, extra)); f_ += PART; i_ += 1
    return out
for name_, (sc_, n_) in RUNS.items(): JOBS2 += parts(name_, sc_, n_, 0)

# the exit: the route up to the shelf left of the sink, then the player is put into the sink (frame 7730), walks on to the
# right and is put next to the exit (7830).  ('px' / 'py': the player's place on the screen; sim_sec3.py does the same to the port)
TAP = S0 + 831
_E = {'exit1': ([(R, 58), (N, 40), (R, 35), (N, 87)], 244),                 # comes down on the exit box
      'exit2': ([(R, 58), (N, 40), (R, 35), (N, 29), (R, 80)], 240),                     # 6 pixels further left: next to the exit box, on the sink's wall
      'exit3': ([(R, 58), (N, 40), (R, 35), (N, 22), ([DOWN], 50), (N, 60)], 246),       # comes down on it crouching: taken when he gets up
      'exit4': ([(R, 58), (N, 40), (R, 35), (N, 22), (L, 80), (N, 30)], 250),            # comes down on it moving left
      'sink': ([(R, 58), (N, 30), (R, 30), (L, 50), ([LEFT, A], 30), ([RIGHT, A], 30), (N, 30)], 0)}             # about in the empty sink
# under the tap: dropped through the running water (blocks $8C / $8B / $8A / $8B and $8D / $8A / $8B / $9F)
_E['tap1'] = ([(R, 58), (N, 100)], 0); _E['tap2'] = ([(R, 58), (N, 100)], 0)
_P = {'tap1': {7730: [('px', 156), ('py', 40)]}, 'tap2': {7730: [('px', 172), ('py', 40)]}}
POKED = []; PORT_POKES = {}
for name_, (runs_, x_) in _E.items():
    sc_, n_ = after(TAP, runs_, ROUTE3); pk_ = _P.get(name_) or {7730: [('px', 170), ('py', 100)]}
    if x_: pk_[7830] = [('px', x_), ('py', 150)]
    POKED.append(('s3_p_' + name_, sc_, n_, 7600, pk_))
    PORT_POKES['s3_p_' + name_] = pk_
def files(name): return [j[0] for j in JOBS2 + POKED if j[0] == 's3_' + name or j[0][:-2] == 's3_' + name]

# all start two seconds before the kitchen's exit is entered: the port takes the place of the player and the camera
# from the NES there ('middle'), walks out of the kitchen and into the third section
KT = 'kt_route3'                                     # (capture_kitchen.py: the route's frames 5970-6759)
CHECKS5 = [('s3_route', ROUTE_FILES, ROUTE3, 6552, 'middle', SINK)]
for name_ in RUNS: CHECKS5.append(('s3_' + name_, files(name_), RUNS[name_][0], 6552, 'middle', None))
for name_ in _E: CHECKS5.append(('s3_p_' + name_, files('p_' + name_), after(TAP, _E[name_][0], ROUTE3)[0], 7652, 'sec3', None))

if __name__ == '__main__':
    import multiprocessing as mp
    from capture_hurt import _run
    from capture_mice import _poked
    only = sys.argv[1:] or None
    run_many(JOBS, only=only)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_run, [j for j in JOBS2 if only is None or j[0] in only], chunksize=1)
        p.map(_poked, [j for j in POKED if only is None or j[0] in only], chunksize=1)
    print('done')

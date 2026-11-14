#!/usr/bin/env python3
"""Emulator runs for deliverable 5 (level 1, section 1: map and camera).  Results: work/lv1_<name>.pkl  (about 3 minutes, 2 GB)
  skip, skip2  START in the night scene (NES frame 1300 / 1500): the level starts, nothing is pressed afterwards
  news         nothing pressed after the menus: night scene, newscaster cutscene, then the level
  route0..2    level1_route.json: the section played from its start to the exit and into the next section
  music, music_sq2, music_rest   like skip but 12000 frames, sound only: all channels / square 2 only / all but square 2"""
import json, os, sys
from scenario import run_many
from emu import START
BASE = {1000: [START], 1100: [START], 1200: [START]}
SKIP = {**BASE, 1300: [START]}
R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'level1_route.json')))
ROUTE = dict(SKIP); f = R['start_frame']
for keys, n in R['inputs']:
    for i in range(n): ROUTE[f] = keys; f += 1
ROUTE_END = f                                     # first frame after the last input
JOBS = [('lv1_skip', SKIP, 2300, 1340), ('lv1_skip2', {**BASE, 1500: [START]}, 1800, 1540), ('lv1_news', BASE, 11300, 10780),
        ('lv1_route0', ROUTE, 2500, 1700), ('lv1_route1', ROUTE, 3300, 2500), ('lv1_route2', ROUTE, ROUTE_END + 400, 3300),
        ]
# sound only (too long to keep the pictures): (name, schedule, frames, mute mask)
SOUND = [('lv1_music', SKIP, 12000, 0), ('lv1_music_sq2', SKIP, 12000, 0x1D), ('lv1_music_rest', SKIP, 12000, 0x02)]

def _sound(args):
    name, sched, n, mute = args
    if mute: os.environ['MESEN_MUTE'] = str(mute)
    import pickle, numpy as np
    from emu import Emu, WORK
    e = Emu(); apu = []; cnt = []; ram = []
    for i in range(n):
        e.step(sched.get(i, [])); apu.append(e.apu_writes()); cnt.append(sum(len(a) for a in e.audio))
        r = e.ram(); ram.append((int(r[0x10]), int(r[0x13]), int(r[0x314]), int(r[0x2FC]), int(r[0xA7])))
    pickle.dump(dict(apu=apu, aud=np.concatenate(e.audio)[:, 0], cnt=np.array(cnt), ram=ram, f0=0), open(os.path.join(WORK, name + '.pkl'), 'wb'), protocol=4)

if __name__ == '__main__':
    import multiprocessing as mp
    only = sys.argv[1:] or None
    run_many(JOBS, only=only)
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_sound, [j for j in SOUND if only is None or j[0] in only], chunksize=1)
    print('done')

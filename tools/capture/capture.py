#!/usr/bin/env python3
"""Runs the ROM in the (patched) Mesen libretro core and stores everything the other scripts need
in tools/capture/work/ :
  st_idle.pkl / frames_idle.npy  per-frame PPU state + rendered frames, power-on -> frame 1199, no input
  aud_long.npy / cnt_long.npy    audio of a 4000 frame run without input (+ sample count after each frame)
  audL_skip300 / cntL_skip300    audio of a run where START is pressed on frame 300 (clean title theme)
  fr_skip<T>.npy                 rendered frames T-2 .. T+397 of runs where START is pressed on frame T
Every run is a separate process: the core keeps global state, one instance per process only."""
import sys, pickle, multiprocessing as mp
import numpy as np
SKIPS = (187, 188, 235, 300, 410, 474, 568, 650, 652, 653, 700, 706, 784, 800, 801, 802)

def idle(_):
    from emu import Emu, WORK
    e = Emu(); st = []; fr = []
    for i in range(1200):
        fr.append(e.step())
        p = {k: (v.copy() if hasattr(v, 'copy') else v) for k, v in e.ppu().items()}
        p['ram'] = e.ram().copy(); st.append(p)
    pickle.dump(st, open(WORK + '/st_idle.pkl', 'wb')); np.save(WORK + '/frames_idle.npy', np.array(fr))

def audio(t):
    from emu import Emu, WORK, START
    e = Emu(); cnt = []
    for i in range(4000):
        e.step([START] if t is not None and t <= i < t + 2 else [])
        cnt.append(sum(len(a) for a in e.audio))
    a = np.concatenate(e.audio)
    if t is None:
        np.save(WORK + '/aud_long.npy', a); np.save(WORK + '/cnt_long.npy', np.array(cnt))
    else:
        np.save(WORK + '/audL_skip%d.npy' % t, a[:, 0]); np.save(WORK + '/cntL_skip%d.npy' % t, np.array(cnt))

def skip(t):
    from emu import Emu, WORK, START
    e = Emu(); fr = []
    for i in range(t + 398):
        f = e.step([START] if t <= i < t + 2 else [])
        if i >= t - 2: fr.append(f)
    np.save(WORK + '/fr_skip%d.npy' % t, np.array(fr))

def job(j):
    globals()[j[0]](j[1])

if __name__ == '__main__':
    jobs = [('idle', None), ('audio', None), ('audio', 300)] + [('skip', t) for t in SKIPS]
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(job, jobs, chunksize=1)
    print('captured', len(jobs), 'runs')

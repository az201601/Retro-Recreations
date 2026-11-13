#!/usr/bin/env python3
"""Run one input scenario in its own process and store the result in work/<name>.pkl
usage (python):  from scenario import run;  d = run('name', {1000: [START], 1001: [START]}, 1400, keep_from=990)
d = dict(frames=[...], st=[ppu+ram per frame], apu=[list of APU writes per frame], aud=int16 mono, cnt=samples after each frame, f0=keep_from)"""
import pickle, os, multiprocessing as mp
import numpy as np

def _run(args):
    name, sched, n, keep_from, mute = args
    if mute: os.environ['MESEN_MUTE'] = str(mute)
    from emu import Emu, WORK
    e = Emu(); fr = []; st = []; apu = []; cnt = []
    for i in range(n):
        f = e.step(sched.get(i, []))
        w = e.apu_writes(); cnt.append(sum(len(a) for a in e.audio))
        if i >= keep_from:
            fr.append(f); apu.append(w)
            p = {k: (v.copy() if hasattr(v, 'copy') else v) for k, v in e.ppu().items()}
            p['ram'] = e.ram().copy(); st.append(p)
    d = dict(frames=np.array(fr), st=st, apu=apu, aud=np.concatenate(e.audio)[:, 0], cnt=np.array(cnt), f0=keep_from)
    pickle.dump(d, open(os.path.join(WORK, name + '.pkl'), 'wb'), protocol=4)
    return name

def run_many(jobs):
    """jobs: list of (name, sched, n, keep_from[, mute])"""
    jobs = [j if len(j) == 5 else j + (0,) for j in jobs]
    with mp.Pool(2, maxtasksperchild=1) as p:
        p.map(_run, jobs, chunksize=1)

def load(name):
    from emu import WORK
    return pickle.load(open(os.path.join(WORK, name + '.pkl'), 'rb'))

def hold(sched, frame, keys, n=2):
    for i in range(frame, frame + n): sched[i] = list(keys)
    return sched

#!/usr/bin/env python3
"""Interactive helper for looking at the game: one emulator, savestates, a compact per-frame log.
    from explore import *;  x = X();  x.to_level();  x.save('start');  x.run([([RIGHT], 30), ([RIGHT, A], 20)])
Not used by the build or check tools."""
import ctypes as C, os, pickle
import numpy as np
from emu import Emu, WORK, START, SELECT, A, B, UP, DOWN, LEFT, RIGHT
NAMES = {B: 'B', SELECT: 's', START: 'S', UP: 'U', DOWN: 'D', LEFT: 'L', RIGHT: 'R', A: 'A'}

class X:
    def __init__(s):
        s.e = Emu(); s.states = {}; s.hist = []
    def step(s, keys=()):
        fr = s.e.step(keys); s.hist.append(list(keys)); return fr
    def to_level(s, dale=False, until=1390):
        for f in range(until):
            k = []
            if f in (1000, 1100, 1200, 1300): k = [START]
            if dale and f == 1150: k = [SELECT]
            s.step(k)
    def save(s, name):
        n = s.e.lib.retro_serialize_size(); buf = C.create_string_buffer(n)
        assert s.e.lib.retro_serialize(buf, n); s.states[name] = (buf.raw, s.e.n, list(s.hist))
        pickle.dump(s.states[name], open(os.path.join(WORK, 'st_%s.pkl' % name), 'wb'))
    def load(s, name):
        if name not in s.states: s.states[name] = pickle.load(open(os.path.join(WORK, 'st_%s.pkl' % name), 'rb'))
        raw, n, hist = s.states[name]
        assert s.e.lib.retro_unserialize(raw, len(raw)); s.e.n = n; s.hist = list(hist); s.world = {}; s.wcam = -999
        s.e.apu_writes()
    def ram(s): return s.e.ram()
    def blocks(s):
        """changes of the 16x16 blocks on screen since the last call: (world column, row, old, new)"""
        r = s.ram(); cam = s.cam(); m = r[0x43A:0x43A + 240].reshape(15, 16); out = []
        if not hasattr(s, 'world') or abs(cam - s.wcam) > 64: s.world = {}
        s.wcam = cam
        for wc in range(cam // 16 + 1, cam // 16 + 15):
            for row in range(15):
                v = int(m[row, wc % 16]); o = s.world.get((wc, row))
                if o is not None and o != v: out.append((wc, row, o, v))
                s.world[(wc, row)] = v
        return out
    def cam(s): r = s.ram(); return int(r[0x10]) + 256 * int(r[0x13])
    def line(s, keys, prev):
        """returns (text, event?)"""
        r = s.ram(); ev = False
        out = '%5d %-4s st %2d x %3d y %3d cam %4d an %02X cel %2d' % (
            s.e.n - 1, ''.join(NAMES[k] for k in keys), r[0xB8], int(r[0x314]) + 256 * int(r[0x320]), r[0x2FC], s.cam(), r[0xC6], r[0x338])
        for i in range(1, 8):
            if r[0x32C + i] not in (0, 2):
                out += ' | #%d t%02X st%02X %d,%d c%d' % (i, r[0x32C + i], r[0xB8 + i], int(r[0x314 + i]) + 256 * int(r[0x320 + i]), r[0x2FC + i], r[0x338 + i])
        if prev is not None:
            if r[0xB8] != prev[0xB8] or any(r[0x32C + i] != prev[0x32C + i] or r[0xB8 + i] != prev[0xB8 + i] for i in range(1, 8)): ev = True
        for wc, row, old, new in s.blocks():
            out += ' | block col %d row %d %02X->%02X' % (wc, row, old, new); ev = True
        w = s.e.apu_writes()
        if w and w[0] == (0x400C, 0xF0): out += ' | snd'; ev = True
        return out, ev
    def run(s, runs, show=1, watch=(), skip=()):
        """show: 0 nothing, 1 events only, 2 every frame.  skip: object types not worth an event"""
        prev = None
        for keys, n in runs:
            for i in range(n):
                s.step(keys); ln, ev = s.line(keys, prev); r = s.ram()
                for a in watch:
                    ln += ' $%X=%02X' % (a, r[a])
                    if prev is not None and prev[a] != r[a]: ev = True
                prev = r.copy()
                if show == 2 or (show == 1 and ev): print(ln)
        print(s.line([], None)[0])

def rl(seq):
    """run-length text of a list"""
    out = []; 
    for v in seq:
        if out and out[-1][0] == v: out[-1][1] += 1
        else: out.append([v, 1])
    return ' '.join('%s%s' % (v, '' if n == 1 else 'x%d' % n) for v, n in out)

def trace(x, runs, slot=3):
    """runs the inputs; returns per-frame dicts"""
    T = []
    for keys, n in runs:
        for i in range(n):
            x.step(keys); r = x.ram().copy(); w = x.e.apu_writes()
            T.append(dict(f=x.e.n - 1, st=int(r[0xB8]), x=int(r[0x314]) + 256 * int(r[0x320]), y=int(r[0x2FC]), cam=x.cam(), cel=int(r[0x338]),
                          h=int(r[0x3BC]), face=int(r[0x344]) >> 6 & 1, ox=int(r[0x314 + slot]) + 256 * int(r[0x320 + slot]), oy=int(r[0x2FC + slot]) + 256*int(r[0x308+slot]),
                          ot=int(r[0x32C + slot]), ost=int(r[0xB8 + slot]), snd=bool(w and w[0] == (0x400C, 0xF0)), ram=r))
    return T

def summ(T):
    print('  player st  ', rl([t['st'] for t in T]))
    print('  player cel ', rl([t['cel'] for t in T]))
    print('  player x,y ', rl(['%d,%d' % (t['x'] + t['cam'], t['y']) for t in T]))
    print('  crate-plr  ', rl(['%d,%d' % (t['ox'] - t['x'], t['oy'] - t['y']) for t in T]))
    print('  crate step ', rl(['%d,%d' % (b['ox'] + b['cam'] - a['ox'] - a['cam'], b['oy'] - a['oy']) for a, b in zip(T, T[1:])]))
    print('  sound at   ', [i for i, t in enumerate(T) if t['snd']])

def pcs(x):
    """set of CPU addresses executed since the last call"""
    p = x.e.lib.retro_get_memory_data(108); d = np.frombuffer(C.string_at(p, 8192), np.uint8)
    s = set(int(v) for v in np.nonzero(np.unpackbits(d, bitorder='little'))[0]); x.e.lib.retro_get_memory_data(109); return s

def ranges(s):
    out = []; 
    for a in sorted(s):
        if out and a - out[-1][1] <= 3: out[-1][1] = a
        else: out.append([a, a])
    return ' '.join('%04X-%04X' % (a, b) for a, b in out)

#!/usr/bin/env python3
"""Step 15: two measurements in the emulator that the port cannot be compared on yet (they need the crates and the
sink's object of later steps).  Prints what it finds.  ~1 min.
 1. Flashing.  A carried crate flashes after 30 frames of running.  On which values of the game's frame counter
    ($2D) is it bright, in the kitchen and in the third section?  (The same in both: the port's count, which is
    compared in the kitchen, is then right in the third section too.)
 2. The landing sound on the floor of the sink, with the object of type $1E on the screen: landing at several
    places, by walking off the shelf above the sink and by jumping from it."""
import collections
from explore import X
from emu import A, B, LEFT, RIGHT
import capture_kitchen as CK, capture_sec3 as S3
N = []; L = [LEFT]; R = [RIGHT]

def bright(x):
    """the carried crate's colour set: 0 normal, 1 bright; None if no crate is carried"""
    r = x.ram(); o = x.e.ppu()['oam'].reshape(64, 4).astype(int)
    for j in range(3, 12):
        if int(r[0x32C + j]) == 3 and (int(r[0x2F0 + j]) & 15) in (3, 9):
            ox = int(r[0x314 + j]); oy = int(r[0x2FC + j])
            a = [q[2] & 3 for q in o if q[0] < 0xEF and -9 <= q[3] - ox <= 1 and -18 <= q[0] - oy <= -1 and q[1] in (140, 141)]
            if a: return max(a)
    return None

def flash(args):
    which, start, runs = args; route = CK.ROUTE2 if which == 'kitchen' else S3.ROUTE3
    x = X(); seq = []
    for f in range(start): x.step(route.get(f, []))
    for k, cnt in runs:
        for i in range(cnt):
            x.step(k); b = bright(x)
            if b is not None: seq.append((int(x.ram()[0x2D]) % 8, int(b)))
    T = collections.defaultdict(collections.Counter)
    for i, (m, b) in enumerate(seq):                           # only while it flashes: within 5 frames of a bright frame
        if any(q for _, q in seq[max(i - 5, 0):i + 6]): T[m][b] += 1
    return {m: dict(v) for m, v in sorted(T.items())}

def landings(_):
    x = X(); out = []
    for f in range(8030): x.step(S3.ROUTE3.get(f, []))          # on the shelf above the sink's left end
    x.save('m_sink')
    T = [('the route', [(S3.ROUTE3.get(f, []), 1) for f in range(8030, 8100)]), ('walks off, 16 frames right', [(R, 16), (N, 60), ([A], 20), (N, 40)]),
         ('walks off, 30 frames right', [(R, 30), (N, 60), ([A], 20), (N, 40)]), ('walks off, 45 frames right', [(R, 45), (N, 60)]),
         ('jumps, 10 frames right', [([RIGHT, A], 10), (N, 80), ([A], 20), (N, 40)]), ('jumps, 30 frames right', [([RIGHT, A], 30), (N, 60), ([A], 20), (N, 40)])]
    for name, runs in T:
        x.load('m_sink'); prev = 5; ev = []
        for k, cnt in runs:
            for i in range(cnt):
                x.step(k); w = [tuple(q) for q in x.e.apu_writes()]; r = x.ram(); st = int(r[0xB8]); wx = int(r[0x314]) + x.cam()
                if st == 2 and prev != 2: ev.append('lands at x %d, y %d on frame %d' % (wx, int(r[0x2FC]), x.e.n - 1))
                if (0x4006, 0x70) in w and (0x4004, 0xBF) in w: ev.append('sound on frame %d' % (x.e.n - 1))
                fl = int(r[0x2F0 + 4])
                if fl == 0x09 and 'the object changes' not in ' '.join(ev): ev.append('the object changes on frame %d (player at x %d)' % (x.e.n - 1, wx))
                prev = st
        out.append((name, ev))
    return out

if __name__ == '__main__':
    import multiprocessing as mp
    with mp.Pool(1, maxtasksperchild=1) as p:                   # (one emulator per process)
        k = p.apply(flash, (('kitchen', 3752, [(R, 75), ([RIGHT, B], 2), (N, 6), (L, 70), (N, 5), (R, 60)]),))
        s = p.apply(flash, (('third', S3.S0, [(R, 100), ([RIGHT, B], 2), (N, 6), (L, 90), (N, 5), ([RIGHT, A], 20), (R, 40)]),))
        ld = p.apply(landings, (0,))
    print('carried crate while it flashes: frames per value of $2D mod 8 {0 normal, 1 bright}')
    print('  kitchen      ', k); print('  third section', s)
    print('  bright on the same values:', sorted(m for m in k if 1 in k[m]) == sorted(m for m in s if 1 in s[m]), sorted(m for m in s if 1 in s[m]))
    print('landing in the sink (the landing sound comes 2 frames after a landing):')
    for name, ev in ld: print('  %-28s %s' % (name, '; '.join(ev)))

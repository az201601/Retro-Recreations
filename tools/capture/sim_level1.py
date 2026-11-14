#!/usr/bin/env python3
"""Python port of the level-1 part of obj_intro (section 7 of Step, last block of Draw) as of deliverable 5: the
background of section 1, its fade-in, the camera position and the fade-out at the exit.  Compared with the
capture_level1.py recordings.  Keep in sync with recreation/05_level1_map/gml/obj_intro_*.gml

The player does not exist yet in the GML, so two things are taken from the recording instead of being computed: the
camera position of every frame and the frame on which the player leaves the section.  Everything the original draws
as sprites (player, enemies, hearts) and every crate that was picked up during the recording is left out of the
comparison.   usage: sim_level1.py"""
import os, pickle
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
from build_level1 import D0, E0, CAM_MAX, scroll
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, 'recreation', '05_level1_map', 'assets', 'sprites') + '/'
BG = [np.array(Image.open('%sspr_lv1a_bg_%d.png' % (A, i)).convert('RGB')) for i in range(56)]
M = pickle.load(open(os.path.join(WORK, 'lv1_map.pkl'), 'rb'))

class Level:
    def __init__(s):
        s.lt = -8            # level clock: -7 on the frame the previous screen ends, 0 = first frame of the level's picture
        s.cam = 0            # camera: x of the left screen edge in the section, 0 .. 1792
        s.exit_t = -1        # lt on which the player left the section
        s.done = False
    def step(s, cam, leave):
        s.lt += 1
        if s.done: return
        s.cam = min(max(cam, 0), CAM_MAX)
        if leave and s.exit_t < 0: s.exit_t = s.lt
        if s.exit_t >= 0 and s.lt == s.exit_t + 22: s.done = True
    def draw(s):
        scr = np.zeros((240, 256, 3), np.uint8); t = s.lt
        if t < 5 or s.done: return scr
        sub = min((t - 5) // 4, 3)                           # 0-2 fade-in, 3 normal
        if s.exit_t >= 0 and t >= s.exit_t + 5:
            sub = 4 + (t - s.exit_t - 5) // 4                # 4-6 fade-out
            if sub > 6: return scr
        n = s.cam // 256; x = n * 256 - s.cam
        scr[:, :256 + x] = BG[n * 7 + sub][:, -x:]
        if x < 0: scr[:, 256 + x:] = BG[(n + 1) * 7 + sub][:, :-x]
        scr[:, :8] = 0                                       # the NES shows nothing in the left-most 8 pixels
        return scr

def compare(names, d0, first, cam_from_picture, leave_at, last=None):
    g = Level(); n = bad = 0; f = d0; worst = []
    done = set()                                             # (column, row) of map tiles that have changed (crates picked up)
    for name in names:
        d = load(name); f0 = d['f0']
        for i, st in enumerate(d['st']):
            fr = f0 + i
            if fr < d0 or (last is not None and fr > last): continue
            while f <= fr:                                   # the port's clock starts on frame d0 (lt = -7)
                cam = scroll(st) if cam_from_picture and st['mask'] else 0
                if cam_from_picture: cam = min(range(cam, 2048, 512), key=lambda c: abs(c - g.cam))     # 0..511 -> position in the section
                g.step(cam, leave_at is not None and f == leave_at); f += 1
            if fr < first: continue
            for cf, c, rows in M['changes']:
                if cf <= fr + 1: done |= {(c, r) for r in rows}
            ok = np.ones((240, 256), bool)
            o = st['oam'].reshape(64, 4).astype(int)
            for y, _, _, x in o:
                if y < 239: ok[y + 1:y + 9, x:x + 8] = False
            for c, r in done:
                x = c * 8 - g.cam
                if -8 < x < 256: ok[r * 8:r * 8 + 8, max(x, 0):x + 8] = False
            diff = (g.draw() != d['frames'][i]).any(axis=2) & ok
            n += 1
            if diff.any(): bad += 1; worst.append((fr, int(diff.sum())))
        del d
    print('%-28s frames %5d  differing %4d %s' % (names[0], n, bad, worst[:5]))
    return n, bad

if __name__ == '__main__':
    tot = [0, 0]
    for r in (compare(['lv1_skip'], D0, D0, False, None), compare(['lv1_skip2'], D0 + 200, D0 + 200, False, None),
              compare(['lv1_news'], 10843, 10843, False, None),
              compare(['lv1_route0', 'lv1_route1', 'lv1_route2'], D0, 1700, True, E0, last=E0 + 30)):
        tot[0] += r[0]; tot[1] += r[1]
    print('frames compared %d, differing %d' % tuple(tot))

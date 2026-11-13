#!/usr/bin/env python3
"""Emulator runs for deliverable 3 (night scene with the blimp).  Results: work/prison_<name>.pkl  (about 3 minutes, 3 GB)
Every run goes START (title) -> START (1player) -> START (Chip); the menu reacts on frame R = last press + 1 and the
scene's first visible frame is R + 41."""
from scenario import run_many
from emu import START, A, B, SELECT

BASE = {1000: [START], 1100: [START], 1200: [START]}          # R = 1201, scene frame t = NES frame - 1242
# START pressed once during the scene, on NES frame p
SKIPS = (1254, 1255, 1300, 1401, 1650, 1740, 1766, 1767, 1800, 1850, 2000, 2100,
         *range(1715, 1735), 1861, 1862, 1863, 2200, 2230, 2240, 2244, 2245,
         2246, 2247, 2249, 2250, 2252, 2255, 2256, 2257, 2260, 2270, 2285, 2295, 2298, 2300)
RUNS = {'idle': (BASE, 2330, 1236),
        'shift3': ({1000: [START], 1100: [START], 1203: [START]}, 2333, 1239),      # same scene, 3 frames later
        'other': ({**BASE, 1300: [A], 1400: [B], 1500: [SELECT]}, 1700, 1236),      # other buttons do nothing
        'twice': ({**BASE, 1400: [START], 1420: [START]}, 1500, 1236),              # a second START press
        'twice2': ({**BASE, 1400: [START], 1440: [START]}, 1500, 1236), 'twice3': ({**BASE, 1900: [START], 1941: [START]}, 1970, 1236)}
for p in SKIPS:
    RUNS['k%d' % p] = ({**BASE, p: [START]}, min(p + 62, 2330), 1236)
if __name__ == '__main__':
    run_many([('prison_' + k,) + v for k, v in RUNS.items()])
    print('done')

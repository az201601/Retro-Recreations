#!/usr/bin/env python3
"""Emulator runs for deliverable 4 (newscaster cutscene).  Results: work/news_*.pkl  (about 10 minutes, 12 GB)
Every run goes START (title) -> START (1player) -> START (Chip) and lets the night scene play; the cutscene's first
visible frame is NES frame 2314.  Long runs are stored in chunks (each chunk re-runs the game from power-on)."""
import sys
from scenario import run_many
from emu import START, A, B, SELECT

BASE = {1000: [START], 1100: [START], 1200: [START]}
def chunks(name, sched, first, last, size):
    return [('%s%d' % (name, i), sched, min(a + size, last), a) for i, a in enumerate(range(first, last, size))]
JOBS = chunks('news_idle', BASE, 2296, 10876, 1430)                                               # no input: 6 chunks
BMASH = {**BASE, **{f: [B] for f in range(2330, 9000) if f % 4 < 2}}                              # B pressed every 4 frames
BSLOW = {**BASE, **{f: [B] for f in range(2330, 9000) if f % 16 < 2}}                             # B pressed every 16 frames
JOBS += chunks('news_bmash', BMASH, 2296, 4496, 1100) + chunks('news_bslow', BSLOW, 2296, 5296, 1000)
B_ONCE = (2436, 2437, 2438, 2439, 2440, 2455, 2456, 2459, 2460,                                   # while a page is typed
          2502, 2503, 2505, 2506, 2507, 2510, 2624, 2625, 2626, 2627, 2628, 2631, 2632)           # while a page waits / is cleared
for p in B_ONCE: JOBS.append(('news_b%d' % p, {**BASE, p: [B]}, 2760, 2420))
JOBS.append(('news_bhold', {**BASE, **{f: [B] for f in range(2430, 3400)}}, 3400, 2420))
JOBS.append(('news_other', {**BASE, 2420: [A], 2520: [A], 2700: [SELECT], 2800: [A], **{f: [A] for f in range(2900, 3000)}}, 3200, 2296))
S_ONCE = (2305, 2310, 2313, 2314, 2315, 2318, 2322, 2325, 2326, 2327, 2330, 2400, 3530, 5600, 7600,
          10700, 10770, 10780, 10790, 10800, 10815, 10830, 10838)
for p in S_ONCE: JOBS.append(('news_s%d' % p, {**BASE, p: [START]}, min(p + 80, 10880), max(2296, p - 12)))
# audio only (MESEN_MUTE bit0 square1, bit1 square2, bit2 triangle, bit3 noise, bit4 DMC).  Square 2 carries one voice of
# the music and the typing sound, so the music is recorded as two layers
JOBS.append(('news_aud_a', BASE, 4300, 4290, 2))             # music without square 2
JOBS.append(('news_aud_b', BASE, 10880, 10870, 29))          # square 2 only, no input
JOBS.append(('news_aud_bm', BMASH, 4300, 4290, 29))          # square 2 only, B mashed (hardly any typing sound)
JOBS.append(('news_aud_bs', BSLOW, 4300, 4290, 29))          # square 2 only, B every 16 frames (typing sounds elsewhere)
JOBS.append(('news_aud_bh', {**BASE, **{f: [B] for f in range(3062, 3400)}}, 3320, 3056, 29))   # square 2 only: three long notes without typing
JOBS.append(('news_aud_full', BASE, 4300, 4290))             # everything (for comparison)
if __name__ == '__main__':
    run_many(JOBS, only=sys.argv[1:] or None)
    print('done')

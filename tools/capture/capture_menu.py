#!/usr/bin/env python3
"""Emulator runs for deliverable 2 (1player/2players + Chip/Dale menus).  Results: work/menu_<name>.pkl
Needs the core built with the patch in this directory (APU write log + MESEN_MUTE).  About 2 minutes."""
from scenario import run_many
from emu import START, SELECT, UP, DOWN, A, B, LEFT, RIGHT

def sc(*ev):          # every button is held for 2 frames
    s = {}
    for f, k in ev:
        for i in (f, f + 1): s[i] = [k]
    return s

# name: (schedule {frame: [buttons]}, number of frames, first frame kept)
RUNS = {
 # menu 1: every button, then A confirms "1player"; menu 2: B, LEFT, RIGHT, SELECT
 'a': (sc((1000, START), (1100, UP), (1160, UP), (1220, DOWN), (1280, DOWN), (1340, A), (1400, B), (1460, LEFT), (1520, RIGHT), (1580, SELECT)), 1650, 990),
 'f': (sc((1000, START), (1100, B), (1160, LEFT), (1220, RIGHT), (1280, SELECT), (1340, A)), 1400, 990),          # 2players chosen with A
 'b': (sc((1000, START), (1100, DOWN), (1160, START)), 1230, 990),                                                # 2players chosen with START
 'c': (sc((1000, START), (1100, START), (1200, UP), (1260, UP), (1320, DOWN), (1380, DOWN), (1440, SELECT), (1500, A)), 1560, 990),   # Chip
 'g': (sc((1000, START), (1100, START), (1200, DOWN), (1300, START)), 1350, 990),                                 # Dale
 'e': (sc((1000, START), (1100, START), (1201, A)), 1260, 990),                                                   # Chip, other frame parity
 # single-frame presses: earliest accepted frames, several buttons at once, key held down
 't2': ({1000: [START], 1002: [START]}, 1060, 990),
 't3': ({1000: [START], 1003: [START]}, 1060, 990),
 'u3': ({1000: [START], 1003: [DOWN]}, 1060, 990),
 'h1': ({1000: [START], 1100: [START], 1101: [DOWN]}, 1160, 990),
 'h2': ({1000: [START], 1100: [START], 1102: [DOWN]}, 1160, 990),
 'h4': ({1000: [START], 1100: [START], 1102: [START]}, 1160, 990),
 'k':  ({1000: [START], 1100: [START], 1200: [START], 1202: [DOWN], 1204: [B]}, 1260, 990),
 'k2': ({1000: [START], 1100: [DOWN], 1101: [START]}, 1160, 990),
 'm1': ({1000: [START], 1100: [DOWN, START]}, 1160, 990),
 'm2': ({1000: [START], 1100: [UP, DOWN]}, 1160, 990),
 'm5': ({1000: [START], 1100: [SELECT, START]}, 1160, 990),
 'm7': ({1000: [START], 1100: [DOWN], 1101: [DOWN, UP], 1102: [UP]}, 1160, 990),
 'm8': ({1000: [START], 1100: [START], 1150: [SELECT, UP, A]}, 1200, 990),
 'fast': ({1000: [START], 1050: [DOWN], 1052: [DOWN], 1054: [UP], 1056: [SELECT], 1057: [SELECT, START]}, 1100, 990),
 'hold': ({f: ([START] if f == 1000 else [DOWN]) for f in [1000] + list(range(1050, 1150))}, 1160, 990),
 # intro skipped with START, then straight through the menus (frame parity / timing after a skip)
 'p1': ({301: [START], 400: [START], 500: [START], 531: [DOWN], 560: [A]}, 620, 290),
 'p2': ({303: [START], 401: [START], 501: [START], 540: [START]}, 600, 290),
}
# audio: MESEN_MUTE bit0 square1, bit1 square2, bit2 triangle, bit3 noise, bit4 DMC
AUDIO = {
 'aud_sq2':  ({300: [START]}, 3300, 3299, 0x1D),     # title theme, square 2 only
 'aud_rest': ({300: [START]}, 3300, 3299, 0x02),     # title theme without square 2
 'aud_full': ({300: [START]}, 3300, 3299, 0x00),
 'aud_sfx':  (sc((1000, START), (1100, DOWN)), 1200, 1199, 0x1D),   # select sound from 1002, move sound from 1102 (square 2 only)
}
if __name__ == '__main__':
    run_many([('menu_' + k,) + v for k, v in RUNS.items()] + [('menu_' + k,) + v for k, v in AUDIO.items()])
    print('done')

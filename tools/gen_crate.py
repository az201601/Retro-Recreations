#!/usr/bin/env python3
"""Draw sprCrate (16x16) in the Stage-1 NES palette, matching the in-game crates."""
import os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT,'ChipNRangers2.project','sprites','images','sprCrate_0.png')
K=(0,0,0,255); W=(248,248,248,255); B=(71,109,255,255); N=(0,25,188,255)
im = Image.new('RGBA',(16,16),(0,0,0,0))
px = im.load()
for y in range(16):
    for x in range(16):
        if x in (0,15) or y in (0,15):          c = K          # outline
        elif y == 1 or x == 1:                  c = W          # top/left highlight
        elif x == 14 or y == 14:                c = N          # right/bottom shade
        elif (y - 2) % 4 == 3:                  c = N          # slat lines
        else:                                   c = B
        px[x,y] = c
im.save(OUT)
print('sprCrate written', OUT)

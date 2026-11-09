#!/usr/bin/env python3
"""Build GameMaker-ready assets from the Mesen/jsnes capture data."""
import os, json, math
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets_src')
OUT = os.path.join(ROOT, 'ChipNRangers2.project')
TMP = os.path.join(SRC, 'refs')

def p(*a): return os.path.join(*a)
os.makedirs(p(OUT,'sprites','images'), exist_ok=True)
os.makedirs(p(OUT,'background','images'), exist_ok=True)
os.makedirs(p(OUT,'sound'), exist_ok=True)

# ---------------------------------------------------------------- player
def frame(name):
    return Image.open(p(SRC,'player_raw3',name)).convert('RGBA')

player_sets = {
    'sprPlayerIdle': ['f002_idle.png','f010_idle.png'],
    'sprPlayerWalk': ['f021_walk.png','f025_walk.png','f029_walk.png','f033_walk.png'],
    'sprPlayerJump': ['f050_jump.png','f059_jump.png'],
    'sprPlayerAct':  ['f084_actB.png','f086_actB.png'],
}
for spr, files in player_sets.items():
    for i,f in enumerate(files):
        im = frame(f)
        # trim fully transparent border but keep canvas 32x32 (origin stays 16,26)
        im.save(p(OUT,'sprites','images',f'{spr}_{i}.png'))

# ---------------------------------------------------------------- heart (from HUD sprite layer)
sl = Image.open(p(TMP,'sprites0.png')).convert('RGB')
# locate a heart: scan bottom-left area for blue heart pixels
hb = sl.crop((16,209,24,217))
print('heart extracted at 16,209')
# make alpha version: magenta -> transparent
def with_alpha(im, key=(255,0,255)):
    im = im.convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x,y][:3] == key:
                px[x,y] = (0,0,0,0)
    return im
hb = with_alpha(hb)
hb.save(p(OUT,'sprites','images','sprHeart_0.png'))

# ---------------------------------------------------------------- crate (ripped from gameplay frame)
b05 = Image.open(p(TMP,'b05.png')).convert('RGB')
crate = b05.crop((189,157,205,173)).convert('RGBA')
crate.save(p(OUT,'sprites','images','sprCrate_0.png'))

# ---------------------------------------------------------------- bug enemy (designed in NES palette)
PAL = {
    'K': (0,0,0), 'B': (0x00,0x54,0xB1), 'L': (0x88,0xED,0xF8),
    'W': (0xF8,0xF8,0xF8), 'R': (0xDC,0x0E,0x22), 'Y': (0xFF,0xAB,0x3C),
}
def draw_art(rows, palette=PAL):
    h=len(rows); w=max(len(r) for r in rows)
    im = Image.new('RGBA',(w,h),(0,0,0,0)); px=im.load()
    for y,r in enumerate(rows):
        for x,ch in enumerate(r):
            if ch in palette: px[x,y]=palette[ch]+(255,)
    return im

bug1 = [
"................",
"................",
"..K..........K..",
"...K..KKKK..K...",
"....KKBBBBKK....",
"...KBBBBBBBBK...",
"..KBBWBBBBWBBK..",
"..KBBBBBBBBBBK..",
"..KBBRBBBBRBBK..",
"...KBBBBBBBBK...",
"....KBBBBBBK....",
"...K.KBBBBK.K...",
"..K..KKKKKK..K..",
".K..K..KK..K..K.",
"....K..K..K.....",
"................",
]
bug2 = [
"................",
"................",
"..K..........K..",
"...K..KKKK..K...",
"....KKBBBBKK....",
"...KBBBBBBBBK...",
"..KBBWBBBBWBBK..",
"..KBBBBBBBBBBK..",
"..KBBRBBBBRBBK..",
"...KBBBBBBBBK...",
"....KBBBBBBK....",
"....KBBBBBBK....",
"...KKKKKKKKKK...",
"..K..K....K..K..",
"..K..K....K..K..",
"................",
]
draw_art(bug1).save(p(OUT,'sprites','images','sprEnemy_0.png'))
draw_art(bug2).save(p(OUT,'sprites','images','sprEnemy_1.png'))

# ---------------------------------------------------------------- spark / debris
spark = [
"................",
".......WW.......",
".......WW.......",
"..W....WW....W..",
"...W...WW...W...",
"....WWWWWWWW....",
".....WYYYYW.....",
"..WWWYYWWYYWWW..",
"..WWWYYWWYYWWW..",
".....WYYYYW.....",
"....WWWWWWWW....",
"...W...WW...W...",
"..W....WW....W..",
".......WW.......",
".......WW.......",
"................",
]
draw_art(spark).save(p(OUT,'sprites','images','sprSpark_0.png'))

# ---------------------------------------------------------------- title & misc backgrounds
title = Image.open(p(TMP,'l900.png')).convert('RGB')
title.save(p(OUT,'background','images','bgTitle.png'))
go = Image.open(p(TMP,'b15.png')).convert('RGB')
go.save(p(OUT,'background','images','bgGameOver.png'))
print('basic sprites written')

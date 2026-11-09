#!/usr/bin/env python3
"""Compose the Stage 1 'Kitchen' background from ripped NES tiles and export
the collision/platform data used by the GameMaker room."""
import json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, 'assets_src')
OUT  = os.path.join(ROOT, 'ChipNRangers2.project')
m = Image.open(os.path.join(SRC,'map_raw.png')).convert('RGB')

W, H = 1280, 240
bg = Image.new('RGB',(W,H),(0,0,0))

# ---- wallpaper fill (32x32 repeating pattern, verified period = 32) --------
wall = m.crop((0,96,32,128))
for y in range(0,H,32):
    for x in range(0,W,32):
        bg.paste(wall,(x,y))

# ---- authentic opening screen (ripped 1:1) --------------------------------
bg.paste(m.crop((0,0,256,240)),(0,0))

# ---- pieces from the ripped screen ----------------------------------------
PIECES = {
 'counter_l': (56,156,16,17),
 'counter_m': (96,156,16,17),
 'counter_r': (224,156,16,17),
 'shelf_l'  : (128,84,16,14),
 'shelf_m'  : (144,84,16,14),
 'shelf_r'  : (240,84,16,14),
 'sandwich' : (128,112,48,36),
 'cup'      : (80,128,32,20),
 'cans'     : (192,128,32,24),
 'window'   : (144,0,112,80),
}
P = {k: m.crop((v[0],v[1],v[0]+v[2],v[1]+v[3])) for k,v in PIECES.items()}
for k,v in PIECES.items(): P[k+'_size'] = (v[2],v[3])

platforms = []   # (x, surfaceY, width, kind)
def counter(x, surfaceY, w):
    """16px-tile counter whose walkable surface is at surfaceY"""
    top = surfaceY - 4
    bg.paste(P['counter_l'], (x, top))
    for cx in range(x+16, x+w-16, 16):
        bg.paste(P['counter_m'], (cx, top))
    bg.paste(P['counter_r'], (x+w-16, top))
    platforms.append((x, surfaceY, w, 'counter'))
def shelf(x, y, w):
    bg.paste(P['shelf_l'], (x, y))
    for cx in range(x+16, x+w-16, 16):
        bg.paste(P['shelf_m'], (cx, y))
    bg.paste(P['shelf_r'], (x+w-16, y))
    platforms.append((x, y, w, 'shelf'))
def deco(name, x, y):
    bg.paste(P[name], (x, y))

# ---- extension ------------------------------------------------------------
counter(288,160,144)
counter(464,160,136)
counter(648,160,152)
counter(840,160,160)
counter(1040,160,240)
shelf(504,112,64)
shelf(880,112,64)
shelf(1180,112,64)
# decorations
deco('sandwich', 340,120)
deco('cup', 470,136)
deco('sandwich', 700,120)
deco('cup', 850,136)
deco('sandwich',1110,120)

# ---- platforms from the authentic screen ----------------------------------
platforms.insert(0,(0,184,80,'ledge'))
platforms.insert(1,(64,160,176,'counter'))
platforms.insert(2,(128,84,128,'shelf'))

bg.save(os.path.join(OUT,'background','images','bgStage1.png'))

# ---- object placement -----------------------------------------------------
crates = [(300,144),(400,144),(520,144),(560,144),(660,144),(780,144),
          (900,144),(950,144),(1060,144),(1220,144)]
enemies = [(370,144,288,432),(510,144,464,600),(730,144,648,800),
           (970,144,840,1000),(1140,144,1040,1280)]
hearts  = [(580,152),(975,152)]

level = {
  'width': W, 'height': H,
  'platforms': [{'x':x,'y':y,'w':w,'kind':k} for (x,y,w,k) in platforms],
  'crates': [{'x':x,'y':y} for x,y in crates],
  'enemies': [{'x':x,'y':y,'left':l,'right':r} for x,y,l,r in enemies],
  'hearts': [{'x':x,'y':y} for x,y in hearts],
  'playerStart': {'x':24,'y':184},
  'goalX': 1240,
}
json.dump(level, open(os.path.join(SRC,'level1.json'),'w'), indent=1)
print('level background', bg.size, 'platforms', len(platforms))

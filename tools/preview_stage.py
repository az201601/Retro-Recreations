#!/usr/bin/env python3
"""Compose preview screenshots of the remake (same layout the GMS room uses)."""
import os, json
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT,'ChipNRangers2.project')
S = os.path.join(P,'sprites','images')
BG = Image.open(os.path.join(P,'background','images','bgStage1.png')).convert('RGBA')
L = json.load(open(os.path.join(ROOT,'assets_src','level1.json')))
os.makedirs(os.path.join(ROOT,'docs'), exist_ok=True)

def spr(name, frame=0):
    return Image.open(os.path.join(S, f'{name}_{frame}.png')).convert('RGBA')

def compose(camx):
    canvas = BG.crop((camx,0,camx+256,240)).copy()
    def blit(im, x, y, ox, oy):
        canvas.alpha_composite(im, (int(x-ox-camx), int(y-oy)))
    for c in L['crates']:
        blit(spr('sprCrate'), c['x'], c['y'], 0, 0)
    for e in L['enemies']:
        blit(spr('sprEnemy'), e['x'], e['y'], 0, 0)
    for h in L['hearts']:
        blit(spr('sprHeart'), h['x'], h['y'], 0, 0)
    if camx < 80:
        blit(spr('sprPlayerIdle', 0), L['playerStart']['x'], L['playerStart']['y'], 16, 26)
    for i in range(3):
        canvas.alpha_composite(spr('sprHeart'), (6+i*10, 214))
    return canvas.convert('RGB')

for i, cam in enumerate([0, 256, 512, 768, 1024]):
    im = compose(cam)
    im.resize((768,720), Image.NEAREST).save(os.path.join(ROOT,'docs',f'preview_stage1_{i+1}.png'))
print('previews written')

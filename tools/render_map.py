import json
from PIL import Image
d = json.load(open('assets_src/map_raw.json'))
W,H = d['cols'], d['rows']
img = Image.new('RGB',(W*8,H*8),(255,0,255))
px = img.load()
tiles = d['tiles']
for k, tid in d['map'].items():
    cx, cy = map(int, k.split(','))
    t = tiles[tid]['px']
    for y in range(8):
        for x in range(8):
            c = t[y*8+x]
            r = (c>>16)&255; g=(c>>8)&255; b=c&255
            px[cx*8+x, cy*8+y] = (r,g,b)
img.save('assets_src/map_raw.png')
print(img.size)

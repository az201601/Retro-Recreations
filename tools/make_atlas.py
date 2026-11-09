import json, sys
from PIL import Image, ImageDraw
data = json.load(open('assets_src/tiles_raw.json'))
data.sort(key=lambda t: -t['count'])
data = [t for t in data if t['count'] >= 6]
print('kept', len(data))
cols = 16
tile = 8
scale = 3
pad = 1
cell = tile*scale + pad*2
rows = (len(data)+cols-1)//cols
img = Image.new('RGB', (cols*cell, rows*cell), (255,0,255))
d = ImageDraw.Draw(img)
for i,t in enumerate(data):
    cx = (i%cols)*cell+pad; cy=(i//cols)*cell+pad
    for y in range(8):
        for x in range(8):
            c = t['px'][y*8+x]
            for sy in range(scale):
                for sx in range(scale):
                    img.putpixel((cx+x*scale+sx, cy+y*scale+sy), ((c>>16)&255,(c>>8)&255,c&255))
    d.text((cx, cy+24), str(i), fill=(0,0,0))
img.save('assets_src/tiles_atlas.png')
json.dump(data, open('assets_src/tiles_filtered.json','w'))
print(img.size)

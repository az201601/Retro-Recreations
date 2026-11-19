"""python pack.py RAW_DIR ; requires Pillow. IDs are zero based."""
import csv, hashlib, sys
from pathlib import Path
from PIL import Image
root = Path(__file__).resolve().parents[1]
raw = Path(sys.argv[1]); ids = {}; images = []; timeline = []; rows = []
for i in range(157, 1151):
    data = (raw / f'f{i}').read_bytes(); digest = hashlib.sha256(data).hexdigest()
    if digest not in ids:
        ids[digest] = len(images); images.append(Image.frombytes('RGB',(256,240),data))
    n = ids[digest]; timeline.append(n); box = images[n].getbbox()
    rows.append([i,i-213,n,* (box or ('',)*4),digest])
for page in range((len(images)+15)//16):
    sheet = Image.new('RGB',(1024,960)); file = root/'data'/f'spot_{page}.png'
    for k,im in enumerate(images[page*16:page*16+16]): sheet.paste(im,(256*(k%4),240*(k//4)))
    sheet.save(file)
# Verify the shipping PNGs and timeline against every source frame, including repeats.
index = root/'data'/'spot_frames.txt'; index.write_text('\n'.join(map(str,timeline))+'\n')
pages = [Image.open(root/'data'/f'spot_{p}.png').convert('RGB') for p in range(page+1)]
for i,line in enumerate(index.read_text().splitlines(),157):
    n=int(line); x=n%4*256; y=n%16//4*240
    assert pages[n//16].crop((x,y,x+256,y+240)).tobytes()==(raw/f'f{i}').read_bytes()
with (root/'frames.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow('jsnes_frame F tile left top right_exclusive bottom_exclusive rgb_sha256'.split()); w.writerows(rows)
print(len(images),'unique images;',page+1,'pages;',len(rows),'verified frames')

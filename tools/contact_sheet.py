#!/usr/bin/env python3
"""contact_sheet.py -- tile a folder of PNG frames into one labeled grid."""
import os
import sys
import glob
from PIL import Image, ImageDraw

def main():
    folder = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(folder, "_sheet.png")
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    files = sorted(glob.glob(os.path.join(folder, "*.png")))
    files = [f for f in files if "_sheet" not in f and "_2x" not in f]
    if not files:
        print("no frames"); return
    w, h = 256, 240
    scale = 0.75
    tw, th = int(w * scale), int(h * scale)
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 14)), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB").resize((tw, th), Image.NEAREST)
        x, y = (i % cols) * tw, (i // cols) * (th + 14)
        sheet.paste(im, (x, y + 14))
        name = os.path.basename(f).replace(".png", "").replace("f00", "").replace("final_", "")
        d.text((x + 3, y + 2), name, fill=(255, 255, 0))
    sheet.save(out)
    print(out, sheet.size, len(files), "frames")

if __name__ == "__main__":
    main()

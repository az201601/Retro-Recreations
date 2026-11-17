"""Derive walkable ledges from an exported level screen.

There is no collision data in the ROM that can be read out directly, but the
stage art is drawn with a hard 1 px black outline over every solid surface, so
the platform tops can be recovered exactly from the pixels:

  * body colours are the fill colours of shelves / tables / stools,
  * a platform top is the first body pixel that has a black outline above it,
  * a run of such pixels at least 16 px wide is a ledge.

Output: assets_vec/backgrounds/<level>/collision.json

    {"platforms": [{"x": 0, "y": 192, "w": 79, "h": 16}, ...]}

``y`` is the stand-on line (the top of the outline), ``h`` how thick the
surface is; h = -1 means "as deep as the screen".
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

LEVEL = "level01"
DIR = os.path.join(ROOT, "assets_vec", "backgrounds", LEVEL)

BLACK = (0, 0, 0)
# fill colours of the standable surfaces (orange, white, light blue, cyan,
# melon highlight)
BODY = [(248, 56, 0), (248, 248, 248), (164, 228, 252),
        (0, 232, 216), (248, 120, 88), (252, 252, 252)]

MIN_WIDTH = 40   # decoration (mug, shaker, burger parts) is narrower


def mask_of(img, colours):
    m = np.zeros(img.shape[:2], bool)
    for c in colours:
        m |= (np.abs(img - np.array(c)).sum(axis=2) == 0)
    return m


def main():
    info = json.load(open(os.path.join(DIR, "info.json")))
    img = np.array(Image.open(os.path.join(DIR, "screen_00.png")).convert("RGB")
                   ).astype(int)
    h, w = img.shape[:2]
    body = mask_of(img, BODY)
    black = mask_of(img, [BLACK])

    top = np.zeros_like(body)
    top[1:] = body[1:] & black[:-1]

    platforms = []
    for y in range(h):
        x = 0
        while x < w:
            if not top[y, x]:
                x += 1
                continue
            x0 = x
            while x < w and top[y, x]:
                x += 1
            run = x - x0
            if run < MIN_WIDTH:
                continue
            # skip thin decoration (outlines / stripes) - a real surface is
            # at least 4 px of continuous body below its top
            thick = 0
            for d in range(0, 8):
                if y + d < h and body[y + d, x0:x].mean() > 0.6:
                    thick += 1
            if thick < 4:
                continue
            platforms.append(dict(x=int(x0), y=int(y - 1), w=int(run), h=-1))

    # a table interrupted by the mug / burger / shaker on it still counts as
    # one ledge: merge neighbours on the same stand line
    platforms.sort(key=lambda p: (p["y"], p["x"]))
    merged = []
    for p in platforms:
        for q in merged:
            if q["y"] == p["y"] and p["x"] <= q["x"] + q["w"] + 32 \
                    and q["x"] <= p["x"] + p["w"] + 32:
                nx0 = min(q["x"], p["x"])
                nx1 = max(q["x"] + q["w"], p["x"] + p["w"])
                q["x"], q["w"] = nx0, nx1 - nx0
                break
        else:
            merged.append(dict(p))

    # drop props standing on a table: a ledge whose x range is inside a lower
    # ledge within 40 px is decoration (mug, salt shaker, burger slices)
    curated = []
    for p in merged:
        prop = False
        for q in merged:
            if q is p or q["y"] <= p["y"] or q["y"] - p["y"] > 40:
                continue
            if p["x"] >= q["x"] - 8 and p["x"] + p["w"] <= q["x"] + q["w"] + 8:
                prop = True
                break
        if not prop:
            curated.append(p)
    merged = curated

    # room bounds: the floor stops at the bottom of the screen
    out = dict(level=LEVEL, screen=info.get("screen_size", [w, h]),
               death_y=int(h), platforms=merged)
    path = os.path.join(DIR, "collision.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print("platforms:", len(merged))
    for p in merged:
        print("  x=%3d y=%3d w=%3d" % (p["x"], p["y"], p["w"]))
    print("wrote", path)


if __name__ == "__main__":
    main()

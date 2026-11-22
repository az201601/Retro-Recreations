#!/usr/bin/env python3
"""
extract_poses.py -- compose full character/prop POSES from multi-sprite OAM groups.

Player poses = all sprites with CHR tile < 0x20, composed relative to feet anchor.
Misc objects (boxes, enemies, HUD) = remaining sprites, composed per object cluster.

Dedupes by pixel content. Outputs:
    assets/sprites/pose_chip_XX.png   (32x32-ish, feet-anchored, RGBA)
    assets/sprites/obj_XX.png         (object clusters)
    poses_meta.json                   (sizes, frame counts)

    .venv/bin/python tools/extract_poses.py --state work/ss/frozen.state \
        --timeline "10:start 40: 100:right ..." --out assets/sprites
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nes_harness import NesEmu  # noqa: E402
from nest_state import parse_state, ppu_dump  # noqa: E402
from run_script import parse_timeline, CORE, ROM  # noqa: E402
from extract_sprites import decode_sprite_tile, MASTER, load_chr_rom  # noqa: E402


def render_sprite(chr_rom, tile, attr, pal):
    """8x16 sprite -> (16,8,4) RGBA array."""
    pal_i = attr & 3
    fh = bool(attr & 0x40)
    fv = bool(attr & 0x80)
    top_table = 0x1000 if (tile & 1) else 0x0000
    top = tile & 0xFE
    img = np.zeros((16, 8, 4), dtype=np.uint8)
    for row, t in [(0, top), (8, top + 1)]:
        px8 = decode_sprite_tile(chr_rom, top_table, t, fh, fv)
        for yy in range(8):
            for xx in range(8):
                idx = px8[yy, xx]
                if idx:
                    c = MASTER[pal[16 + pal_i*4 + idx]]
                    img[row+yy, xx, :3] = c
                    img[row+yy, xx, 3] = 255
    return img


def compose(sprites):
    """sprites: list of (x, y, rgba16x8). Compose on canvas, return trimmed RGBA + bbox."""
    xs = [s[0] for s in sprites]
    ys = [s[1] for s in sprites]
    x0, y0 = min(xs), min(ys)
    x1 = max(s[0] + 8 for s in sprites)
    y1 = max(s[1] + 16 for s in sprites)
    canvas = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.uint8)
    for x, y, img in sprites:
        for yy in range(16):
            for xx in range(8):
                if img[yy, xx, 3]:
                    canvas[y - y0 + yy, x - x0 + xx] = img[yy, xx]
    return canvas, (x0, y0, x1 - x0, y1 - y0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=None)
    ap.add_argument("--timeline", default="1200:")
    ap.add_argument("--out", default="assets/sprites")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    chr_rom = load_chr_rom(ROM)
    emu = NesEmu(CORE).load(ROM)
    if args.state:
        emu.loadstate(open(args.state, "rb").read())

    poses = {}    # hash -> {img, count, bbox}
    objs = {}
    for frames, btns in parse_timeline(args.timeline):
        emu.set_buttons(*btns) if btns else emu.release_all()
        for _ in range(frames):
            emu.run(1)
            p = parse_state(emu.savestate())
            pd = ppu_dump(p)
            pal = np.frombuffer(pd["palette"][:32], dtype=np.uint8) & 0x3F
            oam = pd["oam"][:256]
            player, misc = [], []
            for i in range(64):
                y, tile, attr, x = oam[i*4:i*4+4]
                if y >= 230:
                    continue
                img = render_sprite(chr_rom, tile, attr, pal)
                (player if tile < 0x20 else misc).append((x, y, img))
            if player:
                canvas, bbox = compose(player)
                h = hashlib.md5(canvas.tobytes()).hexdigest()[:10]
                if h not in poses:
                    poses[h] = {"img": canvas, "bbox": bbox, "count": 0}
                poses[h]["count"] += 1
            # misc: cluster by x proximity (each object ~ 8-24px wide)
            misc.sort(key=lambda s: s[0])
            cluster = []
            for s in misc:
                if cluster and s[0] - cluster[-1][0] > 24:
                    canvas, bbox = compose(cluster)
                    h = hashlib.md5(canvas.tobytes()).hexdigest()[:10]
                    if h not in objs:
                        objs[h] = {"img": canvas, "bbox": bbox, "count": 0}
                    objs[h]["count"] += 1
                    cluster = []
                cluster.append(s)
            if cluster:
                canvas, bbox = compose(cluster)
                h = hashlib.md5(canvas.tobytes()).hexdigest()[:10]
                if h not in objs:
                    objs[h] = {"img": canvas, "bbox": bbox, "count": 0}
                objs[h]["count"] += 1

    meta = {"chip_poses": [], "objects": []}
    for i, (h, d) in enumerate(sorted(poses.items(), key=lambda kv: -kv[1]["count"])):
        fn = f"pose_chip_{i:02d}.png"
        Image.fromarray(d["img"]).save(os.path.join(args.out, fn))
        meta["chip_poses"].append({"file": fn, "bbox": d["bbox"], "frames_seen": d["count"]})
    for i, (h, d) in enumerate(sorted(objs.items(), key=lambda kv: -kv[1]["count"])):
        fn = f"obj_{i:02d}.png"
        Image.fromarray(d["img"]).save(os.path.join(args.out, fn))
        meta["objects"].append({"file": fn, "bbox": d["bbox"], "frames_seen": d["count"]})
    with open(os.path.join(args.out, "poses_meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(f"poses: {len(poses)} chip + {len(objs)} objects -> {args.out}/")


if __name__ == "__main__":
    main()

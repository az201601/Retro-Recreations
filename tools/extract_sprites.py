#!/usr/bin/env python3
"""
extract_sprites.py -- extract unique sprites (with transparency + NES palette colors)
from live gameplay, keyed by (CHR tile, palette, flips).

Runs a scripted input timeline from a savestate; every frame it reads OAM, decodes
each visible 8x16 sprite from CHR, colors it via the in-game palette RAM, and
dedupes into assets/sprites/. Also writes sprites_meta.json.

    .venv/bin/python tools/extract_sprites.py --state work/ss/frozen.state \
        --timeline "10:start 40: 120:right 20:right+a 80: 60:left" \
        --out assets/sprites
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
from nest_state import parse_state, cpu_ram, ppu_dump  # noqa: E402
from run_script import parse_timeline, CORE, ROM  # noqa: E402


def load_chr_rom(rom_path):
    rom = open(rom_path, "rb").read()
    chr_rom = rom[16 + 8 * 16384:]
    assert len(chr_rom) == 128 * 1024, len(chr_rom)
    return chr_rom

MASTER = [  # NES master palette (RGB), index = 0x00-0x3F
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136), (68, 0, 100), (92, 0, 48),
    (84, 4, 0), (60, 24, 0), (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0),
    (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228), (136, 20, 176),
    (160, 20, 100), (152, 34, 32), (120, 60, 0), (84, 90, 0), (40, 114, 0),
    (8, 124, 0), (0, 118, 40), (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236), (228, 84, 236),
    (236, 88, 180), (236, 106, 100), (212, 136, 32), (160, 170, 0), (116, 196, 0),
    (76, 208, 32), (56, 204, 108), (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236), (236, 174, 236),
    (236, 174, 212), (236, 180, 176), (228, 196, 144), (204, 210, 120), (180, 222, 120),
    (168, 226, 144), (152, 226, 180), (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0),
]


def decode_sprite_tile(chr_rom, table_base, tile, flip_h, flip_v):
    """Decode one 8x8 tile -> (8,8) palette indices 0-3."""
    off = table_base + tile * 16
    px = np.zeros((8, 8), dtype=np.uint8)
    for y in range(8):
        b0, b1 = chr_rom[off + y], chr_rom[off + 8 + y]
        for x in range(8):
            bit = 7 - x
            px[y, x] = ((b0 >> bit) & 1) | (((b1 >> bit) & 1) << 1)
    if flip_h:
        px = px[:, ::-1]
    if flip_v:
        px = px[::-1, :]
    return px


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

    seen = {}   # key -> dict
    order = []
    for frames, btns in parse_timeline(args.timeline):
        emu.set_buttons(*btns) if btns else emu.release_all()
        for _ in range(frames):
            emu.run(1)
            p = parse_state(emu.savestate())
            pd = ppu_dump(p)
            pal = np.frombuffer(pd["palette"][:32], dtype=np.uint8) & 0x3F
            oam = pd["oam"][:256]
            for i in range(64):
                y, tile, attr, x = oam[i*4:i*4+4]
                if y >= 230:
                    continue
                pal_i = attr & 3
                fh = bool(attr & 0x40)
                fv = bool(attr & 0x80)
                if tile in seen and (pal_i, fh, fv) in seen[tile]["variants"]:
                    continue
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
                key = f"{tile:02x}_{pal_i}{int(fh)}{int(fv)}"
                if tile not in seen:
                    seen[tile] = {"variants": {}, "tile": tile}
                seen[tile]["variants"][(pal_i, fh, fv)] = key
                Image.fromarray(img).save(os.path.join(args.out, f"spr_{key}.png"))
                order.append(key)
    meta = [{"file": f"spr_{k}.png"} for k in order]
    with open(os.path.join(args.out, "sprites_meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(f"extracted {len(order)} sprite variants -> {args.out}/")


if __name__ == "__main__":
    main()

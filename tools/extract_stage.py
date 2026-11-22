#!/usr/bin/env python3
"""
extract_stage.py -- render the full stage (2 nametables = 512x240) from a savestate,
using the verified nes_render decoding, plus tile-index/attribute/palette JSON/CSV
for GMS tilemap import.

    .venv/bin/python tools/extract_stage.py --state work/ss/frozen.state --out assets/stage1
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nes_render import StateView as State, load_rom, master_palette  # noqa: E402


def colorize(st: State, master, ntx):
    tiles, pals = st.nt_grids(0, 0, ntx, 0)
    bank = st.pattern_tiles(st.bg_pattern)
    px = bank[tiles]
    img_idx = px.transpose(0, 2, 1, 3).reshape(240, 256)
    pal_idx = np.repeat(np.repeat(pals, 8, 0), 8, 1)
    color_idx = st.palette[pal_idx * 4 + img_idx] & 0x3F
    return master[color_idx], tiles, pals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="work/ss/frozen.state")
    ap.add_argument("--out", default="assets/stage1")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    _prg, chr_rom = load_rom()
    master = master_palette()
    st = State(open(args.state, "rb").read(), chr_rom)

    img0, t0, p0 = colorize(st, master, 0)
    img1, t1, p1 = colorize(st, master, 1)
    full = np.concatenate([img0, img1], axis=1).astype(np.uint8)
    Image.fromarray(full).save(os.path.join(args.out, "stage_full.png"))

    tiles = np.concatenate([t0, t1], axis=1)
    pals = np.concatenate([p0, p1], axis=1)
    with open(os.path.join(args.out, "tilemap.json"), "w") as f:
        json.dump({
            "w": 64, "h": 30,
            "tiles": tiles.tolist(),
            "attrs": pals.tolist(),
            "palette": [int(v) for v in st.palette[:16]],
            "bg_pattern_table": int(st.bg_pattern),
            "note": "tiles index CHR ROM (assets/tiles/chr_bank_XX.png, 256 tiles/4KB bank)",
        }, f)
    with open(os.path.join(args.out, "tilemap.csv"), "w") as f:
        for row in tiles.tolist():
            f.write(",".join(str(v) for v in row) + "\n")
    print(f"stage rendered: 512x240 -> {args.out}/stage_full.png (bg_pattern={st.bg_pattern:#x})")


if __name__ == "__main__":
    main()

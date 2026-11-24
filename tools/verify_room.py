#!/usr/bin/env python3
"""Re-assemble an extracted room from its handoff files and compare it to the
reference render.

This is the guarantee that the GMS side can rebuild exactly what the NES drew
from ``tileset.png`` + ``tilemap.csv`` + the palette's backdrop colour.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("room", help="directory produced by extract_room.py")
    args = ap.parse_args()
    room = Path(args.room)

    palette = {}
    with (room / "palette.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            palette[row["nes_index"]] = (int(row["r"]), int(row["g"]), int(row["b"]))
    import json
    meta = json.loads((room / "room.json").read_text(encoding="utf-8"))
    backdrop = tuple(meta["backdrop_rgb"])
    ppumask = int(meta["ppumask"], 16)
    left_clipped = not (ppumask & 0x02)  # background hidden in the first 8 pixels

    tileset = Image.open(room / "tileset.png").convert("RGB")
    with (room / "tilemap.csv").open(encoding="utf-8") as f:
        rows = [[int(v) for v in row] for row in list(csv.reader(f))[1:]]

    rebuilt = Image.new("RGB", (256, 240), backdrop)
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell < 0:
                continue
            cx, cy = (cell % 16) * 8, (cell // 16) * 8
            rebuilt.paste(tileset.crop((cx, cy, cx + 8, cy + 8)), (x * 8, y * 8))

    reference = Image.open(room / "page.png").convert("RGB")
    start_x = 0  # page.png is camera-independent, so no hardware left clipping
    diffs = [(x, y) for y in range(240) for x in range(start_x, 256)
             if rebuilt.getpixel((x, y)) != reference.getpixel((x, y))]
    print(f"{room}: {len(diffs)} differing pixel(s) between tileset+tilemap and page.png")
    if diffs:
        print("  first differences:", diffs[:8])
        raise SystemExit(1)
    _ = left_clipped


if __name__ == "__main__":
    main()

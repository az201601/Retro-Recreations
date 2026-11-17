"""Level (background) export for the GameMaker port.

The NES never stores a "level image": it streams 8x8 tiles into a small VRAM
ring.  Everything here is therefore rebuilt straight from VRAM, which is exact
and free of sprites:

  render_canvas(vram)      the whole 512x480 scroll canvas (4 name tables)
  render_bg(vram, scroll)  one 256x240 screen at a given scroll position

Output (assets_vec/backgrounds/<level>/):
  screen_00.png     clean 256x240 screen, no sprites, NES colours
  tileset.png       16x16 metatiles used by the screen (transparent = empty)
  canvas.png        full 512x480 scroll canvas (reference / authoring aid)
  tileset_8x8.png   the raw 8x8 tiles, 16 per row (for GMS tile sets)
  info.json         palette, CHR windows, scroll, metatile map
"""
import json
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import trace as tracemod  # noqa: E402
from nesrom import NesRom  # noqa: E402
from rr2 import sprites as S, bg as BG  # noqa: E402

ROM = NesRom()

# (trace, frame, output name) - frame chosen because it is the first stable
# gameplay frame of the stage (see tools/RECON.md).
SOURCE = ("level", 5604, "level01")
TRACE = os.path.join(ROOT, "out", "level", "trace.bin")


def metatile_sheet(vram, palette, chr_win, bg_page, cols=16):
    """16x16 metatiles for the visible screen + the 15x16 index map."""
    tiles, attrs = BG.name_table(vram, 0)
    index, order, m = {}, [], np.zeros((15, 16), np.uint16)
    for qy in range(15):
        for qx in range(16):
            ids = tuple(int(tiles[qy * 2 + dy, qx * 2 + dx])
                        for dy in range(2) for dx in range(2))
            pal = int(attrs[qy * 2, qx * 2])
            key = (pal, ids)
            if key not in index:
                index[key] = len(order)
                order.append(key)
            m[qy, qx] = index[key]

    rows = (len(order) + cols - 1) // cols
    sheet = np.zeros((max(rows, 1) * 16, cols * 16, 4), np.uint8)
    for i, (pal_idx, ids) in enumerate(order):
        ox, oy = (i % cols) * 16, (i // cols) * 16
        for k, tid in enumerate(ids):
            dx, dy = (k % 2) * 8, (k // 2) * 8
            pix = S.tile_pixels(
                chr_win.read(int(bg_page) * 0x1000 + tid * 16, 16), 0)
            p = palette[pal_idx * 4:pal_idx * 4 + 4]
            blk = np.zeros((8, 8, 4), np.uint8)
            for c in range(4):
                mm = pix == c
                col = S.color(p[c])
                blk[mm, 0], blk[mm, 1], blk[mm, 2] = col
                blk[mm, 3] = 255
            sheet[oy + dy:oy + dy + 8, ox + dx:ox + dx + 8] = blk
    return sheet, m, order


def tile_sheet_8x8(vram, palette, chr_win, bg_page, cols=16):
    """Every 8x8 tile that appears on the screen, one per cell, 16 px grid."""
    tiles, attrs = BG.name_table(vram, 0)
    used = {}
    for y in range(30):
        for x in range(32):
            t, a = int(tiles[y, x]), int(attrs[y, x])
            used.setdefault((a, t), None)
    keys = sorted(used)
    rows = (len(keys) + cols - 1) // cols
    sheet = np.zeros((max(rows, 1) * 8, cols * 8, 4), np.uint8)
    for i, (a, t) in enumerate(keys):
        ox, oy = (i % cols) * 8, (i // cols) * 8
        pix = S.tile_pixels(chr_win.read(int(bg_page) * 0x1000 + t * 16, 16), 0)
        p = palette[a * 4:a * 4 + 4]
        blk = np.zeros((8, 8, 4), np.uint8)
        for c in range(4):
            mm = pix == c
            col = S.color(p[c])
            blk[mm, 0], blk[mm, 1], blk[mm, 2] = col
            blk[mm, 3] = 255
        sheet[oy:oy + 8, ox:ox + 8] = blk
    return sheet, keys


def main():
    trace_name, frame, level = SOURCE
    out = os.path.join(ROOT, "assets_vec", "backgrounds", level)
    os.makedirs(out, exist_ok=True)

    recs = {r.frame: r for r in tracemod.load(TRACE)}
    rec = recs[frame]

    chr_win = S.ChrWindows(ROM.chr, rec.chr_lo, rec.chr_hi, rec.chr_mode)

    # The PPU "v" register captured at the end of a frame holds whatever the
    # game last wrote (mid-frame splits included), so it is NOT the scroll of
    # the finished picture.  Locate the real screen inside the full canvas by
    # matching it against the frame the emulator rendered.
    canvas = BG.render_canvas(rec.vram, rec.palette, chr_win, rec.bg_page)
    ppm = os.path.join(ROOT, "out", "level", "frames", "f%05d.ppm" % frame)
    if os.path.exists(ppm):
        real = np.array(Image.open(ppm).convert("RGB"))
        sy, sx, _ = BG.find_offset(canvas, real, step=8)
    else:
        sy = sx = 0
    nt = 0

    # ---- clean screen (this is what the player actually sees) -------------
    screen = BG.render_bg(rec.vram, rec.palette, chr_win, nt, rec.bg_page,
                          scroll_x=sx, scroll_y=sy)
    # On the NES a background pixel with colour index 0 shows the backdrop
    # colour (palette entry 0), it is not transparent.  render_bg leaves those
    # pixels at alpha 0 so that tiles can be cut out, so flatten the screen
    # here - a level backdrop must be fully opaque.
    backdrop = S.color(rec.palette[0])
    hole = screen[:, :, 3] == 0
    for c in range(3):
        screen[hole, c] = backdrop[c]
    # The NES hides the leftmost 8 pixels (PPUMASK "show background in the left
    # 8 pixels" is off for this game), so they show the backdrop colour only.
    screen[:, 0:8, :3] = backdrop
    screen[:, :, 3] = 255
    Image.fromarray(screen).save(os.path.join(out, "screen_00.png"))

    # ---- whole scroll canvas ---------------------------------------------
    Image.fromarray(canvas).save(os.path.join(out, "canvas.png"))

    # ---- tilesets ---------------------------------------------------------
    meta, m, order = metatile_sheet(rec.vram, rec.palette, chr_win, rec.bg_page)
    Image.fromarray(meta).save(os.path.join(out, "tileset.png"))
    tiles8, keys8 = tile_sheet_8x8(rec.vram, rec.palette, chr_win, rec.bg_page)
    Image.fromarray(tiles8).save(os.path.join(out, "tileset_8x8.png"))

    info = dict(
        level=level,
        source=dict(trace=trace_name, frame=frame),
        screen_size=[256, 240],
        scroll=[sx, sy],
        name_table=nt,
        chr=dict(lo=rec.chr_lo, hi=rec.chr_hi, mode=rec.chr_mode,
                 bg_page=rec.bg_page),
        palette=[int(b) for b in rec.palette[:16]],
        palette_rgb=[[int(c) for c in S.color(rec.palette[i])] for i in range(16)],
        tile_size=16,
        tileset_columns=16,
        tileset_count=len(order),
        tiles_8x8=[list(k) for k in keys8],
        map=[[int(x) for x in row] for row in m],
    )
    with open(os.path.join(out, "info.json"), "w") as f:
        json.dump(info, f, indent=1)

    print("level %s: frame %d, scroll (%d,%d), %d metatiles, %d 8x8 tiles"
          % (level, frame, sx, sy, len(order), len(keys8)))
    print("wrote", out)


if __name__ == "__main__":
    main()

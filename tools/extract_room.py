#!/usr/bin/env python3
"""Extract one NES room/screen into GMS-ready layers.

Given a FCEUmm savestate captured at a stable screen, this writes:

  room.png        full composite exactly as the emulator showed it
  background.png  background layer only, exactly as scrolled on screen
  page.png        the underlying nametable page with no scroll (tilemap basis)
  sprites.png     sprite layer only, transparent where no sprite pixel
  tileset.png     every unique background tile, rendered in NES colours
  tiles.csv       tileset cell -> NES tile id, palette, pixel counts
  tilemap.csv     30 rows x 32 columns of tileset cell indices (-1 = empty)
  palette.csv     NES colour index -> RGB, palette slot and usage
  room.json       banks, mirroring, scroll, object list, checksums

Colours are learned from the matching emulator frame, so the PNGs use the
exact RGB values the core produced rather than an approximated palette.
Collision is intentionally *not* guessed here: tile art and collision are
different concerns, and solidity is assigned later per tileset.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image

from nes_state import (SCREEN_H, SCREEN_W, load_state)

BG_COLS, BG_ROWS = 32, 30


def learn_palette(state, frame_path: str | None) -> tuple[dict[int, tuple[int, int, int]], dict]:
    """Map NES colour indices to RGB using a frame captured at the same frame.

    Falls back to FCEUmm's classic palette for indices the frame never showed.
    Also reports any index that produced more than one RGB value, which means
    the render did not match the frame and the caller should not trust it.
    """
    from nes_state import FCEUMM_CLASSIC_PALETTE
    palette = {i: FCEUMM_CLASSIC_PALETTE[i] for i in range(64)}
    report = {"source": "fallback", "indices": 0, "conflicts": {}}
    if not frame_path:
        return palette, report
    res = state.compare_with_ppm(frame_path)
    for idx, values in res["index_to_rgb"].items():
        palette[idx] = values[0]
        if len(values) > 1:
            report["conflicts"][idx] = [list(v) for v in values]
    report["source"] = "emulator frame"
    report["indices"] = len(res["index_to_rgb"])
    return palette, report


def collect_bg_tiles(state, palette):
    """Return (tilemap, tiles, usage) for the visible background page.

    ``tiles`` is keyed by (nes_tile_id, palette_index) because the same CHR
    tile can legitimately appear in two different palettes.
    """
    ctrl = state.ppuctrl
    bg_slot = 1 if (ctrl & 0x10) else 0
    base_nt = ctrl & 3
    nt = state.nametable(base_nt)
    tilemap: list[list[int]] = []
    usage: Counter = Counter()
    for row in range(BG_ROWS):
        line = []
        for col in range(BG_COLS):
            tile = nt[row * 32 + col]
            attr = nt[0x3C0 + (row // 4) * 8 + (col // 4)]
            shift = ((row % 4) // 2) * 4 + ((col % 4) // 2) * 2
            pal = (attr >> shift) & 3
            pixels = state.tile_pixels(bg_slot, tile)
            blank = all(all(p == 0 for p in line_) for line_ in pixels)
            if blank:
                line.append(-1)
                continue
            key = (tile, pal)
            line.append(key)
            usage[key] += 1
        tilemap.append(line)
    return tilemap, usage


def build_tileset(state, usage, palette):
    """Render unique tiles into a sheet and return the index mapping."""
    ctrl = state.ppuctrl
    bg_slot = 1 if (ctrl & 0x10) else 0
    keys = sorted(usage, key=lambda k: (-usage[k], k))
    cell_w = 8
    cols = 16
    rows = max(1, (len(keys) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_w), (0, 0, 0))
    px = sheet.load()
    mapping = []
    for cell, (tile, pal) in enumerate(keys):
        cx, cy = (cell % cols) * 8, (cell // cols) * 8
        pixels = state.tile_pixels(bg_slot, tile)
        colours = 0
        for y in range(8):
            for x in range(8):
                v = pixels[y][x]
                if v == 0:
                    px[cx + x, cy + y] = palette[state.pram[0] & 0x3F]
                else:
                    px[cx + x, cy + y] = palette[state.pram[pal * 4 + v] & 0x3F]
                    colours += 1
        mapping.append({
            "cell": cell,
            "cell_x": cell % cols,
            "cell_y": cell // cols,
            "nes_tile": tile,
            "palette": pal,
            "count": usage[(tile, pal)],
            "opaque_pixels": colours,
        })
    lookup = {k: m["cell"] for k, m in zip(keys, mapping)}
    return sheet, mapping, lookup


def write_outputs(args) -> dict:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    state = load_state(args.state, args.rom)
    palette, pal_report = learn_palette(state, args.frame)
    full_palette = [palette[i] for i in range(64)]
    backdrop = palette[state.pram[0] & 0x3F]

    # Composite and background-only renders.
    composite = Image.new("RGB", (SCREEN_W, SCREEN_H))
    composite.putdata(state.render_rgb(full_palette, backdrop))
    background = Image.new("RGB", (SCREEN_W, SCREEN_H))
    background.putdata(state.render_rgb(full_palette, backdrop, sprites=False))
    # Camera-independent page view; matches tilemap.csv exactly.
    page_image = Image.new("RGB", (SCREEN_W, SCREEN_H))
    page_image.putdata(state.render_page_rgb(full_palette))

    # Sprite-only layer with transparency.
    mask = state.sprite_mask()
    sprites = Image.new("RGBA", (SCREEN_W, SCREEN_H), (0, 0, 0, 0))
    spx = sprites.load()
    for y in range(SCREEN_H):
        for x in range(SCREEN_W):
            if mask[y][x]:
                spx[x, y] = (*composite.getpixel((x, y)), 255)

    tilemap, usage = collect_bg_tiles(state, palette)
    sheet, mapping, lookup = build_tileset(state, usage, palette)

    # Tilemap as tileset cell indices.
    cellmap = [[(-1 if key == -1 else lookup[key]) for key in row] for row in tilemap]

    composite.save(out / "room.png", optimize=True)
    background.save(out / "background.png", optimize=True)
    page_image.save(out / "page.png", optimize=True)
    sprites.save(out / "sprites.png", optimize=True)
    sheet.save(out / "tileset.png", optimize=True)

    with (out / "tilemap.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow([f"col{ i }" for i in range(BG_COLS)])
        for row in cellmap:
            w.writerow(row)

    with (out / "tiles.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(mapping[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(mapping)

    # Palette table: every NES entry used by this screen, with slot owners.
    owners: dict[int, list[str]] = {}
    for slot in range(16):
        idx = state.pram[slot] & 0x3F
        owners.setdefault(idx, []).append(f"bg{slot}" if slot < 16 else f"sp{slot}")
    with (out / "palette.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["nes_index", "r", "g", "b", "pram_slots"])
        for idx in range(64):
            r, g, b = palette[idx]
            w.writerow([f"0x{idx:02X}", r, g, b, " ".join(owners.get(idx, []))])

    sprites_list = []
    oam = state.oam
    for i in range(64):
        y, tile, attr, x = oam[i * 4:i * 4 + 4]
        if y >= 240:
            continue
        sprites_list.append({"slot": i, "x": x, "y": y, "tile": f"0x{tile:02X}",
                             "palette": 4 + (attr & 3),
                             "flip_h": bool(attr & 0x40), "flip_v": bool(attr & 0x80),
                             "behind_bg": bool(attr & 0x20)})

    meta = {
        "source_state": str(args.state),
        "source_frame": str(args.frame) if args.frame else None,
        "rom_sha256": hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),
        "ppuctrl": f"0x{state.ppuctrl:02X}",
        "ppumask": f"0x{state.ppumask:02X}",
        "scroll": dict(zip(("coarse_x", "fine_x", "coarse_y"), state.scroll())),
        "camera_x_px": (state.ppuctrl & 3) * 256 + state.scroll()[0] * 8 + state.scroll()[1],
        "screen_aligned": state.scroll()[1] == 0,
        "mmc1_dregs": state.dregs.hex(),
        "chr_mode": "4k" if state.chr_mode_4k else "8k",
        "chr_bank_bg": state._bank_for_slot(1 if (state.ppuctrl & 0x10) else 0),
        "chr_bank_sprites": state._bank_for_slot(1 if (state.ppuctrl & 0x08) else 0),
        "mirroring": ["one_lower", "one_upper", "vertical", "horizontal"][state.dregs[0] & 3]
        if (state.dregs[0] & 3) != 1 else "one_upper",
        "backdrop_rgb": list(backdrop),
        "unique_bg_tiles": len(mapping),
        "sprites": sprites_list,
        "palette_learning": pal_report,
        "render_check": "pixel-exact" if not pal_report["conflicts"] and args.frame else "unverified",
        "notes": [
            "tilemap.csv is page-aligned: cell (0,0) is nametable tile (0,0) of the "
            "page selected by PPUCTRL, not necessarily the top-left pixel on screen.",
            "background.png is exactly what the player saw, including the camera scroll.",
            "When screen_aligned is false the screen shows a horizontal sub-tile offset; "
            "use camera_x_px with a stitched map rather than this page alone.",
        ],
    }
    (out / "room.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"{out}: {len(mapping)} unique BG tiles, {len(sprites_list)} sprites, "
          f"palette from {pal_report['source']}, render {meta['render_check']}")
    if pal_report["conflicts"]:
        print(f"  WARNING: {len(pal_report['conflicts'])} colour index conflict(s); "
              "screen is not fully static and the render is approximate")
    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True, help="FCEUmm savestate (.fcs) from retroshot")
    ap.add_argument("--rom", required=True)
    ap.add_argument("--frame", help="PPM captured at the same emulator frame (recommended)")
    ap.add_argument("--out", required=True, help="output directory for this room")
    args = ap.parse_args()
    write_outputs(args)


if __name__ == "__main__":
    main()

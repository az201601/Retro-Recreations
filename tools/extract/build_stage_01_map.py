#!/usr/bin/env python3
"""Reassemble Stage 1 BG tiles from the original ROM's mapped CHR/nametable.

This is a raw NES BG plane for classification, NOT a GameMaker background:
NES BG combines scenic wallpaper and placed scenery. The final bottom scenic
layer and placed-tile atlas must be separated, per project requirements.
See `nes_ppu.py` and `capture_stage_01.py` for inputs and palette provenance.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageDraw
from nes_ppu import PpuCapture

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "tools/out/emu/stage_01_verified"
DEFAULT_OUT = ROOT / "tools/out/emu/stage_01_verified/maps"
ROOMS = {0: "seating", 1: "kitchen", 2: "grill", 3: "monterey_refill",
         4: "boss_intro", 5: "water_rabbit"}


def tile_key(ppu: PpuCapture, tile: int, palette: int) -> bytes:
    """16 pattern bytes + four original NES color numbers, #0 = backdrop."""
    colors = bytes((ppu.nes_palette[0], *ppu.nes_palette[palette * 4 + 1:palette * 4 + 4]))
    start = tile * 16
    return ppu.pattern[start:start + 16] + colors


def key_image(key: bytes, palette_rgb: tuple[tuple[int, int, int], ...]) -> Image.Image:
    im = Image.new("RGBA", (8, 8))
    lo, hi = key[:8], key[8:16]
    for y in range(8):
        for x in range(8):
            shift = 7 - x
            k = ((lo[y] >> shift) & 1) | (((hi[y] >> shift) & 1) << 1)
            im.putpixel((x, y), (*palette_rgb[key[16 + k] & 0x3F], 255))
    return im


def collect(raw_dir: Path) -> tuple[dict[int, dict[tuple[int, int], Counter[bytes]]],
                                    dict[bytes, Counter[str]],
                                    tuple[tuple[int, int, int], ...]]:
    rooms: dict[int, dict[tuple[int, int], Counter[bytes]]] = defaultdict(lambda: defaultdict(Counter))
    examples: dict[bytes, Counter[str]] = defaultdict(Counter)
    nes_rgb = None
    for part in ("seating_opening", "route_to_boss", "water_rabbit"):
        path = raw_dir / part
        snapshots = sorted(path.glob("ppu_*.bin"))
        print(part, len(snapshots), "snapshots", flush=True)
        for pp_path in snapshots:
            frame = int(pp_path.stem.split("_")[1])
            # Boss animation every 2 frames, but the static map only needs one
            # sample per 40; preserve the full PPU stream for sprite extraction.
            if part == "water_rabbit" and frame % 40 != 20351 % 40:
                continue
            ram = (path / f"ram_{frame:05}.bin").read_bytes()
            if len(ram) != 2048:
                raise ValueError(f"invalid RAM capture at {frame}")
            room = ram[0x73]
            scroll_x = ram[0xAF] * 256 + ram[0xAD]
            scroll_y = ram[0xB3] * 256 + ram[0xB1]
            # A room number changes before its camera/nametables finish loading.
            # Also discard the opening cutscene (room 0, main state 5) and the
            # boss's in-room dialogue (room 5, main state 3). Only use stable
            # gameplay pages for permanent Stage 1 geometry.
            if ram[0x40] != 4 or not (
                (room == 0 and scroll_y == 0x200) or
                (room == 1 and 0x600 <= scroll_y <= 0x700) or
                (room == 2 and scroll_y == 0x500) or
                (room == 3 and scroll_y == 0x400 and scroll_x < 0x100) or
                (room == 5 and scroll_y == 0x100 and scroll_x == 0x400)
            ):
                continue
            ppu = PpuCapture.from_file(pp_path)
            if nes_rgb is None:
                nes_rgb = ppu.rgb_palette
            elif ppu.rgb_palette != nes_rgb:
                raise ValueError(f"fceumm palette changed unexpectedly at {frame}")
            # Only capture *complete* 8x8 tiles actually visible on the screen.
            # Sampling tile centers prevents fine-scroll edge corruption.
            for wx in range((scroll_x // 8) * 8, scroll_x + 256, 8):
                sx = wx + 4 - scroll_x
                if not 0 <= sx < 256:
                    continue
                for wy in range((scroll_y // 8) * 8, scroll_y + 240, 8):
                    sy = wy + 4 - scroll_y
                    if not 0 <= sy < 240:
                        continue
                    info = ppu.bg_at(wx + 4, wy + 4)
                    if info is None:
                        continue
                    tile, palette = info
                    key = tile_key(ppu, tile, palette)
                    pos = (wx // 8, wy // 8)
                    rooms[room][pos][key] += 1
                    examples[key][f"{part}:{frame}:{tile:02x}:{palette}"] += 1
    if nes_rgb is None:
        raise RuntimeError("No capture data; run capture_stage_01.py first")
    return rooms, examples, nes_rgb


def build(raw_dir: Path, out: Path) -> None:
    rooms, examples, rgb = collect(raw_dir)
    out.mkdir(parents=True, exist_ok=True)
    chosen = {room: {pos: votes.most_common(1)[0][0] for pos, votes in tilemap.items()}
              for room, tilemap in rooms.items()}
    used = Counter(key for tilemap in chosen.values() for key in tilemap.values())
    keys = sorted(used, key=lambda k: (-used[k], hashlib.sha256(k).hexdigest()))
    images = [key_image(key, rgb) for key in keys]
    index = {key: i for i, key in enumerate(keys)}
    cols = 32
    sheet = Image.new("RGBA", (cols * 8, ((len(keys) + cols - 1) // cols) * 8))
    for i, img in enumerate(images):
        sheet.paste(img, (i % cols * 8, i // cols * 8))
    sheet.save(out / "all_bg_tiles_rom_palette.png")
    preview = Image.new("RGB", (16 * 64, ((min(len(keys), 512) + 15) // 16) * 64), "#303030")
    draw = ImageDraw.Draw(preview)
    for i, img in enumerate(images[:512]):
        big = img.resize((32, 32), Image.Resampling.NEAREST)
        x, y = (i % 16) * 64, (i // 16) * 64
        preview.paste(big, (x, y), big)
        draw.text((x + 2, y + 35), f"{i}: {used[keys[i]]}", fill="#ffffff")
    preview.save(out / "tiles_overview_first_512.png")
    manifest = {
        "description": "raw captured NES BG plane; not yet separated into backdrop and placed scenery",
        "source": "fceumm PPU mapped CHR and nametable, 8x8 pixel tiles at 1x NES scale",
        "atlas": "all_bg_tiles_rom_palette.png",
        "atlas_width_tiles": cols, "tile_size_px": 8,
        "palette_rgb": list(rgb),
        "tiles": [
            {"id": i, "chr_pattern_and_nes_colors_hex": key.hex(),
             "world_cell_count": used[key],
             "example_source": examples[key].most_common(1)[0][0]}
            for i, key in enumerate(keys)
        ],
        "rooms": {},
    }
    for room, cells in chosen.items():
        name = ROOMS[room]
        xs = [pos[0] for pos in cells]
        ys = [pos[1] for pos in cells]
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        grid = Image.new("RGBA", ((xmax - xmin + 1) * 8, (ymax - ymin + 1) * 8))
        for (tx, ty), key in cells.items():
            grid.paste(images[index[key]], ((tx - xmin) * 8, (ty - ymin) * 8))
        grid.save(out / f"room_{room}_{name}_bgplane.png")
        # Compact, reproducible per-cell placement in world pixel coordinates.
        manifest["rooms"][name] = {
            "room_index": room,
            "bounds_world_px": [xmin * 8, ymin * 8, (xmax + 1) * 8, (ymax + 1) * 8],
            "png": f"room_{room}_{name}_bgplane.png",
            "cells": [[tx * 8, ty * 8, index[key]] for (tx, ty), key in sorted(cells.items(), key=lambda t: (t[0][1], t[0][0]))],
            "conflicting_cells": sum(len(v) > 1 for v in rooms[room].values()),
        }
        print(f"  {name}: bounds {(xmin * 8, ymin * 8, (xmax + 1) * 8, (ymax + 1) * 8)},"
              f" {len(cells)} cells, {manifest['rooms'][name]['conflicting_cells']} time-varying", flush=True)
    (out / "raw_bgplane_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Atlas tiles:", len(keys), "written to", out, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=RAW)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    build(args.raw, args.out)


if __name__ == "__main__":
    main()

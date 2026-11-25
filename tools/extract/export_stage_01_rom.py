#!/usr/bin/env python3
"""Export the *static* Restaurant rooms, placed metatiles, and spawn lists.

This reads the checked-in USA NES ROM, not a third-party disassembly. Its layout
is an 8x8 array of screen IDs; each used screen is 16x15 16-pixel metatiles.
The ROM tileset supplies four 8x8 CHR indices and a 2-bit palette per metatile.
The resulting scenery is the original, unmodified stage *before* prizes and
scripted objects are stamped into the NES nametable during gameplay.

Separation follows the project's GMS asset convention: the bottom scenic layer
contains wallpaper/wall paint only; windows, counters, furniture, appliances,
platforms, etc. go in a placed tile atlas, even if non-collidable. Wallpaper
hidden behind placed cells is inferred, not claimed to have existed in the ROM.
Compositing the two layers must recover the ROM's exact static BG in every
mapped cell. Prizes/enemies are separate objects, NEVER baked into the scenery.

Requires Pillow. Optional --verify compares the static tiles with captures
from capture_stage_01.py; differences at dynamic prize/animation positions
are expected and reported rather than silently incorporated into the map.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
ROM = ROOT / "Chip 'n Dale - Rescue Rangers 2 (USA).nes"
DEFAULT_OUT = ROOT / "assets/stages/stage_01_restaurant"
CAPTURE = ROOT / "tools/out/emu/stage_01_verified"
ROM_SHA256 = "34ca559b733ed910b0a493a0cb1f5d64e5cd9e7e4796032d986c08079573e047"
# Offsets are *file* offsets in this exact ROM, validated against captured PPU
# and the header/bank/pointer tables. PRG: 16 + 8*16384; CHR: 131088.
CHR_START = 16 + 8 * 16384
LAYOUT_OFFSET = 56954  # first 64 bytes of PRG bank 3, Restaurant's 8x8 screens
TILESETS = {"restaurant": 49168, "refill": 50256}  # 4*256 pattern IDs + 64 attrs
PALETTES = {"seating": 61742, "kitchen": 61774,
            "grill": 61774, "monterey": 62351, "water_rabbit": 61790}
OBJECT_OFFSETS = {"seating": 58369, "kitchen": 58406, "grill": 58452,
                  "monterey": 58477, "water_rabbit": 58481}
PRIZE_OFFSETS = {"seating": 59228, "kitchen": 59335, "grill": 59446}
OBJECT_TYPES = {0x27: "honey_bee", 0x25: "fork_rat", 0x24: "spoon_rat",
                0x26: "fake_box", 0x08: "bottle_cork", 0x1F: "star_prize",
                0x21: "exit_right", 0x09: "sink_valve", 0x1E: "zipper_in_box",
                0x1B: "monterey_refill", 0x3F: "water_rabbit"}
PRIZE_TYPES = {0x40: "crate", 0x50: "crate_with_rr", 0x60: "crate_with_acorn",
               0x80: "concrete", 0x90: "rr_collectible"}
# Fixed 64-color RGB lookup exposed by the pinned fceumm core's private PPU
# snapshot. This avoids relying on a generated/ignored capture for ROM export.
FCEUMM_RGB = bytes.fromhex(
    "6c6c6c00268e0000a84000947000707800407000006216004424003434000050"
    "00004444004060000000101010101010bababa205cdc3838ff8020f0c000c0d0"
    "1474d02020ac40147c540058640000880000746800749c202020101010101010"
    "ffffff4ca0ff8888ffc06cffff50ffff64b8ff7878ff9638dbab00a2ca204adc"
    "4a2ccca41cc2ea585858101010101010ffffffb0d4ffc4c4ffe8b8ffffb0ffff"
    "b8e8ffc4c4ffd4a8ffe890f0f4a4c0ffc0acf4f0a0e8ffc2c2c2202020101010"
)
if len(FCEUMM_RGB) != 192:
    raise AssertionError("fceumm RGB lookup must have exactly 64 triples")
RGB = tuple(tuple(FCEUMM_RGB[i:i + 3]) for i in range(0, 192, 3))


@dataclass(frozen=True)
class Region:
    name: str
    page_x: int
    page_y: int
    pages_w: int
    pages_h: int
    chr_4k: int
    tileset: str
    # These *visually identified* IDs are wall/backdrop; everything else is
    # conservative foreground. All windows, cups and counter tops are placed.
    scenic_ids: frozenset[int]
    fallback_meta: int
    prize_page_y: int | None = None


REGIONS = (
    Region("seating", 0, 2, 8, 1, 15, "restaurant",
           frozenset([0x93, 0x94, 0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D]), 0x93, 2),
    Region("kitchen", 0, 6, 8, 2, 16, "restaurant",
           frozenset([0x32, 0x33, 0x34, 0x35, 0x36,
                      0x38, 0x39, 0x3A, 0x3B, 0x52]), 0x34, 7),
    Region("grill", 0, 5, 7, 1, 16, "restaurant",
           frozenset([0x32, 0x33, 0x34, 0x35, 0x36,
                      0x38, 0x39, 0x3A, 0x3B, 0x52]), 0x34, 5),
    Region("monterey", 0, 4, 1, 1, 21, "refill",
           frozenset([0x00, 0x32, 0x48, 0x51, 0x52]), 0x52),
    Region("water_rabbit", 4, 1, 1, 1, 15, "restaurant",
           frozenset([0x33, 0x34, 0x35, 0x36, 0x64, 0x81, 0x95,
                      0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D]), 0x95),
)


def load_rom(path: Path = ROM) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != ROM_SHA256:
        raise ValueError(f"requires the original USA ROM (SHA-256 {ROM_SHA256})")
    if data[:16] != bytes.fromhex("4e45531a081010000000000000000000"):
        raise ValueError("unexpected ROM header, cannot decode MMC1 pages")
    if data[LAYOUT_OFFSET:LAYOUT_OFFSET + 8] != bytes.fromhex("0000000000000100"):
        raise ValueError("Restaurant layout offset not present")
    if data[TILESETS["restaurant"]:TILESETS["restaurant"] + 8] != bytes.fromhex("0094b606080c484a"):
        raise ValueError("Restaurant metatile table offset not present")
    if data[PALETTES["seating"]:PALETTES["seating"] + 4] != bytes.fromhex("0f162920"):
        raise ValueError("palette offset not present")
    return data


def screen_offset(rom: bytes, screen_id: int) -> int:
    """Decode 8-bit ROM lo/hi banked pointers for a 16x15-metatile screen.

    The original ROM has 256 *two* pointer bytes at PRG-bank-0 offsets 0 and
    256; unlike a reassembled disassembly its first room begins at file 528.
    """
    if not 0 <= screen_id < 256:
        raise ValueError(screen_id)
    low = rom[16 + screen_id]
    high_bank = rom[16 + 256 + screen_id]
    return 16 + (high_bank >> 6) * 16384 + ((high_bank & 0x3F) << 8) + low


def collision(meta: int) -> str:
    """NES generic object collision: down threshold A0, up/side D0, F9 excepted.

    Special scripted stage hazards and object-to-object collision need code;
    this metadata is not a substitute for a complete GameMaker physics engine.
    """
    if meta == 0xF9:
        return "none"
    if meta >= 0xD0:
        return "solid"
    if meta >= 0xA0:
        return "one_way"
    return "none"


class Metatiles:
    def __init__(self, rom: bytes, region: Region):
        self.rom = rom
        self.chr = rom[CHR_START + region.chr_4k * 4096:CHR_START + (region.chr_4k + 1) * 4096]
        self.table = rom[TILESETS[region.tileset]:TILESETS[region.tileset] + 1088]
        self.palette = rom[PALETTES[region.name]:PALETTES[region.name] + 16]
        if len(self.chr) != 4096 or len(self.table) != 1088 or len(self.palette) != 16:
            raise ValueError(f"missing graphics for {region.name}")
        self.cache: dict[int, Image.Image] = {}

    def tile_ids(self, meta: int) -> tuple[int, int, int, int]:
        return tuple(self.table[q * 256 + meta] for q in range(4))

    def pal(self, meta: int) -> int:
        return (self.table[1024 + meta // 4] >> (2 * (meta % 4))) & 3

    def image(self, meta: int) -> Image.Image:
        if meta not in self.cache:
            img = Image.new("RGBA", (16, 16))
            palette = self.pal(meta)
            for q, tile in enumerate(self.tile_ids(meta)):
                for y in range(8):
                    lo = self.chr[tile * 16 + y]
                    hi = self.chr[tile * 16 + y + 8]
                    for x in range(8):
                        k = ((lo >> (7 - x)) & 1) | (((hi >> (7 - x)) & 1) << 1)
                        color = RGB[self.palette[0 if k == 0 else palette * 4 + k] & 63]
                        img.putpixel((q % 2 * 8 + x, q // 2 * 8 + y), (*color, 255))
            self.cache[meta] = img
        return self.cache[meta]

    def sheet(self) -> Image.Image:
        sheet = Image.new("RGBA", (256, 256))
        for meta in range(256):
            sheet.paste(self.image(meta), (meta % 16 * 16, meta // 16 * 16))
        return sheet

    def prize_cutout(self, meta: int) -> Image.Image:
        """Approximate alpha for a movable object drawn in the NES BG plane.

        Tiles are opaque on hardware, with color 0 underneath the prize. Take
        the bounding rectangle of nonzero CHR pixels, retain its black outline
        and interior, and make ONLY the outside transparent. The user must
        supply background restoration when a crate is moved or destroyed.
        """
        points = []
        for q, tile in enumerate(self.tile_ids(meta)):
            for y in range(8):
                lo, hi = self.chr[tile * 16 + y], self.chr[tile * 16 + y + 8]
                for x in range(8):
                    if ((lo | hi) >> (7 - x)) & 1:
                        points.append((q % 2 * 8 + x, q // 2 * 8 + y))
        cutout = self.image(meta).copy()
        if points:
            left, top = min(x for x, _ in points), min(y for _, y in points)
            right, bottom = max(x for x, _ in points), max(y for _, y in points)
            alpha = Image.new("L", (16, 16))
            alpha.paste(255, (left, top, right + 1, bottom + 1))
            cutout.putalpha(alpha)
        return cutout


def screen_grid(rom: bytes, region: Region) -> list[list[int | None]]:
    """A region grid of 16px metatiles; None for truly unmapped screens/gaps."""
    layout = rom[LAYOUT_OFFSET:LAYOUT_OFFSET + 64]
    rows: list[list[int | None]] = []
    for py in range(region.page_y, region.page_y + region.pages_h):
        for my in range(16):
            row: list[int | None] = []
            for px in range(region.page_x, region.page_x + region.pages_w):
                ref = layout[py * 8 + px]
                if ref and my < 15:
                    off = screen_offset(rom, ref - 1) + 16 * my
                    row.extend(rom[off:off + 16])
                else:
                    row.extend([None] * 16)
            rows.append(row)
    return rows


def parse_prizes(rom: bytes, region: Region) -> list[dict]:
    if region.name not in PRIZE_OFFSETS:
        return []
    assert region.prize_page_y is not None
    p = PRIZE_OFFSETS[region.name]
    result = []
    while rom[p] != 0xFF:
        x, flags_y = rom[p:p + 2]
        kind = PRIZE_TYPES.get(flags_y & 0xF0)
        if kind is None:
            raise ValueError(f"unrecognized prize at ROM offset {p}")
        # A high bit in the ROM X column marks a vertically inserted column:
        # the kitchen has three such boxes at x=0x63, y=0x6B..0x6D (above
        # its normal 0x7x lower room), rather than impossible x=0xE3.
        page_y = region.prize_page_y - (1 if x & 0x80 else 0)
        result.append({"kind": kind, "x": (x & 0x7F) * 16,
                       "y": (page_y * 16 + (flags_y & 15)) * 16,
                       "rom_offset": p, "rom_type": flags_y & 0xF0,
                       "vertical_spawn_flag": bool(x & 0x80)})
        p += 2
    return result


def parse_objects(rom: bytes, region: Region) -> list[dict]:
    p = OBJECT_OFFSETS[region.name]
    result = []
    while rom[p] != 0xFF:
        raw_x, y, obj_id = rom[p:p + 3]
        if obj_id not in OBJECT_TYPES:
            raise ValueError(f"unrecognized object ${obj_id:02x} at ROM offset {p}")
        result.append({"kind": OBJECT_TYPES[obj_id], "x": (raw_x & 0x7F) * 16,
                       "y": y * 16, "rom_offset": p, "rom_type": obj_id,
                       "vertical_spawn_flag": bool(raw_x & 0x80)})
        p += 3
    return result


def make_region(rom: bytes, region: Region, out: Path) -> dict:
    gfx = Metatiles(rom, region)
    grid = screen_grid(rom, region)
    w, h = region.pages_w * 256, region.pages_h * 256
    origin = [region.page_x * 256, region.page_y * 256]
    scenic = Image.new("RGBA", (w, h))
    composite = Image.new("RGBA", (w, h))
    foreground: list[list[int | str]] = []
    used: Counter[int] = Counter()
    # The true scenic cells (not hidden by placed tiles) remain byte-exact.
    # Fill hidden portions by the closest known same-page wallpaper, favouring
    # the same 2x2-grid phase; this is an *inferred* layer, not ROM geometry.
    for y, row in enumerate(grid):
        same_page = grid[(y // 16) * 16:(y // 16 + 1) * 16]
        candidates = [(xx, (y // 16) * 16 + yy, v)
                      for yy, r in enumerate(same_page)
                      for xx, v in enumerate(r) if v in region.scenic_ids]
        for x, meta in enumerate(row):
            if meta is None:
                continue
            used[meta] += 1
            pos = (x * 16, y * 16)
            full = gfx.image(meta)
            composite.paste(full, pos)
            if meta in region.scenic_ids:
                scenic.paste(full, pos)
                continue
            wx, wy = origin[0] + pos[0], origin[1] + pos[1]
            foreground.append([wx, wy, meta, collision(meta)])
            # Avoid pulling a wallpaper sample from an unrelated screen across
            # the kitchen's empty, upper-left pages.
            near = [(cx, cy, value) for cx, cy, value in candidates if cx // 16 == x // 16]
            if not near:
                near = candidates
            backdrop = min(near,
                           key=lambda p: (abs(x - p[0]) + abs(y - p[1])
                                          + 2 * ((x - p[0]) & 1)
                                          + 2 * ((y - p[1]) & 1))) [2] if near else region.fallback_meta
            scenic.paste(gfx.image(backdrop), pos)
    # Invariant: at every mapped pixel, scenic + opaque placed tiles = the
    # ROM's exact original static BG, independent of guessed hidden wallpaper.
    rebuilt = scenic.copy()
    for wx, wy, meta, _ in foreground:
        rebuilt.paste(gfx.image(meta), (int(wx) - origin[0], int(wy) - origin[1]))
    if rebuilt.tobytes() != composite.tobytes():
        raise AssertionError(f"scenic + placed tiles do not reconstruct {region.name}")
    bg_name = f"bg_restaurant_{region.name}.png"
    ts_name = f"ts_restaurant_{region.name}.png"
    (out / "background").mkdir(parents=True, exist_ok=True)
    (out / "tilesets").mkdir(parents=True, exist_ok=True)
    (out / "previews").mkdir(parents=True, exist_ok=True)
    scenic.save(out / "background" / bg_name)
    gfx.sheet().save(out / "tilesets" / ts_name)
    composite.save(out / "previews" / f"rom_static_{region.name}.png")
    prize_strip = None
    if region.prize_page_y is not None:
        # Boxes/RR are dynamically stamped in the NES BG plane, not part of
        # the ROM's static screens. GMS needs them as interactive objects;
        # export approximate-alpha versions of the actual F4/F5/F6/F9 tiles.
        (out / "sprites").mkdir(exist_ok=True)
        prize_strip = f"sprites/spr_prizes_{region.name}_strip.png"
        strip = Image.new("RGBA", (16 * 4, 16))
        for i, meta in enumerate((0xF4, 0xF5, 0xF6, 0xF9)):
            strip.paste(gfx.prize_cutout(meta), (16 * i, 0))
        strip.save(out / prize_strip)
    # No hard-coded room IDs are used for extraction; list the actual 8x8
    # layout bytes and corresponding original ROM pointers for provenance.
    layout = rom[LAYOUT_OFFSET:LAYOUT_OFFSET + 64]
    screens = [{"page": [px, py], "screen_id": layout[py * 8 + px],
                "rom_offset": (screen_offset(rom, layout[py * 8 + px] - 1)
                               if layout[py * 8 + px] else None)}
               for py in range(region.page_y, region.page_y + region.pages_h)
               for px in range(region.page_x, region.page_x + region.pages_w)]
    return {"origin_world_px": origin, "dimensions_px": [w, h],
            "background": f"background/{bg_name}", "tileset": f"tilesets/{ts_name}",
            "pattern_4kb_bank": region.chr_4k, "bg_palette_rom_offset": PALETTES[region.name],
            "bg_palette_nes_indices": list(gfx.palette), "metatile_table_rom_offset": TILESETS[region.tileset],
            "screens": screens, "used_metatiles": {f"{i:02x}": n for i, n in sorted(used.items())},
            "scenic_metatile_ids": sorted(region.scenic_ids),
            "placed_tiles": foreground, "prizes": parse_prizes(rom, region),
            "prize_sprite_strip": prize_strip,
            "prize_sprite_cell_order": (["crate", "crate_with_rr", "crate_with_acorn",
                                         "rr_collectible"] if prize_strip else []),
            "objects": parse_objects(rom, region),
            "unmapped_cells": sum(v is None for row in grid for v in row),
            "static_bg_sha256": hashlib.sha256(composite.tobytes()).hexdigest()}


def verify_capture(rom: bytes, region: Region, captured_file: Path, ram_file: Path) -> tuple[int, int, list]:
    from nes_ppu import PpuCapture  # optional raw captures; not required to export
    pp = PpuCapture.from_file(captured_file)
    ram = ram_file.read_bytes()
    if len(ram) != 2048:
        raise ValueError("RAM snapshot must have 2048 bytes")
    sx, sy = ram[0xAF] * 256 + ram[0xAD], ram[0xB3] * 256 + ram[0xB1]
    gfx = Metatiles(rom, region)
    grid = screen_grid(rom, region)
    good = bad = 0
    examples = []
    for yy in range(0, 208, 8):
        for xx in range(0, 256, 8):
            wx, wy = sx + xx + 4, sy + yy + 4
            ix = wx // 16 - region.page_x * 16
            iy = wy // 16 - region.page_y * 16
            if not (0 <= iy < len(grid) and 0 <= ix < len(grid[0])):
                continue
            meta = grid[iy][ix]
            info = pp.bg_at(wx, wy)
            if info is None or meta is None:
                continue
            expected = gfx.tile_ids(meta)[(wy // 8 % 2) * 2 + (wx // 8 % 2)], gfx.pal(meta)
            if expected == info:
                good += 1
            else:
                bad += 1
                if len(examples) < 4:
                    examples.append({"world": [wx, wy], "rom": list(expected), "ppu": list(info)})
    return good, bad, examples


def build(out: Path, *, verify: bool = False) -> dict:
    rom = load_rom()
    out.mkdir(parents=True, exist_ok=True)
    data = {"format": "NES Stage 1 Restaurant static metatile + object map 1",
            "source_rom_sha256": ROM_SHA256, "ppu_rgb_palette_hex": FCEUMM_RGB.hex(),
            "source_layout_rom_offset": LAYOUT_OFFSET, "screen_pixels": [256, 240],
            "screen_stride_world_pixels": [256, 256], "metatile_pixels": 16,
            "atlas_columns": 16, "room_gms": "rm_stage_01_restaurant",
            "pixel_origin": "NES world coordinates; view top-left = ROM scroll registers; HUD excluded",
            "notes": [
                "Static scenery only: crates/prizes, actors, boss and animated water are objects.",
                "The bottom scenic layer contains inferred wallpaper behind opaque placed tiles.",
                "Collision values describe ROM generic thresholds (down A0, side/up D0; F9 exempt).",
                "Unmapped pages and each 16-pixel nametable-attribute band are transparent, not scenery.",
                "Composite of each scenic PNG and its placed tiles exactly equals the ROM's static BG."
            ], "regions": {}}
    for region in REGIONS:
        result = make_region(rom, region, out)
        data["regions"][region.name] = result
        print(region.name, "pages", len(result["screens"]), "placed tiles", len(result["placed_tiles"]),
              "prizes", len(result["prizes"]), "objects", len(result["objects"]))
    if verify:
        # Screen snapshots at stable, known frames; earlier transition/fade
        # frames do not use the room's static CHR bank/palette yet.
        test_frames = {"seating": ("seating_opening", 11201),
                       "kitchen": ("route_to_boss", 13521),
                       "grill": ("route_to_boss", 15001),
                       "monterey": ("route_to_boss", 16513),
                       "water_rabbit": ("water_rabbit", 20701)}
        for region in REGIONS:
            part, frame = test_frames[region.name]
            loc = CAPTURE / part
            ppu = loc / f"ppu_{frame}.bin"
            if not ppu.is_file():
                raise FileNotFoundError(f"--verify requires {ppu}; regenerate with capture_stage_01.py")
            good, bad, examples = verify_capture(rom, region, ppu, loc / f"ram_{frame}.bin")
            print(f"  capture {region.name} {frame}: {good} static tiles agree, "
                  f"{bad} dynamic differences; {examples[:1]}")
            if good < 600 or (region.name in ("monterey", "water_rabbit") and bad):
                raise AssertionError(f"ROM/static capture mismatch in {region.name}")
            data["regions"][region.name]["capture_check"] = {
                "part": part, "frame": frame, "matching_tiles": good,
                "dynamic_tiles": bad, "first_dynamic_positions": examples}
    maps_dir = out / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)
    (maps_dir / "stage_01_restaurant.json").write_text(json.dumps(data, indent=2) + "\n")
    # One overview is an inspectable reference, NEVER import this composite as
    # a GMS scenic backdrop. The maps/atlas above are the import resources.
    composites = [Image.open(out / "previews" / f"rom_static_{r.name}.png") for r in REGIONS]
    preview = Image.new("RGB", (1060, 950), "#161821")
    draw = ImageDraw.Draw(preview)
    positions = [(16, 22, 0.50), (16, 185, 0.50), (16, 482, 0.55),
                 (16, 663, 1), (306, 663, 1)]
    for region, img, (x, y, factor) in zip(REGIONS, composites, positions):
        draw.text((x, y), f"{region.name.upper()}  |  ROM static BG  |  world {region.page_x * 256}, {region.page_y * 256}",
                  fill="#e9e9e9")
        drawn = img.resize((int(img.width * factor), int(img.height * factor)), Image.Resampling.NEAREST)
        preview.paste(drawn, (x, y + 18), drawn)
    preview.save(out / "previews" / "stage_01_static_overview.png")
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--verify", action="store_true", help="compare stable fceumm PPU frames")
    args = ap.parse_args()
    build(args.out, verify=args.verify)


if __name__ == "__main__":
    main()

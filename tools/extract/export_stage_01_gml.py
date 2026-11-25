#!/usr/bin/env python3
"""Generate GMS 1.4.1760-compatible tile placement and spawn scripts.

The GML contains literal compact metatile rows from the *ROM* export; no JSON
file I/O, external DLL, or emulator is required once it is imported. These
scripts are import resources, not a tested, runnable .gmx project: the user
must create background, object and room resources in GameMaker first.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from export_stage_01_rom import DEFAULT_OUT, ROM_SHA256, ROOT

DATA = DEFAULT_OUT / "maps/stage_01_restaurant.json"
OUT = ROOT / "gms_export/scripts/stage_01"
REGIONS = ("seating", "kitchen", "grill", "monterey", "water_rabbit")
OBJECTS = {"honey_bee": "obj_enemy_honeybee", "fork_rat": "obj_enemy_fork_rat",
           "spoon_rat": "obj_enemy_spoon_rat", "fake_box": "obj_enemy_fake_box",
           "bottle_cork": "obj_enemy_bottle_cork", "star_prize": "obj_star_prize",
           "exit_right": "obj_stage01_exit_right", "sink_valve": "obj_sink_valve",
           "zipper_in_box": "obj_zipper_in_box", "monterey_refill": "obj_monterey_refill",
           "water_rabbit": "obj_boss_water_rabbit"}


def load_map(path: Path) -> dict:
    data = json.loads(path.read_text())
    if data["source_rom_sha256"] != ROM_SHA256:
        raise ValueError("run export_stage_01_rom.py on the original USA ROM first")
    if tuple(data["regions"]) != REGIONS:
        raise ValueError("unexpected Stage 1 regions")
    return data


def dense_rows(region: dict) -> list[str]:
    width, height = region["dimensions_px"]
    ox, oy = region["origin_world_px"]
    rows = [[255 for _ in range(width // 16)] for _ in range(height // 16)]
    for x, y, meta, _ in region["placed_tiles"]:
        if meta == 255:
            raise ValueError("0xff is reserved for transparent/scenic cells")
        dx, dy = x - ox, y - oy
        if dx % 16 or dy % 16 or not 0 <= dx < width or not 0 <= dy < height:
            raise ValueError("placed tile off grid")
        rows[dy // 16][dx // 16] = meta
    return ["".join(f"{meta:02x}" for meta in row) for row in rows]


def make_static(data: dict) -> str:
    lines = [
        "/// scr_stage01_place_static()  |  generated from original USA NES ROM",
        "/// Attach to obj_stage01_controller Create event in rm_stage_01_restaurant.",
        "/// Room size: 2048x2048. View: 256x240; initial view x=0, y=512.",
        "/// Import each bg_restaurant_* and ts_restaurant_* PNG as a GMS Background.",
        "/// Tile dimensions: 16x16, NO interpolation. BG 10000; tiles 1000.",
        "/// Collision grid value 1 = NES one-way from above; 2 = solid.",
        "/// Later: call ds_grid_destroy(global.stage01_collision_grid) on Room End.",
        "var grid_rows, row_text, row_y, cell_x, tile_id, xx, yy;",
        "global.stage01_collision_grid = ds_grid_create(128, 128);",
        "ds_grid_clear(global.stage01_collision_grid, 0);",
    ]
    for name in REGIONS:
        region = data["regions"][name]
        ox, oy = region["origin_world_px"]
        width, height = region["dimensions_px"]
        lines.extend([
            "",
            f"// {name} | NES world {ox},{oy} | {width}x{height} source pixels",
            f"tile_add(bg_restaurant_{name}, 0, 0, {width}, {height}, {ox}, {oy}, 10000);",
        ])
        for i, encoded in enumerate(dense_rows(region)):
            chunks = [encoded[pos:pos + 64] for pos in range(0, len(encoded), 64)]
            lines.append(f"grid_rows[{i}] = " + " + ".join('"' + c + '"' for c in chunks) + ";")
        lines.extend([
            f"for (row_y = 0; row_y < {height // 16}; row_y += 1) {{",
            "    row_text = grid_rows[row_y];",
            f"    for (cell_x = 0; cell_x < {width // 16}; cell_x += 1) {{",
            "        tile_id = scr_stage01_hex_byte(row_text, cell_x);",
            "        if (tile_id != 255) {",
            f"            xx = {ox} + cell_x * 16;",
            f"            yy = {oy} + row_y * 16;",
            f"            tile_add(ts_restaurant_{name}, (tile_id mod 16) * 16,",
            "                     floor(tile_id / 16) * 16, 16, 16, xx, yy, 1000);",
            "            if (tile_id >= 208 && tile_id != 249) {",
            "                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 2);",
            "            } else if (tile_id >= 160 && tile_id != 249) {",
            "                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 1);",
            "            }",
            "        }",
            "    }",
            "}",
        ])
    return "\n".join(lines) + "\n"


def make_prizes(data: dict) -> str:
    lines = [
        "/// scr_stage01_spawn_prizes()  |  generated from NES room prize lists",
        "/// Requires obj_crate and obj_rre. Call after scr_stage01_place_static().",
        "/// Type: 0 ordinary, 1 contains hidden RR, 2 contains hidden acorn.",
        "/// NOTE: obj_crate must implement revealing drops; it is not automatic.",
        "var cr;",
    ]
    for name in REGIONS:
        records = data["regions"][name]["prizes"]
        if not records:
            continue
        lines.extend(["", f"// {name}: {len(records)} individually placed prize metatiles"])
        for item in records:
            x, y, kind = item["x"], item["y"], item["kind"]
            if kind == "rr_collectible":
                lines.append(f"instance_create({x}, {y}, obj_rre);")
            else:
                variant = {"crate": 0, "crate_with_rr": 1,
                           "crate_with_acorn": 2}[kind]
                lines.extend([f"cr = instance_create({x}, {y}, obj_crate);",
                              f"cr.hidden_drop = {variant};"])
    return "\n".join(lines) + "\n"


def make_actors(data: dict) -> str:
    lines = [
        "/// scr_stage01_spawn_actors()  |  generated from NES room object lists",
        "/// Requires every referenced obj_* resource in the GMS 1.4 project.",
        "/// Spawns all actors up-front, unlike the ROM's scroll-column insertion.",
        "/// Exit, faucet, Monterey and boss behavior require implementation.",
    ]
    for name in REGIONS:
        actors = data["regions"][name]["objects"]
        lines.extend(["", f"// {name}"])
        for obj in actors:
            lines.append(f"instance_create({obj['x']}, {obj['y']}, {OBJECTS[obj['kind']]});"
                         + (" // ROM vertical-spawn flag" if obj["vertical_spawn_flag"] else ""))
    return "\n".join(lines) + "\n"


def make_collision_query() -> str:
    return "\n".join([
        "/// scr_stage01_collision_at(world_x, world_y)",
        "/// Return 0=empty, 1=one-way platform, 2=solid; uses ROM thresholds.",
        "/// Boxes and actors are not in this static grid; test their objects separately.",
        "var cx, cy;",
        "cx = floor(argument0 / 16);",
        "cy = floor(argument1 / 16);",
        "if (cx < 0 || cx >= 128 || cy < 0 || cy >= 128) return 0;",
        "return ds_grid_get(global.stage01_collision_grid, cx, cy);",
        "",
    ])


def build(data_path: Path = DATA, out: Path = OUT) -> dict:
    data = load_map(data_path)
    out.mkdir(parents=True, exist_ok=True)
    scripts = {
        "scr_stage01_hex_byte.gml": "\n".join([
            "/// scr_stage01_hex_byte(row, column) -> ROM metatile byte",
            "/// Hex string parser compatible with GameMaker Studio 1.4.",
            "var digits, hi, lo;",
            "digits = \"0123456789abcdef\";",
            "hi = string_pos(string_char_at(argument0, argument1 * 2 + 1), digits) - 1;",
            "lo = string_pos(string_char_at(argument0, argument1 * 2 + 2), digits) - 1;",
            "return hi * 16 + lo;",
            "",
        ]),
        "scr_stage01_place_static.gml": make_static(data),
        "scr_stage01_collision_at.gml": make_collision_query(),
        "scr_stage01_spawn_prizes.gml": make_prizes(data),
        "scr_stage01_spawn_actors.gml": make_actors(data),
    }
    for fn, source in scripts.items():
        (out / fn).write_text(source)
        print(fn, "lines", source.count("\n"))
    return {fn: hashlib.sha256(source.encode()).hexdigest() for fn, source in scripts.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    build(args.data, args.out)


if __name__ == "__main__":
    main()

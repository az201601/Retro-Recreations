#!/usr/bin/env python3
"""Extract palette-correct, transparent OAM sprite strips from verified runs.

The ROM's CHR tiles alone do not identify assembled character frames. This
script groups *actual* 8x8 OAM sprites from the patched fceumm PPU snapshots,
composites them in NES priority order, and deduplicates the resulting frames.
Player and Water Rabbit poses are high confidence; the Monterey NPC is also
isolated while the player is stationary. This does not recover unvisited
animations or non-OAM objects (boxes/collectibles are BG metatiles instead).

Prerequisite: ./tools/emu/build_fceumm.sh; python3 tools/extract/capture_stage_01.py
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from nes_ppu import PpuCapture
from export_stage_01_rom import CAPTURE, DEFAULT_OUT, RGB


@dataclass
class Pose:
    image: Image.Image
    count: int
    first_frame: int
    last_frame: int
    bounds: tuple[int, int, int, int]
    sample: str
    oam_tiles: tuple[int, ...]


def render_sprite_group(ppu: PpuCapture, group: list[tuple[int, int, int, int, int]],
                        width: int, height: int, x_offset: int, y_offset: int) -> Image.Image:
    """Compose screen-coordinate OAM entries on a small RGBA canvas."""
    img = Image.new("RGBA", (width, height))
    cache = {}
    # NES OAM index zero is drawn on top of all later sprites.
    for idx, sx, sy, tile, attr in sorted(group, reverse=True):
        key = tile, attr & 3, bool(attr & 0x40), bool(attr & 0x80)
        if key not in cache:
            glyph = ppu.tile_image(tile, attr & 3, sprite=True)
            if attr & 0x40:
                glyph = glyph.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if attr & 0x80:
                glyph = glyph.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            cache[key] = glyph
        px, py = sx - x_offset, sy - y_offset
        if 0 <= px <= width - 8 and 0 <= py <= height - 8:
            img.alpha_composite(cache[key], (px, py))
    return img


def group_bounds(group: list[tuple[int, int, int, int, int]]) -> tuple[int, int, int, int]:
    return (min(s[1] for s in group), min(s[2] for s in group),
            max(s[1] for s in group) + 8, max(s[2] for s in group) + 8)


def connected_groups(entries: list[tuple[int, int, int, int, int]], gap: int = 12):
    """Find contiguous sprite entities, not simply all sprites sharing a bank."""
    parent = list(range(len(entries)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(entries):
        for j in range(i):
            b = entries[j]
            if abs(a[1] - b[1]) <= 8 + gap and abs(a[2] - b[2]) <= 8 + gap:
                parent[root(i)] = root(j)
    groups: dict[int, list] = defaultdict(list)
    for i, item in enumerate(entries):
        groups[root(i)].append(item)
    return list(groups.values())


ACTOR_CELLS = {"honey_bee": (48, 48), "fork_rat": (64, 56),
               "spoon_rat": (48, 56), "fake_box": (32, 40),
               "sink_valve": (64, 40), "sink_water_jet": (24, 176),
               "boss_box": (32, 40)}


def classify_actor(room: int, group: list[tuple[int, int, int, int, int]]) -> str | None:
    """Recognize sprites by room + distinctive OAM tile families (not color)."""
    ids = {s[3] for s in group}
    x0, y0, x1, y1 = group_bounds(group)
    if room in (0, 2):
        if len(ids & {0xC0, 0xC2, 0xC4, 0xC6, 0xC8, 0xCA}) >= 3:
            return "honey_bee"
        if len(ids & {0xC1, 0xC3, 0xC5, 0xC7, 0xC9, 0xCB}) >= 3:
            return "fork_rat"
    if room == 1:
        if len(ids & {0xA8, 0xAA, 0xAC, 0xAE, 0xB0, 0xB2}) >= 3:
            return "spoon_rat"
        if {0x8C, 0x8D, 0x8E, 0x8F}.issubset(ids) and len(group) <= 10:
            return "fake_box"
    if room == 2:
        if len(ids & {0xAD, 0xAF, 0xB1, 0xB3, 0xB5, 0xB7, 0xB9, 0xBB}) >= 5:
            return "sink_valve"
        if ids == {0xAA} and len(group) >= 8 and y1 - y0 >= 64:
            return "sink_water_jet"
    if room == 5:
        if {0x8C, 0x8D, 0x8E, 0x8F}.issubset(ids) and len(group) <= 8:
            return "boss_box"
    return None


def add_pose(poses: dict[bytes, Pose], image: Image.Image, frame: int, source: str,
             bounds: tuple[int, int, int, int], group: list) -> None:
    if image.getbbox() is None:
        return
    fingerprint = hashlib.sha256(image.tobytes()).digest()
    if fingerprint in poses:
        poses[fingerprint].count += 1
        poses[fingerprint].last_frame = frame
        return
    poses[fingerprint] = Pose(image, 1, frame, frame, bounds, source,
                              tuple(sorted(set(item[3] for item in group))))


def collect(path: Path, name: str, categories: dict[str, dict[bytes, Pose]]) -> Counter:
    tally = Counter()
    ppus = sorted(path.glob("ppu_*.bin"))
    if not ppus:
        raise FileNotFoundError(f"No PPU snapshots in {path}; run capture_stage_01.py")
    for pp_path in ppus:
        frame = int(pp_path.stem.split("_")[1])
        ram = (path / f"ram_{frame:05}.bin").read_bytes()
        room, state = ram[0x73], ram[0x40]
        # Gameplay (not fade/dialogue): a room number can change several
        # frames before its CHR bank and camera have caught up.
        sx, sy = ram[0xAF] * 256 + ram[0xAD], ram[0xB3] * 256 + ram[0xB1]
        region = {0: "seating", 1: "kitchen", 2: "grill", 3: "monterey", 5: "boss"}.get(room)
        stable = state == 4 and region is not None and (
            (room == 0 and sy == 512) or
            (room == 1 and 1536 <= sy <= 1792) or
            (room == 2 and sy == 1280) or
            (room == 3 and sy == 1024 and sx == 0) or
            (room == 5 and sy == 256 and sx == 1024))
        if not stable:
            continue
        ppu = PpuCapture.from_file(pp_path)
        if ppu.rgb_palette != RGB:
            raise ValueError(f"fceumm RGB table changed at {pp_path}")
        entries = ppu.oam_sprites()
        px, py = ram[0xC0], ram[0xC2]
        player = [s for s in entries
                  if s[3] < 0x38 and s[1] >= px - 24 and s[1] < px + 24
                  and py - 40 <= s[2] < py + 8 and s[2] < 200]
        if len(player) >= 6:
            img = render_sprite_group(ppu, player, 48, 48, px - 24, py - 40)
            add_pose(categories[f"chip_{region}"], img, frame, name, group_bounds(player), player)
            tally[f"chip_{region}"] += 1
        if room == 5 and ram[0x3D7] > 0:
            # The boss occupies contiguous >=A0 sprite tiles in CHR 4KB bank
            # 12. Other tiles in that bank include the falling box and HUD;
            # group *spatially* and use only the main <=72x96 body component.
            candidates = [s for s in entries if s[2] < 195 and s[3] >= 0xA0]
            clusters = sorted(connected_groups(candidates), key=len, reverse=True)
            if clusters:
                boss = clusters[0]
                x0, y0, x1, y1 = group_bounds(boss)
                if len(boss) >= 16 and x1 - x0 <= 72 and y1 - y0 <= 96:
                    # Body aligned to bottom-center for GameMaker sprite origin.
                    img = render_sprite_group(ppu, boss, 80, 104,
                                              x0 - (80 - (x1 - x0)) // 2,
                                              y1 - 96)
                    add_pose(categories["water_rabbit"], img, frame, name,
                             (x0, y0, x1, y1), boss)
                    tally["water_rabbit"] += 1
                else:
                    tally["boss_unclassified"] += 1
        if room == 3:
            # Chef Monterey Jack remains at the center-top of the refill
            # scene; the player sits at x24,y192, far from this OAM group.
            npc = [s for s in entries if 96 <= s[1] <= 156
                   and 96 <= s[2] <= 160 and 0x8C <= s[3] <= 0xB3]
            if len(npc) >= 12:
                cluster = max(connected_groups(npc), key=len)
                x0, y0, x1, y1 = group_bounds(cluster)
                if x1 - x0 <= 48 and y1 - y0 <= 56:
                    img = render_sprite_group(ppu, cluster, 64, 64,
                                              x0 - (64 - (x1 - x0)) // 2,
                                              y1 - 60)
                    add_pose(categories["monterey_jack"], img, frame, name,
                             (x0, y0, x1, y1), cluster)
                    tally["monterey_jack"] += 1
        if room in (0, 1, 2, 5):
            # These are extra high-confidence, ROM-named actors visible in the
            # screenshots. Split by OAM tile families before compositing; an
            # enemy and a nearby player should never become one sprite frame.
            other = [s for s in entries if s[2] < 200 and s[0] not in {p[0] for p in player}]
            if room == 5:
                other = [s for s in other if s[3] in (0x8C, 0x8D, 0x8E, 0x8F)]
            for group in connected_groups(other):
                if len(group) < 4:
                    continue
                kind = classify_actor(room, group)
                if kind is None:
                    continue
                x0, y0, x1, y1 = group_bounds(group)
                width, height = ACTOR_CELLS[kind]
                if x1 > 256 or x1 - x0 > width or y1 - y0 > height:
                    tally[f"{kind}_partial"] += 1
                    continue
                if kind == "sink_water_jet":
                    ox, oy = x0 - (width - (x1 - x0)) // 2, y0
                else:
                    ox, oy = x0 - (width - (x1 - x0)) // 2, y1 - height + 8
                img = render_sprite_group(ppu, group, width, height, ox, oy)
                add_pose(categories[kind], img, frame, name, (x0, y0, x1, y1), group)
                tally[kind] += 1
    return tally


def write_category(name: str, poses: dict[bytes, Pose], out: Path) -> dict:
    if not poses:
        return {"frames": 0, "note": "no matching snapshots"}
    sorted_poses = sorted(poses.values(), key=lambda p: (-p.count, p.first_frame))
    width, height = sorted_poses[0].image.size
    cols = 8 if width >= 64 else 16
    max_rows = 16
    per_sheet = cols * max_rows
    sheets = []
    infos = []
    for start in range(0, len(sorted_poses), per_sheet):
        batch = sorted_poses[start:start + per_sheet]
        atlas = Image.new("RGBA", (width * cols, height * ((len(batch) + cols - 1) // cols)))
        for i, pose in enumerate(batch):
            atlas.paste(pose.image, (i % cols * width, i // cols * height), pose.image)
            infos.append({"id": start + i, "atlas": len(sheets), "atlas_cell": i,
                          "capture": pose.sample, "first_frame": pose.first_frame,
                          "last_frame": pose.last_frame, "frames_seen": pose.count,
                          "oam_bounds_screen": list(pose.bounds),
                          "oam_chr_tile_ids": list(pose.oam_tiles)})
        fn = f"spr_{name}_strip_{len(sheets):02d}.png"
        atlas.save(out / fn)
        sheets.append(fn)
    print(name, "poses", len(infos), "sampled frames", sum(p.count for p in poses.values()),
          "strips", len(sheets))
    return {"frames": len(infos), "cell_size": [width, height], "columns": cols,
            "origin": ([width // 2, 40] if name.startswith("chip_")
                       else [width // 2, 96] if name == "water_rabbit"
                       else [width // 2, 60] if name == "monterey_jack"
                       else [width // 2, 0] if name == "sink_water_jet"
                       else [width // 2, height - 8]),
            "strips": sheets, "poses": infos}


def make_preview(asset_dir: Path, manifest: dict) -> None:
    names = [n for n in ("chip_seating", "chip_kitchen", "chip_grill",
                         "chip_monterey", "chip_boss", "honey_bee", "fork_rat",
                         "spoon_rat", "fake_box", "sink_valve", "boss_box",
                         "monterey_jack", "water_rabbit")
             if manifest[n]["frames"] > 0]
    image = Image.new("RGB", (960, len(names) * 146), "#20242c")
    draw = ImageDraw.Draw(image)
    for row, name in enumerate(names):
        info = manifest[name]
        draw.text((12, row * 146 + 4), f"{name} | {info['frames']} unique poses | top 12 shown",
                  fill="#f1f1f1")
        strip = Image.open(asset_dir / info["strips"][0])
        w, h = info["cell_size"]
        for i in range(min(info["frames"], 12)):
            crop = strip.crop(((i % info["columns"]) * w, (i // info["columns"]) * h,
                               (i % info["columns"] + 1) * w, (i // info["columns"] + 1) * h))
            crop = crop.resize((min(w * 2, 96), min(h * 2, 112)), Image.Resampling.NEAREST)
            image.paste(crop, (12 + i * 78, row * 146 + 25), crop)
    p = asset_dir.parent / "previews"
    p.mkdir(exist_ok=True, parents=True)
    image.save(p / "stage_01_sprite_overview.png")


def build(raw: Path = CAPTURE, out: Path = DEFAULT_OUT / "sprites" ) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    categories: dict[str, dict[bytes, Pose]] = defaultdict(dict)
    tallies = {}
    for part in ("seating_opening", "route_to_boss", "water_rabbit"):
        tallies[part] = dict(collect(raw / part, part, categories))
    manifest = {"source": "fceumm mapped PPU/OAM + RGB captures from capture_stage_01.py",
                "note": "Sprite strips are fixed-size RGBA frames, most frequent poses first. "
                        "They are not exhaustive animation/state machines and have not been "
                        "executed inside GameMaker.",
                "collection": tallies}
    for key in ("chip_seating", "chip_kitchen", "chip_grill", "chip_monterey",
                "chip_boss", "honey_bee", "fork_rat", "spoon_rat", "fake_box",
                "sink_valve", "sink_water_jet", "boss_box",
                "monterey_jack", "water_rabbit"):
        manifest[key] = write_category(key, categories[key], out)
    (out / "stage_01_sprites.json").write_text(json.dumps(manifest, indent=2) + "\n")
    make_preview(out, manifest)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=CAPTURE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT / "sprites")
    args = ap.parse_args()
    build(args.raw, args.out)


if __name__ == "__main__":
    main()

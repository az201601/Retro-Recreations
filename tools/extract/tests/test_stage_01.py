"""ROM-layout, layer-composition, transfer-frame, GML and capture tests.

Run: python3 -m unittest discover -s tools/extract/tests -v
No GameMaker project is built or required. Optional tests use ignored emulator
captures when capture_stage_01.py has run in this workspace.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/extract"))
import export_stage_01_rom as rom_export
import export_stage_01_gml as gml_export
import export_stage_01_audio as audio_export
import export_stage_01_import_frames as import_frames
from nes_ppu import PpuCapture


class Stage01RomTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = rom_export.load_rom()
        cls.data = json.loads((rom_export.DEFAULT_OUT / "maps/stage_01_restaurant.json").read_text())

    def test_screen_pointer_table_and_stage_layout(self):
        self.assertEqual(rom_export.screen_offset(self.rom, 0), 528)
        self.assertEqual(rom_export.screen_offset(self.rom, 18), 4848)
        layout = self.rom[rom_export.LAYOUT_OFFSET:rom_export.LAYOUT_OFFSET + 64]
        self.assertEqual(tuple(layout[2 * 8:3 * 8]), (5, 6, 7, 5, 6, 7, 5, 6))
        self.assertEqual(tuple(layout[5 * 8:6 * 8]), (9, 10, 11, 12, 10, 13, 14, 0))
        self.assertEqual(layout[1 * 8 + 4], 2)  # boss page

    def test_collision_thresholds(self):
        self.assertEqual([rom_export.collision(i) for i in (0x93, 0x9F, 0xA0,
                                                               0xCF, 0xD0, 0xF9, 0xFF)],
                         ["none", "none", "one_way", "one_way",
                          "solid", "none", "solid"])

    def test_static_layers_recompose_exact_rom_screens(self):
        self.assertEqual(self.data["source_rom_sha256"], rom_export.ROM_SHA256)
        for name, region in self.data["regions"].items():
            with self.subTest(region=name):
                ox, oy = region["origin_world_px"]
                with Image.open(rom_export.DEFAULT_OUT / region["background"]) as img:
                    base = img.convert("RGBA")
                with Image.open(rom_export.DEFAULT_OUT / region["tileset"]) as img:
                    atlas = img.convert("RGBA")
                self.assertEqual(base.size, tuple(region["dimensions_px"]))
                for x, y, tile, category in region["placed_tiles"]:
                    self.assertEqual(category, rom_export.collision(tile))
                    source = ((tile % 16) * 16, (tile // 16) * 16)
                    cell = atlas.crop((*source, source[0] + 16, source[1] + 16))
                    base.paste(cell, (x - ox, y - oy))
                self.assertEqual(hashlib.sha256(base.tobytes()).hexdigest(),
                                 region["static_bg_sha256"])
                with Image.open(rom_export.DEFAULT_OUT / "previews" /
                                f"rom_static_{name}.png") as img:
                    composite = img.convert("RGBA")
                self.assertEqual(base.tobytes(), composite.tobytes())

    def test_prizes_are_objects_not_rom_static_tiles(self):
        regions = self.data["regions"]
        self.assertEqual([len(regions[n]["prizes"]) for n in ("seating", "kitchen", "grill")],
                         [53, 55, 33])
        self.assertEqual([len(regions[n]["objects"]) for n in
                          ("seating", "kitchen", "grill", "monterey", "water_rabbit")],
                         [12, 15, 8, 1, 1])
        self.assertEqual(regions["water_rabbit"]["objects"][0]["kind"], "water_rabbit")
        vertical = [r for r in regions["kitchen"]["prizes"] if r["vertical_spawn_flag"]]
        self.assertEqual([(p["x"], p["y"]) for p in vertical],
                         [(0x63 * 16, y * 16) for y in (0x6B, 0x6C, 0x6D)])
        self.assertEqual({p["kind"] for p in regions["grill"]["prizes"]},
                         {"crate", "crate_with_rr", "rr_collectible"})

    def test_gml_rows_preserve_rom_metatile_ids(self):
        path = gml_export.OUT / "scr_stage01_place_static.gml"
        gml = path.read_text()
        self.assertIn("tile_add(bg_restaurant_water_rabbit", gml)
        self.assertIn("global.stage01_collision_grid = ds_grid_create(128, 128);", gml)
        for name, region in self.data["regions"].items():
            for row in gml_export.dense_rows(region):
                # Each 16px grid cell is encoded exactly once; FF marks
                # wallpaper/unmapped cells (not a palette/sprite index).
                self.assertEqual(len(row), region["dimensions_px"][0] // 8)
                self.assertEqual(len(bytes.fromhex(row)), region["dimensions_px"][0] // 16)
            self.assertIn(f"tile_add(ts_restaurant_{name}", gml)

    def test_manual_sprite_frames_match_extracted_oam(self):
        root = import_frames.DEFAULT_OUT_FRAMES
        exported = json.loads((root / "manifest.json").read_text())
        source = json.loads((rom_export.DEFAULT_OUT / "sprites/stage_01_sprites.json").read_text())
        self.assertEqual(exported["source_rom_sha256"], rom_export.ROM_SHA256)
        names = {f"spr_{actor}" for actor in import_frames.FRAME_CAPS}
        names.update(f"spr_prize_{kind}" for kind in import_frames.PRIZES)
        self.assertEqual(set(exported["sprites"]), names)
        count = 0
        for actor, cap in import_frames.FRAME_CAPS.items():
            item = source[actor]
            entry = exported["sprites"][f"spr_{actor}"]
            w, h = item["cell_size"]
            self.assertEqual(entry["frames"], min(item["frames"], cap))
            self.assertEqual(entry["origin"], item["origin"])
            self.assertEqual(entry["cell_size"], [w, h])
            count += entry["frames"]
            for frame, pose in zip(entry["images"], item["poses"]):
                self.assertEqual(frame["source_pose_id"], pose["id"])
                path = root / frame["file"]
                with Image.open(path) as im, Image.open(
                        rom_export.DEFAULT_OUT / "sprites" /
                        item["strips"][pose["atlas"]]) as strip:
                    cell = pose["atlas_cell"]
                    col, row = cell % item["columns"], cell // item["columns"]
                    crop = strip.crop((col * w, row * h, (col + 1) * w, (row + 1) * h))
                    self.assertEqual((im.mode, im.size), ("RGBA", (w, h)))
                    self.assertEqual(im.tobytes(), crop.tobytes())
                    self.assertEqual(hashlib.sha256(im.tobytes()).hexdigest(),
                                     frame["rgba_sha256"])
        with Image.open(rom_export.DEFAULT_OUT / "sprites/spr_prizes_seating_strip.png") as strip:
            for i, kind in enumerate(import_frames.PRIZES):
                frame = exported["sprites"][f"spr_prize_{kind}"]["images"][0]
                with Image.open(root / frame["file"]) as im:
                    self.assertEqual(im.tobytes(), strip.crop(
                        (i * 16, 0, (i + 1) * 16, 16)).tobytes())
        self.assertEqual(len(list(root.glob("spr_*/*.png"))), count + 4)
        self.assertFalse(list(root.rglob("*.gmx")))

    def test_manual_gml_scripts_are_complete_and_have_no_missing_references(self):
        scripts = {path.stem: path.read_text() for path in
                   gml_export.OUT.glob("scr_stage01_*.gml")}
        self.assertEqual(len(scripts), 23)
        self.assertIn("scr_stage01_controller_create", scripts)
        self.assertIn("scr_stage01_player_step", scripts)
        self.assertIn("scr_stage01_spawn_actors", scripts)
        self.assertIn("scr_stage01_boss_step", scripts)
        for name, content in scripts.items():
            for reference in re.findall(r"\bscr_stage01_\w+\s*\(", content):
                target = reference.split("(")[0].strip()
                self.assertIn(target, scripts, f"{name} needs {target}")
        self.assertIn("sprite_index = spr_chip_monterey;", scripts["scr_stage01_player_step"])
        self.assertIn("if (box.is_boss)", scripts["scr_stage01_player_step"])
        self.assertIn("if (is_boss) { cx = x; cy = y - 8; feet = y; }",
                      scripts["scr_stage01_crate_step"])
        self.assertNotIn("snd_stage_clear_mix", "\n".join(scripts.values()))
        self.assertTrue((rom_export.DEFAULT_OUT / "audio/bgm_restaurant_stationary_excerpt.wav").is_file())

    def test_fceumm_palettes_and_stable_bg(self):
        test = {"seating": ("seating_opening", 11201),
                "kitchen": ("route_to_boss", 13521),
                "grill": ("route_to_boss", 15001),
                "monterey": ("route_to_boss", 16513),
                "water_rabbit": ("water_rabbit", 20701)}
        if not (rom_export.CAPTURE / "water_rabbit/ppu_20701.bin").is_file():
            self.skipTest("ignored fceumm raw captures not present")
        for region in rom_export.REGIONS:
            part, frame = test[region.name]
            parent = rom_export.CAPTURE / part
            ppu = PpuCapture.from_file(parent / f"ppu_{frame}.bin")
            self.assertEqual(ppu.rgb_palette, rom_export.RGB)
            self.assertEqual(ppu.nes_palette[:16],
                             self.rom[rom_export.PALETTES[region.name]:
                                      rom_export.PALETTES[region.name] + 16])
            good, bad, _ = rom_export.verify_capture(self.rom, region,
                parent / f"ppu_{frame}.bin", parent / f"ram_{frame}.bin")
            self.assertGreaterEqual(good, 750)
            if region.name in ("water_rabbit", "monterey"):
                self.assertEqual(bad, 0)
                # All 53,248 pixels of top 256x208 match the live PPU.
                bg = ppu.bg_image(region.page_x * 256, region.page_y * 256)
                with Image.open(rom_export.DEFAULT_OUT / "previews" /
                                f"rom_static_{region.name}.png") as img:
                    static = img.convert("RGBA")
                self.assertEqual(bg.tobytes(), static.crop((0, 0, 256, 208)).tobytes())

    def test_boss_box_contacts_on_six_hits_if_capture_present(self):
        """OAM contact is evidence, not proof of the ROM's hit routine."""
        parent = rom_export.CAPTURE / "water_rabbit"
        ram_path = parent / "ram_trace.dat"
        oam_path = parent / "oam_trace.dat"
        if not ram_path.is_file() or not oam_path.is_file():
            self.skipTest("ignored Water Rabbit RAM/OAM traces not present")
        ram, oam = ram_path.read_bytes(), oam_path.read_bytes()
        self.assertEqual((ram[:4], oam[:4]), (b"RRT1", b"OAT1"))
        f0, rw = struct.unpack_from("<II", ram, 4)
        of0, ow = struct.unpack_from("<II", oam, 4)
        self.assertEqual((f0, rw, of0, ow), (20351, 2048, 20351, 256))
        hit_frames = []
        for frame in range(20542, 29806):
            prev = ram[12 + (frame - 1 - f0) * rw + 0x3D7]
            hp = ram[12 + (frame - f0) * rw + 0x3D7]
            if 0 <= hp < prev <= 6:
                hit_frames.append(frame)
        self.assertEqual(hit_frames, [22042, 22715, 26288, 27502, 28118, 29729])
        for frame in hit_frames:
            data = oam[12 + (frame - of0) * ow:12 + (frame + 1 - of0) * ow]
            box = [(data[4 * i + 3], data[4 * i] + 1) for i in range(64)
                   if 0x8C <= data[4 * i + 1] <= 0x8F and data[4 * i] < 200]
            boss = [(data[4 * i + 3], data[4 * i] + 1) for i in range(64)
                    if data[4 * i + 1] >= 0xA0 and data[4 * i] < 200]
            self.assertTrue(box and boss)
            bounds = lambda positions: (min(x for x, _ in positions),
                                        min(y for _, y in positions),
                                        max(x for x, _ in positions) + 8,
                                        max(y for _, y in positions) + 8)
            bx0, by0, bx1, by1 = bounds(box)
            rx0, ry0, rx1, ry1 = bounds(boss)
            self.assertTrue(bx0 <= rx1 and rx0 <= bx1 and by0 <= ry1 and ry0 <= by1,
                            f"box not touching boss OAM bound at {frame}")

    def test_audio_samples_index_if_capture_present(self):
        idx = rom_export.CAPTURE / "music_idle/audio_frame_index.dat"
        if not idx.is_file():
            self.skipTest("ignored audio raw captures not present")
        first, rate, boundaries = audio_export.read_index(idx)
        self.assertEqual((first, rate, len(boundaries)), (11201, 48000, 2101))
        audio = json.loads((rom_export.DEFAULT_OUT / "audio/stage_01_audio.json").read_text())
        self.assertEqual(len(audio["clips"]), 3)
        for clip in audio["clips"]:
            path = rom_export.DEFAULT_OUT / "audio" / clip["file"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), clip["sha256"])
            self.assertFalse(clip["loop_verified"])


if __name__ == "__main__":
    unittest.main()

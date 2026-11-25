"""ROM-layout, layer-composition, GML-row and capture regression tests.

Run: python3 -m unittest discover -s tools/extract/tests -v
No emulator build is needed for static tests; optional tests use ignored captures
when capture_stage_01.py has been run in the same workspace.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unittest
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/extract"))
import export_stage_01_rom as rom_export
import export_stage_01_gml as gml_export
import export_stage_01_audio as audio_export
import export_stage_01_gmx as gmx_export
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
                base = Image.open(rom_export.DEFAULT_OUT / region["background"]).convert("RGBA")
                atlas = Image.open(rom_export.DEFAULT_OUT / region["tileset"]).convert("RGBA")
                self.assertEqual(base.size, tuple(region["dimensions_px"]))
                for x, y, tile, category in region["placed_tiles"]:
                    self.assertEqual(category, rom_export.collision(tile))
                    source = ((tile % 16) * 16, (tile // 16) * 16)
                    cell = atlas.crop((*source, source[0] + 16, source[1] + 16))
                    base.paste(cell, (x - ox, y - oy))
                self.assertEqual(hashlib.sha256(base.tobytes()).hexdigest(),
                                 region["static_bg_sha256"])
                composite = Image.open(rom_export.DEFAULT_OUT / "previews" /
                                       f"rom_static_{name}.png").convert("RGBA")
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
                # Each 16px grid cell is encoded exactly once, with FF for
                # wallpaper/unmapped cells (not a palette or sprite index).
                self.assertEqual(len(row), region["dimensions_px"][0] // 8)
                self.assertEqual(len(bytes.fromhex(row)), region["dimensions_px"][0] // 16)
            self.assertIn(f"tile_add(ts_restaurant_{name}", gml)

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
                # Every pixel of the top 256x208 region (53,248 pixels) is
                # identical between independently decoded live PPU and ROM.
                bg = ppu.bg_image(region.page_x * 256, region.page_y * 256)
                static = Image.open(rom_export.DEFAULT_OUT / "previews" /
                                    f"rom_static_{region.name}.png").convert("RGBA")
                self.assertEqual(bg.tobytes(), static.crop((0, 0, 256, 208)).tobytes())

    def test_gmx_project_resources_and_references(self):
        """Structural check only: this does not run the GameMaker compiler."""
        root = gmx_export.DEFAULT_PROJECT
        project = ET.parse(root / "Stage01Restaurant.project.gmx").getroot()
        self.assertEqual(project.tag, "assets")
        groups = {"sounds": ("sound", ".sound.gmx"),
                  "sprites": ("sprite", ".sprite.gmx"),
                  "backgrounds": ("background", ".background.gmx"),
                  "scripts": ("script", ".gml"),
                  "objects": ("object", ".object.gmx"),
                  "rooms": ("room", ".room.gmx")}
        resources = {}
        for group, (child, suffix) in groups.items():
            entries = project.findall(f"{group}/{child}")
            self.assertTrue(entries, group)
            for entry in entries:
                relative = entry.text.replace("\\", "/")
                name = Path(relative).stem if suffix == ".gml" else Path(relative).name
                if suffix == ".gml":
                    self.assertTrue(relative.endswith(".gml"), relative)
                path = root / (relative + ("" if suffix == ".gml" else suffix))
                self.assertTrue(path.is_file(), str(path))
                if suffix != ".gml":
                    ET.parse(path)
                resources[name] = path
        self.assertEqual(len(project.findall("rooms/room")), 1)
        room = ET.parse(resources["rm_stage_01_restaurant"]).getroot()
        self.assertEqual((room.findtext("width"), room.findtext("height")), ("2048", "2048"))
        self.assertEqual(room.findtext("enableViews"), "-1")
        view = room.find("views/view")
        self.assertEqual((view.get("xview"), view.get("yview"),
                          view.get("wview"), view.get("hview")),
                         ("0", "512", "256", "240"))
        self.assertEqual(room.find("instances/instance").get("objName"),
                         "obj_stage01_controller")
        self.assertEqual(len(project.findall("backgrounds/background")), 10)
        for region in self.data["regions"].values():
            for key in ("background", "tileset"):
                source = rom_export.DEFAULT_OUT / region[key]
                packaged = root / "background/images" / source.name
                self.assertEqual(hashlib.sha256(packaged.read_bytes()).hexdigest(),
                                 hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(len(project.findall("sounds/sound")), 3)
        self.assertEqual(len(project.findall("sprites/sprite")), len(gmx_export.FRAME_CAPS) + 7)
        manifest = json.loads((rom_export.DEFAULT_OUT / "sprites/stage_01_sprites.json").read_text())
        selected_frames = 0
        for name in gmx_export.FRAME_CAPS:
            sprite = ET.parse(resources[f"spr_{name}"]).getroot()
            frames = sprite.findall("frames/frame")
            source = manifest[name]
            w, h = source["cell_size"]
            self.assertEqual(len(frames), min(gmx_export.FRAME_CAPS[name], source["frames"]))
            selected_frames += len(frames)
            for i, frame in enumerate(frames):
                self.assertEqual(frame.get("index"), str(i))
                pose = source["poses"][i]
                cell, columns = pose["atlas_cell"], source["columns"]
                with Image.open(rom_export.DEFAULT_OUT / "sprites" /
                                source["strips"][pose["atlas"]]) as strip, \
                     Image.open(root / "sprites" / frame.text.replace("\\", "/")) as image:
                    self.assertEqual((image.size, image.mode), ((w, h), "RGBA"))
                    expected = strip.crop(((cell % columns) * w, (cell // columns) * h,
                                           (cell % columns + 1) * w, (cell // columns + 1) * h))
                    self.assertEqual(image.tobytes(), expected.tobytes())
        self.assertEqual(len(list((root / "sprites/images").glob("*.png"))),
                         selected_frames + 7)  # four prize cutouts and three placeholders
        for name, filename in gmx_export.SOUNDS.items():
            sound = ET.parse(resources[name]).getroot()
            packaged = root / "sound/audio" / sound.findtext("data")
            original = rom_export.DEFAULT_OUT / "audio" / filename
            self.assertEqual(hashlib.sha256(packaged.read_bytes()).hexdigest(),
                             hashlib.sha256(original.read_bytes()).hexdigest())
        for entry in project.findall("objects/object"):
            obj = ET.parse(resources[Path(entry.text).name.replace("objects\\", "")]).getroot()
            sprite = obj.findtext("spriteName")
            if sprite != "<undefined>":
                self.assertIn(sprite, resources)
            parent = obj.findtext("parentName")
            if parent != "<undefined>":
                self.assertIn(parent, resources)
            for script in re.findall(r"scr_stage01_\w+",
                                     " ".join(n.text or "" for n in obj.findall(
                                         "events/event/action/arguments/argument/string"))):
                self.assertIn(script, resources)
        for script in project.findall("scripts/script"):
            name = Path(script.text.replace("\\", "/")).stem
            compiled = resources[name].read_text()
            source = (gmx_export.SCRIPT_DIR / f"{name}.gml").read_text()
            self.assertEqual(compiled, source, f"stale packaged script {name}")
            for referenced in re.findall(r"\bscr_stage01_\w+\s*\(", compiled):
                target = referenced.split("(")[0].strip()
                self.assertIn(target, resources, f"{name} refers to missing {target}")
        self.assertIn("global.stage01_part = 5;",
                      resources["scr_stage01_controller_step"].read_text())

    def test_boss_box_contacts_on_six_hits_if_capture_present(self):
        """OAM box/boss contact is evidence, not proof of the ROM hit routine."""
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

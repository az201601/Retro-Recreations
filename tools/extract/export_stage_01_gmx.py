#!/usr/bin/env python3
"""Build a self-contained *provisional* GameMaker Studio 1.4.1760 GMX project.

Read the verified ROM map and observed sprite strips, split selected OAM poses
into individual GMS sprite frames, and package all backgrounds, initial
objects, scripts, three labeled audio references and a 2048x2048 test room.
Static artwork/placements match the ROM; interactive scripts are approximate
and the GMX cannot be launched/tested in this Linux workspace.

GMX XML structure follows the public GameMaker Studio 1.4 project format;
all PNGs/WAVs are *our own* ROM exports. No sample-project artwork or code
is copied. Always rebuild this project after editing the stage_01 GML sources.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

from export_stage_01_rom import DEFAULT_OUT, ROOT, ROM_SHA256
from export_stage_01_gml import build as build_gml, DATA

DEFAULT_PROJECT = ROOT / "gms_export"
SCRIPT_DIR = ROOT / "gms_export/scripts/stage_01"
# The strips remain the complete sampled pose references. The standalone
# project imports only curated first frames; cycling every 86 Water Rabbit
# OAM samples would include hurt/blink/occluded fragments as normal movement.
FRAME_CAPS = {
    "chip_seating": 4, "chip_kitchen": 8, "chip_grill": 6,
    "chip_monterey": 4, "chip_boss": 7, "honey_bee": 6,
    "fork_rat": 6, "spoon_rat": 7, "fake_box": 4,
    "sink_valve": 2, "sink_water_jet": 1,
    "boss_box": 4, "monterey_jack": 6, "water_rabbit": 18,
}
SOUNDS = {
    "snd_restaurant_excerpt": "bgm_restaurant_stationary_excerpt.wav",
    "snd_boss_mix_reference": "boss_water_rabbit_gameplay_mix.wav",
    "snd_stage_clear_mix": "stage_clear_gameplay_mix.wav",
}


def tag(parent: ET.Element, element_name: str, text: str | int | None = None, **attrs) -> ET.Element:
    node = ET.SubElement(parent, element_name, {k: str(v) for k, v in attrs.items()})
    if text is not None:
        node.text = str(text)
    return node


def xml_save(path: Path, root: ET.Element) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    path.write_text("<!--GameMaker Studio 1.4 GMX import. Generated; see README.-->\n"
                    + ET.tostring(root, encoding="unicode") + "\n")


def make_background(out: Path, name: str, src: Path, *, tileset: bool) -> None:
    image = Image.open(src)
    if tileset and image.size != (256, 256):
        raise ValueError(f"bad tileset dimensions for {src}")
    folder = out / "background"
    (folder / "images").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, folder / "images" / f"{name}.png")
    root = ET.Element("background")
    values = {"istileset": -1 if tileset else 0, "tilewidth": 16,
              "tileheight": 16, "tilexoff": 0, "tileyoff": 0,
              "tilehsep": 0, "tilevsep": 0, "HTile": 0, "VTile": 0}
    for key, value in values.items():
        tag(root, key, value)
    tag(tag(root, "TextureGroups"), "TextureGroup0", 0)
    tag(root, "For3D", 0)
    tag(root, "width", image.width)
    tag(root, "height", image.height)
    tag(root, "data", f"images\\{name}.png")
    xml_save(folder / f"{name}.background.gmx", root)


def make_sprite(out: Path, name: str, frames: list[Image.Image], origin: tuple[int, int]) -> None:
    if not frames:
        raise ValueError(f"no sprite frames for {name}")
    w, h = frames[0].size
    if any(im.size != (w, h) for im in frames) or not 0 <= origin[0] < w or not 0 <= origin[1] < h:
        raise ValueError(f"inconsistent sprite dimensions/origin for {name}")
    folder = out / "sprites"
    (folder / "images").mkdir(parents=True, exist_ok=True)
    # Frame caps may change on a rebuild. Remove only this sprite's generated
    # numbered frames, never unrelated images or editable source strips.
    for old in (folder / "images").glob(f"{name}_*.png"):
        if old.stem[len(name) + 1:].isdigit():
            old.unlink()
    root = ET.Element("sprite")
    for key, val in {"type": 0, "xorig": origin[0], "yorigin": origin[1],
                     "colkind": 1, "coltolerance": 0, "sepmasks": 0,
                     "bboxmode": 0, "bbox_left": 0, "bbox_right": w - 1,
                     "bbox_top": 0, "bbox_bottom": h - 1, "HTile": 0,
                     "VTile": 0}.items():
        tag(root, key, val)
    tag(tag(root, "TextureGroups"), "TextureGroup0", 0)
    tag(root, "For3D", 0)
    tag(root, "width", w)
    tag(root, "height", h)
    dest = tag(root, "frames")
    for i, img in enumerate(frames):
        filename = f"{name}_{i}.png"
        img.save(folder / "images" / filename)
        tag(dest, "frame", f"images\\{filename}", index=i)
    xml_save(folder / f"{name}.sprite.gmx", root)


def observed_sprites(out: Path, manifest: dict) -> list[str]:
    names = []
    for actor, cap in FRAME_CAPS.items():
        info = manifest[actor]
        count, (w, h), columns = info["frames"], info["cell_size"], info["columns"]
        strips = [Image.open(DEFAULT_OUT / "sprites" / filename).convert("RGBA")
                  for filename in info["strips"]]
        frames = []
        for pose in info["poses"][:min(cap, count)]:
            atlas, cell = pose["atlas"], pose["atlas_cell"]
            strip = strips[atlas]
            px, py = cell % columns * w, cell // columns * h
            frames.append(strip.crop((px, py, px + w, py + h)))
        if len(frames) != min(cap, count):
            raise ValueError(f"missing observed frames for {actor}")
        name = f"spr_{actor}"
        make_sprite(out, name, frames, tuple(info["origin"]))
        names.append(name)
    # These prizes are stamped in the NES BG plane but must be movable objects
    # in GMS. The exporter supplies approximate alpha without inventing tiles.
    prize = Image.open(DEFAULT_OUT / "sprites/spr_prizes_seating_strip.png").convert("RGBA")
    for cell, kind in enumerate(("crate", "crate_rr", "crate_acorn", "rr")):
        name = f"spr_prize_{kind}"
        make_sprite(out, name, [prize.crop((cell * 16, 0, cell * 16 + 16, 16))], (0, 0))
        names.append(name)
    # No observed OAM for these small prop visuals: clearly named placeholders.
    for kind, color in (("cork", "#A6602E"), ("acorn", "#BF8B54"), ("star", "#FFCF30")):
        img = Image.new("RGBA", (16, 16))
        draw = ImageDraw.Draw(img)
        if kind == "star":
            draw.polygon([(8, 0), (10, 5), (15, 5), (12, 9), (13, 15),
                          (8, 12), (3, 15), (4, 9), (1, 5), (6, 5)], fill=color)
        elif kind == "acorn":
            draw.ellipse((4, 6, 12, 15), fill=color)
            draw.rectangle((3, 5, 13, 8), fill="#683823")
        else:
            draw.rounded_rectangle((2, 5, 14, 13), radius=2, fill=color)
        name = f"spr_placeholder_{kind}"
        make_sprite(out, name, [img], (0, 0))
        names.append(name)
    return names


def make_sound(out: Path, name: str, filename: str) -> None:
    folder = out / "sound"
    (folder / "audio").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DEFAULT_OUT / "audio" / filename, folder / "audio" / filename)
    root = ET.Element("sound")
    for key, val in (("kind", 0), ("extension", ".wav"),
                     ("origname", f"sound\\audio\\{filename}"), ("effects", 0)):
        tag(root, key, val)
    tag(tag(root, "volume"), "volume", 1)
    tag(root, "pan", 0)
    tag(tag(root, "bitRates"), "bitRate", 192)
    tag(tag(root, "sampleRates"), "sampleRate", 48000)
    tag(tag(root, "types"), "type", 0)
    tag(tag(root, "bitDepths"), "bitDepth", 16)
    for key, val in (("preload", -1), ("data", filename), ("compressed", 0),
                     ("streamed", 0), ("uncompressOnLoad", 0), ("audioGroup", 0)):
        tag(root, key, val)
    xml_save(folder / f"{name}.sound.gmx", root)


def action(parent: ET.Element, event_type: int, enum: int, code: str) -> None:
    event = tag(parent, "event", eventtype=event_type, enumb=enum)
    a = tag(event, "action")
    for key, val in (("libid", 1), ("id", 603), ("kind", 7),
                     ("userelative", 0), ("isquestion", 0), ("useapplyto", -1),
                     ("exetype", 2), ("functionname", ""), ("codestring", ""),
                     ("whoName", "self"), ("relative", 0), ("isnot", 0)):
        tag(a, key, val)
    tag(tag(tag(a, "arguments"), "argument"), "kind", 1)
    # A second sibling under the same argument, not under <kind>.
    argument = a.find("arguments/argument")
    tag(argument, "string", code + "\n")


def make_object(out: Path, name: str, *, sprite: str | None = None,
                parent: str | None = None, depth: int = 0, visible: bool = True,
                events: list[tuple[int, int, str]] = ()) -> None:
    root = ET.Element("object")
    for key, val in (("spriteName", sprite or "<undefined>"), ("solid", 0),
                     ("visible", -1 if visible else 0), ("depth", depth),
                     ("persistent", 0), ("parentName", parent or "<undefined>"),
                     ("maskName", "<undefined>")):
        tag(root, key, val)
    ev = tag(root, "events")
    for event_type, enum, code in events:
        action(ev, event_type, enum, code)
    for key, val in (("PhysicsObject", 0), ("PhysicsObjectSensor", 0),
                     ("PhysicsObjectShape", 0), ("PhysicsObjectDensity", 0.5),
                     ("PhysicsObjectRestitution", 0.1), ("PhysicsObjectGroup", 0),
                     ("PhysicsObjectLinearDamping", 0.1),
                     ("PhysicsObjectAngularDamping", 0.1),
                     ("PhysicsObjectFriction", 0.2), ("PhysicsObjectAwake", -1),
                     ("PhysicsObjectKinematic", 0)):
        tag(root, key, val)
    tag(root, "PhysicsShapePoints")
    xml_save(out / "objects" / f"{name}.object.gmx", root)


def script_call(name: str) -> str:
    return f"{name}();"


def make_objects(out: Path) -> list[str]:
    objects = {
        "obj_stage01_controller": (None, None, 0, True, [
            (0, 0, script_call("scr_stage01_controller_create")),
            (3, 0, script_call("scr_stage01_controller_step")),
            (8, 64, script_call("scr_stage01_controller_draw_gui")),
            (7, 5, "ds_grid_destroy(global.stage01_collision_grid);")]),
        "obj_player": ("spr_chip_seating", None, -100, True, [
            (0, 0, script_call("scr_stage01_player_create")),
            (3, 0, script_call("scr_stage01_player_step"))]),
        "obj_crate": ("spr_prize_crate", None, -50, True, [
            (0, 0, script_call("scr_stage01_crate_create")),
            (3, 0, script_call("scr_stage01_crate_step"))]),
        "obj_boss_box": ("spr_boss_box", "obj_crate", -40, True, []),
        "obj_rre": ("spr_prize_rr", None, -40, True, [
            (3, 0, "scr_stage01_pickup_step(0);")]),
        "obj_acorn": ("spr_placeholder_acorn", None, -40, True, [
            (3, 0, "scr_stage01_pickup_step(1);")]),
        "obj_stage01_enemy": (None, None, -10, True, [
            (0, 0, script_call("scr_stage01_enemy_create")),
            (3, 0, script_call("scr_stage01_enemy_step"))]),
        "obj_enemy_honeybee": ("spr_honey_bee", "obj_stage01_enemy", -10, True, []),
        "obj_enemy_fork_rat": ("spr_fork_rat", "obj_stage01_enemy", -10, True, []),
        "obj_enemy_spoon_rat": ("spr_spoon_rat", "obj_stage01_enemy", -10, True, []),
        "obj_enemy_fake_box": ("spr_fake_box", "obj_stage01_enemy", -10, True, []),
        "obj_enemy_bottle_cork": ("spr_placeholder_cork", "obj_stage01_enemy", -10, True, []),
        "obj_stage01_exit_right": (None, None, 0, False, []),
        "obj_star_prize": ("spr_placeholder_star", None, -10, True, [
            (3, 0, "scr_stage01_pickup_step(0);")]),
        "obj_zipper_in_box": ("spr_prize_crate", None, -10, True, []),
        "obj_sink_valve": ("spr_sink_valve", None, -10, True, [
            (0, 0, "image_speed = 0.05;"),
            (3, 0, script_call("scr_stage01_sink_step"))]),
        "obj_sink_water_jet": ("spr_sink_water_jet", None, -15, True, [
            (3, 0, script_call("scr_stage01_jet_step"))]),
        "obj_monterey_refill": ("spr_monterey_jack", None, -10, True, [
            (0, 0, "image_speed = 0.10;")]),
        "obj_boss_water_rabbit": ("spr_water_rabbit", None, -10, True, [
            (0, 0, script_call("scr_stage01_boss_create")),
            (3, 0, script_call("scr_stage01_boss_step"))]),
    }
    for name, (sprite, parent, depth, visible, events) in objects.items():
        make_object(out, name, sprite=sprite, parent=parent, depth=depth,
                    visible=visible, events=events)
    return list(objects)


def make_room(out: Path) -> None:
    root = ET.Element("room")
    for key, val in (("caption", "Stage 01: The Restaurant (prototype)"),
                     ("width", 2048), ("height", 2048), ("vsnap", 16),
                     ("hsnap", 16), ("isometric", 0), ("speed", 60),
                     ("persistent", 0), ("colour", 0), ("showcolour", -1),
                     ("code", ""), ("enableViews", -1),
                     ("clearViewBackground", -1), ("clearDisplayBuffer", -1)):
        tag(root, key, val)
    settings = tag(root, "makerSettings")
    for key in ("isSet", "w", "h", "showGrid", "showObjects", "showTiles",
                "showBackgrounds", "showForegrounds", "showViews",
                "deleteUnderlyingObj", "deleteUnderlyingTiles", "page",
                "xoffset", "yoffset"):
        tag(settings, key, 0)
    backgrounds = tag(root, "backgrounds")
    for _ in range(8):
        tag(backgrounds, "background", visible=0, foreground=0, name="",
            x=0, y=0, htiled=-1, vtiled=-1, hspeed=0, vspeed=0, stretch=0)
    views = tag(root, "views")
    for i in range(8):
        tag(views, "view", visible=-1 if i == 0 else 0, objName="<undefined>",
            xview=0, yview=512, wview=256, hview=240,
            xport=0, yport=0, wport=512, hport=480,
            hborder=32, vborder=32, hspeed=-1, vspeed=-1)
    instances = tag(root, "instances")
    tag(instances, "instance", objName="obj_stage01_controller", x=0, y=0,
        name="inst_00000001", locked=0, code="", scaleX=1, scaleY=1,
        colour=4294967295, rotation=0)
    tag(root, "tiles")
    for key, val in (("PhysicsWorld", 0), ("PhysicsWorldTop", 0),
                     ("PhysicsWorldLeft", 0), ("PhysicsWorldRight", 2048),
                     ("PhysicsWorldBottom", 2048), ("PhysicsWorldGravityX", 0),
                     ("PhysicsWorldGravityY", 10), ("PhysicsWorldPixToMeters", 0.1)):
        tag(root, key, val)
    xml_save(out / "rooms/rm_stage_01_restaurant.room.gmx", root)


def make_config(out: Path) -> None:
    root = ET.Element("Config")
    options = tag(root, "Options")
    # Common GMS 1.4 options; missing platform-specific entries are filled by
    # GameMaker defaults when the project is opened. Windows is the test target.
    for key, val in (("option_gameguid", "{E291CA02-05FA-480B-9DD1-91A4FBA40657}"),
                     ("option_gameid", 304011761),
                     ("option_display_name", "Stage 01 Restaurant prototype"),
                     ("option_interpolate", "False"),
                     ("option_windows_texture_page", 2048),
                     ("option_windows_use_splash", "False"),
                     ("option_windows_game_icon", "Configs\\Default\\windows\\runner_icon.ico"),
                     ("option_scale", -1),
                     ("option_textureGroup_count", 1),
                     ("option_textureGroups0", "Default")):
        tag(options, key, val)
    xml_save(out / "Configs/Default.config.gmx", root)
    icon = Image.new("RGB", (32, 32), "#121217")
    prize = Image.open(DEFAULT_OUT / "sprites/spr_prizes_seating_strip.png").convert("RGBA")
    icon.paste(prize.crop((0, 0, 16, 16)).resize((28, 28), Image.Resampling.NEAREST),
               (2, 2), prize.crop((0, 0, 16, 16)).resize((28, 28), Image.Resampling.NEAREST))
    icon_path = out / "Configs/Default/windows/runner_icon.ico"
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    icon.save(icon_path, format="ICO", sizes=[(32, 32)])
    (out / "help.rtf").write_text(
        r"{\rtf1\ansi Stage 01 Restaurant (NES to GMS 1.4). ROM scenery exact; "
        r"play controls and boss pattern experimental. Read docs/STAGE_01_RESTAURANT.md.}")


def make_project(out: Path, sprites: list[str], bgs: list[str],
                 sounds: list[str], scripts: list[str], objects: list[str]) -> None:
    root = ET.Element("assets")
    tag(tag(root, "Configs", name="configs"), "Config", "Configs\\Default")
    tag(root, "NewExtensions")
    collections = (("sounds", "sound", sounds, "sound"),
                   ("sprites", "sprite", sprites, "sprites"),
                   ("backgrounds", "background", bgs, "background"),
                   ("paths", "path", [], "paths"),
                   ("scripts", "script", scripts, "scripts"),
                   ("fonts", "font", [], "fonts"),
                   ("objects", "object", objects, "objects"),
                   ("rooms", "room", ["rm_stage_01_restaurant"], "rooms"))
    for group, child, names, folder in collections:
        parent = tag(root, group, name=folder)
        for name in names:
            # GMX lists scripts by their actual .gml filenames; object,
            # sprite and room resource entries omit their .*.gmx suffix.
            suffix = ".gml" if child == "script" else ""
            tag(parent, child, f"{folder}\\{name}{suffix}")
    tag(tag(root, "help"), "rtf", "help.rtf")
    state = tag(root, "TutorialState")
    for key, val in (("IsTutorial", 0), ("TutorialName", ""), ("TutorialPage", 0)):
        tag(state, key, val)
    xml_save(out / "Stage01Restaurant.project.gmx", root)


def build(out: Path = DEFAULT_PROJECT, map_path: Path = DATA) -> dict:
    data = json.loads(map_path.read_text())
    if data["source_rom_sha256"] != ROM_SHA256:
        raise ValueError("wrong ROM map: run export_stage_01_rom.py first")
    manifest = json.loads((DEFAULT_OUT / "sprites/stage_01_sprites.json").read_text())
    if manifest.get("source") != "fceumm mapped PPU/OAM + RGB captures from capture_stage_01.py":
        raise ValueError("unrecognized OAM manifest: run export_stage_01_sprites.py")
    build_gml(map_path, SCRIPT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    bgs = []
    for region, info in data["regions"].items():
        for key in ("background", "tileset"):
            name = Path(info[key]).stem
            make_background(out, name, DEFAULT_OUT / info[key], tileset=key == "tileset")
            bgs.append(name)
    sprites = observed_sprites(out, manifest)
    for name, filename in SOUNDS.items():
        make_sound(out, name, filename)
    objects = make_objects(out)
    make_room(out)
    make_config(out)
    (out / "scripts").mkdir(exist_ok=True)
    scripts = []
    for src in sorted(SCRIPT_DIR.glob("scr_stage01_*.gml")):
        shutil.copyfile(src, out / "scripts" / src.name)
        scripts.append(src.stem)
    make_project(out, sprites, bgs, list(SOUNDS), scripts, objects)
    return {"backgrounds": len(bgs), "sprites": len(sprites), "objects": len(objects),
            "scripts": len(scripts), "sound_references": len(SOUNDS)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_PROJECT)
    ap.add_argument("--map", type=Path, default=DATA)
    args = ap.parse_args()
    print(build(args.out, args.map))


if __name__ == "__main__":
    main()

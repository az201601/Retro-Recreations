#!/usr/bin/env python3
"""Split observed Stage 01 sprite strips into PNG frames for MANUAL GMS import.

This creates images and a manifest only. It never creates a .project.gmx,
room, object, sprite resource, audio resource, or a copy of the user's project.
Each spr_*/ folder is a ready-to-import frame sequence with an explicit origin.
The original OAM strips/pose manifest remain the source of truth; these first
frames are curated to avoid automatically cycling rare blink/hurt fragments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from export_stage_01_rom import DEFAULT_OUT, ROM_SHA256

SPRITES = DEFAULT_OUT / "sprites"
DEFAULT_OUT_FRAMES = SPRITES / "import_frames"
# Order = descending frequency in stage_01_sprites.json. These are only the
# initial normal-looking poses for convenient import, not verified animation
# sequences or claims that unobserved frames don't exist.
FRAME_CAPS = {
    "chip_seating": 4, "chip_kitchen": 8, "chip_grill": 6,
    "chip_monterey": 4, "chip_boss": 7, "honey_bee": 6,
    "fork_rat": 6, "spoon_rat": 7, "fake_box": 4,
    "sink_valve": 2, "sink_water_jet": 1,
    "boss_box": 4, "monterey_jack": 6, "water_rabbit": 18,
}
PRIZES = ("crate", "crate_rr", "crate_acorn", "rr")


def save_frames(directory: Path, frames: list[Image.Image], source: str,
                origin: tuple[int, int], pose_ids: list[int]) -> dict:
    if not frames:
        raise ValueError(f"missing frames for {directory.name}")
    directory.mkdir(parents=True, exist_ok=True)
    # Only remove the numbered files this exporter owns; never alter an
    # artist's other PNGs alongside them or the original OAM strip.
    for old in directory.glob("*.png"):
        if old.stem.isdigit():
            old.unlink()
    w, h = frames[0].size
    if any(frame.size != (w, h) or frame.mode != "RGBA" for frame in frames):
        raise ValueError(f"inconsistent dimensions/mode in {directory}")
    if not (0 <= origin[0] < w and 0 <= origin[1] < h):
        raise ValueError(f"origin outside sprite: {directory.name}")
    files = []
    for index, frame in enumerate(frames):
        filename = f"{index:03d}.png"
        frame.save(directory / filename)
        files.append({"file": f"{directory.name}/{filename}", "source_pose_id": pose_ids[index],
                      "rgba_sha256": hashlib.sha256(frame.tobytes()).hexdigest()})
    return {"frames": len(frames), "cell_size": [w, h], "origin": list(origin),
            "source_strip": source, "images": files}


def build(out: Path = DEFAULT_OUT_FRAMES) -> dict:
    manifest = json.loads((SPRITES / "stage_01_sprites.json").read_text())
    if manifest.get("source") != "fceumm mapped PPU/OAM + RGB captures from capture_stage_01.py":
        raise ValueError("run export_stage_01_sprites.py from the verified ROM captures first")
    out.mkdir(parents=True, exist_ok=True)
    data = {"format": "Stage 01 manually importable sprite frames 1",
            "source_rom_sha256": ROM_SHA256,
            "note": "Curated OAM observations, NOT a complete state machine or prebuilt GMS project."
                    " Full pose strips and metadata are in sprites/stage_01_sprites.json.",
            "sprites": {}}
    for actor, cap in FRAME_CAPS.items():
        info = manifest[actor]
        w, h = info["cell_size"]
        cols = info["columns"]
        strips = []
        for filename in info["strips"]:
            with Image.open(SPRITES / filename) as image:
                strips.append(image.convert("RGBA"))
        poses = info["poses"][:min(info["frames"], cap)]
        frames = []
        for pose in poses:
            cell, atlas = pose["atlas_cell"], pose["atlas"]
            left, top = cell % cols * w, cell // cols * h
            frames.append(strips[atlas].crop((left, top, left + w, top + h)))
        name = f"spr_{actor}"
        data["sprites"][name] = save_frames(out / name, frames,
            ", ".join(info["strips"]), tuple(info["origin"]), [p["id"] for p in poses])
    with Image.open(SPRITES / "spr_prizes_seating_strip.png") as image:
        prize_strip = image.convert("RGBA")
    if prize_strip.size != (64, 16):
        raise ValueError("expected four 16x16 NES BG prize cells")
    for i, kind in enumerate(PRIZES):
        name = f"spr_prize_{kind}"
        frame = prize_strip.crop((i * 16, 0, (i + 1) * 16, 16))
        data["sprites"][name] = save_frames(out / name, [frame],
            "spr_prizes_seating_strip.png (approximate alpha)", (0, 0), [i])
    (out / "manifest.json").write_text(json.dumps(data, indent=2) + "\n")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_FRAMES)
    args = parser.parse_args()
    data = build(args.out)
    print("Exported", sum(v["frames"] for v in data["sprites"].values()),
          "PNG frames in", len(data["sprites"]), "manual sprite folders:", args.out)


if __name__ == "__main__":
    main()

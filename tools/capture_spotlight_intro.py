#!/usr/bin/env python3
"""Capture the game's boot/spotlight intro as native-resolution GMS sprite strips.

Requires the ignored tools/emu/retroshot + FCEUmm build (see tools/README.md)
and Pillow. Output is a sequence of 8x8 atlases of 256x240 frames, directly
importable through the GMS 1.4 Sprite Editor's Add from Strip workflow.
"""
from __future__ import annotations

import argparse
import csv
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EMU = ROOT / "tools" / "emu"
ROM = ROOT / "Chip 'n Dale - Rescue Rangers 2 (USA).nes"
CAPTURE_DIR = ROOT / "tools" / "out" / "spotlight_intro"
ASSET_DIR = ROOT / "extracted" / "spotlight_intro"
FRAME_W, FRAME_H = 256, 240
GRID_COLS, GRID_ROWS = 8, 8
FRAMES_PER_ATLAS = GRID_COLS * GRID_ROWS


def capture(first: int, last: int, max_events: int = 400) -> list[tuple[int, Path]]:
    """Run clean from power-on and capture inclusive frames first..last."""
    captured = []
    # Each screenshot is one timeline event; keep well below retroshot's
    # 512-event limit. Every segment replays from power-on for deterministic
    # startup state, then saves only its requested range.
    for lo in range(first, last + 1, max_events):
        hi = min(last, lo + max_events - 1)
        timeline_lines = [f"{frame} shot f{frame:04d}" for frame in range(lo, hi + 1)]
        timeline_lines.append(f"{hi + 1} quit")
        with tempfile.NamedTemporaryFile("w", encoding="ascii", suffix=".txt", delete=False) as f:
            f.write("\n".join(timeline_lines) + "\n")
            timeline = Path(f.name)
        try:
            cmd = [
                str(EMU / "retroshot"),
                "-c", "libretro-fceumm/fceumm_libretro.so",
                "-r", str(ROM),
                "-t", str(timeline),
                "-o", str(CAPTURE_DIR),
                "-m", str(hi + 1),
            ]
            subprocess.run(cmd, cwd=EMU, check=True)
        finally:
            timeline.unlink(missing_ok=True)
        captured.extend((frame, CAPTURE_DIR / f"f{frame:04d}.ppm") for frame in range(lo, hi + 1))
    return captured


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=int, default=1, help="first rendered emulator frame (default: 1)")
    parser.add_argument("--last", type=int, default=900, help="last rendered emulator frame (default: 900)")
    parser.add_argument("--capture-only", action="store_true", help="leave native PPM captures in tools/out")
    args = parser.parse_args()
    if args.first < 1 or args.last < args.first:
        parser.error("frame range must satisfy 1 <= first <= last")
    if not (EMU / "retroshot").exists() or not (EMU / "libretro-fceumm" / "fceumm_libretro.so").exists():
        parser.error("emulator not built; follow tools/README.md first")
    if not ROM.exists():
        parser.error(f"ROM not found: {ROM}")

    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    frames = capture(args.first, args.last)
    if args.capture_only:
        print(f"Captured {len(frames)} frames in {CAPTURE_DIR}")
        return

    atlas_w, atlas_h = GRID_COLS * FRAME_W, GRID_ROWS * FRAME_H
    atlas_total = math.ceil(len(frames) / FRAMES_PER_ATLAS)
    manifest = ASSET_DIR / "frame_map.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["sequence_frame", "nes_frame", "atlas_file", "cell_column", "cell_row"])
        for atlas_idx in range(atlas_total):
            group = frames[atlas_idx * FRAMES_PER_ATLAS:(atlas_idx + 1) * FRAMES_PER_ATLAS]
            rows = math.ceil(len(group) / GRID_COLS)
            # Crop the final sheet to the used cells, preventing blank atlas
            # cells from becoming extra animation frames when imported.
            sheet = Image.new("RGB", (atlas_w, rows * FRAME_H), (0, 0, 0))
            for cell_idx, (nes_frame, source) in enumerate(group):
                image = Image.open(source).convert("RGB")
                if image.size != (FRAME_W, FRAME_H):
                    raise ValueError(f"unexpected frame dimensions in {source}: {image.size}")
                col, row = cell_idx % GRID_COLS, cell_idx // GRID_COLS
                sheet.paste(image, (col * FRAME_W, row * FRAME_H))
                writer.writerow([atlas_idx * FRAMES_PER_ATLAS + cell_idx, nes_frame,
                                 f"spotlight_{atlas_idx:02d}.png", col, row])
            # All full atlases use 8x8 cells; partial final atlas is tightly
            # cropped and still imports as a regular grid of 256x240 frames.
            out = ASSET_DIR / f"spotlight_{atlas_idx:02d}.png"
            sheet.save(out, optimize=True)
            print(f"{out.relative_to(ROOT)}: {len(group)} frames, {sheet.width}x{sheet.height}")

    print(f"Frame mapping: {manifest.relative_to(ROOT)}")
    print(f"Captured source frames {args.first}..{args.last} ({len(frames)} total).")
    print("GMS 1.4 strip-import cell size: 256x240; read each atlas left-to-right, top-to-bottom.")


if __name__ == "__main__":
    main()

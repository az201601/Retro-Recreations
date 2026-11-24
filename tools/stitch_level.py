#!/usr/bin/env python3
"""Stitch captured camera windows into one wide level strip.

Each checkpoint savestate is re-entered in the emulator, advanced by one frame,
and then both a savestate and a frame are written *from that same frame*.  That
order matters: a frame grabbed after a bare ``load`` shows whatever was last
rendered, not the state that was loaded, which silently produced captures whose
picture and savestate disagreed.

The window is then re-rendered from the savestate (sprites stripped) and placed
at its absolute camera position.  Overlaps favour pixels outside the PPU's
clipped left-hand column, so seams show real background.

The wide image is re-tiled: every unique 8x8 cell becomes a tileset entry and a
wide tilemap is written.  That output maps directly onto a GMS 1.4 room (one
background asset plus one tile layer) and does not depend on how the NES packed
its CHR banks or nametable pages.

Usage:
  python3 tools/stitch_level.py --states DIR --rom ROM --out DIR
``DIR`` is a solver work directory: checkpoints live in ``DIR/checkpoints`` and
are named ``cam_<worldx>.fcs``.  Non-checkpoint states may also be passed with
``--state``.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from PIL import Image

from autoplay import Retroshot
from nes_state import FCEUMM_CLASSIC_PALETTE, SCREEN_H, SCREEN_W, load_state


def camera_xy(st) -> tuple[int, int]:
    """Camera position in pixels.

    X uses both nametable pages (``ppuctrl & 3`` selects the base page and wraps
    every 512 px). Y is a single 240-px page, because the cartridge uses
    vertical mirroring, so a stage that is taller than one screen scrolls Y
    round in a loop and the caller must unwrap it against its neighbour.
    """
    cx, fx, cy = st.scroll()
    return ((st.ppuctrl & 3) * 256 + cx * 8 + fx, cy * 8)


def learn_palette(st, frame: Path) -> dict[int, tuple[int, int, int]]:
    """Index -> RGB, fitted only on background pixels of a matched frame.

    Sprites are excluded because they can move between the state and the
    capture; the background cannot, so it pins the palette exactly.
    """
    palette = {i: FCEUMM_CLASSIC_PALETTE[i] for i in range(64)}
    indices, _, _ = st.frame_indices(with_sprites=True)
    mask = st.sprite_mask()
    fpx = Image.open(frame).convert("RGB").load()
    seen: dict[int, dict[tuple[int, int, int], int]] = {}
    for y in range(SCREEN_H):
        mrow, irow = mask[y], indices[y]
        for x in range(SCREEN_W):
            if mrow[x]:
                continue
            colour = irow[x] & 0x3F
            bucket = seen.setdefault(colour, {})
            bucket[fpx[x, y]] = bucket.get(fpx[x, y], 0) + 1
    for colour, vals in seen.items():
        palette[colour] = max(vals.items(), key=lambda kv: kv[1])[0]
    return palette


def normalise(emu: Retroshot, state: Path, out: Path) -> tuple[Path, Path]:
    """Re-enter a state and capture a matching savestate + frame pair."""
    emu.load(state)
    emu.run(1)
    emu.save(out)
    emu.screenshot(out)
    return out.with_suffix(".fcs"), out.with_suffix(".ppm")


def render_window(st, palette, show_clipped: bool = False) -> Image.Image:
    """Render the visible window.

    ``show_clipped`` reveals the two columns the PPU hides at the left edge.
    The level still has tiles there -- the hardware just does not display them
    -- which is exactly what a wide map wants at the start of the stage.
    """
    full = [palette[i] for i in range(64)]
    backdrop = palette[st.pram[0] & 0x3F]
    pixels = st.render_rgb(full, backdrop, sprites=False,
                           show_clipped=show_clipped)
    img = Image.new("RGB", (SCREEN_W, SCREEN_H))
    img.putdata(pixels)
    return img


def verify_window(img: Image.Image, st, frame: Path) -> tuple[int, list[list[bool]]]:
    """Compare a render against its capture and return an per-pixel validity map.

    OAM is copied to the PPU part-way through a frame, so the savestate holds
    the sprite table for the *next* frame while the picture shows the previous
    one.  Pixels where the two disagree are therefore treated as unreliable
    rather than as background, and a neighbouring window supplies them.
    """
    fpx = Image.open(frame).convert("RGB").load()
    px = img.load()
    mask = st.sprite_mask()
    diff = 0
    valid = [[True] * SCREEN_W for _ in range(SCREEN_H)]
    for y in range(SCREEN_H):
        for x in range(SCREEN_W):
            if mask[y][x]:
                valid[y][x] = False
            elif px[x, y] != fpx[x, y]:
                valid[y][x] = False
                diff += 1
    return diff, valid


def stitch(items, rom: Path, work: Path) -> tuple[Image.Image, list, dict]:
    emu = Retroshot(rom, work)
    norm_dir = work / "normalised"
    norm_dir.mkdir(exist_ok=True)
    windows = []
    palette = None
    try:
        for cam_name, state in items:
            fcs, ppm = normalise(emu, state, norm_dir / f"norm_{cam_name}")
            st = load_state(fcs, rom)
            if palette is None:
                palette = learn_palette(st, ppm)
            cam_x, cam_y = camera_xy(st)
            windows.append({"name": cam_name, "state": fcs, "frame": ppm,
                            "cam_x_mod": cam_x, "cam_y_mod": cam_y, "st": st})
    finally:
        emu.close()

    # Both axes wrap; unwrap along the capture order so the windows line up in
    # one world map. X wraps every 512 px, Y every 240.
    prev_x = prev_y = None
    for w in windows:
        cam_x, cam_y = w["cam_x_mod"], w["cam_y_mod"]
        if prev_x is not None:
            while cam_x < prev_x - 128:
                cam_x += 512
            while cam_x > prev_x + 384:
                cam_x -= 512
        if prev_y is not None:
            while cam_y < prev_y - 60:
                cam_y += 240
            while cam_y > prev_y + 180:
                cam_y -= 240
        w["cam"], w["camy"] = cam_x, cam_y
        prev_x, prev_y = cam_x, cam_y

    min_y = min(0, min(w["camy"] for w in windows))
    total_w = max(w["cam"] for w in windows) + SCREEN_W
    total_h = max(w["camy"] for w in windows) + SCREEN_H - min_y
    canvas = Image.new("RGB", (total_w, total_h), (0, 0, 0))
    covered = [[False] * total_w for _ in range(total_h)]
    reports = []
    for w in windows:
        st = w["st"]
        img = render_window(st, palette)
        diff, valid = verify_window(img, st, w["frame"])
        w["img"], w["valid"] = img, valid
        w["img_full"] = render_window(st, palette, show_clipped=True)
        left_clipped = not (st.ppumask & 0x02)
        reports.append({"name": w["name"], "cam": w["cam"], "camy": w["camy"],
                        "left_column_clipped": left_clipped,
                        "bg_pixel_differences_outside_sprites": diff})
        px = img.load()
        x0 = 8 if left_clipped else 0
        for y in range(SCREEN_H):
            dy = w["camy"] - min_y + y
            if not (0 <= dy < total_h):
                continue
            for sx in range(x0, SCREEN_W):
                if not valid[y][sx]:
                    continue
                x = w["cam"] + sx
                if 0 <= x < total_w:
                    canvas.putpixel((x, dy), px[sx, y])
                    covered[dy][x] = True

    # Anything still unset sits under a sprite in every window that covers it.
    # Fall back to the nearest window: the level itself is static, so the
    # render is right even where the capture was overlaid by a moving object.
    filled = 0
    for y in range(total_h):
        row = covered[y]
        for x in range(total_w):
            if row[x]:
                continue
            cx_world, cy_world = x - SCREEN_W // 2, y - SCREEN_H // 2 + min_y
            best = min(windows, key=lambda w: abs(w["cam"] - cx_world)
                       + abs(w["camy"] - cy_world))
            sx, sy = x - best["cam"], y - (best["camy"] - min_y)
            if 0 <= sx < SCREEN_W and 0 <= sy < SCREEN_H:
                # img_full is used here so the hidden left column gets the real
                # nametable content instead of a blank gap.
                canvas.putpixel((x, y), best["img_full"].load()[sx, sy])
                filled += 1
    gaps = sum(1 for y in range(total_h) for x in range(total_w) if not covered[y][x])
    meta = {"windows": reports, "uncovered_before_fill": gaps,
            "filled_from_nearest_window": filled,
            "palette": {str(k): list(v) for k, v in (palette or {}).items()}}
    return canvas, reports, meta


def build_tileset(level: Image.Image, tileset_path: Path, tilemap_path: Path,
                  tiles_csv: Path):
    w, h = level.size
    cols, rows = w // 8, h // 8
    px = level.load()
    lookup: dict[bytes, int] = {}
    raws: list[bytes] = []
    grid: list[list[int]] = []
    for ty in range(rows):
        line = []
        for tx in range(cols):
            raw = bytes(c for y in range(8) for x in range(8)
                        for c in px[tx * 8 + x, ty * 8 + y])
            if all(b == 0 for b in raw):
                line.append(-1)
                continue
            idx = lookup.get(raw)
            if idx is None:
                idx = len(raws)
                lookup[raw] = idx
                raws.append(raw)
            line.append(idx)
        grid.append(line)

    per_row = 16
    sheet_rows = max(1, math.ceil(len(raws) / per_row))
    sheet = Image.new("RGB", (per_row * 8, sheet_rows * 8), (0, 0, 0))
    spx = sheet.load()
    for idx, raw in enumerate(raws):
        cx, cy = (idx % per_row) * 8, (idx // per_row) * 8
        for y in range(8):
            for x in range(8):
                o = (y * 8 + x) * 3
                spx[cx + x, cy + y] = (raw[o], raw[o + 1], raw[o + 2])
    sheet.save(tileset_path, optimize=True)

    from collections import Counter
    counts = Counter(v for row in grid for v in row if v >= 0)
    with tilemap_path.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow([f"c{i}" for i in range(cols)])
        wr.writerows(grid)
    with tiles_csv.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(["cell", "cell_x", "cell_y", "count"])
        for idx in range(len(raws)):
            wr.writerow([idx, idx % per_row, idx // per_row, counts[idx]])
    return len(raws), cols, rows, sheet.size


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", required=True,
                    help="solver work directory containing checkpoints/")
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", action="append", default=[],
                    help="extra savestate to include, e.g. the level entrance")
    args = ap.parse_args()

    work = Path(args.workdir).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rom = Path(args.rom).resolve()

    states = sorted((work / "checkpoints").glob("cam_*.fcs"))
    if not states:
        raise SystemExit(f"no cam_*.fcs in {work / 'checkpoints'}")
    items = [("start_" + Path(p).stem, Path(p).resolve()) for p in args.start]
    items += [(p.stem, p) for p in states]

    level, reports, meta = stitch(items, rom, work)
    # Tile-align the strip: a partial 8-pixel column cannot be expressed in a
    # tilemap, so trim rather than ship a map that silently drops pixels.
    aligned = (level.width // 8) * 8
    if aligned != level.width:
        level = level.crop((0, 0, aligned, level.height))
    level.save(out / "level.png", optimize=True)
    unique, cols, rows, sheet_size = build_tileset(
        level, out / "tileset.png", out / "tilemap.csv", out / "tiles.csv")

    worst = max((r["bg_pixel_differences_outside_sprites"] for r in reports),
                default=0)
    doc = {
        "source_workdir": str(work),
        "windows": reports,
        "width_px": level.width,
        "height_px": level.height,
        "vertical_scroll_used": any(w["camy"] != 0 for w in reports),
        "uncovered_before_fill": meta["uncovered_before_fill"],
        "filled_from_nearest_window": meta["filled_from_nearest_window"],
        "max_background_pixel_error": worst,
        "unique_tiles": unique,
        "tilemap": {"cols": cols, "rows": rows},
        "tileset_size": list(sheet_size),
        "notes": [
            "level.png is the background layer only (no sprites), 1:1 NES pixels.",
            "tilemap.csv indexes 8x8 cells in tileset.png, 16 cells per row.",
            "-1 means empty (transparent / backdrop).",
            "Overlaps prefer pixels outside the PPU's clipped left 8-pixel column.",
            "Windows were re-captured from their savestates, so picture and state agree.",
        ],
    }
    (out / "level.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"{out}: {level.width}x{level.height} from {len(reports)} windows, "
          f"{unique} unique tiles, {meta['uncovered_before_fill']} uncovered pixels")
    print(f"  max background pixel error per window: {worst}; "
          f"{meta['filled_from_nearest_window']} pixels taken from a neighbour")
    if worst:
        print("  warning: a window did not reproduce exactly; check palette learning")
    if meta["uncovered_before_fill"]:
        print(f"  note: {meta['uncovered_before_fill']} pixels were under a sprite in "
              "every window and came from a neighbouring render")


if __name__ == "__main__":
    main()

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

    X uses both nametable pages and wraps every 512 px. The cartridge uses
    vertical mirroring, so only two physical pages exist and PPUCTRL bit 1 is a
    *mirror* of bit 0, not a third page: masking with ``& 3`` added a phantom
    512 px to every window whose bit 1 happened to be set. Y is a single 240-px
    page, so a taller stage wraps Y and the caller unwraps it against its
    neighbour.
    """
    cx, fx, cy = st.scroll()
    return ((st.ppuctrl & 1) * 256 + cx * 8 + fx, cy * 8)


def sample_colours(st, frame: Path, tally: dict) -> None:
    """Add one window's background colours to a running index -> RGB tally.

    Every window is sampled, not just the first: a window only reveals the
    handful of palette entries it happens to use, and the fallback NES palette
    is *not* the emulator's (it differs by ~16 on several entries). Sampling
    only the first window left every later window's unseen colours wrong.
    """
    indices, mask, _ = st.frame_indices(with_sprites=True)
    fpx = Image.open(frame).convert("RGB").load()
    for y in range(SCREEN_H):
        mrow, irow = mask[y], indices[y]
        for x in range(SCREEN_W):
            if mrow[x]:
                continue
            colour = irow[x] & 0x3F
            bucket = tally.setdefault(colour, {})
            bucket[fpx[x, y]] = bucket.get(fpx[x, y], 0) + 1


def palette_from(tally: dict) -> tuple[dict[int, tuple[int, int, int]], dict]:
    palette = {i: FCEUMM_CLASSIC_PALETTE[i] for i in range(64)}
    conflicts = {}
    for colour, vals in tally.items():
        palette[colour] = max(vals.items(), key=lambda kv: kv[1])[0]
        if len(vals) > 1:
            conflicts[colour] = vals
    return palette, conflicts


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


def known_cameras(work: Path) -> dict[str, int]:
    """Absolute camera x per checkpoint, as recorded by the route search."""
    route = work / "route.json"
    if not route.exists():
        return {}
    try:
        return json.loads(route.read_text()).get("checkpoint_cams", {}) or {}
    except (ValueError, OSError):
        return {}


def step_delta(new: int, old: int, wrap: int, back: int) -> int:
    """Shortest signed displacement between two wrapped positions."""
    d = (new - old) % wrap
    return d - wrap if d >= wrap - back else d


def sample_agreement(canvas, covered, w, x) -> float | None:
    """How well a window's pixels match what is already on the canvas at x."""
    px, valid = w["px"], w["valid"]
    x0 = 8 if w["left_clipped"] else 0
    same = total = 0
    width = canvas.width
    for sy in range(0, SCREEN_H, 4):
        vrow, crow = valid[sy], covered[sy]
        for sx in range(x0, SCREEN_W):
            cx = x + sx
            if cx < 0 or cx >= width or not vrow[sx] or not crow[cx]:
                continue
            total += 1
            if px[sx, sy] == canvas.load()[cx, sy]:
                same += 1
    return (same / total) if total else None


def place_windows(windows: list[dict]) -> list[dict]:
    """Assign every window a world x, splitting the route into rooms.

    Camera arithmetic alone cannot do this: each room restarts the camera at 0,
    so the register gives position *within* a room and nothing across rooms.
    Windows are therefore placed from their camera delta and then checked
    against the pixels already stitched. A window that lands on content it
    disagrees with is not in the same room, so it starts a new one at the right
    edge of everything captured so far.
    """
    width = 320 * len(windows) + 512
    canvas = Image.new("RGB", (width, SCREEN_H), (0, 0, 0))
    cpx = canvas.load()
    covered = [[False] * width for _ in range(SCREEN_H)]
    placed: list[dict] = []
    frontier = 0
    room = 0
    prev = None
    for w in windows:
        if prev is None:
            x, join, agreement = 0, "start", None
        else:
            delta = step_delta(w["cam_x_mod"], prev["cam_x_mod"], 512, 128)
            cand = max(0, prev["x"] + delta)
            agreement = sample_agreement(canvas, covered, w, cand)
            if agreement is not None and agreement >= 0.80:
                x, join = cand, "overlap"
            elif 0 < delta <= 128:
                # Small step with nothing to compare against (a gap): trust the
                # camera, which is exact within a room.
                x, join = cand, "camera"
            else:
                x, join = frontier, "new-room"
                room += 1
        entry = {"x": x, "y": 0, "room": room, "join": join,
                 "agreement": round(agreement, 3) if agreement is not None else None}
        placed.append(entry)
        prev = {"x": x, "cam_x_mod": w["cam_x_mod"]}
        frontier = max(frontier, x + SCREEN_W)

        px, valid = w["px"], w["valid"]
        x0 = 8 if w["left_clipped"] else 0
        for sy in range(SCREEN_H):
            vrow, crow = valid[sy], covered[sy]
            for sx in range(x0, SCREEN_W):
                cx = x + sx
                if cx < 0 or cx >= width or not vrow[sx]:
                    continue
                cpx[cx, sy] = px[sx, sy]
                crow[cx] = True
    return placed


def stitch(items, rom: Path, work: Path) -> tuple[Image.Image, list, dict]:
    emu = Retroshot(rom, work)
    norm_dir = work / "normalised"
    norm_dir.mkdir(exist_ok=True)
    windows = []
    tally: dict = {}
    try:
        for cam_name, state in items:
            fcs, ppm = normalise(emu, state, norm_dir / f"norm_{cam_name}")
            st = load_state(fcs, rom)
            sample_colours(st, ppm, tally)
            cam_x, cam_y = camera_xy(st)
            windows.append({"name": cam_name, "state": fcs, "frame": ppm,
                            "cam_x_mod": cam_x, "cam_y_mod": cam_y, "st": st})
    finally:
        emu.close()
    palette, palette_conflicts = palette_from(tally)

    for w in windows:
        # Render every window once, before placement: placement needs the
        # pictures, not just the camera.
        st = w["st"]
        img = render_window(st, palette)
        diff, valid = verify_window(img, st, w["frame"])
        w["img"], w["valid"], w["px"], w["diff"] = img, valid, img.load(), diff
        w["img_full"] = render_window(st, palette, show_clipped=True)
        w["left_clipped"] = not (st.ppumask & 0x02)

    placements = place_windows(windows)
    min_x = min(p["x"] for p in placements)
    max_x = max(p["x"] + SCREEN_W for p in placements)
    min_y = min(0, min(p["y"] for p in placements))
    total_h = max(p["y"] for p in placements) + SCREEN_H - min_y
    total_w = max_x - min_x
    canvas = Image.new("RGB", (total_w, total_h), (0, 0, 0))
    covered = [[False] * total_w for _ in range(total_h)]
    reports = []
    for w, p in zip(windows, placements):
        x, y = p["x"] - min_x, p["y"] - min_y
        reports.append({"name": w["name"], "cam": p["x"], "camy": p["y"],
                        "room": p["room"],
                        "join": p["join"],
                        "overlap_agreement": p["agreement"],
                        "left_column_clipped": w["left_clipped"],
                        "bg_pixel_differences_outside_sprites": w["diff"]})
        px, valid = w["px"], w["valid"]
        x0 = 8 if w["left_clipped"] else 0
        for sy in range(SCREEN_H):
            dy = y + sy
            for sx in range(x0, SCREEN_W):
                if not valid[sy][sx]:
                    continue
                xx = x + sx
                if 0 <= xx < total_w and 0 <= dy < total_h:
                    canvas.putpixel((xx, dy), px[sx, sy])
                    covered[dy][xx] = True

    # Re-point windows at their final canvas coordinates for the fill pass.
    for w, p in zip(windows, placements):
        w["cam"], w["camy"] = p["x"] - min_x, p["y"] - min_y

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
            "palette_conflicts": {str(k): {str(c): n for c, n in v.items()}
                                  for k, v in palette_conflicts.items()},
            "palette": {str(k): list(v) for k, v in palette.items()}}
    return canvas, reports, meta


def build_tileset(level: Image.Image, tileset_path: Path, tilemap_path: Path,
                  tiles_csv: Path, page_width: int = 2048):
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
    # GMS 1.4 caps a texture page at 2048 px, so a longer strip is also written
    # as consecutive pages sharing one tileset.
    out_dir = tileset_path.parent
    pages = []
    if cols * 8 > page_width:
        per_page = page_width // 8
        for start_col in range(0, cols, per_page):
            index = len(pages)
            end_col = min(cols, start_col + per_page)
            page_img = level.crop((start_col * 8, 0, end_col * 8, rows * 8))
            page_img.save(out_dir / f"page_{index:02d}.png", optimize=True)
            with (out_dir / f"tilemap_{index:02d}.csv").open("w", newline="",
                                                            encoding="utf-8") as f:
                wr = csv.writer(f, lineterminator="\n")
                wr.writerow([f"c{start_col + i}" for i in range(end_col - start_col)])
                for row in grid:
                    wr.writerow(row[start_col:end_col])
            pages.append({"index": index, "file": f"page_{index:02d}.png",
                          "tilemap": f"tilemap_{index:02d}.csv",
                          "first_column": start_col,
                          "columns": end_col - start_col,
                          "width_px": (end_col - start_col) * 8})
    return len(raws), cols, rows, sheet.size, pages


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", required=True,
                    help="solver work directory containing checkpoints/")
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-cam", type=int, default=None,
                    help="ignore windows at or beyond this camera x (room cut)")
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
    if args.max_cam is not None:
            states = [p for p in states
                  if known.get(p.stem, 0) <= args.max_cam]
    items += [(p.stem, p) for p in states]

    level, reports, meta = stitch(items, rom, work)
    # Tile-align the strip: a partial 8-pixel column cannot be expressed in a
    # tilemap, so trim rather than ship a map that silently drops pixels.
    aligned = (level.width // 8) * 8
    if aligned != level.width:
        level = level.crop((0, 0, aligned, level.height))
    level.save(out / "level.png", optimize=True)
    unique, cols, rows, sheet_size, pages = build_tileset(
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
        "palette_conflicts": meta["palette_conflicts"],
        "unique_tiles": unique,
        "tilemap": {"cols": cols, "rows": rows},
        "tileset_size": list(sheet_size),
        "pages": pages,
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
    if pages:
        print(f"  split into {len(pages)} texture pages of at most 2048 px")
    if unique * 8 > 2048:
        print("  tileset exceeds 2048 px in one row; use tileset.png (16 per row) "
              "as a tileset background")
    print(f"  max background pixel error per window: {worst}; "
          f"{meta['filled_from_nearest_window']} pixels taken from a neighbour")
    if worst:
        print("  warning: a window did not reproduce exactly; check palette learning")
    if meta["uncovered_before_fill"]:
        print(f"  note: {meta['uncovered_before_fill']} pixels were under a sprite in "
              "every window and came from a neighbouring render")


if __name__ == "__main__":
    main()

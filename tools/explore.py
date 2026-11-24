"""Explore a level for new background content, with no idea where the player is.

Searching for the way forward by watching the camera or the player's OAM block
keeps failing in the same way: the camera is pinned at a room edge, and the
player's sprite block changes OAM slot as its state changes, so both metrics go
flat while the character is actually doing something. This explorer scores the
one thing that cannot be faked -- *how much background nobody has seen yet* --
and follows whatever input produces it.

Every accepted window is logged with the camera it was captured at, so the
stitcher can place it afterwards. Novelty is counted over 8x8 background cells
by content hash, so a room that reuses the same tiles as its neighbour still
counts as new when the cells sit somewhere new.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from autoplay import Retroshot
from nes_state import load_state

BUTTONS = ["A", "B", "UP", "RIGHT", "LEFT", "UP+RIGHT", "UP+LEFT",
           "RIGHT+A", "LEFT+A", "UP+A", "UP+RIGHT+A", "DOWN"]

# (buttons, frames) candidates; frames are per-segment and short enough that a
# single jump or climb completes inside one segment.
ACTIONS = [
    ("A", 8), ("A", 16), ("A", 26),
    ("UP", 20), ("UP", 45), ("UP+A", 12), ("UP+RIGHT", 24), ("UP+LEFT", 24),
    ("RIGHT", 30), ("LEFT", 30), ("RIGHT+A", 14), ("LEFT+A", 14),
    ("UP+RIGHT+A", 14), ("B", 10), ("", 20),
]


def tile_hashes(state, page: int | None = None) -> dict[tuple[int, int], int]:
    """Hash each 8x8 cell of a rendered nametable page.

    Hashes are compared as a set of contents, not per position: a scrolling
    screen moves every cell, and a position-keyed comparison would call that
    "new" forever while real new content went unnoticed.
    """
    img = state.render_page_rgb(page=page)   # flat RGB, 256x240
    out = {}
    for ty in range(30):
        for tx in range(32):
            h = hashlib.blake2b(digest_size=8)
            for y in range(8):
                row = (ty * 8 + y) * 256 + tx * 8
                for x in range(8):
                    h.update(bytes(img[row + x]))
            out[(tx, ty)] = int.from_bytes(h.digest(), "big")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--emu-dir", default=None)
    ap.add_argument("--steps", type=int, default=120)
    ap.add_argument("--candidates", type=int, default=10)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--max-steps-back", type=int, default=6)
    args = ap.parse_args()

    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    emu = Retroshot(args.rom, str(workdir), emu_dir=args.emu_dir)
    probe = str((workdir / "probe").resolve())

    def press(combo: str, frames: int) -> None:
        keys = [b for b in combo.split("+") if b]
        for k in keys:
            emu.press(k)
        emu.run(frames)
        for k in keys:
            emu.release(k)
        emu.run(3)

    def snapshot(tag: str):
        path = str((workdir / f"{tag}.fcs").resolve())
        emu.save(path)
        st = load_state(path, args.rom)
        cx, fx, cy = st.scroll()
        cam = (st.ppuctrl & 1) * 256 + cx * 8 + fx
        return path, cam, cy * 8, st

    random.seed(args.seed)

    # Seed the archive with the starting window.
    emu.load(args.state)
    emu.run(2)
    path, cam, camy, st = snapshot("step_0000")
    seen: set[int] = set(tile_hashes(st).values())
    # Camera positions already visited. The kitchen, like most of this stage,
    # reuses the same handful of wall tiles, so content novelty alone saturates
    # after one screen; being somewhere the camera has never been is the more
    # useful signal, and content novelty breaks the ties.
    camera_seen: set[tuple[int, int]] = {(cam, camy)}
    log = [{"step": 0, "state": path, "cam": cam, "cam_y": camy, "new_cells": 0}]

    # A stack of accepted states, so a dead end can be rewound instead of
    # ending the run.
    stack = [(args.state, [])]
    step = 1
    while step < args.steps and stack:
        base_state, base_hist = stack[-1]
        best = None
        for _ in range(args.candidates):
            hist = [(random.choice(ACTIONS), random.choice(ACTIONS))
                    for _ in range(random.randrange(1, 4))]
            emu.load(base_state)
            emu.run(2)
            for (combo, frames), _ in hist:
                press(combo, frames)
            path, cam, camy, st = snapshot("probe")
            hashes = tile_hashes(st)
            new_cells = sum(1 for h in hashes.values() if h not in seen)
            score = new_cells + (200 if (cam, camy) not in camera_seen else 0)
            if best is None or score > best[0]:
                best = (score, hist, path, cam, camy, hashes)
        if best is None or best[0] == 0:
            stack.pop()
            continue
        score, hist, path, cam, camy, hashes = best
        final = str((workdir / f"step_{step:04d}.fcs").resolve())
        Path(path).replace(final)
        seen.update(hashes.values())
        camera_seen.add((cam, camy))
        log.append({"step": step, "state": final, "cam": cam, "cam_y": camy,
                    "new_cells": score,
                    "actions": [[c, f] for (c, f), _ in hist]})
        print(f"step {step:3d} new_cells={score:3d} cam={cam:3d} cam_y={camy:3d} "
              f"{[(c, f) for (c, f), _ in hist]}", flush=True)
        stack.append((final, base_hist + hist))
        if len(stack) > args.max_steps_back:
            stack.pop(0)
        step += 1

    (workdir / "windows.json").write_text(json.dumps(log, indent=1))
    emu.close()
    print(f"wrote {len(log)} windows to {workdir/'windows.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

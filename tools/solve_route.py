#!/usr/bin/env python3
"""Best-first savestate search for asset capture.

The emulator restores savestates instantly, so a route can be searched without
replaying the level: expand the most promising state with a set of short input
macros, keep the children that move the camera further right, and repeat.

Two details matter for correctness:

* The PPU scroll registers at the end of a frame describe the *next* frame, so
  every macro ends with a short no-input settle before progress is measured.
* The camera is only visible modulo a 512-pixel window (two nametables), so it
  is unwrapped against the parent's position.  A large rewind means the state
  fell back to a checkpoint, i.e. the macro died even if the lives counter was
  restored by a continue.

Checkpoints are dumped whenever the frontier passes a new 64-pixel camera
boundary; those states are what later get stitched into wide level maps.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoplay import Retroshot
from nes_state import load_state

HEALTH_ADDR = 0x03D4
LIVES_ADDR = 0x00A7


@dataclass
class Macro:
    name: str
    segments: list[tuple[str, int]]  # ("RIGHT+A", frames)


def jump_after(delay: int) -> Macro:
    """Walk right, then jump -- delay matters for gaps and moving platforms."""
    return Macro(f"wait{delay:02d}_jump",
                 [("RIGHT", 8), ("", delay), ("RIGHT", 4), ("RIGHT+A", 14),
                  ("RIGHT", 54 - delay)])


MACROS = [
    Macro("walk", [("RIGHT", 70)]),
    Macro("jump_early", [("RIGHT", 5), ("RIGHT+A", 12), ("RIGHT", 53)]),
    Macro("jump_mid", [("RIGHT", 25), ("RIGHT+A", 12), ("RIGHT", 33)]),
    Macro("jump_late", [("RIGHT", 40), ("RIGHT+A", 12), ("RIGHT", 18)]),
    Macro("hop_high", [("RIGHT", 8), ("RIGHT+A", 22), ("RIGHT", 40)]),
    Macro("hop_short", [("RIGHT", 8), ("RIGHT+A", 7), ("RIGHT", 55)]),
    Macro("double_early", [("RIGHT", 4), ("RIGHT+A", 12), ("RIGHT", 16),
                           ("RIGHT+A", 12), ("RIGHT", 26)]),
    Macro("double_late", [("RIGHT", 20), ("RIGHT+A", 12), ("RIGHT", 20),
                          ("RIGHT+A", 12), ("RIGHT", 6)]),
    Macro("stand_jump", [("RIGHT", 10), ("A", 18), ("RIGHT", 42)]),
    # Stand still, then commit: covers moving platforms and spring-loaded gaps
    # where the timing of the jump, not the jump itself, is what matters.
    Macro("still_jump", [("", 30), ("RIGHT+A", 16), ("RIGHT", 40)]),
    jump_after(20),
    jump_after(40),
    Macro("back_off_jump", [("LEFT", 12), ("RIGHT", 6), ("RIGHT+A", 16), ("RIGHT", 40)]),
    # Vertical travel: pillars, vines and ladders are climbed with UP, and the
    # camera does not move while doing it, so these earn their place even
    # though they make no horizontal progress.
    Macro("climb_up", [("UP", 45), ("RIGHT", 25)]),
    Macro("climb_far", [("UP", 70), ("RIGHT", 20)]),
    Macro("up_right", [("UP+RIGHT", 50), ("RIGHT", 20)]),
    Macro("climb_jump", [("UP", 35), ("UP+RIGHT+A", 14), ("RIGHT", 30)]),
]


@dataclass
class Node:
    state: str
    cam: int
    depth: int
    world_x: int = 0   # cam + player screen x, unwrapped
    player_y: int = 0
    alive: bool = True
    children: int = 0
    history: list = field(default_factory=list)


def camera_of(state_path: Path, rom: str | Path) -> int:
    st = load_state(state_path, rom)
    cx, fx, _ = st.scroll()
    return (st.ppuctrl & 3) * 256 + cx * 8 + fx


PLAYER_OAM = 47   # first of the ten player sprites; the rest follow it


def player_of(state_path: Path, rom: str | Path) -> tuple[int, int, int]:
    """Return (world_x, screen_y, cam) for the player.

    The camera alone cannot tell a climb from standing still, and it lags the
    player during a jump, so progress is measured on the player instead.
    """
    st = load_state(state_path, rom)
    cx, fx, _ = st.scroll()
    cam = (st.ppuctrl & 3) * 256 + cx * 8 + fx
    oam = st.oam
    base = PLAYER_OAM * 4
    sx, sy = oam[base + 3], oam[base]
    if sy >= 240:  # player hidden (respawn/death frames)
        return cam, 240, cam
    return cam + sx, sy, cam


def unwrap(cam: int, reference: int) -> int:
    best = cam
    for candidate in (cam - 512, cam, cam + 512):
        if abs(candidate - reference) < abs(best - reference):
            best = candidate
    return best


def run_macro(emu: Retroshot, macro: Macro) -> None:
    held: set[str] = set()
    for spec, frames in macro.segments:
        want = set(spec.split("+")) if spec else set()
        for b in held - want:
            emu.release(b)
        for b in want - held:
            emu.press(b)
        held = want
        emu.run(frames)
    for b in held:
        emu.release(b)


def settle(emu: Retroshot, frames: int = 30) -> None:
    """Let the player land and the scroll registers reach a steady value."""
    emu.run(frames)


def solve(start: Path, rom: Path, workdir: Path, iterations: int,
          beam: int, checkpoint_step: int, target: int | None) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    emu = Retroshot(rom, workdir)
    checkpoints = workdir / "checkpoints"
    checkpoints.mkdir(exist_ok=True)
    next_ckpt = checkpoint_step
    nodes: list[Node] = []
    try:
        emu.load(start)
        emu.cmd(f"guard {HEALTH_ADDR:X} 3")
        start_cam = camera_of(start, rom)
        start_wx, start_py, _ = player_of(start, rom)
        nodes.append(Node(state=start.stem, cam=start_cam, depth=0,
                          world_x=start_wx, player_y=start_py))
        best = nodes[0]
        log = []
        for it in range(iterations):
            alive = [n for n in nodes if n.alive]
            if not alive:
                print("frontier exhausted")
                break
            parent = max(alive, key=lambda n: (n.world_x, -n.player_y))
            base_lives = None
            new_nodes = []
            for macro in MACROS:
                emu.load(workdir / f"{parent.state}.fcs")
                base_lives = emu.ram("lives")[LIVES_ADDR]
                run_macro(emu, macro)
                settle(emu)
                lives = emu.ram("lives")[LIVES_ADDR]
                name = f"n{len(nodes)}_{macro.name}"
                path = workdir / f"{name}.fcs"
                emu.save(path)
                cam = unwrap(camera_of(path, rom), parent.cam)
                wx, py, _ = player_of(path, rom)
                wx = cam + (wx - cam)
                # Same 512-pixel world wrap as the camera; normalise against
                # the parent so a wrap does not look like a huge leap back.
                while wx - parent.world_x > 256:
                    wx -= 512
                while parent.world_x - wx > 256:
                    wx += 512
                died = lives < base_lives or wx < parent.world_x - 64
                advanced = wx >= parent.world_x + 2
                climbed = py <= parent.player_y - 8
                if not died and (advanced or climbed):
                    node = Node(state=name, cam=cam, depth=parent.depth + 1,
                                world_x=wx, player_y=py)
                    new_nodes.append(node)
                    nodes.append(node)
                    if (wx, -py) > (best.world_x, -best.player_y):
                        best = node
                        kind = "climb" if climbed and not advanced else "walk"
                        print(f"  new best wx={wx} y={py} via {macro.name} "
                              f"({kind}, depth {node.depth})", flush=True)
                else:
                    path.unlink(missing_ok=True)
            parent.children = len(new_nodes)
            if not new_nodes:
                parent.alive = False
                print(f"iter {it:03d}: dead end at wx={parent.world_x} y={parent.player_y}", flush=True)
            else:
                # Keep the search narrow: prune the worst branches.
                alive = sorted([n for n in nodes if n.alive],
                               key=lambda n: (n.world_x, -n.player_y), reverse=True)
                for stale in alive[beam:]:
                    stale.alive = False
            while best.world_x >= next_ckpt:
                # Re-enter the best state so the saved state and the captured
                # frame are the same frame: a shot taken after a bare load
                # shows whatever was last rendered, not the loaded state.
                emu.load(workdir / f"{best.state}.fcs")
                emu.run(1)
                ck_name = f"cam_{best.world_x:05d}"
                emu.save(checkpoints / ck_name)
                emu.screenshot(checkpoints / ck_name)
                next_ckpt = best.world_x + checkpoint_step
            log.append({"iter": it, "parent": parent.state, "parent_cam": parent.cam,
                        "children": len(new_nodes), "best": best.cam})
            if target is not None and best.world_x >= target:
                print("target reached")
                break
        (workdir / "route.json").write_text(json.dumps({
            "best_cam": best.world_x, "best_state": best.state,
            "checkpoints": sorted(p.name for p in checkpoints.glob("*.fcs")),
            "checkpoint_step": checkpoint_step,
            "log": log,
        }, indent=2))
        return {"best_cam": best.world_x, "state": str(workdir / f"{best.state}.fcs"),
                "checkpoints": len(list(checkpoints.glob("*.fcs")))}
    finally:
        emu.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--iterations", type=int, default=60)
    ap.add_argument("--beam", type=int, default=4, help="live branches kept")
    ap.add_argument("--checkpoint-step", type=int, default=64,
                    help="camera pixels between saved checkpoint states")
    ap.add_argument("--target", type=int, default=None)
    args = ap.parse_args()
    start = Path(args.state).resolve()
    rom = Path(args.rom).resolve()
    wd = Path(args.workdir).resolve()
    wd.mkdir(parents=True, exist_ok=True)
    if start.parent != wd:
        shutil.copy(start, wd / start.name)
        start = wd / start.name
    result = solve(start, rom, wd, args.iterations, args.beam,
                   args.checkpoint_step, args.target)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

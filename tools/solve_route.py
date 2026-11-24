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
    # Found by randomised local search from the beam at the top of the
    # restaurant interior, where every simpler macro had stalled: jump right,
    # walk, climb right past the pillar, then hold B.
    Macro("climb_over", [("RIGHT+A", 24), ("RIGHT", 25), ("UP+RIGHT", 21),
                         ("B", 19)]),
]


@dataclass
class Node:
    state: str
    cam: int
    depth: int
    world_x: int = 0   # odometer: sum of per-macro player displacements
    player_y: int = 0
    player_px: int = 0  # camera + player screen x, wrapped; the odometer input
    cam_raw: int = 0    # camera as the hardware reports it, 0..511
    expanded: bool = False
    alive: bool = True
    children: int = 0
    history: list = field(default_factory=list)


def camera_of(state_path: Path, rom: str | Path) -> int:
    st = load_state(state_path, rom)
    cx, fx, _ = st.scroll()
    return (st.ppuctrl & 1) * 256 + cx * 8 + fx


PLAYER_OAM = 47   # first of the ten player sprites; the rest follow it


def player_of(state_path: Path, rom: str | Path) -> tuple[int, int, int]:
    """Return (world_x, screen_y, cam) for the player.

    The camera alone cannot tell a climb from standing still, and it lags the
    player during a jump, so progress is measured on the player instead.
    """
    st = load_state(state_path, rom)
    cx, fx, _ = st.scroll()
    cam = (st.ppuctrl & 1) * 256 + cx * 8 + fx
    oam = st.oam
    base = PLAYER_OAM * 4
    sx, sy = oam[base + 3], oam[base]
    if sy >= 240:  # player hidden (respawn/death frames)
        return cam, 240, cam
    # Keep the sum inside the 512-px wrap the caller measures differences in;
    # cam + sx can reach 767 and would be read as a large spurious jump.
    return (cam + sx) % 512, sy, cam


def step_delta(new: int, old: int, wrap: int, back: int) -> int:
    """Shortest signed displacement between two wrapped positions.

    The camera register only holds 0..511 and the player's screen x only
    0..255, so neither is a world position. Unwrapping one against the other
    (picking the +-512 candidate nearest the parent) silently caps apparent
    progress at 256 px -- which is exactly why every earlier search appeared to
    stall near camera 1000 no matter how the macros were changed. Measuring the
    *change* instead cannot drift, as long as a single macro cannot move the
    player more than ``wrap - back`` pixels.
    """
    d = (new - old) % wrap
    if d >= wrap - back:
        d -= wrap
    return d


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


def expand(emu: Retroshot, parent: Node, workdir: Path, rom: Path,
           nodes: list[Node], bookkeeping: dict) -> list[Node]:
    """Try every macro from one state and return the states that made progress."""
    children: list[Node] = []
    for macro in MACROS:
        emu.load(workdir / f"{parent.state}.fcs")
        base_lives = emu.ram("lives")[LIVES_ADDR]
        run_macro(emu, macro)
        settle(emu)
        lives = emu.ram("lives")[LIVES_ADDR]
        name = f"n{len(nodes)}_{macro.name}"
        path = workdir / f"{name}.fcs"
        emu.save(path)
        cam = camera_of(path, rom)
        pos, py, _ = player_of(path, rom)   # pos = camera + player screen x
        # Displacement of (camera + player) between parent and child: an
        # odometer, not an absolute position.
        delta = step_delta(pos, parent.player_px, 512, 128)
        world_x = parent.world_x + delta
        cam_abs = parent.cam + step_delta(cam, parent.cam_raw, 512, 128)
        died = lives < base_lives or delta < -64
        # Either signal counts: the camera only moves forward when the player
        # has really gone right, and it can catch up after a jump in a way that
        # briefly shrinks cam + player-screen-x.
        advanced = (cam_abs >= parent.cam + 2 or
                    world_x >= parent.world_x + 96)
        climbed = py <= parent.player_y - 8
        if not died and (advanced or climbed):
            node = Node(state=name, cam=cam_abs, depth=parent.depth + 1,
                        world_x=world_x, player_y=py, player_px=pos,
                        cam_raw=cam)
            children.append(node)
            nodes.append(node)
            # Capture the moment the route first reaches each camera step, so
            # windows are evenly spaced along the path that actually exists.
            # Capturing at the frontier leader instead skipped 100+ px whenever
            # one jump carried it past several thresholds at once.
            while cam_abs >= bookkeeping["next_ckpt"]:
                emu.load(path)
                emu.run(1)
                ck_name = f"cam_{bookkeeping['next_ckpt']:05d}"
                emu.save(bookkeeping["checkpoints"] / ck_name)
                emu.screenshot(bookkeeping["checkpoints"] / ck_name)
                bookkeeping["cams"][ck_name] = cam_abs
                bookkeeping["next_ckpt"] += bookkeeping["step"]
        else:
            path.unlink(missing_ok=True)
    return children


def solve(start: Path, rom: Path, workdir: Path, iterations: int,
          beam: int, checkpoint_step: int, target: int | None) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    emu = Retroshot(rom, workdir)
    checkpoints = workdir / "checkpoints"
    checkpoints.mkdir(exist_ok=True)
    next_ckpt = checkpoint_step
    # Checkpoint name -> absolute camera x. The camera register only holds
    # 0..511, so a stitcher that re-derives position from the state alone has to
    # guess each 512-px wrap; the search already knows the answer.
    checkpoint_cams: dict[str, int] = {}
    nodes: list[Node] = []
    try:
        emu.load(start)
        emu.cmd(f"guard {HEALTH_ADDR:X} 3")
        start_cam = camera_of(start, rom)
        start_wx, start_py, _ = player_of(start, rom)
        nodes.append(Node(state=start.stem, cam=start_cam, depth=0,
                          world_x=0, player_y=start_py, player_px=start_wx,
                          cam_raw=start_cam))
        best = nodes[0]
        log = []
        for it in range(iterations):
            # Best-first: every state is expanded exactly once, in order of
            # how far it got. Re-expanding the leader until it dies (the old
            # shape) burned the whole budget on one branch, and pruning by beam
            # threw away the deep path whenever a macro made the frontier
            # wider -- which is why adding macros used to make runs *worse*.
            pending = [n for n in nodes if n.alive and not n.expanded]
            if not pending:
                print("frontier exhausted")
                break
            # Rank on the camera: it is exact within a room and its wrap is
            # 512 px, so a mis-read costs at most one room's worth. Summing
            # per-macro player displacements (the "odometer") drifts instead --
            # it ranked a state still in the first room as the furthest of all.
            parent = max(pending, key=lambda n: (n.cam, -n.player_y, n.world_x))
            parent.expanded = True
            bookkeeping = {"checkpoints": checkpoints, "next_ckpt": next_ckpt,
                           "step": checkpoint_step,
                           "cams": checkpoint_cams}
            children = expand(emu, parent, workdir, rom, nodes, bookkeeping)
            next_ckpt = bookkeeping["next_ckpt"]
            parent.children = len(children)
            if not children:
                parent.alive = False
                print(f"iter {it:03d}: dead end at wx={parent.world_x} "
                      f"y={parent.player_y}", flush=True)
            for node in children:
                if (node.cam, -node.player_y) > (best.cam, -best.player_y):
                    best = node
                    print(f"  new best cam={node.cam} y={node.player_y} "
                          f"(depth {node.depth})", flush=True)
            # Keep the frontier bounded by score, but never drop the leader.
            pending = [n for n in nodes if n.alive and not n.expanded]
            if len(pending) > beam * 12:
                cut = sorted(pending, key=lambda n: (n.cam, -n.player_y,
                                                     n.world_x), reverse=True)
                for stale in cut[beam * 12:]:
                    if stale is not best:
                        stale.alive = False
            log.append({"iter": it, "parent": parent.state,
                        "parent_wx": parent.world_x,
                        "children": parent.children, "best": best.world_x})
            if target is not None and best.cam >= target:
                print("target reached")
                break
        (workdir / "route.json").write_text(json.dumps({
            "best_cam": camera_of(workdir / f"{best.state}.fcs", rom),
            "best_world_x": best.world_x, "best_state": best.state,
            "checkpoints": sorted(p.name for p in checkpoints.glob("*.fcs")),
            "checkpoint_step": checkpoint_step,
            "checkpoint_cams": checkpoint_cams,
            "log": log,
        }, indent=2))
        return {"best_cam": best.cam, "state": str(workdir / f"{best.state}.fcs"),
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

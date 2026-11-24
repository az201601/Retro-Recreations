"""Walk a level forward by sweeping jump timing, one screenful at a time.

The best-first search can only chain the macros it is given, and its macros use
fixed hold durations. In dense platform sections the *timing* of the jump is
what decides whether the character lands on the next shelf, so a fixed set
stalls even though a human playing the same spot moves on within seconds.

This sweeper does what a human does: at every state, try every jump timing
(how long to run first, how long to hold the button) and keep whichever one
carries the camera furthest forward. Each accepted state is saved in order, so
the stitcher can place them exactly as it places search results.

A camera delta is read with a threshold of *256* rather than 128: a running
jump can advance 168 px in one macro, and the tighter threshold misreads that
as 332 px backwards and rejects the best move on the screen.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from autoplay import Retroshot
from nes_state import load_state
from solve_route import step_delta

PLAYER_TILE = range(168, 204)


def camera_of(path: Path, rom) -> tuple[int, int, int]:
    st = load_state(path, rom)
    cx, fx, cy = st.scroll()
    return (st.ppuctrl & 1) * 256 + cx * 8 + fx, cy * 8, st


def candidates():
    """Jump timings to try, as full sequences of (buttons, frames).

    Phase is how long the character runs up first; hold is how long the jump
    button stays down. Both matter: a shelf that is one pixel too far is
    reached by running longer, one too high by holding longer.
    """
    seqs = []
    for phase in range(0, 88, 8):
        for hold in (12, 18, 24, 30):
            seqs.append((("RIGHT", phase), ("A", hold), ("RIGHT", 40)))
            seqs.append((("RIGHT", phase), ("A", hold), ("RIGHT", 10),
                         ("A", hold), ("RIGHT", 30)))
        seqs.append((("LEFT", 12), ("RIGHT", phase), ("A", 18), ("RIGHT", 40)))
        seqs.append((("RIGHT", phase), ("A", 24), ("LEFT", 12), ("RIGHT", 30)))
    # Enemies in this stage are removed with a thrown box, not jumped over:
    # B picks one up and B again throws it. Without these the sweeper walks
    # into the chef standing at the room's right edge and dies there.
    for phase in (0, 16, 32, 48):
        seqs.append((("RIGHT", phase), ("B", 5), ("RIGHT", 8), ("B", 8), ("RIGHT", 40)))
        seqs.append((("B", 5), ("RIGHT", phase), ("B", 8), ("RIGHT", 40)))
        seqs.append((("RIGHT", phase), ("B", 5), ("RIGHT", 8), ("B", 8),
                     ("RIGHT", 20), ("A", 20), ("RIGHT", 30)))
    # Enemy position is on a timer, so the same jump succeeds or fails
    # depending on when it starts: wait before committing.
    for wait in (30, 60, 90):
        for phase in (0, 16, 32, 48):
            seqs.append((("", wait), ("RIGHT", phase), ("A", 24), ("RIGHT", 40)))
            seqs.append((("", wait), ("RIGHT", phase), ("A", 18), ("LEFT", 10),
                         ("RIGHT", 30)))
    seqs.append((("A", 18), ("RIGHT", 40)))
    seqs.append((("UP", 20), ("RIGHT", 30), ("A", 24), ("RIGHT", 40)))
    return seqs


def run_seq(emu, seq) -> None:
    for combo, frames in seq:
        keys = [k for k in combo.split("+") if k]
        for k in keys:
            emu.press(k)
        emu.run(frames)
        for k in keys:
            emu.release(k)


def player_y(st) -> int:
    oam = st.oam
    hits = [oam[i * 4] for i in range(64)
            if 24 <= oam[i * 4] < 216 and oam[i * 4 + 1] in PLAYER_TILE]
    return min(hits) if hits else 240


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--emu-dir", default=None)
    args = ap.parse_args()

    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    emu = Retroshot(args.rom, str(work), emu_dir=args.emu_dir)
    probe = str((work / "probe.fcs").resolve())

    current = args.state
    log = []
    cam_abs = 0
    for step in range(args.steps):
        emu.load(current)
        emu.run(2)
        emu.save(probe)
        cam0, camy0, st0 = camera_of(probe, args.rom)
        y0 = player_y(st0)
        hp0, lives0 = st0.ram[0x3D4], st0.ram[0xA7]
        best = None
        for seq in candidates():
            emu.load(current)
            emu.run(2)
            run_seq(emu, seq)
            emu.run(10)
            emu.save(probe)
            cam, camy, st = camera_of(probe, args.rom)
            dy = step_delta(cam, cam0, 512, 256)
            if st.ram[0xA7] < lives0:
                continue                    # dying is not progress
            score = (dy * 4 + (y0 - player_y(st))
                     - 60 * max(0, hp0 - st.ram[0x3D4]))
            if best is None or score > best[0]:
                best = (score, dy, cam, camy, seq)
        if best is None or best[1] <= 4:
            print(f"step {step}: no forward move (best dy={best[1] if best else 0})")
            break
        _, dy, cam, camy, seq = best
        emu.load(current)
        emu.run(2)
        run_seq(emu, seq)
        emu.run(10)
        out = str((work / f"w{step:04d}.fcs").resolve())
        emu.save(out)
        cam_abs += dy
        log.append({"step": step, "state": out, "cam": cam, "cam_y": camy,
                    "dy": dy, "cam_abs": cam_abs, "actions": [list(x) for x in seq]})
        print(f"step {step:3d} dy={dy:4d} cam_abs={cam_abs:5d} cam={cam:3d} "
              f"cam_y={camy:3d} {seq}", flush=True)
        current = out

    (work / "route.json").write_text(json.dumps(
        {"start": args.state, "steps": log}, indent=1))
    emu.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

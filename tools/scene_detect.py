#!/usr/bin/env python3
"""
scene_detect.py -- run a timeline and report frames where the picture changes
significantly (scene transitions, dialog, movement). Prints frame numbers with
a change score so we can jump straight to the interesting moments.

    .venv/bin/python tools/scene_detect.py --timeline "..." --step 1
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nes_harness import NesEmu  # noqa: E402
from run_script import parse_timeline, CORE, ROM  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default="600:")
    ap.add_argument("--step", type=int, default=1, help="sample every N frames")
    ap.add_argument("--thresh", type=float, default=1.5, help="mean abs diff threshold")
    ap.add_argument("--save", default=None, help="folder to save changed frames")
    ap.add_argument("--audio", default=None)
    args = ap.parse_args()

    emu = NesEmu(CORE).load(ROM)
    import nes_harness
    emu._log_cb = nes_harness.LOG_CB(lambda l, m: None)

    if args.save:
        os.makedirs(args.save, exist_ok=True)
    emu.clear_audio()
    prev = None
    events = []
    for frames, btns in parse_timeline(args.timeline):
        emu.set_buttons(*btns) if btns else emu.release_all()
        left = frames
        while left > 0:
            n = min(args.step, left)
            emu.run(n)
            left -= n
            cur = emu.rgb_frame().astype(np.int16)
            if prev is not None:
                d = float(np.abs(cur - prev).mean())
                if d > args.thresh:
                    events.append((emu.frames_run, d))
                    if args.save:
                        emu.screenshot(os.path.join(args.save, f"f{emu.frames_run:06d}.png"))
            prev = cur
    # collapse runs of consecutive changed frames into ranges
    ranges = []
    for f, d in events:
        if ranges and f - ranges[-1][1] <= 4:
            ranges[-1][1] = f
            ranges[-1][2] = max(ranges[-1][2], d)
        else:
            ranges.append([f, f, d])
    for a, b, d in ranges:
        print(f"change frames {a}-{b}  peak {d:.1f}")
    if args.audio:
        import soundfile as sf
        a = emu.audio_array().astype("float32") / 32768.0
        sf.write(args.audio, a, emu.sample_rate)
    emu.close()


if __name__ == "__main__":
    main()

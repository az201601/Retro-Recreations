#!/usr/bin/env python3
"""
run_script.py -- run the NES ROM with a scripted input timeline and capture
screenshots / audio / RAM / savestates along the way.

Timeline syntax (colon-separated segments):
    <frames>:<buttons>[,<buttons>...]
Buttons are names joined with '+': e.g.  300:  60:start  90:right+a  30:

Examples:
    # boot to title, screenshot every 60 frames
    .venv/bin/python tools/run_script.py --timeline "600:" --shots 60 --out work/boot

    # press start on title and capture
    .venv/bin/python tools/run_script.py --timeline "900: 10:start 600:" --shots 30 \
        --out work/menu --audio work/menu.wav
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nes_harness import NesEmu, joypad_mask  # noqa: E402

CORE = os.environ.get("NES_CORE", "/tmp/nestopia/libretro/nestopia_libretro.so")
ROM = os.environ.get("NES_ROM", "Chip 'n Dale - Rescue Rangers 2 (USA).nes")


def parse_timeline(spec: str):
    """'300: 60:start 30:right+a' -> [(300, []), (60, ['start']), (30, ['right','a'])]"""
    segs = []
    for chunk in spec.replace(",", " ").split():
        pass
    # split on whitespace but each segment is frames:buttons (buttons may use +)
    import re
    for m in re.finditer(r"(\d+):([a-z+]*)", spec):
        frames = int(m.group(1))
        btns = [b for b in m.group(2).split("+") if b]
        segs.append((frames, btns))
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default="600:")
    ap.add_argument("--shots", type=int, default=0, help="capture a frame every N frames")
    ap.add_argument("--out", default="work/run")
    ap.add_argument("--audio", default=None, help="write WAV of all audio")
    ap.add_argument("--state", default=None, help="write savestate at end")
    ap.add_argument("--ram-log", default=None, help="append RAM snapshots (hex) every shot")
    ap.add_argument("--pal", default="composite-direct-fbx")
    ap.add_argument("--mute-log", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    emu = NesEmu(CORE).load(ROM, pal=args.pal)
    if args.mute_log:
        import nes_harness
        emu._log_cb = nes_harness.LOG_CB(lambda l, m: None)

    segs = parse_timeline(args.timeline)
    total = sum(f for f, _ in segs)
    print(f"timeline: {segs}  total {total} frames")
    emu.clear_audio()
    shot_i = 0
    ram_f = open(args.ram_log, "w") if args.ram_log else None
    last_shot = 0
    for frames, btns in segs:
        emu.set_buttons(*btns) if btns else emu.release_all()
        step = 1
        remaining = frames
        while remaining > 0:
            n = min(step, remaining)
            if args.shots:
                n = min(n, max(1, args.shots - (emu.frames_run - last_shot)))
            emu.run(n)
            remaining -= n
            if args.shots and (emu.frames_run - last_shot) >= args.shots:
                last_shot = emu.frames_run
                emu.screenshot(os.path.join(args.out, f"f{emu.frames_run:06d}.png"))
                if ram_f:
                    ram_f.write(f"{emu.frames_run} {emu.ram().hex()}\n")
                shot_i += 1
    emu.screenshot(os.path.join(args.out, f"final_{emu.frames_run:06d}.png"))
    if ram_f:
        ram_f.write(f"{emu.frames_run} {emu.ram().hex()}\n")
        ram_f.close()
    if args.audio:
        import soundfile as sf
        import numpy as np
        a = emu.audio_array().astype("float32") / 32768.0
        sf.write(args.audio, a, emu.sample_rate)
        print("audio:", args.audio, f"{len(a)/emu.sample_rate:.2f}s")
    if args.state:
        with open(args.state, "wb") as f:
            f.write(emu.savestate())
        print("state:", args.state)
    print(f"ran {emu.frames_run} frames, {shot_i} shots -> {args.out}/")
    emu.close()


if __name__ == "__main__":
    main()

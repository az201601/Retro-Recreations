#!/usr/bin/env python3
"""
ram_watch.py -- record per-frame CPU RAM while applying inputs, to reverse
engineer game variables (positions, velocities, timers).

    .venv/bin/python tools/ram_watch.py --state work/ss/frozen.state \
        --inputs "10:start 40: 120:right 60:" --out work/ramlog.csv
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nes_harness import NesEmu  # noqa: E402
from run_script import parse_timeline, CORE, ROM  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=None)
    ap.add_argument("--timeline", default="120:")
    ap.add_argument("--out", default="work/ramlog.csv")
    ap.add_argument("--every", type=int, default=1)
    args = ap.parse_args()

    emu = NesEmu(CORE).load(ROM)
    import nes_harness
    emu._log_cb = nes_harness.LOG_CB(lambda l, m: None)
    if args.state:
        emu.loadstate(open(args.state, "rb").read())

    rows = []
    frame = 0
    for frames, btns in parse_timeline(args.timeline):
        emu.set_buttons(*btns) if btns else emu.release_all()
        for _ in range(frames):
            emu.run(1)
            frame += 1
            if frame % args.every == 0:
                ram = emu.ram()
                rows.append([frame, ",".join(btns) if btns else ""] + list(ram))
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["frame", "input"] + [f"{i:02X}" for i in range(2048)])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {args.out}")


if __name__ == "__main__":
    main()

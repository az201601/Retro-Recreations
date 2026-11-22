#!/usr/bin/env python3
"""
capture_audio.py -- record NES audio via the harness.

Supports channel isolation: nestopia can mute individual APU channels
(square1/2, triangle, noise, DPCM), so the same input timeline can be recorded
multiple times to separate music from sound effects.

    .venv/bin/python tools/capture_audio.py --timeline "..." --out work/audio_run \
        [--state f.state] [--channels all|sq1|sq2|tri|noi|dpcm|music|muted]
"""
import argparse
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nes_harness import NesEmu  # noqa: E402
from run_script import parse_timeline, CORE, ROM  # noqa: E402

VOL_KEYS = {
    "sq1": "nestopia_audio_vol_sq1",
    "sq2": "nestopia_audio_vol_sq2",
    "tri": "nestopia_audio_vol_tri",
    "noi": "nestopia_audio_vol_noise",
    "dpcm": "nestopia_audio_vol_dpcm",
}
ALL = ["sq1", "sq2", "tri", "noi", "dpcm"]
PRESETS = {
    "all": ALL,
    "music": ["sq1", "sq2", "tri"],
    "muted": [],
    **{c: [c] for c in ALL},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default="600:")
    ap.add_argument("--state", default=None)
    ap.add_argument("--channels", default="all")
    ap.add_argument("--out", default="work/audio_capture.wav")
    ap.add_argument("--gain", type=float, default=1.0)
    args = ap.parse_args()

    emu = NesEmu(CORE).load(ROM)
    import nes_harness
    emu._log_cb = nes_harness.LOG_CB(lambda l, m: None)
    audible = set(PRESETS.get(args.channels, ALL))
    for ch, key in VOL_KEYS.items():
        emu.options[key] = "100" if ch in audible else "0"
    if args.state:
        emu.loadstate(open(args.state, "rb").read())
        # force option re-read? volumes are applied at load; re-apply via state load is fine
    emu.clear_audio()
    for frames, btns in parse_timeline(args.timeline):
        emu.set_buttons(*btns) if btns else emu.release_all()
        emu.run(frames)
    a = emu.audio_array().astype("float32") / 32768.0
    a *= args.gain
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    sf.write(args.out, a, emu.sample_rate)
    print(f"wrote {args.out}: {len(a)/emu.sample_rate:.2f}s peak={np.abs(a).max():.3f}")


if __name__ == "__main__":
    main()

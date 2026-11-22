#!/usr/bin/env python3
"""
capture_panorama.py -- drive the player right through the stage, capturing a
sprite-free 256x240 screen render at every new camera position. Saves
assets/stage1/screen_NN.png + panorama.json (scroll offsets) for GMS level building.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nes_harness import NesEmu  # noqa: E402
from nest_state import parse_state, cpu_ram, ppu_dump  # noqa: E402
from nes_render import StateView, load_rom, master_palette  # noqa: E402
from run_script import CORE, ROM  # noqa: E402


def main():
    out = "assets/stage1"
    os.makedirs(out, exist_ok=True)
    _prg, chr_rom = load_rom()
    master = master_palette()
    emu = NesEmu(CORE).load(ROM)
    emu.loadstate(open("work/ss/frozen.state", "rb").read())

    def pos():
        p = parse_state(emu.savestate())
        ram = cpu_ram(p)
        oam = ppu_dump(p)["oam"][:256]
        xw = (ram[0x313] | (ram[0x314] << 8)) >> 8
        sx = oam[7]
        return xw, sx, ram[0xC2]

    screens = {}
    def snap(tag):
        xw, sx, y = pos()
        cam = xw - sx
        cam = max(0, cam)
        if cam not in screens:
            st = StateView(emu.savestate(), chr_rom)
            img = st.render(master, sprites=False).astype(np.uint8)
            screens[cam] = img
            print(f"  snap {tag}: worldX={xw} sprX={sx} cam~{cam} y={y}")

    emu.set_buttons("start"); emu.run(10); emu.release_all(); emu.run(40)
    snap("start")
    # walk to the mug, hop on, then keep hopping right
    emu.set_buttons("right")
    for f in range(120):
        emu.run(1)
        xw, _, _ = pos()
        if xw >= 58:
            break
    snap("mug")
    emu.set_buttons("right", "a"); emu.run(20); emu.release_all(); emu.run(20)
    snap("burger")
    for hop in range(25):
        emu.set_buttons("right"); emu.run(12)
        emu.set_buttons("right", "a"); emu.run(18)
        emu.release_all(); emu.run(14)
        snap(f"hop{hop}")
        xw, _, _ = pos()
        if xw >= 500:
            break
    meta = [{"cam": c, "file": f"screen_{i:02d}.png"} for i, c in enumerate(sorted(screens))]
    for i, c in enumerate(sorted(screens)):
        Image.fromarray(screens[c]).save(os.path.join(out, f"screen_{i:02d}.png"))
    with open(os.path.join(out, "panorama.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(f"{len(meta)} screens -> {out}/")


if __name__ == "__main__":
    main()

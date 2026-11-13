# Capture tools

These run the ROM headlessly in the Mesen libretro core, dump the picture, PPU state, RAM and
audio every frame, and build the assets in `recreation/`. Linux, Python 3.11+.

## Setup

```bash
pip install numpy pillow soxr soundfile

git clone --depth 1 https://github.com/libretro/Mesen.git
cd Mesen
git apply /path/to/Retro-Recreations/tools/capture/mesen_libretro_debug.patch
cd Libretro && make -j2
cp mesen_libretro.so /path/to/Retro-Recreations/tools/capture/work/
```

The patch adds read-only debug outputs to the core (pattern tables, nametables, palette, OAM,
scroll registers, a per-scanline record used to find mid-frame bank switches, and a log of the
CPU writes to the sound registers $4000-$4017). It does not change emulation. It also adds the
environment variable `MESEN_MUTE`, a bit mask that silences sound channels in the output
(1 square 1, 2 square 2, 4 triangle, 8 noise, 16 DMC), used to record channels separately. `work/` is git-ignored. Set `MESEN_CORE` to use a core stored elsewhere.

## Run

```bash
cd tools/capture
python3 capture.py       # ~30 s: all emulator runs -> work/
python3 build_gfx.py     # PNGs  -> recreation/01_intro_title/assets
python3 build_audio.py   # OGGs  -> recreation/01_intro_title/assets/sounds
python3 capture_menu.py  # ~1 min: menu runs -> work/menu_*.pkl (about 2 GB)
python3 build_menu.py    # PNGs and OGGs -> recreation/02_title_menu/assets
python3 sim.py           # checks the GML logic against the emulator, pixel for pixel
python3 capture_prison.py  # ~5 min: night-scene runs -> work/prison_*.pkl (about 9 GB)
python3 build_prison.py    # PNGs and OGG -> recreation/03_night_scene/assets
python3 sim_prison.py      # ~2 min: checks the night scene, pixel for pixel
```

## Files

| File | Purpose |
|---|---|
| `emu.py` | Minimal libretro frontend (ctypes). One `Emu()` per process: the core keeps global state. |
| `ppu.py` | Reference NES renderer that rebuilds a frame from the dumped PPU state. |
| `capture.py` | The emulator runs: no input, and START pressed on various frames. |
| `build_gfx.py` | Cuts the spotlight, wall masks and title layers out of the PPU state. |
| `build_audio.py` | Cuts the four sounds and retimes them to 800 samples per frame at 48 kHz. |
| `scenario.py` | Runs one input schedule per process and stores frames, PPU state, RAM, sound-register writes and audio. |
| `capture_menu.py` | The menu runs: every button, timing probes, and the separated sound channels. |
| `build_menu.py` | Cuts the menu panels, the title fade-out and the menu sounds / music stems. |
| `sim.py` | Python port of `obj_intro` Create/Step/Draw (steps 01 and 02). Keep it in step with the `.gml` files. |
| `capture_prison.py` | The night-scene runs: no input, other buttons, START on many frames. |
| `build_prison.py` | Builds the two background bands, the beams, the blimp and the alarm sound. |
| `sim_prison.py` | Python port of the night-scene parts of `obj_intro` Step/Draw, with the picture and sound checks. |

`tools/dis/dis6502.py` is a small 6502 disassembler for the ROM's PRG banks
(`dis6502.py 7 C5A2 C690`, or `dis6502.py find 85 49` to search for bytes).

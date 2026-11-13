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

The patch only adds read-only debug outputs to the core (pattern tables, nametables, palette,
OAM, scroll registers, and a per-scanline record used to find mid-frame bank switches). It does
not change emulation. `work/` is git-ignored. Set `MESEN_CORE` to use a core stored elsewhere.

## Run

```bash
cd tools/capture
python3 capture.py       # ~30 s: all emulator runs -> work/
python3 build_gfx.py     # PNGs  -> recreation/01_intro_title/assets
python3 build_audio.py   # OGGs  -> recreation/01_intro_title/assets/sounds
python3 sim.py           # checks the GML logic against the emulator, pixel for pixel
```

## Files

| File | Purpose |
|---|---|
| `emu.py` | Minimal libretro frontend (ctypes). One `Emu()` per process: the core keeps global state. |
| `ppu.py` | Reference NES renderer that rebuilds a frame from the dumped PPU state. |
| `capture.py` | The emulator runs: no input, and START pressed on various frames. |
| `build_gfx.py` | Cuts the spotlight, wall masks and title layers out of the PPU state. |
| `build_audio.py` | Cuts the four sounds and retimes them to 800 samples per frame at 48 kHz. |
| `sim.py` | Python port of `obj_intro` Create/Step/Draw. Keep it in step with the `.gml` files. |

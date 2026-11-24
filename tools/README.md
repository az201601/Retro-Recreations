# Spotlight intro extraction and GMS 1.4 handoff

`python3 tools/capture_spotlight_intro.py` replays the USA ROM from power-on, captures NES frames 1–900 at native 256×240, and writes the GMS sprite-strip atlases plus `extracted/spotlight_intro/frame_map.csv`. Every atlas cell was checked pixel-for-pixel against the corresponding emulator capture. GMS import and playback instructions are in [`docs/spotlight_intro.md`](../docs/spotlight_intro.md).

## Build the capture frontend

The build products and downloaded emulator sources are ignored by Git. From the repository root:

```bash
git clone --depth 1 https://github.com/libretro/libretro-fceumm tools/emu/libretro-fceumm
git clone --depth 1 https://github.com/libretro/libretro-common tools/emu/libretro-common
cp tools/emu/libretro-common/include/libretro.h tools/emu/lc_include/libretro.h
(cd tools/emu/libretro-fceumm && make -f Makefile.libretro -j2)
(cd tools/emu && gcc -O2 -o retroshot retroshot.c -I lc_include \
  ./libretro-fceumm/fceumm_libretro.so \
  -Wl,-rpath,'$ORIGIN/libretro-fceumm' -lm)
```

Install Pillow for atlas generation if needed, then run:

```bash
python3 -m pip install Pillow
python3 tools/capture_spotlight_intro.py
```

Raw PPM captures are temporary and written under `tools/out/` (ignored). The checked-in deliverable is the PNG sprite strips, frame map, intro WAV, GML snippets, and editor instructions—not emulator build artifacts.

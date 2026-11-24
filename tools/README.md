# Spotlight intro extraction and GMS 1.4 handoff

`python3 tools/capture_spotlight_intro.py` replays the USA ROM from power-on, captures NES frames 1–900 at native 256×240, and writes the GMS sprite-strip atlases plus `extracted/spotlight_intro/frame_map.csv`. Every atlas cell was checked pixel-for-pixel against the corresponding emulator capture. GMS import and playback instructions are in [`docs/spotlight_intro.md`](../docs/spotlight_intro.md).

`python3 tools/extract_one_player_menu.py` continues from power-on, presses START at frame 1000, extracts the static menu screen at frame 1006 with the 2-player row removed, and writes separate menu-music and selection-SFX WAVs. The menu music comes from a matching no-input run; subtracting that audio from the START run over frames 1000–1015 isolates the one-shot selection sound. See [`docs/title_menu_1p.md`](../docs/title_menu_1p.md) for GMS resources and the one-player-only input flow.

## Level extraction

`tools/nes_state.py` parses FCEUmm savestates and re-renders the PPU from CHR
ROM, nametables, palette and OAM. `tools/extract_room.py` writes the GMS
handoff folder for one captured window and `tools/verify_room.py` proves the
tileset + tilemap rebuild it exactly. `tools/autoplay.py` drives the emulator
interactively for scripted capture. See [`docs/levels.md`](../docs/levels.md).

For whole stages use the two-stage pipeline:

```bash
# 1. walk the stage, dropping a savestate every 64 pixels of progress
.venv/bin/python tools/solve_route.py \
  --state tools/emu/out/scrollcap/s10954.fcs \
  --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" \
  --workdir tools/emu/out/solve20 --iterations 200 --beam 8 --checkpoint-step 64

# 2. stitch those checkpoints into one wide strip + tileset + tilemap
.venv/bin/python tools/stitch_level.py \
  --workdir tools/emu/out/solve20 \
  --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" \
  --out tools/emu/out/stage20 \
  --start tools/emu/out/scrollcap/s10954.fcs --max-cam 1200
```

`stitch_level.py` re-enters every checkpoint, advances one frame, and captures
the savestate and the frame together, so a window's picture always matches its
state. It reports the background pixel error per window and how many pixels had
to be taken from a neighbouring window (sprites covering them).

The headless frontend now also supports savestates (`state`/`load`), RAM dumps
(`ram`), RAM guards for survivable capture (`guard`/`unguard`), `poke`, and an
interactive stdin protocol (`-i`).

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
python3 tools/extract_one_player_menu.py
```

Raw PPM captures and intermediate full-run WAVs are temporary and written under `tools/out/` (ignored). Checked-in deliverables are the sprite strips, frame map, single-player title image, intro/menu-music/selection-SFX WAVs, GML snippets, and editor instructions—not emulator build artifacts.

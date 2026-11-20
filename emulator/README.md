# NES oracle: headless, frame-accurate capture of the reference ROM

This is the measuring instrument for the Gradius recreation. It runs the real
NES ROM in a cycle-accurate emulator, headless and deterministic, and writes
out per-frame pictures, APU audio, frame hashes, and memory watches. Every
number the recreation is matched against comes from here.

```
emulator/
  libretro_host.c   headless libretro frontend ("nesrun") - our code
  libretro.h        libretro API header (upstream copy)
  build.sh          builds nesrun + pinned emulator cores into emulator/out/
  oracle.sh         convenience wrapper + self-test (REC/CHECK modes)
  .build/           cloned core sources (git-ignored)
  out/              built binaries and cores (git-ignored)
```

## Why two cores

| core | role | why |
|------|------|-----|
| **Nestopia** (libretro, pinned `f1e02d1`) | the **pixel oracle** | cycle-accurate CPU/PPU/APU, `XRGB8888` output, stable libretro memory maps |
| **FCEUmm** (libretro, pinned `77468e5`) | **cross-check** | independent CPU/PPU/APU implementation, and it can be forced onto an external palette file |

Cross-check result with both cores on one palette (frames 300-340 of the
attract sequence): **41/41 frames byte-identical**. With a one-frame phase
offset allowed, the whole 600-frame run agrees. See
`../oracle/palette/README.md` for what still differs and why.

Both are built from source at pinned commits, so the oracle is reproducible
on any machine with a C toolchain - nothing binary is stored in the repo.
The one thing that *is* stored is the recovered palette
(`oracle/palette/nestopia.pal`), because it is the visual target.

## Accuracy properties (verified by `oracle.sh selftest`)

1. **Deterministic** - same frame count + same input script = byte-identical
   frame hashes across runs and across processes.
2. **Frame-exact** - video is delivered once per emulated frame at
   `256x240` (NTSC PPU, no overscan masking, no NTSC filter), so frame *n*
   of the oracle is frame *n* of the emulator. Audio is 48000 Hz stereo
   (800 samples per frame), i.e. the APU's own output, unfiltered.
3. **Inspectable** - system RAM, palette RAM, OAM, nametables and CHR are
   readable per frame through the core's memory map, so the recreation is
   compared on *state*, not just on pixels.
4. **One palette** - the NES outputs palette *indices*, not colour; the
   emulator's palette table is a free choice. `oracle/palette/` pins it, and
   `tools/palette_probe.py` re-derives it from any core on demand.

Frame timing used everywhere: **60.098814 Hz** (NTSC PPU), i.e. the NES
draws 60.0988 frames per second, 16.638 ms apart. In GameMaker games that are
fixed at 60 fps, a frame counter is therefore *not* the same clock as the
NES; `oracle.sh` reports every capture against this clock so drift is visible.

## Usage

```
./emulator/build.sh                 # first time, ~2 min
./emulator/oracle.sh selftest       # prove determinism + cross-core agreement

# capture 900 frames of power-on through the title screen
./emulator/oracle.sh rec title --frames 900 --png-every 30

# capture with a controller script (see scripts/input format below)
./emulator/oracle.sh rec start --frames 1200 --input inputs/start.txt \
    --png-every 10 --wav

# what does the game do for frames 300..320?
./emulator/oracle.sh check ref/title --frames 320 --png 300-320
```

Outputs land in `oracle/out/<name>/`: `f%06d.png`, `audio.wav`, `hash.txt`,
`ram.txt` (when `--watch` is given), plus `meta.txt` describing exactly how
the capture was made.

## `nesrun` directly

```
nesrun --core CORE.so --rom ROM.nes --frames N
       [--dir DIR] [--png LIST] [--png-every K] [--png-from N]
       [--scale S] [--crop X,Y,W,H]
       [--wav FILE] [--hash FILE]
       [--var KEY=VALUE] [--var-file FILE]
       [--input FILE] [--watch NAME:OFF:LEN]... [--watch-out FILE]
       [--save-state FRAME:FILE] [--load-state FILE]
       [--sysdir DIR] [--probe] [--mem-list] [--quiet]
```

Frame numbering starts at 0 for the first emulated frame after power-on.

**Input scripts** (`--input`), one rule per line, later rules OR together:

```
# frame  FROM-TO  BUTTONS      buttons: U D L R A B S(select) T(start)
0-100   -                     # nothing held
101-140 T                     # press start
141-180 -
200-260 R
```

**Watches** (`--watch`): `CPU:0:2048` dumps 2048 bytes of system RAM from
`$0000` each frame; regions are those the core publishes - `CPU` (real 6502
addresses) plus e.g. `PPUPAL:0:32`, `PPUOAM:0:32`, `PPUNTA:0:2048`, `PPUCHR`.

**Core options** default to each core's own defaults. The ones that matter
for pixel work are set explicitly by `oracle.sh`:

```
nestopia_blargg_ntsc_filter=disabled   keep raw PPU pixels, no NTSC blur
nestopia_overscan_h_left=0             no overscan masking: full 256x240
nestopia_overscan_h_right=0
nestopia_overscan_v_top=0
nestopia_overscan_v_bottom=0
nestopia_nospritelimit=disabled        hardware 8-sprites/scanline behaviour
nestopia_audio_filter=disabled         raw APU mixer output
```

## Known limits

* The oracle gives *behaviour*, not source. Reading game state out of the
  oracle (which RAM bytes are the player position, how levels are streamed)
  is a separate reverse-engineering job; the watches above are the raw
  material for it.
* Nestopia's libretro build is cycle-accurate but not a hardware
  logic-level simulator; for the handful of cases where real silicon and
  all emulators disagree (some sprite-0-hit and $2007 read corner cases),
  treat hardware documentation as the tie-breaker.
* Mesen 2 is the cross-reference "gold standard" UI build. Release binaries
  are not downloadable from this sandbox, so it is documented for use on your
  own machine in `../oracle/MESEN-REFERENCE.md` - including the exact settings
  that make it a valid comparison against these captures.

## Related tools

| tool | purpose |
|---|---|
| `emulator/oracle.sh` | capture / re-check / diff reference runs, self-test |
| `tools/pngcmp.py` | exact and palette-normalised PNG comparison |
| `tools/palette_probe.py` | recover a core's 64-entry palette as `.pal`/`.c`/`.json` |

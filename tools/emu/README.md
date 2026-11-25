# Pinned fceumm headless capture harness

Frame-accurate NES research harness for the original USA ROM of **Chip 'n Dale Rescue Rangers 2**. It is **not** a gameplay engine or a stand-alone game. `build_fceumm.sh` clones the upstream libretro core at commit `fb919fb6fa881aaa6279b765d480220579e5c606`, applies `patches/fceumm_capture_layers.patch`, and compiles `fceumm_headless.c`.

```bash
./tools/emu/build_fceumm.sh
python3 tools/extract/capture_stage_01.py --part all
# output: tools/out/emu/stage_01_verified/ (ignored by git)
```

The 20 small, tracked `checkpoints/stage_01_restaurant/frame_N.state` files and absolute-frame `inputs/stage_01_restaurant_*` scripts reproduce opening, Seating → Kitchen → Grill → Monterey → Water Rabbit, and a **cheat-assisted** boss defeat. The independent replay from preserved frame 11800 to frame 20350 is checked byte-for-byte against the expected save. Frame 11200 does **not** replay to that distinct frame-11800 checkpoint; do not chain them as if identical. The boss sample uses lives cheat `00A7:03` plus player-HP cheat `0067:01`; it never sets boss HP. A no-cheat victory was not confirmed.

## Invocation

```bash
tools/out/emu/fceumm_headless \
  --core tools/out/emu/fceumm_libretro.so \
  --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" \
  --load-state tools/emu/checkpoints/stage_01_restaurant/frame_11800.state \
  --start-frame 11800 --frames 12000 \
  --inputs tools/emu/inputs/stage_01_restaurant_route_to_boss.txt \
  --cheat 00A7:03 --out tools/out/emu/sample \
  --shots 11900,12000 --shot-every 32 --shot-start 11801 \
  --ppu-dir tools/out/emu/sample --ppu-every 8 --ppu-start 11801 \
  --ram-dir tools/out/emu/sample \
  --ram-trace tools/out/emu/sample/ram_trace.dat \
  --oam-trace tools/out/emu/sample/oam_trace.dat \
  --wav tools/out/emu/sample/audio.wav \
  --audio-index tools/out/emu/sample/audio_frame_index.dat
```

- `--inputs` CSV lines: `absolute_frame,down|up,BUTTON` for `A,B,SELECT,START,UP,DOWN,LEFT,RIGHT`. Events are stably sorted by frame, preserving same-frame file order. Loading a checkpoint with `--start-frame N` starts emulating N+1; events through N establish the held-input state.
- `--save-state PATH` writes at the final frame unless `--save-state-frame N` is also given.
- `--shots`, `--shot-every N`/`--shot-start N` write 256×240 P6 PPM frames. `--ram-dir` writes 2048-byte system RAM for screenshot **and** PPU-sampled frames.
- `--ppu-dir` with `--ppu-every N`/`--ppu-start N` saves mapped PPU snapshots independently of screenshot frequency. Captured 8×8 BG and OAM sprites can be decoded with `tools/extract/nes_ppu.py`.
- `--ram-trace` and `--oam-trace` write every emulated frame after the checkpoint (optional `--ram-trace-start` / `--oam-trace-start`). `RRT1` / `OAT1` each begin with a four-byte ASCII magic, then little-endian `uint32 first_frame` and `uint32 bytes_per_frame`; RAM is 2048 bytes/frame, OAM is 256 bytes/frame. Frame data follow immediately in order.
- `--audio-index` requires `--wav`. `AFI1` is four-byte ASCII magic + little-endian `uint32 first_frame`, `uint32 sample_rate` + **one little-endian `uint64` cumulative stereo-sample count per frame**, where boundary zero before first frame is implicit. Last boundary equals the 16-bit stereo WAV frame count. Use it instead of estimating samples per emulated frame; fceumm alternates ~798/799 samples at 48 kHz. `tools/extract/export_stage_01_audio.py` makes exact cuts.
- Standard libretro VRAM APIs do **not** expose the mapped nametables/CHR needed here. The patched core's **private** memory ID `0xFCE1` returns **0x31E0 bytes**: mapped pattern tables `[0x0000:0x2000]`, four mirrored nametables `[0x2000:0x3000]`, NES palette indices `[0x3000:0x3020]`, OAM `[0x3020:0x3120]`, and the pinned core's 64 RGB palette triples `[0x3120:0x31E0]`. This is for extraction only and must not be mistaken for standard libretro `RETRO_MEMORY_VIDEO_RAM`.

## Layer capture and precautions

With the **patched core**, run with environment `FCEUMM_HIDE_SPRITES=1` to capture BG-only or `FCEUMM_HIDE_BG=1` for sprite-only. A previous upstream ternary-precedence bug made older supposedly BG-only screenshots invalid; do not identify `background/full_frame_11200.png` / `bg_frame_11200.png` as authentic sprite-free images. The patch fixes independent toggling. jsnes 3.x also produced incorrect swapped red/blue channels in earlier trials, so Stage 1 palette work uses only pinned fceumm.

The raw traces/PPMs/PPU snapshots can be hundreds of MB. They belong in `tools/out/` (gitignored); the small input files, save-state checkpoints, core patch and extraction scripts are tracked.

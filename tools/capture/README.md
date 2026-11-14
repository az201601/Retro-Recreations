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
(1 square 1, 2 square 2, 4 triangle, 8 noise, 16 DMC), used to record channels separately. For finding code it has a write watch (`MESEN_WATCH=lo,hi` logs CPU writes to that address range with the program counter), a dump of the mapped program ROM and a bitmap of executed addresses. `work/` is git-ignored. Set `MESEN_CORE` to use a core stored elsewhere.

## Run

```bash
cd tools/capture
python3 capture.py       # ~30 s: all emulator runs -> work/
python3 build_gfx.py     # PNGs  -> recreation/01_intro_title/assets
python3 build_audio.py   # OGGs  -> recreation/01_intro_title/assets/sounds
python3 capture_menu.py  # ~1 min: menu runs -> work/menu_*.pkl (about 3 GB)
python3 build_menu.py    # PNGs and OGGs -> recreation/02_title_menu/assets
python3 sim.py           # checks the GML logic against the emulator, pixel for pixel
python3 capture_prison.py  # ~5 min: night-scene runs -> work/prison_*.pkl (about 9 GB)
python3 build_prison.py    # PNGs and OGG -> recreation/03_night_scene/assets
python3 sim_prison.py      # ~2 min: checks the night scene, pixel for pixel
python3 capture_news.py      # ~6 min: newscaster runs -> work/news_*.pkl (about 5 GB)
python3 build_news_audio.py  # OGGs -> recreation/04_newscaster/assets/sounds
python3 build_news.py        # PNGs -> recreation/04_newscaster/assets/sprites, and the cutscene model
python3 news_data.py         # packs the model into the tables the GML uses
python3 gen_news_gml.py      # writes those tables into 04_newscaster/gml/obj_intro_Create.gml
python3 sim_news.py          # ~30 s: checks the newscaster cutscene, pixel for pixel
python3 capture_level1.py    # ~2 min: level 1 runs -> work/lv1_*.pkl (about 1 GB)
python3 build_level1.py      # PNGs and OGGs -> recreation/05_level1_map/assets
python3 sim_level1.py        # checks the level background, fades and exit, pixel for pixel
python3 capture_player.py    # ~2 min: player runs, Chip and Dale -> work/pl_*.pkl, work/dl_*.pkl (about 3 GB); needs level1_route.json
python3 build_player.py      # PNG, OGG -> recreation/06_level1_player/assets and 07_level1_dale/assets; tables -> work/player_tables.gml
python3 sim_player.py        # checks the player: positions, sprite tiles, picture, landing sound
python3 capture_crates.py    # ~4 min: crate runs, Chip and Dale -> work/cr_*.pkl, work/dl_cr_*.pkl (about 4 GB)
python3 build_crates.py      # PNG, OGG -> recreation/08_level1_crates/assets; tables -> work/cr_tables.pkl, work/crate_tables.gml
python3 sim_crates.py        # checks crates and bonus boxes: memory, sprite tiles, picture, sounds (--old: also the player runs)
python3 capture_enemies.py   # ~1 min: enemy runs -> work/en_*.pkl, work/dl_en_*.pkl (about 3 GB)
python3 build_enemies.py     # PNG, OGG -> recreation/09_level1_enemies/assets; tables -> work/en_tables.pkl, work/enemy_tables.gml
python3 sim_enemies.py       # ~20 s: checks the enemies: memory, sprites, picture, sounds (--old, ~80 s: also the player and crate runs)
python3 sim_enemies_route.py # checks the enemies of the whole section against the route recordings
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
| `capture_news.py` | The newscaster runs: no input, B in several patterns, START on many frames, separated sound channels. |
| `news_model.py` | Reads text, palette, sound writes and the game's object table out of the runs and derives the cutscene model (pages, actor tracks). |
| `build_news_audio.py` | Builds the two music loops and the six typing sounds, and finds the note starts used for muting. |
| `build_news.py` | Builds the studio background, the font tiles and the 8x8 sprite pieces in 7 brightness steps. |
| `news_data.py` | Packs model, graphics index and sound data into flat tables. |
| `gen_news_gml.py` | Writes those tables into the marked block of the step 04 Create event. |
| `sim_news.py` | Python port of the newscaster parts of `obj_intro` Step/Draw, with the picture and typing-sound checks. |
| `level1_route.json` | Input recording: level 1, section 1 played from start to exit without taking a hit. |
| `capture_level1.py` | The level runs: both ways into the level, the recorded playthrough, and long sound-only runs for the music. |
| `build_level1.py` | Builds the section's background from the playthrough (8 screens, 7 brightness steps) and the two music loops. |
| `sim_level1.py` | Python port of the step 05 `obj_stage1` End Step/Draw (background, fades, camera position, exit). |
| `capture_player.py` | The player runs: scripted moves at the start, falls into the first pit, random buttons, three ways out of the last screen. `pl_` runs are Chip, `dl_` runs the same with Dale. |
| `build_player.py` | Builds Chip's and Dale's 8x8 tiles in 7 brightness steps, the landing sound, the block map of the section and the sprite tables (as GML text in `work/player_tables.gml`, pasted into the step 06 Create events). Needs `lv1_route0..2` from `capture_level1.py`. |
| `sim_player.py` | Python port of `obj_player` (steps 06 and 07) and the step 06 `obj_stage1`. Compares player memory, sprite tiles, the picture and the landing sound with the runs. Keep it in step with the `.gml` files. |
| `explore.py` | Helper for trying things out by hand in Python: one emulator, named savestates, runs of buttons from a savestate. Not needed for the builds. |
| `capture_crates.py` | The crate runs: carrying, the throws, far throws, the bonus boxes, a pit with a crate, random buttons, short runs for the order of the sounds; some repeated with Dale; three sound-only runs with single channels. |
| `build_crates.py` | Builds the player tiles with the carrying and throwing pictures (they replace the step 06 / 07 strips), the crate sprite and the eyes, the four sounds, the list of crates and bonus boxes with their background patches, and the tables (as GML text in `work/crate_tables.gml`, pasted into the step 08 Create events). Run it before `sim_crates.py`: without `work/cr_tables.pkl` the tile and picture checks are skipped. |
| `sim_crates.py` | Python port of the step 08 `obj_player`, `obj_crate` and `obj_stage1`. Compares memory, sprite tiles, the picture and the sound starts with the crate runs, and with `--old` with the player runs. Keep it in step with the `.gml` files. |
| `capture_enemies.py` | The enemy runs: a crate thrown into the first flyer (two ways), hiding under a crate below it, the first cook knocked out by the crate the player hides under and by a thrown one, the fork knocked down, a pit, six runs of random buttons; two repeated with Dale; four sound-only runs with single channels. |
| `build_enemies.py` | Builds the enemy tile strip and the picture tables from the ROM's picture lists (bank 5), and the three sounds. Adds files to the step 09 assets, deletes nothing else. |
| `sim_enemies.py` | Python port of the step 09 GML (`obj_stage1`, `obj_player`, `obj_crate`, `obj_enemy`). Compares memory (every place of the object list), sounds, sprites with their order, and the picture. Keep it in step with the `.gml` files. |
| `sim_enemies_route.py` | The same enemy code against the route recordings (all twelve objects of the section), with the player and camera taken from the NES memory. |

`tools/dis/script.py` lists the byte code that drives the game's objects (`script.py 4 82D9`; the
scripts of the level 1 enemies are in bank 4). Opcodes above `$3F` are not decoded and are shown as `??`.

`tools/dis/dis6502.py` is a small 6502 disassembler for the ROM's PRG banks
(`dis6502.py 7 C5A2 C690`, or `dis6502.py find 85 49` to search for bytes).
`tools/dis/cols.py` prints the same listing in columns.

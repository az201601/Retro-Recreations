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
python3 capture_hurt.py      # ~6 min: hurt / status screen / game over runs -> work/hu_*.pkl, work/dl_hu_*.pkl
python3 build_hurt.py        # PNG, OGG -> recreation/10_level1_hurt/assets; tables -> work/hu_tables.pkl, work/hurt_tables.gml
python3 sim_hurt.py          # ~2.5 min: checks step 10: memory, sprites, picture, sounds (--old, ~1.5 min: also the runs of steps 06-09)
python3 capture_kitchen.py   # ~8 min: kitchen runs of steps 11 and 12 -> work/kt_*.pkl
python3 build_kitchen.py     # ~15 s: PNG -> recreation/11_level1_kitchen/assets; block map -> work/kt_blocks.pkl, work/kt_tables.gml
python3 sim_kitchen.py       # ~20 s: checks step 11: memory, landing sound, picture (--old, ~4.5 min: all runs of steps 06-10)
python3 build_kitchen_boxes.py # PNG, OGG -> recreation/12_level1_kitchen_crates/assets; boxes -> work/kt_boxes.pkl, work/kt_box_tables.gml
python3 sim_kitchen2.py      # ~50 s: checks step 12: memory, objects, sounds, picture (--old --nopic, ~1 min: all runs of steps 06-10)
python3 capture_mice.py      # several minutes: the kitchen runs again from frame 3680, the mouse runs, 6 sound-only runs -> work/mi_*.pkl
python3 build_mice.py        # PNG, OGG -> recreation/13_level1_kitchen_mice/assets; tables -> work/mi_tables.pkl, work/mouse_tables.gml
python3 sim_mice.py          # ~100 s: checks step 13: memory, objects, sounds, picture (--old --nopic, ~40 s: all runs of steps 06-10)
python3 capture_caps.py     # ~12 min: 16 runs with the bottle caps, 11 with memory written, 4 sound-only runs -> work/cp_*.pkl
python3 build_caps.py       # PNG, OGG -> recreation/14_level1_kitchen_caps/assets; tables -> work/cp_tables.pkl, work/cap_tables.gml
python3 sim_caps.py         # ~5.5 min: checks step 14: memory, objects, sounds, picture (--old --nopic, ~40 s: all runs of steps 06-10)
python3 capture_sec3.py     # ~5 min: the third section: the route to the sink, 13 runs, 7 with memory written -> work/s3_*.pkl; needs level1_route3.json
python3 build_sec3.py       # ~5 s: PNG -> recreation/15_level1_stove/assets; block map -> work/s3_blocks.pkl, work/s3_tables.gml
python3 sim_sec3.py         # ~6 min: checks step 15 and again everything sim_caps.py checks (--new: only the third section, ~20 s; --old --nopic: all runs of steps 06-10)
python3 measure_sec3.py     # ~1 min: step 15, emulator only: when a carried crate is bright (kitchen / third section), the landing sound in the sink
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
| `capture_hurt.py` | The step 10 runs: the route without avoiding enemies, a death by enemies, random buttons near enemies, the status screen, three falls with GAME OVER, the continue screen (CONTINUE, END, until no credit is left); seven repeated with Dale; the hurt and stun sounds alone, asked for by writing the game's sound request byte. Recordings are stored in parts of 1200 frames with compressed pictures. |
| `build_hurt.py`, `build_hurt_screens.py` | Build the step 10 assets: the two new player pictures from the ROM's picture lists, hearts, star, the status, GAME OVER and continue screens (cut from the recordings, with checks that the cut-out parts are all that changes), the character's movements on the continue screen, five sounds. |
| `sim_hurt.py` | Python port of the step 10 GML. As `sim_enemies.py`, plus hearts, the status screen, GAME OVER and the continue screen; all sprites and the whole picture are compared. Keep it in step with the `.gml` files. |
| `level1_route2.json` | Buttons for the kitchen, continuing `level1_route.json` from frame 3760 to the kitchen's exit, without being hurt. Found by a savestate search. |
| `capture_kitchen.py` | The step 11 runs: the kitchen from entry to exit, the exit reached in three ways, random buttons in the shaft, the top edge, the status screen, held buttons at the section change, a fall in the shaft, lost lives up to GAME OVER; three repeated with Dale. |
| `build_kitchen.py` | Builds the kitchen's 9 background screens in 7 brightness steps from the route recording (the map is put together from the scroll position in the game's memory), the wall piece around the exit hole, and the block map. |
| `sim_kitchen.py` | Python port of the step 11 GML: `sim_hurt.py` plus the second section, a camera that also goes up, and the shaft's row-by-row picture. Compares memory, landing sound and the whole picture, leaving out what the port does not have yet (mice, bonus boxes). Keep it in step with the `.gml` files. |
| `kitchen_runs.json` | Buttons from power-on for the 10 step 12 runs (`cr_a0` … `cr_h3`): crates picked up, thrown in every way, bonus boxes, the acorn. Found by a savestate search that keeps away from the mice. |
| `build_kitchen_boxes.py` | Step 12: finds the kitchen's crates, bonus boxes and item crates in the block map and, from the ROM's second copy of each screen, what is behind each; cuts the acorn, star and "1UP" sprites and the extra-life sound. |
| `sim_kitchen2.py` | Python port of the step 12 GML: `sim_kitchen.py` plus the kitchen's boxes, the items and the corrected throw rules. Compares the step 11 runs, the `kitchen_runs.json` runs and `kt_star`. |
| `capture_mice.py` | Step 13: records the kitchen runs of steps 11 and 12 again, kept from frame 3680 (before the kitchen) so the mice can be followed from their start, 9 runs with the mice (hurt, crate batted back, stunned, pushed, carried and thrown, knocked out, the mouse under the crate) and 6 sound-only runs. Takes job names as arguments to record single jobs. |
| `build_mice.py` | Step 13: adds the tiles of the mice to the enemy strip of step 09, writes their picture tables and cuts the three sounds out of the sound-only runs. |
| `sim_mice.py` | Python port of the step 13 GML: `sim_kitchen2.py` plus the two mice, the stun star, pushing / carrying / throwing a stunned mouse, the bottle caps' places in the object list. Counts the NES sprites the port does not draw. Since the follow-up: standing on a stunned mouse, a pushed mouse stopping at a wall, 10 lives, and 10 more recordings (`mi_cleft`, `mi_push`, `mi_push2`, `mi_mtop`, `mi_mtop2`, `mi_mwake`, `mi_cwall`, and with memory written `mi_acorn3`, `mi_lives10`, `mi_lives11`). Also 20 recordings `mi_p_*` with memory written in the middle of a run (the list in `capture_mice.py`, `_M`), which the port repeats through `PORT_POKES`: 78 recordings in all. |
| `capture_caps.py` | Step 14: 16 runs from the ledge at the first bottle, 6 of them with a crate (kept from frame 3680 like the runs of step 13), 11 runs with the player's place written into memory on one frame (under a cap, at its edges, next to it in its flight), and the cap's sound alone, one channel at a time. |
| `build_caps.py` | Step 14: adds the 8 tiles of the cap to the enemy strip of step 13, writes the picture tables 80-83 and cuts the sound. |
| `sim_caps.py` | Python port of the step 14 GML: `sim_mice.py` plus the bottle caps (an enemy of kind 7) and the solid-thing test of the player. Runs the checks of step 13 and of step 14. |
| `level1_route3.json` | Buttons for the third section from frame 6841 (no buttons from 6600 to there) to its exit, found by a savestate search. Step 15 uses it up to the sink (frame 8076); the rest needs the rising water. |
| `capture_sec3.py` | Step 15: the third section up to the sink, a fall into a pit, lost lives up to GAME OVER and CONTINUE, random buttons on the first screen, the status screen, held buttons at the section change, three runs with Dale; 7 runs with the player's place written into memory (into the sink, under the tap, next to the exit). All are kept from frame 6540, the end of the kitchen. |
| `build_sec3.py` | Step 15: builds the section's 7 background screens in 7 brightness steps, the picture's right end without the backdrop colour (drawn over a player who is behind the picture), the block map and the map of the "behind" blocks. |
| `sim_sec3.py` | Python port of the step 15 GML: `sim_caps.py` plus the third section (block map, camera up to 1536, the exit right of the sink, "behind the picture" from the block map). Runs the checks of step 15 and those of `sim_caps.py`. |
| `measure_sec3.py` | Step 15: two measurements without the port, for things that need later steps to be compared: the values of the frame counter `$2D` on which a carried crate is bright, in the kitchen and in the third section (the same: 5, 6, 7, 0 of every 8); and the landing sound on the sink's floor at six places (always there, except next to the object of type `$1E`). |

`capture_kitchen.py` also records the step 12 runs (`kt_cr_*`), `kt_star` and `kt_fx_life_sq2`. `kt_star` is the only
recording that is not pure button input: on frame 6545 the player's position is written into the game's memory
(`$314` = 180, `$2FC` = 50) so that he lands on the shelf next to the star, which no found button sequence reaches yet.

`tools/dis/script.py` lists the byte code that drives the game's objects (`script.py 4 82D9`; the
scripts of the level 1 enemies are in bank 4). Opcodes above `$3F` are not decoded and are shown as `??`.

`tools/dis/dis6502.py` is a small 6502 disassembler for the ROM's PRG banks
(`dis6502.py 7 C5A2 C690`, or `dis6502.py find 85 49` to search for bytes).
`tools/dis/cols.py` prints the same listing in columns.

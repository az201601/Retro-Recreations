# Stage 01 → *your own* GameMaker Studio 1.4.1760 project

**Nothing here is a GameMaker project.** You create and retain your own `.project.gmx` in GameMaker Studio; transfer the PNG/WAV assets and copy the `.gml` source into resources you create. This repository does not generate or modify your project file. Start with a copy/backup of your project. The static NES map is verified; the gameplay scripts are an **untested prototype**, not a faithful/complete game.

Paths below are relative to this repository's root. On Windows, you can copy files into a temporary folder beside your GMS project before importing; **do not copy the whole `gms_export` tree over your project**. Resource names are case-sensitive in GML. You need the original USA ROM in this repo to rerun extraction, but not to import the already extracted files.

## 1. Confirm the transfer files

Already present:

- `assets/stages/stage_01_restaurant/background/bg_restaurant_*.png` — **five scenic backdrops**, not full-frame screenshots.
- `assets/stages/stage_01_restaurant/tilesets/ts_restaurant_*.png` — **five 256×256 metatile atlases**, 16×16 cells/16 columns.
- `assets/stages/stage_01_restaurant/sprites/import_frames/` — 18 named folders containing **87** individual, numbered, transparent PNG frames and `manifest.json` with cell sizes, origin points and ROM/OAM provenance. Their parent OAM strips and full pose manifest remain in `sprites/`.
- `assets/stages/stage_01_restaurant/audio/*.wav` and `audio/stage_01_audio.json` — exact-length capture excerpts, **not** verified loops/isolated SFX.
- `gms_export/scripts/stage_01/scr_stage01_*.gml` — **23** script sources. These are *not* object resources; you attach them below.

To regenerate these from the supplied ROM and recorded checkpoints, install Python 3 + Pillow and a C compiler, then run `./tools/emu/build_fceumm.sh`, `python3 tools/extract/capture_stage_01.py`, `python3 tools/extract/export_stage_01_rom.py --verify`, `python3 tools/extract/export_stage_01_sprites.py`, `python3 tools/extract/export_stage_01_import_frames.py`, `python3 tools/extract/export_stage_01_audio.py`, and `python3 tools/extract/export_stage_01_gml.py`. You **do not** need to rebuild to import the committed output. `--verify` needs large, ignored emulator captures; without those, omit the flag. Run `python3 -m unittest discover -s tools/extract/tests -v` to check the exported data/scripts without GameMaker.

## 2. Create the room *in your project*

1. Open **your** GMS 1.4.1760 project. Add a room named exactly **`rm_stage_01_restaurant`**, size **2048×2048**, speed **60**, black background, not persistent. Temporarily move it **first** in your room list for testing; leave your other rooms intact.
2. Enable room **Views**; make view 0 visible, view-in-room **x=0, y=512, width=256, height=240**. Set its screen port **x=0, y=0, width=512, height=480** (or another integer 256×240 multiple). No object-follow: the controller changes `view_xview[0]`/`view_yview[0]`. Turn off texture interpolation in your target/platform options.
3. Do **not** place backdrops, tiles, prizes or enemy instances manually in the room. After step 6, put exactly **one** `obj_stage01_controller` instance at `(0,0)`. Its Create event builds the layers/initial objects from the ROM data and creates Chip. Do not place a second `obj_player`.

## 3. Import ten Background resources

For **each** region `seating`, `kitchen`, `grill`, `monterey`, `water_rabbit`:

| Resource name you create | Import this PNG | Configuration |
| --- | --- | --- |
| `bg_restaurant_<region>` | `assets/stages/stage_01_restaurant/background/bg_restaurant_<region>.png` | Background; no tiling or scaling. Some areas intentionally transparent. |
| `ts_restaurant_<region>` | `assets/stages/stage_01_restaurant/tilesets/ts_restaurant_<region>.png` | Background with tileset enabled; tile width/height **16×16**, horizontal/vertical offset **0**, separation **0**. |

The Seating/Kitchen/Grill PNGs cover larger ROM-world areas; Monterey and the boss each occupy one 256×256 page. The GML `tile_add()` calls place all backgrounds and metatiles automatically at depths **10000** (scenery) and **1000** (furniture/platforms). **Never import `previews/rom_static_*.png` or `previews/stage_01_static_overview.png` as backdrops**: they are composites for inspection, and using them would draw platforms/furniture twice and bake over dynamic objects.

## 4. Import eighteen Sprite resources

For each folder below, create a sprite **with that exact folder name**. In its sprite editor, add `000.png`, `001.png`, … **as separate frames in numeric order**. Set its **Origin X/Y** to the table. Keep alpha transparency; disable interpolation. Do **not** import a contact-sheet PNG as a single animated frame. The original strips have additional observed/partial poses; these folders select only practical initial frames and do not establish NES animation timing.

| Sprite folder/resource in `sprites/import_frames/` | PNG frames | Frame size | Origin X,Y |
| --- | ---: | ---: | ---: |
| `spr_chip_seating` | 4 | 48×48 | 24,40 |
| `spr_chip_kitchen` | 8 | 48×48 | 24,40 |
| `spr_chip_grill` | 6 | 48×48 | 24,40 |
| `spr_chip_monterey` | 4 | 48×48 | 24,40 |
| `spr_chip_boss` | 7 | 48×48 | 24,40 |
| `spr_honey_bee` | 6 | 48×48 | 24,40 |
| `spr_fork_rat` | 6 | 64×56 | 32,48 |
| `spr_spoon_rat` | 7 | 48×56 | 24,48 |
| `spr_fake_box` | 4 | 32×40 | 16,32 |
| `spr_sink_valve` | 2 | 64×40 | 32,32 |
| `spr_sink_water_jet` | 1 | 24×176 | 12,0 |
| `spr_boss_box` | 4 | 32×40 | 16,32 |
| `spr_monterey_jack` | 6 | 64×64 | 32,60 |
| `spr_water_rabbit` | 18 | 80×104 | 40,96 |
| `spr_prize_crate` | 1 | 16×16 | 0,0 |
| `spr_prize_crate_rr` | 1 | 16×16 | 0,0 |
| `spr_prize_crate_acorn` | 1 | 16×16 | 0,0 |
| `spr_prize_rr` | 1 | 16×16 | 0,0 |

The `spr_prize_*` cells originate in the NES **background plane**, not OAM: their alpha is an approximation for movable GMS objects. The thrown-box code accounts for the **different origins** of the static crate and OAM falling boss box. No verified cork, loose acorn or star sprite has been extracted; step 6 notes explicit temporary visual substitutions. Do not call those substitutions original art.

## 5. Add audio and GML scripts

1. Add a Sound resource **`snd_restaurant_excerpt`** from `assets/stages/stage_01_restaurant/audio/bgm_restaurant_stationary_excerpt.wav` (23.31 seconds). It is the **one** sound name referenced by the prototype GML: played once, not looped. You may also import `boss_water_rabbit_gameplay_mix.wav` and `stage_clear_gameplay_mix.wav` separately *as analysis references*, but they contain SFX and should **not** be used as clean looping BGM or individual SFX. None has a verified loop point.
2. In your project's Scripts tree, create a script for **every `scr_stage01_*.gml` file** in `gms_export/scripts/stage_01/` and name it exactly after its filename **without `.gml`**. Paste that file's entire contents into the script. Create the five data/placement scripts (`hex_byte`, `place_static`, `collision_at`, `spawn_prizes`, `spawn_actors`) and the gameplay scripts before running. The Python ROM exporter can regenerate just the five data/placement scripts; it does not overwrite your GMS project.
3. **Do not** import older `scr_player_step`/`scr_crate_step` scripts from earlier experiments: they are removed because they used `obj_solid`, not the current ROM collision grid.

## 6. Create objects and attach events

Make the **19 objects below in your project**, in the order shown so parents exist before children. Leave the built-in **Solid unchecked** on all of them. Set **Visible** on except `obj_stage01_exit_right`. GMS 1.4 event naming: *Step* means normal Step (not Begin/End); *Draw GUI* is not normal Draw; *Other → Room End* is Room End, not Game End. Paste the event content verbatim from the table. If no event is listed, create none; child objects inherit their parent's Create/Step automatically.

| Object to create | Parent, sprite (and depth if important) | Events to add |
| --- | --- | --- |
| `obj_stage01_controller` | None; no sprite; depth 0; **nonpersistent, visible** | Create: `scr_stage01_controller_create();` · Step: `scr_stage01_controller_step();` · Draw GUI: `scr_stage01_controller_draw_gui();` · **Other → Room End**: `ds_grid_destroy(global.stage01_collision_grid);` |
| `obj_player` | None; `spr_chip_seating`; depth **-100** | Create: `scr_stage01_player_create();` · Step: `scr_stage01_player_step();` |
| `obj_crate` | None; `spr_prize_crate`; depth **-50** | Create: `scr_stage01_crate_create();` · Step: `scr_stage01_crate_step();` |
| `obj_boss_box` | **Parent `obj_crate`**; `spr_boss_box`; depth **-40** | **No own Create/Step**: inherit crate events. The boss script sets `is_boss`/`falling` after creation. |
| `obj_rre` | None; `spr_prize_rr`; depth -40 | Step: `scr_stage01_pickup_step(0);` |
| `obj_acorn` | None; **no extracted sprite** (temporary `spr_prize_rr` is distinguishable only by behavior); depth -40 | Step: `scr_stage01_pickup_step(1);` (heals one HP in prototype). Replace the stand-in graphic when authentic art is extracted. |
| `obj_stage01_enemy` | None; no sprite; depth -10 | Create: `scr_stage01_enemy_create();` · Step: `scr_stage01_enemy_step();` · **Do not place this abstract parent**. |
| `obj_enemy_honeybee` | Parent `obj_stage01_enemy`; `spr_honey_bee`; depth -10 | No own events; inherits parent. |
| `obj_enemy_fork_rat` | Parent `obj_stage01_enemy`; `spr_fork_rat`; depth -10 | No own events; inherits parent. |
| `obj_enemy_spoon_rat` | Parent `obj_stage01_enemy`; `spr_spoon_rat`; depth -10 | No own events; inherits parent. |
| `obj_enemy_fake_box` | Parent `obj_stage01_enemy`; `spr_fake_box`; depth -10 | No own events; inherits parent. |
| `obj_enemy_bottle_cork` | Parent `obj_stage01_enemy`; **no verified sprite**; depth -10 | No own Create/Step; temporarily draw an obvious stand-in sprite **you create** before playtesting, so this enemy is not invisible. |
| `obj_stage01_exit_right` | None; no sprite; **Visible unchecked** | No events. The player Step script handles crossing into the next segment; this resource is needed by `scr_stage01_spawn_actors`. |
| `obj_star_prize` | None; **no verified sprite** (temporary `spr_prize_rr`); depth -10 | Step: `scr_stage01_pickup_step(0);` (RR stand-in; original star effect still needs implementation). |
| `obj_zipper_in_box` | None; temporary `spr_prize_crate`; depth -10 | No events. Original behavior/art still needed. |
| `obj_sink_valve` | None; `spr_sink_valve`; depth -10 | Create: `image_speed = 0.05;` · Step: `scr_stage01_sink_step();` |
| `obj_sink_water_jet` | None; `spr_sink_water_jet`; depth -15 | Step: `scr_stage01_jet_step();` |
| `obj_monterey_refill` | None; `spr_monterey_jack`; depth -10 | Create: `image_speed = 0.10;` |
| `obj_boss_water_rabbit` | None; `spr_water_rabbit`; depth -10 | Create: `scr_stage01_boss_create();` · Step: `scr_stage01_boss_step();` |

**Important:** When `instance_create()` runs for crates, their Create event sets `hidden_drop=0`; `scr_stage01_spawn_prizes()` then sets `hidden_drop` to 0/1/2 based on the ROM. `scr_stage01_crate_step()` switches the crate sprite accordingly. The three `obj_stage01_enemy` children and `obj_boss_box` *must* have the specified parent or the inherited Create/Step and parent-type collision queries will fail. The grid is destroyed only at Room End; do not destroy it in Step or while another room still uses it.

## 7. Test in GameMaker (not done here)

1. Save your project; put the sole controller instance in the room and run. Verify the first screen has **wallpaper + individually placed furniture**, Chip near world `(58,704)`, and a lower HUD. A blank screen usually means a misspelled `bg_restaurant_*` / `ts_restaurant_*` resource or an absent controller. Double-drawn furniture usually means you imported a *composite preview* instead of scenic PNGs.
2. **Left/Right** move; **Z** or **Space** jump; **X** pick up/throw a crate and operate the Grill faucet (world x≈1584); **R** restarts at game-over/clear. The view should follow through Seating → Kitchen → Grill. Wait for the sink gauge to fill, leave right for Monterey Jack, then enter Water Rabbit; six box contacts end the prototype boss sequence. Monterey refills and advances on a timer (X can skip after a delay).
3. If Studio reports a missing identifier, check the exact 10 background names, 18 sprite names, 19 object names, 23 script names and `snd_restaurant_excerpt` before changing code. If GML compiles but play differs from the NES, treat the captured ROM snapshots and `docs/STAGE_01_RESTAURANT.md` as references; movement, AI, hazards, dialogue, HUD and audio still require **GMS-side testing and iteration**. No clean boss music loop or isolated SFX is claimed.

You own your project file: keep working on it wherever you normally store GameMaker projects. Send me the specific **compile error, screenshot, or behavior** you observe, and I can update the corresponding assets/GML here without packaging or modifying your project.

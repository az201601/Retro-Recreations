# Stage 01 — The Restaurant (Chip 'n Dale Rescue Rangers 2, USA NES)

## Status (GMS 1.4.1760)

**This repository contains extracted artwork/audio/data and editable GML only—not a GameMaker project.** You will create `rm_stage_01_restaurant` and all resource/event attachments **in your own GMS 1.4.1760 project**. [Follow the manual step-by-step transfer guide](STAGE_01_TRANSFER_GMS14.md). The ROM-derived static artwork and placement data are verified; the supplied player/crate/enemy/sink/boss GML is an **untested prototype** and has not been compiled or played in GameMaker.

The verified route is **Seating → Kitchen → Grill → Monterey Jack's refill → Water Rabbit**. A six-hit boss defeat and stage-clear transition were captured **with** a player-health safeguard (`0067:01`); cheat-free victory remains unverified. The lives safeguard (`00A7:03`) alone was used for the route. Neither cheat directly sets boss HP or skips a room. The HP safeguard does **not** make pits safe; no-input boss tests still repeatedly died in a floor hole. Water Rabbit is the Stage 1 boss, *not* Fatcat Robot.

**Source ROM:** `Chip 'n Dale - Rescue Rangers 2 (USA).nes` · SHA-256 `34ca559b733ed910b0a493a0cb1f5d64e5cd9e7e4796032d986c08079573e047` · iNES MMC1, 8×16 KiB PRG + 16×8 KiB CHR. Export scripts reject other ROMs. No third-party disassembly is needed to regenerate assets.

## Reproduce and verify

Requires Python 3, Pillow, GCC, make, git. The pinned libretro-fceumm core is fetched once from GitHub, patched, and built locally; large raw captures are **gitignored** under `tools/out/`.

```bash
./tools/emu/build_fceumm.sh
python3 tools/extract/capture_stage_01.py
python3 tools/extract/export_stage_01_rom.py --verify
python3 tools/extract/export_stage_01_sprites.py
python3 tools/extract/export_stage_01_import_frames.py
python3 tools/extract/export_stage_01_audio.py
python3 tools/extract/export_stage_01_gml.py
python3 -m unittest discover -s tools/extract/tests -v
```

Capture starts from the included emulator checkpoints and absolute-frame inputs. The frame-11800→20350 route save state is checked **byte-for-byte** against the preserved endpoint. The separate frame-11200 opening is useful for the first screen/music; it is *not* asserted to reproduce the different frame-11800 checkpoint. An idle, stationary Seating capture supplies the cleanest music reference. The boss capture uses both safeguards, and records RAM/OAM, periodic mapped-PPU snapshots, screenshots, WAV and an **AFI1** audio-frame sample index.

### ROM static room geometry

The original ROM has an 8×8 page layout at file offset 56954. A nonzero entry selects a 16×15 grid of **16×16** metatiles through banked PRG pointers; each metatile has four 8×8 CHR tiles and one 2-bit palette. The last 16 pixels of each 256-pixel-tall page are nametable attribute space, **not known scenery**. These and genuinely unmapped pages are transparent in the export. Room graphics use the core's verified RGB palette, not grayscale previews or jsnes's swapped red/blue.

| Region | World origin | Scenic PNG size | CHR 4-KiB bank | ROM placed tiles | Separate prizes | Actor/event spawns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Seating | (0, 512) | 2048×256 | 15 | 911 | 53 | 12 |
| Kitchen | (0, 1536) | 2048×512 | 16 | 994 | 55 | 15 |
| Grill | (0, 1280) | 1792×256 | 16 | 883 | 33 | 8 |
| Monterey refill | (0, 1024) | 256×256 | 21 | 101 | 0 | 1 |
| Water Rabbit | (1024, 256) | 256×256 | 15 | 82 | 0 | 1 |

- **Bottom scenic backdrop**: `assets/stages/stage_01_restaurant/background/bg_restaurant_<region>.png` contains wallpaper/wall paint and an **inferred hidden backdrop** under opaque placed props. Hidden wallpaper is not asserted to be original ROM data.
- **Placed tiles**: `assets/stages/stage_01_restaurant/tilesets/ts_restaurant_<region>.png` is a 256×256, 16-column atlas of 16×16 palette-correct metatiles. Windows, countertop edges, chairs, cups, dishes, appliances, shelves and non-collidable décor are **placed tiles**, not part of the bottom scenic layer. GMS source rectangle for ID `n`: `(n mod 16)*16, floor(n/16)*16, 16, 16`.
- **Exact placements + objects**: `assets/stages/stage_01_restaurant/maps/stage_01_restaurant.json`. Coordinates are ROM world pixels. Each placed tile is `[world_x, world_y, metatile_id, collision_class]`; separate prize entries specify ordinary crates, crates with hidden RR/acorn, and RR pickups. Actors include the two rats, bee, false boxes, faucet/exit, Monterey and boss. The map captures **static/initial** state; separate `gms_export/scripts/stage_01/scr_stage01_*.gml` files offer provisional logic for moving crates, sink filling, contact damage, Monterey refill and a six-hit boss. They are not wired into a project here and do not claim the ROM's exact timing, AI, cutscenes or spawn/despawn state machines.
- **Dynamic prize graphics**: `sprites/spr_prizes_<seating|kitchen|grill>_strip.png` has four 16×16 cells (ordinary crate, RR crate, acorn crate, RR emblem); NES BG-drawn prize tiles are exported as *approximate-alpha* cutouts for moving GameMaker objects, not baked into the backdrop. The opaque ROM-rendered placed/scenic composite is exact; the movable cutout alpha is an approximation.
- **References only**: `previews/rom_static_<region>.png` and `previews/stage_01_static_overview.png` show the exact **composite** and must **not** be imported as the bottom scenic backdrop. `tools/extract/build_stage_01_map.py` produces an incomplete PPU-snapshot diagnostic map, not a final GMS asset.

The ROM's generic object collision checks use `metatile >= $A0` for landing on a platform and `>= $D0` for side/up solidity, with `$F9` excepted. The JSON and generated GML label these `one_way`, `solid`, `none`; the prototype has a 12×18 foot-based player hitbox, simple object hits and a sink gate, but their fidelity still needs GameMaker/ROM comparison. The generated scenic + placed layers are asserted byte-for-byte equal to the **ROM's original static BG**. In live, stable fceumm snapshots: the Monterey and Water Rabbit pages match **all 832 8×8 tiles / 53,248 pixels** of the upper 256×208 BG; Seating has 8 differences from spawned prizes, Kitchen 18, Grill 24 (from objects/animations). Transition/fade states must not be mistaken for permanent tiles.

### Actual OAM animations

`assets/stages/stage_01_restaurant/sprites/spr_<name>_strip_00.png` and `stage_01_sprites.json` hold transparent NES-palette sprite frames reconstructed from real OAM compositions (8×8 sprites in pattern table 1, flip flags/priority honored), **not** individual monochrome CHR squares. Strips have fixed cell sizes/origins in the manifest; the most frequently seen poses are first.

| Captured actor | Distinct frames | Captured actor | Distinct frames |
| --- | ---: | --- | ---: |
| Chip (Seating / Kitchen / Grill) | 7 / 17 / 15 | Chip (refill / boss) | 7 / 13 |
| Honey bee / fork rat / spoon rat | 16 / 12 / 11 | False crate / sink valve / water jet | 14 / 2 / 1 |
| Monterey Jack | 9 | Water Rabbit / falling boss box | 86 / 9 |

See `previews/stage_01_sprite_overview.png`. For easier manual GameMaker import, `sprites/import_frames/` splits **87 curated individual PNGs** into 18 named sprite folders; `manifest.json` records cell sizes/origins and source pose IDs. Some rare/hurt frames flicker or are partly offscreen; the original strips are **sampled reference poses**, not a finished animation state machine or full list of unseen sprites. The boss capture reaches HP **6→5→4→3→2→1→0** (RAM `$3D7`), with player HP `$3D4` held at 3 in the successful safeguarded run. Gameplay is around frame 20400; victory/clear transition begins after frame 29729. The reliable boss run holds LEFT to avoid lethal floor holes. Frame-by-frame OAM traces show a falling box sprite **touching or overlapping the boss bounding area** on each of the six HP-decrement frames (22042, 22715, 26288, 27502, 28118, 29729); the first appears to touch at its left edge. This is consistent with unthrown falling boxes hitting the boss, although the exact ROM collision path has not been proven. **Do not infer that standing LEFT is the intended combat mechanic.** Intended fight: avoid water pulling Chip toward holes, pick up the one falling box at a time, and throw boxes for six hits ([walkthrough](https://gamefaqs.gamespot.com/nes/587566-disneys-chip-n-dale-rescue-rangers-2/faqs/30889)).

### Cutscene brick wall

The herringbone brick backdrop seen around the stage-clear "TV" frame
(`background/full_frame_24400.png`) is **not** in the BG pattern table used by the
playable rooms. Its 8×8 CHR tile is at 8 KiB bank 15, tile `425` (`0x1A9`) — i.e.
4 KiB bank 31, the half normally mapped as the sprite pattern table. That is why
a PPU viewer parked on a gameplay frame shows no brick tiles: MMC1 has swapped a
different 4 KiB bank into BG, or the cutscene points BG at the other pattern table.

A seamless, palette-correct **32×32 px** sample of that wall (the verified repeat
period) is provided as
`assets/stages/stage_01_restaurant/tilesets/brick_wall_32x32.png` for recreation
work. It is cut from the exact ROM-rendered frame, not redrawn.

### Audio

`assets/stages/stage_01_restaurant/audio/` includes a 23.31-second **stationary Seating music excerpt**, an 18.32-second **mixed Water Rabbit fight reference**, and a 6.16-second **mixed stage-clear reference**. `stage_01_audio.json` records exact AFI1 sample ranges and checksums. **None** has verified loop points. Boss/clear samples contain game SFX and must not be passed off as isolated music or clean individual SFX. If you attach the supplied controller GML to your project, it plays the Seating excerpt **once**, without looping; the boss/clear WAVs are analysis references, not used by that code. Isolated boss BGM and per-action SFX still need dedicated extraction.

## Manual GameMaker Studio 1.4.1760 transfer (not runtime-tested)

**[Use the step-by-step transfer guide](STAGE_01_TRANSFER_GMS14.md)** to create the room, Backgrounds, Sprites, one Sound, 23 Scripts and 19 Objects **in your own project**. This repository contains no `.project.gmx` and does not write or overwrite your project file. The manual guide gives every resource name, sprite size/origin, event attachment, view setting and a test sequence.

The prototype GML adds scenic BGs at depth 10000 and ROM placed metatiles at depth 1000, builds a 128×128 collision grid, spawns initial prizes/actors and handles provisional movement, sink, refill, camera and six-hit boss logic. It uses simplified AI, approximate physics and a stand-in HUD; no GameMaker import, compile or playtest has been performed here. The original pose strips (including 86 Water Rabbit observations) remain separate from the 87 curated transfer frames. Compare screenshots/behavior in your project against the NES captures before judging fidelity.

## Legacy references and remaining work

Older tracked `background/full_frame_*.png` / `bg_frame_*.png` are frame samples, *not* scenic backgrounds. In particular, frame 11200's supposed "BG-only" image came from an emulator layer-toggle bug and **must not** be used as a BG truth source. Earlier grayscale `chr_bank_*` previews, `raw_frame_*` sprite crops and the long playthrough WAV are scratch references, not final imports. The patched fceumm core fixes independent BG/sprite visibility and exposes private mapped-PPU snapshots; see `tools/emu/README.md`.

Remaining: **transfer assets and GML into your own GMS 1.4.1760 project** using the manual guide, then compile and playtest there; fix any errors reported by Studio; verify a no-cheat ROM boss victory; measure exact combat/box/current physics, AI and contact hitboxes; replace provisional behavior and temporary visuals with faithfully timed NES interactions and HUD; isolate SFX and true loop points; verify scroll seams and animated sink at every frame; implement original dialogue/cutscene choreography. The supplied code is **untested source**, not a verified complete game.

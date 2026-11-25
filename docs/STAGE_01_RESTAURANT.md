# Stage 01 - Restaurant (Chip 'n Dale Rescue Rangers 2, NES)

## Scope / status
- **Target room**: `rm_stage_01_restaurant` (move to top of room list while building).
- **ROM**: `Chip 'n Dale - Rescue Rangers 2 (USA).nes` (iNES MMC1, PRG 8x16KB, CHR 16x8KB).
- **Emulator**: libretro-fceumm headless harness (`tools/emu/fceumm_headless.c`, built via `tools/emu/build_fceumm.sh`). Deterministic input scripts, PNG/PPM screenshots, WAV audio dump, RAM dump, Game Genie cheats, `FCEUMM_HIDE_SPRITES` / `FCEUMM_HIDE_BG` layer capture.
- **Coverage**: scripted playthrough reached multiple Stage 1 Restaurant sections (kitchen counter, green-wall/window area, brick/platform sections) with infinite-health/lives cheats (`OUXLLEVS`, `NXKZKTVI`, `OXUNGIVK`). **Boss fight not reached** by blind scripted/RAM-feedback traversal; boss assets need a targeted boss-room capture pass (see Gaps).

## Asset classification (user-defined)
- **Background**: bottom scenic backdrop layer only.
- **Tileset**: placed level tiles (collidable or not). Examples: coffee mugs, chairs, sandwich, counter top, windows, salt/pepper. Counter top/collidable tiles still belong to tileset.
- **Sprites/objects**: anything requiring code or interaction. Examples: crates (interactable, items can be under them), enemies, player, pickups, projectiles, HUD elements handled by code.

NES note: the NES BG plane contains both scenic backdrop and placed tiles. BG-only captures are exported as background references; CHR tiles/banks used for placed props/structure should be treated as tileset, and interactive/moving entities as sprites.

## Extracted artifacts

### Emulator / capture
- `tools/emu/fceumm_headless.c` - headless libretro frontend (shots, `--shot-every`, `--wav`, `--cheat`, RAM dump, inputs).
- `tools/emu/build_fceumm.sh` - builds core + frontend.
- `tools/emu/stage1_driver.py` - replay-based RAM/screenshot feedback driver (backtracking strategies) for scripted traversal attempts.
- `tools/emu/inputs/stage_01_restaurant_to_gameplay.txt` - reaches Stage 1 gameplay.
- `tools/emu/inputs/stage_01_restaurant_driver_best.txt` - best driver-generated input so far.
- `tools/emu/README.md` - harness usage.
- Built binaries (gitignored): `tools/out/emu/fceumm_libretro.so`, `tools/out/emu/fceumm_headless`.

### Raw captures (gitignored under tools/out)
- `tools/out/emu/stage1_cheat/normal/` - normal playthrough frames (every 300 frames, 70k total).
- `tools/out/emu/stage1_cheat/bg/` - BG-only (`FCEUMM_HIDE_SPRITES=1`).
- `tools/out/emu/stage1_cheat/spr/` - sprite-only (`FCEUMM_HIDE_BG=1`).
- `tools/out/emu/stage1_cheat/*_contact.png` - contact sheets.

### Background references (workspace)
- `assets/stages/stage_01_restaurant/background/` - deduped BG-only captures.
  - `full_frame_*.png` - full BG plane including HUD.
  - `bg_frame_*.png` - HUD-cropped (top 24px removed) background reference.
  - `stage_01_restaurant_bg_start.png` - initial screen BG reference.
  These are reference captures; final GMS background should be composed from scenic backdrop only, with tileset props placed via tile layers/objects per classification.

### Tilesets (workspace, CHR-derived candidates)
- `assets/stages/stage_01_restaurant/tilesets/chr_bank_08_restaurant.png`
- `assets/stages/stage_01_restaurant/tilesets/chr_bank_09_restaurant.png`
- `assets/stages/stage_01_restaurant/tilesets/chr_bank_10_restaurant.png`
- `assets/stages/stage_01_restaurant/tilesets/chr_bank_11_shared.png`
- `assets/stages/stage_01_restaurant/tilesets/chr_bank_12_shared.png`
- `assets/stages/stage_01_restaurant/tilesets/chr_bank_13_shared.png`
- Per-tile 8x8 slices (2x): `assets/stages/stage_01_restaurant/tilesets/bank_{08..13}_*_tiles/tile_XXX.png`
- Manifest: `assets/stages/stage_01_restaurant/chr_tile_manifest.json`
Source: `tools/extract/extract_chr.py` from ROM CHR banks (128x128 tilesheets, 2x scale, index 0 transparent).

### Sprites (workspace)
- `assets/stages/stage_01_restaurant/sprites/raw_frame_*_sprites.png` - deduped sprite-layer crops from sprite-only capture pass.
- `assets/stages/stage_01_restaurant/sprites/chr_bank_14_boss.png` - CHR bank candidate (boss/special sprites; verify against boss capture).
- `assets/stages/stage_01_restaurant/sprites/chr_bank_15_sprites_ui.png` - CHR bank candidate (player/enemies/UI sprites).
- Per-tile 8x8 slices (2x): `assets/stages/stage_01_restaurant/sprites/bank_{14,15}_*_tiles/tile_XXX.png`
- Candidate entity list: Chip/Dale player, crate (object/sprite), R.R.E. pickup, honeybee, silverware/slimeball, boss (not captured in gameplay yet), HUD icons/hearts/lives.

### Audio (workspace)
- `assets/stages/stage_01_restaurant/audio/stage_01_full_playthrough.wav` - long playthrough capture (fceumm audio, includes SFX/deaths/respawns; 70k-frame run with cheats).
- Raw earlier sample: `tools/out/emu/stage1_play_bg/audio.wav` (gitignored).

## Gaps / next extraction passes
1. **Boss fight capture**: scripted traversal and replay-feedback driver did not reach boss room. Need save-state-assisted/manual-assisted input script, or deeper RAM map (screen ID/scroll/player state) to navigate pits/doors; capture normal/bg/spr/audio.
2. **Full stage BG composition**: stitch BG-only captures into a clean scenic background map; separate tileset-placed props from true backdrop.
3. **Tileset atlas**: build GMS-ready tileset from used CHR tiles, with collision metadata for mugs/chairs/sandwich/countertop/windows (collidable) and salt/pepper (no collision).
4. **Sprite slicing**: slice per-entity, per-animation-frame sprites (idle/run/jump/crouch/throw/hurt for player; crate states; enemy anims; pickups; boss). Current sprite crops are raw sprite-layer references.
5. **Audio split**: split stage music, boss music, and SFX into individual importable files; verify loop points.
6. **RAM/physics map**: identify player X/Y/velocity/state, scroll, enemy state, crate state addresses for frame-accurate GML.

## GMS 1.4.1760 import notes
- Background: import composed scenic backdrop as `bg_stage_01_restaurant`; keep parallax/scroll behavior in room/code as needed.
- Tilesets: create `ts_stage_01_restaurant_*` from tileset sheets; set tile size after confirming (likely 8x8 source, scaled as needed). Apply collision via tile layers/object collision map per user classification.
- Sprites/objects: `spr_chip`, `spr_dale`, `spr_crate`, `spr_rre`, `spr_honeybee`, `spr_slimeball`, boss sprites; create corresponding objects with GML.
- Audio: import WAVs as `bgm_stage_01_restaurant`, boss/SFX resources after splitting.
- Room: `rm_stage_01_restaurant`, temporarily top of room list during Stage 1 development.

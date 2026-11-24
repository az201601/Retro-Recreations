# Level extraction pipeline (NES → GMS 1.4)

## What is proven working

- `tools/nes_state.py` parses FCEUmm libretro savestates (`RAM`, `NTAR`, `PRAM`,
  `SPRA`, `PPUR`, `XOFF`, `TADD`, MMC1 `DREG`) and re-renders the PPU exactly.
  Validation on the gameplay screen at emulator frame 12,000 produced **0
  differing pixels** against the emulator's own frame, and every captured state
  so far re-renders without a single palette-index conflict.
- `tools/extract_room.py` turns one state + its matching frame into a room
  handoff folder (background, tileset, tilemap, sprites, palette, metadata).
- `tools/verify_room.py` rebuilds the screen from `tileset.png` + `tilemap.csv`
  and compares it to `page.png`. Both extracted windows currently verify with
  **0 differing pixels**.
- `tools/autoplay.py` drives `retroshot -i` so capture can be scripted, RAM can
  be inspected and savestate/load can be used for retries.

## What the ROM actually does

| Item | Value |
|---|---|
| Mapper | 1 (MMC1), 128 KiB PRG, 128 KiB CHR ROM |
| CHR banking | 4 KiB mode; banks selected by MMC1 registers in state `DREG` |
| Background pattern table | `$0000` or `$1000` from PPUCTRL bit 4 |
| Sprite pattern table | `$0000` or `$1000` from PPUCTRL bit 3 |
| Nametables | vertical mirroring; 2 KiB physical, both pages used |
| Scrolling | smooth via `$2005`; fine X takes values 0–7, coarse X 0–31 |

**Stages are wide scrolling maps, not one-screen rooms.** The camera moves in
8-pixel coarse steps while the game rewrites tiles a column at a time, and the
nametable page flips at 256-pixel boundaries. Two adjacent 256-pixel pages of
stage 1 (Downtown) are already extracted under
`extracted/levels/stage1_downtown/`.

## Handoff folder contents

```
extracted/levels/stage1_downtown/cam_0000/
  room.png        full composite (background + sprites) as the player saw it
  background.png  background layer only, exactly at that camera position
  page.png        the nametable page with zero scroll (this is what tilemap
                  describes, so it is camera-independent)
  sprites.png     sprite layer with transparency
  tileset.png     unique background tiles, 16 cells per row, 8x8 each
  tiles.csv       cell -> NES tile id, palette index, usage count
  tilemap.csv     30 rows x 32 columns of tileset cells (-1 = blank/backdrop)
  palette.csv     NES colour index -> RGB, with the PRAM slots that use it
  room.json       CHR banks, mirroring, PPUCTRL/PPUMASK, camera_x_px,
                  screen_aligned, object list, checksums, notes
```

Colours are learned from the emulator frame that was captured on the same
frame as the state, so they are the exact RGB values the core output — no
approximation or "NES palette" guesswork. `render_check` in `room.json` is
`pixel-exact` when that held for every colour index on screen.

## Capturing a new window

The emulator is a headless libretro frontend (`tools/emu/retroshot`, built per
`tools/README.md`). Two ways to capture:

1. **Timeline** (deterministic, good for scripted routes):

   ```
   1000 tap START 6
   1100 tap START 6
   2000 tap START 6
   12000 shot w12000
   12000 state w12000
   12001 quit
   ```

   `state` writes a FCEUmm savestate, `shot` writes a PPM; both taken at the
   same emulator frame are required for exact palette learning.

2. **Interactive** (`retroshot ... -i`, driven by `tools/autoplay.py`):

   ```
   run N | press BTN | release BTN | tap BTN N
   shot NAME | state NAME | ram NAME | load NAME | poke ADDR VAL
   guard ADDR VAL | unguard | quit
   ```

   `guard` rewrites a RAM byte after every frame — the Pro Action Replay
   addresses for this game are health `$03D4` and lives `$00A7`, which makes
   capture runs survivable. `load` restores a savestate so a route can be
   retried without restarting the game.

## Extracting and verifying

```bash
python3 tools/extract_room.py \
  --state tools/out/capture/w12000.fcs \
  --frame tools/out/capture/w12000.ppm \
  --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" \
  --out extracted/levels/stage1_downtown/cam_0128

python3 tools/verify_room.py extracted/levels/stage1_downtown/cam_0128
```

`verify_room.py` must print `0 differing pixel(s)`; if it does not, the state
and frame were not from the same frame (or the screen was mid-effect).

## GMS 1.4 notes

- Import `tileset.png` as a sprite with **8×8** cells and `tilemap.csv` as the
  room's tile layer; blank cells use the backdrop colour from `palette.csv`
  (NES index `0x0F` in the captured rooms).
- For a first playable pass, `background.png` can be used directly as a
  full-size background asset; rebuilding from `tilemap.csv` is what makes
  collision and camera culling possible later.
- `room.json` records `camera_x_px`; when stitching pages into one wide level,
  place a page at `camera_x_px` rounded down to the page start.
- Sprite tiles use the sprite CHR bank recorded as `chr_bank_sprites`; the
  sprite list in `room.json` has screen positions, tile ids and flips.

## Current limitation

Automated traversal dies on pits before the whole stage is covered. The health
guard prevents enemy damage but not falling. Capture needs either a better
route bot (search with savestate retries) or savestates supplied from manual
play; both plug directly into `extract_room.py` without changes.

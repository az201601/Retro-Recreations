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
- `tools/solve_route.py` searches for a route through the stage with savestate
  retries (best-first, beam-pruned), dropping a checkpoint every N pixels.
- `tools/stitch_level.py` turns those checkpoints into one wide strip plus a
  tileset and tilemap, and verifies each window against the emulator frame.
  The stage 1 strip under `extracted/levels/stage1_downtown/wide/` rebuilds from
  its own tileset with **0 differing pixels**.

## What the ROM actually does

| Item | Value |
|---|---|
| Mapper | 1 (MMC1), 128 KiB PRG, 128 KiB CHR ROM |
| CHR banking | 4 KiB mode; banks selected by MMC1 registers in state `DREG` |
| Background pattern table | `$0000` or `$1000` from PPUCTRL bit 4 |
| Sprite pattern table | `$0000` or `$1000` from PPUCTRL bit 3 |
| Nametables | vertical mirroring; 2 KiB physical, both pages used |
| Scrolling | smooth via `$2005`; fine X takes values 0–7, coarse X 0–31 |

### Reading the camera — the only trustworthy progress signal

`cam = (ppuctrl & 3) * 256 + coarse_x * 8 + fine_x`, and it wraps every 512 px,
so unwrap each reading against the previous one. No RAM byte or word tracks the
camera; searching for one gives false positives only.

Three traps cost real time here, and all three produce *plausible-looking bad
data* rather than errors:

1. **End-of-frame scroll registers belong to the next frame.** Measure a jump's
   result immediately and you read the camera position it is about to have.
   Settle ~30 frames before measuring, or measure the player instead.
2. **OAM is copied mid-frame.** A savestate holds the sprite table for the next
   frame while its picture shows the previous one. Expect a few hundred pixels
   of disagreement around moving sprites and treat those pixels as "unknown",
   not as background.
3. **A screenshot taken right after `load` shows the frame that was already on
   screen,** not the loaded state. Always `load`, run at least one frame, then
   save the state and shoot the frame together. `tools/stitch_level.py` does
   this itself so checkpoints cannot drift out of sync with their pictures.

`retroshot -i` now answers `ERR <reason>` when a command fails (`load` with a
path relative to the emulator's own working directory used to fail silently and
leave the previous state running, which made a whole search run look valid).
`tools/autoplay.py` raises on `ERR` and resolves paths to absolute.

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

## Traversal: what the solver can and cannot do

The solver expands a frontier of savestates with ~90-frame input macros, keeps
the best beam, and measures progress on the *player* (`cam + player screen x`,
plus screen y) because the camera alone cannot distinguish climbing from
standing still. Health `$03D4` is guarded; a run that loses a life or falls
back is rejected.

It currently reaches player world x **1339** on stage 1 (camera 1142). Two
obstacles needed extra thinking and will need more:

- **Pits.** A greedy route died at camera 726; the frontier/beam search plus a
  wider macro set (delayed jumps, double jumps, stand-and-commit) clears them.
- **Climbing.** The pillar at the end of the restaurant interior is climbed
  with `UP`, which no horizontal macro ever presses. Macro set now includes
  `climb_up`, `climb_far`, `up_right` and `climb_jump`.
- **The next wall** is at x≈1339, y≈95 (high up, mid-climb). More vertical
  macros and a proper collision map are the intended unlock: with the ROM's
  collision table, the solver can path-find instead of guessing.

## Collision

Collision must come from the ROM, not from hand-classifying tiles or probing
the player (both were rejected). Status: the level is streamed straight to VRAM
with no intermediate tile buffer in RAM, so the tile→solid table has to be
found in the ROM image. The plan is to locate the 256-entry table indexed by
tile id and validate candidates against observed standing positions collected
from the captured states — a first pass over 138 states gave only 13 usable
labels, so the labelling (identifying the player's feet against the correct
page) needs tightening before the search is meaningful.

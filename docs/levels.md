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

## Traversal: the measurement was the bug

The search expands frontier states best-first: every state is expanded exactly
once, in order of how far it got, and dead ends are retired. The earlier shape
(re-expand the leader until it dies, prune with a beam) burned whole runs on one
branch, and — worse — adding macros made runs *shorter*.

Four separate measurement faults explained the "walls" that the macros were
being blamed for:

1. **Unwrapping the camera against its parent caps apparent progress at 256 px.**
   The register only holds 0–511, so the code picked the ±512 candidate nearest
   the parent. Every state more than 256 px past its parent got silently folded
   back, which is why every run stalled "around camera 1000" no matter what was
   changed. Progress is now an odometer: the *change* in `camera + player x`
   between parent and child, mapped into a signed window.
2. **`cam + player_x` reached 767 without wrapping**, so the odometer invented
   jumps.
3. **Palette learned from the first window only.** A window only reveals the few
   palette entries it uses, and the fallback NES palette is *not* what the core
   outputs (it is ~16 off on several entries), so later windows rendered in the
   wrong colours — 50k-pixel errors. The palette is now fitted across every
   window at once.
4. **Checkpoints keyed to player progress.** A checkpoint names a *window*, so
   they are keyed to camera distance and the search records the absolute camera
   for each one in `route.json`; deriving the wrap afterwards is guesswork.

With those fixed, the same macro set reaches world x **5904** (odometer) instead
of 1339, and the one macro that was genuinely missing — `climb_over`, found by
randomised search from the beam where everything stalled — is in the set.

## Rooms, not one long strip

Stage 1 is a sequence of rooms and **each room restarts the camera at 0**. So
camera arithmetic alone cannot place a window in one long world strip; rooms
have to be segmented and concatenated. `stitch_level.py --max-cam` cuts a strip
at the end of the current room, which is how the delivered
`extracted/levels/stage1_downtown/wide/` (camera 0–1142) is produced. The next
step is automatic room detection: a window whose content matches nothing in the
accumulated canvas starts a new room instead of being unwrapped.

## Collision: what the ROM shows

No RAM mirror of the nametable exists — searching 138 captured states for
nametable columns, rows and metatile downsamples found nothing, and the visible
level map is written straight to VRAM. The streaming code is in the fixed bank:

| CPU address | What it is |
|---|---|
| `$83BE` | blit loop: `LDA ($00),Y` → `STA $2007`, `$03` = byte count, bit 7 of `$02` = direction |
| `$8390` | prepares that call: fetches flags/`$03`, turns `$02` into a PPUCTRL value |
| `$8384` | flushes a prepared column from the RAM buffer at `$053B` |
| `$83C4` | entry that sets the VRAM address from `$44/$45` and runs the blit |

While the restaurant room scrolls, `$00/$01` walks from `$8ABD` upward at about
20 bytes per 8-px column (PRG file offset `0x0ABD`, data not code), so the level
stream for this room lives there. The stream is not a plain tile list: none of
the nametable's columns, rows or 2×2 blocks appear verbatim in PRG, and the
data-resident blocks do not form a definition table.

So the collision table has to come from following that stream (or from the
collision routine that consumes it) rather than from pattern-matching the ROM.
That is the open thread; the addresses above are the entry points.

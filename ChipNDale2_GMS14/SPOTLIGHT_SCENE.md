# The Spotlight Scene (title attract sequence)

The scene that plays immediately after the copyright screen.

Everything in this document was **measured from the running ROM**, not guessed.
The tools that produced the numbers and the assets are in `tools/`.

---

## 1. What is actually on screen

It is not a scrolling mask or a lighting effect. It is a **1-bit stencil with a
sprite-based light disk sweeping behind it**, and then a palette fade.

Two completely different backgrounds are used one after the other:

| Phase | Steps | Background | Nametable | CHR bank |
|---|---|---|---|---|
| Spotlight | 0 – 885 | 1-bit stencil (45 tiles, colour indices 0/1 only) | `$2000` | 31 |
| Mural | 886 – 904 | colourful title mural (241 tiles) | `$2000` (rewritten) | 30 |

### The spotlight phase

* Palette is `$0F $0F $0F $20` for all four background palettes, so the stencil
  renders as **solid black shapes on a black backdrop**. The only visible
  difference between colour 0 and colour 1 is which one the sprites can show
  through.
* The stencil is a silhouette of the title mural itself — Chip, Dale, the logo
  and the brick frame appear as solid black shapes.
* The light disk is **32 hardware sprites** in 8×16 mode: 4 sprites wide × 8
  rows = **64 × 63 pixels**, all with sprite attribute bit 5 set, i.e. drawn
  *behind the background*.
* Because the disk is behind the background, the PPU only shows it where the
  background pixel is colour 0. Verified at step 480:

  | disc pixels landing on background colour | visible |
  |---|---|
  | 0 | 2198 / 2198 |
  | 1 | 0 / 738 |

  So the disk appears everywhere *except* where the black silhouette is — which
  is why the logo seems to emerge from the darkness as the disk sweeps over it.

### The mural phase

At step 886 the stencil nametable is replaced with the colourful title mural and
its four background palettes are faded up from black, one palette entry per
step, finishing at step 904. Every intermediate palette state the ROM writes is
recorded in `EXTRACTED/spotlight/fade_palettes.txt`.

---

## 2. The disk's exact path

The disk is 64 × 63. Coordinates are the top-left of the unclipped disk.

| Steps | Motion |
|---|---|
| 212 – 219 | `x = 160`, `y = 2 + 2*(f-212)` — only 1 of 8 sprite rows is on screen |
| 220 – 226 | `x = 160`, `y = 2 + 2*(f-220)` — 2 rows |
| 227 – 234 | `x = 160`, `y = 1 + 2*(f-227)` — 3 rows |
| 235 – 315 | `x = 160`, `y = 1 + 2*(f-235)` — full disk falling |
| 316 – 411 | diagonal up-left |
| 412 – 475 | `x = 30 + 2*(f-412)`, `y = 29` — straight right |
| 476 – 522 | diagonal down-left |
| 523 – 596 | `x = 90 - 2*(f-523)`, `y = 95` — straight left, exits the screen |
| 597 – 705 | `x = -56`, `y = 95` — fully off screen, still "alive" |
| 706 – 785 | `x = -56 + 2*(f-706)`, `y = 73` — re-enters from the left |
| 786 – 801 | `x = 98 - 4*(f-786)`, `y = 73` — fast reversal |
| 802 – 885 | `x = 38`, `y = 73` — parks over the logo and holds |

### The diagonals are integer patterns, not float speeds

They average −1.375 px/step, but the ROM adds a repeating integer sequence. It
must be copied exactly or the disk desyncs from the stencil:

```
diag 1 (up-left)    both axes: [-1, -2, -1, -1, -2, -1, -1, -2]   (-11 per 8)
diag 2 (down-left)  x axis   : [-1, -2, -1, -1, -2, -1, -1, -2]
                    y axis   : [+1, +2, +1, +1, +2, +1, +2, +1]   (+11 per 8)
```

These tables were checked against the ROM: **566 measured frames, 0
mismatches.**

---

## 3. Implementing it in GameMaker Studio 1.4

The NES composites "sprite behind background", which GMS has no layer for. Draw
in the opposite order:

```
1. draw_clear(black)                     // the backdrop
2. draw the light disk                   // spr_spotlight_disk
3. draw the stencil ON TOP               // spr_spotlight_mask
```

`spr_spotlight_mask` is the stencil with **every colour-0 pixel transparent and
every colour-1 pixel opaque black**. The disk then shows through exactly where
the NES showed it.

This recipe was verified against the ROM at step 480 and is
**100% pixel-identical — 0 differing pixels out of 61,440.**

### Files

| File | What it is |
|---|---|
| `GML/scr_title_spotlight.gml` | timings, palette, measured path tables |
| `GML/scr_spot_pattern.gml` | helper that sums a repeating integer pattern |
| `GML/obj_title_spotlight_Create.gml` | Create event |
| `GML/obj_title_spotlight_Step.gml` | Step event (the timeline) |
| `GML/obj_title_spotlight_Draw.gml` | Draw event (the layer order) |

### Sprite resources to create

Load from `EXTRACTED/spotlight/`. Origin **Top Left**, interpolation **off**,
"Separate Texture Page" on for the full-screen ones.

| Sprite | Size | Source PNG |
|---|---|---|
| `spr_spotlight_disk` | 64 × 63 | `spotlight_circle.png` |
| `spr_spotlight_mask` | 256 × 240 | `spotlight_mask.png` |
| `spr_spotlight_wall` | 256 × 240 | `backdrop_bricks.png` |

### Room setup

* 256 × 240, speed 60, no views.
* "Interpolate colours between pixels" **off**.

---

## 4. Extracted assets

All in `EXTRACTED/spotlight/`.

| File | Contents |
|---|---|
| `spotlight_circle.png` | the 64 × 63 light disk, transparent outside the disc, in its real NES colours (`$36`/`$16`/`$26`) |
| `spotlight_circle_grid.png` | same, 4× with 8×8 sprite-cell guides |
| `spotlight_circle_raw.txt` | the raw 2-bit colour indices of the disk |
| `spotlight_mask.png` | the 1-bit stencil, mortar transparent — the sprite you draw over the disk |
| `spotlight_stencil_preview.png` | the stencil as the player sees it (black silhouette on backdrop) |
| `backdrop_bricks.png` | the colourful title mural (the phase after step 886) |
| `backdrop_bricks_dark.png` | the same area fully blacked out |
| `backdrop_bricks_tilemap.txt` | 32 × 30 tile indices + attribute table of the mural |
| `backdrop_bricks_palette.txt` | the four background palettes of the mural |
| `fade_palettes.txt` | every palette state the ROM writes during the mural fade |
| `scene_frames/fNNNN.png` | 27 real rendered frames of the sequence |
| `scene_contact_sheet.png` | 4 × 4 grid of the sequence, for eyeballing timing |

---

## 5. Regenerating everything

The extractor boots the ROM in a headless NES (6502 + MMC1 + PPU register
model), runs it to an exact video frame, and reads back the real PPU state —
nametables, palette RAM, OAM and bank registers. No emulator GUI, no guesswork.

```bash
cd ChipNDale2_GMS14/tools
pip install py65                 # only dependency
python3 extract_spotlight_scene.py
```

Optional: dump the PPU state at any single frame.

```bash
python3 nes_emu.py "../../Chip 'n Dale - Rescue Rangers 2 (USA).nes" 480
```

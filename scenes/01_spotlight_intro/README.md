# Scene 01 — Pre-Title Spotlight Intro (`rm_spotlight_intro`)

This folder contains all extracted graphics (using **Mesen's exact default 2C02 palette** at crisp 1:1 pixel resolution), assembled 16×16 tilesets, assembled multi-tile sprite sheets, 44.1 kHz 16-bit PCM WAV audio cues, and **GameMaker Studio 1.4.1760** object code for the spotlight sequence right after the copyright screen and right before the Title Screen.

---

## How the NES PPU Renders This Scene (and How It Maps to GMS 1.4.1760)

On the NES, this scene uses a clever hardware priority masking trick:
1. **Backdrop (`$3F00 = $0F` Black)**: Pure black `#000000` covers the unlit screen.
2. **Spotlight (`OAM Sprites 32–63`, Priority bit `1` = BEHIND background)**: 32 separate `8×16` hardware sprites are stitched together with horizontal/vertical flips to form a `64×64` glowing spotlight circle (`#FECCC5` center, `#FE8170` inner edge, `#B53120` outer anti-aliased edge) that sweeps behind the nametable!
3. **Brick Mortar & Silhouette (`Nametable $2400` → `$2000`)**: The brick interiors are **transparent** (color index 0), while the mortar lines and Chip & Dale's silhouette are **opaque black (`#000000`)** sitting **in front** of the spotlight sprite! Wherever the spotlight moves, the bricks light up while the mortar and silhouette mask it cleanly.

In **GMS 1.4.1760**, this maps cleanly to your exact layer setup without needing any shaders or surfaces:
- **Lowest Background Layer**: `bg_spotlight_backdrop.png` (`256×240`)
- **Object Layer (`Depth = 100`)**: `obj_spotlight_beam` using the assembled `64×64` 4-frame sprite strip `spr_spotlight_beam_strip4.png`
- **Room Tile Layers (`Depth = 0` and `Depth = -10`)**: `ts_spotlight_mask_16x16.png` (`16×16` tiles assembled from 4× `8×8` NES PPU tiles)

---

## Folder Contents & GMS 1.4.1760 Import Settings

### 1. `backgrounds/`
| File | Size | GMS 1.4 Resource Name | Settings |
|---|---|---|---|
| `bg_spotlight_backdrop.png` | `256×240` | `bg_spotlight_backdrop` | **Use as tile set**: Unchecked. Assign to Background 0 in `rm_spotlight_intro`. |

### 2. `tilesets/`
| File | Size | GMS 1.4 Resource Name | Settings |
|---|---|---|---|
| `ts_spotlight_mask_16x16.png` | `128×48` (8×3 grid of `16×16` tiles) | `ts_spotlight_mask` | **Use as tile set**: Checked (`Tile Width = 16`, `Tile Height = 16`, `Offsets = 0`, `Sep = 0`). |
| `tilemap_grids_16x16.json` | JSON | *(Reference data)* | Exact `16×15` tile ID matrices for Phase 1 & Phase 2. |

> **Note when viewing `ts_spotlight_mask_16x16.png`**: Because the mortar/silhouette pixels are opaque black (`#000000`) and the brick interiors are transparent (`rgba(0,0,0,0)`), image viewers with black backgrounds may make the PNG look solid black. Check `reference/guide_tileset_visual_preview.png` to see the exact 8×3 layout clearly highlighted in brick-pink!
>
> **Tile Index Map (8 columns × 3 rows)**:
> - **Tile 0** `(col 0, row 0)`: Empty transparent `16×16` (reserved by GMS 1.4)
> - **Tile 1** `(col 1, row 0)` & **Tile 2** `(col 2, row 0)`: The 2 alternating `16×16` Brick Wall mortar tiles! Every row alternates `1, 2, 1, 2, ...` across all 16 columns (`0..15`) and all 15 rows (`0..14`).
> - **Tiles 3..21**: The Chip & Dale silhouette mask `16×16` tiles placed on **Tile Layer Depth `-10`** in the `6×4` region at grid columns `2..7` (`x = 32, 48, 64, 80, 96, 112`), grid rows `5..8` (`y = 80, 96, 112, 128`):
>   - **Row `y = 80` (grid row 5, cols 2..7)**: `[  3,  4,  5,  6,  7,  8 ]`
>   - **Row `y = 96` (grid row 6, cols 2..7)**: `[  9, 10, 11, 10, 12, 13 ]` *(Tile 10 is solid silhouette black)*
>   - **Row `y = 112` (grid row 7, cols 2..7)**: `[ 14, 10, 15, 10, 16, 17 ]`
>   - **Row `y = 128` (grid row 8, cols 2..7)**: `[ 18, 10, 19, 20, 10, 21 ]`

### 3. `sprites/`
| File | Size | GMS 1.4 Resource Name | Settings |
|---|---|---|---|
| `spr_spotlight_beam_strip4.png` | `256×64` (4 frames of `64×64`) | `spr_spotlight_beam` | In GMS Sprite Editor: **Edit Sprite → File → Create from Strip** (GMS auto-detects `_strip4` as 4 subimages of `64×64`). Set **Origin: Center (`X = 32, Y = 32`)**. Subimages `0..3` contain the exact 4-step NES hardware palette fade! |
| `spr_spotlight_beam.png` | `64×64` | *(Single-frame backup)* | Full-brightness frame 0 standalone PNG. |
| `spr_chip_dale_silhouette_mask.png` | `96×64` | `spr_chip_dale_silhouette` *(Optional)* | Origin `(0, 0)`. Assembled complete `96×64` silhouette mask if you prefer placing 1 object at `(32, 80)` instead of painting the 24 silhouette tiles on Depth `-10`. |

### 4. `audio/`
| File | Duration | GMS 1.4 Resource Name | Trigger Timing |
|---|---|---|---|
| `snd_spotlight_drumroll.wav` | `2.37s` (`44.1 kHz` 16-bit mono) | `snd_spotlight_drumroll` | Triggered automatically by `obj_spotlight_beam` at Phase 2 start (`timer == 477`). |
| `snd_spotlight_brass_swell.wav` | `1.42s` (`44.1 kHz` 16-bit mono) | `snd_spotlight_brass_swell` | Triggered automatically right as the spotlight snaps & locks onto Chip & Dale (`timer == 627`), swelling right into the Title Screen drop! |
| `snd_spotlight_sequence_full.wav` | `3.92s` (`44.1 kHz` 16-bit mono) | *(Combined reference)* | Continuous recording of both cues with original gap (`NES Frames 653..888`). |

### 5. `gml/` (Object Properties & Code)
1. **`obj_spotlight_beam`**
   - **Sprite**: `spr_spotlight_beam`
   - **Depth**: `100` *(so it renders above `bg_spotlight_backdrop` and behind Tile Layers `0` and `-10`)*
   - **Events**:
     - **Create Event**: Paste `gml/obj_spotlight_beam_Create.gml`
     - **Step Event**: Paste `gml/obj_spotlight_beam_Step.gml`
   - **Room Placement**: Place 1 instance anywhere in `rm_spotlight_intro` (`256×240`, `Speed = 60`).
2. **`obj_chip_dale_silhouette`** *(Optional — only if you choose not to paint the `-10` tile layer)*
   - **Sprite**: `spr_chip_dale_silhouette`
   - **Depth**: `-10`
   - **Create Event**: Paste `gml/obj_chip_dale_silhouette_Create.gml`
   - **Room Placement**: Place at `(x = 32, y = 80)`.

### 6. `reference/`
- `ref_phase1_brick_sweep_f300.png` — Exact NES render during Phase 1 brick wall sweep
- `ref_phase2_silhouette_sweep_f780.png` — Exact NES render as spotlight sweeps across Chip & Dale's silhouette
- `ref_phase2_silhouette_lock_f840.png` — Exact NES render when spotlight snaps & locks on Chip & Dale
- `guide_tileset_visual_preview.png` — High-contrast visual preview of `ts_spotlight_mask_16x16.png`
- `guide_room_tiles_phase1_bricks.png` & `guide_room_tiles_phase2_silhouette.png` — Full `256×240` visual guides for tiling the room

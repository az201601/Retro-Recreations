# Stage 1 (Downtown) — wide strip

One continuous background strip of the level, plus the tileset and tilemap that
reproduce it tile for tile. Pixel-exact: `tools/stitch_level.py` rebuilds the
strip from `tileset.png` + `tilemap.csv` with **0 differing pixels**.

| File | What it is |
|---|---|
| `level.png` | 3584 × 240, background layer only (no sprites), 1:1 NES pixels |
| `page_00.png`, `page_01.png` | the same strip cut at 2048 px, for GMS texture pages |
| `tileset.png` | 337 unique 8×8 cells, 16 per row (a valid GMS tileset grid) |
| `tilemap.csv` | 448 columns × 30 rows, comma separated, `-1` = empty |
| `tilemap_00.csv`, `tilemap_01.csv` | the same grid, one file per page |
| `tiles.csv` | cell → position in `tileset.png` + how often the cell is used |
| `level.json` | window list, room assignment, camera x and per-window checks |
| `gml/scr_level_tiles.gml` | GMS 1.4 script that builds the tile layer from the CSV |

This covers the opening restaurant interior (camera 0–1792) and the blue-tiled
kitchen that follows it. The two are separate rooms: **each room restarts the
camera at 0**, so the stitcher places windows from their camera delta and then
checks them against the pixels already stitched — a window that lands on content
it disagrees with starts a new room at the right-hand edge instead. `level.json`
records the room number and the join type for every window.

## Importing into GameMaker Studio 1.4

1. **Background resources** `bg_stage1_downtown_0`, `_1`
   - *Create Background* → Load `page_00.png` (then `page_01.png`) → *Use as
     texture* off, *Smooth* off (this is pixel art).
   - Give them depth `10000`. Two pages because GMS 1.4 caps a texture page at
     2048 px and the strip is 3584 wide.
2. **Tileset background** `bg_ts_stage1_downtown`
   - *Create Background* → Load `tileset.png` → tick **Use as tileset**,
     tile width **8**, tile height **8**, separation 0, offset 0.
   - Do **not** tick "Use as texture"; tilesets are their own texture page.
   - 337 cells at 16 per row is 128 × 176, so it fits a texture page easily. It
     is a normal tileset grid — every multiple of 8 is a tile — which is why no
     single-row strip ships here (that would be 2696 px wide).
3. **Room** `rm_stage1_downtown`
   - Size 3584 × 240.
   - Backgrounds tab: `bg_stage1_downtown_0` at (0, 0) and
     `bg_stage1_downtown_1` at (2048, 0), depth 10000, *Stretch* off and
     *Horizontal tile* off on both.
   - Add a **Tile layer** at depth 5000 and pick `bg_ts_stage1_downtown`.
   - Drop a controller instance at (0, 0) whose Create event calls the importer
     once per page:
     ```gml
     scr_level_tiles("tilemap_00.csv", bg_ts_stage1_downtown,    0, 0, 8, 5000);
     scr_level_tiles("tilemap_01.csv", bg_ts_stage1_downtown, 2048, 0, 8, 5000);
     ```
4. **Included files** tab: add `tilemap_00.csv` and `tilemap_01.csv`.

If you would rather paint the layer by hand, open `tilemap.csv` in a
spreadsheet alongside `tiles.csv`; each number is the cell index in
`tileset.png`, 16 cells to a row.

### Why the tile layer *and* the flat image?

`level.png` is what the game looks like. The tile layer is what the level *is*:
it is what collision will be attached to, what lets you rework geometry, and
what keeps the file size flat when the stage gets longer. Both are generated
from the same capture, so they cannot drift apart.

### Texture pages

GMS 1.4 caps a texture page at 2048 × 2048. The strip is 3584 px wide, so it
ships as `page_00.png` (2048) + `page_01.png` (1536), each with its own tilemap
and its own tile layer in the same room. `level.png` is the unsplit strip, handy
for reference and for the build script. Both pages rebuild from the shared
tileset with **0 differing pixels**.

## How it was produced

```bash
.venv/bin/python tools/solve_route.py \
  --state tools/emu/out/scrollcap/s10954.fcs \
  --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" \
  --workdir tools/emu/out/solve20 --iterations 200 --beam 8 --checkpoint-step 64

.venv/bin/python tools/stitch_level.py \
  --workdir tools/emu/out/solve20 \
  --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" \
  --out tools/emu/out/stage20 \
  --start tools/emu/out/scrollcap/s10954.fcs --max-cam 1200
```

`level.json` records every window's true camera x and confirms that the
background re-render matched the emulator frame pixel for pixel (the only
excluded pixels are those covered by sprites, which are filled from a
neighbouring window).

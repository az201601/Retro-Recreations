# Stage 1 (Downtown) — wide strip

One continuous background strip of the level, plus the tileset and tilemap that
reproduce it tile for tile. Pixel-exact: `tools/stitch_level.py` rebuilds the
strip from `tileset.png` + `tilemap.csv` with **0 differing pixels**.

| File | What it is |
|---|---|
| `level.png` | 1392 × 240, background layer only (no sprites), 1:1 NES pixels |
| `tileset.png` | 194 unique 8×8 cells, 16 per row |
| `tileset_strip.png` | the same 194 cells in a single 1552 × 8 row (for Add from Strip) |
| `tilemap.csv` | 174 columns × 30 rows, comma separated, `-1` = empty |
| `tiles.csv` | cell → position in `tileset.png` + how often the cell is used |
| `level.json` | window list with real camera positions and per-window checks |
| `gml/scr_level_tiles.gml` | GMS 1.4 script that builds the tile layer from the CSV |

This covers the opening restaurant interior of the stage: tables, food, the
window with the skyline, and the climbable pillar at the right-hand end
(camera x 0–1142, player world x 0–1339).

## Importing into GameMaker Studio 1.4

1. **Background resource** `bg_stage1_downtown`
   - *Create Background* → Load `level.png` → tick *Use as texture* off,
     *Smooth* off (this is pixel art).
   - Give it a depth of `10000` so sprites draw in front.
2. **Tileset background** `bg_ts_stage1_downtown`
   - *Create Background* → Load `tileset.png` → tick **Use as tileset**,
     tile width **8**, tile height **8**, separation 0, offset 0.
   - Do **not** tick "Use as texture"; tilesets are their own texture page.
3. **Room** `rm_stage1_downtown`
   - Size 1392 × 240.
   - Backgrounds tab: assign `bg_stage1_downtown` at depth 10000,
     *Stretch* off, *Horizontal tile* off.
   - Add a **Tile layer** at depth 5000 and pick `bg_ts_stage1_downtown`.
   - Drop a controller instance at (0, 0) whose Create event calls
     `scr_level_tiles("tilemap.csv", bg_ts_stage1_downtown, 0, 0, 8, 5000);`
4. **Included files** tab: add `tilemap.csv` so the script can read it.

If you would rather paint the layer by hand, open `tilemap.csv` in a
spreadsheet alongside `tiles.csv`; each number is the cell index in
`tileset.png`, 16 cells to a row.

### Why the tile layer *and* the flat image?

`level.png` is what the game looks like. The tile layer is what the level *is*:
it is what collision will be attached to, what lets you rework geometry, and
what keeps the file size flat when the stage gets longer. Both are generated
from the same capture, so they cannot drift apart.

### Texture pages

GMS 1.4 caps a texture page at 2048 × 2048. This strip is 1392 × 240, so it
fits in one background with room to spare. As more of the stage arrives the
strip will exceed 2048 px wide; it will then be split into consecutive
`level_00.png`, `level_01.png` pages of at most 2048 px, each with its own
tile layer, and the room widened to match.

## How it was produced

```bash
.venv/bin/python tools/solve_route.py \
  --state tools/emu/out/scrollcap/s10954.fcs \
  --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" \
  --workdir tools/emu/out/solve5 --iterations 80 --beam 5 --checkpoint-step 64

.venv/bin/python tools/stitch_level.py \
  --workdir tools/emu/out/solve5 \
  --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" \
  --out tools/emu/out/stage5 \
  --start tools/emu/out/scrollcap/s10954.fcs
```

`level.json` records every window's true camera x and confirms that the
background re-render matched the emulator frame pixel for pixel (the only
excluded pixels are those covered by sprites, which are filled from a
neighbouring window).

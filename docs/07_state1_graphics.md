# State 1 (second screen) — graphics extraction & spotlight effect

Extractor: `tools/extract_state1.py` → `extracted/screens/state1/` (`state1_bg.png`, `emblem.png`, `emblem_one.png`, `preview_end.png`, `state1_data.json`).

## Palettes

State-1 config (`$D738`) points at bank 3 `$B081` (background, copied to staging `$05AE`) and `$B091` (sprites, staging `$05BE`):

- BG (×4 identical groups): `0F 0F 0F 20` — only pixel value 3 would show (white). The screen's BG tiles in fact use **only values 0/1**, so pixel value 1 = colour `$0F` = **black ink**, value 0 = transparent/backdrop. The picture is a *silhouette*.
- SPR groups: `0F 17 37 20` / `0F 3C 15 26` / `0F 36 16 26` / `0F 1C 3C 20`.

Palette engine (`$C06C` in NMI, set up by `$C1B0/$C1BF`): 8 groups of 4 colours are faded by raising the colour "row" (`$63` = $00→$10→$20→$30, `active = min((staging&$0F)|row, staging)`), masked per group by `$64` bits (table `$C174`). Fade-in set at `$D09D` (mask `$FF`, period 4) completes in ≈16 frames; `$C1CE` blocks the main loop until it finishes. Steady-state palette equals the staging bytes above. RGB values in the extractor use the standard NES palette table (data-only choice, swap later if desired).

## Background (CHR bank 31 → PPU $0000 table)

State init `$D63D` first fills both nametables with tile `$00`/attr 0 (`$C309`), then `$D74C` loads:

- bank 3 `$B98B` stream → `$2000` and `$2400` (same data both): header `20 02` = 32 tiles × 2 rows of brick-pattern tiles (`CC CD CA CB` repeating).
- bank 3 `$B9CD` stream → `$2144`: header `0C 08` = 12 × 8 tiles at row 10, cols 4–15: the character silhouettes against bricks.

Stream format (`$C46D`): blocks of `[count_code, row_code, literal data...]`; count_code bits 0–5 = bytes/row (0→64), bit 6 = column mode, bit 7 = RLE; row_code bits 0–5 = rows, bit 7 = repeat-row. Only literal mode occurs here (extractor asserts the rest).

`state1_bg.png` is exported as **black ink (value >0) on transparency** — see compositing below.

## Sprites: the spotlight disc (CHR bank 29 → PPU $1000 table, 8×16)

Object rendering (`$F191`, PRG bank 5): `$032C,X` selects a metasprite set from the pointer table at `$8000`, `$0338,X` a frame. Frame format: `[count][dx, dy, tile, attr][tile, attr] × (count−1)` — a horizontal strip of 8×16 sprites advancing 8 px per tile (count bit 7 would make it vertical). Object flag byte `$0344` is XORed into each sprite's attribute (so bits 6/7 flip the whole object), and when `$0344` bit 7 is set the object Y is raised by `$03BC` (32 here).

State 1 uses set 0 frame 0 for all four objects: strip of 4 tiles (`$C5 $C7 $C9 $D5`, attr `$02` → sprite palette 2) at offset (−32,−32). Parent flags `$20`; children `$60/$A0/$E0` (the script's FLG ops) produce the four flip combinations → a 64×32 pale disc (`emblem.png`, anchor at image (32,32) = the object's position, i.e. disc bottom-centre).

Trajectory (from decoded script `$F2DB`, velocities via the nibble-packed format; see `state1_data.json`): start (192,−64); phases 128f (vy+2), 96f (−1.375,−1.375), 64f (+2,0), 48f (−1.375,+1.375), 128f (−2,0), then SETY 104 + 134f (+2,0), 16f (−4,0), WAIT 60 → state 2 (≈674 frames; button press skips). End anchor (70,104), inside the silhouette patch.

## Compositing (why it looks right)

The disc's effective attribute is `$02 XOR $20 = $22`: palette 2 **with behind-background priority**. On the NES the disc therefore shows exactly where the BG tile pixel is 0 and is hidden by the black silhouette pixels (value 1). GMS reproduction: black canvas → `spr_spotlight1` at the anchor → `spr_state1_bg` (black-ink overlay) on top. `preview_end.png` shows the result at the final position.

The per-frame bank-3 routine `$B508` (another `$C54E` dispatch, on `$98`) is **idle during state 1** (`$98=0` → immediate RTS), so no other palette animation applies to this screen.

## Deviations / TODO

- Fade-out into state 2 (shared exit ≈20f + fades) not yet applied in GMS; fade-in (≈16f) is approximated with a black alpha ramp in `obj_nes_core` Draw.
- BG scroll Y=1 (config bytes) ignored — sub-1-tile shift, revisit with the M2 renderer.
- Sprite-versus-BG priority is by draw order; per-pixel NES priority is equivalent for this screen's data but will be revisited for gameplay screens.
- Sounds `$7F` (entry), `$74` (frame ≈464), `$73` (≈614) logged only; audio milestone later.

## Transfer #3 (beginner steps also given in chat)

1. Create sprite `spr_spotlight1` from `extracted/screens/state1/emblem.png`, set **Origin X=32, Y=32** (type the numbers; the anchor is the disc's centre, so for this 64×64 image the Center button happens to give the same result).
2. Create sprite `spr_state1_bg` from `extracted/screens/state1/state1_bg.png`, Origin stays **0, 0**.
3. Re-paste `gml/scripts/scr_nes_init.gml`, `gml/scripts/scr_game_state_step.gml`, and `gml/objects/obj_nes_core/Draw.gml` (double-click each in the tree, Ctrl+A, Delete, paste the new file, green ✓).
4. Ctrl+S, F5. Expect: fade-in, then a pale spotlight disc swooping around the dark screen over faint silhouettes; pressing any button (or waiting ~11 s) ends it to STATE 2 (black placeholder).

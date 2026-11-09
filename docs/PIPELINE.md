# Asset rip pipeline

Everything visual and audible in `ChipNRangers2.project/` comes from the US
cartridge `Chip 'n Dale - Rescue Rangers 2 (USA).nes` (256 KB, Mapper 1 / MMC1,
16 × 16 KB PRG, 16 × 8 KB CHR, vertical mirroring).

## Tooling note

The intended instrument was **Mesen**'s debugger (PPU viewer, memory viewer,
sprite viewer). This machine has no display and no Mesen binary, so the same
information was extracted headlessly with **[jsnes](https://github.com/bfirsh/jsnes)**
driven by Node: the emulator core exposes the PPU registers, VRAM, OAM and a
sample callback on the APU, which is everything the Mesen viewers would show.

| Mesen would give | what was used instead |
| --- | --- |
| CHR / pattern viewer | `vramMem` + `chrMem` dump → `tools/make_atlas.py` |
| Nametable viewer | scroll registers + `f_nTblAddress` → `tools/render_map.py` |
| Sprite viewer | OAM mirror at `$0600–$063F` → `tools/extract_player3.mjs` |
| Memory viewer | direct reads of `nes.cpu.mem` |
| Audio recording | `onAudioSample(L, R)` at 22 050 Hz → `tools/capmusic.mjs` |

The helper scripts (*jsnes* itself, the `*.mjs` extractors) lived outside the
repository in a scratch folder; their outputs are checked in under
`assets_src/`.

## 1. Tiles

```js
const vram = Buffer.from(nes.ppu.vramMem);   // 2 KB nametables + palettes
const chr  = nes.ppu.chrMem;                 // 8 KB CHR (pattern tables)
```

`tools/make_atlas.py` slices CHR into 8×8 tiles, drops the tiles that are never
referenced by a nametable, and packs the rest into `tiles_atlas.png`
(1 869 tiles) with `tiles_raw.json` / `tiles_filtered.json` describing the
mapping. The NES RGB palette is taken from the master palette used by the PPU
emulation, so the colours match the hardware output.

## 2. Background

The level is a horizontally scrolling nametable pair (vertical mirroring, so
two 256-px screens). For each rendered frame the camera X is

```js
camX = (ppu.f_nTblAddress & 1) * 256 + ppu.regHT * 8 + ppu.regFH;
```

and the same value is mirrored in RAM at `$00AD/$00AE`, which made it trivial to
step the game until the scroll stops and then render a full 512 × 240 image from
VRAM (`tools/render_map.py` → `assets_src/map_raw.png`).

Only the opening screen is a genuine 512-px render; `tools/gen_level.py` uses
it 1:1 for `x < 256` and extends the stage to 1 280 px by re-tiling the
authentic wallpaper tile (`(0,96)–(32,128)`, verified to be seamless) and
repeating the ripped counter / shelf / decoration pieces. That keeps the whole
stage on-model without inventing new tile art.

## 3. Player sprites

OAM slot 56–63 is the player (slots 52–55 are the HUD hearts). Each frame the
extractor records every player OAM entry (x, y, tile, attribute, palette) and
composites the 16 × 24 character (two 8 × 16 objects plus feet) into a 32 × 32
canvas with the origin at `(16, 26)`:

```js
const px = vramMem[0x3F00 + ((0x10 + (attr & 3) * 4 + pix) & 0x1F)];
```

87 frames were captured and tagged by action
(`assets_src/player_raw3/f###_<tag>.png` + `meta.json`):

| animation | frames | used by |
| --- | --- | --- |
| idle | f002, f010 | `sprPlayerIdle` |
| walk | f020–f033, f067–f078 | `sprPlayerWalk` |
| jump / fall | f046–f066 | `sprPlayerJump` |
| pick-up / throw | f079–f086 | `sprPlayerAct` |

## 4. Other sprites

* `sprEnemy` — the kitchen-stage bug, cropped from the sprite layer.
* `sprHeart` — the 8 × 8 HUD heart at map `(16, 209)`.
* `sprSpark` — hit/dust particle.
* `sprCrate` — drawn pixel-by-pixel in the stage palette
  (`tools/gen_crate.py`) to match the small blue crates that sit on the
  shelves in the ripped screen; the game's crates are not sprites, they are
  background tiles, so no sprite frame existed to crop.
* `sprSolid` — a fully transparent 16 × 16 sprite; it exists only as a
  collision mask for the invisible walls.

## 5. Sound

The APU callback was tapped with the emulator running at 22 050 Hz. After the
title → stage transition the input was left idle for 26 s, which yields the
stage-1 background music with no sound-effect contamination
(`assets_src/audio/bgm_stage1.wav`, RMS ≈ 2 450, i.e. definitely music and not
silence).

The seven sound effects (`sndJump`, `sndThrow`, `sndPickup`, `sndBreak`,
`sndHurt`, `sndEnemyHit`, `sndClear`) are *not* rips: the APU channels were not
separated, so the effects are synthesised square-wave sweeps and noise bursts
in `tools/gen_sounds.py`, tuned to the NES timbre.

## 6. Level data

`assets_src/level1.json` is the single description of the stage that both the
background composer and the room generator consume:

```json
{ "width": 1280, "height": 240,
  "platforms": [{ "x": 0, "y": 184, "w": 80, "kind": "ledge" }, ...],
  "crates":  [{ "x": 300, "y": 144 }, ...],
  "enemies": [{ "x": 370, "y": 144, "left": 288, "right": 432 }, ...],
  "hearts":  [{ "x": 580, "y": 152 }, ...],
  "playerStart": { "x": 24, "y": 184 }, "goalX": 1240 }
```

Platform `y` values are the *walkable surface* (the pixel the player's feet
rest on); the background composer offsets the counter art by −4 px to match.

## 7. GameMaker output

`tools/gen_project.py` writes the entire GMS 1.4 project: `.gmx` XML for every
resource plus the GML inside `<argument><string>` blocks (newlines as `&#xA;`).
The format was cross-checked against
[Super-Mega-Engine](https://github.com/rafaelcp/Super-Mega-Engine), a
GMS 1.4.1760 project that uses the same layout, including the reusable
`Configs/Default.config.gmx` Windows runner configuration.

`tools/verify_project.py` re-parses every `.gmx` and checks that each sprite
frame, background image and sound file referenced by the XML exists on disk.

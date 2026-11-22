# Chip 'n Dale — Rescue Rangers 2 (USA) — GMS 1.4.1760 Import Guide

Everything in this repo was extracted **from the original NES ROM**
(`Chip 'n Dale - Rescue Rangers 2 (USA).nes`) with the tools in `tools/`
(Nestopia libretro core + custom savestate/RAM/CHR analysis). This guide walks
through importing the assets, audio and GML code into
**GameMaker: Studio 1.4.1760** and wiring up a playable recreation of the
gameplay (Stage 1 — the giant kitchen).

---

## 1. What you got

| Folder | Contents |
|---|---|
| `assets/tiles/` | All 8192 CHR-ROM tiles as PNG sheets (`chr_bank_00.png` … `chr_bank_31.png`, 256 tiles each), `chr_meta.json` |
| `assets/sprites/` | `pose_chip_00…25.png` — full composed Chip poses (idle/walk/jump/throw, both facings), `spr_XX_*.png` — individual 8×16 sprite cells, `obj_*.png` — HUD hearts/counter, `poses_meta.json` |
| `assets/sprites2/` | The fly enemy ("Randy") animation frames (`obj_*.png`), more pose captures |
| `assets/stage1/` | `screen_00.png` (pixel-exact NES render of the kitchen start screen), `screen_01/02.png` (further camera positions), `stage_full.png` (raw nametable render), `tilemap.json`/`tilemap.csv` (tile indices + palettes), `collision.csv` (64×30 collision grid), `panorama.json` (screen scroll offsets) |
| `audio/` | `title_theme.ogg`, `character_select.ogg`, `stage_intro.ogg`, `stage1_theme.ogg`, `jingle_pause.ogg`, `jingle_unpause.ogg`, `sfx_jump.ogg` |
| `gml/` | One `.gml` file per GMS 1.4 script/object event — paste contents into the matching event |
| `tools/` | The extraction/verification toolchain (see §7) |

Audio was recorded from the real game at 48 kHz stereo via the emulator;
`sfx_jump.ogg` was isolated by differential capture (jump-input run minus
no-input run — the game is deterministic, so subtracting cancels the music).

---

## 2. Physics constants (measured from the NES game)

These live in `gml/scr_init.gml`. They were measured frame-by-frame from RAM
watch (`$00C2` = player Y, `$0313/$0314` = 8.8 fixed-point world X, 60.0988 fps):

| Constant | Value | Evidence |
|---|---|---|
| `walk_speed` | **2.0 px/frame** | world X 24→44 in 10 frames while holding right |
| `jump_v0` | **−7.2 px/frame** | first rise deltas 7,7,6 px/frame |
| `gravity_hold` | **0.38 px/f²** | rise deltas decay ~0.4/frame while A held |
| `gravity_fall` | **1.0 px/f²** | fall deltas +1,+2,+3,+4,+5,+6 |
| `max_fall` | **6.0 px/frame** | terminal velocity plateau |
| `jump_hold_max` | **20 frames** | full jump = 67 px apex, 39 frames airtime |
| tap jump | 14 px apex | A held 2 frames |
| full jump | 67 px apex | A held ≥19 frames |

Walk cycle: 4 poses, ~8 frames each (from `$07A8` anim frame index).
Damage: 1 heart, ~90-frame invulnerability with blinking (from gameplay).

---

## 3. Import steps (GMS 1.4.1760)

### 3.1 Sprites

1. **File → Import Sprites** — import every `assets/sprites/pose_chip_*.png`
   keeping the file names (`pose_chip_00` … `pose_chip_25`).
2. For each chip sprite set **Origin: Bottom-Middle** (the GML treats `y` as
   the feet position — matching the NES RAM convention).
3. Import `assets/sprites2/obj_*.png` frames of the fly as one sprite
   `spr_fly` (add each PNG as a frame) or separate sprites `spr_fly_0/1`.
4. From `assets/sprites/` import the HUD art: hearts → `spr_heart` /
   `spr_heart_empty`, the counter strip → `spr_hud_counter`. For the box,
   crop the checkered cube from `pose_chip_04` (the held box) or take tile
   `0x2B` from `assets/tiles/chr_bank_02.png` and colour it with sprite
   palette 1 — name it `spr_box`.

> The poses face **right**; the code flips with `draw_sprite_ext(..., facing, ...)`.
> If you imported left-facing poses for some indices, adjust the table in
> `obj_player_draw.gml`.

### 3.2 Backgrounds / room art

1. Import `assets/stage1/screen_00.png` as background `bg_stage_start`
   (256×240, no transparency, no tiling).
2. Create a new **room**: size **256×240**, `room_speed = 60`, snap 8.
   Set `bg_stage_start` as Background 0 (visible, not tiled, at 0,0).
3. Optional multi-screen: import `screen_01.png`, `screen_02.png` as frames of
   one sprite `bg_stage` and let `obj_level` draw them at `256*i` (see
   `gml/obj_level_draw.gml`; set `global.screens` in `scr_init.gml`).
   `panorama.json` records the camera offset each screen was captured at.

### 3.3 Sounds

Import the `.ogg` files in `audio/` as background sounds / sounds:

| Resource name | File | Type |
|---|---|---|
| `mus_title` | `title_theme.ogg` | background (loop) |
| `mus_charsel` | `character_select.ogg` | background |
| `mus_stage` | `stage1_theme.ogg` | background (loop) |
| `mus_intro` | `stage_intro.ogg` | background |
| `snd_jump` | `sfx_jump.ogg` | sound |
| `snd_pause` | `jingle_pause.ogg` | sound |
| `snd_unpause` | `jingle_unpause.ogg` | sound |

(Then hook them: `sound_loop(mus_stage)` in `obj_game` Create, `sound_play(snd_jump)`
in the jump-start branch of `obj_player_step.gml`, etc.)

### 3.4 Scripts (paste each `gml/*.gml` as a script resource of the same name)

| Script resource | File |
|---|---|
| `scr_init` | `gml/scr_init.gml` |
| `scr_solid_at` | `gml/scr_solid_at.gml` |
| `scr_move_h` | `gml/scr_move_h.gml` |
| `scr_move_v` | `gml/scr_move_v.gml` |
| `scr_string_split_vals` | `gml/scr_string_split_vals.gml` |

### 3.5 Objects (paste the matching file into each event)

| Object | Events | File(s) |
|---|---|---|
| `obj_game` | Create, Step | `gml/obj_game_create.gml`, `gml/obj_game_step.gml` |
| `obj_level` | Create, Draw | `gml/obj_level_create.gml`, `gml/obj_level_draw.gml` |
| `obj_player` | Create, Step, Draw | `gml/obj_player_create.gml`, `gml/obj_player_step.gml`, `gml/obj_player_draw.gml` |
| `obj_camera` | Step | `gml/obj_camera_step.gml` |
| `obj_enemy_fly` | Create, Step, Draw | `gml/obj_enemy_fly_*.gml` |
| `obj_box` | Create, Step, Draw | `gml/obj_box_*.gml` |
| `obj_hud` | Draw (depth −100) | `gml/obj_hud_draw.gml` |

Room instance order (Create event order matters — `obj_game` first):

1. `obj_game` (loads `collision.csv`)
2. `obj_level`, `obj_camera`, `obj_hud`
3. `obj_player` at (32, 128)
4. a few `obj_enemy_fly` (e.g. at 160,96 and 380,120)
5. `obj_box` instances on the tables (e.g. 200,152 / 216,152)

### 3.6 Included file

Copy `assets/stage1/collision.csv` into the **Included Files** of your project
(so `file_text_open_read("collision.csv")` finds it). It is a 64×30 grid of
0/1 (8 px cells): 0–31 = screen 1, 32–63 = screen 2. The platform rows were
derived from measured rest heights (left table 184, mug 136, burger 120,
mid table 160, window shelf 88, floor 216) — nudge rows in the CSV to taste.

### 3.7 Controls

| Keys | NES |
|---|---|
| ← / → or A / D | D-pad |
| Z / Space / ↑ (tap for short hop, hold for full) | A (jump) |
| X | B (pick up / throw boxes) |

---

## 4. How faithful is it?

* Physics: measured from the original to sub-pixel level (see §2) — tap/full
  jump, variable jump height, terminal velocity and walk speed match.
* Art & audio: extracted/recording from the ROM — pixel-exact.
* Collision grid: approximate (platform tops measured, extents hand-placed).
* Enemy AI: approximated from observation (patrol + sine bob + contact damage).
* The NES rotates OAM sprite order every frame to hide the 8-sprites-per-line
  flicker; GMS has no such limit, so the recreation omits it.

---

## 5. Extending the recreation

The tools in `tools/` are re-runnable (Python 3 + Pillow/numpy/soundfile +
a libretro core, see `tools/README` notes in each file header):

* `tools/extract_sprites.py` / `extract_poses.py` — more sprites/poses from any
  input timeline or savestate.
* `tools/capture_panorama.py` — drive through the level to capture further
  screen PNGs at every camera position.
* `tools/capture_audio.py` — record music/SFX windows; channel-isolated
  capture (`--channels sq1|sq2|tri|noi|dpcm`) is available for remixing.
* `tools/extract_stage.py` — nametable render + tilemap JSON/CSV from a state.
* `tools/ram_watch.py` / `patch_state.py` — the RAM watch / state poker used
  to reverse-engineer the physics.

Savestates used by the guide scripts live in `work/ss/` (`frozen.state` is the
kitchen stage entry point; press START ≥10 frames to unpause — the kitchen
starts PAUSED, exactly like the real game).

## 6. Known gaps

* Stage 1 beyond the first two screens is captured only partially
  (`screen_01/02.png`); run `capture_panorama.py` while playing to fill in more.
* Pickup/throw SFX were not cleanly isolatable (B makes no sound unless
  carrying a box); use `sfx_jump.ogg`'s differential method to grab more.
* Title/menu flows are not recreated (assets are provided: `mus_title`,
  `mus_charsel`, and the CHR banks contain all logo/font tiles).

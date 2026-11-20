# Chip 'n Dale Rescue Rangers 2 — Step-by-Step Guide
### For GameMaker Studio 1.4.1760 (complete beginners welcome!)

This guide takes you from an empty GameMaker project to a playable
Chip 'n Dale 2 recreation, one click at a time. You don't need any prior
GameMaker experience — just follow along. Everything is written for
**GMS 1.4.1760** specifically (the menus and function names are different
from newer GameMaker versions, so don't follow GameMaker 2 tutorials).

**Time needed:** about 1–2 hours, mostly clicking and pasting.

---

## Part 0 — What you're building

A side-scrolling platformer that runs at the NES's native **256×240**
resolution and **60 frames per second**, with the original game's movement
(walk speed, jump, gravity, animation timing). The code uses a clean,
modern structure (one settings script, a state machine for the player,
tile-grid collision) but only uses features that exist in GMS 1.4.

You'll create these resources (full checklist in **Appendix A**):

- **6 scripts** — the reusable code (settings, input, collision).
- **7 objects** — player, enemy, block, acorn, pickup, camera, game controller.
- **Sprites, tilesets, backgrounds, sounds** — imported from `EXTRACTED/`.

---

## Part 1 — Install GameMaker Studio 1.4.1760

1. Download **GameMaker Studio 1.4.1760** (the last 1.4 build). It's a free
   download from YoYo Games' archive / the GameMaker website. Search for
   "GameMaker Studio 1.4.1760 download".
2. Install it and launch it. You'll see the **GameMaker welcome screen**
   with options like *Create a new project*.
3. (Optional but recommended) In the welcome screen, open
   **Preferences → Editor** and tick **"Show code editor line numbers"** —
   it makes the code easier to read.

> **Note:** GMS 1.4 is old software. On modern Windows it runs fine, but if
> the welcome screen looks odd, just make sure you're running the
> `GameMaker-Studio-v1.4.1760` installer (not GameMaker 2).

---

## Part 2 — Create the project and set the NES resolution

1. On the welcome screen, click **Create a new project**.
2. Choose a name like `ChipNDale2` and a folder, then click **Save**.
   GameMaker creates a project with one empty room (`room0`).
3. **Rename the room:** in the Resource Tree (left panel), right-click
   `room0` → **Rename** → type `rm_level1` → Enter.
4. **Open the room settings:** double-click `rm_level1`. In the Room Editor,
   click the **Room Settings** tab (top row of icons) and set:
   - **Width:** `256`
   - **Height:** `240`
   - **Speed:** `60`  ← this is the NES frame rate. **Very important.**
5. **Enable the view** (so the camera works): in the Room Editor, click the
   **View** tab and tick **Enable views**. Set:
   - **View Width:** `256`, **View Height:** `240`
   - **Port Width:** `256`, **Port Height:** `240`
   - (Leave "Follow object" empty — our `obj_camera` controls the view.)
6. Click **OK** to close the room settings.

> **Why 256×240 and 60 speed?** That's the NES screen size and frame rate.
> Keeping them means every pixel and every physics value matches the
> original exactly. GameMaker will scale the 256×240 view up to fill your
> window while keeping the aspect ratio.

---

## Part 3 — Import the graphics and sounds

All the art is in the `EXTRACTED/` folder. Here's how to import each type.
(Do this in the **Resource Tree** — right-click the folder you want, e.g.
**Sprites**, and choose the import option.)

### 3a. Sprites (the characters and objects)

1. Right-click **Sprites** → **Import Sprites**.
2. Browse to `EXTRACTED/` and select the sprite sheet PNG(s).
3. In the **Sprite Editor**, set:
   - **Origin:** for the player/enemy, choose **Bottom Centre** (feet at the
     bottom). For items, **Centre** is fine.
   - If you imported a sheet of multiple frames, use the **"Split"** tool
     (or set the frame size) to cut it into individual frames.
4. Name them exactly as in **Appendix A** (e.g. `spr_player`).

> **About colours:** NES tiles store only *shape* (2 bits/pixel); the colours
> come from a palette + per-tile "attribute tables" in the level data. That's
> why the extracted tilesets are **grayscale** (accurate shape data) with
> `palette.png` alongside. For tiles in their **exact original colours**, use
> **Mesen** (Appendix B) — its PPU Viewer renders tiles with the correct
> sub-palette applied, so you can screenshot/export pixel-perfect art.
> The code is written so you can swap sprites in freely.

### 3b. Tilesets (the level graphics)

1. Right-click **Tilesets** → **Create Tileset**.
2. Name it `ts_level`. Click **Import** and choose
   `EXTRACTED/tileset_level.png`.
3. Set **Tile Width:** `8`, **Tile Height:** `8` (NES tiles are 8×8).
4. Click **OK**. (You can now paint tiles in the room editor — Part 6.)

### 3c. Backgrounds

1. Right-click **Backgrounds** → **Import Backgrounds**.
2. Choose the background PNG(s) from `EXTRACTED/` (e.g. the title art).
3. Name them as in **Appendix A**.

### 3d. Sounds

1. Right-click **Sounds** → **Import Sounds**.
2. Add short sound effects named `snd_jump`, `snd_throw`, `snd_bounce`,
   `snd_hit`, `snd_pickup`, `snd_hurt` (see **Appendix A**). You can use any
   .wav files you like, or record the originals from Mesen.
3. **Enable the new audio engine:** open **Global Game Settings** (in the
   Resource Tree) → **Audio** tab → tick **"Use new audio engine"**. This
   makes `audio_play_sound()` work (the code uses it).

---

## Part 4 — Create the scripts (the code library)

Scripts are reusable chunks of code. Create each one, then paste the matching
file from the `GML/` folder into it.

**For each script:**
1. Right-click **Scripts** → **Create Script**.
2. Name it (e.g. `scr_init`).
3. Open the `GML/scr_init.gml` file from this project folder, copy all the
   text, and paste it into the script editor.
4. Press **Ctrl+S** to save the script.

Create these **6 scripts** (names must match exactly):

| Script name | Paste from |
|---|---|
| `scr_init` | `GML/scr_init.gml` |
| `scr_input` | `GML/scr_input.gml` |
| `scr_tile_solid_at` | `GML/scr_tile_solid_at.gml` |
| `scr_rect_solid` | `GML/scr_rect_solid.gml` |
| `scr_move_x` | `GML/scr_move_x.gml` |
| `scr_move_y` | `GML/scr_move_y.gml` |

> **Important:** In GMS 1.4, each script IS a function. That's why the
> collision helpers are separate scripts — you call them like
> `scr_move_x(hsp)`. (The `function` keyword from newer GameMaker does
> **not** exist in 1.4, so don't use it.)

---

## Part 5 — Create the objects (the characters and things)

Objects are the things that exist in the game. For each object:
1. Right-click **Objects** → **Create Object**.
2. Name it (e.g. `obj_player`).
3. Set its **Sprite** (from Part 3).
4. Click **Add Event**, pick the event type, and paste the matching code.

Create these **7 objects**:

### `obj_game` (the controller — holds the game rules)
- **Sprite:** none (leave empty).
- **Game Start** event → paste `GML/scr_init.gml`'s *call* only:
  ```
  scr_init();
  ```
  (This sets up all the physics constants before anything else runs.)
- **Create** event → paste `GML/obj_game_Create.gml`.
- **Room Start** event → paste `GML/obj_game_RoomStart.gml`.
- **Step** event → paste `GML/obj_game_Step.gml`.
- **Draw** event → paste `GML/obj_game_Draw.gml`.

### `obj_player` (Chip / Dale)
- **Sprite:** `spr_player`.
- **Create** → `GML/obj_player_Create.gml`.
- **Step** → `GML/obj_player_Step.gml`.

### `obj_enemy` (patrol enemy)
- **Sprite:** `spr_enemy`.
- **Create** → `GML/obj_enemy_Create.gml`.
- **Step** → `GML/obj_enemy_Step.gml`.

### `obj_block` (throwable crate/barrel)
- **Sprite:** `spr_block`.
- **Create** → `GML/obj_block_Create.gml`.
- **Step** → `GML/obj_block_Step.gml`.

### `obj_acorn` (thrown projectile)
- **Sprite:** `spr_acorn`.
- **Create** → `GML/obj_acorn_Create.gml`.
- **Step** → `GML/obj_acorn_Step.gml`.

### `obj_pickup` (flower / star)
- **Sprite:** `spr_pickup`.
- **Create** → `GML/obj_pickup_Create.gml`.
- **Step** → `GML/obj_pickup_Step.gml`.

### `obj_camera` (follows the player)
- **Sprite:** none.
- **Create** → `GML/obj_camera_Create.gml`.
- **Step** → `GML/obj_camera_Step.gml`.

> **Adding events in GMS 1.4:** With the object open, click **Add Event**.
> A window shows event categories (e.g. **Other**). For **Game Start** and
> **Room Start**, look under **Other**. For **Create**, **Step**, **Draw**,
> they're in their own categories. Pick the one you need, then paste.

---

## Part 6 — Build the room and paint the level

1. Open `rm_level1` (double-click it).
2. **Place the objects:** in the Room Editor, click the **Objects** tab,
   select `obj_game`, and click in the room to place it. Do the same for
   `obj_player` (where Chip starts), `obj_camera`, and a few `obj_enemy`,
   `obj_block`, `obj_pickup` instances.
3. **Paint the solid tiles:** click the **Backgrounds** tab (tile painting).
   Select the `ts_level` tileset, then choose the background layer you'll
   use for solids. **Name that background `bg_solid`** (the code looks for
   this exact name in `obj_game_RoomStart`). Paint the ground, platforms
   and walls with solid tiles.
4. **(Optional) Add a visual background:** on another background layer,
   place a background image (from Part 3c) behind the tiles.
5. Click **OK** to save the room.

> **How collision works:** When the room starts, `obj_game` scans every tile
> on the `bg_solid` layer and builds a grid. The player/enemy/block code
> then collides against that grid. So: **paint it with tiles, and it becomes
> solid automatically.** No per-object collision setup needed.

---

## Part 7 — Run and test!

1. Press **F5** (or click the green **Run** button) to play your game.
2. **Move** with the arrow keys or WASD.
3. **Jump** with `X` or `Space`. **Throw/pick up** with `Z` or `Ctrl`.
4. Walk into a block and press throw to pick it up, then throw to toss it.
   Hit an enemy with it!

If something doesn't work, see **Part 8**.

---

## Part 8 — Troubleshooting

| Problem | Fix |
|---|---|
| "Unknown variable" / red squiggles in code | A script or object name is misspelled. Names must match **Appendix A** exactly (including underscores). |
| `audio_play_sound` errors | You forgot to enable the new audio engine (Part 3d), or a `snd_*` sound is missing. Create all sounds in Appendix A. |
| Player falls through the floor | The floor tiles aren't on the `bg_solid` background, or `obj_game` isn't in the room. Check Part 6. |
| Player doesn't move / nothing happens | `scr_init()` isn't being called. Make sure `obj_game` has a **Game Start** event containing `scr_init();`. |
| Game runs at the wrong speed | Set the room **Speed** to `60` (Part 2). |
| Screen is stretched / wrong size | Set the room **View** to 256×240 and **Port** to 256×240 (Part 2). |
| `enum` / `ST.` errors | `scr_init` must run first (Game Start). Don't reference `ST.` in an object that runs before it. |
| Black screen | Make sure `obj_camera` is in the room and the view is enabled (Part 2 & 6). |

---

## Appendix A — Resource checklist (create ALL of these)

**Scripts (6):** `scr_init`, `scr_input`, `scr_tile_solid_at`, `scr_rect_solid`, `scr_move_x`, `scr_move_y`

**Objects (7):** `obj_game`, `obj_player`, `obj_enemy`, `obj_block`, `obj_acorn`, `obj_pickup`, `obj_camera`

**Sprites:** `spr_player` (8 frames), `spr_enemy` (2 frames), `spr_block`, `spr_acorn`, `spr_pickup`

**Tilesets:** `ts_level` (from `tileset_level.png`), and a background named `bg_solid` for the solid layer

**Backgrounds:** title/background images from `EXTRACTED/`

**Sounds (6):** `snd_jump`, `snd_throw`, `snd_bounce`, `snd_hit`, `snd_pickup`, `snd_hurt`

**Room:** `rm_level1` (256×240, speed 60, view enabled 256×240)

---

## Appendix B — Verifying everything in Mesen (the included `Mesen.exe`)

Mesen is a Windows NES emulator with a memory viewer, PPU viewer and
frame-stepping. Use it to confirm your recreation matches the original.

1. **Run `Mesen.exe`** and open `Chip 'n Dale - Rescue Rangers 2 (USA).nes`.
2. **Exact sprites:** open **Debug → PPU Viewer**. It shows the live sprite
   pattern table and palette. Screenshot Chip/Dale/enemies in their poses
   and import those PNGs as your `spr_*` sprites (Part 3a). This guarantees
   pixel-perfect frames.
3. **Palette:** the PPU Viewer shows the active 32-colour palette. Compare
   with `EXTRACTED/palette.png`.
4. **Physics:** use **frame advance** (pause, then step one frame at a time)
   and the **Memory Viewer** to measure walk speed, jump height and gravity.
   Known addresses: `$00A7`/`$00A8` (lives), `$03D4` (P1 health). Update the
   constants in `GML/scr_init.gml` with what you measure — see
   `PHYSICS_REFERENCE.md` for the full method.
5. **Backgrounds:** Mesen can export the tilemap / screenshot any screen, so
   you can rebuild the original levels tile-for-tile if you want.

---

## Appendix C — How the code works (the big ideas)

- **One settings script (`scr_init`):** every physics number lives in one
  place as `global.*` variables. Change a value, and the whole game updates.
- **State machine (player):** the player is always in one state (`ST.IDLE`,
  `ST.WALK`, `ST.JUMP`, …). The Step event updates the state, then sets the
  animation frame. This is much easier to read and extend than a tangle of
  `if` statements.
- **Tile-grid collision:** the level is a grid of 8×8 tiles. Objects move in
  small steps and ask "is this tile solid?" — exactly how the NES game works,
  and it means you build levels just by painting tiles.
- **Input abstraction (`scr_input`):** all keyboard/gamepad reading happens
  in one script that outputs simple values (`global.in_move_x`, etc.). The
  player code never touches the keyboard directly, so it's easy to remap.
- **60 steps/second:** the room speed is 60, matching the NES, so "pixels
  per step" in the code equals "pixels per frame" in the original.

Good luck, and have fun rescuing! 🐿️

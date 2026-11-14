# Step 06 – level 1, section 1: the player (Chip)

This step puts the player into the dining room: walking, jumping, crouching, dropping through
thin platforms, falling out of the picture and leaving on the right. The temporary arrow-key
camera of step 05 is gone; the camera now follows the player.

1. map and camera (step 05)
2. **player movement (this step) – Chip only; Dale is added next**
3. crates and bonus boxes
4. enemies, health, death, heart display

There are still no enemies, no crates to pick up, no hearts and no lives display. Crates in the
background are not solid yet: the player walks through them. B does nothing.

Frame numbers are level frames `lt`, as in step 05.

## What was confirmed in the original

- **Start**: x 24, y 192 (the feet), facing right. The buttons do nothing until `lt = 18`, one
  frame after full brightness.
- **Walking**: 2 pixels per frame, no acceleration. The walk picture changes every 8 frames.
  On the screen the player cannot go left of x 18 or right of x 238.
- **Camera**: it follows only to the right, when the player is at x 128 or further and moved
  right. It never scrolls back.
- **Jump**: A starts it. The speed starts at 110 sixteenths of a pixel per frame upwards and
  loses 6 per frame. Letting go of A ends the rise at once, so a tap gives a jump of 14 pixels.
  Falling speed is limited to 110. There is no sound for the jump itself.
- **Landing**: a short pose of 5 frames, cut short by LEFT, RIGHT or A. The landing sound starts
  2 frames after the landing and lasts 6 frames.
- **Crouching**: DOWN. The player can turn but not move, and is 16 high instead of 22.
  DOWN + A on a thin platform drops through it.
- **Blocks**: table tops and shelves can be stood on and jumped through from below. Solid
  blocks stop the player from the side and from below.
- **Blinking**: standing still, the eyes close for 16 of every 256 frames.
- **Falling out** (y 232 or lower): the player disappears and one life is taken. 60 frames
  later the picture fades out, and the section starts again from its beginning with the same
  fade-in. The music plays on without a break.
- **Exit**: an invisible box stands at the right end of the last table. Touching it while on the
  ground makes the player walk right by itself and off the screen; then the picture fades out
  as in step 05.
- The level code of the original has no check for Chip or Dale. Whether Dale moves differently
  will be measured in the next step.

One odd detail is reproduced: the game runs the player once at `lt = -1`, before the fade-in,
with the buttons it read last. At the level start that is nothing. After a fall it is whatever
was held on the 21st frame after the 60-frame wait, so holding LEFT there makes the player
start 2 pixels further left.

## Buttons

| Key | NES | Action |
|---|---|---|
| Left / Right | LEFT / RIGHT | walk |
| Down | DOWN | crouch |
| X | A | jump; with Down on a thin platform: drop through |

## Assets

| File | Size | Sub-images |
|---|---|---|
| `spr_chip_strip434.png` | 8x8 | 31 tiles × 2 directions × 7 brightness steps: index = (tile × 2 + (0 right, 1 left)) × 7 + step |
| `snd_land.ogg` | 6 frames (0.1 s) | the landing sound |

The brightness steps are the same as the background's: 0–2 fade-in, 3 normal, 4–6 fade-out.
The player's 7 pictures (standing, 3 walking, crouching, in the air, eyes closed) are put
together from these tiles by the tables at the end of `obj_player_Create.gml`.

The assets of step 05 are still needed.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprite `spr_chip`**: load `spr_chip_strip434.png`. Untick **Remove Background** and
   **Smooth Edges**, origin 0,0. It must have 434 sub-images of 8x8; if not, use *Edit Sprite →
   File → Create from Strip* (434 images, 8 wide, 8 high, 434 per row).
2. **Sound `snd_land`**: mono, 48000 Hz, not streamed.
3. **Scripts**: create `scr_pl_row`, `scr_pl_floor`, `scr_pl_wall` and `scr_pl_move_y` with the
   code from the files of the same names.
4. **Object `obj_player`** (new): no sprite. Add three events:
   - **Create** ← `gml/obj_player_Create.gml`
   - **Other → User Defined 0** ← `gml/obj_player_User0.gml`
   - **Draw** ← `gml/obj_player_Draw.gml`

   It has no Step event, and it is not placed in the room; `obj_stage1` creates it.
5. **Object `obj_stage1`**: replace its three events with `gml/obj_stage1_Create.gml`,
   `gml/obj_stage1_EndStep.gml` (still **Step → End Step**) and `gml/obj_stage1_Draw.gml`.
6. `obj_intro` stays as it is in step 05.

### How the objects work together

`obj_player` is a real object with its own variables and its own Draw event, but `obj_stage1`
decides when it runs: once per frame, in its End Step event, it gives the player the buttons
(`p_pad`, `p_pressed`), runs the player's User Defined 0 event, and then reads what happened
(`p_landed`, `p_out`, `p_restart`). GameMaker does not promise an order between the Step events
of different objects, and this keeps the order fixed. Enemies will be run the same way.

The player's position is a screen position, as on the NES; `lv_cam_x` of the stage is added
when the block map is looked at. The block map is in `lv_map` in the stage's Create event: 15
strings of 128 digits, one digit per 16x16 block (0 nothing, 1 can be stood on, 2 solid).

Both Draw events show the state the previous frame left behind, because the NES picture is one
frame behind its game. `obj_player` has depth -10 so it is drawn after the background.

The `TODO`s in the End Step event mark the kitchen (section 1e) and the game over when the
lives run out (section 1f); for now the section just restarts every time.

## How it was checked

`tools/capture/sim_player.py` is a Python port of `obj_player` and `obj_stage1`. It was run
with the same button inputs as 12 emulator recordings: scripted moves at the start, falls into
the first pit (four of them with buttons held around the restart), three runs of random
buttons through the section, and three different ways out of the last screen.

On all 5,345 compared frames:

- Player memory: state, x, y, y speed, picture, direction, height, camera and lives are the
  same as in the NES memory. 0 differences.
- Sprite tiles: every tile the port draws is in the NES sprite list at the same place. 0
  differences.
- Picture: 0 differing pixels, outside the places listed below.
- Landing sound: on every landing where the NES plays it, the port starts it on the same frame.

What that leaves out, and what was not checked:

- The GML has not been run in GameMaker; only the Python port has.
- The random-button runs stop being compared when the original player touches an enemy or
  picks up a crate, since those do not exist here yet. That is why most frames come from the
  first screens and the last one; the middle of the section is covered less.
- In the picture check, pixels under the original's other sprites (enemies, hearts) and crate
  spots that changed in the recording are skipped.
- In the three exit runs the port starts from the NES memory on the last screen instead of
  from the level start.
- From camera position 140 on, something in the original (most likely the first enemy) keeps
  repeating a sound on the same channel the landing sound uses, and the landing sound is then
  not heard. 13 of the 55 landings in the recordings were like that. The port plays the landing
  sound on every landing, so there it is heard where the original is silent. This belongs to
  the enemy step.
- The sounds were compared through the sound driver's register writes, not by ear.
- The eyes-closed picture was only seen facing left in the recordings; the right-facing one is
  its mirror image.
- Losing the last life was not recorded.
- Dale was not looked at.

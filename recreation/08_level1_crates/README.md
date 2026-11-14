# Step 08 – level 1, section 1: crates and bonus boxes

The player can now pick up the crates of the dining room, carry them, hide under them and throw
them, and collect the bonus boxes.

1. map and camera (step 05)
2. player movement (steps 06 and 07)
3. **crates and bonus boxes (this step)**
4. enemies, health, death, heart display

There are still no enemies, so a thrown crate has nothing to hit: it flies until it leaves the
screen.

## What was confirmed in the original

- **The section has 27 plain crates, 7 crates with a bonus box inside, and 19 bonus boxes.**
  Crates are solid and can be stood on. Bonus boxes are not solid.
- **Picking up**: stand on the ground, walk against the crate and press B. B must go down while
  the direction is already held. The crate is on the head at once. Nothing happens in the air,
  while crouching, while a throw is going on, or when a crate is already carried.
- Where the crate stood, the background appears one frame later. A crate with a bonus leaves a
  bonus box in its place.
- **Carrying**: the player walks and jumps as before, with other pictures. The body height stays
  22; the crate sits above it.
- **Hiding**: DOWN while carrying. The crate comes down over the player in 5 frames (the player
  is not drawn from the 2nd frame on), then bobs a little and rests on the ground.
- **Throwing** (B while carrying; 15 frames, the player stands still during them):
  - straight ahead: 4 pixels per frame;
  - UP + B: straight up, 6 pixels per frame;
  - UP + LEFT or RIGHT + B: diagonally, 4 pixels each way per frame;
  - **far throw**: after walking 30 frames without a stop on the ground. The crate flashes while
    it is carried from then on, and when thrown it flies 4 pixels per frame in a slight wave and
    has its own sound.
  
  A crate is gone when its middle leaves the screen left or right, or when it is far above it.
- **Bonus boxes**: touching one removes it and counts it (up to 99). One box per frame.
- **Falling out while carrying**: the crate flies straight up, without a sound. When the section
  restarts, all crates and boxes are back; the bonus count stays.
- **UP and DOWN held together** count as neither. (Not possible on a real controller, but on a
  keyboard.)
- **Draw order**: the original lists its sprites forwards on one frame and backwards on the
  next. The player is in front of the crate on one frame and behind it on the next. It shows in
  the one pixel row the head and the carried crate share.
- **Sounds**: only one sound effect plays at a time. A new one stops the one before it 1 frame
  after its cause and starts 2 frames after its cause. So a bonus box collected during a throw
  or pick-up sound cuts that sound off, and a throw or pick-up during the bonus sound cuts the
  bonus sound off.
  - The **landing sound is the exception**: it never stops another effect, and it is left out
    when a pick-up, throw, far-throw or bonus sound is playing or about to start. Landing on a
    bonus box therefore gives the bonus sound only.
  - Lengths in frames: pick-up 14, throw 25, bonus 53, landing 6, far throw 73.
  - All but the far throw use the music's second square channel; the music's part is silent
    while they play. The far-throw sound is noise only and leaves the music alone.
- Dale: same behaviour on the same frames, own pictures.

## Buttons

| Key | NES | Action |
|---|---|---|
| Left / Right | LEFT / RIGHT | walk |
| Down | DOWN | crouch; with a crate: hide under it |
| X | A | jump; with Down on a thin platform: drop through |
| Z | B | against a crate: pick it up; with a crate: throw it |
| Up | UP | with Z: throw upwards |

## Assets

| File | Size | Sub-images |
|---|---|---|
| `spr_chip_strip728.png` | 8x8 | 52 tiles × 2 directions × 7 brightness steps: index = (tile × 2 + (0 right, 1 left)) × 7 + step |
| `spr_dale_strip714.png` | 8x8 | 51 tiles, same layout |
| `spr_crate_strip14.png` | 16x16 | (0 normal, 1 flash) × 7 + brightness step |
| `snd_pick.ogg` | 14 frames (0.23 s) | picking up a crate |
| `snd_throw.ogg` | 25 frames (0.42 s) | throw |
| `snd_throw_far.ogg` | 73 frames (1.22 s) | far throw |
| `snd_bonus.ogg` | 53 frames (0.88 s) | bonus box: a short click, then a high note that fades out |

The two player strips **replace** the ones of steps 06 and 07; the tile numbers changed. The
player now has 14 pictures: the 7 old ones, 5 with a crate (standing, 3 walking, in the air) and
2 throwing.

The assets of step 05 and `snd_land` of step 06 are still needed.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprites `spr_chip`, `spr_dale`**: load the new strips into the existing sprites (728 and
   714 sub-images of 8x8, origin 0,0, **Remove Background** and **Smooth Edges** unticked).
2. **Sprite `spr_crate`** (new): `spr_crate_strip14.png`, 14 sub-images of 16x16, origin 0,0,
   same two boxes unticked.
3. **Sounds** (new) `snd_pick`, `snd_throw`, `snd_throw_far`, `snd_bonus`: mono, 48000 Hz, not
   streamed.
4. **Scripts**:
   - replace `scr_pl_row` and `scr_pl_wall`;
   - new: `scr_pl_touch`, `scr_pl_pick`, `scr_pl_throw`, `scr_pl_open_box`;
   - `scr_pl_floor` and `scr_pl_move_y` stay as they are.
5. **Object `obj_crate`** (new): no sprite, not placed in the room. Three events:
   - **Create** ← `gml/obj_crate_Create.gml`
   - **Other → User Defined 0** ← `gml/obj_crate_User0.gml`
   - **Other → User Defined 1** ← `gml/obj_crate_User1.gml`
6. **Object `obj_player`**:
   - **Create** ← `gml/obj_player_Create.gml`
   - **User Defined 0** ← `gml/obj_player_User0.gml`
   - **delete the Draw event**; add **Other → User Defined 1** ← `gml/obj_player_User1.gml`
7. **Object `obj_stage1`**: replace Create, End Step and Draw, and add
   **Other → User Defined 0** ← `gml/obj_stage1_User0.gml`.
8. `obj_intro` stays as it is.

### What changed in the code

- **Drawing moved into `obj_stage1`'s Draw event.** It draws the background, then the patches
  where boxes are gone, then the player and the crates through their User Defined 1 events, in
  the order of the frame. That is why `obj_player` has no Draw event any more.
- **The block table is now an array.** `lv_map` (the 15 strings) is still in the Create event,
  but User Defined 0 copies it into `lv_kind[row, column]`, which can change. `lv_box[row,
  column]` says what is in a block: 0 nothing, 1 crate, 2 crate with a bonus, 3 bonus box. User
  Defined 0 runs at the start and at every restart.
- **A crate nobody has touched is not an object.** It is part of the background picture and of
  the two tables. When it is picked up, `scr_pl_pick` clears the block and creates an
  `obj_crate`. `obj_stage1` keeps the crate objects in `lv_cr[0 .. lv_cr_n - 1]`, runs the
  thrown ones after the player, and destroys them when they are gone.
- **Patches**: for each of the 53 boxes the table in the Create event (`lv_bdc`, `lv_bdr`) names
  another block of the background picture that looks like what is behind the box. The Draw
  event copies that block over it.
- **Sounds**: `lv_land_n` is replaced by `lv_fx_*` (one waiting sound effect, one playing).
- New player variables are in the "crates" part of `obj_player_Create.gml`.

`lv_bonus` is only counted. Where the game shows or uses it comes later.

## How it was checked

`tools/capture/sim_crates.py` is a Python port of this step's GML. It was run with the same
buttons as 31 new emulator recordings (25 with Chip, 6 with Dale): carrying and throwing the
first crates in every direction, far throws, a run along the floor, the bonus boxes, falling
into a pit with a crate, seven runs of random buttons, and twelve short runs for the order of
the sounds (a bonus box just before, during and after a landing, a throw and a pick-up; a
landing during the far-throw sound).

On all 24,415 compared frames:

- Memory: the player's state, position, speed, picture, direction, height, the camera, lives,
  whether a crate is carried, the position of every crate object, all 53 box blocks and the
  bonus count are the same as in the NES memory. 0 differences.
- Sprite tiles of the player and the crates, including their order: 0 differences.
- Picture: 0 differing pixels, outside the other sprites of the original (hearts, enemies).
- Sounds: every pick-up, throw, far-throw, bonus and landing sound the port starts, starts on
  the same frame in the original, and the original starts no others (see the exception below).
  The long note of the bonus sound and the noise of the far throw are on and off on the same
  frames as in the original, so sounds that cut each other off are covered too.

The 21 recordings of steps 06 and 07 were run through the new port as well: 10,120 frames, 0
differences.

What that leaves out, and what was not checked:

- The GML has not been run in GameMaker; only the Python port has.
- **A thrown crate hitting an enemy** is not in this step. A recording is compared until the
  player touches an enemy; when a crate hits one in the original, that crate is left out from
  there on.
- **A thrown crate and walls**: in the recordings no crate flew into a solid block in a way
  that showed whether it stops. The port lets it fly through.
- Whether a crate can be put down without throwing it was not found; none of the tried button
  combinations did it.
- The repeating sound that starts with the first enemy (see step 06) also silences bonus
  sounds: 14 of the 44 bonus sounds and 26 of the 200 landings in the new recordings. The port
  plays them every time. This belongs to the enemy step.
- The repeating sound also cuts a bonus sound off after 2 or 4 frames when it starts just
  after it. In the port the bonus sound plays in full there.
- The sounds were compared through the sound driver's register writes, not by ear. The lengths
  in frames come from those writes too.
- One of Chip's pictures was only seen facing left; the right-facing one is its mirror image.
- What the bonus count does (display, extra life) was not looked at.
- Two-player rules (carrying the other player, and so on) are not part of the recreation yet.
- Losing the last life was not recorded.

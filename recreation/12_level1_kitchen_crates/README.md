# Step 12 – level 1, section 2: the kitchen's crates, bonus boxes, the acorn and the star

The kitchen now has its crates, its bonus boxes, the crate with the acorn inside, and the star
that gives a life. Second of the kitchen's three steps (step 11: map, camera, player, exit;
step 13: the mice). One player.

This step also corrects three rules of the player and the crates that hold in the dining room
too (see "Corrections to earlier steps").

## What was confirmed in the original

- **Boxes.** The kitchen has 18 plain crates, 6 crates with a bonus box inside, 29 bonus boxes
  and 2 crates with an item inside (columns 44 and 92 of the lower floor, third block above
  the floor). They behave as in the dining room (step 08): picked up with B, carried, thrown,
  hidden under; bonus boxes are collected by touching them.
- **What is behind a box.** The ROM holds every screen of the kitchen twice: with the boxes and
  without. The background that appears where a box was is taken from the second copy.
- **The acorn.** Picking up one of the two item crates leaves an acorn where the crate was
  (its middle 8 pixels right of the block's left edge, standing on the block's bottom line).
  Touching it gives one heart and it is gone. It makes no sound. It lies there as long as it is
  on the screen.
- **The star.** It lies on the high shelf at the right end of the upper floor (x 2000, y 64).
  Touching it gives one life and plays a sound (32 frames, on the music's 2nd square channel,
  starting 2 frames after the touch like the other effects). The star turns into the sign
  "1UP", 17 pixels higher; the sign rises 1 pixel on every 4th frame, 15 times, and is gone 85
  frames after the touch.
- **Camera going up.** Crates and items on the screen move down with the picture. The camera
  does not start to rise on the very frame on which it arrives under the shaft.
- **Frame count.** The count behind the crate's flashing and the order of the sprites loses 3
  frames at the change from the dining room to the kitchen.

## Corrections to earlier steps

Found with the kitchen's recordings; they hold in the dining room as well, and all recordings
of steps 06–10 still compare without a difference.

- **Throw direction (step 08).** LEFT or RIGHT held on the frame of the throw decides where the
  crate flies, even if the player has not turned yet. Only with neither held does it fly the
  way the player faces.
- **Throwing out of the hiding place (step 08, "Hiding").** Fully hidden under the crate, with
  LEFT or RIGHT held and DOWN let go: the crate leaves along the floor, and the player is set
  13 pixels back from it (RIGHT: 13 to the left; LEFT: 13 to the right), through whatever is
  there, and takes no step on that frame. With B alone or UP + B, or when not yet fully
  hidden, nothing is shifted.
- **Standing up from under a crate.** On the frame on which the player comes out, the walls are
  already tested with the full body height (22).

## Not in this step

- **The mice** and the other enemies of the kitchen: step 13. That includes a thrown crate
  hitting a mouse.
- **The way up to the star.** No sequence of buttons that reaches the shelf was found without
  the mice in the port. The star's rules were therefore measured in a recording in which the
  player was put next to the star by writing his position into the game's memory; from there
  on the game ran untouched. How the player gets up there is open.
- **Not measured when this step was written, measured since** (see step 13, whose files replace
  this step's):
  - The reach of the acorn and the star: sideways the two half widths (acorn 10, star 12), up
    the item's height (10, 12), down the player's body height (22).
  - The acorn at 3 hearts is taken and gives nothing (as here).
  - The most lives are 10, shown as 9 (here: 9; corrected in step 13).
  - The bonus count stops at 99 and is paid out at the end of the level.
  - A thrown crate flies through walls and crates (as here).
- **Differences left as they are:** the two of step 11 (the half-replaced row in the shaft;
  the player shown facing left once more when the exit takes him over from the right, 1 frame
  of the comparison).
- Sprites per line and dropped frames as in step 09.

## Assets

All new. Origin 0,0 everywhere.

| File | Size | Sub-images |
|---|---|---|
| `sprites/spr_item_strip7.png` | 16x16 | the acorn, 7 brightness steps |
| `sprites/spr_lifestar_strip7.png` | 16x16 | the star that gives a life, 7 brightness steps |
| `sprites/spr_1up_strip7.png` | 16x8 | the sign "1UP", 7 brightness steps |
| `sounds/snd_extra_life.ogg` | 0.567 s | the sound of the star (34 frames) |

Brightness steps as before: 0–2 fade-in, 3 normal, 4–6 fade-out. All assets of steps 01 to 11
are still needed and unchanged.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprites** (new): `spr_item`, `spr_lifestar`, `spr_1up`, 7 sub-images each. Origin 0,0,
   **Remove Background** and **Smooth Edges** unticked. (`spr_star` of step 10 stays: it is the
   star over a stunned player.)
2. **Sound** (new): `snd_extra_life`, settings as the other effects.
3. **Object `obj_item`** (new): no sprite, not visible. Events Create, User Defined 0 and User
   Defined 1 from `obj_item_Create.gml`, `obj_item_User0.gml`, `obj_item_User1.gml`.
4. **Scripts**: replace `scr_pl_pick`, `scr_pl_throw`, `scr_pl_enemy_touch`.
5. **Object `obj_player`**: replace Create and User Defined 0.
6. **Object `obj_stage1`**: replace Create, End Step, Draw, User Defined 0, User Defined 1 and
   User Defined 2.
7. Everything else is unchanged; the other files in `gml/` are the same as in step 11.

To get to the kitchen quickly while testing: in `obj_stage1` Create set `lv_sec = 1;`,
`lv_cam_y = 240; lv_cam_yshow = 240; lv_cam_yold = 240;` just before the `event_user(0);` near
the end.

### What changed in the code

- **`obj_stage1` Create**: the kitchen's box table (`lv_box2_n`, `lv_bc2`, `lv_br2`, `lv_bk2`,
  `lv_bdc2`, `lv_bdr2`, `lv_rbox2_c/r`; kind 4 = crate with the item) and its object list
  `lv_ob2_*` (the star and the exit).
- **User Defined 0**: fills `lv_box` from the table of the current section; removes items.
- **End Step**: the list of items `lv_it` (shown, removed, run in the order of the object
  list; place kind 5); the kitchen's objects enter like the dining room's; crates and items
  move down when the camera rises; the camera rule at the shaft; the frame count at the
  section change.
- **Draw**: the background pieces behind the kitchen's boxes (also while the shaft's picture is
  replaced row by row); items in the sprite order.
- **User Defined 1**: sound 14 (`snd_extra_life`).
- **`scr_pl_pick`**: kind 4 leaves the acorn. **`scr_pl_enemy_touch`**: items.
  **`scr_pl_throw`** and **`obj_player`**: the three corrections above (`p_kick`, `under`).

## How it was checked

`tools/capture/sim_kitchen2.py` is a Python port of this step's GML. It was run with the same
buttons as 29 emulator recordings: the 18 of step 11, 10 new runs through the kitchen that
pick up, carry, throw (ahead, up, diagonally, far, out of the hiding place), collect bonus
boxes and take the acorn, and the star recording described above. The new runs were found by a
search over savestates that keeps away from the mice; they are in
`tools/capture/kitchen_runs.json`.

Compared on every frame: the player's memory values, camera, lives, hearts, the bonus count,
which boxes are still on the map, every crate, piece, item and sign in the object list with
its position, the frames on which the sounds start (pick-up, throw, bonus, far throw, landing,
extra life), and the whole picture.

Left out of the comparison: the picture where the NES has sprites the port does not draw (the
mice); the landing sound for 60 frames after a sound of the mice; and a run is compared only up
to the frame on which a thrown crate meets a mouse (two runs end early for that reason).

| | frames | differences |
|---|---|---|
| Kitchen recordings (29) | 25,669 | 1 (the exit entered from the right, see step 11) |
| All recordings of steps 06–10 (`--old`) | 121,903 | 0 |
| Step 11's own check (`sim_kitchen.py`), unchanged | 9,377 | 1 (the same) |

The GML itself was not run: there is no GameMaker here. Please check in GameMaker in
particular: the background behind a box taken on the upper floor and in the shaft, the acorn
appearing when an item crate is lifted, and the throw out of the hiding place.

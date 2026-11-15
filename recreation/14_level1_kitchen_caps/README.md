# Step 14 – level 1, section 2: the bottle caps of the kitchen

The three bottles on the kitchen's last screens now have their caps: the way up to the star
that gives a life. This completes the kitchen (step 11: map, camera, player, exit; step 12:
crates, bonus boxes, acorn, star; step 13: the mice). One player.

## What was confirmed in the original

### Where they are

- The kitchen's object list has three objects of type `$08`: columns 99, 107 and 115 of the
  upper floor. Each cap sits in the middle of its column (x 1592, 1720, 1848 of the section), its
  line at y 96, on the neck of a bottle that is part of the background picture.
- A cap enters like an enemy, when its column is 264 pixels right of the camera, and takes a
  place in the object list. It is removed like an enemy when it leaves the picture, and enters
  again when the camera comes back (also a cap that had flown off).
- After a lost life the kitchen starts again with all three caps.

### What a cap is

- Solid for the player, from every side. Nothing else touches it: a thrown crate and a thrown
  mouse fly through it, and it does not hurt.
- It is 16 pixels wide. The player is "in" it when his middle is at most 14 pixels from the
  cap's middle (measured: lands at 14, falls past at 15, both sides) and his feet line is
  between the cap's height above its line and his own height (22, crouching 16) below it.

| picture | when | height above its line | the player stands at |
|---|---|---|---|
| 80 | on the bottle | 7 | y 88 |
| 81 | after the first landing | 4 | y 91 |
| 82 | after the second landing | 2 | y 93 |
| 83 | flying (16 pixels high) | 15 | cap y − 16 |

### Landing on it

- Falling: he is put on the cap as soon as his feet line, 1 pixel further down, is in it. The
  landing sound plays as on the ground.
- The cap looks at the player once per frame, after the player has moved. A landing counts
  when he stands on it now and did not at the cap's last look: he has to leave it (a small jump
  is enough) and come down again. Standing or walking on it does nothing.
- The frame after a landing the cap goes down a step (picture + 1) and takes the player with
  it. His picture follows one frame later than his position: for one frame he is drawn 3 (2)
  pixels above the cap.
- With the third landing the cap flies off: picture 83, the cap's sound, the player lifted to
  16 above the cap's line.

### The flight

- 1 pixel to the right every frame. Up at 4 pixels per frame (64 sixteenths), 3 sixteenths less
  each frame, until it falls at 5 pixels per frame. It goes through blocks and objects, leaves
  the picture at the bottom and is gone (about 72 frames after the start, 72 pixels further
  right).
- The player on it is put on its top **before** it moves, so he is one frame behind it. While
  it rises he is inside it and stays on; when it starts to sink by a whole pixel per frame it has
  left him and he falls. He falls faster than the cap, so he lands on it again further down
  (the landing sound each time; these landings change nothing).
- The cap does not carry him sideways: standing still he is 14 pixels off its middle after 14
  frames and drops off. To stay on he walks along (one step of 2 pixels every other frame).
- The level's way: land three times on the first cap, ride it up, jump to the second cap at the
  top of the flight, the same to the third, and from its flight onto the shelf with the star.

### From the side and from below

- Walking or jumping into its side: he stops 15 pixels from its middle.
- Rising into it with his feet line above the cap's line: he is put on top of it, standing.
- Rising into it lower than that: his head is stopped 1 pixel under the cap's line (his feet 23
  below it) and he falls from the next frame. A jump from the floor does not reach a cap on its
  bottle (measured with his height written into memory: 20 and 0 pixels below the line his head
  is stopped, 1 above he is put on the cap).
- A flying cap that comes down through a player on the floor lifts him for single frames (he
  is "in" it, his feet above its line, so he is put on top) and goes on.

### The sound

Sound `$4A`: 5 frames on the 2nd square channel, two short notes. Like the other effects it
stops the one before it and starts 2 frames after its cause.

## Corrections to step 13

- The caps no longer just hold places in the object list (place kind 6, `lv_cap_x`,
  `lv_cap_seen` are gone). A cap is an `obj_enemy` of kind 7 and holds its place like any enemy.
- `scr_pl_on_mouse` now asks `scr_pl_solid_at`, which knows stunned mice **and** caps, and
  remembers what he stands on (`p_on`). For the mice nothing changes.

## Not in this step

- **What no recording shows:**
  - A walking mouse and a flying cap in the same place. They go through each other in the
    recordings; nothing was seen that one does to the other.
  - Standing on a cap with a crate in his hands, and throwing from it. The port uses the same
    rules as on the ground.
  - A cap from the side while it flies (only caps on their bottles were walked into).
- On the frame a cap enters, the original has it up to 2 pixels off its place for one frame
  (it is not drawn on that frame). The port has it in its place at once.
- Sprites per line and dropped frames as in step 09; the half-replaced row in the shaft (step
  11).
- Two players, levels 2 and later.

## Assets

Origin 0,0 everywhere.

| File | Size | Sub-images |
|---|---|---|
| `sprites/spr_enemy_strip1680.png` | 8x8 | **replaces** `spr_enemy_strip1568.png` of step 13: the same 112 tiles, then 8 tiles of the cap. 120 tiles × 2 directions × 7 brightness steps: index = (tile × 2 + (0 left, 1 right)) × 7 + step |
| `sounds/snd_cap.ogg` | 0.083 s | the cap flies off (5 frames) |

All other assets of steps 01 to 13 are still needed and unchanged.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprite `spr_enemy`**: load `spr_enemy_strip1680.png` in place of the old strip (1680
   sub-images of 8x8, origin 0,0, **Remove Background** and **Smooth Edges** unticked).
2. **Sound** (new): `snd_cap`, settings as the other effects.
3. **Scripts, new**: `scr_en_cap`, `scr_pl_solid_at`.
4. **Scripts, replace**: `scr_pl_on_mouse`, `scr_lv_spawn2`, and (comments only) `scr_lv_spawn`,
   `scr_lv_take_slot`.
5. **Object `obj_enemy`**: replace Create (comments only) and User Defined 0.
6. **Object `obj_player`**: replace Create (two new variables, `p_on` and `p_late`) and User
   Defined 0.
7. **Object `obj_stage1`**: replace Create, End Step, User Defined 0 and User Defined 1.
8. Everything else is unchanged; the other files in `gml/` are the same as in step 13.

To get to the caps quickly: the test shortcut of step 12 (in `obj_stage1` Create, just before
the `event_user(0);` near the end: `lv_sec = 1; lv_cam_y = 240; lv_cam_yshow = 240;
lv_cam_yold = 240;`) starts in the kitchen; the caps are on its last two screens. Go up the
crates at the wall to the ledge on the left of the first bottle and jump onto the cap from
there.

### What changed in the code

- **`scr_en_cap`** (new): the whole cap; called by `obj_enemy` User Defined 0 for kind 7.
- **`scr_pl_solid_at`** (new): the solid thing the player is in. **`scr_pl_on_mouse`**: uses it
  and sets `p_on`.
- **`scr_lv_spawn2`**: list kind 17 creates an enemy of kind 7.
- **`obj_player` User Defined 0**: `p_on` cleared at the start; rising into a solid thing; the
  stop at a cap's side.
- **`obj_stage1` Create**: `en_cap_h`, the picture tables 80–83. **User Defined 0**: the cap
  places removed. **End Step**: place kind 6 removed; the player's shown height takes `p_late`.
  **User Defined 1**: sound 18.

## How it was checked

`tools/capture/sim_caps.py` is a Python port of this step's GML. It was run with the same
buttons as the emulator recordings of step 13 and 19 new ones (95 runs in all). Compared on every
frame: the player's memory (position, speed, state, hearts, picture), every place of the object
list (for a cap: position, speed, picture, height), the blocks, the sounds started, and the
picture (sprite tiles and pixels).

| recording | what it shows |
|---|---|
| `cp_pop` | three landings on the first cap; it flies off with the player, who stands still and drops off it |
| `cp_quick` | the same with the jumps pressed on the frame after each landing |
| `cp_ride` | walking along with the flying cap, dropping off and landing on it again on the way down; at the bottom the mouse with the spoon takes the last heart |
| `cp_ride16` | the same with fewer steps |
| `cp_half` | one landing, back to the ledge, down on the cap again, one jump |
| `cp_star` | the level's way: cap, cap, cap, the shelf, the star |
| `cp_side` | a jump from the first cap in its flight that comes down against the side of the second |
| `cp_reland` | off the second cap in its flight and on it twice more on the way down |
| `cp_under` | the player on the floor where the second cap comes down |
| `cp_again` | the first cap sent off, the last heart lost: the kitchen starts again and the cap is back |

With memory written in the middle of the run (the port gets the same value on the same frame):

| recording | written | what it shows |
|---|---|---|
| `cp_p_bump`, `cp_p_bump96` | the player's height during a jump under the first cap: 20 / 0 pixels below its line | his head is stopped under the cap |
| `cp_p_bump95` | 1 pixel above its line | he is put on the cap |
| `cp_p_edgel13` … `cp_p_edger15` (6) | his place during the fall onto the first cap: 13, 14, 15 pixels left / right of its middle | he lands on it at 13 and 14, falls past it at 15 |

Result: **149,750 frames compared, 0 with a difference**. The earlier runs of steps 06 to 10 with
`--old --nopic`: **121,903 frames, 0 with a difference**.

The tile `D5` (the caps) has left the list of NES sprites the port does not draw. What is left
in it: the mouse tiles in the 12 kitchen recordings that start in the middle of the kitchen
(checked without mice by `sim_kitchen2.py`), and the acorns written into memory to fill the
object list (step 13).

The cap's sound was recorded alone (written to `$F0` by hand, one channel at a time, like the
sounds of step 10) and cut from the 2nd square channel.

As in every step: the GML was written by hand from the Python port and has never been run in
GameMaker. If something behaves differently there, the GML has the mistake, not the rule.

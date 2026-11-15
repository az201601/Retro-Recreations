# Step 13 – level 1, section 2: the mice of the kitchen

The kitchen now has its two kinds of mice: the mouse with the spoon, and the mouse that hides
under a crate. Third of the kitchen's three steps (step 11: map, camera, player, exit; step 12:
crates, bonus boxes, acorn, star). One player.

**Not in this step: the bottle caps.** They are the way up to the star (thank you for the hint:
the three `$08` objects of the kitchen's list are the caps). They are a step of their own (step
14) and nothing of them is in this step's code; see "Not in this step".

## What was confirmed in the original

Speeds are in sixteenths of a pixel per frame. Gravity of the mice: 3 more per frame, up to 80.

- **Where they are.** The kitchen's object list has 5 mice with a spoon (columns 27, 58, 78, 94
  and 104), 5 mice under a crate, 3 bottle caps, the star and the exit. An object
  enters when the column 264 pixels right of the camera becomes its column. The first mouse
  under a crate (column 15) is there from the start. One mouse under a crate (column 91) enters
  from above while the camera climbs the shaft.
- **Mouse with the spoon.** 2 hits, body 8 to either side and 24 high. Walks 1 pixel a frame,
  32 pixels one way and 32 back (4 pictures of 8 steps); turns at once at a wall; falls where
  the floor ends. Touching it costs a heart.
- **The spoon.** A thrown crate that comes at its face, on its level and less than 64 pixels
  away, makes it stop and swing: 9 frames spoon back, 9 the swing, 9 + 9 after it (36 in all).
  A sound starts with the swing (19 frames, 2nd square channel). If the crate is less than 32
  pixels away at that moment, it flies back the way it came. A crate that flies back and
  touches the player breaks; the player is stunned (as by the flyer's load, step 10) and pushed
  half a pixel a frame the way the crate flew. No heart is lost.
- **Stunning it.** A crate that does reach it (from behind, from above, or too late for the
  spoon) breaks and stuns it: it is thrown back 1 pixel a frame with a small hop (up speed 48),
  lands on its back and lies for 600 frames. A sound plays (58 frames, 2nd square channel). A
  star goes round over it, 2 pixels higher than the player's star. From frame 482 of the 600 it
  flickers (2 frames hidden, 2 shown); then it stands up, as new. While stunned it does not
  hurt.
- **Standing on it.** A stunned mouse carries the player like a block. When his middle is 14
  pixels or less from the mouse's (15: not) and his feet line is anywhere from 25 above the
  mouse's down to less than his own body height below it (21 below standing: yes, 22: no; 15
  and 16 crouching), he is put on top of it, 25 above its feet line: a fall ends there with
  the landing sound, he can walk, crouch and jump on it, and he falls off once his middle is 15
  away. This holds while the mouse is still in the air from the hit, too, and for a player
  who is stunned or has just been hurt. A player inside the mouse (below its top) is put on
  top at once, also while rising. When the mouse gets up under him he is hurt like by any
  touch.
- **Pushing, carrying, throwing.** The player walking into a stunned mouse from the side pushes
  it along at 1 pixel a frame, to the right and to the left. A wall or a crate stops the mouse
  (its edge next to the block); the player then stands 15 pixels from it. With B pressed on such a frame it is picked up like a crate (same sound): it
  sits upside down on the head, looking the other way, and its star goes round at the height of
  its head. B again throws it: straight ahead only, 4 pixels a frame, with the throw sound. It
  leaves from where the player stands after that frame's step. Crouching with a mouse on the
  head does nothing (no hiding).
- **A thrown mouse** flies through walls and crates until it leaves the screen, and is gone
  with its star. Every mouse it meets is knocked out at once, also a mouse with a spoon that
  has not been stunned (it is shown on its back); the thrown mouse flies on. It counts as met
  when the two are 16 pixels or less apart sideways and the thrown mouse's feet line is at
  most 24 below the other's and at most the other's body height above it (thrown 15 above the
  mouse under the crate: met, 16: not; 24 below the mouse with the spoon: met, 25: not).
  The spoon does not answer a thrown mouse, even one that comes at its face from 60 pixels
  away.
- **A crate of a far throw** (after a run-up) makes the mouse swing its spoon like any crate,
  but is not turned back by it. It knocks the mouse with the spoon out at once, stunned or
  not, and flies on.
- **A carried mouse stays stunned** for as long as it is carried: carried 650 frames, it had
  not woken and did not flicker.
- **Hurt while carrying.** Losing a heart does not make the player drop the mouse. Losing the
  last heart does: the mouse and its star are gone on that frame, with the throw sound.
- **A second crate** on a stunned mouse knocks it out like any enemy (flung away up and
  sideways, the knock-out sound of step 09); its star stays with it until it is off the screen.
  A crate flying left flings it to the left, the mirror image of the other way.
- **A thrown crate and the blocks.** A crate thrown level flies through walls and through other
  crates; only an enemy or leaving the screen ends its flight. (The crate that
  "turned at the wall" in an earlier test had been batted back by a mouse's spoon.)
- **Stunned with a mouse on the head.** It cannot come about by playing: only a crate that was
  batted back stuns the player here, and no crate can be thrown with a mouse on the head. With
  the player's state forced by a memory write: the mouse stays on the head, the player gets
  his star for as long as he is stunned, and the mouse can be thrown afterwards. The port does the same.
- **Acorn, star, lives, bonus count** (open since step 12):
  - The acorn at 3 hearts is taken and gives nothing.
  - The star gives a life up to 10 (the status screen shows one less: 9). At 10 it is still
    taken, with its sound and its sign.
  - The star's gift comes one frame after the touch.
  - Reach: sideways the two half widths; the player's feet line may be above the item's line
    by the item's height, and below it by his own body height. Star: 12 to either side (13:
    not), the player 12 above it (13: not) to 22 below it (23: not). Acorn: 10 to either side
    (11: not), the player 10 above it (11: not); below it the same rule is used.
  - The bonus count stops at 99; a box taken after that still makes its sound. In the kitchen
    the count does nothing else. It is paid out at the end of the level (routine at `$F60A` of
    the fixed bank); that belongs to the step with the level's end.
- **A full object list** (all 9 places taken; only with memory writes, the kitchen's own
  objects never fill more than a few). While it is full the original also runs slower:
  - Picking up a crate: the block is gone, no crate, no sound, nothing carried.
  - The crate with the acorn: with one free place the acorn appears and no crate; with none,
    neither.
  - A crate stuns a mouse: stunned as usual, without a star.
  - The player stunned: no star, and none later when a place comes free.
  - A mouse whose column comes up on that frame never appears. There is one try, on the frame
    the camera reaches its column.
- **Mouse under a crate.** 1 hit; looks like a crate (16 wide, 15 high) and does hurt when
  touched. When the player is on its level and less than 80 pixels away, it gets up (4 pictures
  over 24 frames, a sound of 12 frames on the 2nd square and the noise channel), hops, and
  walks towards where the player was, 1 pixel a frame. At a wall or at the end of the floor it
  jumps (up speed 64) and walks on where it lands. One crate knocks it out.
- **Two floors.** For the mice the original keeps only 15 rows of blocks: each row is that of
  the lower floor while the camera is low enough, else that of the upper floor. A mouse that
  the camera has left behind on the other floor therefore finds the wrong floor's blocks. The
  port does the same (`scr_lv_block`).
- **Camera going up.** Mice on the screen move down with the picture like crates and items; a
  mouse is removed when it was below line 237 before the camera moved.
- **Object list.** A stunned mouse's star and the bottle caps take places in the list like
  everything else. Since the list decides the order in which things act and are drawn, the caps
  take their places in this step already, without being shown.

## Corrections to steps 11 and 12

- **The life star coming in from the right (step 12).** Its left half is shown as soon as that
  half is on the screen, 4 frames before its middle is. The acorn follows the same rule here.
- **Entering the exit from the right.** On the frame on which the exit takes the player over,
  the picture still shows the player looking the way he walked. This was the one differing
  frame of steps 11 and 12; it is gone.

## Not in this step

- **The bottle caps** (columns 99, 107 and 115 of the upper floor, y 96). Seen so far: the
  player can stand on a cap; each landing on it changes its picture; the third landing makes it
  fly off (its own sound) and throws the player up, which is how the star's shelf is reached.
  None of this is in the port: the caps are not drawn and cannot be stood on. Proposal: step 14.
- **Not measured: nothing that this step contains.** The rules that cannot be reached by
  playing are now recorded too, with memory written in the middle of a run, and the Python port
  is checked against those recordings like against the others (the table below).
- **What no recording can show:**
  - The acorn's reach downwards. The kitchen's one acorn lies 6 pixels above the bottom line,
    and a player 22 below it would be off the screen and lost. The port uses the star's rule.
  - A stunned player sliding sideways (after a real crate from the spoon) onto a stunned mouse.
    The recording has him stunned by a memory write straight above the mouse: he lands on it.
- **Differences left as they are:**
  - The half-replaced row in the shaft (step 11).
- Sprites per line and dropped frames as in step 09.

## Assets

Origin 0,0 everywhere.

| File | Size | Sub-images |
|---|---|---|
| `sprites/spr_enemy_strip1568.png` | 8x8 | **replaces** `spr_enemy_strip840.png` of step 09: the same 60 tiles, then 52 tiles of the mice. 112 tiles × 2 directions × 7 brightness steps: index = (tile × 2 + (0 left, 1 right)) × 7 + step |
| `sounds/snd_mouse_stun.ogg` | 0.967 s | a crate stuns the mouse (58 frames) |
| `sounds/snd_mouse_swat.ogg` | 0.317 s | the swing of the spoon (19 frames) |
| `sounds/snd_mouse_wake.ogg` | 0.200 s | the mouse under the crate gets up (12 frames) |

The mice use the kitchen's sprite colours, which are the dining room's. With Dale the tiles are
the same. All other assets of steps 01 to 12 are still needed and unchanged.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprite `spr_enemy`**: load `spr_enemy_strip1568.png` in place of the old strip (1568
   sub-images of 8x8, origin 0,0, **Remove Background** and **Smooth Edges** unticked).
2. **Sounds** (new): `snd_mouse_stun`, `snd_mouse_swat`, `snd_mouse_wake`, settings as the other
   effects.
3. **Scripts, new**: `scr_en_mouse`, `scr_en_cmouse`, `scr_en_air`, `scr_en_crate_ahead`,
   `scr_en_next_pic`, `scr_lv_spawn2`, `scr_pl_on_mouse`.
4. **Scripts, replace**: `scr_lv_block`, `scr_lv_spawn` and `scr_lv_take_slot` (comments only),
   `scr_en_row`, `scr_en_floor`, `scr_en_ceiling`, `scr_en_wall`, `scr_en_near_player` (comment
   only), `scr_pl_throw`, `scr_pl_enemy_touch`, `scr_pl_floor`, `scr_pl_pick`.
5. **Object `obj_enemy`**: replace Create, User Defined 0 and User Defined 1; add **User
   Defined 2** from `obj_enemy_User2.gml`.
6. **Object `obj_crate`**: replace Create (one new variable, `c_back`) and User Defined 0
   (comment only). **Object `obj_item`**: replace Create (one new variable, `i_hit`).
7. **Object `obj_player`**: replace Create and User Defined 0.
8. **Object `obj_stage1`**: replace Create, End Step, Draw, User Defined 0 and User Defined 1.
9. Everything else is unchanged; the other files in `gml/` are the same as in step 12.

The test shortcut of step 12 still works (in `obj_stage1` Create, just before the
`event_user(0);` near the end: `lv_sec = 1; lv_cam_y = 240; lv_cam_yshow = 240;
lv_cam_yold = 240;`). The first mouse with a spoon is one screen to the right; the first crates
to throw at it are on the way.

### What changed in the code

- **`obj_stage1` Create**: the kitchen's whole object list `lv_ob2_*` (rows now count 0–29), the
  list of what enters in the shaft `lv_ob2v_*`, `lv_dy`, `en_cwalk`, and the picture tables of
  the mice (`en_tn`, `en_tdx`, `en_tdy`, `en_tim` for pictures 0–6, 15–21 and 76).
- **User Defined 0**: the kitchen's first screen gets its objects; bottle cap places.
- **End Step**: objects enter through `scr_lv_spawn2`; the shaft's entry from above; enemies
  move down with the picture; place kind 6 (bottle cap); what an enemy shows is now set by
  `obj_enemy` User Defined 2; the player's direction on the exit frame (`p_face_was`).
- **Draw**: the stars of stunned mice in the sprite order.
- **User Defined 1**: sounds 15, 16, 17.
- **`obj_enemy`**: kinds 5 and 6 (`scr_en_mouse`, `scr_en_cmouse`); the first hit on kind 5 only
  stuns; the star's place; upside-down drawing; flicker; the variables `c_hot`, `c_dir`, `c_snd`
  so that `obj_player.p_carry` can hold a mouse.
- **`obj_player` User Defined 0**: pushing and picking up a stunned mouse; no crouching under
  it; carrying it. **`scr_pl_throw`**: a mouse. **`scr_pl_enemy_touch`**: the crate that was
  batted back.
- **`scr_en_row` / `floor` / `ceiling` / `wall`, `scr_lv_block`**: the kitchen's camera height
  and its two floors.

Added after the first version of this step (all of it is in the files above; if you have not
transferred step 13 yet, there is nothing extra to do):

- **`scr_pl_on_mouse`** (new), **`scr_pl_floor`**, **`obj_player` User Defined 0** (jumping,
  falling, stunned, pushing): standing on a stunned mouse; a pushed mouse stops at a wall.
- **`scr_pl_enemy_touch`**, **`obj_item` Create**: 10 lives at most; the star has its own reach
  and gives its life one frame after the touch.
- **`scr_pl_pick`**, **`obj_stage1` End Step**, **`scr_en_mouse`**: the full object list (no
  crate, no item, no star).

## How it was checked

`tools/capture/sim_mice.py` is a Python port of this step's GML. It was run with the same
buttons as 78 emulator recordings: 17 kitchen recordings of steps 11 and 12, now compared to
their end with the mice (the 12 that start in the middle of the kitchen, where the mice cannot
be followed from their start, stay with `sim_kitchen2.py`); 10 of the step 11 runs recorded
again from before the kitchen; 21 of the first version of this step: touched by a mouse, a
crate batted back, a mouse stunned and left to get up, stunned and pushed, picked up and thrown
in four ways, knocked out with a second crate, the mouse under the crate waking, a mouse thrown
at a mouse under a crate and at a mouse with a spoon, a mouse carried for 650 frames, a heart
and the last heart lost with the mouse on the head, a mouse thrown at the face of a mouse with
a spoon, four throws 1 pixel inside and outside the limits of its reach up and down, and two
far throws of a crate at a mouse with a spoon; 10 added with the first follow-up; and 20 with
memory written in the middle of the run (second table):

| recording | what it shows |
|---|---|
| `mi_cleft` | a second crate from the right: the mouse is flung to the left |
| `mi_push` | a stunned mouse pushed to the right until it stands at a crate; the player walks off and into it again |
| `mi_push2` | onto the mouse, off it on the far side, pushed to the left until the player is at the left edge of the picture |
| `mi_mtop` | a jump onto the stunned mouse, walking along it and off it, pushing it left |
| `mi_mtop2` | a jump that comes down just beside it, pushing it while still in the air |
| `mi_mwake` | crouching and jumping on the mouse, then standing on it until it gets up (the last heart is lost) |
| `mi_cwall` | of two crates side by side the left one picked up and thrown along the ground: it flies through the right one |
| `mi_acorn3` | the acorn run of step 12 with 3 hearts written into memory: the acorn is taken, 3 hearts stay |
| `mi_lives10` | the star run of step 12 with 9 lives written into memory: 10 |
| `mi_lives11` | the same with 10 lives: 10 stay, sound and sign as usual |

With memory written during the run (`capture_mice.py` lists the writes; the port repeats each
one on the same frame):

| recording | written | what it shows |
|---|---|---|
| `mi_p_bonus99` | bonus count 98 | two boxes taken: 99, 99, the sound both times |
| `mi_p_star_r`, `_l`, `_u`, `_d` | the player's place | 3 frames 1 pixel outside the star's reach (13 right, 13 left, 13 above, 23 below): nothing; then 1 pixel inside: taken |
| `mi_p_acorn_s`, `_u` | the player's place | the same for the acorn: 11 to the side, 11 above; then 10 |
| `mi_p_inside` | the player's place | put inside a lying mouse on the ground: on top of it at once |
| `mi_p_rise` | the player's height | inside it while jumping up: on top, standing |
| `mi_p_air` | the player's place | on a mouse still in the air from the hit: carried up with it |
| `mi_p_cstun` | the player's state | stunned with a mouse on the head: it stays there and is thrown afterwards |
| `mi_p_stunfall` | state and place | stunned in the air above a stunned mouse: lands on it |
| `mi_p_hurtfall` | the player's state | hurt while standing on it: thrown up, comes down on it again |
| `mi_p_pushl` | places of mouse and player | pushed to the left against a crate: the mouse stops next to it, the player 15 away |
| `mi_p_fpick` | list filled | a crate picked up: block gone, nothing carried, no sound |
| `mi_p_fitem0`, `mi_p_fitem1` | list filled / one place left | the crate with the acorn: nothing at all / the acorn and no crate |
| `mi_p_fstar` | list filled | a mouse stunned without a star; none when places come free; it gets up as usual |
| `mi_p_fplstar` | list filled | the player stunned without a star |
| `mi_p_fspawn` | list filled | the mouse of column 78 never appears |

`mi_lives10`, `mi_lives11` and the four star recordings start in the middle of the kitchen; the
one mouse that walks below the star's shelf in them is not followed (and its sprite is left out
of the picture comparison). Not compared either: the picture on a frame on which a place was
written (the NES shows it one frame later), and on the one frame on which the acorns that
fill the list make the NES run out of its 64 sprites.

Compared on every frame: everything step 12 compared, and every mouse, star of a mouse and
bottle cap in the object list with its place, position, picture and direction; the frames on
which the three new sounds start; and the whole picture.

Left out of the comparison: the picture where the NES has a sprite the port does not draw.
The check counts which sprites those are: the bottle caps, the mouse of the star recordings,
and the acorns that fill the object list.

| | frames | differences |
|---|---|---|
| Kitchen recordings (78) | 93,451 | 0 |
| All recordings of steps 06–10 (`--old --nopic`) | 121,903 | 0 |

The GML itself was not run: there is no GameMaker here, and the GML was written from the
Python port by hand. Please check in GameMaker in particular: the mouse carried upside down
(`draw_sprite_ext` with a negative y scale in `obj_enemy` User Defined 1), the star over a
stunned mouse, and the crate that comes back from the spoon.

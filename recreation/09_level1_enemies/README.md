# Step 09 – level 1, section 1: enemies

The enemies of the dining room now appear, move, make their sounds and can be knocked out with
a crate.

1. map and camera (step 05)
2. player movement (steps 06 and 07)
3. crates and bonus boxes (step 08)
4. **enemies (this step)**
5. health, death, heart display (next step)

**The enemies cannot hurt the player yet.** The player walks through them. That, the hearts,
lives and game over are step 10.

## What was confirmed in the original

- **The section has 11 enemies and the exit in one list**: 6 flyers and 5 cooks. Each one enters
  when the camera is 264 pixels left of it.

  | x | y | what |   | x | y | what |
  |---|---|---|---|---|---|---|
  | 384 | 32 | flyer | | 1376 | 96 | flyer |
  | 512 | 160 | cook | | 1568 | 64 | flyer |
  | 640 | 64 | flyer | | 1728 | 80 | cook |
  | 816 | 192 | cook | | 1904 | 32 | flyer |
  | 1088 | 32 | flyer | | 1936 | 192 | cook |
  | 1248 | 80 | cook | | 2016 | 160 | exit |

- **Flyer** (body 16 wide, 16 high). It turns towards the player once, then repeats: 48 frames
  flying (1 pixel sideways and 1/4 pixel down per frame), 48 frames on the spot. After 32 of
  those 48 frames it drops something. On the next flight it goes up instead of down, and so on.
  It never turns round. Two pictures while flying (3 frames each), four while on the spot (4
  frames each).
- **What it drops** (4 wide, 4 high) starts 8 pixels below the flyer and falls faster and
  faster (3/16 pixel per frame more), up to 5 pixels per frame.
- **Cook** (16 wide, 24 high). Walks 32 pixels one way and 32 back, 1 pixel per frame. When the
  player is on its level and less than 80 pixels away, it turns to the player, stops for 68
  frames and throws a **fork** on the 34th. After that it walks on in that direction and jumps
  at walls and at the end of the ground.
- **Fork** (16 wide, 4 high): starts 16 pixels up and 19 pixels ahead of the cook, flies 3
  pixels per frame.
- An enemy is removed when its middle leaves the screen left or right, or when it is below
  it. The camera only moves right, so it does not come back.
- **A crate knocks an enemy out** when it was thrown and touches it, or when the player hides
  under it (crouched all the way down) and the enemy walks into it.
  - Flyer and cook are flung away, 4 3/16 pixels up and sideways per frame, with a sound.
  - The fork drops in a small arc, without a sound.
  - The crate stops, stays whole for one more frame, flies apart in four pieces for 5 frames
    and is gone. A player who was hiding under it is left crouching without a crate.
- **Order.** Crates and enemies share one list of 9 places. A new one takes the lowest free
  place. They act and are drawn in that order. It matters: for example something made by an
  enemy in a place before its maker's does not move on the frame it is made.
- **Sounds.** Three new ones, in the same single effect slot as the others:

  | Sound | Frames | Channel |
  |---|---|---|
  | flyer's buzz | 4 (2 sounding) | 2nd square |
  | cook throws | 10 (8 sounding) | 2nd square |
  | enemy knocked out | 17 (noise for the first 9) | 2nd square and noise |

  - A flyer asks for its buzz every 3 frames while flying and every 4 while on the spot. Each
    buzz cuts off whatever is playing. So while a flyer is about, a pick-up, bonus or landing
    sound is only heard for 1 to 3 frames. This is the "repeating sound" that the README of
    step 08 listed as missing.
  - When several things ask for a sound on one frame, the last one in the order above is
    heard. The player asks first (pick-up, bonus, landing). A throw sound is asked for by the
    crate, at its place in the list.
- **Two corrections to step 08**, found through the new recordings:
  - While a crate is coming down over the player (the first 4 frames of hiding), letting go of
    DOWN or pressing A does nothing yet.
  - Which sprite is in front changes with every frame *of the game*. While the game stands
    still (the fade after a fall, the fade at the start) the order stays as it is. Before, it
    kept changing, and overlapping sprites flickered during the fade.
- Dale: same behaviour on the same frames.

## Two things the port does differently on purpose

- **Sprites per line.** The NES shows at most 8 sprites on a picture line and leaves the others
  out, so parts of enemies vanish for a frame when much is on one line. The port draws
  everything.
- **Dropped frames.** When the original is too busy it leaves a game frame out (everything
  stands still for one frame). This happened at one place in the new recordings (NES frame 2097) and
  three times in the route recording. The port never does that. From such a frame on, the port
  is one frame ahead of the original.

## Assets

| File | Size | Sub-images |
|---|---|---|
| `spr_enemy_strip840.png` | 8x8 | 60 tiles × 2 directions × 7 brightness steps: index = (tile × 2 + (0 left, 1 right)) × 7 + step |
| `snd_buzz.ogg` | 4 frames (0.07 s) | flyer |
| `snd_cook_throw.ogg` | 10 frames (0.17 s) | cook throws the fork |
| `snd_enemy_hit.ogg` | 17 frames (0.28 s) | flyer or cook knocked out |

Note the direction: the enemy strip has **left first**, the player strips have right first.

All assets of steps 05 to 08 are still needed and unchanged.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprite `spr_enemy`** (new): `spr_enemy_strip840.png`, 840 sub-images of 8x8, origin 0,0,
   **Remove Background** and **Smooth Edges** unticked.
2. **Sounds** (new) `snd_buzz`, `snd_cook_throw`, `snd_enemy_hit`: mono, 48000 Hz, not streamed.
3. **Scripts**:
   - replace `scr_pl_pick` and `scr_pl_throw`;
   - new: `scr_lv_take_slot`, `scr_lv_spawn`, `scr_lv_block`, `scr_en_move_x`, `scr_en_move_y`,
     `scr_en_face_player`, `scr_en_near_player`, `scr_en_row`, `scr_en_floor`,
     `scr_en_ceiling`, `scr_en_wall`, `scr_en_hit_by`;
   - the other `scr_pl_*` scripts stay as they are.
4. **Object `obj_enemy`** (new): no sprite, not placed in the room. Three events:
   - **Create** ← `gml/obj_enemy_Create.gml`
   - **Other → User Defined 0** ← `gml/obj_enemy_User0.gml`
   - **Other → User Defined 1** ← `gml/obj_enemy_User1.gml`
5. **Object `obj_crate`**: replace Create, User Defined 0 and User Defined 1.
6. **Object `obj_player`**: replace Create and User Defined 0. User Defined 1 is unchanged.
7. **Object `obj_stage1`**: replace Create, End Step, Draw and User Defined 0.
8. `obj_intro` stays as it is.

### What changed in the code

- **The object list.** `obj_stage1` has `lv_slot[3..11]` (the instance) and `lv_slot_k[3..11]`
  (0 free, 1 crate, 2 enemy, 3 the exit). `scr_pl_pick` and `scr_lv_spawn` take a place;
  a crate or enemy gives it back when it is gone. End Step runs the User Defined 0 events in
  this order, Draw the User Defined 1 events.
- **`obj_enemy`** is one object for all four kinds (`e_kind`). All its rules are in User
  Defined 0. Its pictures are tables in `obj_stage1` Create (`en_tn`, `en_tdx`, `en_tdy`,
  `en_tim`), numbered as in the original.
- **`obj_crate`** has a new mode 5 (breaking), and `c_hot`, `c_slot`, `c_pic`, `c_snd`.
- **Sounds**: `p_snd` no longer carries the throw sounds; the crate asks for them (`c_snd`).
  The stage collects what crates and enemies ask for in `lv_snd`.
- `lv_ord` replaces `lv_fc & 1` for the drawing order.

## How it was checked

`tools/capture/sim_enemies.py` is a Python port of this step's GML. It was run with the same
buttons as 15 new emulator recordings (13 with Chip, 2 with Dale): a crate thrown up and
forwards into the first flyer, hiding under a crate while the flyer passes and drops things,
the first cook walking into the crate the player hides under, a crate thrown at the cook, a
crate thrown at the fork, a fall into the pit with a crate that flies up into the flyer, and
six runs of random buttons.

On all 12,587 compared frames (2,927 with a flyer, 362 with something dropped, 1,458 with a
cook, 189 with a fork; 11 enemies knocked out):

- Memory: everything step 08 compared, and for every place of the object list an enemy's
  position with fractions, speeds, picture, direction, hit points, damage value and body size,
  and a crate's position and breaking picture. 0 differences.
- Sprites: every sprite the port draws is in the original's sprite list; every sprite of the
  original except the hearts is drawn by the port; the order is the same. 0 differences. (This
  closes the gap named in step 08: a sprite the port fails to draw is now reported.)
- Picture: 0 differing pixels outside the hearts, and outside the 471 picture lines on which
  the original had more than 8 sprites.
- Sounds: all 617 sounds the port starts (431 buzzes, 4 cook throws, 10 hits, 22 pick-ups, 14
  throws, 32 bonus, 104 landings) start on the same frame in the original, and the original
  starts no others. On every frame the same side (music or effect) has the second square
  channel. The "drowned sound" allowance of step 08 is gone.
  This check compares when sounds start and who has the channel, not the sound files
  themselves. That is how a fault in `snd_buzz.ogg` got through: its 4th frame held a note
  of the music instead of silence. The file is now cut from the last buzz of a row (frame
  1990 of the recording `en_hide`), where the original is silent on frames 3 and 4.

The 48 recordings of steps 06 to 08 that do not start at the end of the section were run
through the new port as well, now up to the first time the player is hurt: 35,550 frames, 0
differences (1,351 more buzzes, 2 more hits).

`tools/capture/sim_enemies_route.py` runs the enemy code against the old recording of a walk
through the whole section, with the player's position taken from the original (the player
gets hurt there). All twelve objects enter; the cooks jump at walls and edges. 1,998 frames,
0 differences in the enemies' memory. Pictures and sounds are not compared in that run.

What that leaves out, and what was not checked:

- The GML has not been run in GameMaker; only the Python port has.
- **A crate of a far throw hitting an enemy was not recorded.** The port lets that crate fly
  on and knocks the enemy out. This is an assumption.
- **No crate flying left hit anything.** The port flings the enemy left in that case; not
  measured.
- **What the flyer drops and a crate**: the port never lets a crate hit it. The recordings
  show the two near each other without a hit, but no case that would prove it for every
  position.
- A full object list (9 crates and enemies at once) did not occur. The port then makes no new
  object.
- The cooks' jumps and the enemies further right than the first cook were only checked in the
  route run (memory only, not picture or sound).
- The three exit recordings of steps 06 and 07 start among enemies the port has not seen
  arrive, so they cannot be run through this port. The exit code itself is unchanged.
- `snd_enemy_hit` is two single-channel recordings added together, and it plays on top of the
  music's drums. In the original the drums are silent for those 9 frames.
- The sounds were compared through the sound driver's register writes, not by ear.
- Still open from step 08: a thrown crate and walls; putting a crate down; what the bonus
  count does; two-player rules; losing the last life.

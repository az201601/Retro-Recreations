# Step 15 – level 1, section 3: the stove and the sink (map, camera, player, exit)

Going through the hole in the kitchen wall now leads into the third section of level 1: a
kitchen counter with two ovens, shelves, pots, and a sink at its right end. This step has the
section's picture, its camera, the player's movement in it, the falls, and its exit. One player.

**The exit cannot be reached by playing in this step.** It is behind the sink, and the way out
of the sink needs the water that rises in it (a later step). The exit itself is in and was
checked; a test shortcut that starts next to it is given below.

The section is split over several steps, as the kitchen was:

1. **section change, background, camera, player, falls, exit (this step)**
2. crates and bonus boxes
3. the enemies
4. the sink: the tap, the rising water, the thing that floats on it

## What was confirmed in the original

- **Shape.** 7 screens in a row, 1792 × 240 pixels. The camera only moves sideways (to x 1536).
  A counter top at y 192 with four gaps of 32 pixels in front of the two ovens (x 288–319,
  480–511 and 1056–1087, 1248–1279), shelves at y 32 to 160, and no floor from x 1440
  to the sink. The sink is the box from x 1584 to 1759: walls 16 pixels thick from y 48 down,
  its floor at y 208.
- **Section change.** As from the dining room into the kitchen: 22 frames after the player has
  gone into the kitchen's hole the section is set up (camera 0, player at x 24, y 192), 9 frames
  later its picture comes on and fades in (steps at 5, 9 and 13 frames, control from frame 18).
  Hearts, lives and the bonus count are kept, the music plays on. One difference: the frame
  count behind the flashing and the order of the sprites loses 3 frames at the first section
  change and none at this one. Confirmed in two ways: the status screen's portrait, which
  depends on the order of the sprites, and a carried crate in the original, which is bright on
  the same four of every eight values of the game's frame counter (5, 6, 7, 0) in the kitchen
  and in this section (`measure_sec3.py`). The port's count is compared with the picture in the
  kitchen and keeps the same distance to the game's counter here.
- **Camera:** as before, it follows a player in the right half of the screen who moves right and
  never goes back.
- **Falling.** Below the picture a life is lost; the section starts again from its left end with
  3 hearts. After GAME OVER and CONTINUE the level starts in the dining room.
- **Top edge.** A jump from the top shelf (y 32) leaves the picture at the top; nothing happens.
- **Exit.** The object list of the section (ROM bank 3, `$A444`) ends with the exit, type `$21`
  as in the other sections, at column 111, row 10: x 1776, y 160, the ledge right of the sink.
  The box is 12 pixels to each side and takes over a player who stands, as before. He then walks
  right by himself, and here the camera has not stopped yet: it moves 2 pixels per frame **and**
  he moves 2 pixels per frame on the screen. The section is over when he gets behind the picture
  in the dark gap at x 1776 (next point); then fade-out as before.
- **Behind the picture.** The block map has a kind of block (`$9F`) in which the player is drawn
  behind the background: the whole inside of the sink below its rim (x 1600–1743, from y 96,
  left column from y 112), and the gap of the exit (x 1776–1791, y 128–159). The kitchen's hole
  is made of the same block. The point that is looked at is 2 pixels right of where the player
  is after the frame's move and 1 pixel above where his feet were before it (found by dropping
  him through the tap's water: the blocks of the water itself, `$8A`–`$8D`, do not hide him).
- **A column the game has not loaded.** The original keeps 16 columns of blocks, up to the one
  248 pixels right of the camera. The exit's gap is in the section's last column, which is only
  loaded when the camera is at 1528. A player who walks into the exit by himself is looked up
  with the camera's place before that frame, so depending on where he started he gets behind the
  picture 3 or 4 frames after the exit box took him (measured: taken at x 1766 with the camera at
  1522: out at 1782 after 4 frames; with the camera at 1528: out at 1778 after 3 frames). This
  is reproduced.

## Not in this step

- **Crates and bonus boxes:** crates are solid blocks that cannot be picked up, bonus boxes are
  only part of the picture.
- **The enemies** (the list has seven, of the two types of the dining room) and what they throw.
- **The sink:** the tap (type `$09`), the thing lying in the sink (type `$1E`) and the rising
  water. In this step the sink is an empty box: a player who drops in cannot get out (falling
  out of the picture is not possible there either). Use the shortcut below to see the exit.
- **One sound that belongs to the sink's object.** Landing on the sink's floor gives the
  landing sound like any landing (measured at x 1640, 1652, 1680 and 1694, walking off the shelf
  above and jumping from it, with the object on the screen). Only a landing right next to the
  object (x 1714, it lies at 1728) is silent: the object notices the player on that frame, a
  sound comes 16 frames later and after 3 more frames the object changes. That is the object's
  doing and comes with it; in this step, where the object is not there, the landing sound plays
  there too.
- What follows the exit: the screen stays black, as it did after the kitchen until now.
- Sprites per line and dropped frames as in step 09.
- Two players, levels 2 and later.

## Assets

All new. Origin 0,0 everywhere.

| File | Size | Sub-images |
|---|---|---|
| `sprites/spr_lv1c_bg_strip49.png` | 256x240 | 7 screens × 7 brightness steps: index = screen × 7 + step |
| `sprites/spr_lv1c_front_strip7.png` | 224x240 | the picture from x 1568 to its right end, 7 brightness steps, transparent where the picture has the backdrop colour: drawn over a player who is behind the picture |

The big strip also exists as single files (`spr_lv1c_bg_0.png` … `_48.png`). Brightness steps as
before: 0–2 fade-in, 3 normal, 4–6 fade-out. No new sounds. All assets of steps 01 to 14 are
still needed and unchanged.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprites** (new): `spr_lv1c_bg` (49 sub-images of 256x240) and `spr_lv1c_front` (7
   sub-images of 224x240). Origin 0,0, **Remove Background** and **Smooth Edges** unticked.
2. **Object `obj_player`**: replace User Defined 0.
3. **Object `obj_stage1`**: replace Create, End Step, Draw and User Defined 0.
4. Everything else is unchanged; the other files in `gml/` are the same as in step 14.

Test shortcuts, in `obj_stage1` Create just before the `event_user(0);` near the end:

- `lv_sec = 2;` starts the level in the third section.
- To see the exit, also put the player on its ledge: in the same place add
  `lv_cam_x = 1522; lv_cam_show = 1522;` and, after the line that creates the player further
  down, `pl.p_x = 200; pl.p_y = 208;` puts him into the sink; `pl.p_x = 244; pl.p_y = 150;` drops
  him onto the exit. (Remove these lines again afterwards.)

### What changed in the code

- **`obj_stage1` Create**: `lv_map3` (the section's blocks, 15 rows) and `lv_back3` (the
  blocks in which the player is behind the picture).
- **User Defined 0**: builds `lv_kind` from `lv_map3` when `lv_sec` is 2.
- **End Step**: the section change now also goes from 1 to 2 (where the `TODO` was); the exit
  box at x 1776, y 160; the camera's end at 1536; the camera no longer takes its step off the
  position of a player who walks by himself; the exit takes its place in the object list when
  column 111 comes up; `p_behind` and the end of the section from `lv_back3`.
- **Draw**: the section's background, and `spr_lv1c_front` over a player who is behind the
  picture.
- **`obj_player` User Defined 0**: in the third section it leaves `p_out` and `p_behind` to
  `obj_stage1`.

## How it was checked

`tools/capture/sim_sec3.py` is a Python port of this step's GML. It was run with the same
buttons as 21 emulator recordings of the third section, each starting two seconds before the
kitchen's exit: the way through the section up to the sink, a fall into the first gap, three
falls with GAME OVER and CONTINUE, three runs of random buttons on the first screen, the status
screen twice, held buttons during the section change, jumps on the first shelf, and three runs with
Dale. Seven more have the player's place written into the game's memory on one or two frames,
because the exit and the sink's inside cannot be reached without the rising water: dropped onto
the exit standing, crouching and moving left, next to it, walking and jumping in the empty sink,
and dropped twice through the water under the tap.

Compared on every frame: the player's memory values (state, position, speed, picture,
direction, body height, hearts, flags including "behind the picture"), camera, lives, the
landing sound, and the whole picture.

Because crates, bonus boxes, enemies and the sink's objects are not in the port yet, in the
third section these are taken out of the comparison: the object list and the bonus count, the
picture where the NES has sprites the port does not draw and in a block where the NES player
took a bonus box, and the landing sound while the NES plays a sound the port does not have. The
way through the section is compared up to the frame before the player lands in the sink (the
recording was not hurt up to there).

| | frames | differences |
|---|---|---|
| Third section, 21 recordings | 9,756 | 0 |
| Everything `sim_caps.py` checks (the kitchen, 103 runs; those that reach its exit now run on into the new section) | 172,327 | 0 (5 accepted frames, see step 14) |
| All recordings of steps 06–10 (`--old --nopic`) | 121,903 | 0 |

Two things the port cannot be compared on yet were measured in the emulator alone, with
`tools/capture/measure_sec3.py`: the frames on which a carried crate is bright (kitchen and
this section), and the landing sound in the sink at six places.

The GML itself was not run: there is no GameMaker here. Please check in GameMaker in
particular: the walk from the kitchen into the new section, a fall into a gap, and (with the
shortcut) the player behind the glints of the sink and going into the exit.

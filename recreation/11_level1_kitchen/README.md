# Step 11 – level 1, section 2: the kitchen (map, camera, player, exit)

Walking out of the dining room on the right now leads into the kitchen. This step has the
kitchen's picture, its camera (sideways, up a shaft, sideways again), the player's movement in
it, falling out of it and its exit. One player.

The kitchen is split over three steps:

1. **section change, background, camera, player, falls, exit (this step)**
2. crates, bonus boxes and the star item (step 12)
3. the mice (step 13)

## What was confirmed in the original

- **Shape.** The kitchen is an L of 9 screens, 2048 × 480 pixels: a lower floor 6 screens long,
  a shaft going up one screen height above its right end, and an upper floor that goes on to
  the right for 3 screens.
- **Section change.** The player walks out of the dining room, the picture fades out as before.
  22 frames after leaving, the kitchen is set up: camera at its left end, player at x 24, y 192.
  9 frames later its picture comes on and fades in like the level start (steps 5, 9 and 13
  frames in; control from frame 18). Hearts, lives and the bonus count are kept, the music
  plays on, and the walk animation goes on in step.
- **Camera, sideways:** as in the dining room (it follows a player in the right half of the
  screen who moves right, never goes back). It stops at x 1280, under the shaft, and only goes
  on (to 1792) once it has gone all the way up.
- **Camera, up:** only at x 1280. When the player moves up while above screen line 128, the
  camera goes up by the same amount, until it has risen 240 pixels. It never comes down.
- **Falling.** Only what is on the screen exists: whoever falls below the picture in the shaft
  loses a life, even with floor further down. After a life is lost the kitchen starts again
  from its left end with 3 hearts. After GAME OVER and CONTINUE the level starts again in the
  dining room.
- **Top edge.** On the upper floor a jump can leave the picture at the top; nothing happens.
- **Exit.** A hole in the wall at the right end of the upper floor. The invisible exit box is
  at x 2016 on the floor (y 192), 12 pixels to each side, and works like the dining room's:
  it takes over a player who stands or walks, who then walks right by himself. The section is
  over when he reaches x 2014 (the hole), not the edge of the picture; then fade-out as before.
- **Behind the wall.** In the hole the player is shown behind the wall: only where the wall
  picture has the colour of the background he shows through. This holds exactly while the point
  2 pixels right of and 8 above his feet is inside the 32 × 32 hole (x 2016–2047, y 160–191 of
  the kitchen); checked on 3,173 frames, 88 of them behind the wall.
- **The shaft's picture.** The NES holds only one screen height of background, in 15 rows of 16
  pixels, and replaces each row by the one 240 pixels higher while the camera rises. So a row
  at the top edge of the screen still shows the lower floor for a moment, and the same row at
  the bottom edge already shows the upper floor afterwards. This is reproduced (see Draw).

## Not in this step

- **Crates, the present and bonus boxes of the kitchen:** crates and present are solid blocks
  that cannot be picked up, bonus boxes are only part of the picture. Step 12.
- **The mice** and the other objects of the kitchen. Step 13.
- The third section: after the kitchen's exit the screen stays black, as it did after the
  dining room until now.
- **Two differences from the original that are left as they are:**
  - While the NES replaces a row of the shaft it shows that row half-replaced for one frame
    (58 such rows in the recordings). Here the row changes at once.
  - When the exit box takes over a player who came from the right (walking left), the NES shows
    him once more facing left, 2 pixels off, for 2 frames. Here he turns at once. (1 frame of
    the comparison.)
- Sprites per line and dropped frames as in step 09.

## Assets

All new. Origin 0,0 everywhere.

| File | Size | Sub-images |
|---|---|---|
| `spr_lv1b_bg_strip63.png` | 256x240 | 9 screens × 7 brightness steps: index = screen × 7 + step. Screens 0–5: the lower floor from the left; 6–8: the upper floor (6 is above 5) |
| `spr_lv1b_hole_strip7.png` | 48x64 | the wall around the exit hole (at 2000, 128 of the kitchen), 7 brightness steps; transparent where the player shows through |

The big strip also exists as single files (`spr_lv1b_bg_0.png` … `_62.png`), in case the
16128-pixel-wide strip does not load. Brightness steps as before: 0–2 fade-in, 3 normal, 4–6
fade-out. No new sounds. All assets of steps 01 to 10 are still needed and unchanged.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprites** (new): `spr_lv1b_bg` (63 sub-images) and `spr_lv1b_hole` (7 sub-images). Origin
   0,0, **Remove Background** and **Smooth Edges** unticked.
2. **Scripts**: replace `scr_pl_row`, `scr_pl_floor`, `scr_pl_wall`, `scr_pl_touch`.
3. **Object `obj_player`**: replace Create and User Defined 0.
4. **Object `obj_stage1`**: replace Create, End Step, Draw, User Defined 0 and User Defined 2.
5. Everything else is unchanged; the other files in `gml/` are the same as in step 10.

To get to the kitchen quickly while testing: in `obj_stage1` Create set `lv_sec = 1;`,
`lv_cam_y = 240; lv_cam_yshow = 240; lv_cam_yold = 240;` just before the `event_user(0);` near
the end. The level then starts in the kitchen.

### What changed in the code

- **`obj_stage1`**: `lv_sec` (0 dining room, 1 kitchen), `lv_rows`, the camera height
  `lv_cam_y` with `lv_cam_yshow` / `lv_cam_yold` for the Draw event, and the kitchen's block map
  `lv_map2` (30 rows). User Defined 0 builds `lv_kind` from the map of the current section.
  End Step: the section change (where the `TODO` was), the camera rules, the exit box at the
  kitchen's height, the restart at the kitchen's start. User Defined 2: CONTINUE goes back to
  the dining room.
- **Draw**: the kitchen's background (lower floor, upper floor, or the shaft row by row) and
  the wall piece over a player in the hole.
- **`obj_player`** and the four scripts: every look at the block map adds `lv_cam_y`, since the
  player's `p_y` stays a screen position; `scr_pl_row` ignores what is below the picture; the
  section ends at the hole; `p_behind` / `s_behind`.
- A sound effect still playing at the section change plays on (its end time is moved with the
  level clock).

## How it was checked

`tools/capture/sim_kitchen.py` is a Python port of this step's GML. It was run with the same
buttons as 18 emulator recordings: the way from the dining room into the kitchen, the whole
kitchen from entry to exit, held buttons during the section change, a fall in the shaft, lost
lives up to GAME OVER and CONTINUE, the exit reached in three ways (walking, crouching in front
of it, jumping over it and coming back), five runs of random buttons in the shaft, the top edge,
the status screen, and three runs with Dale.

Compared on every frame: the player's memory values (state, position, speed, picture,
direction, body height, hearts, flags including "behind the wall"), camera x and y, lives, the
landing sound, and the whole picture.

Because the mice, crates and bonus boxes are not in the port yet, three things are taken out of
the comparison: the picture where the NES has sprites the port does not draw (the mice), the
blocks where the NES player took a bonus box, and a landing sound while another effect plays on
the NES. The recorded runs avoid being hurt, except the ones that lose lives by falling.

| | frames | differences |
|---|---|---|
| Kitchen recordings | 9,377 | 1 (the exit entered from the right, see above) |
| All recordings of steps 06–10 (`--old`) | 121,903 | 0 |

The GML itself was not run: there is no GameMaker here. Please check in GameMaker in
particular: the picture in the shaft while the camera rises, the walk into the hole, and a
fall in the shaft.

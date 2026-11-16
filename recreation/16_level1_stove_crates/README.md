# Step 16 – level 1, section 3: the stove's crates and bonus boxes

The third section of level 1 (step 15: map, camera, player, falls, exit) now has its crates
and bonus boxes. Second of the section's four steps; still to come: the enemies, and the sink
(the tap, the rising water, the thing that floats on it). One player.

## What was confirmed in the original

- **Boxes.** The section has 10 plain crates, 2 crates with a bonus box inside and 21 bonus
  boxes (no crate with an item inside, unlike the kitchen): the block `$F4` is a crate, `$F5`
  a crate with a bonus box inside, `$F9` a bonus box, as before. They behave as in the dining
  room and the kitchen (step 08): picked up with B when walked into, carried, thrown (the way
  the player faces, or with LEFT/RIGHT held on that frame, or straight up with UP), breaking
  into pieces on a crate, a wall or the shelf above; bonus boxes are collected by touching
  them (+1, at most 99). Two crates are stacked at column 62 (rows 10 and 11): the upper one
  is found first by the wall test and picked first.
- **What is behind a box.** The ROM holds the section's seven screens twice: with the boxes
  (the map of the recordings) and without. The list of the section's screens is at bank 3
  `$9E92` (7 bytes, minus 1); the screen pointers point into the table at bank 0 `$8000` /
  `$8100` as before. Each without-box screen matches the recording's map in every block that
  is not a box, so the block that shows where a box was is taken from it. (Each section has
  its own such list — the dining room's is at bank 3 `$9E6A` + 16.)
- **The patch appears one frame after the box went**, as in the other sections, and where a
  crate had a bonus box inside the bonus box appears instead (then it can be touched).
- **Sounds.** Taking a bonus box (3), picking a crate up (1) and throwing (2; the broken
  crate's noise is part of the same effect) start on the same frames as in the other sections.
  On the recording's way through the section the player takes four bonus boxes; three more
  recordings pick crates up, throw them and take the revealed bonus box.

## Not in this step

- **The enemies** (they stand and walk about in this section from column 36 on, the flyers
  with their buzz) and what they throw: step 17. A thrown crate already hits one and knocks
  it out (that much falls out of the crate code from step 08).
- **The sink** (the tap, the thing in it, the rising water): step 18.
- The enemy sounds themselves are not in the port yet, so while the NES plays one — above all
  the flyer's buzz, the very sound 6 of step 09, which the NES restarts every 3 frames while
  the flyer flies — the starting of sounds is not compared for 100 frames after; the boxes'
  sounds are compared outside those windows.
- Two players, levels 2 and later. Sprites per line and dropped frames as in step 09.

## Assets

No new ones. The patches come from `spr_lv1c_bg` (step 15). All assets of steps 01 to 15 are
still needed and unchanged.

## Transfer into GameMaker: Studio 1.4.1760

1. **Object `obj_stage1`**: replace Create, User Defined 0 and Draw.
2. Everything else is unchanged; the other files in `gml/` are the same as in step 15.

### What changed in the code

- **`obj_stage1` Create**: the section's box table `lv_box3_n`, `lv_bc3` / `lv_br3` /
  `lv_bk3` (column, row, kind) and `lv_bdc3` / `lv_bdr3` (a block of the section's picture
  that looks like what is behind the box), and `lv_rbox3_c` / `lv_rbox3_r` (a bonus box of the
  picture, shown where a crate had one inside).
- **User Defined 0**: fills `lv_box` from that table when `lv_sec` is 2 (as the dining room's
  and the kitchen's tables do for their sections).
- **Draw**: the loop that patches the picture where a box is gone now also handles the third
  section, copying the 16x16 piece from `spr_lv1c_bg` (image = screen of the donor block × 7 +
  `lv_bright`).

A test shortcut stays as in step 15: `lv_sec = 2;` in `obj_stage1` Create (just before the
`event_user(0);` near the end) starts the level in the third section; the first crates are on
the first counter at x 224/240, the first bonus boxes on the shelf at x 352–368.

## How it was checked

`tools/capture/sim_sec3.py` is a Python port of this step's GML, kept in sync with the files
here. It was run with the same buttons as the 21 emulator recordings of step 15 plus three new
ones with crates (`s3_p_cr0`–`s3_p_cr2`): the route never touches a crate, so in the new
recordings the player is put on the counter next to crates by a write into the game's memory
on one frame (the port does the same to its player), and from there on the game runs
untouched. `capture_sec3.py` now also makes these recordings.

Compared on every frame, now also in the third section: the player's memory values, camera,
lives, **the bonus count**, **the block buffer** (the boxes the NES still knows, in the 16
columns it holds), the starts of the landing/pick/throw/bonus sounds (not for 100 frames
after a sound the port does not have yet — the flyer's buzz, restarted while it flies), and the whole
picture — including the patched 16x16 pieces where a box is gone. The object list is still
not compared in the third section (the enemies come in step 17), and the picture is not
compared in a block the NES has changed that is not a box (the sink's water and object: step
18).

| | frames | differences |
|---|---|---|
| Third section, 24 recordings | 10,267 | 0 |
| Everything `sim_caps.py` checks (the kitchen and before it) | 172,327 | 0 (5 accepted frames, see step 14) |
| All recordings of steps 06–10 (`--old --nopic`) | 121,903 | 0 |

The GML itself was not run: there is no GameMaker here. Please check in GameMaker in
particular (with the `lv_sec = 2` shortcut): taking a bonus box on the shelves, picking a
crate up and throwing it, the crate with a bonus box inside at column 41 (its bonus appears
and can be taken), and what shows in a box's place one frame after it went.

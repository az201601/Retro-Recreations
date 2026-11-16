# Step 17 – level 1, section 3: the enemies

The third section of level 1 now has its enemies: the cooks and flyers of the kitchen counter.
Third of the section's four steps; still to come: the sink (the tap, the rising water, the thing
that floats on it). One player.

1. section change, background, camera, player, falls, exit (step 15)
2. crates and bonus boxes (step 16)
3. **the enemies (this step)**
4. the sink: the tap, the rising water, the thing that floats on it (step 18)

## What was confirmed in the original

- **The list.** The section's object list is at ROM bank 3 `$A444`, 8 entries of three bytes each
  (column, row, type), ending with the exit, as the dining room's (`$A3F1`) and the kitchen's
  (`$A416`) do. Each one enters when the column 264 pixels right of the camera becomes its
  column; it starts at x = column × 16. Unlike the dining room's list the row is the row byte's
  low four bits (the section has one floor of 15 rows), so y = row × 16, not row × 16 − 512.

  | column | row | x | y | what |
  |---|---|---|---|---|
  | 28 | 12 | 448 | 192 | cook |
  | 44 | 6 | 704 | 96 | flyer |
  | 60 | 12 | 960 | 192 | cook |
  | 78 | 2 | 1248 | 32 | flyer |
  | 82 | 12 | 1312 | 192 | cook |
  | 99 | 3 | 1584 | 48 | the tap (step 18) |
  | 108 | 13 | 1728 | 208 | the thing in the sink (step 18) |
  | 111 | 10 | 1776 | 160 | the exit (step 15) |

  Types: `$25` cook (kind 3), `$27` flyer (kind 1), `$09` the tap, `$1E` the thing in the sink,
  `$21` the exit. The route of step 15 walks past all five enemies without a hit.

- **The enemies are unchanged.** They behave exactly as in the dining room (step 09): a cook
  walks 32 pixels each way, turns to a player on its level less than 80 pixels away, stops for
  68 frames and throws a fork on the 34th (sound 7); the fork starts 16 pixels up and 19 ahead
  of the cook and flies 3 pixels per frame. A flyer turns once towards the player, then repeats
  48 frames flying (buzz, sound 6, restarted every 3 frames) and 48 hovering, dropping
  something 32 frames into the hover; what it drops falls faster and faster and stuns the player
  for 120 frames without costing a heart (step 10). An enemy leaves when its middle goes off the
  screen. A crate thrown onto one knocks it out (step 08/09). Their sounds and their places in
  the object list are now compared in this section too.

- **What they do to the player.** The route never meets one, so four new recordings put the
  player in an enemy's way by a write into the game's memory on one frame (the port does the same
  to its player), and from there on the game runs untouched. They are kept from the kitchen's
  exit, so the port has every enemy from its spawn and can show what happens:
  - `s3_p_en0` — put at the level of the cook of column 60 (world x 884, y 192): the fork it
    throws reaches him on NES frame 7379. A heart goes, he is thrown up and 2 pixels per frame
    to the right without control, and nothing can hurt him for 64 frames while the picture
    blinks (step 10's ways, now in this section).
  - `s3_p_en1` — put just past the first cook, over the pit at world x 1010: he falls out of the
    picture while the cook of column 60 and its fork go on above him; the section starts again
    with 3 hearts (step 15's fall and restart).
  - `s3_p_en2` — put on the counter at world x 1248, y 190 on frame 7678, under the shelves of
    the flyer of column 78: the flyer has flown off the left edge and the thing it dropped has
    already fallen at world x 1200, so neither reaches him. The cook of column 82 walks left past
    him and leaves the screen at world x 1165 on frame 7708; its fork had gone by long before.
    He stands there for 240 frames with his one heart.
  - `s3_p_en3` — walking out of the first ledge, the fork of the first cook (column 28) reaches
    him on frame 7046; he is flung to the right into the next pit and the section starts again.

## Not in this step

- **The sink** (the tap, the thing in it, the rising water): step 18. The tap's and the sink
  object's places in the object list are kept (kinds 10 and 11 take the lowest free place and
  nothing else), as the exit's was; the picture is not compared in a block the NES changed that
  is not a box (the water).
- **Getting a crate onto one of these enemies** is a run for later: on the four recordings the
  player never has a crate in hand near an enemy. The knock-out itself (a thrown crate or the
  player hiding under one, the crate breaking, sound 8) fell out of step 08's crate code and is
  unchanged; step 16's README already noted it.
- **On a start in the middle of the section** (the `s3_p_*` recordings of steps 15 and 16, which
  begin on their put frame, not these four) the enemies already out are not in the port: their
  places in the object list are taken, and for 100 frames after a sound of theirs the starting of
  sounds is not compared (above all the flyer's buzz, restarted every 3 frames while it flies).
- Two players, levels 2 and later. Sprites per line and dropped frames as in step 09.

## Assets

No new ones. All assets of steps 01 to 16 are still needed and unchanged.

## Transfer into GameMaker: Studio 1.4.1760

1. **Object `obj_stage1`**: replace Create and End Step.
2. Everything else is unchanged; the other files in `gml/` are the same as in step 16.

### What changed in the code

- **`obj_stage1` Create**: the third section's object table `lv_ob3_n` and `lv_ob3_c` /
  `lv_ob3_r` / `lv_ob3_k` (column, row, kind), read from bank 3 `$A444`. Kinds 9 (the exit), 10
  (the tap) and 11 (the thing in the sink) only take a place in the object list.
- **End Step**: the spawn loop that reads `lv_ob3_*` when the camera's column changes, with
  y = row × 16. This replaces the single "only the exit, at column 111" placeholder of step 15.
  The dining room's and the kitchen's loops are unchanged.

A test shortcut stays as in step 16: `lv_sec = 2;` in `obj_stage1` Create (just before the
`event_user(0);` near the end) starts the level in the third section; the first cook is on the
counter at x 448, the first flyer above the shelves at x 704.

## How it was checked

`tools/capture/sim_sec3.py` is a Python port of this step's GML, kept in sync with the files
here. It was run with the same buttons as the 24 emulator recordings of steps 15 and 16 plus
four new ones with the player put in the enemies' way (`s3_p_en0`–`s3_p_en3`); unlike the
other `s3_p_*` runs these four are kept from the kitchen's exit, so every enemy enters in the
port too. `capture_sec3.py` now also makes these recordings.

Compared on every frame, now also in the third section: the player's memory values, camera,
lives, the bonus count, the block buffer, **every place of the object list** (the enemies, the
forks, the drops, the crates), the starts of **all** the sounds (including the flyer's buzz and
the cook's throw), and the whole picture. On a start in the middle of the section the objects
the port never got are only kept as taken places (see above).

| | frames | differences |
|---|---|---|
| Third section, 28 recordings (`--new`) | 14,382 | 0 |
| Everything `sim_caps.py` checks (the kitchen and before it) | 172,327 | 0 (5 accepted frames, see step 14) |
| All recordings of steps 06–10 (`--old --nopic`) | 121,903 | 0 |

All of `sim_sec3.py` at once — the first two rows together — compared 186,709 frames with 0
differences. `sim_caps.py` on its own compared 172,050 frames with 0 differences (277 frames
fewer: the third-section tails only `sim_sec3.py` follows past the kitchen's exit), and
`sim_hurt.py --old --nopic` 47,405 frames with 0 differences.

The GML itself was not run: there is no GameMaker here. Please check in GameMaker in
particular (with the `lv_sec = 2` shortcut): the first fork catching a player who stands in
front of the cook of column 60, the flyer of column 78 hovering above its shelves, and the
crates of step 16 still behaving with enemies about. Also worth a look there: the spawn loop's
`col` / `lv_sp_col` parity and the kinds and rows read from the ROM's object list, which the
Python port follows but only the GameMaker build can show on screen.

# Step 05 – level 1, section 1: map and camera

The first level is a restaurant. It is made of sections; this is the first one, the dining
room. This step adds its background, the music, the fade-in, the camera and the way out.
There is no player yet, and no enemies, crates you can pick up, bonus boxes or hearts. Those
come in the next steps:

1. **map and camera (this step)**
2. player movement
3. crates and bonus boxes
4. enemies, health, death, heart display

Because there is no player, the camera is moved with the arrow keys for now. That part is
temporary and marked as such in the code.

All frame numbers below are level frames `lt`. `lt = 0` is 7 frames after the screen before the
level ended (`lt = frame - (lv_d + 7)` in the code).

## What was confirmed in the original

- The level is reached two ways, with identical timing: START in the night scene, or the end of
  the newscaster cutscene.
- The section is 8 screens wide (2048 pixels) and one screen high. It scrolls only sideways. The
  camera's left edge goes from 0 to 1792.
- There is no floor under the tables. Falling off the bottom sends the player back to the start.
- The section ends when the player walks off the right edge of the last screen, from the table
  there. The picture fades out and the second section, a kitchen, fades in, with the player on
  the left again. No new music is started at the change, so the level music should simply play
  on; this was read from the sound driver's log, not listened to.
- The left-most 8 pixels of the screen are always black in this level.
- The red crates and the "RR" bonus boxes are part of the background on the NES. When one is
  picked up, the game repaints that spot with wallpaper.

`tools/capture/level1_route.json` is a recorded playthrough of the section, start to exit,
without taking a hit. It was found by a search program, without cheats, and is what the map was
captured from.

## What happens

| lt | Event |
|---|---|
| -7 | the previous screen has ended (black) |
| -6 | the level music starts |
| 0 | the level's picture is on, still black |
| 5, 9, 13 | fade-in steps |
| 17 | full brightness |

At the exit, with the player leaving on frame `e`:

| lt | Event |
|---|---|
| e + 5, e + 9, e + 13 | fade-out steps |
| e + 17 | black |
| e + 22 | the section is over (the code stops here) |
| e + 31 | in the original, the kitchen's picture comes on and fades in the same way |

The fade-out does not use the same colours as the fade-in, so there are separate pictures for it.

### Buttons (temporary)

- **LEFT / RIGHT** (arrow keys) move the camera 2 pixels per frame, from `lt = 17` on.
- **RIGHT pressed again** when the camera is at its right end starts the exit.

## Assets

| File | Size | Sub-images |
|---|---|---|
| `spr_lv1a_bg_strip56.png` | 256x240 | 8 screens × 7 brightness steps: index = screen × 7 + step; steps 0–2 fade-in, 3 normal, 4–6 fade-out |
| `snd_lv1_music_a.ogg` | 1920 frames (32 s) | the level music loop without the NES's 2nd square channel |
| `snd_lv1_music_b.ogg` | 1920 frames (32 s) | the 2nd square channel of the loop |

The strip also exists as single files (`spr_lv1a_bg_0.png` … `_55.png`). All are in
`assets/sprites/` and `assets/sounds/`.

The background shows the section as it is before anything is touched: every crate and bonus box
is in the picture. Step 3 will take them out and make them objects.

The music is in two files for the same reason as in the cutscene: sound effects are expected to
use the 2nd square channel and silence the music's part on it. Nothing mutes it yet.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprite `spr_lv1a_bg`**: load `spr_lv1a_bg_strip56.png`. Untick **Remove Background** and
   **Smooth Edges**, origin 0,0. Check that it has 56 sub-images of 256x240; if not, use *Edit
   Sprite → File → Create from Strip* (56 images, 256 wide, 240 high, 56 per row).
2. **Sounds**: create `snd_lv1_music_a` and `snd_lv1_music_b`, mono, 48000 Hz, not streamed.
3. **Code**: replace the three events of `obj_intro` with `gml/obj_intro_Create.gml`,
   `gml/obj_intro_Step.gml` and `gml/obj_intro_Draw.gml`. They are complete replacements for
   the step 04 versions; the new parts are the `lv_` variables in Create, section 7 of Step and
   the last block of Draw. LEFT and RIGHT were added to the controller section.

The background is drawn as two neighbouring screens, and the right one sticks out past x = 256.
This relies on the room being 256 pixels wide, as in the earlier steps.

The `TODO` for the kitchen is in section 7c of the Step event. Section 7b is the temporary
camera control that the player will replace.

## How it was checked

`tools/capture/sim_level1.py` is a Python port of section 7 of Step and the level block of Draw.
It was run against four emulator recordings: the level reached by START in the night scene on
two different frames, the level reached through the whole cutscene, and the recorded
playthrough from start to exit.

- Picture: 0 differing pixels on all 3,675 compared frames. That covers the fade-in on all
  three ways in, every camera position along the playthrough, and the fade-out at the exit.

What that comparison leaves out, and what was not checked:

- The GML itself has not been run in GameMaker; only the Python port has been run, and it was
  not chained after the earlier steps.
- In the playthrough check, the camera position of each frame and the exit frame are taken from
  the recording, because the player who drives them does not exist yet. The temporary arrow-key
  control is not part of the port.
- Pixels covered by the original's sprites (player, enemies, hearts) are skipped, and so are the
  11 crate spots the playthrough changed, from the frame they changed.
- The music was recorded with nothing pressed and loops exactly every 1920 frames in the game's
  sound data. It was not compared by ear.
- Whether the camera can scroll back to the left in the original was not looked at; that
  belongs to the player step.

# Step 03 – night scene (fence, skyline, blimp, searchlights)

The screen that follows the menus: a night sky behind a barbed-wire fence, the picture scrolls
to a skyline, a blimp flies in, hovers, dips, gets lit by two searchlights while an alarm
sounds, and flies off. Then the picture fades to black. This step ends on that black screen.

All frame numbers below are scene frames `t`. `t = 0` is the first visible frame, 41 frames
after the last menu choice (`t = frame - (menu_t + 41)` in the code).

## What happens

| t | Event |
|---|---|
| 0, 4, 8, 12 | fade-in, four brightness steps |
| 13 | START is accepted from here |
| 43 | the fence starts scrolling, 2 pixels per frame, once around its 512 pixels (back at the start on t = 298) |
| 44 | sky and skyline start scrolling, 1 pixel per frame, 256 pixels (ends t = 299); the blimp enters from the left, half a pixel per frame |
| 331 | the blimp stops |
| 396–427 | the blimp sinks 16 pixels |
| 492–523 | the blimp rises again |
| 524 | the blimp flies on to the right (gone after t = 810) |
| 525 | the blimp is lit (orange, with its sign) |
| 526 | searchlight beams appear and swap every 64 frames; the alarm starts and is restarted every 49 frames |
| 1003 | end of the script: the alarm starts to get quieter |
| 1041, 1045, 1049, 1053 | fade-out, black from 1053 |
| 1060 | the scene is over |

The blimp's propeller has two pictures of 8 frames each and never stops.

### START

START ends the scene early; A, B, SELECT and the d-pad do nothing. With START on frame `p`:

- the scene keeps running unchanged for 37 more frames,
- the alarm (if playing) loses one volume step every 4 frames from `p + 4`,
- fade-out steps on `p + 38`, `p + 42`, `p + 46`, black from `p + 50`,
- the scene is over on `p + 57`.

The code sets `global.skip_cutscene`. In the original, START here also skips the newscaster
cutscene that follows and goes straight to the first level. That holds even when START is
pressed after the scene has already begun to end by itself (up to `t = 1056`).

Three quirks of the original are reproduced, because they are visible:

- **Lights on a black screen.** If START is pressed between about t = 470 and 490, the picture
  is already fading or black when the lights are due on t = 525/526. They come on anyway: the
  lit blimp pops up and fades again, and both beams show on the black screen until the scene
  ends.
- **Fade restart.** START and the end of the script each start the fade clock. If both happen
  close together, the second one delays the remaining fade steps by up to 3 frames.
- **Swallowed alarm.** START pressed exactly 2 frames before an alarm restart cancels that
  restart, so the alarm is silent for that cycle.

## Assets

| File | Size | Sub-images |
|---|---|---|
| `spr_prison_far_strip6.png` | 512x178 | 6: fade-in steps 0–3 (3 = full brightness), fade-out steps 4–5 |
| `spr_prison_fence_strip6.png` | 512x61 | 6: same order |
| `spr_prison_beam_a_strip5.png` | 256x128 | 5: lit, three fade-out steps, sky colour |
| `spr_prison_beam_b_strip5.png` | 256x111 | 5: same order |
| `spr_prison_blimp_strip16.png` | 40x24 | 16: index = lit × 8 + fade step × 2 + propeller picture |
| `snd_prison_alarm.ogg` | 49 frames | one alarm cycle |

Every strip also exists as single files (`..._0.png`, `..._1.png`, …). All are in
`assets/sprites/` and `assets/sounds/`.

The sky band is drawn at y = 0 and the fence at y = 179. Screen row 178 between them is black.
The beams are transparent except for the beam shapes and are drawn at (0,0) over the skyline.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprites**: create `spr_prison_far`, `spr_prison_fence`, `spr_prison_beam_a`,
   `spr_prison_beam_b` and `spr_prison_blimp`, each loaded from its `_stripN.png` file. Untick
   **Remove Background** and **Smooth Edges** in the load dialog, origin 0,0. Check the number
   of sub-images (6, 6, 5, 5, 16); if it is wrong, use *Edit Sprite → File → Create from Strip*
   with the sizes from the table above.
2. **Sound `snd_prison_alarm`**: Create Sound, load the file, mono, 48000 Hz, not streamed.
3. **Code**: replace the three events of `obj_intro` with `gml/obj_intro_Create.gml`,
   `gml/obj_intro_Step.gml` and `gml/obj_intro_Draw.gml`. They are complete replacements for
   the step 02 versions; the new parts are the `ns_` variables at the end of Create, section 5
   of Step and the last block of Draw.

`spr_prison_far` and `spr_prison_fence` are 512 pixels wide per sub-image. If your texture
page size is set below 1024, raise it in Global Game Settings.

The `TODO` for the next screen is in section 5f of the Step event.

## How it was checked

`tools/capture/sim_prison.py` is a Python port of the night-scene parts of Step and Draw. It was
run against 60 emulator recordings: no input, the same scene started 3 frames later, other
buttons, two START presses, and a single START on 54 different frames across the whole scene.

- Picture: 0 differing pixels on all 42,646 compared frames.
- Alarm: the frames on which the port starts the alarm match the frames on which the game's
  sound driver starts it in all 60 recordings. The volume the port uses matches the volume the
  game writes on every frame except one frame in one recording.

Not checked, or known to differ:

- The GML itself has not been run in GameMaker; only the Python port has been run. The port was
  checked for the scene on its own, not chained after the step 02 menus.
- The alarm is one recorded cycle replayed. Its loudness steps during the fade use the NES
  volume formula rather than recordings of each step.
- The earliest START was tested frame by frame (t = 12 ignored, t = 13 accepted). The latest
  START that still skips the cutscene is t = 1056 or 1057; 1057 was not tested and the code
  treats it as accepted.
- The lights-on-black quirk was captured for START on t = 473–492 only; outside that range the
  code follows the same rule without a recording to compare.

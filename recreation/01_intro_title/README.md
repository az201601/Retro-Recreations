# 01 – Spotlight intro and title screen

Chip 'n Dale Rescue Rangers 2 (USA), recreated for GameMaker: Studio 1.4.1760.

This covers everything from the first black frame after the copyright screen fades out,
through the spotlight sequence, to the title screen waiting on "Press START button".

- `assets/` – graphics and sound extracted from the ROM running in Mesen
- `gml/` – the three code blocks to paste into one object
- `../../tools/capture/` – the scripts that produced and checked all of this

Nothing here was run in GameMaker. The GML logic was ported line for line to Python
(`tools/capture/sim.py`) and that port, drawing the PNGs in `assets/`, matches the emulator
pixel for pixel on every frame tested (see "What was checked").

## What the original does

Frame numbers are "NES frames" counted from power-on in Mesen. The GML counts from 0 at
NES frame 156, so `frame = NES frame - 156`.

| NES frame | frame | Event |
|---|---|---|
| 156 | 0 | Copyright text has faded to black. Screen stays black. |
| 169, 189 | 13, 33 | Two short thumps from the sound chip being set up (`snd_intro_pops`). |
| 188 | 32 | Spotlight is created above the screen at x=160, moving down 2 px/frame. |
| 212 | 56 | First rows of the spotlight become visible at the top edge. |
| 316 | 160 | Turns up-left, 1.375 px/frame on each axis. |
| 412 | 256 | Turns right, 2 px/frame. |
| 476 | 320 | Turns down-left, 1.375 px/frame. |
| 524 | 368 | Turns left, 2 px/frame, and leaves the screen (gone by 597). |
| 652 | 496 | Wall switches to the version with the Chip and Dale silhouettes. |
| 653 | 497 | Intro jingle starts. Spotlight is placed off-screen left at y=73, moving right 2 px/frame. |
| 786 | 630 | Overshoots the silhouettes and snaps back left at 4 px/frame. |
| 802 | 646 | Stops on the silhouettes. Drum roll starts on 803. |
| 867, 871, 875, 879 | 711… | Spotlight fades out in three darker steps, then black. |
| 888 | 732 | Title music starts (replaces the drum roll). |
| 892, 896, 900, 904 | 736… | Title screen fades in over four palette steps. |
| 905 | 749 | START is accepted from here on. |

Other things found:

- **How the spotlight is built.** The disc is 32 sprites (8x16 each) forming a 64x63 image,
  drawn *behind* the background. The brick mortar lines and the silhouettes are background
  tiles in solid black, so they cut their shape out of the disc.
- **Sub-pixel movement.** Position is 8.8 fixed point, which gives the uneven 2,1,2,1,1 pixel
  steps on the diagonals. The GML keeps position in 1/256 pixel units for the same reason.
- **Edge behaviour.** Sprites are hidden in the left 8 pixels of the screen, and a 16 pixel
  row of the disc is not drawn until that row's Y is on screen. So the disc enters from the
  top in four chunks rather than smoothly. The Draw code reproduces both.
- **START skips the intro**, but only while the spotlight is travelling (NES frames 188–801).
  The picture freezes, the fade-out starts 5 frames after the press, and the rest follows on
  the same schedule as the normal ending. Presses before 188 or from 802 to 904 are ignored.
- **A, B, SELECT and the d-pad do nothing** on the title screen.
- **The title screen is completely static** (no blinking text, no attract mode in the first
  ~2 minutes). The music is a 2880 frame (48 s) loop that ends with about a second of silence.
- **START on the title screen** replaces "Press START button" with a "1player / 2players" menu
  over 3 frames. That is not built yet; the Step code has a `TODO` where it goes.

## Assets

| File | GMS resource | Size | Notes |
|---|---|---|---|
| `sprites/spr_spotlight_strip4.png` | Sprite `spr_spotlight` | 64x63, 4 sub-images | 0 = full brightness, 1–3 = fade steps |
| `sprites/spr_title_bg_strip4.png` | Sprite `spr_title_bg` | 256x240, 4 sub-images | NES background layer; 0 = darkest, 3 = final |
| `sprites/spr_title_fg_strip4.png` | Sprite `spr_title_fg` | 256x240, 4 sub-images | NES sprite layer, transparent elsewhere |
| `backgrounds/bg_intro_wall.png` | Background `bg_intro_wall` | 256x240 | Black mortar lines on transparent |
| `backgrounds/bg_intro_silhouette.png` | Background `bg_intro_silhouette` | 256x240 | Mortar lines plus Chip and Dale silhouettes |
| `sounds/snd_intro_pops.ogg` | Sound `snd_intro_pops` | 44 frames | The two thumps; optional |
| `sounds/snd_intro_jingle.ogg` | Sound `snd_intro_jingle` | 150 frames | |
| `sounds/snd_intro_roll.ogg` | Sound `snd_intro_roll` | 85 frames | |
| `sounds/snd_title_theme.ogg` | Sound `snd_title_theme` | 2880 frames | Loops |

The `_0.png` … `_3.png` files next to each strip are the same sub-images as separate files,
in case you prefer to add them one by one.

Colours are Mesen's default NES palette. The audio was recorded from Mesen at 48 kHz and
stretched by 0.17 % so that one frame is exactly 800 samples; the NES runs at 60.0988 fps and
the GMS room runs at 60, so this keeps sound and picture in step.

## Putting it into GameMaker: Studio 1.4.1760

Resource names must match exactly, because the code refers to them.

### 1. Sprites

For each of the three `*_strip4.png` files:

1. Right-click **Sprites → Create Sprite**.
2. Set the name (`spr_spotlight`, `spr_title_bg`, `spr_title_fg`).
3. **Load Sprite**, pick the strip file. Untick **Remove Background** and **Smooth Edges** in
   the file dialog. The `_strip4` suffix makes GMS split it into 4 sub-images.
4. Check it shows 4 sub-images at the size in the table above. If it loaded as one wide image
   instead, use **Edit Sprite → File → Create from Strip** with 4 images, 4 per row, and the
   width and height from the table.
5. Leave the origin at 0, 0.

### 2. Backgrounds

For each of the two PNGs: **Backgrounds → Create Background**, set the name, **Load Background**,
untick **Remove Background** and **Smooth Edges**.

### 3. Sounds

For each of the four OGGs: **Sounds → Create Sound**, set the name, load the file. Leave the
defaults.

### 4. Object

1. **Objects → Create Object**, name it `obj_intro`. No sprite.
2. **Add Event → Create**, drag in **Execute Code** (Control tab), paste `gml/obj_intro_Create.gml`.
3. **Add Event → Step → Step**, same with `gml/obj_intro_Step.gml`.
4. **Add Event → Draw → Draw**, same with `gml/obj_intro_Draw.gml`.

### 5. Room

1. **Rooms → Create Room**, name it `rm_intro`. It must be the first room in the list.
2. **settings** tab: Width 256, Height 240, **Speed 60**.
3. **backgrounds** tab: tick **Draw background color**, set the colour to black.
4. **views** tab: tick **Enable the use of Views**, select View 0, tick **Visible when room starts**.
   View in room: X 0, Y 0, W 256, H 240. Port on screen: X 0, Y 0, W 768, H 720 (3x; use any
   whole multiple of 256x240).
5. **objects** tab: place one `obj_intro` anywhere in the room.

### 6. Global Game Settings

- **Windows → Graphics**: untick **Interpolate colors between pixels**.
- **General**: **Use New Audio Engine** must be ticked (it is by default).

### Controls

START is the Enter key. To change it, edit the `keyboard_check_pressed(vk_enter)` line at the
top of the Step code.

## What was checked

`tools/capture/sim.py` compares the Python port of the GML against the emulator:

- Normal run, no input: NES frames 156–1198, 1043 frames, 0 mismatched pixels.
- START pressed on NES frame 187, 188, 235, 300, 410, 474, 568, 650, 652, 653, 700, 706, 784,
  800, 801 and 802: 400 frames each, 0 mismatched pixels. This covers both edges of the skip
  window and both sides of the jingle and drum roll triggers.

What that does not cover:

- **GameMaker itself.** The comparison is on a Python port, so a typo in the GML, or a GMS
  drawing quirk, would not show up. Please tell me if anything looks off when you run it.
- **Audio timing inside GameMaker.** The sounds are started on the right frame, but GMS adds its
  own output delay (typically a few tens of milliseconds), which cannot be controlled from GML.
- **Audio during a skip.** When START cuts into the jingle, the code stops it on the frame the
  title music starts. That matches what the recordings show, but it was judged from loudness
  per frame, not compared sample for sample.
- **Sound effects.** There are none on this screen. Later screens will have effects that take
  over a music channel on the NES; pre-recorded music cannot reproduce that exactly, so sound
  will need a different approach there.

## Regenerating

See `../../tools/capture/README.md`.

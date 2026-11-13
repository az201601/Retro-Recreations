# Step 04 – newscaster cutscene

The screen that follows the night scene when START was not pressed there: a TV studio with a
text box on top. Chip reads the news, Gadget, Monty, Zipper and Dale come and go, and the story
is typed into the text box page by page with a typing sound over the music. Then the picture
fades to black. This step ends on that black screen; the first level comes next.

All frame numbers below are cutscene frames `nt`. `nt = 0` is the first visible frame, 12 frames
after the night scene ends (`nt = frame - nw_t0` in the code).

## What happens

| nt | Event |
|---|---|
| -11 | the music starts (the alarm of the night scene is cut off) |
| 0, 4, 8, 12 | fade-in, four brightness steps; Chip is at the desk |
| 13 | START is accepted from here |
| 51 | the first page starts typing |
| 1519 | Gadget enters (leaves around 5201) |
| 3139 | Monty enters (leaves around 5598) |
| 5201 | Zipper flies in and hovers (flies off by 6301) |
| 5598 | Dale enters; a star spins above him from 6301 |
| 8464 | the last page is cleared |
| 8472 | end of the script: the music starts to get quieter |
| 8510, 8514, 8518, 8522 | fade-out, black from 8522 |
| 8529 | the cutscene is over |

These times are for a player who presses nothing. Pressing B makes everything after it earlier.

### Text

- 25 pages (numbered 0–24 in the code), three lines each, on text rows 3, 5 and 7. Tall
  characters also use the row below.
- One character every 5 frames. A space takes the same 5 frames. A line break takes 1 frame.
- Every character and space starts a typing sound, 3 frames long. There are six of them, one
  per speaker: narrator, Chip, Gadget, Monty, the crowd on page 15, Dale.
- A page stays for 120 frames after its last character and is then cleared, top row first,
  within 6 frames. The next page starts after a pause that differs per page (7 to 176 frames;
  the long ones are where an actor walks in).
- The speaker's mouth opens and closes every two characters and closes when the page is
  cleared. Pages 0–2, 15 and 21–24 have no speaker on screen.

### Buttons

- **B while a page is typing**: the rest of the page appears at one character per frame,
  without typing sounds.
- **B while a complete page is showing**: the page is cleared at once.
- **START** on frame `p` ends the cutscene: it keeps running for 37 more frames, the music loses
  one volume step every 4 frames from `p + 4`, fade-out steps on `p + 38`, `p + 42`, `p + 46`,
  black from `p + 50`, over on `p + 57`. A typing sound that would start on `p + 2` is dropped.
- A, SELECT and the d-pad do nothing. In the GML, B is the **Z** key.

The actors' movements are tied to the pages, so they follow when B shortens a page. Zipper is
the exception: his hovering runs on its own 252-frame clock, and he only leaves at the start of
a wing beat.

## Assets

| File | Size | Sub-images |
|---|---|---|
| `spr_news_bg_strip7.png` | 256x240 | 7 brightness steps: 0–2 fade-in, 3 normal, 4–6 fade-out |
| `spr_news_font_strip357.png` | 8x8 | 51 glyph tiles × 7 brightness steps (index = glyph × 7 + step) |
| `spr_news_piece_strip1113.png` | 8x8 | 159 sprite pieces × 7 brightness steps (index = piece × 7 + step) |
| `snd_news_music_a.ogg` | 1920 frames (32 s) | the music loop without the NES's 2nd square channel |
| `snd_news_music_b.ogg` | 1920 frames (32 s) | the 2nd square channel of the music loop |
| `snd_news_type_0.ogg` … `_5.ogg` | 3 frames | the six typing sounds |

Every strip also exists as single files (`..._0.png`, `..._1.png`, …). All are in
`assets/sprites/` and `assets/sounds/`.

`spr_news_bg` is the studio with an empty text box; the man at the studio desk is part of it.
The actors are not stored as whole pictures. Each pose is a list of 8x8 pieces, as on the NES,
because the original picture depends on the order of those pieces: the order flips every frame,
and at most 8 pieces are shown on one screen line. Where actors overlap or stand side by side
this makes parts of them flicker. The Draw event reproduces that rule; whole-pose images were
tried first and were wrong on 89 frames.

The typing sound and the music share one NES sound channel. That is why the music is in two
files: `snd_news_music_b` is muted when a typing sound starts and comes back with its next note.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprites**: create `spr_news_bg`, `spr_news_font` and `spr_news_piece`, each loaded from its
   `_stripN.png` file. Untick **Remove Background** and **Smooth Edges** in the load dialog,
   origin 0,0. Check the number of sub-images (7, 357, 1113); if it is wrong, use *Edit Sprite →
   File → Create from Strip* with the sizes from the table above. For `spr_news_piece` the
   transparency of the PNG must be kept.
2. **Sounds**: create `snd_news_music_a`, `snd_news_music_b` and `snd_news_type_0` to
   `snd_news_type_5`, mono, 48000 Hz, not streamed.
3. **Code**: replace the three events of `obj_intro` with `gml/obj_intro_Create.gml`,
   `gml/obj_intro_Step.gml` and `gml/obj_intro_Draw.gml`. They are complete replacements for
   the step 03 versions; the new parts are the `nw_` variables and the data tables at the end
   of Create, section 6 of Step and the last block of Draw. The B button was added to the
   controller section.

The second half of the Create event is data: the text, the actors' movements and poses, and the
note starts of the music, each as a long string of digits that a loop unpacks into an array. It
is generated by `tools/capture/gen_news_gml.py` and is not meant to be edited by hand.

Two `TODO`s mark where the first level takes over: section 5f of Step (START was pressed in the
night scene) and section 6a (the cutscene has ended).

## How it was checked

`tools/capture/sim_news.py` is a Python port of section 6 of Step and the cutscene block of
Draw. It runs on the same tables that are written into the Create event. It was run against 49
emulator recordings: no input for the whole cutscene, B pressed rapidly, B pressed slowly, B
held, a single B on 21 different frames, the other buttons, and a single START on 23 different
frames.

- Picture: 0 differing pixels on all 24,004 compared frames.
- Typing sounds: the frames on which the port starts one match the frames on which the game's
  sound driver starts one in all 49 recordings.

Not checked, or known to differ:

- The GML itself has not been run in GameMaker; only the Python port has been run. The GML was
  written from the port by hand, so a slip in that translation would not show in the numbers
  above. The port was checked for the cutscene on its own, not chained after step 03.
- Muting of `snd_news_music_b`: the rule was compared with the game's own channel on the
  no-input recording and differs on 12 of 4,875 frames. Those were not looked into.
- The fade of the music at the end is approximated. The game lowers each channel's volume by one
  step every 4 frames; the code scales the whole recording down in 11 equal steps instead.
- With B, the music and typing sounds were checked by start frame only, not by listening.
- The latest START the game still reacts to was not tested frame by frame; the code uses the
  same limit as the night scene (54 frames after the script ends).
- START was tested with one press per recording, and not combined with B.

# 02 – Title menus: "1player / 2players" and "Chip / Dale"

Continues `01_intro_title`. START on the title screen opens the player menu; "1player" leads to
the character menu; the final choice fades the screen to black. Everything still lives in
`obj_intro`. This step ends on the black screen, with the choice stored in `global.players`
and `global.p1_char`.

## What the original does

`p` is the frame on which a button goes down. The game always reacts on frame `p + 1`.

| Screen | Buttons | Result |
|---|---|---|
| Title | START | Player menu. The text row is replaced over 3 frames (`p+1`, `p+2`, `p+3`). Buttons are read again from `p + 3`. |
| Player menu | UP, DOWN or SELECT | Cursor jumps to the other line (it wraps, there is no key repeat). Move sound. |
| Player menu, cursor on 1player | START or A | Character menu. Text on `p+1`, the two faces from `p+2`. Buttons are read again from `p + 2`. |
| Player menu, cursor on 2players | START or A | Fade-out (below). Player 1 is Chip. |
| Character menu | UP, DOWN or SELECT | Cursor jumps to the other line. The chosen face lights up, the other one goes dark. Move sound. |
| Character menu | START or A | Fade-out (below). |

- B, LEFT and RIGHT do nothing on any of these screens. There is no way back to the previous menu.
- A cursor button and START/A on the same frame both count: the cursor moves first, then the choice is made.
- Fade-out, counted from the reaction frame `r = p + 1`: select sound on `r`, darker palettes on
  `r+4`, `r+8`, `r+12`, black from `r+16`. Buttons are ignored. The title music keeps playing
  until `r+23`, where the next screen's sound takes over. The next screen appears on `r+41`.
- On the character menu the two faces overlap the cursor by a few pixels, and the NES swaps the
  drawing order of its sprites every frame. Three pixels at x=66, y=213–217 therefore flicker.
  The parity follows the frame counter (`frame & 1`), not the moment the menu opened.

## Sound effects

There are two effects, and both play on the NES's second square-wave channel:

| Sound | Used for | Length |
|---|---|---|
| `snd_menu_select` | START on the title, START/A in both menus | 12 frames |
| `snd_menu_move` | cursor movement | 10 frames |

While an effect plays, the music loses that channel and gets it back afterwards. To reproduce
this, the title music is now split into two files that play together:

- `snd_title_theme` – the music **without** the second square channel (replaces the file from step 01),
- `snd_title_theme_sq2` – the second square channel alone.

The code sets the volume of `snd_title_theme_sq2` to 0 for the 12 or 10 frames of an effect. An
effect requested on frame `r` is audible from `r + 1`, like every sound in this game. A new
effect cuts off the one that is still playing.

## Assets

| File | Size | Sub-images |
|---|---|---|
| `assets/sprites/spr_menu_00..23.png` (or `spr_menu_strip24.png`) | 160x32 | 24, drawn at (48,188) over the title picture |
| `assets/sprites/spr_title_out_0..2.png` (or `spr_title_out_strip3.png`) | 256x240 | 3, the whole title picture in its three fade-out palettes |
| `assets/sounds/snd_title_theme.ogg` | 2880 frames | replaces the old file |
| `assets/sounds/snd_title_theme_sq2.ogg` | 2880 frames | new |
| `assets/sounds/snd_menu_select.ogg`, `snd_menu_move.ogg` | 12 / 10 frames | new |

`spr_menu` sub-images:

| Index | Content |
|---|---|
| 0, 1 | text being replaced (frames 1 and 2 after START) |
| 2, 3 | 1player / 2players, cursor on line 1 / line 2 |
| 4 | Chip / Dale text without faces (first frame) |
| 5, 6 | cursor on Chip, even / odd frame |
| 7, 8 | cursor on Dale, even / odd frame |
| 9, 10, 11 | "2players" chosen, fade steps 1–3 |
| 12–17 | Chip chosen, fade steps 1–3, each even / odd frame |
| 18–23 | Dale chosen, fade steps 1–3, each even / odd frame |

The fade-out palettes are not the fade-in palettes of step 01, which is why `spr_title_out` exists.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprite `spr_menu`**: Create Sprite, name it `spr_menu`, *Load Sprite*, pick
   `spr_menu_strip24.png` (the `_strip24` suffix splits it into 24 sub-images of 160x32).
   Untick **Remove Background** and **Smooth Edges** in the load dialog: the black must stay
   solid, because it covers "Press START button". Origin 0,0. Check that the sprite shows 24
   sub-images; if not, use *Edit Sprite → File → Create from Strip* with 24 images, 24 per row,
   160x32.
2. **Sprite `spr_title_out`**: same procedure with `spr_title_out_strip3.png` (3 sub-images of
   256x240, origin 0,0, Remove Background off).
3. **Sound `snd_title_theme`**: open the existing sound and load the new
   `snd_title_theme.ogg` over it. Keep the settings from step 01.
4. **Sounds `snd_title_theme_sq2`, `snd_menu_select`, `snd_menu_move`**: Create Sound, load the
   file, mono, 48000 Hz. Use the same kind and compression settings for `snd_title_theme_sq2`
   as for `snd_title_theme`, and do not choose "Streamed" for either: both must start on the
   same instant to stay in step.
5. **Code**: replace the three events of `obj_intro` with `gml/obj_intro_Create.gml`,
   `gml/obj_intro_Step.gml` and `gml/obj_intro_Draw.gml`. They are complete replacements for the
   step 01 versions.

Keys: Enter = START, Shift = SELECT, X = A, arrow keys = d-pad. They are set at the top of the
Step event.

## How it was checked

`tools/capture/sim.py` is a line-for-line Python port of the three events. It was run against
23 emulator recordings covering every button on both menus, the earliest accepted frames,
several buttons on one frame, a held button, and the menus reached after skipping the intro.

- Picture: 0 differing pixels on all 5,260 compared frames, up to the last black frame before the next screen.
- Sound timing: every frame on which the simulation requests an effect is a frame on which the
  game's sound driver starts one, and vice versa.
- The step 01 checks (natural run and 16 START-skip runs) still pass with the new code.

Not checked, because it cannot be checked from here:

- The GML itself has not been run in GameMaker; only the Python port has been run.
- How tightly GameMaker keeps the two music files in step. They are the same length to the
  sample, so they should not drift, but listen for it.
- The two music files added together differ slightly from the original mix (about 3% RMS),
  because the NES mixes its two square channels non-linearly.
- UP and DOWN held together cancel out in the emulator, and the code copies that. A real NES pad
  cannot produce this input, so the real behaviour is unknown.

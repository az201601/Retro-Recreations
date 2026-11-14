# Step 10 – level 1, section 1: hearts, getting hurt, lives, game over

The enemies now hurt the player. New in this step: the hearts, losing a life, the status screen
(SELECT), GAME OVER and the continue screen, and from there back into the level or back to the
title screen.

1. map and camera (step 05)
2. player movement (steps 06 and 07)
3. crates and bonus boxes (step 08)
4. enemies (step 09)
5. **health, death, heart display, status screen, game over (this step)**

## What was confirmed in the original

- **Hearts.** 3 hearts. They are shown at the bottom, Chip's on the left (face at 16,201, hearts
  from 16,209), Dale's on the right (from 208). A heart goes one frame after the hit. The face
  disappears when the last life is gone.
- **Touching an enemy** (flyer, cook, fork): one heart less, a sound, the player is thrown up
  and 2 pixels per frame away from the enemy, without control, until the jump is over. For 64
  frames nothing can hurt again; the picture is shown 2 frames out of 4 meanwhile.
- **Touching what the flyer drops** costs no heart: the player is stunned for 120 frames
  (cannot move, slides half a pixel per frame while in the air), with a sound of 97 frames and
  a star going round the head (7 places, 4 frames each). The star takes a place in the object
  list like an enemy.
- Nothing is touched while hiding under a crate, during the 16 frames of a throw, or while
  walking out of the section.
- **Last heart:** the life is taken at once, the player is thrown up as usual and then falls
  through everything out of the picture. From there on it is the same as a fall into the pit
  (60 frames wait, fade, the section starts again with 3 hearts).
- **Status screen (SELECT).** Opens only while the game is running. The level stays for one
  frame, 2 black frames, then the screen: the character, bonus boxes collected (two digits),
  lives left besides the one in play. The sound goes on for 4 frames and is then paused. A second
  SELECT closes it, at the earliest 8 frames after it opened: 13 black frames, then the level
  and the sound go on. The buttons held on the closing frame count for the first game frame.
- **GAME OVER** (no life left). The bonus count is set to 0. 85 frames after the fall the level
  music stops and the screen appears; the tune (180 frames) starts on the next frame. The words
  appear at y = 89 and sink 1 pixel every 4 frames to y = 121. Buttons do nothing.
- **Continue screen** (3 credits at the start). It follows 374 frames after the fall. No
  music. UP or DOWN moves the arrow (sound, 14 frames), A chooses (sound, 17 frames); START,
  SELECT and B do nothing. Buttons count from the 20th frame of the screen.
  - **CONTINUE:** one credit less, 3 lives. The dizzy character gets up with a jump and runs off
    to the right (102 frames); the level starts again 145 frames after the button, with its
    music from the beginning.
  - **END:** the character is thrown out to the lower left (42 frames); the title screen takes
    over 84 frames after the button.
  - **No credit left:** no continue screen. GAME OVER stays 61 frames longer and the title
    screen follows.
- The fade-out of these screens uses other colours than the fade-in, as in the level.
- Dale: the same on the same frames. His status screen half is 80 pixels further right.

### Corrections to earlier steps

- A landing sound is not asked for while another effect is still playing (step 09 only left it
  out while another one was *about* to start).
- Walking out of the section, the player no longer touches enemies.

## Not in this step

- A second player. Extra lives and what the bonus count gives. The heart that flies to the lives
  count on the status screen when a life is gained.
- **Sprites per line** and **dropped frames** are handled as in step 09 (the port draws
  everything and never leaves a frame out). The new recordings have 10 dropped frames in 5 runs.

## Assets

All new. Origin 0,0 everywhere.

| File | Size | Sub-images |
|---|---|---|
| `spr_chip_hurt_strip168.png` | 8x8 | 12 tiles × 2 directions × 7 brightness steps (pictures 14 hurt, 15 stunned) |
| `spr_dale_hurt_strip168.png` | 8x8 | the same for Dale |
| `spr_hud_strip21.png` | 8x8 | Chip's face, heart, Dale's face × 7 brightness steps |
| `spr_star_strip7.png` | 8x8 | the star in the level, 7 brightness steps |
| `spr_status_strip4.png` | 256x240 | status screen without numbers: character × 2 + sprite order |
| `spr_status_digit_strip10.png` | 8x8 | digits 0–9 |
| `spr_gameover_bg_strip7.png` | 256x240 | GAME OVER without the words, 7 brightness steps |
| `spr_gameover_text_strip7.png` | 64x16 | the words |
| `spr_continue_bg_strip7.png` | 256x240 | continue screen without arrow, number and character; transparent where the character shows through |
| `spr_continue_arrow_strip7.png` | 8x8 | the arrow |
| `spr_continue_digit_strip28.png` | 8x8 | digit × 7 + brightness step (digits 0–3) |
| `spr_continue_wake_strip6.png` | 32x48 | dizzy character with star while the screen fades in: character × 3 + step |
| `spr_continue_star.png` | 8x8 | the star on the continue screen |
| `snd_hurt.ogg` | 24 frames (0.40 s) | hurt: 2nd square for 16 frames, noise for 24 |
| `snd_stun.ogg` | 97 frames (1.62 s) | stunned |
| `snd_gameover.ogg` | 180 frames (3.00 s) | GAME OVER tune, all channels |
| `snd_cursor.ogg` | 14 frames (0.23 s) | arrow of the continue screen |
| `snd_confirm.ogg` | 17 frames (0.28 s) | choice on the continue screen |

Brightness steps as before: 0–2 fade-in, 3 normal, 4–6 fade-out. All assets of steps 01 to 09
are still needed and unchanged.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprites** (new, names without `_stripN`): `spr_chip_hurt`, `spr_dale_hurt`, `spr_hud`,
   `spr_star`, `spr_status`, `spr_status_digit`, `spr_gameover_bg`, `spr_gameover_text`,
   `spr_continue_bg`, `spr_continue_arrow`, `spr_continue_digit`, `spr_continue_wake`,
   `spr_continue_star`. Origin 0,0, **Remove Background** and **Smooth Edges** unticked.
2. **Sounds** (new): `snd_hurt`, `snd_stun`, `snd_gameover`, `snd_cursor`, `snd_confirm`: mono,
   48000 Hz, not streamed.
3. **Scripts**: replace `scr_pl_touch`; new: `scr_pl_enemy_touch`. The others are unchanged.
4. **Object `obj_player`**: replace Create, User Defined 0 and User Defined 1.
5. **Object `obj_enemy`**: only a comment changed in Create.
6. **Object `obj_stage1`**: replace Create, End Step, Draw and User Defined 0. Two new events:
   - **Other → User Defined 1** ← `gml/obj_stage1_User1.gml` (the sound effects, moved out of
     End Step)
   - **Other → User Defined 2** ← `gml/obj_stage1_User2.gml` (GAME OVER and the continue screen)
7. `obj_crate` and `obj_intro` stay as they are.

### What changed in the code

- **`obj_player`**: `p_hp`, `p_inv`, `p_flash`, `p_ghost`, `p_push`, `p_stun`; states 9 / 10
  (hurt) and 14 / 15 (stunned); pictures 14 and 15, whose tiles are in a second sprite
  (`p_spr2`, tile numbers from `p_tbase`).
- **`obj_stage1` End Step** now starts with the status screen (`lv_stat`, `lv_view`) and hands
  over to User Defined 2 while `lv_go >= 2`. The level clock `lt` stands still on both.
- **Back to the title:** User Defined 2 creates `obj_intro` again and sets its `frame` to
  `fade_start + 18`: the black frame 2 frames before it asks for the title music. The stage then
  destroys itself and its objects. Nothing in `obj_intro` had to change.
- **Draw** draws, in this order of checks: GAME OVER / continue screen, black or the status
  screen, the level. The hearts and the star are part of the level's sprite order.

## How it was checked

`tools/capture/sim_hurt.py` is a Python port of this step's GML. It was run with the same
buttons as 34 new emulator recordings (27 with Chip, 7 with Dale): the route through the section
without avoiding anything, a death by enemies, 17 runs of random buttons near enemies, the status
screen opened and closed (also while moving and with a bonus count), three falls with GAME OVER,
the continue screen with the arrow moved and CONTINUE, with END, and four game overs in a row
until no credit is left.

Compared on every frame: the player's memory values (state, position, speed, picture, hearts,
the no-hurt counter, flags), camera, lives, bonus count, every place of the object list, the
start frame of every sound, who has the sound channels, every sprite with its order, and the
whole picture, including the status, GAME OVER and continue screens.

| Run | Frames compared | Frames with a difference |
|---|---|---|
| `sim_hurt.py` (34 new recordings) | 74,498 | 0 |
| `sim_hurt.py --old` (61 recordings of steps 06–09) | 47,405 | 0 |

Sounds started in the new recordings, each on the same frame as the original: hurt 34, stunned
8, arrow 8, choice 2, GAME OVER tune 3. Three runs end at the title screen.

Limits of the check:

- The GML itself was not run; the Python port follows it line by line.
- The sound check compares start frames and channel use, not the samples. The five new sound
  files were cut from the recordings at frames confirmed by the sound register writes.
- The continue screen was recorded with 3, 2 and 1 credits. The digit 0 is only ever seen fading
  out; its fade-in images are copies of the normal one and are never shown.
- The title screen after END is not compared picture by picture. Its timing was read from the
  recording (music 87 frames after the button, fade-in steps at 91, 95, 99, 103) and matches
  `obj_intro` from `fade_start + 18` on.
- The full lengths of the hurt and stun sounds (24 and 97 frames) were measured by asking the
  game's sound driver for them directly. In the recordings the stun sound is always cut off
  earlier by another sound.

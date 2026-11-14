# Step 07 – level 1, section 1: Dale

Step 06 put Chip into the dining room. This step adds Dale: when Dale was picked in the
character menu (`global.p1_char == 1`, set by `obj_intro` since step 02), the player is Dale.

It is a small step. Only two events of `obj_player` change and one sprite is added. Everything
else stays as in step 06.

## What was confirmed in the original

- **Dale moves exactly like Chip.** The nine recordings that have a Chip twin were repeated
  with Dale chosen in the menu and the same buttons. On all 5,870 frames the player's state,
  position, speed, picture number, direction, height, the camera and the lives are identical
  to Chip's. So are the frame the level starts on and the timing of the fall and the exit.
- **Only the pictures differ.** Dale has his own tiles (33 instead of Chip's 31), and they
  are put together at slightly different offsets. The 7 poses are the same ones.
- **The colours are the same.** The sprite palettes are identical in both cases, through the
  fades as well.
- **The landing sound is the same.**
- The heart display is on the right side of the screen for Dale (x 208–224) and on the left for
  Chip (x 16–32), with a different face tile. It is not part of this step; it comes with the
  health step.

## Assets

| File | Size | Sub-images |
|---|---|---|
| `spr_dale_strip462.png` | 8x8 | 33 tiles × 2 directions × 7 brightness steps: index = (tile × 2 + (0 right, 1 left)) × 7 + step |

Same layout as `spr_chip`. The assets of steps 05 and 06 are still needed.

## Transfer into GameMaker: Studio 1.4.1760

1. **Sprite `spr_dale`**: load `spr_dale_strip462.png`. Untick **Remove Background** and
   **Smooth Edges**, origin 0,0. It must have 462 sub-images of 8x8; if not, use *Edit Sprite →
   File → Create from Strip* (462 images, 8 wide, 8 high, 462 per row).
2. **Object `obj_player`**: replace two events:
   - **Create** ← `gml/obj_player_Create.gml`
   - **Draw** ← `gml/obj_player_Draw.gml`

   The User Defined 0 event, the scripts, `obj_stage1` and `obj_intro` do not change.

### What changed in the code

- Create: the picture tables at the end are now inside `if (global.p1_char == 0) … else …`,
  one set for each character, and the new variable `p_spr` holds `spr_chip` or `spr_dale`.
  Chip's tables are unchanged.
- Draw: `draw_sprite(spr_chip, …)` became `draw_sprite(p_spr, …)`.

To try Dale without the menu, set `global.p1_char = 1;` before `obj_stage1` is created.

With 2 players the menu sets `global.p1_char` to 0, so player 1 is Chip. The second player is
not part of the recreation yet.

## How it was checked

`tools/capture/sim_player.py` now runs the port with Dale's tables and sprite against the nine
Dale recordings (the `dl_` runs), next to the twelve Chip recordings of step 06.

On the 4,775 compared Dale frames:

- Player memory: 0 differences.
- Sprite tiles: every tile the port draws is in the NES sprite list at the same place. 0
  differences.
- Picture: 0 differing pixels, outside the places step 06 lists (other sprites, changed crates).
- Landing sound: same frames as the NES.

The Chip recordings were run again and still show 0 differences (10,120 frames in total).

What was not checked:

- The GML has not been run in GameMaker; only the Python port has.
- Dale's eyes-closed picture was only seen facing left, like Chip's; the right-facing one is
  its mirror image.
- The limits listed in the step 06 README apply here too.
- In the three exit recordings the other sounds of the level fall on different frames with
  Dale than with Chip, although the player does the same. The cause was not looked for; it
  points at the enemies and belongs to that step.

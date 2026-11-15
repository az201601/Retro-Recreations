/// scr_lv_block(row, column)
// Called by obj_stage1 (or "with (stage)"). The kind of block (0 nothing, 1 can be stood on, 2 solid) an ENEMY
// finds in a column. The original only remembers 16 columns, up to the one 248 pixels right of the camera, so
// in the column at the left edge of the screen an enemy finds the blocks of the column 16 further right.
// The kitchen has two floors (rows 0-14 the upper, 15-29 the lower one) and the original keeps only 15 rows:
// row b of the lower floor while the camera is at most b * 16 + 8 above it, else row b of the upper floor.
// An enemy further away than that finds the blocks of the other floor.
var r = argument0;
var c = argument1;
if (lv_sec == 1)
{
    r = r mod 15;
    if (lv_cam_y >= r * 16 + 8) r += 15;
}
if (c < ((lv_cam_x + 248) div 16) - 15) c += 16;
if (c < 0 || c > 127 || r < 0) return 0;
return lv_kind[r, c];

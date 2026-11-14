/// scr_lv_block(row, column)
// Called by obj_stage1 (or "with (stage)"). The kind of block (0 nothing, 1 can be stood on, 2 solid) an ENEMY
// finds in a column. The original only remembers 16 columns, up to the one 248 pixels right of the camera, so
// in the column at the left edge of the screen an enemy finds the blocks of the column 16 further right.
var c = argument1;
if (c < ((lv_cam_x + 248) div 16) - 15) c += 16;
if (c < 0 || c > 127) return 0;
return lv_kind[argument0, c];

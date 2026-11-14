/// scr_pl_row(y, kind)
// Called by obj_player. Looks at the row of 16x16 blocks that contains the height y (a screen position),
// in every column the player's 12-pixel-wide body touches.
// Returns true if one of those blocks is of the given kind or higher (1 = can be stood on, 2 = solid).
// (Only what is on the screen counts: in the kitchen's shaft the floor below the picture is not there.)
if (argument0 < 0 || argument0 > 239) return false;
var r = (argument0 + stage.lv_cam_y) div 16;    // lv_cam_y: 0 except in the kitchen
if (r >= stage.lv_rows) return false;
var wx = p_x + stage.lv_cam_x;                  // the player's position in the section
var c0 = (wx - 6) div 16;
var c1 = (wx + 5) div 16;
var c;
for (c = c0; c <= c1; c += 1)
{
    if (c >= 0 && c < 128)
    {
        if (stage.lv_kind[r, c] >= argument1) return true;
    }
}
return false;

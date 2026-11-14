/// scr_en_row(y, kind)
// Called by obj_enemy. Looks at the row of 16x16 blocks that contains the height y, in every column the body
// touches. Returns true if one of them is of the given kind or higher (1 = can be stood on, 2 = solid).
// (The original looks one camera step too far right: lv_cam_x - lv_cam_show.)
var r = floor(argument0 / 16);
if (r < 0 || r > 14) return false;
var wx = e_wx + stage.lv_cam_x - stage.lv_cam_show;
var c0 = floor((wx - e_w) / 16);
var c1 = floor((wx + e_w - 1) / 16);
var c, k;
for (c = c0; c <= c1; c += 1)
{
    with (stage) k = scr_lv_block(r, c);
    if (k >= argument1) return true;
}
return false;

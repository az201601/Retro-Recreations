/// scr_en_wall()
// Called by obj_enemy: true if the edge of its body it moves towards is in a solid block; it is put next to it.
// (The original looks one camera step too far right: lv_cam_x - lv_cam_show.)
if (e_xv == 0 || e_y < 1 || e_y > 255) return false;
var xx;
if (e_xv > 0) xx = e_wx + e_w; else xx = e_wx - e_w;
var sx = xx - stage.lv_cam_show;
if (sx < 0 || sx > 255) return false;
var d = stage.lv_cam_x - stage.lv_cam_show;
var c = floor((xx + d) / 16);
var r0 = max(e_y - e_h, 0) div 16;
var r1 = min(((e_y + 15) div 16) - 1, 14);
var r, k;
for (r = r0; r <= r1; r += 1)
{
    with (stage) k = scr_lv_block(r, c);
    if (k >= 2)
    {
        if (e_xv > 0) e_wx = c * 16 - e_w - d;
        else e_wx = floor((xx + d - 1) / 16) * 16 + 16 + e_w - d;
        return true;
    }
}
return false;

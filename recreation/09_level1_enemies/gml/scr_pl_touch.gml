/// scr_pl_touch()
// Called by obj_player at the start of its frame. If the body (where the previous frame left it) is in a
// block with a bonus box, the box is collected. One box per frame; the search goes from the top row down,
// in each row from right to left.
if (p_y < 0 || p_y > 255) return false;
var wx = p_x + stage.lv_cam_x;
var r0 = max(p_y - p_h, 0) div 16;
var r1 = min(p_y div 16, 14);
var c0 = (wx - 6) div 16;
var c1 = (wx + 5) div 16;
var r, c;
for (r = r0; r <= r1; r += 1)
{
    for (c = c1; c >= c0; c -= 1)
    {
        if (c >= 0 && c < 128)
        {
            if (stage.lv_box[r, c] == 3)
            {
                scr_pl_open_box(c, r, 0);
                stage.lv_bonus = min(stage.lv_bonus + 1, 99);
                p_snd = 3;
                return true;
            }
        }
    }
}
return false;

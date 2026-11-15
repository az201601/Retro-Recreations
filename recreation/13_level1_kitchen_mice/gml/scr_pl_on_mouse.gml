/// scr_pl_on_mouse()
// Called by obj_player. A stunned mouse carries the player like a block: lying on the ground (state 6), and also
// while it is still in the air from the crate's hit (state 5).
// True if the player's middle is 14 pixels or less from the mouse's (6 + 8, the two half widths) and his feet
// line is anywhere from 25 above the mouse's feet line (standing on it) down to less than his own body height
// below it (22 standing, 16 crouching); he is then put on top of it. The fraction of his height stays.
// Uses where the player was before this frame's step sideways, and where the mouse was after the frame before.
var i, e;
for (i = 0; i < stage.lv_en_n; i += 1)
{
    e = stage.lv_en[i];
    if (e.e_kind != 5 || (e.e_state != 5 && e.e_state != 6) || e.e_gone) continue;
    if (abs(e.e_wx - stage.lv_cam_x - p_x) <= 14 && p_y >= e.e_y - 25 && p_y < e.e_y + p_h)
    {
        p_y = e.e_y - 25;
        return true;
    }
}
return false;

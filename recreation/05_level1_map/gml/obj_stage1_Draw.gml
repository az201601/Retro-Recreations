/// obj_stage1 : Draw
// ---- section 1: the dining room ---------------------------------------------------------
if (!lv_done)
{
    var sub = -1;                               // brightness: 0..2 fade-in, 3 normal, 4..6 fade-out, -1 = black
    if (lt >= 5) sub = min((lt - 5) div 4, 3);  // fade-in steps on lt == 5, 9, 13, full brightness from 17
    if (lv_exit_t >= 0 && lt >= lv_exit_t + 5)
    {
        sub = 4 + ((lt - lv_exit_t - 5) div 4); // fade-out steps 5, 9 and 13 frames after the exit
        if (sub > 6) sub = -1;
    }
    if (sub >= 0)
    {
        // the background is cut into 8 screens of 256 pixels; at most two of them are visible
        var scr = lv_cam_x div 256;
        draw_sprite(spr_lv1a_bg, scr * 7 + sub, scr * 256 - lv_cam_x, 0);
        if ((lv_cam_x mod 256) != 0) draw_sprite(spr_lv1a_bg, (scr + 1) * 7 + sub, (scr + 1) * 256 - lv_cam_x, 0);
        // the NES shows nothing in the left-most 8 pixels of this level
        draw_set_color(c_black);
        draw_rectangle(0, 0, 7, 239, false);
        draw_set_color(c_white);
    }
}

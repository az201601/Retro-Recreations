/// obj_stage1 : Draw
// ---- section 1: the dining room ---------------------------------------------------------
// (the player draws itself afterwards: obj_player has a lower depth)
if (lv_bright >= 0)
{
    // the background is cut into 8 screens of 256 pixels; at most two of them are visible
    var scr = lv_cam_show div 256;
    draw_sprite(spr_lv1a_bg, scr * 7 + lv_bright, scr * 256 - lv_cam_show, 0);
    if ((lv_cam_show mod 256) != 0) draw_sprite(spr_lv1a_bg, (scr + 1) * 7 + lv_bright, (scr + 1) * 256 - lv_cam_show, 0);
    // the NES shows nothing in the left-most 8 pixels of this level
    draw_set_color(c_black);
    draw_rectangle(0, 0, 7, 239, false);
    draw_set_color(c_white);
}

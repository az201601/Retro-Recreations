/// obj_stage1 : Draw
// ---- section 1: the dining room ---------------------------------------------------------
// Draws everything of the section: obj_player and obj_crate have no Draw event of their own, because
// which of them is in front changes from frame to frame.
if (lv_bright >= 0)
{
    // the background is cut into 8 screens of 256 pixels; at most two of them are visible
    var scr = lv_cam_show div 256;
    draw_sprite(spr_lv1a_bg, scr * 7 + lv_bright, scr * 256 - lv_cam_show, 0);
    if ((lv_cam_show mod 256) != 0) draw_sprite(spr_lv1a_bg, (scr + 1) * 7 + lv_bright, (scr + 1) * 256 - lv_cam_show, 0);

    // where a crate or bonus box is gone: a 16x16 piece copied from another place of the background picture
    // that looks like what is behind the box (or, where a crate had a bonus inside, a bonus box).
    // The piece appears one frame after the box went.
    var i, b, dc, dr;
    for (i = 0; i < lv_open_n; i += 1)
    {
        if (lt - lv_open_t[i] >= 1)
        {
            b = lv_open_i[i];
            if (lv_open_k[i]) { dc = lv_rbox_c; dr = lv_rbox_r; }
            else { dc = lv_bdc[b]; dr = lv_bdr[b]; }
            draw_sprite_part(spr_lv1a_bg, (dc div 16) * 7 + lv_bright, (dc mod 16) * 16, dr * 16, 16, 16,
                             lv_bc[b] * 16 - lv_cam_show, lv_br[b] * 16);
        }
    }

    if (!lv_done)
    {
        // The NES lists its sprites forwards on one frame and backwards on the next, so the player is in
        // front of the crates on one frame and behind them on the next. It only shows where they overlap
        // (the one pixel row the carried crate and the head share).
        if ((lv_fc & 1) != 0)
        {
            with (pl) { p_rev = false; event_user(1); }
            for (i = 0; i < lv_cr_n; i += 1) { with (lv_cr[i]) event_user(1); }
        }
        else
        {
            for (i = 0; i < lv_cr_n; i += 1) { with (lv_cr[i]) event_user(1); }
            with (pl) { p_rev = true; event_user(1); }
        }
    }

    // the NES shows nothing in the left-most 8 pixels of this level, sprites included
    draw_set_color(c_black);
    draw_rectangle(0, 0, 7, 239, false);
    draw_set_color(c_white);
}

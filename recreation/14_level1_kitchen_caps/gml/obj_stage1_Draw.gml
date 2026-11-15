/// obj_stage1 : Draw
var i, j, n, o, b, k, t, dc, dr, yy, y0, y1;
// ---- GAME OVER and the continue screen -------------------------------------------------------
if (lv_go >= 2)
{
    b = go_bright;
    t = lv_go_t;
    if (b >= 0 && lv_go == 2)
    {
        // the words appear at y = 89 and sink one pixel every 4 frames from t == 46, down to y = 121
        draw_sprite(spr_gameover_bg, b, 0, 0);
        draw_sprite(spr_gameover_text, b, 96, 89 + min(max((t - 42) div 4, 0), 32));
    }
    else if (b >= 0)
    {
        // The continue screen. The character is BEHIND the picture (spr_continue_bg is transparent where the
        // character can be seen): dizzy with a star going round its head; after CONTINUE it gets up with a
        // jump and runs off to the right, after END it is thrown out to the lower left.
        var show = true;
        var pic = 15;
        var px = 112;
        var py = 160;
        if (lv_go == 3 && b < 3) show = false;          // fading in: see spr_continue_wake below
        if (lv_go == 4 && t >= 2)
        {
            if (t - 2 < go_cn) { pic = go_cp[t - 2]; px = go_cx[t - 2]; py = go_cy[t - 2]; } else show = false;
        }
        if (lv_go == 5 && t >= 2)
        {
            if (t - 2 < go_en) { pic = go_ep[t - 2]; px = go_ex[t - 2]; py = go_ey[t - 2]; } else show = false;
        }
        if (show)
        {
            // the player's own Draw code, at full brightness
            lv_bright = 3;
            with (pl)
            {
                s_x = px;  s_y = py;  s_pic = pic;  s_face = 1;  s_vis = true;  s_blink = false;
                p_rev = (stage.lv_ord != 0);
                event_user(1);
                s_vis = false;
            }
            lv_bright = -1;
            if (lv_go == 3 || t < 2)
            {
                // the star: 7 places, 4 frames each, from t == 20 of the continue screen
                if (lv_go == 3) k = t; else k = go_t3 + t;
                if (k >= 20) k = ((k - 20) div 4) mod 7; else k = 0;
                draw_sprite(spr_continue_star, 0, go_sx[k], go_sy[k]);
            }
        }
        draw_sprite(spr_continue_bg, b, 0, 0);
        if (lv_go == 3 && b < 3) draw_sprite(spr_continue_wake, global.p1_char * 3 + b, 96, 120);
        draw_sprite(spr_continue_arrow, b, 80, 88 + 16 * s_cur);
        draw_sprite(spr_continue_digit, s_credits * 7 + b, 192, 184);
    }
    exit;
}
// ---- the status screen (SELECT) -----------------------------------------------------------------
if (lv_view == 0) exit;         // black
if (lv_view == 2)
{
    // Chip's half is on the left, Dale's 80 pixels further right. The numbers: bonus boxes (two digits, no
    // leading zero) and the lives left besides the one in play.
    var ox = 80 * global.p1_char;
    draw_sprite(spr_status, global.p1_char * 2 + lv_stat_ord, 0, 0);
    if (lv_bonus >= 10) draw_sprite(spr_status_digit, lv_bonus div 10, 96 + ox, 153);
    draw_sprite(spr_status_digit, lv_bonus mod 10, 104 + ox, 153);
    draw_sprite(spr_status_digit, max(lv_lives - 1, 0), 104 + ox, 177);
    exit;
}
// ---- the level: the dining room (lv_sec == 0) or the kitchen (lv_sec == 1) --------------------
// Draws everything of the section: obj_player, obj_crate, obj_enemy and obj_item have no Draw event of their own, because
// which of them is in front changes from frame to frame.
if (lv_bright >= 0)
{
    // the background is cut into 8 screens of 256 pixels; at most two of them are visible
    var scr = lv_cam_show div 256;
    if (lv_sec == 0)
    {
        draw_sprite(spr_lv1a_bg, scr * 7 + lv_bright, scr * 256 - lv_cam_show, 0);
        if ((lv_cam_show mod 256) != 0) draw_sprite(spr_lv1a_bg, (scr + 1) * 7 + lv_bright, (scr + 1) * 256 - lv_cam_show, 0);
    }
    else if (lv_cam_yshow == 240 && lv_cam_yold == 240)
    {
        // the kitchen's lower floor: pictures 0..5 of spr_lv1b_bg, from the left
        draw_sprite(spr_lv1b_bg, scr * 7 + lv_bright, scr * 256 - lv_cam_show, 0);
        if ((lv_cam_show mod 256) != 0) draw_sprite(spr_lv1b_bg, (scr + 1) * 7 + lv_bright, (scr + 1) * 256 - lv_cam_show, 0);
    }
    else if (lv_cam_yshow == 0 && lv_cam_yold == 0)
    {
        // its upper floor: pictures 6..8, the first of them above picture 5
        draw_sprite(spr_lv1b_bg, (scr + 1) * 7 + lv_bright, scr * 256 - lv_cam_show, 0);
        if ((lv_cam_show mod 256) != 0) draw_sprite(spr_lv1b_bg, (scr + 2) * 7 + lv_bright, (scr + 1) * 256 - lv_cam_show, 0);
    }
    else
    {
        // The shaft between them (the camera stands at x = 1280): picture 6 above picture 5.
        // The NES holds one screen height of picture, in 15 rows of 16 pixels, and replaces a row by the one 240
        // pixels higher up once the camera has been less than 8 pixels below the row's top edge. Until then a
        // row at the top edge of the screen still shows the lower floor, and afterwards the same row at the
        // bottom edge already shows the upper one. That is reproduced here.
        // (The NES takes two frames to replace a row and shows it half-replaced in between; here it changes
        // at once.)
        for (b = 0; b < 15; b += 1)
        {
            if (lv_cam_yold < b * 16 + 8) k = 6; else k = 5;
            for (j = 0; j < 2; j += 1)
            {
                yy = b * 16 + 240 * j - lv_cam_yshow;       // where the row is on the screen: once or twice, clipped
                y0 = max(yy, 0);
                y1 = min(yy + 16, 240);
                if (y1 > y0) draw_sprite_part(spr_lv1b_bg, k * 7 + lv_bright, 0, b * 16 + y0 - yy, 256, y1 - y0, 1280 - lv_cam_show, y0);
            }
        }
    }

    // where a crate or bonus box is gone: a 16x16 piece copied from another place of the background picture
    // that looks like what is behind the box (or, where a crate had a bonus inside, a bonus box).
    // The piece appears one frame after the box went.
    for (i = 0; i < lv_open_n; i += 1)
    {
        if (lt - lv_open_t[i] >= 1)
        {
            b = lv_open_i[i];
            if (lv_sec == 0)
            {
                if (lv_open_k[i]) { dc = lv_rbox_c; dr = lv_rbox_r; }
                else { dc = lv_bdc[b]; dr = lv_bdr[b]; }
                draw_sprite_part(spr_lv1a_bg, (dc div 16) * 7 + lv_bright, (dc mod 16) * 16, dr * 16, 16, 16,
                                 lv_bc[b] * 16 - lv_cam_show, lv_br[b] * 16);
            }
            else
            {
                // The kitchen: rows 0-14 are the upper floor (pictures 6..8 of spr_lv1b_bg, for the columns from 80
                // on), rows 15-29 the lower one (pictures 0..5).
                if (lv_open_k[i]) { dc = lv_rbox2_c; dr = lv_rbox2_r; }
                else { dc = lv_bdc2[b]; dr = lv_bdr2[b]; }
                if (dr < 15) k = dc div 16 + 1; else k = dc div 16;
                // In the shaft a row of the screen shows one floor or the other (see above): the piece is drawn
                // only where its own floor is shown.
                yy = lv_br2[b] mod 15;
                if ((lv_br2[b] < 15) == (lv_cam_yold < yy * 16 + 8))
                {
                    for (j = 0; j < 2; j += 1)
                    {
                        y0 = yy * 16 + 240 * j - lv_cam_yshow;
                        if (y0 > -16 && y0 < 240)
                        {
                            draw_sprite_part(spr_lv1b_bg, k * 7 + lv_bright, (dc mod 16) * 16, (dr mod 15) * 16, 16, 16,
                                             lv_bc2[b] * 16 - lv_cam_show, y0);
                        }
                    }
                }
            }
        }
    }

    if (!lv_done)
    {
        // The NES lists its sprites (the player's, then those of the crates and enemies in the order of the
        // object list) forwards on one frame and backwards on the next, so what is in front changes with every
        // frame: where things overlap they flicker, as in the original.
        // (The NES shows at most 8 sprites on a picture line and leaves the rest out; here all are drawn.)
        // An object that left on this frame is still shown once, although its place may already be taken again.
        n = 0;
        for (j = 3; j < 12; j += 1)
        {
            for (i = 0; i < lv_cr_n; i += 1) { o = lv_cr[i]; if (o.c_slot == j) { lv_dr[n] = o; n += 1; } }
            for (i = 0; i < lv_en_n; i += 1) { o = lv_en[i]; if (o.e_slot == j) { lv_dr[n] = o; n += 1; } }
            for (i = 0; i < lv_it_n; i += 1) { o = lv_it[i]; if (o.e_slot == j) { lv_dr[n] = o; n += 1; } }
            if (pl.s_star >= 0 && pl.s_star_slot == j) { lv_dr[n] = noone; n += 1; }      // the star over a stunned player
            for (i = 0; i < lv_en_n; i += 1)                                              // ... over a stunned mouse
            {
                o = lv_en[i];
                if (o.s_star >= 0 && o.s_star_slot == j) { lv_dr[n] = -100 - i; n += 1; }
            }
        }
        // The star and the hearts are part of the list: the hearts come last.
        var mx, my;
        var sx = pl.s_x;
        var sy = pl.s_y;
        if (pl.s_star >= 0) { sx += go_sx[pl.s_star] - 112; sy += go_sy[pl.s_star] - 160; }
        var star = (pl.s_star >= 0 && sy >= 1 && sx >= 0 && sx <= 255);
        if (lv_ord != 0)
        {
            with (pl) { p_rev = false; event_user(1); }
            for (i = 0; i < n; i += 1)
            {
                if (lv_dr[i] == noone) { if (star) draw_sprite(spr_star, lv_bright, sx, sy); }
                else if (lv_dr[i] <= -100)
                {
                    // the star of a stunned mouse goes round 2 pixels higher than the player's; while the mouse is
                    // carried or flies (upside down) it is 25 pixels lower, at the mouse's head
                    o = lv_en[-100 - lv_dr[i]];
                    mx = o.s_x + go_sx[o.s_star] - 112;
                    my = o.s_y + go_sy[o.s_star] - 160 - 2;
                    if (o.s_flip) my += 25;
                    if (my >= 1 && my < 240 && mx >= 0 && mx <= 255) draw_sprite(spr_star, lv_bright, mx, my);
                }
                else { with (lv_dr[i]) event_user(1); }
            }
        }
        // the hearts: Chip's face and hearts are on the left, Dale's on the right; one heart per p_hp.
        // The face goes with the last life.
        var hx = 16;
        var hf = 0;
        if (global.p1_char != 0) { hx = 208; hf = 2; }
        if (s_lives > 0) draw_sprite(spr_hud, hf * 7 + lv_bright, hx, 201);
        for (i = 0; i < s_hp; i += 1) draw_sprite(spr_hud, 7 + lv_bright, hx + 8 * i, 209);
        if (lv_ord == 0)
        {
            for (i = n - 1; i >= 0; i -= 1)
            {
                if (lv_dr[i] == noone) { if (star) draw_sprite(spr_star, lv_bright, sx, sy); }
                else if (lv_dr[i] <= -100)
                {
                    // the star of a stunned mouse goes round 2 pixels higher than the player's; while the mouse is
                    // carried or flies (upside down) it is 25 pixels lower, at the mouse's head
                    o = lv_en[-100 - lv_dr[i]];
                    mx = o.s_x + go_sx[o.s_star] - 112;
                    my = o.s_y + go_sy[o.s_star] - 160 - 2;
                    if (o.s_flip) my += 25;
                    if (my >= 1 && my < 240 && mx >= 0 && mx <= 255) draw_sprite(spr_star, lv_bright, mx, my);
                }
                else { with (lv_dr[i]) event_user(1); }
            }
            with (pl) { p_rev = true; event_user(1); }
        }
        // In the hole of the kitchen wall the player is behind the wall: the wall around the hole (48 x 64 pixels
        // at 2000, 128 of the kitchen) is drawn again over the player. spr_lv1b_hole is transparent where the
        // player can be seen (inside the hole).
        if (lv_sec == 1 && pl.s_behind)
        {
            if (lv_cam_show >= 1792 && lv_cam_yshow <= 128) draw_sprite(spr_lv1b_hole, lv_bright, 2000 - lv_cam_show, 128 - lv_cam_yshow);
        }
    }

    // the NES shows nothing in the left-most 8 pixels of this level, sprites included
    draw_set_color(c_black);
    draw_rectangle(0, 0, 7, 239, false);
    draw_set_color(c_white);
}

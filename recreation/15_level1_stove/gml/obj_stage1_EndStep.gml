/// obj_stage1 : End Step
var i, n, cr, en, j, k, col;

// ---- 0) controller ------------------------------------------------------------
var pad = 0;
if (keyboard_check(vk_enter)) pad |= 1;     // START
if (keyboard_check(vk_shift)) pad |= 2;     // SELECT
if (keyboard_check(ord("X"))) pad |= 4;     // A
if (keyboard_check(vk_up))    pad |= 8;     // UP
if (keyboard_check(vk_down))  pad |= 16;    // DOWN
if (keyboard_check(ord("Z"))) pad |= 32;    // B
if (keyboard_check(vk_left))  pad |= 64;    // LEFT
if (keyboard_check(vk_right)) pad |= 128;   // RIGHT
var pressed = pad & (pad_prev ^ 255);       // buttons that went down on this frame
pad_prev = pad;

// ---- 0a) GAME OVER and the continue screen have their own code (User Defined 2) ---------------
if (lv_go >= 2) { go_pressed = pressed; event_user(2); exit; }

// ---- 0b) the status screen (SELECT): the game stands still --------------------------------------
// SELECT opens it while the game is running (not during the fades). The level is shown for one more frame,
// then 2 black frames, then the screen. The sounds go on for 4 frames and are then paused.
// SELECT closes it, at the earliest 8 frames after it opened: 13 black frames, on the last of them the game
// runs again (with the buttons of the frame SELECT was pressed), then the level is shown and the sounds go on.
var sel = ((pressed & 2) != 0);
if (lv_stat == 0 && sel && lt + 1 >= 18 && lv_exit_t < 0 && lv_restart_t < 0 && !lv_done)
{
    lv_stat = 1;
    lv_stat_t = -1;
    sel = false;
}
var keep = false;
if (lv_stat != 0)
{
    lv_stat_t += 1;
    if (lv_stat_t == 0)
    {
        // the level is still shown on this frame, and already as it is now (not one frame behind)
        if (lv_ran) lv_ord = (lv_fc + 1) & 1;
        lv_stat_ord = lv_ord;
        lv_cam_show = lv_cam_x;
        lv_cam_yold = lv_cam_yshow;
        lv_cam_yshow = lv_cam_y;
        s_hp = pl.p_hp;
        s_lives = lv_lives;
        with (pl)
        {
            s_x = p_x;  s_y = p_y + p_late;  p_late = 0;  s_pic = p_pic;  s_face = p_face;  s_behind = p_behind;
            if (p_face_was >= 0) { s_face = p_face_was; p_face_was = -1; }      // (the frame the exit takes over: still the old way)
            s_vis = (p_state != 23 && !p_hide);
            s_blink = p_flash;
            if (p_state == 15) s_star = ((119 - p_cnt) div 4) mod 7; else s_star = -1;
            s_star_slot = stage.lv_star;
        }
        for (i = 0; i < lv_cr_n; i += 1)
        {
            cr = lv_cr[i];
            cr.s_x = cr.c_wx - lv_cam_x;
            cr.s_y = cr.c_y;
            cr.s_eyes = cr.c_eyes;
            cr.s_pic = 0;
            if (cr.c_mode == 5 && cr.c_t >= 2) cr.s_pic = cr.c_pic;
        }
        for (i = 0; i < lv_en_n; i += 1)
        {
            with (lv_en[i]) event_user(2);
        }
        for (i = 0; i < lv_it_n; i += 1)
        {
            en = lv_it[i];
            en.s_x = en.e_wx - lv_cam_x;
            en.s_y = en.e_y;
            en.s_kind = en.i_kind;
            en.s_vis = (!en.e_gone && en.s_x >= 0 && en.s_x <= 263);
        }
    }
    lv_ran = false;
    if (lv_stat == 1)
    {
        if (lv_stat_t != 2) lv_fc = (lv_fc + 1) mod 8;
        if (lv_stat_t < 4)
        {
            lv_fx_end -= 1;         // the sound effects go on while the level clock stands still
            event_user(1);
        }
        if (lv_stat_t == 4)
        {
            lv_paused = true;
            if (lv_music_on) { audio_pause_sound(lv_music_a); audio_pause_sound(lv_music_b); }
            if (lv_fx_now != 0) audio_pause_sound(lv_fx_inst);
        }
        if (lv_stat_t == 0) lv_view = 1; else if (lv_stat_t < 3) lv_view = 0; else lv_view = 2;
        if (sel && lv_stat_t >= 8)
        {
            lv_stat = 2;
            lv_stat_t = 0;
            lv_stat_pad = pad;
            lv_stat_now = pressed;
        }
    }
    else
    {
        lv_view = 0;
        if (lv_stat_t == 13) { lv_stat = 0; lv_resume = 2; keep = true; }
    }
    if (lv_stat != 0) exit;
}
else if (lv_view == 0) lv_view = 1;
if (lv_resume > 0)
{
    lv_resume -= 1;
    if (lv_resume == 0)
    {
        lv_paused = false;
        if (lv_music_on) { audio_resume_sound(lv_music_a); audio_resume_sound(lv_music_b); }
        if (lv_fx_now != 0) audio_resume_sound(lv_fx_inst);
    }
}

lt += 1;
lv_fc = (lv_fc + 1) mod 8;
if (lv_ran) lv_ord = lv_fc & 1;     // the order of the sprites changes with every frame of the game
lv_ran = false;
if (keep) { pad = lv_stat_pad; pressed = lv_stat_now; }

// ---- 1) section 1: the dining room ------------------------------------------------
if (!lv_done)
{
    // 1a) the level music starts one frame after the previous screen ended
    if (lt == -6)
    {
        if (!lv_music_on)
        {
            audio_stop_sound(snd_prison_alarm);     // still playing at its lowest volume when START skipped the night scene
            lv_music_a = audio_play_sound(snd_lv1_music_a, 10, true);    // both are 1920 frames long and loop
            lv_music_b = audio_play_sound(snd_lv1_music_b, 10, true);
            lv_music_on = true;
        }
        // (it keeps playing when the section restarts after a fall)
    }

    // 1b) sound effects (User Defined 1)
    event_user(1);

    // 1c) the Draw events show what the previous frame left behind (the NES picture is one frame behind its game)
    lv_cam_show = lv_cam_x;
    lv_cam_yold = lv_cam_yshow;
    lv_cam_yshow = lv_cam_y;
    with (pl)
    {
        s_x = p_x;  s_y = p_y + p_late;  p_late = 0;  s_pic = p_pic;  s_face = p_face;  s_behind = p_behind;
            if (p_face_was >= 0) { s_face = p_face_was; p_face_was = -1; }      // (the frame the exit takes over: still the old way)
        s_vis = (p_state != 23 && !p_hide);
        s_blink = p_flash;
        if (p_state == 15) s_star = ((119 - p_cnt) div 4) mod 7; else s_star = -1;      // stunned: the star
        s_star_slot = stage.lv_star;
    }
    s_hp = pl.p_hp;
    s_lives = lv_lives;
    // crates: a crate that is carried after a run-up of 30 frames, or flies far, flashes (4 frames normal, 4 bright)
    for (i = 0; i < lv_cr_n; i += 1)
    {
        cr = lv_cr[i];
        cr.s_x = cr.c_wx - lv_cam_x;
        cr.s_y = cr.c_y;
        cr.s_vis = true;
        cr.s_eyes = cr.c_eyes;
        cr.s_flash = 0;
        cr.s_pic = 0;
        if (cr.c_mode == 5 && cr.c_t >= 2) cr.s_pic = cr.c_pic;     // 3..7: flying apart
        if (cr.c_mode == 3 || (cr.c_mode == 0 && pl.p_run >= 30))
        {
            if ((lv_fc & 4) != 0) cr.s_flash = 1;
        }
    }
    // crates that left the screen or broke on the previous frame are removed (not shown again)
    n = 0;
    for (i = 0; i < lv_cr_n; i += 1)
    {
        cr = lv_cr[i];
        if (cr.c_gone) { with (cr) instance_destroy(); }
        else { lv_cr[n] = cr; n += 1; }
    }
    lv_cr_n = n;
    // enemies: the same
    n = 0;
    for (i = 0; i < lv_en_n; i += 1)
    {
        en = lv_en[i];
        if (en.e_gone) { with (en) instance_destroy(); }
        else
        {
            with (en) event_user(2);
            lv_en[n] = en;
            n += 1;
        }
    }
    lv_en_n = n;
    // items: the same; one is shown from 8 pixels before its middle is on the screen (its left half)
    n = 0;
    for (i = 0; i < lv_it_n; i += 1)
    {
        en = lv_it[i];
        if (en.e_gone) { with (en) instance_destroy(); }
        else
        {
            en.s_x = en.e_wx - lv_cam_x;
            en.s_y = en.e_y;
            en.s_kind = en.i_kind;
            en.s_vis = (en.s_x >= 0 && en.s_x <= 263);     // (its left half shows before its middle is on the screen)
            lv_it[n] = en;
            n += 1;
        }
    }
    lv_it_n = n;

    // 1d) the game itself: once on lt == -1, then every frame from lt == 18 (after the fade-in),
    //     until the player has left the section or has to start it again
    if ((lt == -1 || lt >= 18) && lv_exit_t < 0 && lv_restart_t < 0)
    {
        lv_ran = true;
        // the exit: an invisible box 12 wide and 16 high, standing at x = 2016 on the last table (y = 160);
        // in the kitchen at the same x on its upper floor (y = 192), in front of the hole in the wall;
        // in the third section at x = 1776 on the ledge right of the sink (y = 160).
        // It notices the player touching it (the player's position before this frame's move) ...
        if (lv_trig_on && pl.p_state != 23)
        {
            var ey = 160;
            var ex = 2016;
            if (lv_sec == 1) ey = 192;
            if (lv_sec == 2) ex = 1776;
            if (abs(lv_cam_x + pl.p_x - ex) <= 12 && pl.p_y + lv_cam_y >= ey - 16 && pl.p_y + lv_cam_y <= ey + pl.p_h)
            {
                lv_trig_on = false;
                lv_trig_wait = 2;
            }
        }

        // the player
        var x0 = pl.p_x;
        var y0 = pl.p_y;
        if (lt == -1)
        {
            // this single early run does not see the controller: on the NES it gets what was read last
            // (nothing at the level start; after a fall, the buttons of the 21st frame of the fade-out)
            pl.p_pad = lv_pad_keep;
            pl.p_pressed = lv_pressed_keep;
        }
        else
        {
            pl.p_pad = pad;
            pl.p_pressed = pressed;
        }
        with (pl) event_user(0);
        // stunned: a star goes round the head. It takes a place in the object list (which decides what it covers).
        // If all 9 places are taken on the frame the stun starts, this stun has no star (lv_star = -1): the
        // original does not try again when a place becomes free.
        if (pl.p_state == 15 && lv_star == 0)
        {
            lv_star = scr_lv_take_slot();
            if (lv_star > 0) lv_slot_k[lv_star] = 4; else lv_star = -1;
        }
        else if (pl.p_state != 15 && lv_star != 0)
        {
            if (lv_star > 0) lv_slot_k[lv_star] = 0;
            lv_star = 0;
        }

        // the camera follows when the player is in the right half of the screen and has moved right
        var d = pl.p_x - x0;
        var camx0 = lv_cam_x;
        if (pl.p_x >= 128 && d > 0 && d < 5)
        {
            // (the kitchen: the camera stops at the shaft, x = 1280, until it has gone all the way up)
            // (the third section is 7 screens wide: the camera stops at 1536)
            if (lv_sec == 2) d = min(d, 1536 - lv_cam_x);
            else if (lv_sec == 0 || lv_cam_y == 0) d = min(d, 1792 - lv_cam_x);
            else d = min(d, 1280 - lv_cam_x);
            lv_cam_x += d;
            // (a player who walks into an exit by himself also moves on the screen: seen in the third section,
            //  the only one whose camera has not stopped by then)
            if (!pl.p_auto) pl.p_x -= d;
        }
        // The third section: the player is behind the picture while in a block of the sink's inside or of the
        // dark gap right of it (lv_back3). The point looked at: 2 pixels right of where he is now, 1 above
        // where his feet were before this frame. The original only has the columns up to the one 248 pixels
        // right of the camera: further right it finds the column 16 to the left. For a player who walks by
        // himself the camera counts as it was before this frame; he is through the exit when he gets behind
        // the picture.
        if (lv_sec == 2)
        {
            var cq = lv_cam_x;
            if (pl.p_auto) cq = camx0;
            var bc = (pl.p_x + cq + 2) div 16;
            var br = floor((y0 - 1) / 16);
            if (bc > (cq + 248) div 16) bc -= 16;
            pl.p_behind = false;
            if (br >= 0 && br < 15 && bc >= 0 && bc < 128) pl.p_behind = (string_char_at(lv_back3[br], bc + 1) == "1");
            if (pl.p_auto && pl.p_behind) pl.p_out = true;
        }
        // the kitchen's shaft: the camera goes up with a player who rises above y = 128, and never comes down
        // (not yet on the frame on which the camera arrives at the shaft)
        d = y0 - pl.p_y;
        lv_dy = 0;
        if (lv_sec == 1 && camx0 == 1280 && pl.p_y < 128 && d > 0)
        {
            d = min(d, lv_cam_y);
            lv_cam_y -= d;
            pl.p_y += d;
            // crates, items and enemies keep a screen position: they move down with the picture
            for (i = 0; i < lv_cr_n; i += 1) lv_cr[i].c_y += d;
            for (i = 0; i < lv_it_n; i += 1) lv_it[i].e_y += d;
            for (i = 0; i < lv_en_n; i += 1) lv_en[i].e_y += d;
            lv_dy = d;
        }

        // objects enter when the column 264 pixels right of the camera changes
        col = (lv_cam_x + 264) div 16;
        if (col != lv_sp_col)
        {
            lv_sp_col = col;
            while (lv_sec == 0 && lv_sp_i < lv_ob_n)
            {
                if (lv_ob_c[lv_sp_i] != col) break;
                k = lv_ob_k[lv_sp_i];
                if (k == 9)
                {
                    // the exit (see lv_trig_on) only takes a place in the object list here
                    j = scr_lv_take_slot();
                    if (j >= 0) lv_slot_k[j] = 3;
                }
                else scr_lv_spawn(k, lv_ob_c[lv_sp_i] * 16, lv_ob_r[lv_sp_i] * 16 - 512, 0);
                lv_sp_i += 1;
            }
            if (lv_sec == 2 && col == 111 && lv_sp_i == 0)
            {
                // the third section's list: for now only its exit, which takes a place in the object list
                j = scr_lv_take_slot();
                if (j >= 0) lv_slot_k[j] = 3;
                lv_sp_i = 1;
            }
            while (lv_sec == 1 && lv_sp_i < lv_ob2_n)     // the kitchen's list
            {
                if (lv_ob2_c[lv_sp_i] != col) break;
                scr_lv_spawn2(lv_sp_i, lv_cam_y);
                lv_sp_i += 1;
            }
        }
        // ... and in the shaft from above (see lv_ob2v_* in Create)
        if (lv_sec == 1 && lv_dy != 0)
        {
            for (i = 0; i < lv_ob2v_n; i += 1)
            {
                if (((lv_cam_y + 8) >> 4) != lv_ob2v_r[i] || ((lv_cam_y + lv_dy + 8) >> 4) == lv_ob2v_r[i]) continue;
                k = lv_ob2v_c[i] * 16 - lv_cam_x;
                if (k >= 0 && k <= 255) scr_lv_spawn(lv_ob2v_k[i] - 10, lv_ob2v_c[i] * 16, lv_ob2v_r[i] * 16 - 16 - lv_cam_y, 0);
            }
        }

        // crates and enemies act in the order of their places in the object list
        // (an enemy made on this frame in a later place than its maker's acts on this frame too)
        lv_snd = 0;
        for (j = 3; j < 12; j += 1)
        {
            k = lv_slot_k[j];
            if (k == 1)
            {
                cr = lv_slot[j];
                if (cr.c_snd != 0) { lv_snd = cr.c_snd; cr.c_snd = 0; }      // thrown on this frame
                if (cr.c_mode != 0) { with (cr) event_user(0); }
            }
            else if (k == 2 || k == 5) { with (lv_slot[j]) event_user(0); }
        }

        // ... and one frame later the exit takes over if the player is on the ground and not crouching
        //     or just landed; otherwise it starts waiting again
        if (lv_trig_wait > 0)
        {
            lv_trig_wait -= 1;
            if (lv_trig_wait == 0)
            {
                if (pl.p_state == 5)
                {
                    pl.p_state = 20;
                    pl.p_auto = true;
                    pl.p_face_was = pl.p_face;      // the next picture still shows the player looking the old way
                    pl.p_face = 1;
                    pl.p_xv = 2;
                    pl.p_ghost = true;      // enemies are not touched any more
                }
                else lv_trig_on = true;
            }
        }

        // sounds caused on this frame
        // (a landing does not take the place of a pick-up, throw or bonus sound that is about to start)
        // (nor is it asked for while another effect is playing)
        if (pl.p_landed && !(lv_fx_wait > 0 && lv_fx_k != 5) && !(lv_fx_now != 0 && lv_fx_now != 5 && lt < lv_fx_end)) { lv_fx_k = 5; lv_fx_wait = 2; }
        if (pl.p_snd != 0) { lv_fx_k = pl.p_snd; lv_fx_wait = 2; }
        if (lv_snd != 0)   { lv_fx_k = lv_snd;   lv_fx_wait = 2; }     // the objects ask after the player: the last one to ask is heard
        if (pl.p_out)     lv_exit_t = lt;       // walked off the right edge
        if (pl.p_restart) lv_restart_t = lt;    // fell out of the picture 60 frames ago
    }

    // 1e) leaving the section: the picture fades out and is black from lv_exit_t + 17
    if (lv_exit_t >= 0 && lt == lv_exit_t + 22 && lv_sec < 2)
    {
        // the dining room is left: the kitchen; the kitchen is left: the third section. Its picture comes on 9 frames from now (its level frame 0) and
        // fades in like the level start. Hearts, lives, the bonus count and the music stay; the walk goes on in
        // step (p_cnt). The player's single early run (lt == -1) gets the buttons of this frame.
        var hp = pl.p_hp;
        var cnt = pl.p_cnt;
        lv_sec += 1;
        // (the count behind the flashing and the order of the sprites loses 3 frames at the first change, none at the second)
        if (lv_sec == 1) lv_fc = (lv_fc + 5) mod 8;
        lv_fx_end += -9 - lt;       // (a sound effect that is playing plays on)
        lt = -9;
        lv_exit_t = -1;
        lv_cam_x = 0;
        if (lv_sec == 1) lv_cam_y = 240; else lv_cam_y = 0;
        lv_cam_yshow = lv_cam_y;  lv_cam_yold = lv_cam_y;
        lv_trig_on = true;
        lv_trig_wait = 0;
        with (pl) event_perform(ev_create, 0);
        pl.p_hp = hp;
        pl.p_cnt = cnt;
        event_user(0);              // the new section's block map; crates and enemies of the old one are gone
        lv_pad_keep = pad;
        lv_pressed_keep = pressed;
    }
    else if (lv_exit_t >= 0 && lt == lv_exit_t + 22)
    {
        // the third section is left through the gap right of the sink
        lv_done = true;
        with (pl) instance_destroy();
        with (obj_crate) instance_destroy();
        lv_cr_n = 0;
        with (obj_enemy) instance_destroy();
        lv_en_n = 0;
        with (obj_item) instance_destroy();
        lv_it_n = 0;
        for (i = 3; i < 12; i += 1) lv_slot_k[i] = 0;
        if (lv_fx_now != 0) { lv_fx_now = 0; audio_sound_gain(lv_music_b, 1, 0); }      // (a sound that is playing plays on)
        lv_fx_wait = 0;
        // TODO (later step): what follows the third section appears on level frame lv_exit_t + 31.
        //                    No new music is started there, the level music should keep playing.
    }

    // 1f) after a fall (or the last heart): the same fade-out, then ...
    if (lv_restart_t >= 0 && lv_lives == 0)
    {
        // ... the last life is gone: GAME OVER. The bonus count is lost at once; 25 frames later the level
        // music stops and the GAME OVER screen takes over (User Defined 2), its tune starts on the frame after.
        if (lt == lv_restart_t) lv_bonus = 0;
        if (lt == lv_restart_t + 25)
        {
            lv_go = 2;
            lv_go_t = 25;
            go_bright = -1;
            go_snd = 1;
            go_k = 13;
            if (lv_music_on) { audio_stop_sound(lv_music_a); audio_stop_sound(lv_music_b); lv_music_on = false; }
            if (lv_fx_now != 0) { audio_stop_sound(lv_fx_inst); lv_fx_now = 0; }
            lv_fx_wait = 0;
        }
    }
    else if (lv_restart_t >= 0 && lt == lv_restart_t + 21)
    {
        lv_pad_keep = pad;
        lv_pressed_keep = pressed;
    }
    // ... the section starts again from its beginning (the kitchen from the kitchen's)
    if (lv_restart_t >= 0 && lv_lives != 0 && lt == lv_restart_t + 24)
    {
        lv_restart_t = -1;
        lt = -7;
        lv_cam_x = 0;
        if (lv_sec == 1) lv_cam_y = 240; else lv_cam_y = 0;      // (the section starts again, not the level)
        lv_cam_yshow = lv_cam_y;
        lv_cam_yold = lv_cam_y;
        lv_trig_on = true;
        lv_trig_wait = 0;
        with (pl) event_perform(ev_create, 0);
        event_user(0);          // all crates and bonus boxes are back, the enemies are gone
        if (lv_fx_now != 0) { lv_fx_now = 0; audio_sound_gain(lv_music_b, 1, 0); }      // (a sound that is playing plays on)
        lv_fx_wait = 0;
    }
}

// ---- 2) brightness of this frame's picture -------------------------------------------
lv_bright = -1;
if (!lv_done)
{
    if (lt >= 5) lv_bright = min((lt - 5) div 4, 3);        // fade-in steps on lt == 5, 9, 13, full brightness from 17
    var o = max(lv_exit_t, lv_restart_t);
    if (o >= 0 && lt >= o + 5)
    {
        lv_bright = 4 + ((lt - o - 5) div 4);               // fade-out steps 5, 9 and 13 frames after the exit / the restart
        if (lv_bright > 6) lv_bright = -1;
    }
}

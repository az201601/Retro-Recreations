/// obj_stage1 : End Step
lt += 1;
lv_fc = (lv_fc + 1) mod 8;
if (lv_ran) lv_ord = lv_fc & 1;     // the order of the sprites changes with every frame of the game
lv_ran = false;
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

    // 1b) sound effects: 1 pick up, 2 throw, 3 bonus, 4 far throw, 5 landing, 6 the flyer's buzz, 7 the cook
    //     throws, 8 an enemy is knocked out. Only one plays at a time.
    //     A new one stops the one before it 1 frame after its cause and starts 2 frames after its cause.
    //     The landing sound is the exception: it stops nothing, and is left out while another effect is playing.
    //     All but 4 use the music's 2nd square channel: the music's part is silent meanwhile. 4 is noise only
    //     (8 is both).
    //     The buzz is asked for again every 3 or 4 frames while a flyer is about: whatever else starts is cut
    //     off by it after 1 to 3 frames, as in the original.
    if (lv_fx_wait > 0)
    {
        lv_fx_wait -= 1;
        if (lv_fx_wait == 1)
        {
            if (lv_fx_k != 5 && lv_fx_now != 0)
            {
                audio_stop_sound(lv_fx_inst);
                audio_sound_gain(lv_music_b, 1, 0);
                lv_fx_now = 0;
            }
        }
        else if (!(lv_fx_k == 5 && lv_fx_now != 0 && lv_fx_now != 5 && lt < lv_fx_end))
        {
            if (lv_fx_now != 0) audio_stop_sound(lv_fx_inst);       // (only a landing sound can still be playing here)
            switch (lv_fx_k)
            {
                case 1: lv_fx_inst = audio_play_sound(snd_pick, 20, false);      lv_fx_end = lt + 14; break;
                case 2: lv_fx_inst = audio_play_sound(snd_throw, 20, false);     lv_fx_end = lt + 25; break;
                case 3: lv_fx_inst = audio_play_sound(snd_bonus, 20, false);     lv_fx_end = lt + 53; break;
                case 4: lv_fx_inst = audio_play_sound(snd_throw_far, 20, false); lv_fx_end = lt + 73; break;
                case 5: lv_fx_inst = audio_play_sound(snd_land, 20, false);      lv_fx_end = lt + 6;  break;
                case 6: lv_fx_inst = audio_play_sound(snd_buzz, 20, false);      lv_fx_end = lt + 4;  break;
                case 7: lv_fx_inst = audio_play_sound(snd_cook_throw, 20, false); lv_fx_end = lt + 10; break;
                case 8: lv_fx_inst = audio_play_sound(snd_enemy_hit, 20, false); lv_fx_end = lt + 17; break;
            }
            lv_fx_now = lv_fx_k;
            if (lv_fx_k == 4) audio_sound_gain(lv_music_b, 1, 0);
            else audio_sound_gain(lv_music_b, 0, 0);
        }
    }
    if (lv_fx_now != 0 && lt == lv_fx_end)
    {
        lv_fx_now = 0;
        audio_sound_gain(lv_music_b, 1, 0);
    }

    // 1c) the Draw events show what the previous frame left behind (the NES picture is one frame behind its game)
    lv_cam_show = lv_cam_x;
    with (pl)
    {
        s_x = p_x;  s_y = p_y;  s_pic = p_pic;  s_face = p_face;
        s_vis = (p_state != 23 && !p_hide);
    }
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
            en.s_x = en.e_wx - lv_cam_x;
            en.s_y = en.e_y;
            en.s_pic = en.e_pic;
            en.s_face = en.e_face;
            en.s_vis = !en.e_hide;
            lv_en[n] = en;
            n += 1;
        }
    }
    lv_en_n = n;

    // 1d) the game itself: once on lt == -1, then every frame from lt == 18 (after the fade-in),
    //     until the player has left the section or has to start it again
    if ((lt == -1 || lt >= 18) && lv_exit_t < 0 && lv_restart_t < 0)
    {
        lv_ran = true;
        // the exit: an invisible box 12 wide and 16 high, standing at x = 2016 on the last table (y = 160).
        // It notices the player touching it (the player's position before this frame's move) ...
        if (lv_trig_on && pl.p_state != 23)
        {
            if (abs(lv_cam_x + pl.p_x - 2016) <= 12 && pl.p_y >= 144 && pl.p_y <= 160 + pl.p_h)
            {
                lv_trig_on = false;
                lv_trig_wait = 2;
            }
        }

        // the player
        var x0 = pl.p_x;
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

        // the camera follows when the player is in the right half of the screen and has moved right
        var d = pl.p_x - x0;
        if (pl.p_x >= 128 && d > 0 && d < 5)
        {
            d = min(d, 1792 - lv_cam_x);
            lv_cam_x += d;
            pl.p_x -= d;
        }

        // objects enter when the column 264 pixels right of the camera changes
        col = (lv_cam_x + 264) div 16;
        if (col != lv_sp_col)
        {
            lv_sp_col = col;
            while (lv_sp_i < lv_ob_n)
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
            else if (k == 2) { with (lv_slot[j]) event_user(0); }
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
                    pl.p_face = 1;
                    pl.p_xv = 2;
                }
                else lv_trig_on = true;
            }
        }

        // sounds caused on this frame
        // (a landing does not take the place of a pick-up, throw or bonus sound that is about to start)
        if (pl.p_landed && !(lv_fx_wait > 0 && lv_fx_k != 5)) { lv_fx_k = 5; lv_fx_wait = 2; }
        if (pl.p_snd != 0) { lv_fx_k = pl.p_snd; lv_fx_wait = 2; }
        if (lv_snd != 0)   { lv_fx_k = lv_snd;   lv_fx_wait = 2; }     // the objects ask after the player: the last one to ask is heard
        if (pl.p_out)     lv_exit_t = lt;       // walked off the right edge
        if (pl.p_restart) lv_restart_t = lt;    // fell out of the picture 60 frames ago
    }

    // 1e) leaving the section: the picture fades out and is black from lv_exit_t + 17
    if (lv_exit_t >= 0 && lt == lv_exit_t + 22)
    {
        lv_done = true;
        with (pl) instance_destroy();
        with (obj_crate) instance_destroy();
        lv_cr_n = 0;
        with (obj_enemy) instance_destroy();
        lv_en_n = 0;
        for (i = 3; i < 12; i += 1) lv_slot_k[i] = 0;
        if (lv_fx_now != 0) { lv_fx_now = 0; audio_sound_gain(lv_music_b, 1, 0); }      // (a sound that is playing plays on)
        lv_fx_wait = 0;
        // TODO (later step): the next section (the kitchen) appears on level frame lv_exit_t + 31.
        //                    No new music is started there, the level music should keep playing.
    }

    // 1f) after a fall: the same fade-out, then the section starts again from its beginning
    if (lv_restart_t >= 0 && lt == lv_restart_t + 21)
    {
        lv_pad_keep = pad;
        lv_pressed_keep = pressed;
    }
    if (lv_restart_t >= 0 && lt == lv_restart_t + 24)
    {
        // TODO (later step): lv_lives == 0 is the game over
        lv_restart_t = -1;
        lt = -7;
        lv_cam_x = 0;
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

/// obj_stage1 : End Step
lt += 1;

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

    // 1b) landing sound: starts 2 frames after the landing and takes the music's 2nd square channel for 6 frames
    if (lv_land_n > 0)
    {
        lv_land_n += 1;
        if (lv_land_n == 3)
        {
            audio_play_sound(snd_land, 20, false);
            audio_sound_gain(lv_music_b, 0, 0);
        }
        if (lv_land_n == 9)
        {
            audio_sound_gain(lv_music_b, 1, 0);
            lv_land_n = 0;
        }
    }

    // 1c) the Draw events show what the previous frame left behind (the NES picture is one frame behind its game)
    lv_cam_show = lv_cam_x;
    with (pl)
    {
        s_x = p_x;  s_y = p_y;  s_pic = p_pic;  s_face = p_face;
        s_vis = (p_state != 23);
    }

    // 1d) the game itself: once on lt == -1, then every frame from lt == 18 (after the fade-in),
    //     until the player has left the section or has to start it again
    if ((lt == -1 || lt >= 18) && lv_exit_t < 0 && lv_restart_t < 0)
    {
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

        if (pl.p_landed)  lv_land_n = 1;
        if (pl.p_out)     lv_exit_t = lt;       // walked off the right edge
        if (pl.p_restart) lv_restart_t = lt;    // fell out of the picture 60 frames ago
    }

    // 1e) leaving the section: the picture fades out and is black from lv_exit_t + 17
    if (lv_exit_t >= 0 && lt == lv_exit_t + 22)
    {
        lv_done = true;
        with (pl) instance_destroy();
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

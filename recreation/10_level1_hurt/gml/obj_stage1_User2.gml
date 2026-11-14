/// obj_stage1 : User Defined 2   (one frame of GAME OVER / the continue screen; run by End Step while lv_go >= 2)
// go_pressed: the buttons that went down on this frame (set by End Step).
var pressed = go_pressed;

lv_go_t += 1;
var t = lv_go_t;
lv_ord = 1 - lv_ord;                // the sprite list goes on turning round every frame
lv_fc = (lv_fc + 1) mod 8;
lv_ran = false;
s_cur = go_cur;                     // the picture is one frame behind
s_credits = lv_credits;

// a sound asked for starts 2 frames after the button (the GAME OVER tune: on the frame after the music stopped)
if (go_snd > 0)
{
    go_snd -= 1;
    if (go_snd == 0)
    {
        if (go_k == 13) audio_play_sound(snd_gameover, 10, false);
        else
        {
            if (go_inst != -1) audio_stop_sound(go_inst);
            if (go_k == 11) go_inst = audio_play_sound(snd_cursor, 20, false);
            else go_inst = audio_play_sound(snd_confirm, 20, false);
        }
    }
}

go_bright = -1;
var back = false;                   // back to the title screen
switch (lv_go)
{
    case 2:
        // GAME OVER: black for 5 frames, fades in (t == 30, 34, 38, 42); the words sink 32 pixels (see Draw).
        // The buttons do nothing. With a credit left it fades out from t == 296 and the continue screen follows
        // on t == 314; without one it stays until t == 357 and the title screen follows on t == 375.
        if (t >= 30) go_bright = min((t - 30) div 4, 3);
        var out = 357;
        if (lv_credits > 0) out = 296;
        if (t >= out) go_bright = 4 + ((t - out) div 4);
        if (go_bright > 6) go_bright = -1;
        if (lv_credits > 0 && t == 314) { lv_go = 3; lv_go_t = 0; go_cur = 0; s_cur = 0; }
        if (lv_credits == 0 && t == 375) back = true;
        break;

    case 3:
        // the continue screen: fades in (t == 7, 11, 15, 19); the buttons count from t == 20.
        // UP / DOWN move the arrow, A chooses. START, SELECT and B do nothing.
        if (t >= 7) go_bright = min((t - 7) div 4, 3);
        if (t >= 20)
        {
            if ((pressed & 24) != 0) { go_cur = 1 - go_cur; go_snd = 2; go_k = 11; }
            if ((pressed & 4) != 0)
            {
                go_snd = 2;
                go_k = 12;
                go_t3 = t;
                lv_go = 4 + go_cur;
                lv_go_t = 0;
                if (go_cur == 0) { lv_credits -= 1; lv_lives = 3; }     // CONTINUE: a credit for 3 lives
            }
        }
        break;

    case 4:
        // CONTINUE: the character gets up and runs off (Draw), the screen fades out (t == 126, 130, 134),
        // and on t == 145 the level starts again from its beginning
        go_bright = 3;
        if (t >= 126) go_bright = 4 + ((t - 126) div 4);
        if (go_bright > 6) go_bright = -1;
        if (t == 145)
        {
            lv_go = 0;
            lv_restart_t = -1;
            lt = -7;                // (the level music starts again on the next frame, see End Step)
            lv_cam_x = 0;
            lv_trig_on = true;
            lv_trig_wait = 0;
            lv_pad_keep = 0;
            lv_pressed_keep = 0;
            with (pl) event_perform(ev_create, 0);
            event_user(0);          // all crates and bonus boxes are back, the enemies are gone
            lv_fx_now = 0;
            lv_fx_wait = 0;
            lv_bright = -1;
        }
        break;

    case 5:
        // END: the character is thrown out (Draw), the screen fades out (t == 66, 70, 74),
        // and on t == 84 the title screen takes over
        go_bright = 3;
        if (t >= 66) go_bright = 4 + ((t - 66) div 4);
        if (go_bright > 6) go_bright = -1;
        if (t == 84) back = true;
        break;
}

if (back)
{
    // Back to the title screen: obj_intro again, at the point of its clock where the screen is black, 2 frames
    // before the title music is asked for and 7 before the title fades in (as measured in the original).
    var o = instance_create(0, 0, obj_intro);
    o.frame = o.fade_start + 18;
    audio_stop_all();
    with (pl) instance_destroy();
    with (obj_crate) instance_destroy();
    with (obj_enemy) instance_destroy();
    instance_destroy();
}

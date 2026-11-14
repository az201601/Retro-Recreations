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
        audio_stop_sound(snd_prison_alarm);     // still playing at its lowest volume when START skipped the night scene
        lv_music_a = audio_play_sound(snd_lv1_music_a, 10, true);    // both are 1920 frames long and loop
        lv_music_b = audio_play_sound(snd_lv1_music_b, 10, true);
    }

    // 1b) TEMPORARY, until the player exists (next step): LEFT / RIGHT move the camera 2 pixels per frame.
    //     In the original the camera follows the player, and the section ends when the player walks off the
    //     right edge of the last screen. Here: press RIGHT once more when the camera is at its right end.
    if (lt >= 17 && lv_exit_t < 0)
    {
        if ((pressed & 128) != 0 && lv_cam_x == 1792) lv_exit_t = lt;
        else if ((pad & 128) != 0) lv_cam_x = min(lv_cam_x + 2, 1792);
        else if ((pad & 64) != 0)  lv_cam_x = max(lv_cam_x - 2, 0);
    }

    // 1c) leaving the section: the picture fades out (see Draw) and is black from lv_exit_t + 17
    if (lv_exit_t >= 0 && lt == lv_exit_t + 22)
    {
        lv_done = true;
        // TODO (later step): the next section (the kitchen) appears on level frame lv_exit_t + 31.
        //                    No new music is started there, the level music should keep playing.
    }
}

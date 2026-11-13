/// obj_intro : Step
frame += 1;
var n = frame;
var start_pressed = keyboard_check_pressed(vk_enter);   // NES START button

// ---- 1) a sound requested on the previous frame starts now -----------------
if (snd_queue != -1)
{
    if (snd_queue == snd_title_theme)
    {
        // the title music replaces whatever intro sound is still playing
        audio_stop_sound(snd_intro_jingle);
        audio_stop_sound(snd_intro_roll);
        audio_play_sound(snd_title_theme, 10, true);    // 2880 frames long, loops forever
    }
    else
    {
        audio_play_sound(snd_queue, 10, false);
    }
    snd_queue = -1;
}
if (n == 0) audio_play_sound(snd_intro_pops, 10, false);   // two APU "thumps" on NES frames 169 and 189 (optional)

// ---- 2) scripted spotlight sequence (stops for good once START skips it) ---
if (skip_frame < 0 && n < fade_start)
{
    switch (n)
    {
        case 14:    // NES frame 170: brick wall mask is on screen
            bg_mode = 1;
            break;
        case 32:    // NES frame 188: spotlight is created above the screen, moving down 2 px/frame
            spot_on = true;
            spot_x  = 160 * 256;
            spot_y  = -95 * 256;
            spot_vx = 0;
            spot_vy = 512;
            break;
        case 160:   // NES frame 316: up-left, 1.375 px/frame on both axes
            spot_vx = -352;
            spot_vy = -352;
            break;
        case 256:   // NES frame 412: right, 2 px/frame
            spot_vx = 512;
            spot_vy = 0;
            break;
        case 320:   // NES frame 476: down-left, 1.375 px/frame
            spot_vx = -352;
            spot_vy = 352;
            break;
        case 368:   // NES frame 524: left, 2 px/frame (leaves the screen)
            spot_vx = -512;
            spot_vy = 0;
            break;
        case 496:   // NES frame 652: wall now has the Chip & Dale silhouettes, intro jingle is requested
            bg_mode   = 2;
            snd_queue = snd_intro_jingle;
            break;
        case 497:   // NES frame 653: spotlight is moved off-screen left, comes back in at 2 px/frame
            spot_x  = -164 * 256;
            spot_y  = 73 * 256;
            spot_vx = 512;
            spot_vy = 0;
            break;
        case 630:   // NES frame 786: overshoots, snaps back left at 4 px/frame
            spot_vx = -1024;
            break;
        case 646:   // NES frame 802: stops on the silhouettes, drum roll is requested
            spot_vx   = 0;
            snd_queue = snd_intro_roll;
            break;
    }

    if (spot_on)
    {
        spot_x += spot_vx;
        spot_y += spot_vy;
    }

    // START skips the intro, but only while the spotlight is travelling (NES frames 188..801).
    // The picture freezes and the fade-out begins 5 frames later.
    if (start_pressed && n >= 32 && n <= 645)
    {
        skip_frame = n;
        fade_start = n + 5;
    }
}

// ---- 3) fade out the spotlight, fade in the title screen -------------------
var f = n - fade_start;
if (f >= 0)
{
    switch (f)
    {
        case 0:  spot_fade = 1;                break;
        case 4:  spot_fade = 2;                break;
        case 8:  spot_fade = 3;                break;
        case 12: spot_on = false;              break;   // all black
        case 17: bg_mode = 0;                  break;
        case 20: snd_queue = snd_title_theme;  break;   // audible from f == 21
        case 25: title_fade = 0;               break;
        case 29: title_fade = 1;               break;
        case 33: title_fade = 2;               break;
        case 37: title_fade = 3;               break;   // title screen fully visible
    }

    // the title screen accepts START from f == 38 on
    if (f >= 38 && start_pressed && !menu_open)
    {
        menu_open = true;
        // TODO (next step): "Press START button" is replaced by the 1player / 2players menu
    }
}

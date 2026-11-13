/// obj_intro : Step
frame += 1;
var n = frame;

// ---- 0) controller ------------------------------------------------------------
var pad = 0;
if (keyboard_check(vk_enter)) pad |= 1;     // START
if (keyboard_check(vk_shift)) pad |= 2;     // SELECT
if (keyboard_check(ord("X"))) pad |= 4;     // A
if (keyboard_check(vk_up))    pad |= 8;     // UP
if (keyboard_check(vk_down))  pad |= 16;    // DOWN
if ((pad & 24) == 24) pad -= 24;            // UP + DOWN together cancel out (impossible on a real d-pad)
var pressed = pad & (pad_prev ^ 31);        // buttons that went down on this frame
pad_prev = pad;
var start_pressed = ((pressed & 1) != 0);

// ---- 1) sound ---------------------------------------------------------------------
// the menu sound effects use the 2nd square channel of the NES; the music on that channel comes back afterwards
if (n == sq2_unmute) audio_sound_gain(theme_sq2, 1, 0);

// a sound requested on the previous frame starts now
if (snd_queue != -1)
{
    if (snd_queue == snd_title_theme)
    {
        // the title music replaces whatever intro sound is still playing
        audio_stop_sound(snd_intro_jingle);
        audio_stop_sound(snd_intro_roll);
        theme_main = audio_play_sound(snd_title_theme, 10, true);       // both are 2880 frames long and loop forever
        theme_sq2  = audio_play_sound(snd_title_theme_sq2, 10, true);
    }
    else if (snd_queue == snd_menu_select || snd_queue == snd_menu_move)
    {
        audio_stop_sound(snd_menu_select);      // only one effect at a time (one NES channel)
        audio_stop_sound(snd_menu_move);
        audio_play_sound(snd_queue, 20, false);
        audio_sound_gain(theme_sq2, 0, 0);      // the effect takes the channel away from the music ...
        if (snd_queue == snd_menu_select) sq2_unmute = n + 12;   // ... for 12 frames
        else                              sq2_unmute = n + 10;   // ... for 10 frames
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
}

// ---- 4) menus ---------------------------------------------------------------------
// 4a) a button pressed on the previous frame takes effect on this frame
if (act_move)
{
    act_move    = false;
    menu_cursor = 1 - menu_cursor;
    snd_queue   = snd_menu_move;
}
if (act_confirm)
{
    act_confirm = false;
    snd_queue   = snd_menu_select;      // replaces the move sound if both happen on the same frame
    menu_t      = n;
    if (menu_state == 0)
    {
        menu_state  = 1;                // "Press START button" turns into 1player / 2players (takes 3 frames)
        menu_cursor = 0;
    }
    else if (menu_state == 1 && menu_cursor == 0)
    {
        menu_state = 2;                 // 1player: choose Chip or Dale
    }
    else
    {
        if (menu_state == 1) { global.players = 2; global.p1_char = 0; }
        else                 { global.players = 1; global.p1_char = menu_cursor; }
        menu_from  = menu_state;
        menu_state = 3;                 // the screen fades out; buttons are ignored from here on
    }
}

// 4b) read the buttons
if (menu_state == 0)
{
    // the title screen accepts START from f == 38 on (A, B, SELECT and the d-pad do nothing)
    if (f >= 38 && start_pressed) act_confirm = true;
}
else if ((menu_state == 1 && n >= menu_t + 2) || (menu_state == 2 && n >= menu_t + 1))
{
    if ((pressed & 26) != 0) act_move    = true;    // SELECT, UP or DOWN: the cursor goes to the other line
    if ((pressed & 5)  != 0) act_confirm = true;    // START or A
}

// 4c) after the choice: fade steps on menu_t + 4 / + 8 / + 12 (see Draw), black from menu_t + 16
if (menu_state == 3 && n == menu_t + 16) menu_state = 4;
if (menu_state == 4 && n == menu_t + 23)
{
    // the title music is cut off here by the sound of the next screen
    audio_stop_sound(snd_title_theme);
    audio_stop_sound(snd_title_theme_sq2);
    // TODO (next step): the next screen appears on frame menu_t + 41
    //                   (global.players and global.p1_char hold the choice)
}

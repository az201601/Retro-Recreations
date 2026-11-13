/// obj_intro : Create
// Chip 'n Dale Rescue Rangers 2 (NES, USA) - spotlight intro, title screen, player / character menus,
// night scene with the blimp.
// One Step == one NES frame (room_speed must be 60).
// frame 0 == the first all-black frame after the copyright screen has faded out
//            (frame 156 counted from power-on in Mesen; "NES frame" = frame + 156).

texture_set_interpolation(false);   // crisp pixels

frame      = -1;    // current frame number (set to 0 by the first Step)
skip_frame = -1;    // frame on which START skipped the intro (-1 = not skipped)
fade_start = 711;   // frame on which the spotlight starts fading out (START moves this earlier)

// spotlight: position of the top-left corner of the 64x63 image,
// in 1/256 pixel units (NES 8.8 fixed point), velocity in 1/256 pixel per frame
spot_on   = false;
spot_x    = 0;
spot_y    = 0;
spot_vx   = 0;
spot_vy   = 0;
spot_fade = 0;      // sub-image of spr_spotlight: 0 = full brightness .. 3 = darkest

bg_mode    = 0;     // black mask drawn IN FRONT of the spotlight: 0 none, 1 brick wall, 2 wall + silhouettes
title_fade = -1;    // sub-image of spr_title_bg / spr_title_fg: -1 hidden, 0 = darkest .. 3 = full brightness

// ---- controller ---------------------------------------------------------------
// bits: 1 = START, 2 = SELECT, 4 = A, 8 = UP, 16 = DOWN   (B, LEFT and RIGHT do nothing on these screens)
pad_prev = 0;       // buttons that were held on the previous frame

// ---- menus ----------------------------------------------------------------------
menu_state  = 0;    // 0 "Press START button", 1 1player/2players, 2 Chip/Dale, 3 fading out, 4 black (finished)
menu_t      = 0;    // frame on which menu_state last changed
menu_cursor = 0;    // 0 = upper line, 1 = lower line
menu_from   = 0;    // while fading out: the menu the choice was made in (1 = "2players", 2 = Chip/Dale)
act_move    = false;   // a cursor button was pressed on the previous frame
act_confirm = false;   // START / A was pressed on the previous frame

global.players = 1;    // result: 1 or 2
global.p1_char = 0;    // result: character of player 1, 0 = Chip, 1 = Dale (2 players: always Chip)

// ---- sound ------------------------------------------------------------------------
snd_queue  = -1;    // sound requested this frame; it becomes audible on the next frame (like the NES sound driver)
theme_main = -1;    // playing instance of snd_title_theme      (title music without the 2nd square channel)
theme_sq2  = -1;    // playing instance of snd_title_theme_sq2  (the 2nd square channel of the title music)
sq2_unmute = -1;    // frame on which theme_sq2 becomes audible again after a menu sound effect

// ---- night scene (starts 41 frames after the last menu choice) ------------------------
// its own clock: t = frame - (menu_t + 41), t == 0 is the first visible frame
ns_done     = false;   // the scene is over (black screen, the next screen takes over)
ns_skipped  = false;   // START was pressed during the scene
ns_exit_t   = -1;      // t on which the scene started to end (START, or 1003 = end of the script)
ns_fade_at1 = -1;      // t on which START (re)starts the fade-out clock
ns_fade_at2 = -1;      // t on which the end of the script (re)starts the fade-out clock
ns_fade_t0  = -1;      // t on which the fade-out clock was last started; one step every 4 frames after it
ns_lv_bg    = 0;       // fade-out step of the background, 0 = full .. 4 = black
ns_lv_blimp = 0;       // fade-out step of the blimp
ns_lv_beam  = 0;       // fade-out step of the lit searchlight beam
ns_blimp_x  = 0;       // blimp position in 1/256 pixel (x of its nose, y of its top edge)
ns_blimp_y  = 24 * 256;
ns_blimp_lit = 0;      // 1 = the blimp is lit by the searchlights
ns_beam_mode = 0;      // searchlights: 0 off, 1 swapping every 64 frames, 2 frozen and fading out
ns_beam     = 0;       // which beam is lit: 0 = spr_prison_beam_a, 1 = spr_prison_beam_b
ns_vol      = 15;      // NES volume of the alarm, 15 .. 1
ns_alarm    = -1;      // playing instance of snd_prison_alarm
ns_alarm_skip = -1;    // t of an alarm restart that START has swallowed

// loudness of the NES square channel for volume 0..15, relative to volume 15
ns_gain[0]  = 0;     ns_gain[1]  = 0.078; ns_gain[2]  = 0.154; ns_gain[3]  = 0.228;
ns_gain[4]  = 0.301; ns_gain[5]  = 0.372; ns_gain[6]  = 0.441; ns_gain[7]  = 0.509;
ns_gain[8]  = 0.575; ns_gain[9]  = 0.640; ns_gain[10] = 0.703; ns_gain[11] = 0.765;
ns_gain[12] = 0.826; ns_gain[13] = 0.885; ns_gain[14] = 0.943; ns_gain[15] = 1;

global.skip_cutscene = false;   // result: START was pressed in the night scene (the game then goes straight to the first level)

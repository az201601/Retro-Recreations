/// obj_intro : Create
// Chip 'n Dale Rescue Rangers 2 (NES, USA) - spotlight intro, title screen, player / character menus.
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

/// obj_intro : Create
// Chip 'n Dale Rescue Rangers 2 (NES, USA) - spotlight intro + title screen.
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
menu_open  = false; // START was pressed on the title screen (the 1player/2players menu is the next step)

snd_queue  = -1;    // sound requested this frame; it becomes audible on the next frame (like the NES sound driver)

/// obj_stage1 : Create
// Chip 'n Dale Rescue Rangers 2 (NES, USA) - level 1 (the restaurant).
// So far: section 1 (the dining room) with music, background, camera, the player (obj_player),
// falling out of the picture, and the way out.
// No enemies, crates, bonus items or hearts yet.
//
// obj_intro creates this object on the frame its last screen ends, and destroys itself.
// The code is in the END STEP event, not in Step: End Step always runs after obj_intro's Step, also on the
// frame this object is created, so the frame count does not depend on the order of the instances.
// One End Step == one NES frame (room_speed must be 60).
// The player is a separate object without a Step event; this object runs its code (User Defined 0).

texture_set_interpolation(false);   // crisp pixels

lt = -8;               // level clock, +1 per frame: -7 on the frame the previous screen ended,
                       // 0 = first frame of the level's picture (still black)
                       // It is set back to -7 when the section restarts after a fall.

// ---- controller ---------------------------------------------------------------
// bits: 1 = START, 2 = SELECT, 4 = A, 8 = UP, 16 = DOWN, 32 = B, 64 = LEFT, 128 = RIGHT
pad_prev = 255;        // buttons that were held on the previous frame (255: nothing counts as newly pressed at first)

// ---- section 1: the dining room (8 screens wide) --------------------------------
lv_done      = false;  // the section is over (black screen, the next section takes over)
lv_cam_x     = 0;      // camera: x of the left screen edge inside the section, 0 .. 1792 (only ever moves right)
lv_cam_show  = 0;      // the camera position the Draw event shows (the one after the previous frame)
lv_bright    = -1;     // brightness of the picture: 0..2 fade-in, 3 normal, 4..6 fade-out, -1 black
lv_exit_t    = -1;     // lt on which the player left the section on the right (-1 = not yet)
lv_restart_t = -1;     // lt on which the wait after a fall ended (-1 = no restart going on)
lv_pad_keep = 0;       // buttons the single early run of the game gets (see End Step)
lv_pressed_keep = 0;
lv_lives     = 3;      // lives left; a fall costs one  (TODO later step: game over at 0, the display)
lv_music_on  = false;  // the level music has been started
lv_music_a   = -1;     // playing instance of snd_lv1_music_a  (level music without the 2nd square channel)
lv_music_b   = -1;     // playing instance of snd_lv1_music_b  (the 2nd square channel of the level music)
lv_land_n    = 0;      // frames since the player landed, +1 (0 = no landing sound going on)

// the invisible exit at the right end of the last table (in the original an object like the enemies)
lv_trig_on   = true;   // it is waiting for the player
lv_trig_wait = 0;      // frames until it looks at the player it touched

// the 16x16 blocks of the section, 128 columns x 15 rows: 0 = nothing, 1 = can be stood on, 2 = solid
lv_map[0] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map[1] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map[2] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map[3] = "00000000000000002000000000000000000000000000000000000000002000200020002000000000000000000000000000000000000000000000000000000000";
lv_map[4] = "00000000002200002000000000220000000000000000000000000000002000200020002000000000000000000000000000000000000000222200000022000000";
lv_map[5] = "00000000111111111111111111111111111111111000000000000000111111111111111111111111111111111000000000000000111111111111111111111111";
lv_map[6] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map[7] = "00000000111000000000000000000000001110000000000000000000111000000000000000000000001110000000000000000000111000000000000000000000";
lv_map[8] = "00000110000011000000000000000001100000011000000000000110000011000000000000000001100000211000000000000110000011000000000000000001";
lv_map[9] = "00000000000000000000000000000000000022000000000000000000000000000000000000000000000000200000000000000022000000000000000000000000";
lv_map[10] = "10002222222222200001001000202222222222222000010010002222222222200021001000002222222222222000010010002222222222200001001000002222";
lv_map[11] = "00000000000000000000000000200000000000000220000000000000000000000020000000000000000000000000000000000000000000000220000000000000";
lv_map[12] = "22222000000000022222002222200000000000000222220022222000000000022222002222200000000000000222220022222000000000022222002222200000";
lv_map[13] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map[14] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";

// ---- the player ---------------------------------------------------------------------
pl = instance_create(0, 0, obj_player);
pl.stage = id;

/// obj_stage1 : Create
// Chip 'n Dale Rescue Rangers 2 (NES, USA) - level 1 (the restaurant).
// So far: section 1 (the dining room) with music, background, camera and the way out.
// No player, enemies, crates or hearts yet.
//
// obj_intro creates this object on the frame its last screen ends, and destroys itself.
// The code is in the END STEP event, not in Step: End Step always runs after obj_intro's Step, also on the
// frame this object is created, so the frame count does not depend on the order of the instances.
// One End Step == one NES frame (room_speed must be 60).

texture_set_interpolation(false);   // crisp pixels

lt = -8;               // level clock, +1 per frame: -7 on the frame the previous screen ended,
                       // 0 = first frame of the level's picture (still black)

// ---- controller ---------------------------------------------------------------
// bits: 1 = START, 2 = SELECT, 4 = A, 8 = UP, 16 = DOWN, 32 = B, 64 = LEFT, 128 = RIGHT
pad_prev = 255;        // buttons that were held on the previous frame (255: nothing counts as newly pressed at first)

// ---- section 1: the dining room (8 screens wide) --------------------------------
lv_done    = false;    // the section is over (black screen, the next section takes over)
lv_cam_x   = 0;        // camera: x of the left screen edge inside the section, 0 .. 1792
lv_exit_t  = -1;       // lt on which the player left the section on the right (-1 = not yet)
lv_music_a = -1;       // playing instance of snd_lv1_music_a  (level music without the 2nd square channel)
lv_music_b = -1;       // playing instance of snd_lv1_music_b  (the 2nd square channel of the level music)

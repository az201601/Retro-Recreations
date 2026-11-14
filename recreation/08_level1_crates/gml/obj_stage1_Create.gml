/// obj_stage1 : Create
// Chip 'n Dale Rescue Rangers 2 (NES, USA) - level 1 (the restaurant).
// So far: section 1 (the dining room) with music, background, camera, the player (obj_player),
// falling out of the picture, the way out, crates (obj_crate) and bonus boxes.
// No enemies or hearts yet.
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
lv_bonus     = 0;      // bonus boxes collected (0..99)  (TODO later step: where the game shows / uses it)
lv_fc        = 4;      // frame counter 0..7, +1 per frame, never set back: which sprites are in front (odd / even
                       // frames) and the flashing of a crate before and during a far throw

// sound effects (only one plays at a time): 1 pick up, 2 throw, 3 bonus, 4 far throw, 5 landing
lv_fx_k      = 0;      // the effect that is waiting to start
lv_fx_wait   = 0;      // frames until it starts (an effect starts 2 frames after its cause)
lv_fx_now    = 0;      // the effect that is playing (0 = none)
lv_fx_end    = -99;    // lt on which it is over
lv_fx_inst   = -1;     // its playing instance

// the invisible exit at the right end of the last table (in the original an object like the enemies)
lv_trig_on   = true;   // it is waiting for the player
lv_trig_wait = 0;      // frames until it looks at the player it touched

// the 16x16 blocks of the section, 128 columns x 15 rows: 0 = nothing, 1 = can be stood on, 2 = solid
// (crates are solid; bonus boxes are nothing). User Defined 0 copies this into lv_kind[row, column].
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

lv_box_n = 53;
lv_bc[0] = 30; lv_br[0] = 2; lv_bk[0] = 3; lv_bdc[0] = 12; lv_bdr[0] = 2;
lv_bc[1] = 34; lv_br[1] = 2; lv_bk[1] = 3; lv_bdc[1] = 10; lv_bdr[1] = 2;
lv_bc[2] = 90; lv_br[2] = 2; lv_bk[2] = 3; lv_bdc[2] = 2; lv_bdr[2] = 0;
lv_bc[3] = 91; lv_br[3] = 2; lv_bk[3] = 3; lv_bdc[3] = 1; lv_bdr[3] = 0;
lv_bc[4] = 16; lv_br[4] = 3; lv_bk[4] = 1; lv_bdc[4] = 10; lv_bdr[4] = 3;
lv_bc[5] = 32; lv_br[5] = 3; lv_bk[5] = 3; lv_bdc[5] = 14; lv_bdr[5] = 3;
lv_bc[6] = 36; lv_br[6] = 3; lv_bk[6] = 3; lv_bdc[6] = 10; lv_bdr[6] = 3;
lv_bc[7] = 58; lv_br[7] = 3; lv_bk[7] = 1; lv_bdc[7] = 10; lv_bdr[7] = 3;
lv_bc[8] = 62; lv_br[8] = 3; lv_bk[8] = 1; lv_bdc[8] = 14; lv_bdr[8] = 3;
lv_bc[9] = 66; lv_br[9] = 3; lv_bk[9] = 1; lv_bdc[9] = 18; lv_bdr[9] = 3;
lv_bc[10] = 70; lv_br[10] = 3; lv_bk[10] = 1; lv_bdc[10] = 14; lv_bdr[10] = 3;
lv_bc[11] = 92; lv_br[11] = 3; lv_bk[11] = 3; lv_bdc[11] = 1; lv_bdr[11] = 0;
lv_bc[12] = 10; lv_br[12] = 4; lv_bk[12] = 2; lv_bdc[12] = 10; lv_bdr[12] = 3;
lv_bc[13] = 11; lv_br[13] = 4; lv_bk[13] = 2; lv_bdc[13] = 18; lv_bdr[13] = 3;
lv_bc[14] = 16; lv_br[14] = 4; lv_bk[14] = 1; lv_bdc[14] = 10; lv_bdr[14] = 3;
lv_bc[15] = 26; lv_br[15] = 4; lv_bk[15] = 1; lv_bdc[15] = 10; lv_bdr[15] = 3;
lv_bc[16] = 27; lv_br[16] = 4; lv_bk[16] = 1; lv_bdc[16] = 10; lv_bdr[16] = 3;
lv_bc[17] = 58; lv_br[17] = 4; lv_bk[17] = 1; lv_bdc[17] = 10; lv_bdr[17] = 3;
lv_bc[18] = 62; lv_br[18] = 4; lv_bk[18] = 2; lv_bdc[18] = 13; lv_bdr[18] = 3;
lv_bc[19] = 66; lv_br[19] = 4; lv_bk[19] = 1; lv_bdc[19] = 10; lv_bdr[19] = 3;
lv_bc[20] = 70; lv_br[20] = 4; lv_bk[20] = 2; lv_bdc[20] = 13; lv_bdr[20] = 3;
lv_bc[21] = 110; lv_br[21] = 4; lv_bk[21] = 1; lv_bdc[21] = 13; lv_bdr[21] = 3;
lv_bc[22] = 111; lv_br[22] = 4; lv_bk[22] = 1; lv_bdc[22] = 14; lv_bdr[22] = 3;
lv_bc[23] = 112; lv_br[23] = 4; lv_bk[23] = 2; lv_bdc[23] = 10; lv_bdr[23] = 3;
lv_bc[24] = 113; lv_br[24] = 4; lv_bk[24] = 1; lv_bdc[24] = 35; lv_bdr[24] = 3;
lv_bc[25] = 120; lv_br[25] = 4; lv_bk[25] = 1; lv_bdc[25] = 10; lv_bdr[25] = 3;
lv_bc[26] = 121; lv_br[26] = 4; lv_bk[26] = 1; lv_bdc[26] = 10; lv_bdr[26] = 3;
lv_bc[27] = 93; lv_br[27] = 5; lv_bk[27] = 3; lv_bdc[27] = 2; lv_bdr[27] = 0;
lv_bc[28] = 93; lv_br[28] = 7; lv_bk[28] = 3; lv_bdc[28] = 2; lv_bdr[28] = 0;
lv_bc[29] = 116; lv_br[29] = 7; lv_bk[29] = 3; lv_bdc[29] = 1; lv_bdr[29] = 0;
lv_bc[30] = 20; lv_br[30] = 8; lv_bk[30] = 3; lv_bdc[30] = 2; lv_bdr[30] = 0;
lv_bc[31] = 21; lv_br[31] = 8; lv_bk[31] = 3; lv_bdc[31] = 1; lv_bdr[31] = 0;
lv_bc[32] = 74; lv_br[32] = 8; lv_bk[32] = 3; lv_bdc[32] = 2; lv_bdr[32] = 0;
lv_bc[33] = 75; lv_br[33] = 8; lv_bk[33] = 3; lv_bdc[33] = 1; lv_bdr[33] = 0;
lv_bc[34] = 86; lv_br[34] = 8; lv_bk[34] = 1; lv_bdc[34] = 2; lv_bdr[34] = 0;
lv_bc[35] = 36; lv_br[35] = 9; lv_bk[35] = 1; lv_bdc[35] = 84; lv_bdr[35] = 9;
lv_bc[36] = 37; lv_br[36] = 9; lv_bk[36] = 1; lv_bdc[36] = 2; lv_bdr[36] = 0;
lv_bc[37] = 86; lv_br[37] = 9; lv_bk[37] = 1; lv_bdc[37] = 4; lv_bdr[37] = 9;
lv_bc[38] = 93; lv_br[38] = 9; lv_bk[38] = 3; lv_bdc[38] = 2; lv_bdr[38] = 0;
lv_bc[39] = 102; lv_br[39] = 9; lv_bk[39] = 1; lv_bdc[39] = 6; lv_bdr[39] = 9;
lv_bc[40] = 103; lv_br[40] = 9; lv_bk[40] = 1; lv_bdc[40] = 7; lv_bdr[40] = 9;
lv_bc[41] = 117; lv_br[41] = 9; lv_bk[41] = 3; lv_bdc[41] = 2; lv_bdr[41] = 0;
lv_bc[42] = 16; lv_br[42] = 10; lv_bk[42] = 3; lv_bdc[42] = 2; lv_bdr[42] = 0;
lv_bc[43] = 26; lv_br[43] = 10; lv_bk[43] = 1; lv_bdc[43] = 2; lv_bdr[43] = 0;
lv_bc[44] = 66; lv_br[44] = 10; lv_bk[44] = 1; lv_bdc[44] = 2; lv_bdr[44] = 0;
lv_bc[45] = 16; lv_br[45] = 11; lv_bk[45] = 3; lv_bdc[45] = 1; lv_bdr[45] = 0;
lv_bc[46] = 26; lv_br[46] = 11; lv_bk[46] = 2; lv_bdc[46] = 1; lv_bdr[46] = 0;
lv_bc[47] = 41; lv_br[47] = 11; lv_bk[47] = 2; lv_bdc[47] = 2; lv_bdr[47] = 0;
lv_bc[48] = 42; lv_br[48] = 11; lv_bk[48] = 1; lv_bdc[48] = 1; lv_bdr[48] = 0;
lv_bc[49] = 66; lv_br[49] = 11; lv_bk[49] = 1; lv_bdc[49] = 1; lv_bdr[49] = 0;
lv_bc[50] = 113; lv_br[50] = 11; lv_bk[50] = 1; lv_bdc[50] = 2; lv_bdr[50] = 0;
lv_bc[51] = 114; lv_br[51] = 11; lv_bk[51] = 1; lv_bdc[51] = 1; lv_bdr[51] = 0;
lv_bc[52] = 116; lv_br[52] = 11; lv_bk[52] = 3; lv_bdc[52] = 1; lv_bdr[52] = 0;
lv_rbox_c = 30; lv_rbox_r = 2;      // a bonus box in the background picture (shown where a crate had one inside)

// lv_kind, lv_box and the list of opened boxes: built now, and again whenever the section restarts
event_user(0);

// ---- the player ---------------------------------------------------------------------
pl = instance_create(0, 0, obj_player);
pl.stage = id;

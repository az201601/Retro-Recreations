/// obj_stage1 : Create
// Chip 'n Dale Rescue Rangers 2 (NES, USA) - level 1 (the restaurant).
// So far: section 1 (the dining room) with music, background, camera, the player (obj_player),
// falling out of the picture, the way out, crates (obj_crate), bonus boxes and enemies (obj_enemy).
// The enemies cannot hurt the player yet; no hearts yet.
//
// obj_intro creates this object on the frame its last screen ends, and destroys itself.
// The code is in the END STEP event, not in Step: End Step always runs after obj_intro's Step, also on the
// frame this object is created, so the frame count does not depend on the order of the instances.
// One End Step == one NES frame (room_speed must be 60).
// The player, the crates and the enemies are separate objects without a Step event; this object runs their
// code (User Defined 0) in a fixed order.

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
lv_fc        = 4;      // frame counter 0..7, +1 per frame, never set back: the flashing of a crate before and
                       // during a far throw, and lv_ord
lv_ord       = 0;      // which sprites are in front: changes with every frame of the game (not while it stands still)
lv_ran       = false;  // the game ran on the previous frame

// sound effects (only one plays at a time): 1 pick up, 2 throw, 3 bonus, 4 far throw, 5 landing,
// 6 the flyer's buzz, 7 the cook throws, 8 an enemy is knocked out
lv_snd       = 0;      // the sound the crates and enemies ask for on this frame (the last one to ask is heard)
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

// the objects of the section in the order the camera reaches them (from the ROM): column, row, kind (1 flyer, 3 cook,
// 9 the exit). One enters when the column 264 pixels right of the camera becomes its column; it starts at
// x = column * 16, y = row * 16 - 512.
lv_ob_n = 12;
lv_ob_c[0] = 24; lv_ob_r[0] = 34; lv_ob_k[0] = 1;
lv_ob_c[1] = 32; lv_ob_r[1] = 42; lv_ob_k[1] = 3;
lv_ob_c[2] = 40; lv_ob_r[2] = 36; lv_ob_k[2] = 1;
lv_ob_c[3] = 51; lv_ob_r[3] = 44; lv_ob_k[3] = 3;
lv_ob_c[4] = 68; lv_ob_r[4] = 34; lv_ob_k[4] = 1;
lv_ob_c[5] = 78; lv_ob_r[5] = 37; lv_ob_k[5] = 3;
lv_ob_c[6] = 86; lv_ob_r[6] = 38; lv_ob_k[6] = 1;
lv_ob_c[7] = 98; lv_ob_r[7] = 36; lv_ob_k[7] = 1;
lv_ob_c[8] = 108; lv_ob_r[8] = 37; lv_ob_k[8] = 3;
lv_ob_c[9] = 119; lv_ob_r[9] = 34; lv_ob_k[9] = 1;
lv_ob_c[10] = 121; lv_ob_r[10] = 44; lv_ob_k[10] = 3;
lv_ob_c[11] = 126; lv_ob_r[11] = 42; lv_ob_k[11] = 9;
en_walk[0] = 8; en_walk[1] = 9; en_walk[2] = 10; en_walk[3] = 9;      // the cook's walking pictures
// the flyer's pictures while it hovers (4 frames each)
en_hover[0] = 24; en_hover[1] = 25; en_hover[2] = 24; en_hover[3] = 25; en_hover[4] = 26; en_hover[5] = 27; en_hover[6] = 26; en_hover[7] = 27; en_hover[8] = 22; en_hover[9] = 23; en_hover[10] = 22; en_hover[11] = 23;

// enemy pictures (the numbers are the original picture numbers): tile i of picture c is drawn at
// (x + en_tdx, y + en_tdy + 1) facing left, (x - en_tdx - 8, ...) facing right; sub-image (en_tim * 2 + facing) * 7 + brightness.
// The tiles are in the order of the NES sprite list.
en_tn[7] = 14;
en_tdx[7,0] = -21; en_tdy[7,0] = -33; en_tim[7,0] = 0; en_tdx[7,1] = -13; en_tdy[7,1] = -33; en_tim[7,1] = 1; en_tdx[7,2] = 0; en_tdy[7,2] = -33; en_tim[7,2] = 2; en_tdx[7,3] = -13; en_tdy[7,3] = -25; en_tim[7,3] = 3; en_tdx[7,4] = -8; en_tdy[7,4] = -17; en_tim[7,4] = 4; en_tdx[7,5] = 0; en_tdy[7,5] = -17; en_tim[7,5] = 5; en_tdx[7,6] = 8; en_tdy[7,6] = -17; en_tim[7,6] = 6; en_tdx[7,7] = -8; en_tdy[7,7] = -9; en_tim[7,7] = 7; en_tdx[7,8] = 0; en_tdy[7,8] = -9; en_tim[7,8] = 8; en_tdx[7,9] = 8; en_tdy[7,9] = -9; en_tim[7,9] = 9; en_tdx[7,10] = -4; en_tdy[7,10] = -25; en_tim[7,10] = 10; en_tdx[7,11] = 4; en_tdy[7,11] = -25; en_tim[7,11] = 11; en_tdx[7,12] = -1; en_tdy[7,12] = -25; en_tim[7,12] = 12; en_tdx[7,13] = 2; en_tdy[7,13] = -15; en_tim[7,13] = 13;
en_tn[8] = 14;
en_tdx[8,0] = -22; en_tdy[8,0] = -33; en_tim[8,0] = 0; en_tdx[8,1] = -14; en_tdy[8,1] = -33; en_tim[8,1] = 1; en_tdx[8,2] = -1; en_tdy[8,2] = -33; en_tim[8,2] = 2; en_tdx[8,3] = -14; en_tdy[8,3] = -25; en_tim[8,3] = 3; en_tdx[8,4] = -9; en_tdy[8,4] = -17; en_tim[8,4] = 4; en_tdx[8,5] = -1; en_tdy[8,5] = -17; en_tim[8,5] = 5; en_tdx[8,6] = 7; en_tdy[8,6] = -17; en_tim[8,6] = 6; en_tdx[8,7] = -9; en_tdy[8,7] = -9; en_tim[8,7] = 7; en_tdx[8,8] = -1; en_tdy[8,8] = -9; en_tim[8,8] = 14; en_tdx[8,9] = 7; en_tdy[8,9] = -9; en_tim[8,9] = 15; en_tdx[8,10] = -5; en_tdy[8,10] = -25; en_tim[8,10] = 10; en_tdx[8,11] = 3; en_tdy[8,11] = -25; en_tim[8,11] = 11; en_tdx[8,12] = -2; en_tdy[8,12] = -25; en_tim[8,12] = 12; en_tdx[8,13] = 1; en_tdy[8,13] = -15; en_tim[8,13] = 13;
en_tn[9] = 15;
en_tdx[9,0] = -22; en_tdy[9,0] = -34; en_tim[9,0] = 0; en_tdx[9,1] = -14; en_tdy[9,1] = -34; en_tim[9,1] = 1; en_tdx[9,2] = -1; en_tdy[9,2] = -34; en_tim[9,2] = 2; en_tdx[9,3] = -14; en_tdy[9,3] = -26; en_tim[9,3] = 3; en_tdx[9,4] = -9; en_tdy[9,4] = -18; en_tim[9,4] = 4; en_tdx[9,5] = -1; en_tdy[9,5] = -18; en_tim[9,5] = 5; en_tdx[9,6] = 7; en_tdy[9,6] = -18; en_tim[9,6] = 16; en_tdx[9,7] = -9; en_tdy[9,7] = -10; en_tim[9,7] = 7; en_tdx[9,8] = -1; en_tdy[9,8] = -10; en_tim[9,8] = 17; en_tdx[9,9] = 7; en_tdy[9,9] = -10; en_tim[9,9] = 18; en_tdx[9,10] = -5; en_tdy[9,10] = -26; en_tim[9,10] = 10; en_tdx[9,11] = 3; en_tdy[9,11] = -26; en_tim[9,11] = 11; en_tdx[9,12] = -2; en_tdy[9,12] = -26; en_tim[9,12] = 12; en_tdx[9,13] = 1; en_tdy[9,13] = -16; en_tim[9,13] = 13; en_tdx[9,14] = 6; en_tdy[9,14] = -2; en_tim[9,14] = 19;
en_tn[10] = 14;
en_tdx[10,0] = -22; en_tdy[10,0] = -33; en_tim[10,0] = 0; en_tdx[10,1] = -14; en_tdy[10,1] = -33; en_tim[10,1] = 1; en_tdx[10,2] = -1; en_tdy[10,2] = -33; en_tim[10,2] = 2; en_tdx[10,3] = -14; en_tdy[10,3] = -25; en_tim[10,3] = 3; en_tdx[10,4] = -9; en_tdy[10,4] = -17; en_tim[10,4] = 4; en_tdx[10,5] = -1; en_tdy[10,5] = -17; en_tim[10,5] = 5; en_tdx[10,6] = 7; en_tdy[10,6] = -17; en_tim[10,6] = 6; en_tdx[10,7] = -9; en_tdy[10,7] = -9; en_tim[10,7] = 7; en_tdx[10,8] = -1; en_tdy[10,8] = -9; en_tim[10,8] = 20; en_tdx[10,9] = 7; en_tdy[10,9] = -9; en_tim[10,9] = 21; en_tdx[10,10] = -5; en_tdy[10,10] = -25; en_tim[10,10] = 10; en_tdx[10,11] = 3; en_tdy[10,11] = -25; en_tim[10,11] = 11; en_tdx[10,12] = -2; en_tdy[10,12] = -25; en_tim[10,12] = 12; en_tdx[10,13] = 1; en_tdy[10,13] = -15; en_tim[10,13] = 13;
en_tn[12] = 13;
en_tdx[12,0] = 8; en_tdy[12,0] = -41; en_tim[12,0] = 22; en_tdx[12,1] = 8; en_tdy[12,1] = -33; en_tim[12,1] = 23; en_tdx[12,2] = 8; en_tdy[12,2] = -25; en_tim[12,2] = 24; en_tdx[12,3] = 8; en_tdy[12,3] = -17; en_tim[12,3] = 25; en_tdx[12,4] = 8; en_tdy[12,4] = -9; en_tim[12,4] = 9; en_tdx[12,5] = 0; en_tdy[12,5] = -33; en_tim[12,5] = 26; en_tdx[12,6] = 0; en_tdy[12,6] = -25; en_tim[12,6] = 27; en_tdx[12,7] = 0; en_tdy[12,7] = -17; en_tim[12,7] = 28; en_tdx[12,8] = 0; en_tdy[12,8] = -9; en_tim[12,8] = 29; en_tdx[12,9] = 1; en_tdy[12,9] = -26; en_tim[12,9] = 12; en_tdx[12,10] = -8; en_tdy[12,10] = -25; en_tim[12,10] = 30; en_tdx[12,11] = -8; en_tdy[12,11] = -17; en_tim[12,11] = 31; en_tdx[12,12] = 3; en_tdy[12,12] = -14; en_tim[12,12] = 32;
en_tn[13] = 10;
en_tdx[13,0] = -8; en_tdy[13,0] = -25; en_tim[13,0] = 33; en_tdx[13,1] = -8; en_tdy[13,1] = -17; en_tim[13,1] = 34; en_tdx[13,2] = -8; en_tdy[13,2] = -9; en_tim[13,2] = 35; en_tdx[13,3] = 0; en_tdy[13,3] = -25; en_tim[13,3] = 36; en_tdx[13,4] = 0; en_tdy[13,4] = -17; en_tim[13,4] = 37; en_tdx[13,5] = 0; en_tdy[13,5] = -9; en_tim[13,5] = 38; en_tdx[13,6] = -5; en_tdy[13,6] = -23; en_tim[13,6] = 12; en_tdx[13,7] = 8; en_tdy[13,7] = -17; en_tim[13,7] = 39; en_tdx[13,8] = 8; en_tdy[13,8] = -9; en_tim[13,8] = 9; en_tdx[13,9] = 2; en_tdy[13,9] = -13; en_tim[13,9] = 40;
en_tn[14] = 4;
en_tdx[14,0] = -16; en_tdy[14,0] = -8; en_tim[14,0] = 41; en_tdx[14,1] = -8; en_tdy[14,1] = -8; en_tim[14,1] = 42; en_tdx[14,2] = 0; en_tdy[14,2] = -8; en_tim[14,2] = 43; en_tdx[14,3] = 8; en_tdy[14,3] = -8; en_tim[14,3] = 44;
en_tn[22] = 10;
en_tdx[22,0] = -8; en_tdy[22,0] = -24; en_tim[22,0] = 45; en_tdx[22,1] = 0; en_tdy[22,1] = -24; en_tim[22,1] = 46; en_tdx[22,2] = -1; en_tdy[22,2] = -26; en_tim[22,2] = 47; en_tdx[22,3] = -8; en_tdy[22,3] = -24; en_tim[22,3] = 48; en_tdx[22,4] = -8; en_tdy[22,4] = -16; en_tim[22,4] = 49; en_tdx[22,5] = -8; en_tdy[22,5] = -8; en_tim[22,5] = 50; en_tdx[22,6] = 0; en_tdy[22,6] = -16; en_tim[22,6] = 51; en_tdx[22,7] = 0; en_tdy[22,7] = -8; en_tim[22,7] = 52; en_tdx[22,8] = -8; en_tdy[22,8] = -11; en_tim[22,8] = 53; en_tdx[22,9] = 0; en_tdy[22,9] = -10; en_tim[22,9] = 54;
en_tn[23] = 10;
en_tdx[23,0] = -8; en_tdy[23,0] = -24; en_tim[23,0] = 48; en_tdx[23,1] = -8; en_tdy[23,1] = -16; en_tim[23,1] = 49; en_tdx[23,2] = -8; en_tdy[23,2] = -8; en_tim[23,2] = 50; en_tdx[23,3] = -8; en_tdy[23,3] = -24; en_tim[23,3] = 45; en_tdx[23,4] = 0; en_tdy[23,4] = -24; en_tim[23,4] = 46; en_tdx[23,5] = 0; en_tdy[23,5] = -24; en_tim[23,5] = 55; en_tdx[23,6] = 0; en_tdy[23,6] = -16; en_tim[23,6] = 51; en_tdx[23,7] = 0; en_tdy[23,7] = -8; en_tim[23,7] = 52; en_tdx[23,8] = -8; en_tdy[23,8] = -11; en_tim[23,8] = 53; en_tdx[23,9] = 0; en_tdy[23,9] = -10; en_tim[23,9] = 54;
en_tn[24] = 10;
en_tdx[24,0] = -8; en_tdy[24,0] = -24; en_tim[24,0] = 45; en_tdx[24,1] = 0; en_tdy[24,1] = -24; en_tim[24,1] = 46; en_tdx[24,2] = -1; en_tdy[24,2] = -26; en_tim[24,2] = 47; en_tdx[24,3] = -8; en_tdy[24,3] = -24; en_tim[24,3] = 48; en_tdx[24,4] = -8; en_tdy[24,4] = -16; en_tim[24,4] = 49; en_tdx[24,5] = -8; en_tdy[24,5] = -8; en_tim[24,5] = 56; en_tdx[24,6] = 0; en_tdy[24,6] = -16; en_tim[24,6] = 51; en_tdx[24,7] = 0; en_tdy[24,7] = -8; en_tim[24,7] = 52; en_tdx[24,8] = -8; en_tdy[24,8] = -11; en_tim[24,8] = 53; en_tdx[24,9] = 0; en_tdy[24,9] = -10; en_tim[24,9] = 54;
en_tn[25] = 10;
en_tdx[25,0] = -8; en_tdy[25,0] = -24; en_tim[25,0] = 48; en_tdx[25,1] = -8; en_tdy[25,1] = -16; en_tim[25,1] = 49; en_tdx[25,2] = -8; en_tdy[25,2] = -8; en_tim[25,2] = 56; en_tdx[25,3] = -8; en_tdy[25,3] = -24; en_tim[25,3] = 45; en_tdx[25,4] = 0; en_tdy[25,4] = -24; en_tim[25,4] = 46; en_tdx[25,5] = 0; en_tdy[25,5] = -24; en_tim[25,5] = 55; en_tdx[25,6] = 0; en_tdy[25,6] = -16; en_tim[25,6] = 51; en_tdx[25,7] = 0; en_tdy[25,7] = -8; en_tim[25,7] = 52; en_tdx[25,8] = -8; en_tdy[25,8] = -11; en_tim[25,8] = 53; en_tdx[25,9] = 0; en_tdy[25,9] = -10; en_tim[25,9] = 54;
en_tn[26] = 10;
en_tdx[26,0] = -8; en_tdy[26,0] = -24; en_tim[26,0] = 45; en_tdx[26,1] = 0; en_tdy[26,1] = -24; en_tim[26,1] = 46; en_tdx[26,2] = -1; en_tdy[26,2] = -26; en_tim[26,2] = 47; en_tdx[26,3] = -8; en_tdy[26,3] = -24; en_tim[26,3] = 48; en_tdx[26,4] = -8; en_tdy[26,4] = -16; en_tim[26,4] = 49; en_tdx[26,5] = -8; en_tdy[26,5] = -8; en_tim[26,5] = 57; en_tdx[26,6] = 0; en_tdy[26,6] = -16; en_tim[26,6] = 51; en_tdx[26,7] = 0; en_tdy[26,7] = -8; en_tim[26,7] = 52; en_tdx[26,8] = -8; en_tdy[26,8] = -11; en_tim[26,8] = 53; en_tdx[26,9] = 0; en_tdy[26,9] = -10; en_tim[26,9] = 54;
en_tn[27] = 10;
en_tdx[27,0] = -8; en_tdy[27,0] = -24; en_tim[27,0] = 48; en_tdx[27,1] = -8; en_tdy[27,1] = -16; en_tim[27,1] = 49; en_tdx[27,2] = -8; en_tdy[27,2] = -8; en_tim[27,2] = 57; en_tdx[27,3] = -8; en_tdy[27,3] = -24; en_tim[27,3] = 45; en_tdx[27,4] = 0; en_tdy[27,4] = -24; en_tim[27,4] = 46; en_tdx[27,5] = 0; en_tdy[27,5] = -24; en_tim[27,5] = 55; en_tdx[27,6] = 0; en_tdy[27,6] = -16; en_tim[27,6] = 51; en_tdx[27,7] = 0; en_tdy[27,7] = -8; en_tim[27,7] = 52; en_tdx[27,8] = -8; en_tdy[27,8] = -11; en_tim[27,8] = 53; en_tdx[27,9] = 0; en_tdy[27,9] = -10; en_tim[27,9] = 54;
en_tn[28] = 2;
en_tdx[28,0] = -7; en_tdy[28,0] = -8; en_tim[28,0] = 58; en_tdx[28,1] = -7; en_tdy[28,1] = 0; en_tim[28,1] = 59;
// a crate that hit an enemy flies apart: its quarters (0 top left, 1 bottom left, 2 top right, 3 bottom right) on the
// frames 2..6 after the hit, relative to the crate (x, y)
cr_pdx[3,0] = -7; cr_pdy[3,0] = -15; cr_pq[3,0] = 0; cr_pdx[3,1] = -1; cr_pdy[3,1] = -15; cr_pq[3,1] = 2; cr_pdx[3,2] = -7; cr_pdy[3,2] = -9; cr_pq[3,2] = 1; cr_pdx[3,3] = -1; cr_pdy[3,3] = -9; cr_pq[3,3] = 3;
cr_pdx[4,0] = -9; cr_pdy[4,0] = -17; cr_pq[4,0] = 0; cr_pdx[4,1] = 1; cr_pdy[4,1] = -17; cr_pq[4,1] = 2; cr_pdx[4,2] = -9; cr_pdy[4,2] = -7; cr_pq[4,2] = 1; cr_pdx[4,3] = 1; cr_pdy[4,3] = -7; cr_pq[4,3] = 3;
cr_pdx[5,0] = -11; cr_pdy[5,0] = -19; cr_pq[5,0] = 0; cr_pdx[5,1] = 3; cr_pdy[5,1] = -19; cr_pq[5,1] = 2; cr_pdx[5,2] = -11; cr_pdy[5,2] = -5; cr_pq[5,2] = 1; cr_pdx[5,3] = 3; cr_pdy[5,3] = -5; cr_pq[5,3] = 3;
cr_pdx[6,0] = -13; cr_pdy[6,0] = -21; cr_pq[6,0] = 0; cr_pdx[6,1] = 5; cr_pdy[6,1] = -21; cr_pq[6,1] = 2; cr_pdx[6,2] = -13; cr_pdy[6,2] = -3; cr_pq[6,2] = 1; cr_pdx[6,3] = 5; cr_pdy[6,3] = -3; cr_pq[6,3] = 3;
cr_pdx[7,0] = -15; cr_pdy[7,0] = -23; cr_pq[7,0] = 0; cr_pdx[7,1] = 7; cr_pdy[7,1] = -23; cr_pq[7,1] = 2; cr_pdx[7,2] = -15; cr_pdy[7,2] = -1; cr_pq[7,2] = 1; cr_pdx[7,3] = 7; cr_pdy[7,3] = -1; cr_pq[7,3] = 3;

// lv_kind, lv_box, the list of opened boxes and the object list: built now, and again whenever the section restarts
event_user(0);

// ---- the player ---------------------------------------------------------------------
pl = instance_create(0, 0, obj_player);
pl.stage = id;

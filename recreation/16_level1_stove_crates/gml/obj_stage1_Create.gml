/// obj_stage1 : Create
// Chip 'n Dale Rescue Rangers 2 (NES, USA) - level 1 (the restaurant).
// So far: section 1 (the dining room) with music, background, camera, the player (obj_player),
// falling out of the picture, the way out, crates (obj_crate), bonus boxes, enemies (obj_enemy), hearts,
// lives, the status screen (SELECT), GAME OVER and the continue screen.
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
lv_sec       = 0;      // the section: 0 the dining room, 1 the kitchen, 2 the stove and the sink
lv_rows      = 15;     // rows of 16x16 blocks in the section (the kitchen is two screens high: 30)
lv_cam_y     = 0;      // camera: y of the top screen edge inside the section. Always 0 in the dining room;
                       // the kitchen starts at 240 (its lower floor) and goes up to 0 in the shaft, never down
lv_cam_yshow = 0;      // the one the Draw event shows
lv_cam_yold  = 0;      // the one it showed a frame earlier (the shaft's picture lags behind, see Draw)
lv_bright    = -1;     // brightness of the picture: 0..2 fade-in, 3 normal, 4..6 fade-out, -1 black
lv_exit_t    = -1;     // lt on which the player left the section on the right (-1 = not yet)
lv_restart_t = -1;     // lt on which the wait after a fall ended (-1 = no restart going on)
lv_pad_keep = 0;       // buttons the single early run of the game gets (see End Step)
lv_pressed_keep = 0;
lv_lives     = 3;      // lives left; a fall or the last heart costs one; at 0: GAME OVER
lv_credits   = 3;      // continues left
lv_music_on  = false;  // the level music has been started
lv_music_a   = -1;     // playing instance of snd_lv1_music_a  (level music without the 2nd square channel)
lv_music_b   = -1;     // playing instance of snd_lv1_music_b  (the 2nd square channel of the level music)
lv_bonus     = 0;      // bonus boxes collected (0..99), shown on the status screen; back to 0 at GAME OVER
lv_fc        = 4;      // frame counter 0..7, +1 per frame, never set back: the flashing of a crate before and
                       // during a far throw, and lv_ord
lv_ord       = 0;      // which sprites are in front: changes with every frame of the game (not while it stands still)
lv_ran       = false;  // the game ran on the previous frame

// sound effects (only one plays at a time): 1 pick up, 2 throw, 3 bonus, 4 far throw, 5 landing,
// 6 the flyer's buzz, 7 the cook throws, 8 an enemy is knocked out, 9 hurt, 10 stunned
lv_snd       = 0;      // the sound the crates and enemies ask for on this frame (the last one to ask is heard)
lv_fx_k      = 0;      // the effect that is waiting to start
lv_fx_wait   = 0;      // frames until it starts (an effect starts 2 frames after its cause)
lv_fx_now    = 0;      // the effect that is playing (0 = none)
lv_fx_end    = -99;    // lt on which it is over
lv_fx_inst   = -1;     // its playing instance

// ---- the hearts in the corner (shown one frame behind, like everything) ---------------------
s_hp         = 3;      // hearts shown
s_lives      = 3;      // (the face above the hearts goes when the last life is gone)
lv_star      = 0;      // the place in the object list of the star over a stunned player (0 = not stunned, -1 = stunned without a star: the list was full)

// ---- the status screen (SELECT): the game stands still ---------------------------------------
lv_stat      = 0;      // 0 not shown, 1 open, 2 closing
lv_stat_t    = 0;      // frames since then
lv_stat_ord  = 0;      // lv_ord when it was opened (decides which of two overlapping sprites of the screen is in front)
lv_stat_pad  = 0;      // the buttons of the frame SELECT closed it: the game gets them on its first frame
lv_stat_now  = 0;
lv_view      = 1;      // what the Draw event shows: 1 the level, 0 black, 2 the status screen
lv_paused    = false;  // the sounds are paused
lv_resume    = 0;      // frames until they go on

// ---- GAME OVER and the continue screen -------------------------------------------------------
lv_go        = 0;      // 0 no, 2 GAME OVER, 3 the continue screen, 4 CONTINUE chosen, 5 END chosen
lv_go_t      = 0;      // frames since then (GAME OVER: since the wait after the last fall ended)
go_bright    = -1;     // brightness of these screens: 0..2 fade-in, 3 normal, 4..6 fade-out, -1 black
go_cur       = 0;      // the arrow: 0 CONTINUE, 1 END
s_cur        = 0;      // ... as shown (one frame behind)
s_credits    = 3;      // the number shown after CREDIT
go_snd       = 0;      // frames until the sound go_k starts
go_k         = 0;      // 11 the arrow moved, 12 chosen, 13 the GAME OVER tune
go_inst      = -1;     // the playing arrow / choice sound
go_pressed   = 0;      // the buttons that went down on this frame
go_t3        = 0;      // lv_go_t of the continue screen when A was pressed (the star goes on from there)
// the continue screen: the star goes round the head (7 places, 4 frames each)
go_sx[0] = 108; go_sy[0] = 130; go_sx[1] = 104; go_sy[1] = 130; go_sx[2] = 102; go_sy[2] = 128; go_sx[3] = 104; go_sy[3] = 125; go_sx[4] = 108; go_sy[4] = 125; go_sx[5] = 112; go_sy[5] = 125; go_sx[6] = 114; go_sy[6] = 128;
// CONTINUE: gets up with a jump, runs off to the right.  Picture, x, y on the frames 2, 3, ... after the A button (102 frames)
go_cn = 102;
go_cp[0] = 5; go_cx[0] = 112; go_cy[0] = 158; go_cp[1] = 5; go_cx[1] = 112; go_cy[1] = 156; go_cp[2] = 5; go_cx[2] = 112; go_cy[2] = 154; go_cp[3] = 5; go_cx[3] = 112; go_cy[3] = 153; go_cp[4] = 5; go_cx[4] = 112; go_cy[4] = 152; go_cp[5] = 5; go_cx[5] = 112; go_cy[5] = 151; go_cp[6] = 5; go_cx[6] = 112; go_cy[6] = 150; go_cp[7] = 5; go_cx[7] = 112; go_cy[7] = 150;
go_cp[8] = 5; go_cx[8] = 112; go_cy[8] = 149; go_cp[9] = 5; go_cx[9] = 112; go_cy[9] = 149; go_cp[10] = 5; go_cx[10] = 112; go_cy[10] = 149; go_cp[11] = 5; go_cx[11] = 112; go_cy[11] = 149; go_cp[12] = 5; go_cx[12] = 112; go_cy[12] = 150; go_cp[13] = 5; go_cx[13] = 112; go_cy[13] = 150; go_cp[14] = 5; go_cx[14] = 112; go_cy[14] = 151; go_cp[15] = 5; go_cx[15] = 112; go_cy[15] = 152;
go_cp[16] = 5; go_cx[16] = 112; go_cy[16] = 153; go_cp[17] = 5; go_cx[17] = 112; go_cy[17] = 154; go_cp[18] = 5; go_cx[18] = 112; go_cy[18] = 156; go_cp[19] = 5; go_cx[19] = 112; go_cy[19] = 158; go_cp[20] = 5; go_cx[20] = 112; go_cy[20] = 160; go_cp[21] = 4; go_cx[21] = 112; go_cy[21] = 160; go_cp[22] = 4; go_cx[22] = 112; go_cy[22] = 160; go_cp[23] = 4; go_cx[23] = 112; go_cy[23] = 160;
go_cp[24] = 4; go_cx[24] = 112; go_cy[24] = 160; go_cp[25] = 4; go_cx[25] = 112; go_cy[25] = 160; go_cp[26] = 4; go_cx[26] = 112; go_cy[26] = 160; go_cp[27] = 4; go_cx[27] = 112; go_cy[27] = 160; go_cp[28] = 4; go_cx[28] = 112; go_cy[28] = 160; go_cp[29] = 4; go_cx[29] = 112; go_cy[29] = 160; go_cp[30] = 4; go_cx[30] = 112; go_cy[30] = 160; go_cp[31] = 4; go_cx[31] = 112; go_cy[31] = 160;
go_cp[32] = 0; go_cx[32] = 112; go_cy[32] = 160; go_cp[33] = 0; go_cx[33] = 112; go_cy[33] = 160; go_cp[34] = 0; go_cx[34] = 112; go_cy[34] = 160; go_cp[35] = 0; go_cx[35] = 112; go_cy[35] = 160; go_cp[36] = 0; go_cx[36] = 112; go_cy[36] = 160; go_cp[37] = 0; go_cx[37] = 112; go_cy[37] = 160; go_cp[38] = 1; go_cx[38] = 114; go_cy[38] = 160; go_cp[39] = 1; go_cx[39] = 116; go_cy[39] = 160;
go_cp[40] = 1; go_cx[40] = 118; go_cy[40] = 160; go_cp[41] = 1; go_cx[41] = 120; go_cy[41] = 160; go_cp[42] = 1; go_cx[42] = 122; go_cy[42] = 160; go_cp[43] = 1; go_cx[43] = 124; go_cy[43] = 160; go_cp[44] = 1; go_cx[44] = 126; go_cy[44] = 160; go_cp[45] = 1; go_cx[45] = 128; go_cy[45] = 160; go_cp[46] = 2; go_cx[46] = 130; go_cy[46] = 160; go_cp[47] = 2; go_cx[47] = 132; go_cy[47] = 160;
go_cp[48] = 2; go_cx[48] = 134; go_cy[48] = 160; go_cp[49] = 2; go_cx[49] = 136; go_cy[49] = 160; go_cp[50] = 2; go_cx[50] = 138; go_cy[50] = 160; go_cp[51] = 2; go_cx[51] = 140; go_cy[51] = 160; go_cp[52] = 2; go_cx[52] = 142; go_cy[52] = 160; go_cp[53] = 2; go_cx[53] = 144; go_cy[53] = 160; go_cp[54] = 3; go_cx[54] = 146; go_cy[54] = 160; go_cp[55] = 3; go_cx[55] = 148; go_cy[55] = 160;
go_cp[56] = 3; go_cx[56] = 150; go_cy[56] = 160; go_cp[57] = 3; go_cx[57] = 152; go_cy[57] = 160; go_cp[58] = 3; go_cx[58] = 154; go_cy[58] = 160; go_cp[59] = 3; go_cx[59] = 156; go_cy[59] = 160; go_cp[60] = 3; go_cx[60] = 158; go_cy[60] = 160; go_cp[61] = 3; go_cx[61] = 160; go_cy[61] = 160; go_cp[62] = 2; go_cx[62] = 162; go_cy[62] = 160; go_cp[63] = 2; go_cx[63] = 164; go_cy[63] = 160;
go_cp[64] = 2; go_cx[64] = 166; go_cy[64] = 160; go_cp[65] = 2; go_cx[65] = 168; go_cy[65] = 160; go_cp[66] = 2; go_cx[66] = 170; go_cy[66] = 160; go_cp[67] = 2; go_cx[67] = 172; go_cy[67] = 160; go_cp[68] = 2; go_cx[68] = 174; go_cy[68] = 160; go_cp[69] = 2; go_cx[69] = 176; go_cy[69] = 160; go_cp[70] = 1; go_cx[70] = 178; go_cy[70] = 160; go_cp[71] = 1; go_cx[71] = 180; go_cy[71] = 160;
go_cp[72] = 1; go_cx[72] = 182; go_cy[72] = 160; go_cp[73] = 1; go_cx[73] = 184; go_cy[73] = 160; go_cp[74] = 1; go_cx[74] = 186; go_cy[74] = 160; go_cp[75] = 1; go_cx[75] = 188; go_cy[75] = 160; go_cp[76] = 1; go_cx[76] = 190; go_cy[76] = 160; go_cp[77] = 1; go_cx[77] = 192; go_cy[77] = 160; go_cp[78] = 2; go_cx[78] = 194; go_cy[78] = 160; go_cp[79] = 2; go_cx[79] = 196; go_cy[79] = 160;
go_cp[80] = 2; go_cx[80] = 198; go_cy[80] = 160; go_cp[81] = 2; go_cx[81] = 200; go_cy[81] = 160; go_cp[82] = 2; go_cx[82] = 202; go_cy[82] = 160; go_cp[83] = 2; go_cx[83] = 204; go_cy[83] = 160; go_cp[84] = 2; go_cx[84] = 206; go_cy[84] = 160; go_cp[85] = 2; go_cx[85] = 208; go_cy[85] = 160; go_cp[86] = 3; go_cx[86] = 210; go_cy[86] = 160; go_cp[87] = 3; go_cx[87] = 212; go_cy[87] = 160;
go_cp[88] = 3; go_cx[88] = 214; go_cy[88] = 160; go_cp[89] = 3; go_cx[89] = 216; go_cy[89] = 160; go_cp[90] = 3; go_cx[90] = 218; go_cy[90] = 160; go_cp[91] = 3; go_cx[91] = 220; go_cy[91] = 160; go_cp[92] = 3; go_cx[92] = 222; go_cy[92] = 160; go_cp[93] = 3; go_cx[93] = 224; go_cy[93] = 160; go_cp[94] = 2; go_cx[94] = 226; go_cy[94] = 160; go_cp[95] = 2; go_cx[95] = 228; go_cy[95] = 160;
go_cp[96] = 2; go_cx[96] = 230; go_cy[96] = 160; go_cp[97] = 2; go_cx[97] = 232; go_cy[97] = 160; go_cp[98] = 2; go_cx[98] = 234; go_cy[98] = 160; go_cp[99] = 2; go_cx[99] = 236; go_cy[99] = 160; go_cp[100] = 2; go_cx[100] = 238; go_cy[100] = 160; go_cp[101] = 2; go_cx[101] = 240; go_cy[101] = 160;
// END: thrown out to the lower left.  Picture, x, y on the frames 2, 3, ... after the A button (42 frames)
go_en = 42;
go_ep[0] = 14; go_ex[0] = 111; go_ey[0] = 157; go_ep[1] = 14; go_ex[1] = 110; go_ey[1] = 156; go_ep[2] = 14; go_ex[2] = 109; go_ey[2] = 154; go_ep[3] = 14; go_ex[3] = 108; go_ey[3] = 152; go_ep[4] = 14; go_ex[4] = 107; go_ey[4] = 151; go_ep[5] = 14; go_ex[5] = 106; go_ey[5] = 150; go_ep[6] = 14; go_ex[6] = 105; go_ey[6] = 149; go_ep[7] = 14; go_ex[7] = 104; go_ey[7] = 148;
go_ep[8] = 14; go_ex[8] = 103; go_ey[8] = 148; go_ep[9] = 14; go_ex[9] = 102; go_ey[9] = 147; go_ep[10] = 14; go_ex[10] = 101; go_ey[10] = 147; go_ep[11] = 14; go_ex[11] = 100; go_ey[11] = 147; go_ep[12] = 14; go_ex[12] = 99; go_ey[12] = 147; go_ep[13] = 14; go_ex[13] = 98; go_ey[13] = 148; go_ep[14] = 14; go_ex[14] = 97; go_ey[14] = 148; go_ep[15] = 14; go_ex[15] = 96; go_ey[15] = 149;
go_ep[16] = 14; go_ex[16] = 95; go_ey[16] = 150; go_ep[17] = 14; go_ex[17] = 94; go_ey[17] = 151; go_ep[18] = 14; go_ex[18] = 93; go_ey[18] = 152; go_ep[19] = 14; go_ex[19] = 92; go_ey[19] = 154; go_ep[20] = 14; go_ex[20] = 91; go_ey[20] = 156; go_ep[21] = 14; go_ex[21] = 90; go_ey[21] = 157; go_ep[22] = 14; go_ex[22] = 89; go_ey[22] = 160; go_ep[23] = 14; go_ex[23] = 88; go_ey[23] = 162;
go_ep[24] = 14; go_ex[24] = 87; go_ey[24] = 164; go_ep[25] = 14; go_ex[25] = 86; go_ey[25] = 167; go_ep[26] = 14; go_ex[26] = 85; go_ey[26] = 170; go_ep[27] = 14; go_ex[27] = 84; go_ey[27] = 173; go_ep[28] = 14; go_ex[28] = 83; go_ey[28] = 176; go_ep[29] = 14; go_ex[29] = 82; go_ey[29] = 179; go_ep[30] = 14; go_ex[30] = 81; go_ey[30] = 183; go_ep[31] = 14; go_ex[31] = 80; go_ey[31] = 187;
go_ep[32] = 14; go_ex[32] = 79; go_ey[32] = 190; go_ep[33] = 14; go_ex[33] = 78; go_ey[33] = 195; go_ep[34] = 14; go_ex[34] = 77; go_ey[34] = 199; go_ep[35] = 14; go_ex[35] = 76; go_ey[35] = 203; go_ep[36] = 14; go_ex[36] = 75; go_ey[36] = 208; go_ep[37] = 14; go_ex[37] = 74; go_ey[37] = 213; go_ep[38] = 14; go_ex[38] = 73; go_ey[38] = 218; go_ep[39] = 14; go_ex[39] = 72; go_ey[39] = 223;
go_ep[40] = 14; go_ex[40] = 71; go_ey[40] = 228; go_ep[41] = 14; go_ex[41] = 70; go_ey[41] = 233;

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
// the kitchen's crates and bonus boxes: column, row (0-29), kind (1 crate, 2 crate with a bonus box inside, 3 bonus box,
// 4 crate with the item inside), and the column / row of a block of the kitchen picture that looks like what is behind it
lv_box2_n = 55;
lv_bc2[0] = 101; lv_br2[0] = 1; lv_bk2[0] = 3; lv_bdc2[0] = 97; lv_bdr2[0] = 1;
lv_bc2[1] = 106; lv_br2[1] = 1; lv_bk2[1] = 3; lv_bdc2[1] = 96; lv_bdr2[1] = 1;
lv_bc2[2] = 109; lv_br2[2] = 1; lv_bk2[2] = 3; lv_bdc2[2] = 97; lv_bdr2[2] = 1;
lv_bc2[3] = 114; lv_br2[3] = 1; lv_bk2[3] = 3; lv_bdc2[3] = 96; lv_bdr2[3] = 1;
lv_bc2[4] = 117; lv_br2[4] = 1; lv_bk2[4] = 3; lv_bdc2[4] = 97; lv_bdr2[4] = 1;
lv_bc2[5] = 122; lv_br2[5] = 1; lv_bk2[5] = 3; lv_bdc2[5] = 96; lv_bdr2[5] = 1;
lv_bc2[6] = 100; lv_br2[6] = 2; lv_bk2[6] = 3; lv_bdc2[6] = 96; lv_bdr2[6] = 0;
lv_bc2[7] = 107; lv_br2[7] = 2; lv_bk2[7] = 3; lv_bdc2[7] = 97; lv_bdr2[7] = 0;
lv_bc2[8] = 108; lv_br2[8] = 2; lv_bk2[8] = 3; lv_bdc2[8] = 96; lv_bdr2[8] = 0;
lv_bc2[9] = 115; lv_br2[9] = 2; lv_bk2[9] = 3; lv_bdc2[9] = 97; lv_bdr2[9] = 0;
lv_bc2[10] = 116; lv_br2[10] = 2; lv_bk2[10] = 3; lv_bdc2[10] = 96; lv_bdr2[10] = 0;
lv_bc2[11] = 123; lv_br2[11] = 2; lv_bk2[11] = 3; lv_bdc2[11] = 97; lv_bdr2[11] = 0;
lv_bc2[12] = 91; lv_br2[12] = 3; lv_bk2[12] = 1; lv_bdc2[12] = 81; lv_bdr2[12] = 0;
lv_bc2[13] = 92; lv_br2[13] = 3; lv_bk2[13] = 2; lv_bdc2[13] = 81; lv_bdr2[13] = 0;
lv_bc2[14] = 93; lv_br2[14] = 3; lv_bk2[14] = 1; lv_bdc2[14] = 81; lv_bdr2[14] = 0;
lv_bc2[15] = 97; lv_br2[15] = 6; lv_bk2[15] = 3; lv_bdc2[15] = 99; lv_bdr2[15] = 0;
lv_bc2[16] = 97; lv_br2[16] = 7; lv_bk2[16] = 3; lv_bdc2[16] = 99; lv_bdr2[16] = 1;
lv_bc2[17] = 97; lv_br2[17] = 8; lv_bk2[17] = 3; lv_bdc2[17] = 97; lv_bdr2[17] = 0;
lv_bc2[18] = 97; lv_br2[18] = 9; lv_bk2[18] = 3; lv_bdc2[18] = 97; lv_bdr2[18] = 1;
lv_bc2[19] = 122; lv_br2[19] = 11; lv_bk2[19] = 1; lv_bdc2[19] = 96; lv_bdr2[19] = 11;
lv_bc2[20] = 123; lv_br2[20] = 11; lv_bk2[20] = 2; lv_bdc2[20] = 96; lv_bdr2[20] = 11;
lv_bc2[21] = 86; lv_br2[21] = 16; lv_bk2[21] = 1; lv_bdc2[21] = 81; lv_bdr2[21] = 0;
lv_bc2[22] = 87; lv_br2[22] = 16; lv_bk2[22] = 1; lv_bdc2[22] = 81; lv_bdr2[22] = 0;
lv_bc2[23] = 14; lv_br2[23] = 17; lv_bk2[23] = 3; lv_bdc2[23] = 96; lv_bdr2[23] = 1;
lv_bc2[24] = 15; lv_br2[24] = 17; lv_bk2[24] = 3; lv_bdc2[24] = 97; lv_bdr2[24] = 1;
lv_bc2[25] = 70; lv_br2[25] = 17; lv_bk2[25] = 3; lv_bdc2[25] = 96; lv_bdr2[25] = 1;
lv_bc2[26] = 72; lv_br2[26] = 17; lv_bk2[26] = 3; lv_bdc2[26] = 96; lv_bdr2[26] = 1;
lv_bc2[27] = 80; lv_br2[27] = 17; lv_bk2[27] = 3; lv_bdc2[27] = 80; lv_bdr2[27] = 0;
lv_bc2[28] = 81; lv_br2[28] = 17; lv_bk2[28] = 3; lv_bdc2[28] = 81; lv_bdr2[28] = 0;
lv_bc2[29] = 46; lv_br2[29] = 18; lv_bk2[29] = 1; lv_bdc2[29] = 81; lv_bdr2[29] = 0;
lv_bc2[30] = 47; lv_br2[30] = 18; lv_bk2[30] = 1; lv_bdc2[30] = 80; lv_bdr2[30] = 0;
lv_bc2[31] = 82; lv_br2[31] = 18; lv_bk2[31] = 3; lv_bdc2[31] = 81; lv_bdr2[31] = 0;
lv_bc2[32] = 8; lv_br2[32] = 19; lv_bk2[32] = 1; lv_bdc2[32] = 98; lv_bdr2[32] = 1;
lv_bc2[33] = 8; lv_br2[33] = 20; lv_bk2[33] = 1; lv_bdc2[33] = 96; lv_bdr2[33] = 0;
lv_bc2[34] = 23; lv_br2[34] = 22; lv_bk2[34] = 3; lv_bdc2[34] = 99; lv_bdr2[34] = 0;
lv_bc2[35] = 64; lv_br2[35] = 22; lv_bk2[35] = 3; lv_bdc2[35] = 96; lv_bdr2[35] = 0;
lv_bc2[36] = 65; lv_br2[36] = 22; lv_bk2[36] = 3; lv_bdc2[36] = 84; lv_bdr2[36] = 5;
lv_bc2[37] = 50; lv_br2[37] = 23; lv_bk2[37] = 3; lv_bdc2[37] = 96; lv_bdr2[37] = 1;
lv_bc2[38] = 23; lv_br2[38] = 24; lv_bk2[38] = 3; lv_bdc2[38] = 97; lv_bdr2[38] = 0;
lv_bc2[39] = 43; lv_br2[39] = 24; lv_bk2[39] = 1; lv_bdc2[39] = 81; lv_bdr2[39] = 0;
lv_bc2[40] = 44; lv_br2[40] = 24; lv_bk2[40] = 4; lv_bdc2[40] = 81; lv_bdr2[40] = 0;
lv_bc2[41] = 17; lv_br2[41] = 25; lv_bk2[41] = 1; lv_bdc2[41] = 99; lv_bdr2[41] = 1;
lv_bc2[42] = 50; lv_br2[42] = 25; lv_bk2[42] = 3; lv_bdc2[42] = 96; lv_bdr2[42] = 1;
lv_bc2[43] = 72; lv_br2[43] = 25; lv_bk2[43] = 1; lv_bdc2[43] = 96; lv_bdr2[43] = 1;
lv_bc2[44] = 10; lv_br2[44] = 26; lv_bk2[44] = 1; lv_bdc2[44] = 84; lv_bdr2[44] = 13;
lv_bc2[45] = 11; lv_br2[45] = 26; lv_bk2[45] = 1; lv_bdc2[45] = 4; lv_bdr2[45] = 26;
lv_bc2[46] = 17; lv_br2[46] = 26; lv_bk2[46] = 2; lv_bdc2[46] = 96; lv_bdr2[46] = 11;
lv_bc2[47] = 30; lv_br2[47] = 26; lv_bk2[47] = 1; lv_bdc2[47] = 96; lv_bdr2[47] = 11;
lv_bc2[48] = 31; lv_br2[48] = 26; lv_bk2[48] = 2; lv_bdc2[48] = 96; lv_bdr2[48] = 11;
lv_bc2[49] = 56; lv_br2[49] = 26; lv_bk2[49] = 1; lv_bdc2[49] = 82; lv_bdr2[49] = 13;
lv_bc2[50] = 57; lv_br2[50] = 26; lv_bk2[50] = 1; lv_bdc2[50] = 83; lv_bdr2[50] = 13;
lv_bc2[51] = 72; lv_br2[51] = 26; lv_bk2[51] = 2; lv_bdc2[51] = 96; lv_bdr2[51] = 11;
lv_bc2[52] = 89; lv_br2[52] = 26; lv_bk2[52] = 2; lv_bdc2[52] = 81; lv_bdr2[52] = 0;
lv_bc2[53] = 90; lv_br2[53] = 26; lv_bk2[53] = 4; lv_bdc2[53] = 81; lv_bdr2[53] = 0;
lv_bc2[54] = 91; lv_br2[54] = 26; lv_bk2[54] = 1; lv_bdc2[54] = 81; lv_bdr2[54] = 0;
lv_rbox2_c = 101; lv_rbox2_r = 1;    // a bonus box in the kitchen picture (shown where a crate had one inside)
// the third section's crates and bonus boxes: column, row (0-14), kind (1 crate, 2 crate with a bonus box inside,
// 3 bonus box), and the column / row of a block of the section's picture that looks like what is behind it
lv_box3_n = 33;
lv_bc3[0] = 7; lv_br3[0] = 1; lv_bk3[0] = 3; lv_bdc3[0] = 111; lv_bdr3[0] = 0;
lv_bc3[1] = 8; lv_br3[1] = 1; lv_bk3[1] = 3; lv_bdc3[1] = 110; lv_bdr3[1] = 0;
lv_bc3[2] = 55; lv_br3[2] = 2; lv_bk3[2] = 3; lv_bdc3[2] = 1; lv_bdr3[2] = 0;
lv_bc3[3] = 57; lv_br3[3] = 2; lv_bk3[3] = 3; lv_bdc3[3] = 1; lv_bdr3[3] = 0;
lv_bc3[4] = 70; lv_br3[4] = 2; lv_bk3[4] = 3; lv_bdc3[4] = 17; lv_bdr3[4] = 0;
lv_bc3[5] = 74; lv_br3[5] = 2; lv_bk3[5] = 3; lv_bdc3[5] = 17; lv_bdr3[5] = 0;
lv_bc3[6] = 110; lv_br3[6] = 2; lv_bk3[6] = 3; lv_bdc3[6] = 110; lv_bdr3[6] = 0;
lv_bc3[7] = 110; lv_br3[7] = 4; lv_bk3[7] = 3; lv_bdc3[7] = 110; lv_bdr3[7] = 0;
lv_bc3[8] = 38; lv_br3[8] = 5; lv_bk3[8] = 1; lv_bdc3[8] = 110; lv_bdr3[8] = 0;
lv_bc3[9] = 39; lv_br3[9] = 5; lv_bk3[9] = 1; lv_bdc3[9] = 111; lv_bdr3[9] = 0;
lv_bc3[10] = 46; lv_br3[10] = 6; lv_bk3[10] = 3; lv_bdc3[10] = 0; lv_bdr3[10] = 0;
lv_bc3[11] = 98; lv_br3[11] = 6; lv_bk3[11] = 3; lv_bdc3[11] = 17; lv_bdr3[11] = 0;
lv_bc3[12] = 110; lv_br3[12] = 6; lv_bk3[12] = 3; lv_bdc3[12] = 110; lv_bdr3[12] = 0;
lv_bc3[13] = 24; lv_br3[13] = 7; lv_bk3[13] = 3; lv_bdc3[13] = 22; lv_bdr3[13] = 7;
lv_bc3[14] = 28; lv_br3[14] = 7; lv_bk3[14] = 3; lv_bdc3[14] = 76; lv_bdr3[14] = 7;
lv_bc3[15] = 97; lv_br3[15] = 7; lv_bk3[15] = 3; lv_bdc3[15] = 97; lv_bdr3[15] = 5;
lv_bc3[16] = 98; lv_br3[16] = 7; lv_bk3[16] = 3; lv_bdc3[16] = 17; lv_bdr3[16] = 0;
lv_bc3[17] = 22; lv_br3[17] = 8; lv_bk3[17] = 3; lv_bdc3[17] = 103; lv_bdr3[17] = 4;
lv_bc3[18] = 26; lv_br3[18] = 8; lv_bk3[18] = 3; lv_bdc3[18] = 103; lv_bdr3[18] = 4;
lv_bc3[19] = 46; lv_br3[19] = 8; lv_bk3[19] = 3; lv_bdc3[19] = 0; lv_bdr3[19] = 0;
lv_bc3[20] = 72; lv_br3[20] = 8; lv_bk3[20] = 3; lv_bdc3[20] = 103; lv_bdr3[20] = 4;
lv_bc3[21] = 76; lv_br3[21] = 8; lv_bk3[21] = 3; lv_bdc3[21] = 103; lv_bdr3[21] = 4;
lv_bc3[22] = 46; lv_br3[22] = 10; lv_bk3[22] = 3; lv_bdc3[22] = 0; lv_bdr3[22] = 0;
lv_bc3[23] = 62; lv_br3[23] = 10; lv_bk3[23] = 1; lv_bdc3[23] = 0; lv_bdr3[23] = 0;
lv_bc3[24] = 14; lv_br3[24] = 11; lv_bk3[24] = 1; lv_bdc3[24] = 0; lv_bdr3[24] = 11;
lv_bc3[25] = 15; lv_br3[25] = 11; lv_bk3[25] = 1; lv_bdc3[25] = 0; lv_bdr3[25] = 11;
lv_bc3[26] = 41; lv_br3[26] = 11; lv_bk3[26] = 2; lv_bdc3[26] = 0; lv_bdr3[26] = 11;
lv_bc3[27] = 42; lv_br3[27] = 11; lv_bk3[27] = 1; lv_bdc3[27] = 0; lv_bdr3[27] = 11;
lv_bc3[28] = 55; lv_br3[28] = 11; lv_bk3[28] = 1; lv_bdc3[28] = 0; lv_bdr3[28] = 11;
lv_bc3[29] = 56; lv_br3[29] = 11; lv_bk3[29] = 1; lv_bdc3[29] = 0; lv_bdr3[29] = 11;
lv_bc3[30] = 62; lv_br3[30] = 11; lv_bk3[30] = 2; lv_bdc3[30] = 0; lv_bdr3[30] = 11;
lv_bc3[31] = 88; lv_br3[31] = 11; lv_bk3[31] = 1; lv_bdc3[31] = 43; lv_bdr3[31] = 3;
lv_bc3[32] = 89; lv_br3[32] = 11; lv_bk3[32] = 1; lv_bdc3[32] = 44; lv_bdr3[32] = 3;
lv_rbox3_c = 7; lv_rbox3_r = 1;    // a bonus box in the picture (shown where a crate had one inside)
// the kitchen's objects, in the order the camera reaches them: column, row (0-14 the upper floor, 15-29 the lower
// one), kind: 5 the star that gives a life, 9 the exit, 15 the mouse with the spoon, 16 the mouse under a crate,
// 17 a bottle cap (an obj_enemy of kind 7: scr_en_cap).
lv_ob2_n = 14;
lv_ob2_c[0] = 15; lv_ob2_r[0] = 24; lv_ob2_k[0] = 16;
lv_ob2_c[1] = 27; lv_ob2_r[1] = 27; lv_ob2_k[1] = 15;
lv_ob2_c[2] = 43; lv_ob2_r[2] = 25; lv_ob2_k[2] = 16;
lv_ob2_c[3] = 58; lv_ob2_r[3] = 21; lv_ob2_k[3] = 15;
lv_ob2_c[4] = 78; lv_ob2_r[4] = 27; lv_ob2_k[4] = 15;
lv_ob2_c[5] = 89; lv_ob2_r[5] = 27; lv_ob2_k[5] = 16;
lv_ob2_c[6] = 94; lv_ob2_r[6] = 23; lv_ob2_k[6] = 15;
lv_ob2_c[7] = 99; lv_ob2_r[7] = 6; lv_ob2_k[7] = 17;
lv_ob2_c[8] = 104; lv_ob2_r[8] = 12; lv_ob2_k[8] = 15;
lv_ob2_c[9] = 107; lv_ob2_r[9] = 6; lv_ob2_k[9] = 17;
lv_ob2_c[10] = 115; lv_ob2_r[10] = 6; lv_ob2_k[10] = 17;
lv_ob2_c[11] = 122; lv_ob2_r[11] = 12; lv_ob2_k[11] = 16;
lv_ob2_c[12] = 125; lv_ob2_r[12] = 4; lv_ob2_k[12] = 5;
lv_ob2_c[13] = 126; lv_ob2_r[13] = 12; lv_ob2_k[13] = 9;
// ... and those that enter from above while the camera climbs the shaft: when the row 8 pixels below the top of
// the picture becomes theirs (they appear one row higher than the list says)
lv_ob2v_n = 1;
lv_ob2v_c[0] = 91; lv_ob2v_r[0] = 5; lv_ob2v_k[0] = 16;
lv_dy = 0;             // how far the kitchen camera went up on this frame
// the walking pictures of the mouse under its crate (8 steps each)
en_cwalk[0] = 19; en_cwalk[1] = 20; en_cwalk[2] = 21; en_cwalk[3] = 20;
en_cap_h[0] = 7; en_cap_h[1] = 4; en_cap_h[2] = 2; en_cap_h[3] = 15;     // a bottle cap's height: on the bottle, pressed once, pressed twice, flying
// the pictures of the mice (same layout as the tables of step 09; the tile numbers go on from there)
en_tn[0] = 14;
en_tdx[0,0] = -13; en_tdy[0,0] = -33; en_tim[0,0] = 60; en_tdx[0,1] = -13; en_tdy[0,1] = -25; en_tim[0,1] = 61; en_tdx[0,2] = -10; en_tdy[0,2] = -26; en_tim[0,2] = 62; en_tdx[0,3] = -5; en_tdy[0,3] = -25; en_tim[0,3] = 63; en_tdx[0,4] = 0; en_tdy[0,4] = -25; en_tim[0,4] = 64; en_tdx[0,5] = 7; en_tdy[0,5] = -24; en_tim[0,5] = 65; en_tdx[0,6] = -16; en_tdy[0,6] = -17; en_tim[0,6] = 66; en_tdx[0,7] = -15; en_tdy[0,7] = -17; en_tim[0,7] = 67; en_tdx[0,8] = -7; en_tdy[0,8] = -17; en_tim[0,8] = 68; en_tdx[0,9] = 1; en_tdy[0,9] = -17; en_tim[0,9] = 69; en_tdx[0,10] = -8; en_tdy[0,10] = -9; en_tim[0,10] = 70; en_tdx[0,11] = 0; en_tdy[0,11] = -9; en_tim[0,11] = 71; en_tdx[0,12] = 8; en_tdy[0,12] = -9; en_tim[0,12] = 72; en_tdx[0,13] = -3; en_tdy[0,13] = -17; en_tim[0,13] = 73;
en_tn[1] = 14;
en_tdx[1,0] = -13; en_tdy[1,0] = -34; en_tim[1,0] = 60; en_tdx[1,1] = -13; en_tdy[1,1] = -26; en_tim[1,1] = 61; en_tdx[1,2] = -10; en_tdy[1,2] = -27; en_tim[1,2] = 62; en_tdx[1,3] = -5; en_tdy[1,3] = -26; en_tim[1,3] = 63; en_tdx[1,4] = 0; en_tdy[1,4] = -26; en_tim[1,4] = 64; en_tdx[1,5] = 7; en_tdy[1,5] = -25; en_tim[1,5] = 65; en_tdx[1,6] = -16; en_tdy[1,6] = -18; en_tim[1,6] = 66; en_tdx[1,7] = -15; en_tdy[1,7] = -18; en_tim[1,7] = 67; en_tdx[1,8] = -7; en_tdy[1,8] = -18; en_tim[1,8] = 68; en_tdx[1,9] = 1; en_tdy[1,9] = -18; en_tim[1,9] = 69; en_tdx[1,10] = -3; en_tdy[1,10] = -18; en_tim[1,10] = 73; en_tdx[1,11] = 0; en_tdy[1,11] = -10; en_tim[1,11] = 74; en_tdx[1,12] = 8; en_tdy[1,12] = -10; en_tim[1,12] = 75; en_tdx[1,13] = 1; en_tdy[1,13] = -2; en_tim[1,13] = 76;
en_tn[2] = 14;
en_tdx[2,0] = -13; en_tdy[2,0] = -33; en_tim[2,0] = 60; en_tdx[2,1] = -13; en_tdy[2,1] = -25; en_tim[2,1] = 61; en_tdx[2,2] = -10; en_tdy[2,2] = -26; en_tim[2,2] = 62; en_tdx[2,3] = -5; en_tdy[2,3] = -25; en_tim[2,3] = 63; en_tdx[2,4] = 0; en_tdy[2,4] = -25; en_tim[2,4] = 64; en_tdx[2,5] = 7; en_tdy[2,5] = -24; en_tim[2,5] = 65; en_tdx[2,6] = -16; en_tdy[2,6] = -17; en_tim[2,6] = 66; en_tdx[2,7] = -15; en_tdy[2,7] = -17; en_tim[2,7] = 67; en_tdx[2,8] = -7; en_tdy[2,8] = -17; en_tim[2,8] = 68; en_tdx[2,9] = 1; en_tdy[2,9] = -17; en_tim[2,9] = 69; en_tdx[2,10] = -8; en_tdy[2,10] = -9; en_tim[2,10] = 77; en_tdx[2,11] = 0; en_tdy[2,11] = -9; en_tim[2,11] = 78; en_tdx[2,12] = 8; en_tdy[2,12] = -9; en_tim[2,12] = 79; en_tdx[2,13] = -3; en_tdy[2,13] = -17; en_tim[2,13] = 73;
en_tn[3] = 15;
en_tdx[3,0] = -8; en_tdy[3,0] = -34; en_tim[3,0] = 80; en_tdx[3,1] = 0; en_tdy[3,1] = -34; en_tim[3,1] = 81; en_tdx[3,2] = -8; en_tdy[3,2] = -9; en_tim[3,2] = 82; en_tdx[3,3] = 0; en_tdy[3,3] = -9; en_tim[3,3] = 83; en_tdx[3,4] = 8; en_tdy[3,4] = -9; en_tim[3,4] = 84; en_tdx[3,5] = 1; en_tdy[3,5] = -33; en_tim[3,5] = 60; en_tdx[3,6] = 1; en_tdy[3,6] = -25; en_tim[3,6] = 61; en_tdx[3,7] = 0; en_tdy[3,7] = -17; en_tim[3,7] = 85; en_tdx[3,8] = 8; en_tdy[3,8] = -17; en_tim[3,8] = 86; en_tdx[3,9] = 8; en_tdy[3,9] = -33; en_tim[3,9] = 87; en_tdx[3,10] = 16; en_tdy[3,10] = -29; en_tim[3,10] = 88; en_tdx[3,11] = 16; en_tdy[3,11] = -21; en_tim[3,11] = 89; en_tdx[3,12] = 4; en_tdy[3,12] = -26; en_tim[3,12] = 62; en_tdx[3,13] = 9; en_tdy[3,13] = -25; en_tim[3,13] = 63; en_tdx[3,14] = 7; en_tdy[3,14] = -15; en_tim[3,14] = 90;
en_tn[4] = 22;
en_tdx[4,0] = -16; en_tdy[4,0] = -33; en_tim[4,0] = 91; en_tdx[4,1] = -13; en_tdy[4,1] = -33; en_tim[4,1] = 60; en_tdx[4,2] = -13; en_tdy[4,2] = -25; en_tim[4,2] = 61; en_tdx[4,3] = -8; en_tdy[4,3] = -33; en_tim[4,3] = 92; en_tdx[4,4] = 7; en_tdy[4,4] = -33; en_tim[4,4] = 93; en_tdx[4,5] = 0; en_tdy[4,5] = -32; en_tim[4,5] = 94; en_tdx[4,6] = -24; en_tdy[4,6] = -31; en_tim[4,6] = 95; en_tdx[4,7] = -24; en_tdy[4,7] = -23; en_tim[4,7] = 96; en_tdx[4,8] = -24; en_tdy[4,8] = -15; en_tim[4,8] = 97; en_tdx[4,9] = -10; en_tdy[4,9] = -26; en_tim[4,9] = 62; en_tdx[4,10] = -5; en_tdy[4,10] = -25; en_tim[4,10] = 63; en_tdx[4,11] = -16; en_tdy[4,11] = -17; en_tim[4,11] = 98; en_tdx[4,12] = -16; en_tdy[4,12] = -9; en_tim[4,12] = 99; en_tdx[4,13] = -15; en_tdy[4,13] = -17; en_tim[4,13] = 100; en_tdx[4,14] = -7; en_tdy[4,14] = -17; en_tim[4,14] = 68; en_tdx[4,15] = 1; en_tdy[4,15] = -17; en_tim[4,15] = 69; en_tdx[4,16] = -9; en_tdy[4,16] = -13; en_tim[4,16] = 101; en_tdx[4,17] = -1; en_tdy[4,17] = -13; en_tim[4,17] = 102; en_tdx[4,18] = -8; en_tdy[4,18] = -9; en_tim[4,18] = 70; en_tdx[4,19] = 0; en_tdy[4,19] = -9; en_tim[4,19] = 71; en_tdx[4,20] = 8; en_tdy[4,20] = -9; en_tim[4,20] = 72; en_tdx[4,21] = -3; en_tdy[4,21] = -17; en_tim[4,21] = 73;
en_tn[5] = 14;
en_tdx[5,0] = -13; en_tdy[5,0] = -33; en_tim[5,0] = 60; en_tdx[5,1] = -13; en_tdy[5,1] = -25; en_tim[5,1] = 61; en_tdx[5,2] = 7; en_tdy[5,2] = -33; en_tim[5,2] = 93; en_tdx[5,3] = 0; en_tdy[5,3] = -32; en_tim[5,3] = 94; en_tdx[5,4] = -10; en_tdy[5,4] = -26; en_tim[5,4] = 62; en_tdx[5,5] = -5; en_tdy[5,5] = -25; en_tim[5,5] = 63; en_tdx[5,6] = -16; en_tdy[5,6] = -17; en_tim[5,6] = 98; en_tdx[5,7] = -15; en_tdy[5,7] = -17; en_tim[5,7] = 100; en_tdx[5,8] = -7; en_tdy[5,8] = -17; en_tim[5,8] = 68; en_tdx[5,9] = 1; en_tdy[5,9] = -17; en_tim[5,9] = 69; en_tdx[5,10] = -8; en_tdy[5,10] = -9; en_tim[5,10] = 70; en_tdx[5,11] = 0; en_tdy[5,11] = -9; en_tim[5,11] = 71; en_tdx[5,12] = 8; en_tdy[5,12] = -9; en_tim[5,12] = 72; en_tdx[5,13] = -3; en_tdy[5,13] = -17; en_tim[5,13] = 73;
en_tn[6] = 14;
en_tdx[6,0] = -13; en_tdy[6,0] = -33; en_tim[6,0] = 60; en_tdx[6,1] = -13; en_tdy[6,1] = -25; en_tim[6,1] = 61; en_tdx[6,2] = -10; en_tdy[6,2] = -26; en_tim[6,2] = 62; en_tdx[6,3] = -5; en_tdy[6,3] = -25; en_tim[6,3] = 103; en_tdx[6,4] = 0; en_tdy[6,4] = -25; en_tim[6,4] = 64; en_tdx[6,5] = 7; en_tdy[6,5] = -24; en_tim[6,5] = 65; en_tdx[6,6] = -16; en_tdy[6,6] = -17; en_tim[6,6] = 66; en_tdx[6,7] = -15; en_tdy[6,7] = -17; en_tim[6,7] = 67; en_tdx[6,8] = -7; en_tdy[6,8] = -17; en_tim[6,8] = 104; en_tdx[6,9] = 1; en_tdy[6,9] = -17; en_tim[6,9] = 69; en_tdx[6,10] = -8; en_tdy[6,10] = -9; en_tim[6,10] = 70; en_tdx[6,11] = 0; en_tdy[6,11] = -9; en_tim[6,11] = 71; en_tdx[6,12] = 8; en_tdy[6,12] = -9; en_tim[6,12] = 72; en_tdx[6,13] = -3; en_tdy[6,13] = -17; en_tim[6,13] = 73;
en_tn[15] = 6;
en_tdx[15,0] = -8; en_tdy[15,0] = -19; en_tim[15,0] = 105; en_tdx[15,1] = 0; en_tdy[15,1] = -19; en_tim[15,1] = 106; en_tdx[15,2] = -8; en_tdy[15,2] = -17; en_tim[15,2] = 107; en_tdx[15,3] = -8; en_tdy[15,3] = -9; en_tim[15,3] = 108; en_tdx[15,4] = 0; en_tdy[15,4] = -17; en_tim[15,4] = 109; en_tdx[15,5] = 0; en_tdy[15,5] = -9; en_tim[15,5] = 110;
en_tn[16] = 6;
en_tdx[16,0] = -8; en_tdy[16,0] = -21; en_tim[16,0] = 105; en_tdx[16,1] = 0; en_tdy[16,1] = -21; en_tim[16,1] = 106; en_tdx[16,2] = -8; en_tdy[16,2] = -17; en_tim[16,2] = 107; en_tdx[16,3] = -8; en_tdy[16,3] = -9; en_tim[16,3] = 108; en_tdx[16,4] = 0; en_tdy[16,4] = -17; en_tim[16,4] = 109; en_tdx[16,5] = 0; en_tdy[16,5] = -9; en_tim[16,5] = 110;
en_tn[17] = 6;
en_tdx[17,0] = -8; en_tdy[17,0] = -23; en_tim[17,0] = 105; en_tdx[17,1] = 0; en_tdy[17,1] = -23; en_tim[17,1] = 106; en_tdx[17,2] = -8; en_tdy[17,2] = -17; en_tim[17,2] = 107; en_tdx[17,3] = -8; en_tdy[17,3] = -9; en_tim[17,3] = 108; en_tdx[17,4] = 0; en_tdy[17,4] = -17; en_tim[17,4] = 109; en_tdx[17,5] = 0; en_tdy[17,5] = -9; en_tim[17,5] = 110;
en_tn[18] = 7;
en_tdx[18,0] = -8; en_tdy[18,0] = -25; en_tim[18,0] = 105; en_tdx[18,1] = -8; en_tdy[18,1] = -17; en_tim[18,1] = 107; en_tdx[18,2] = -8; en_tdy[18,2] = -9; en_tim[18,2] = 108; en_tdx[18,3] = -5; en_tdy[18,3] = -25; en_tim[18,3] = 111; en_tdx[18,4] = 0; en_tdy[18,4] = -25; en_tim[18,4] = 106; en_tdx[18,5] = 0; en_tdy[18,5] = -17; en_tim[18,5] = 109; en_tdx[18,6] = 0; en_tdy[18,6] = -9; en_tim[18,6] = 110;
en_tn[19] = 7;
en_tdx[19,0] = -13; en_tdy[19,0] = -9; en_tim[19,0] = 70; en_tdx[19,1] = -5; en_tdy[19,1] = -9; en_tim[19,1] = 71; en_tdx[19,2] = 3; en_tdy[19,2] = -9; en_tim[19,2] = 72; en_tdx[19,3] = -8; en_tdy[19,3] = -25; en_tim[19,3] = 107; en_tdx[19,4] = -8; en_tdy[19,4] = -17; en_tim[19,4] = 108; en_tdx[19,5] = 0; en_tdy[19,5] = -25; en_tim[19,5] = 109; en_tdx[19,6] = 0; en_tdy[19,6] = -17; en_tim[19,6] = 110;
en_tn[20] = 7;
en_tdx[20,0] = -8; en_tdy[20,0] = -26; en_tim[20,0] = 107; en_tdx[20,1] = -8; en_tdy[20,1] = -18; en_tim[20,1] = 108; en_tdx[20,2] = 0; en_tdy[20,2] = -26; en_tim[20,2] = 109; en_tdx[20,3] = 0; en_tdy[20,3] = -18; en_tim[20,3] = 110; en_tdx[20,4] = -5; en_tdy[20,4] = -10; en_tim[20,4] = 74; en_tdx[20,5] = 3; en_tdy[20,5] = -10; en_tim[20,5] = 75; en_tdx[20,6] = -4; en_tdy[20,6] = -2; en_tim[20,6] = 76;
en_tn[21] = 7;
en_tdx[21,0] = -13; en_tdy[21,0] = -9; en_tim[21,0] = 77; en_tdx[21,1] = -5; en_tdy[21,1] = -9; en_tim[21,1] = 78; en_tdx[21,2] = 3; en_tdy[21,2] = -9; en_tim[21,2] = 79; en_tdx[21,3] = -8; en_tdy[21,3] = -25; en_tim[21,3] = 107; en_tdx[21,4] = -8; en_tdy[21,4] = -17; en_tim[21,4] = 108; en_tdx[21,5] = 0; en_tdy[21,5] = -25; en_tim[21,5] = 109; en_tdx[21,6] = 0; en_tdy[21,6] = -17; en_tim[21,6] = 110;
en_tn[76] = 4;
en_tdx[76,0] = -8; en_tdy[76,0] = -17; en_tim[76,0] = 107; en_tdx[76,1] = -8; en_tdy[76,1] = -9; en_tim[76,1] = 108; en_tdx[76,2] = 0; en_tdy[76,2] = -17; en_tim[76,2] = 109; en_tdx[76,3] = 0; en_tdy[76,3] = -9; en_tim[76,3] = 110;
// the pictures of the bottle cap: 80 on the bottle, 81 pressed once, 82 pressed twice, 83 flying
// (same layout as the tables of step 09; the tile numbers go on from those of step 13)
en_tn[80] = 2;
en_tdx[80,0] = -8; en_tdy[80,0] = -8; en_tim[80,0] = 112; en_tdx[80,1] = 0; en_tdy[80,1] = -8; en_tim[80,1] = 113;
en_tn[81] = 2;
en_tdx[81,0] = -8; en_tdy[81,0] = -8; en_tim[81,0] = 114; en_tdx[81,1] = 0; en_tdy[81,1] = -8; en_tim[81,1] = 115;
en_tn[82] = 2;
en_tdx[82,0] = -8; en_tdy[82,0] = -8; en_tim[82,0] = 116; en_tdx[82,1] = 0; en_tdy[82,1] = -8; en_tim[82,1] = 117;
en_tn[83] = 4;
en_tdx[83,0] = -8; en_tdy[83,0] = -16; en_tim[83,0] = 112; en_tdx[83,1] = -8; en_tdy[83,1] = -8; en_tim[83,1] = 118; en_tdx[83,2] = 0; en_tdy[83,2] = -16; en_tim[83,2] = 113; en_tdx[83,3] = 0; en_tdy[83,3] = -8; en_tim[83,3] = 119;
lv_it_n = 0;           // the obj_item instances: lv_it[0 .. lv_it_n - 1]
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

// The same for the kitchen, 128 columns x 30 rows (rows 0-14: the upper floor, rows 15-29: the lower floor).
// Its crates and its present are solid blocks for now, its bonus boxes nothing (a later step).
lv_map2[0] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map2[1] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map2[2] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000011111000000000000000000000000000000000000011";
lv_map2[3] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002220000000000000000000000000000000000";
lv_map2[4] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000111111111111111100000000000000000000000000111111";
lv_map2[5] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map2[6] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000100000001000000000000";
lv_map2[7] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map2[8] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000111111000000000000000000000000000000000000000000";
lv_map2[9] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map2[10] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000111111000000000000000000000000000000000000000000";
lv_map2[11] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000220000";
lv_map2[12] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000001110000000000022222222222222222222222222222222";
lv_map2[13] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020022002200220022002200220022002";
lv_map2[14] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000111111000000000020022002200220022002200220022002";
lv_map2[15] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map2[16] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000220000000000000000000000000000000000000000";
lv_map2[17] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000111111111100000000000000000000000000000000";
lv_map2[18] = "00000000000000000000000000000000000000000000002200000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map2[19] = "00111110201111001110000000111000001110000000111100111110001111001110000000111000000000000000000000000000000000000000000000000000";
lv_map2[20] = "00000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map2[21] = "11111111111100001111110011111100111111001111110011111111111100001111110011111100000000000000111100000000000000000000000000000000";
lv_map2[22] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map2[23] = "00001111100000000000000000111110001111100000000000001111100000000000000000111110000000000011111100000000000000000000000000000000";
lv_map2[24] = "00000000000011110011110000000000000000000002200000000000000011110011110000000000000000000000000000000000000000000000000000000000";
lv_map2[25] = "00000000111111110200000000000000000000000011111000000000111111110000000020000000001111100000111100000000000000000000000000000000";
lv_map2[26] = "00000000002200000200000000000022000000000000000000000000220000000000000020000000000000000222000000000000000000000000000000000000";
lv_map2[27] = "22222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222200000000000000000000000000000000";
lv_map2[28] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map2[29] = "22222222000000002222222200000000000000000000000022222222000000002222222200000000222222220000000000000000000000000000000000000000";

// The third section (the stove and the sink), 112 columns x 15 rows, filled up to 128 columns with nothing.
// Its crates are solid blocks for now, its bonus boxes nothing (a later step).
lv_map3[0] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map3[1] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_map3[2] = "11100000000000000000000000000000000000000011100000000000000000000000000000000000000000000011100001111000000000000000000000000000";
lv_map3[3] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020000000002000000000000000000";
lv_map3[4] = "11111100000011101100111111111100111110001111110011100000001110001100111111111100111110001111100111120000000002000000000000000000";
lv_map3[5] = "00000000000000000000000000000000000000220000000000000000000000000000000000000000000000000000000000020000000002000000000000000000";
lv_map3[6] = "00000000001111110000000000000000111111111100000011111100111111000000000000000000111111111100000000020000000002000000000000000000";
lv_map3[7] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020000000002000000000000000000";
lv_map3[8] = "00001111101111101100000000000000000000000000000000000000001111101100000000000000000000000000000011120000000002000000000000000000";
lv_map3[9] = "00000000000000000000000000000000000000000000000000111100000000000000000000000000000000000000000000020000000002000000000000000000";
lv_map3[10] = "00000000000000000000000000000000001111110000000000000000000000200000000000000000000011111100000000020000000002220000000000000000";
lv_map3[11] = "00000000000000220000000000000000000000000220000000000002200000200000000000000000000000002200000000020000000002000000000000000000";
lv_map3[12] = "22222222222222222200222222222200222222222222222222222222222222222200222222222200222222222200000000020000000002000000000000000000";
lv_map3[13] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000022222222222000000000000000000";
lv_map3[14] = "22222222000000000000000000000000000000000000000022222222000000000000000000000000000000000000000000022222222222000000000000000000";

// The blocks in which the player is behind the picture (block $9F of the original: the inside of the sink and
// the dark gap right of it, which is the exit). 1 = a block in which the player is behind the picture (block $9F: the inside of the sink, the gap of the exit)
lv_back3[0] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_back3[1] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_back3[2] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_back3[3] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_back3[4] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_back3[5] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_back3[6] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000111111110000000000000000000";
lv_back3[7] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001111111110000000000000000000";
lv_back3[8] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001111111110010000000000000000";
lv_back3[9] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001111111110010000000000000000";
lv_back3[10] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001111111110000000000000000000";
lv_back3[11] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001111111110000000000000000000";
lv_back3[12] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001111111110000000000000000000";
lv_back3[13] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
lv_back3[14] = "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";

// lv_kind, lv_box, the list of opened boxes and the object list: built now, and again whenever the section restarts
event_user(0);

// ---- the player ---------------------------------------------------------------------
pl = instance_create(0, 0, obj_player);
pl.stage = id;

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
lv_star      = 0;      // the place in the object list of the star over a stunned player (0 = no star)

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

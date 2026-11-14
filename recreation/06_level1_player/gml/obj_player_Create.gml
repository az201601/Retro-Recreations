/// obj_player : Create
// Chip in level 1. This object has NO Step event: obj_stage1 runs User Defined 0 once per frame (so the order
// of everything in the level is fixed), and the object draws itself in its Draw event.
// obj_stage1 creates it and sets the variable "stage" (the id of the stage) right after creating it.
// The Create event is run again when the section restarts after a fall.

depth = -10;           // in front of the stage's background

// ---- position and movement ------------------------------------------------------
p_x     = 24;          // screen x of the middle of the feet (the body is 6 pixels wide to either side)
p_y     = 192;         // screen y of the feet
p_ysub  = 0;           // sixteenths of a pixel of p_y
p_xv    = 0;           // pixels per frame: -2, 0 or 2
p_yv    = 0;           // sixteenths of a pixel per frame, negative = up
p_face  = 1;           // 1 = facing right, 0 = facing left
p_h     = 22;          // height of the body: 22, crouching 16
p_state = 5;           // 5 on the ground, 3 crouching, 8 jumping (rising), 1 falling, 2 just landed,
                       // 20 walking out of the section by itself, 23 fell out of the picture
p_cnt   = 0;           // counter: walk animation / frames since landing / frames left after a fall
p_pose  = 2;           // 0 standing, 1 walking, 2 in the air, 3 landed, 4 crouching
p_walk  = 0;           // walking: step 0..3 of the walk cycle
p_blink = 0;           // standing: counts down; the eyes are closed for 16 of every 256 frames
p_pic   = 5;           // picture: 0 standing, 1-3 walking, 4 crouching / landed, 5 in the air, 6 eyes closed
p_auto  = false;       // true: the exit took over, the buttons are ignored

// ---- set by obj_stage1 before User Defined 0 --------------------------------------
p_pad     = 0;         // buttons held    (4 = A, 16 = DOWN, 64 = LEFT, 128 = RIGHT)
p_pressed = 0;         // buttons that went down on this frame

// ---- read by obj_stage1 after User Defined 0 --------------------------------------
p_landed  = false;     // landed on this frame (landing sound)
p_out     = false;     // walked off the right edge: the section is finished
p_restart = false;     // the wait after a fall is over: the section starts again

// ---- what the Draw event shows: the state after the PREVIOUS frame (set by obj_stage1) ----
s_x = p_x;  s_y = p_y;  s_pic = 0;  s_face = 1;  s_vis = true;

// sprite tables: tile i of picture f is drawn at (x + p_tdx, y + p_tdy + 1) facing right, (x - p_tdx - 8, ...) facing left
p_tn[0] = 7;
p_tdx[0,0] = -8; p_tdy[0,0] = -9; p_tim[0,0] = 0; p_tdx[0,1] = -7; p_tdy[0,1] = -25; p_tim[0,1] = 1; p_tdx[0,2] = -7; p_tdy[0,2] = -17; p_tim[0,2] = 2; p_tdx[0,3] = 0; p_tdy[0,3] = -17; p_tim[0,3] = 3; p_tdx[0,4] = 0; p_tdy[0,4] = -9; p_tim[0,4] = 4; p_tdx[0,5] = 1; p_tdy[0,5] = -25; p_tim[0,5] = 5; p_tdx[0,6] = 1; p_tdy[0,6] = -17; p_tim[0,6] = 6;
p_tn[1] = 7;
p_tdx[1,0] = -8; p_tdy[1,0] = -9; p_tim[1,0] = 7; p_tdx[1,1] = -4; p_tdy[1,1] = -25; p_tim[1,1] = 1; p_tdx[1,2] = -3; p_tdy[1,2] = -17; p_tim[1,2] = 8; p_tdx[1,3] = 0; p_tdy[1,3] = -9; p_tim[1,3] = 9; p_tdx[1,4] = 3; p_tdy[1,4] = -17; p_tim[1,4] = 3; p_tdx[1,5] = 4; p_tdy[1,5] = -25; p_tim[1,5] = 5; p_tdx[1,6] = 5; p_tdy[1,6] = -17; p_tim[1,6] = 10;
p_tn[2] = 8;
p_tdx[2,0] = -8; p_tdy[2,0] = -10; p_tim[2,0] = 11; p_tdx[2,1] = -7; p_tdy[2,1] = -2; p_tim[2,1] = 12; p_tdx[2,2] = -4; p_tdy[2,2] = -26; p_tim[2,2] = 1; p_tdx[2,3] = -3; p_tdy[2,3] = -18; p_tim[2,3] = 13; p_tdx[2,4] = 0; p_tdy[2,4] = -10; p_tim[2,4] = 14; p_tdx[2,5] = 3; p_tdy[2,5] = -18; p_tim[2,5] = 3; p_tdx[2,6] = 4; p_tdy[2,6] = -26; p_tim[2,6] = 5; p_tdx[2,7] = 5; p_tdy[2,7] = -18; p_tim[2,7] = 10;
p_tn[3] = 8;
p_tdx[3,0] = -8; p_tdy[3,0] = -17; p_tim[3,0] = 15; p_tdx[3,1] = -6; p_tdy[3,1] = -9; p_tim[3,1] = 16; p_tdx[3,2] = -4; p_tdy[3,2] = -25; p_tim[3,2] = 1; p_tdx[3,3] = 0; p_tdy[3,3] = -17; p_tim[3,3] = 17; p_tdx[3,4] = 2; p_tdy[3,4] = -9; p_tim[3,4] = 18; p_tdx[3,5] = 3; p_tdy[3,5] = -17; p_tim[3,5] = 3; p_tdx[3,6] = 4; p_tdy[3,6] = -25; p_tim[3,6] = 5; p_tdx[3,7] = 5; p_tdy[3,7] = -17; p_tim[3,7] = 10;
p_tn[4] = 7;
p_tdx[4,0] = -8; p_tdy[4,0] = -9; p_tim[4,0] = 19; p_tdx[4,1] = -1; p_tdy[4,1] = -19; p_tim[4,1] = 1; p_tdx[4,2] = 0; p_tdy[4,2] = -17; p_tim[4,2] = 20; p_tdx[4,3] = 0; p_tdy[4,3] = -9; p_tim[4,3] = 21; p_tdx[4,4] = 6; p_tdy[4,4] = -11; p_tim[4,4] = 3; p_tdx[4,5] = 7; p_tdy[4,5] = -19; p_tim[4,5] = 5; p_tdx[4,6] = 8; p_tdy[4,6] = -11; p_tim[4,6] = 10;
p_tn[5] = 9;
p_tdx[5,0] = -8; p_tdy[5,0] = -26; p_tim[5,0] = 22; p_tdx[5,1] = -7; p_tdy[5,1] = -18; p_tim[5,1] = 23; p_tdx[5,2] = -7; p_tdy[5,2] = -10; p_tim[5,2] = 24; p_tdx[5,3] = -4; p_tdy[5,3] = -26; p_tim[5,3] = 1; p_tdx[5,4] = 1; p_tdy[5,4] = -18; p_tim[5,4] = 25; p_tdx[5,5] = 1; p_tdy[5,5] = -10; p_tim[5,5] = 26; p_tdx[5,6] = 3; p_tdy[5,6] = -18; p_tim[5,6] = 27; p_tdx[5,7] = 4; p_tdy[5,7] = -26; p_tim[5,7] = 5; p_tdx[5,8] = 9; p_tdy[5,8] = -18; p_tim[5,8] = 28;
p_tn[6] = 7;
p_tdx[6,0] = -8; p_tdy[6,0] = -9; p_tim[6,0] = 0; p_tdx[6,1] = -7; p_tdy[6,1] = -25; p_tim[6,1] = 1; p_tdx[6,2] = -7; p_tdy[6,2] = -17; p_tim[6,2] = 2; p_tdx[6,3] = 0; p_tdy[6,3] = -17; p_tim[6,3] = 29; p_tdx[6,4] = 0; p_tdy[6,4] = -9; p_tim[6,4] = 4; p_tdx[6,5] = 1; p_tdy[6,5] = -25; p_tim[6,5] = 5; p_tdx[6,6] = 1; p_tdy[6,6] = -17; p_tim[6,6] = 30;

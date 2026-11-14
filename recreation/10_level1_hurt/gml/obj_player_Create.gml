/// obj_player : Create
// The player (Chip or Dale) in level 1. This object has NO Step event: obj_stage1 runs User Defined 0 once per frame (so the order
// of everything in the level is fixed) and User Defined 1 from its Draw event.
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
p_h     = 22;          // height of the body: 22, crouching 16; crouching under a carried crate: down to 0
p_state = 5;           // 5 on the ground, 3 crouching, 8 jumping (rising), 1 falling, 2 just landed,
                       // 20 walking out of the section by itself, 23 fell out of the picture,
                       // 9 / 10 hurt (9 for one frame), 14 / 15 stunned (14 for one frame)
p_cnt   = 0;           // counter: walk animation / frames since landing / frames left after a fall
p_pose  = 2;           // 0 standing, 1 walking, 2 in the air, 3 landed, 4 crouching, 5 hurt, 6 stunned
p_walk  = 0;           // walking: step 0..3 of the walk cycle
p_blink = 0;           // standing: counts down; the eyes are closed for 16 of every 256 frames
p_pic   = 5;           // picture: 0 standing, 1-3 walking, 4 crouching / landed, 5 in the air, 6 eyes closed,
                       // with a crate: 7 standing, 8-10 walking, 11 in the air; 12-13 throwing; 14 hurt, 15 stunned
p_auto  = false;       // true: the exit took over, the buttons are ignored

// ---- hearts ----------------------------------------------------------------------------
p_hp    = 3;           // hearts left
p_inv   = 0;           // frames left in which nothing can hurt (64 after being hurt)
p_flash = false;       // the picture flickers (2 frames shown, 2 not) during those frames
p_ghost = false;       // enemies are not touched: during those frames, after the last heart, while leaving the section
p_push  = 0;           // thrown aside, sixteenths of a pixel per frame: 32 hurt, 8 stunned (negative = to the left)
p_xsub  = 0;           // sixteenths of a pixel of p_x (only used while thrown aside)
p_stun  = false;       // stunned (cannot be stunned again meanwhile)

// ---- crates ----------------------------------------------------------------------------
p_carry = noone;       // the obj_crate on the head (noone = none)
p_throw = 0;           // throwing: counts 1..15 from the frame of the throw, 0 = not throwing
p_run   = 0;           // frames walked without a stop while carrying; from 30 on the throw is a far throw
p_moved = 0;           // pixels moved left / right on the previous frame
p_hide  = false;       // crouching under the carried crate: the player is not drawn
p_wc    = 0;           // set by scr_pl_wall: column and row of the solid block that stopped the player
p_wr    = 0;
p_snd   = 0;           // read by obj_stage1: sound caused on this frame (1 pick up, 3 bonus; a throw: see obj_crate c_snd)
p_rev   = false;       // set by obj_stage1 before User Defined 1: draw the tiles in the opposite order
// body height on the frames of crouching under a carried crate (the crate comes down with it)
p_duck[0] = 16; p_duck[1] = 12; p_duck[2] = 8; p_duck[3] = 4; p_duck[4] = 0;
p_duck[5] = 1;  p_duck[6] = 2;  p_duck[7] = 4; p_duck[8] = 2; p_duck[9] = 0;

// ---- set by obj_stage1 before User Defined 0 --------------------------------------
p_pad     = 0;         // buttons held    (4 = A, 8 = UP, 16 = DOWN, 32 = B, 64 = LEFT, 128 = RIGHT)
p_pressed = 0;         // buttons that went down on this frame

// ---- read by obj_stage1 after User Defined 0 --------------------------------------
p_landed  = false;     // landed on this frame (landing sound)
p_out     = false;     // walked off the right edge: the section is finished
p_restart = false;     // the wait after a fall is over: the section starts again

// ---- what User Defined 1 draws: the state after the PREVIOUS frame (set by obj_stage1) ----
s_x = p_x;  s_y = p_y;  s_pic = 0;  s_face = 1;  s_vis = true;
s_blink = false;       // flickering
s_star = -1;           // stunned: where the star is on its way round the head (0..6), -1 = no star
s_star_slot = 0;       // the star's place in the stage's object list

// ---- the character: global.p1_char is set by the menu (0 = Chip, 1 = Dale) ------------------------
// Chip and Dale move exactly alike. Only the pictures differ: other tiles, put together in a different way.
// Tile i of picture f is drawn at (x + p_tdx, y + p_tdy + 1) facing right, (x - p_tdx - 8, ...) facing left.
// The tiles are in the order of the NES sprite list: tile 0 is in front on even frames, the last one on odd frames.
if (global.p1_char == 0)
{
    p_spr = spr_chip;
    p_spr2 = spr_chip_hurt;      // the tiles of the pictures 14 and 15
    p_tbase = 52;             // the first tile number that is in p_spr2
    p_tn[0] = 7;
    p_tdx[0,0] = 1; p_tdy[0,0] = -25; p_tim[0,0] = 0; p_tdx[0,1] = 1; p_tdy[0,1] = -17; p_tim[0,1] = 1; p_tdx[0,2] = -7; p_tdy[0,2] = -25; p_tim[0,2] = 2; p_tdx[0,3] = -7; p_tdy[0,3] = -17; p_tim[0,3] = 3; p_tdx[0,4] = 0; p_tdy[0,4] = -17; p_tim[0,4] = 4; p_tdx[0,5] = 0; p_tdy[0,5] = -9; p_tim[0,5] = 5; p_tdx[0,6] = -8; p_tdy[0,6] = -9; p_tim[0,6] = 6;
    p_tn[1] = 7;
    p_tdx[1,0] = 5; p_tdy[1,0] = -17; p_tim[1,0] = 7; p_tdx[1,1] = -3; p_tdy[1,1] = -17; p_tim[1,1] = 8; p_tdx[1,2] = 4; p_tdy[1,2] = -25; p_tim[1,2] = 0; p_tdx[1,3] = -4; p_tdy[1,3] = -25; p_tim[1,3] = 2; p_tdx[1,4] = 3; p_tdy[1,4] = -17; p_tim[1,4] = 4; p_tdx[1,5] = 0; p_tdy[1,5] = -9; p_tim[1,5] = 9; p_tdx[1,6] = -8; p_tdy[1,6] = -9; p_tim[1,6] = 10;
    p_tn[2] = 8;
    p_tdx[2,0] = 5; p_tdy[2,0] = -18; p_tim[2,0] = 7; p_tdx[2,1] = -3; p_tdy[2,1] = -18; p_tim[2,1] = 11; p_tdx[2,2] = 4; p_tdy[2,2] = -26; p_tim[2,2] = 0; p_tdx[2,3] = -4; p_tdy[2,3] = -26; p_tim[2,3] = 2; p_tdx[2,4] = 3; p_tdy[2,4] = -18; p_tim[2,4] = 4; p_tdx[2,5] = 0; p_tdy[2,5] = -10; p_tim[2,5] = 12; p_tdx[2,6] = -8; p_tdy[2,6] = -10; p_tim[2,6] = 13; p_tdx[2,7] = -7; p_tdy[2,7] = -2; p_tim[2,7] = 14;
    p_tn[3] = 8;
    p_tdx[3,0] = 4; p_tdy[3,0] = -25; p_tim[3,0] = 0; p_tdx[3,1] = -4; p_tdy[3,1] = -25; p_tim[3,1] = 2; p_tdx[3,2] = 5; p_tdy[3,2] = -17; p_tim[3,2] = 7; p_tdx[3,3] = 3; p_tdy[3,3] = -17; p_tim[3,3] = 4; p_tdx[3,4] = 2; p_tdy[3,4] = -9; p_tim[3,4] = 15; p_tdx[3,5] = -6; p_tdy[3,5] = -9; p_tim[3,5] = 16; p_tdx[3,6] = 0; p_tdy[3,6] = -17; p_tim[3,6] = 17; p_tdx[3,7] = -8; p_tdy[3,7] = -17; p_tim[3,7] = 18;
    p_tn[4] = 7;
    p_tdx[4,0] = 7; p_tdy[4,0] = -19; p_tim[4,0] = 0; p_tdx[4,1] = -1; p_tdy[4,1] = -19; p_tim[4,1] = 2; p_tdx[4,2] = 0; p_tdy[4,2] = -17; p_tim[4,2] = 19; p_tdx[4,3] = 0; p_tdy[4,3] = -9; p_tim[4,3] = 20; p_tdx[4,4] = 8; p_tdy[4,4] = -11; p_tim[4,4] = 7; p_tdx[4,5] = 6; p_tdy[4,5] = -11; p_tim[4,5] = 4; p_tdx[4,6] = -8; p_tdy[4,6] = -9; p_tim[4,6] = 21;
    p_tn[5] = 9;
    p_tdx[5,0] = 9; p_tdy[5,0] = -18; p_tim[5,0] = 22; p_tdx[5,1] = 1; p_tdy[5,1] = -18; p_tim[5,1] = 23; p_tdx[5,2] = -7; p_tdy[5,2] = -18; p_tim[5,2] = 24; p_tdx[5,3] = 4; p_tdy[5,3] = -26; p_tim[5,3] = 0; p_tdx[5,4] = -4; p_tdy[5,4] = -26; p_tim[5,4] = 2; p_tdx[5,5] = -8; p_tdy[5,5] = -26; p_tim[5,5] = 25; p_tdx[5,6] = 3; p_tdy[5,6] = -18; p_tim[5,6] = 26; p_tdx[5,7] = 1; p_tdy[5,7] = -10; p_tim[5,7] = 27; p_tdx[5,8] = -7; p_tdy[5,8] = -10; p_tim[5,8] = 28;
    p_tn[6] = 7;
    p_tdx[6,0] = 1; p_tdy[6,0] = -25; p_tim[6,0] = 0; p_tdx[6,1] = 1; p_tdy[6,1] = -17; p_tim[6,1] = 29; p_tdx[6,2] = -7; p_tdy[6,2] = -25; p_tim[6,2] = 2; p_tdx[6,3] = -7; p_tdy[6,3] = -17; p_tim[6,3] = 3; p_tdx[6,4] = 0; p_tdy[6,4] = -17; p_tim[6,4] = 30; p_tdx[6,5] = 0; p_tdy[6,5] = -9; p_tim[6,5] = 5; p_tdx[6,6] = -8; p_tdy[6,6] = -9; p_tim[6,6] = 6;
    p_tn[7] = 7;
    p_tdx[7,0] = 2; p_tdy[7,0] = -25; p_tim[7,0] = 31; p_tdx[7,1] = 2; p_tdy[7,1] = -17; p_tim[7,1] = 1; p_tdx[7,2] = -6; p_tdy[7,2] = -25; p_tim[7,2] = 32; p_tdx[7,3] = -6; p_tdy[7,3] = -17; p_tim[7,3] = 33; p_tdx[7,4] = 1; p_tdy[7,4] = -17; p_tim[7,4] = 4; p_tdx[7,5] = 0; p_tdy[7,5] = -9; p_tim[7,5] = 34; p_tdx[7,6] = -8; p_tdy[7,6] = -9; p_tim[7,6] = 35;
    p_tn[8] = 7;
    p_tdx[8,0] = 3; p_tdy[8,0] = -25; p_tim[8,0] = 31; p_tdx[8,1] = 3; p_tdy[8,1] = -17; p_tim[8,1] = 1; p_tdx[8,2] = -5; p_tdy[8,2] = -25; p_tim[8,2] = 32; p_tdx[8,3] = -5; p_tdy[8,3] = -17; p_tim[8,3] = 33; p_tdx[8,4] = 2; p_tdy[8,4] = -17; p_tim[8,4] = 4; p_tdx[8,5] = 0; p_tdy[8,5] = -9; p_tim[8,5] = 36; p_tdx[8,6] = -8; p_tdy[8,6] = -9; p_tim[8,6] = 37;
    p_tn[9] = 8;
    p_tdx[9,0] = 3; p_tdy[9,0] = -26; p_tim[9,0] = 31; p_tdx[9,1] = 3; p_tdy[9,1] = -18; p_tim[9,1] = 1; p_tdx[9,2] = -5; p_tdy[9,2] = -26; p_tim[9,2] = 32; p_tdx[9,3] = -5; p_tdy[9,3] = -18; p_tim[9,3] = 33; p_tdx[9,4] = 2; p_tdy[9,4] = -18; p_tim[9,4] = 4; p_tdx[9,5] = 0; p_tdy[9,5] = -10; p_tim[9,5] = 38; p_tdx[9,6] = -8; p_tdy[9,6] = -10; p_tim[9,6] = 39; p_tdx[9,7] = -7; p_tdy[9,7] = -2; p_tim[9,7] = 14;
    p_tn[10] = 7;
    p_tdx[10,0] = 3; p_tdy[10,0] = -25; p_tim[10,0] = 31; p_tdx[10,1] = 3; p_tdy[10,1] = -17; p_tim[10,1] = 1; p_tdx[10,2] = -5; p_tdy[10,2] = -25; p_tim[10,2] = 32; p_tdx[10,3] = -5; p_tdy[10,3] = -17; p_tim[10,3] = 33; p_tdx[10,4] = 2; p_tdy[10,4] = -17; p_tim[10,4] = 4; p_tdx[10,5] = 0; p_tdy[10,5] = -9; p_tim[10,5] = 40; p_tdx[10,6] = -8; p_tdy[10,6] = -9; p_tim[10,6] = 41;
    p_tn[11] = 7;
    p_tdx[11,0] = 2; p_tdy[11,0] = -25; p_tim[11,0] = 31; p_tdx[11,1] = 2; p_tdy[11,1] = -17; p_tim[11,1] = 42; p_tdx[11,2] = -6; p_tdy[11,2] = -25; p_tim[11,2] = 32; p_tdx[11,3] = -6; p_tdy[11,3] = -17; p_tim[11,3] = 33; p_tdx[11,4] = 1; p_tdy[11,4] = -17; p_tim[11,4] = 26; p_tdx[11,5] = 0; p_tdy[11,5] = -9; p_tim[11,5] = 27; p_tdx[11,6] = -8; p_tdy[11,6] = -9; p_tim[11,6] = 28;
    p_tn[12] = 7;
    p_tdx[12,0] = 1; p_tdy[12,0] = -25; p_tim[12,0] = 31; p_tdx[12,1] = 1; p_tdy[12,1] = -17; p_tim[12,1] = 1; p_tdx[12,2] = -7; p_tdy[12,2] = -25; p_tim[12,2] = 32; p_tdx[12,3] = -7; p_tdy[12,3] = -17; p_tim[12,3] = 33; p_tdx[12,4] = 0; p_tdy[12,4] = -17; p_tim[12,4] = 4; p_tdx[12,5] = 0; p_tdy[12,5] = -9; p_tim[12,5] = 34; p_tdx[12,6] = -8; p_tdy[12,6] = -9; p_tim[12,6] = 35;
    p_tn[13] = 12;
    p_tdx[13,0] = 11; p_tdy[13,0] = -33; p_tim[13,0] = 0; p_tdx[13,1] = 11; p_tdy[13,1] = -25; p_tim[13,1] = 43; p_tdx[13,2] = 11; p_tdy[13,2] = -17; p_tim[13,2] = 26; p_tdx[13,3] = 11; p_tdy[13,3] = -9; p_tim[13,3] = 44; p_tdx[13,4] = 3; p_tdy[13,4] = -33; p_tim[13,4] = 2; p_tdx[13,5] = 3; p_tdy[13,5] = -25; p_tim[13,5] = 45; p_tdx[13,6] = 3; p_tdy[13,6] = -17; p_tim[13,6] = 46; p_tdx[13,7] = 3; p_tdy[13,7] = -9; p_tim[13,7] = 47; p_tdx[13,8] = 4; p_tdy[13,8] = -26; p_tim[13,8] = 48; p_tdx[13,9] = -5; p_tdy[13,9] = -25; p_tim[13,9] = 49; p_tdx[13,10] = -5; p_tdy[13,10] = -17; p_tim[13,10] = 50; p_tdx[13,11] = 11; p_tdy[13,11] = -17; p_tim[13,11] = 51;
    // chip: the pictures 14 (hurt) and 15 (stunned), as in the tables above.  Tiles from 52 on are in
    // spr_chip_hurt: sub-image ((tile - 52) * 2 + (1 - facing)) * 7 + brightness
    p_tn[14] = 7;
    p_tdx[14,0] = 0; p_tdy[14,0] = -27; p_tim[14,0] = 52; p_tdx[14,1] = 0; p_tdy[14,1] = -19; p_tim[14,1] = 53; p_tdx[14,2] = 0; p_tdy[14,2] = -11; p_tim[14,2] = 54; p_tdx[14,3] = -8; p_tdy[14,3] = -27; p_tim[14,3] = 55; p_tdx[14,4] = -8; p_tdy[14,4] = -19; p_tim[14,4] = 56; p_tdx[14,5] = -8; p_tdy[14,5] = -11; p_tim[14,5] = 57; p_tdx[14,6] = 0; p_tdy[14,6] = -19; p_tim[14,6] = 58;
    p_tn[15] = 7;
    p_tdx[15,0] = 3; p_tdy[15,0] = -25; p_tim[15,0] = 52; p_tdx[15,1] = 3; p_tdy[15,1] = -17; p_tim[15,1] = 59; p_tdx[15,2] = -5; p_tdy[15,2] = -25; p_tim[15,2] = 55; p_tdx[15,3] = -5; p_tdy[15,3] = -17; p_tim[15,3] = 60; p_tdx[15,4] = 0; p_tdy[15,4] = -17; p_tim[15,4] = 61; p_tdx[15,5] = 0; p_tdy[15,5] = -9; p_tim[15,5] = 62; p_tdx[15,6] = -8; p_tdy[15,6] = -9; p_tim[15,6] = 63;
}
else
{
    p_spr = spr_dale;
    p_spr2 = spr_dale_hurt;      // the tiles of the pictures 14 and 15
    p_tbase = 51;             // the first tile number that is in p_spr2
    p_tn[0] = 7;
    p_tdx[0,0] = 0; p_tdy[0,0] = -25; p_tim[0,0] = 0; p_tdx[0,1] = 0; p_tdy[0,1] = -17; p_tim[0,1] = 1; p_tdx[0,2] = 0; p_tdy[0,2] = -9; p_tim[0,2] = 2; p_tdx[0,3] = 1; p_tdy[0,3] = -17; p_tim[0,3] = 3; p_tdx[0,4] = -7; p_tdy[0,4] = -17; p_tim[0,4] = 4; p_tdx[0,5] = -8; p_tdy[0,5] = -25; p_tim[0,5] = 5; p_tdx[0,6] = -8; p_tdy[0,6] = -9; p_tim[0,6] = 6;
    p_tn[1] = 7;
    p_tdx[1,0] = 3; p_tdy[1,0] = -25; p_tim[1,0] = 0; p_tdx[1,1] = 3; p_tdy[1,1] = -17; p_tim[1,1] = 1; p_tdx[1,2] = 5; p_tdy[1,2] = -17; p_tim[1,2] = 7; p_tdx[1,3] = -3; p_tdy[1,3] = -17; p_tim[1,3] = 8; p_tdx[1,4] = 0; p_tdy[1,4] = -9; p_tim[1,4] = 9; p_tdx[1,5] = -8; p_tdy[1,5] = -9; p_tim[1,5] = 10; p_tdx[1,6] = -5; p_tdy[1,6] = -25; p_tim[1,6] = 5;
    p_tn[2] = 8;
    p_tdx[2,0] = 3; p_tdy[2,0] = -26; p_tim[2,0] = 0; p_tdx[2,1] = 3; p_tdy[2,1] = -18; p_tim[2,1] = 1; p_tdx[2,2] = 5; p_tdy[2,2] = -18; p_tim[2,2] = 7; p_tdx[2,3] = -3; p_tdy[2,3] = -18; p_tim[2,3] = 11; p_tdx[2,4] = 0; p_tdy[2,4] = -10; p_tim[2,4] = 12; p_tdx[2,5] = -8; p_tdy[2,5] = -10; p_tim[2,5] = 13; p_tdx[2,6] = -5; p_tdy[2,6] = -26; p_tim[2,6] = 5; p_tdx[2,7] = -7; p_tdy[2,7] = -2; p_tim[2,7] = 14;
    p_tn[3] = 8;
    p_tdx[3,0] = 3; p_tdy[3,0] = -25; p_tim[3,0] = 0; p_tdx[3,1] = 3; p_tdy[3,1] = -17; p_tim[3,1] = 1; p_tdx[3,2] = -5; p_tdy[3,2] = -25; p_tim[3,2] = 5; p_tdx[3,3] = 5; p_tdy[3,3] = -17; p_tim[3,3] = 7; p_tdx[3,4] = 2; p_tdy[3,4] = -9; p_tim[3,4] = 15; p_tdx[3,5] = -6; p_tdy[3,5] = -9; p_tim[3,5] = 16; p_tdx[3,6] = 0; p_tdy[3,6] = -17; p_tim[3,6] = 17; p_tdx[3,7] = -8; p_tdy[3,7] = -17; p_tim[3,7] = 18;
    p_tn[4] = 7;
    p_tdx[4,0] = 6; p_tdy[4,0] = -19; p_tim[4,0] = 0; p_tdx[4,1] = 6; p_tdy[4,1] = -11; p_tim[4,1] = 1; p_tdx[4,2] = -2; p_tdy[4,2] = -19; p_tim[4,2] = 5; p_tdx[4,3] = 0; p_tdy[4,3] = -17; p_tim[4,3] = 19; p_tdx[4,4] = 0; p_tdy[4,4] = -9; p_tim[4,4] = 20; p_tdx[4,5] = 8; p_tdy[4,5] = -11; p_tim[4,5] = 7; p_tdx[4,6] = -8; p_tdy[4,6] = -9; p_tim[4,6] = 21;
    p_tn[5] = 9;
    p_tdx[5,0] = 3; p_tdy[5,0] = -26; p_tim[5,0] = 22; p_tdx[5,1] = 3; p_tdy[5,1] = -18; p_tim[5,1] = 23; p_tdx[5,2] = -5; p_tdy[5,2] = -26; p_tim[5,2] = 5; p_tdx[5,3] = -8; p_tdy[5,3] = -26; p_tim[5,3] = 24; p_tdx[5,4] = 4; p_tdy[5,4] = -18; p_tim[5,4] = 25; p_tdx[5,5] = 1; p_tdy[5,5] = -18; p_tim[5,5] = 26; p_tdx[5,6] = 1; p_tdy[5,6] = -10; p_tim[5,6] = 27; p_tdx[5,7] = -7; p_tdy[5,7] = -18; p_tim[5,7] = 28; p_tdx[5,8] = -7; p_tdy[5,8] = -10; p_tim[5,8] = 29;
    p_tn[6] = 7;
    p_tdx[6,0] = 0; p_tdy[6,0] = -25; p_tim[6,0] = 30; p_tdx[6,1] = 0; p_tdy[6,1] = -17; p_tim[6,1] = 31; p_tdx[6,2] = 0; p_tdy[6,2] = -9; p_tim[6,2] = 2; p_tdx[6,3] = 1; p_tdy[6,3] = -17; p_tim[6,3] = 32; p_tdx[6,4] = -7; p_tdy[6,4] = -17; p_tim[6,4] = 4; p_tdx[6,5] = -8; p_tdy[6,5] = -25; p_tim[6,5] = 5; p_tdx[6,6] = -8; p_tdy[6,6] = -9; p_tim[6,6] = 6;
    p_tn[7] = 7;
    p_tdx[7,0] = 2; p_tdy[7,0] = -25; p_tim[7,0] = 33; p_tdx[7,1] = 2; p_tdy[7,1] = -17; p_tim[7,1] = 3; p_tdx[7,2] = -6; p_tdy[7,2] = -25; p_tim[7,2] = 34; p_tdx[7,3] = -6; p_tdy[7,3] = -17; p_tim[7,3] = 35; p_tdx[7,4] = 1; p_tdy[7,4] = -17; p_tim[7,4] = 1; p_tdx[7,5] = 0; p_tdy[7,5] = -9; p_tim[7,5] = 36; p_tdx[7,6] = -8; p_tdy[7,6] = -9; p_tim[7,6] = 37;
    p_tn[8] = 7;
    p_tdx[8,0] = 3; p_tdy[8,0] = -25; p_tim[8,0] = 33; p_tdx[8,1] = 3; p_tdy[8,1] = -17; p_tim[8,1] = 3; p_tdx[8,2] = -5; p_tdy[8,2] = -25; p_tim[8,2] = 34; p_tdx[8,3] = -5; p_tdy[8,3] = -17; p_tim[8,3] = 35; p_tdx[8,4] = 2; p_tdy[8,4] = -17; p_tim[8,4] = 1; p_tdx[8,5] = 0; p_tdy[8,5] = -9; p_tim[8,5] = 38; p_tdx[8,6] = -8; p_tdy[8,6] = -9; p_tim[8,6] = 39;
    p_tn[9] = 8;
    p_tdx[9,0] = 3; p_tdy[9,0] = -26; p_tim[9,0] = 33; p_tdx[9,1] = 3; p_tdy[9,1] = -18; p_tim[9,1] = 3; p_tdx[9,2] = -5; p_tdy[9,2] = -26; p_tim[9,2] = 34; p_tdx[9,3] = -5; p_tdy[9,3] = -18; p_tim[9,3] = 35; p_tdx[9,4] = 2; p_tdy[9,4] = -18; p_tim[9,4] = 1; p_tdx[9,5] = 0; p_tdy[9,5] = -10; p_tim[9,5] = 40; p_tdx[9,6] = -8; p_tdy[9,6] = -10; p_tim[9,6] = 41; p_tdx[9,7] = -7; p_tdy[9,7] = -2; p_tim[9,7] = 14;
    p_tn[10] = 7;
    p_tdx[10,0] = 3; p_tdy[10,0] = -25; p_tim[10,0] = 33; p_tdx[10,1] = 3; p_tdy[10,1] = -17; p_tim[10,1] = 3; p_tdx[10,2] = -5; p_tdy[10,2] = -25; p_tim[10,2] = 34; p_tdx[10,3] = -5; p_tdy[10,3] = -17; p_tim[10,3] = 35; p_tdx[10,4] = 2; p_tdy[10,4] = -17; p_tim[10,4] = 1; p_tdx[10,5] = 0; p_tdy[10,5] = -9; p_tim[10,5] = 42; p_tdx[10,6] = -8; p_tdy[10,6] = -9; p_tim[10,6] = 43;
    p_tn[11] = 7;
    p_tdx[11,0] = 2; p_tdy[11,0] = -25; p_tim[11,0] = 33; p_tdx[11,1] = 2; p_tdy[11,1] = -17; p_tim[11,1] = 25; p_tdx[11,2] = -6; p_tdy[11,2] = -25; p_tim[11,2] = 34; p_tdx[11,3] = -6; p_tdy[11,3] = -17; p_tim[11,3] = 35; p_tdx[11,4] = 1; p_tdy[11,4] = -17; p_tim[11,4] = 23; p_tdx[11,5] = 0; p_tdy[11,5] = -9; p_tim[11,5] = 27; p_tdx[11,6] = -8; p_tdy[11,6] = -9; p_tim[11,6] = 29;
    p_tn[12] = 7;
    p_tdx[12,0] = 1; p_tdy[12,0] = -25; p_tim[12,0] = 33; p_tdx[12,1] = 1; p_tdy[12,1] = -17; p_tim[12,1] = 3; p_tdx[12,2] = -7; p_tdy[12,2] = -25; p_tim[12,2] = 34; p_tdx[12,3] = -7; p_tdy[12,3] = -17; p_tim[12,3] = 35; p_tdx[12,4] = 0; p_tdy[12,4] = -17; p_tim[12,4] = 1; p_tdx[12,5] = 0; p_tdy[12,5] = -9; p_tim[12,5] = 36; p_tdx[12,6] = -8; p_tdy[12,6] = -9; p_tim[12,6] = 37;
    p_tn[13] = 9;
    p_tdx[13,0] = 11; p_tdy[13,0] = -25; p_tim[13,0] = 0; p_tdx[13,1] = 11; p_tdy[13,1] = -17; p_tim[13,1] = 44; p_tdx[13,2] = 11; p_tdy[13,2] = -9; p_tim[13,2] = 45; p_tdx[13,3] = 3; p_tdy[13,3] = -25; p_tim[13,3] = 46; p_tdx[13,4] = 3; p_tdy[13,4] = -17; p_tim[13,4] = 47; p_tdx[13,5] = 3; p_tdy[13,5] = -9; p_tim[13,5] = 48; p_tdx[13,6] = -5; p_tdy[13,6] = -25; p_tim[13,6] = 49; p_tdx[13,7] = -5; p_tdy[13,7] = -17; p_tim[13,7] = 50; p_tdx[13,8] = 11; p_tdy[13,8] = -17; p_tim[13,8] = 23;
    // dale: the pictures 14 (hurt) and 15 (stunned), as in the tables above.  Tiles from 51 on are in
    // spr_dale_hurt: sub-image ((tile - 51) * 2 + (1 - facing)) * 7 + brightness
    p_tn[14] = 7;
    p_tdx[14,0] = 0; p_tdy[14,0] = -19; p_tim[14,0] = 51; p_tdx[14,1] = -8; p_tdy[14,1] = -19; p_tim[14,1] = 52; p_tdx[14,2] = -3; p_tdy[14,2] = -27; p_tim[14,2] = 53; p_tdx[14,3] = -9; p_tdy[14,3] = -27; p_tim[14,3] = 54; p_tdx[14,4] = 0; p_tdy[14,4] = -19; p_tim[14,4] = 55; p_tdx[14,5] = 0; p_tdy[14,5] = -11; p_tim[14,5] = 56; p_tdx[14,6] = -8; p_tdy[14,6] = -11; p_tim[14,6] = 57;
    p_tn[15] = 7;
    p_tdx[15,0] = 0; p_tdy[15,0] = -25; p_tim[15,0] = 53; p_tdx[15,1] = 0; p_tdy[15,1] = -17; p_tim[15,1] = 58; p_tdx[15,2] = 0; p_tdy[15,2] = -9; p_tim[15,2] = 59; p_tdx[15,3] = 3; p_tdy[15,3] = -17; p_tim[15,3] = 60; p_tdx[15,4] = -5; p_tdy[15,4] = -17; p_tim[15,4] = 61; p_tdx[15,5] = -6; p_tdy[15,5] = -25; p_tim[15,5] = 54; p_tdx[15,6] = -8; p_tdy[15,6] = -9; p_tim[15,6] = 62;
}

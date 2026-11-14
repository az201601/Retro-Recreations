/// obj_crate : Create
// A crate that has been picked up: carried on the player's head or flying. (A crate that nobody has
// touched yet is part of the background picture and of obj_stage1's block table.)
// Created by scr_pl_pick, which also sets stage, c_wx, c_y, s_x, s_y.
// It has no Step and no Draw event: obj_stage1 runs User Defined 0 and 1.
stage  = noone;        // the obj_stage1 instance
c_wx   = 0;            // position in the section: middle ...
c_y    = 0;            // ... and bottom edge (screen position)
c_mode = 0;            // 0 carried, 1 thrown straight ahead, 2 straight up, 3 far throw, 4 diagonally up,
                       // 5 it hit an enemy and breaks
c_dir  = 1;            // 1 flies right, -1 left
c_t    = 0;            // frames since the throw / since it hit an enemy
c_gone = false;        // left the screen or broken: obj_stage1 removes it
c_eyes = 0;            // the player hides under it and looks out: 0 no eyes, 1 eyes to the left, 2 eyes to the right
c_slot = 0;            // its place 3..11 in the stage's object list (crates and enemies act and are drawn in this order)
c_hot  = false;        // it has been thrown: an enemy it touches is knocked out
c_pic  = 0;            // breaking: 0-2 still whole (as c_eyes), 3..7 the four quarters flying apart
c_snd  = 0;            // sound to ask for when its turn comes (2 throw, 4 far throw)

// ---- what is shown: the state after the PREVIOUS frame (set by obj_stage1) ----
s_x = 0;  s_y = 0;  s_flash = 0;  s_vis = false;  s_eyes = 0;  s_pic = 0;

/// obj_enemy : Create
// An enemy of level 1, section 1. Created by scr_lv_spawn, which sets stage, e_kind, e_wx, e_y, e_face, e_slot.
// It has no Step and no Draw event: obj_stage1 runs User Defined 0 (in the order of the object list) and 1.
stage  = noone;        // the obj_stage1 instance
e_kind = 0;            // 1 flyer, 2 what the flyer drops, 3 cook, 4 the fork the cook throws
e_slot = 0;            // its place 3..11 in the stage's object list
e_wx   = 0;            // position in the section: middle ...
e_y    = 0;            // ... and bottom edge (screen position)
e_xs   = 0;            // sixteenths of a pixel of e_wx and e_y
e_ys   = 0;
e_xv   = 0;            // speed in sixteenths of a pixel per frame
e_yv   = 0;
e_face = 0;            // 0 looks left, 1 looks right
e_pic  = 0;            // picture (the original's number; tables en_t* in obj_stage1 Create)
e_w    = 0;            // half the width and the height of its body
e_h    = 0;
e_hp   = 0;            // 1 alive, 0 knocked out
e_dmg  = 0;            // what touching it will cost the player (TODO later step: hurting the player)
e_state = -1;          // -1 new; flyer: 0 waiting, 1 flying / hovering; cook: 0 waiting, 1 walking to and fro,
                       // 2 throwing, 3 walking on, 4 in the air; 8 the fork knocked down; 9 knocked out
e_t    = 0;            // frame counter of the state
e_n    = 0;            // cook: step of the walk
e_ok   = false;        // flyer / cook: it was on the screen when it last looked
e_seen = false;        // it has been on the screen: it is removed when it leaves it
e_hide = true;         // not shown yet (new)
e_gone = false;        // left the screen: obj_stage1 removes it

// ---- what is shown: the state after the PREVIOUS frame (set by obj_stage1) ----
s_x = 0;  s_y = 0;  s_pic = 0;  s_face = 0;  s_vis = false;

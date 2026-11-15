/// obj_enemy : Create
// An enemy of level 1, section 1. Created by scr_lv_spawn, which sets stage, e_kind, e_wx, e_y, e_face, e_slot.
// It has no Step and no Draw event: obj_stage1 runs User Defined 0 (in the order of the object list) and 1.
stage  = noone;        // the obj_stage1 instance
e_kind = 0;            // 1 flyer, 2 what the flyer drops, 3 cook, 4 the fork the cook throws,
                       // 5 the mouse with the spoon, 6 the mouse under a crate
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
e_hp   = 0;            // 1 alive, 0 knocked out (the mouse with the spoon: 2, and 1 once a crate has stunned it)
e_dmg  = 0;            // what touching it will cost the player (0 = nothing; see scr_pl_enemy_touch)
e_state = -1;          // -1 new; flyer: 0 waiting, 1 flying / hovering; cook: 0 waiting, 1 walking to and fro,
                       // 2 throwing, 3 walking on, 4 in the air; 8 the fork knocked down; 9 knocked out;
                       // the mice: see scr_en_mouse and scr_en_cmouse
e_t    = 0;            // frame counter of the state
e_n    = 0;            // cook: step of the walk; mouse: frames of the swing / 0, 1, 2 = frames it has been carried
e_i    = 0;            // mouse with the spoon: which of its 4 walking pictures
e_star = 0;            // stunned mouse: the place of its star in the stage's object list (0 = no star)
e_sc   = 0;            // frames the star has been going round
e_new  = false;        // stunned on this frame: it starts to move on the next
// A stunned mouse can be carried and thrown like a crate (obj_player's p_carry): for that it has these variables
// of obj_crate. Only c_hot (thrown), c_dir and c_snd are used.
c_eyes = 0;  c_hot = false;  c_dir = 1;  c_mode = 0;  c_t = 0;  c_snd = 0;
e_ok   = false;        // flyer / cook: it was on the screen when it last looked
e_seen = false;        // it has been on the screen: it is removed when it leaves it
e_hide = true;         // not shown yet (new)
e_gone = false;        // left the screen: obj_stage1 removes it

// ---- what is shown: the state after the PREVIOUS frame (set by obj_stage1) ----
s_x = 0;  s_y = 0;  s_pic = 0;  s_face = 0;  s_vis = false;
s_flip = false;        // upside down (carried or thrown)
s_star = -1;           // the step 0..6 of its star's circle (-1 = no star)
s_star_slot = 0;       // the star's place in the object list

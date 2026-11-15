/// obj_item : Create   (something to collect; made and filled in by scr_pl_pick or obj_stage1's End Step)
// Not visible by itself and without a Draw event: obj_stage1 draws it (User Defined 1).
stage  = noone;        // the obj_stage1 instance
i_kind = 0;            // 0 the acorn (a heart more), 1 the star (a life more), 2 the sign "1UP" the star turns into
i_t    = 0;            // frames as a sign
i_hit  = false;        // the star: the player touched it on this frame (it gives its life on the next)
e_wx   = 0;            // position in the section (x of its middle) ...
e_y    = 0;            // ... and on the screen (y of its lower edge)
e_slot = 0;            // its place in the stage's object list
e_gone = false;        // taken, or the sign's time is over: obj_stage1 removes it on the next frame
// what the Draw event shows (the picture is one frame behind the game): set by obj_stage1
s_x = 0;  s_y = 0;  s_kind = 0;  s_vis = false;

/// obj_enemy : User Defined 2   (remembers what the next picture shows; run by obj_stage1 at the end of a frame)
s_x = e_wx - stage.lv_cam_x;
s_y = e_y;
s_pic = e_pic;
s_face = e_face;
s_vis = (!e_hide && !e_gone);
// a mouse that is carried (from the 2nd frame on) or thrown is upside down
s_flip = (e_state == 13 || (e_state == 12 && e_n == 2));
// a stunned mouse that is about to get up flickers: from frame 482 of the 600 it is hidden for 2 frames of every 4
if (e_state == 6 && e_t >= 482 && (e_t & 3) >= 2) s_vis = false;
// its star: a step further round every 4 frames
if (e_star != 0) s_star = (e_sc div 4) mod 7; else s_star = -1;
s_star_slot = e_star;

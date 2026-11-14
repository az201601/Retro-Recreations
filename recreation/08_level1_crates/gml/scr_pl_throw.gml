/// scr_pl_throw(held)
// Called by obj_player: the carried crate is let go.
// held = the buttons (8 = UP, 64 / 128 = LEFT / RIGHT) that choose the direction.
var cr = p_carry;
p_carry = noone;
p_throw = 1;
p_snd = 2;
cr.c_wx = p_x + stage.lv_cam_x;
if (p_h != 0) cr.c_y = p_y - 16;                // (crouched all the way down: it starts where it is)
if (p_face == 1) cr.c_dir = 1; else cr.c_dir = -1;
cr.c_t = 0;
if (p_run >= 30) { cr.c_mode = 3; p_snd = 4; }  // after a run-up: the far throw
else if ((argument0 & 8) != 0)
{
    if ((argument0 & 192) != 0) cr.c_mode = 4;  // UP + LEFT / RIGHT: diagonally up
    else cr.c_mode = 2;                         // UP: straight up
}
else cr.c_mode = 1;                             // straight ahead

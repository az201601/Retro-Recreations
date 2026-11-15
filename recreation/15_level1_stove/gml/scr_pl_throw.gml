/// scr_pl_throw(held)
// Called by obj_player: the carried crate (or stunned mouse) is let go.
// held = the buttons (8 = UP, 16 = DOWN, 64 / 128 = LEFT / RIGHT) that choose the direction.
var cr = p_carry;
p_carry = noone;
cr.c_eyes = 0;
p_throw = 1;
var snd = 2;
cr.c_hot = true;                                // from now on it knocks enemies out
if (cr.object_index == obj_enemy)
{
    // a stunned mouse: it flies straight ahead from where it was carried, whatever else is held; no far throw
    if (cr.e_n != 0) cr.e_y = p_y - p_h - 1;
    if (p_face == 1) cr.c_dir = 1; else cr.c_dir = -1;
    if ((argument0 & 128) != 0) cr.c_dir = 1;
    else if ((argument0 & 64) != 0) cr.c_dir = -1;
    p_kick = false;
    cr.c_snd = snd;
    return 0;
}
cr.c_wx = p_x + stage.lv_cam_x;
if (p_h != 0) cr.c_y = p_y - 16;                // (crouched all the way down: it starts where it is)
if (p_face == 1) cr.c_dir = 1; else cr.c_dir = -1;
// LEFT / RIGHT held on the frame of the throw decide the direction, even before the player has turned
if ((argument0 & 128) != 0) cr.c_dir = 1;
else if ((argument0 & 64) != 0) cr.c_dir = -1;
// Thrown sideways from under the crate (crouched all the way down, LEFT or RIGHT held, DOWN let go): the crate
// leaves along the ground, the player is set 13 pixels back from it, whatever is there, and takes no step
// on this frame.
p_kick = (p_h == 0 && (argument0 & 192) != 0 && (argument0 & 16) == 0);
if (p_kick) p_x -= 13 * cr.c_dir;
cr.c_t = 0;
if (p_run >= 30) { cr.c_mode = 3; snd = 4; }    // after a run-up: the far throw
else if ((argument0 & 8) != 0)
{
    if ((argument0 & 192) != 0) cr.c_mode = 4;  // UP + LEFT / RIGHT: diagonally up
    else cr.c_mode = 2;                         // UP: straight up
}
else cr.c_mode = 1;                             // straight ahead
cr.c_snd = snd;                                 // the crate asks for the sound (2 throw, 4 far throw) when its turn comes

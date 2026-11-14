/// obj_crate : User Defined 0   (one NES frame of a thrown or breaking crate; run by obj_stage1 in the order of the object list)
if (c_mode == 5)
{
    // it hit an enemy (see obj_enemy User Defined 0): 1 more frame whole, 5 frames of pieces, then gone
    c_t += 1;
    if (c_t == 1) c_pic = c_eyes; else c_pic = c_t + 1;
    if (stage.pl.p_carry == id) stage.pl.p_carry = noone;       // the player was hiding under it
    if (c_t == 7) { c_gone = true; stage.lv_slot_k[c_slot] = 0; }
    exit;
}
switch (c_mode)
{
    case 1: c_wx += 4 * c_dir; break;
    case 2: c_y -= 6; break;
    case 4: c_wx += 4 * c_dir; c_y -= 4; break;
    case 3:     // far throw: 8 frames rising by 1, 8 frames sinking by 1, and so on
        c_wx += 4 * c_dir;
        if (((c_t div 8) mod 2) == 0) c_y -= 1; else c_y += 1;
        break;
}
c_t += 1;
// gone when its middle is off the screen (measured with the camera position before this frame) or far above it
var sx = c_wx - stage.lv_cam_show;
if (sx < 0 || sx > 255 || c_y < -72) { c_gone = true; stage.lv_slot_k[c_slot] = 0; }
// Not checked: hitting a wall (see the README).

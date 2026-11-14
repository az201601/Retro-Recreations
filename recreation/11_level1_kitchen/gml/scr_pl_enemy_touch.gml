/// scr_pl_enemy_touch()
// Called by obj_player at the start of its frame: does the body touch an enemy (both where the previous frame
// left them)? The enemies are looked at from the last place of the object list down; the first one touched counts.
//   what the flyer drops: stunned (state 14), pushed half a pixel a frame the way the thing was flying
//   anything else that can hurt: a heart less, thrown up and 2 pixels a frame away from the enemy (state 9),
//   64 frames in which nothing can hurt; the last heart costs a life
// Nothing is touched while crouching under a crate (p_h == 0), in the 16 frames of a throw, or while p_ghost is set.
if (p_h == 0 || p_ghost || p_throw != 0) return false;
var j, e, dx, dy;
for (j = 11; j >= 3; j -= 1)
{
    if (stage.lv_slot_k[j] != 2) continue;
    e = stage.lv_slot[j];
    if (e.e_hp == 0 || e.e_hide) continue;
    dx = p_x - (e.e_wx - stage.lv_cam_x);
    dy = p_y - e.e_y;
    if (abs(dx) > 6 + e.e_w || dy > p_h || dy < -e.e_h) continue;
    if (e.e_kind == 2)
    {
        if (!p_stun)
        {
            if (e.e_xv < 0) p_push = -8; else p_push = 8;
            p_yv = 0;
            p_state = 14;
        }
    }
    else if (e.e_dmg != 0)
    {
        if (dx >= 0) p_push = -32; else p_push = 32;
        p_state = 9;
        p_inv = 64;
        p_flash = true;
        p_ghost = true;
        p_snd = 9;
        p_stun = false;
        if (p_hp != 0)
        {
            p_hp -= 1;
            if (p_hp == 0) stage.lv_lives -= 1;
        }
    }
    return true;
}
return false;

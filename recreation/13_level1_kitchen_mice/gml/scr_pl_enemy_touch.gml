/// scr_pl_enemy_touch()
// Called by obj_player at the start of its frame: does the body touch an enemy (both where the previous frame
// left them)? The enemies are looked at from the last place of the object list down; the first one touched counts.
//   what the flyer drops, a crate the mouse has batted back: stunned (state 14), pushed half a pixel a frame the way the thing was flying
//   anything else that can hurt: a heart less, thrown up and 2 pixels a frame away from the enemy (state 9),
//   64 frames in which nothing can hurt; the last heart costs a life
// Nothing is touched while crouching under a crate (p_h == 0), in the 16 frames of a throw, or while p_ghost is set.
var j, e, dx, dy;
// A star that was touched on the frame before: a life more (10 at most, shown as 9), and the star turns into the
// sign "1UP", 17 pixels higher up - also when the player has moved away since, and also at 10 lives.
for (j = 3; j < 12; j += 1)
{
    if (stage.lv_slot_k[j] != 5) continue;
    e = stage.lv_slot[j];
    if (e.i_kind == 1 && e.i_hit)
    {
        stage.lv_lives = min(stage.lv_lives + 1, 10);
        p_snd = 14;
        e.i_kind = 2;
        e.i_t = -1;
        e.e_y -= 17;
    }
}
if (p_h == 0 || p_ghost || p_throw != 0) return false;
for (j = 11; j >= 3; j -= 1)
{
    if (stage.lv_slot_k[j] == 5)
    {
        // An item. Its reach is that of every object: sideways the two half widths, up and down from the item's
        // height above its line to the player's body height below it.
        //   the acorn (4 wide to each side, 10 high): a heart more (3 at most; at 3 hearts it is taken and gives
        //     nothing) and it is gone at once, without a sound
        //   the star (6 and 12): only marked here; what it gives comes on the next frame (above)
        // Touching one does not end the search.
        e = stage.lv_slot[j];
        dx = p_x - (e.e_wx - stage.lv_cam_x);
        dy = p_y - e.e_y;
        if (e.i_kind == 0 && abs(dx) <= 10 && dy >= -10 && dy <= p_h)
        {
            p_hp = min(p_hp + 1, 3);
            e.e_gone = true;
            stage.lv_slot_k[j] = 0;
        }
        else if (e.i_kind == 1 && abs(dx) <= 12 && dy >= -12 && dy <= p_h) e.i_hit = true;
        continue;
    }
    if (stage.lv_slot_k[j] == 1)
    {
        // a crate the mouse has batted back: it breaks on the player, who is stunned and pushed the way it flew
        e = stage.lv_slot[j];
        dx = p_x - (e.c_wx - stage.lv_cam_x);
        dy = p_y - e.c_y;
        if (e.c_back && e.c_mode != 5 && abs(dx) <= 14 && dy >= -16 && dy <= p_h)
        {
            e.c_mode = 5; e.c_t = 0; e.c_hot = false;
            if (!p_stun)
            {
                if (e.c_dir < 0) p_push = -8; else p_push = 8;
                p_yv = 0;
                p_state = 14;
            }
            return true;
        }
        continue;
    }
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

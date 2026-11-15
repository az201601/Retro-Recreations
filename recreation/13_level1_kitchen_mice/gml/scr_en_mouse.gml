/// scr_en_mouse(state)
// Called by obj_enemy User Defined 0: one frame of the mouse with the spoon (e_kind 5).
// e_state: 0 waits until it has been on the screen, 1 walks 32 pixels to and fro, 2 swings the spoon at a crate,
//          4 falls, 5 hit by a crate: in the air, 6 lies stunned, 12 carried by the player, 13 thrown
var st = argument0;
var g = stage;
var c;
if (st == -1)
{
    e_pic = 0; e_hp = 2; e_dmg = 1; e_w = 8; e_h = 24;
    e_hide = false; e_state = 0; e_ok = e_seen;
}
else if (st == 0)
{
    if (e_ok)
    {
        scr_en_face_player();
        if (e_face == 1) e_xv = 16; else e_xv = -16;
        e_yv = 0; e_state = 1; e_t = 0; e_i = 0;
    }
    else e_ok = e_seen;
}
else if (st == 2)
{
    // 9 frames the spoon is back, 9 frames the swing, 9 + 9 frames after it
    e_n += 1;
    if (e_n == 9)
    {
        e_pic = 4;
        g.lv_snd = 16;
        c = scr_en_crate_ahead(32);                     // a crate that is near enough now flies back
        if (c != noone)                                 // (not a crate of a far throw: that one flies on)
        {
            if (c.c_mode != 3) { c.c_dir = -c.c_dir; c.c_back = true; }
        }
    }
    else if (e_n == 18) e_pic = 5;
    else if (e_n == 27) e_pic = 0;
    else if (e_n == 36)
    {
        // ... and on with the next of its walking pictures, towards the player
        scr_en_face_player();
        if (e_face == 1) e_xv = 16; else e_xv = -16;
        e_state = 1;
        scr_en_next_pic();
    }
}
else if (st == 4)
{
    if (scr_en_air()) e_state = 1;
}
else if (st == 5)
{
    if (scr_en_air()) { e_state = 6; e_t = 0; e_xv = 0; }
}
else if (st == 12)
{
    // carried: upside down on the player's head, looking the other way (from the 2nd frame on). It stays
    // stunned for as long as it is carried.
    // The player's throw sets c_hot: it flies off level, 4 pixels a frame, through walls, and knocks out
    // every enemy it meets (see obj_enemy User Defined 0).
    if (e_n != 0) { e_face = 1 - g.pl.p_face; e_n = 2; }
    else e_n = 1;
    if (c_hot && g.pl.p_state == 23)
    {
        // the player lost the last heart: the mouse is gone at once, with the throw sound
        if (c_snd != 0) { g.lv_snd = c_snd; c_snd = 0; }
        e_gone = true;
        g.lv_slot_k[e_slot] = 0;
        if (e_star != 0) { g.lv_slot_k[e_star] = 0; e_star = 0; }
        exit;
    }
    if (c_hot)
    {
        // it leaves from where the player is now on the screen (with the camera position before this frame)
        e_wx = g.pl.p_x + g.lv_cam_show;
        e_state = 13; e_dmg = 2; e_xv = 64 * c_dir; e_yv = 0;
        scr_en_move_x();
        if (c_snd != 0) { g.lv_snd = c_snd; c_snd = 0; }
    }
}
else if (st == 13) scr_en_move_x();
else if (st == 6)
{
    // stunned for 600 frames, then it is as new (its star goes)
    e_t += 1;
    if (e_t == 600)
    {
        e_dmg = 1; e_state = 0; e_pic = 0; e_hp = 2;
        g.lv_slot_k[e_star] = 0;
        e_star = 0;
    }
}
if (e_state == 1 && st == 1)
{
    c = scr_en_crate_ahead(64);
    if (c != noone)
    {
        // a thrown crate is coming: it turns to it and swings the spoon
        if (c.c_wx >= e_wx) e_face = 1; else e_face = 0;
        e_pic = 3; e_state = 2; e_n = 0;
    }
    else
    {
        scr_en_move_x();
        if (scr_en_wall()) { e_i = 3; scr_en_next_pic(); exit; }        // at a wall it turns at once
        if (!scr_en_floor()) { e_state = 4; exit; }                     // the floor is gone: it falls
        e_t += 1;
        if (e_t == 8) { e_t = 0; scr_en_next_pic(); }
    }
}

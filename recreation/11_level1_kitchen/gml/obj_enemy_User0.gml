/// obj_enemy : User Defined 0   (one NES frame; run by obj_stage1 in the order of the object list)
var g = stage;
var cam0 = g.lv_cam_show;               // the camera position before this frame
var sx, j, c, d, st, t, q, y0, e, hot;

// ---- 1) hit by a crate?  (not what the flyer drops) -------------------------------------
// A crate knocks an enemy out if it was thrown, or if the player hides under it (crouched all the way down).
sx = e_wx - cam0;
if (e_kind != 2 && e_hp != 0 && sx >= 0 && sx <= 255 && e_y >= 0 && e_y <= 255)
{
    for (j = 11; j >= 3; j -= 1)
    {
        if (g.lv_slot_k[j] != 1) continue;
        c = g.lv_slot[j];
        hot = c.c_hot;
        if (c.c_mode == 0 && g.pl.p_state == 3 && g.pl.p_h == 0) hot = true;
        if (!hot) continue;
        if (!scr_en_hit_by(c)) continue;
        d = 1;                                                  // it is flung the way the crate flew (right if it did not fly sideways)
        if ((c.c_mode == 1 || c.c_mode == 3 || c.c_mode == 4) && c.c_dir < 0) d = -1;
        // the crate stops and breaks. (NOT MEASURED: a crate of a far throw is assumed to fly on; and the fling
        // to the left was not seen, no crate flying left hit anything in the recordings.)
        if (c.c_mode != 3) { c.c_mode = 5; c.c_t = 0; c.c_hot = false; }
        e_hp = 0;
        e_t = 0;
        if (e_kind == 4) { e_state = 8; e_xv = 12 * d; e_yv = -32; }         // the fork: no sound
        else { e_state = 9; e_dmg = 0; e_xv = 67 * d; e_yv = -67; g.lv_snd = 8; }
        break;
    }
}

// ---- 2) what it does ------------------------------------------------------------------
st = e_state;
if (st == 9)                            // knocked out: flies away up and sideways, 4 3/16 pixels each per frame
{
    scr_en_move_x();
    scr_en_move_y();
}
else if (st == 8)                       // the fork, knocked down: falls
{
    if (e_t > 0 && e_yv < 80) e_yv += 3;
    e_t = 1;
    scr_en_move_x();
    scr_en_move_y();
}
else if (e_kind == 1)                   // ---- flyer
{
    if (st == -1)
    {
        e_pic = 22; e_hp = 1; e_dmg = 1; e_w = 8; e_h = 16; e_xv = 16; e_yv = 4;
        e_hide = false; e_state = 0; e_ok = e_seen;
    }
    else if (st == 0)
    {
        if (e_ok)                       // starts towards the player
        {
            scr_en_face_player();
            if (e_face == 1) e_xv = 16; else e_xv = -16;
            e_state = 1; e_t = 0;
        }
        else e_ok = e_seen;
    }
    if (e_state == 1)
    {
        // 48 frames flying (1 pixel sideways and 1/4 pixel down or up per frame), 48 frames on the spot
        if (e_t == 96) { e_t = 0; e_yv = -e_yv; }       // down on one flight, up on the next
        t = e_t;
        if (t < 48)
        {
            if ((t mod 3) == 0) { e_pic = 22 + ((t div 3) mod 2); g.lv_snd = 6; }
            scr_en_move_x();
            scr_en_move_y();
        }
        else if (((t - 48) mod 4) == 0)
        {
            q = (t - 48) div 4;         // 0..11
            if (q == 8)                 // after 32 frames on the spot it drops something
            {
                with (g) e = scr_lv_spawn(2, other.e_wx, other.e_y, other.e_face);
                // in a place before its maker's it does not act on this frame, and misses this frame's camera step
                if (e != noone) { if (e.e_slot < e_slot) e.e_wx += g.lv_cam_x - g.lv_cam_show; }
            }
            e_pic = g.en_hover[q];
            g.lv_snd = 6;
        }
        e_t += 1;
    }
}
else if (e_kind == 2)                   // ---- what the flyer drops: falls, faster by 3/16 per frame up to 5 pixels per frame
{
    if (st == -1)
    {
        e_seen = true; e_y += 8; e_hp = 1; e_dmg = 2; e_w = 2; e_h = 4; e_pic = 28; e_yv = 8;
        e_hide = false; e_state = 1;
    }
    else if (e_yv < 80) e_yv += 3;
    scr_en_move_y();
}
else if (e_kind == 4)                   // ---- the fork: 3 pixels per frame
{
    if (st == -1)
    {
        e_hp = 1; e_dmg = 1; e_w = 8; e_h = 4; e_pic = 14; e_y -= 16; e_seen = true;
        e_hide = false; e_state = 1;
        if (e_face == 1) { e_wx += 19; e_xv = 48; } else { e_wx -= 19; e_xv = -48; }
    }
    scr_en_move_x();
}
else if (e_kind == 3)                   // ---- cook
{
    if (st == -1)
    {
        e_pic = 7; e_hp = 1; e_dmg = 1; e_w = 8; e_h = 24;
        e_hide = false; e_state = 0; e_ok = e_seen;
    }
    else if (st == 0)
    {
        if (e_ok)
        {
            scr_en_face_player();
            if (e_face == 1) e_xv = 16; else e_xv = -16;
            e_yv = 0; e_state = 1; e_t = 0;
        }
        else e_ok = e_seen;
    }
    else if (st == 1 && scr_en_near_player())           // sees the player: stops and throws
    {
        scr_en_face_player();
        if (e_face == 1) e_xv = 16; else e_xv = -16;
        e_state = 2; e_t = 0; e_pic = 7;
    }
    else if (st == 2)
    {
        e_t += 1;
        if (e_t == 17) e_pic = 12;
        else if (e_t == 34)
        {
            e_pic = 13;
            g.lv_snd = 7;
            with (g) e = scr_lv_spawn(4, other.e_wx, other.e_y, other.e_face);
            if (e != noone) { if (e.e_slot < e_slot) e.e_wx += g.lv_cam_x - g.lv_cam_show; }
        }
        else if (e_t == 51) e_pic = 7;
        else if (e_t == 68) { e_pic = 8; e_state = 3; e_t = 0; e_n = 0; }
    }
    else if (st == 3)                                   // after the throw: walks on, jumps at walls and edges
    {
        scr_en_move_x();
        d = scr_en_wall();
        if (!d) d = !scr_en_floor();
        if (d) { e_pic = 9; e_yv = -64; e_state = 4; }
        else
        {
            e_t += 1;
            if (e_t == 8) { e_t = 0; e_n = (e_n + 1) mod 4; e_pic = g.en_walk[e_n]; }
        }
    }
    else if (st == 4)                                   // in the air
    {
        scr_en_move_x();
        scr_en_wall();
        if (e_yv < 80) e_yv += 3;
        if (e_yv < 0)
        {
            scr_en_move_y();
            if (scr_en_ceiling()) e_yv = 1;
        }
        else
        {
            y0 = e_y;
            scr_en_move_y();
            // lands when it enters a new row of blocks that can be stood on
            if (floor((((e_y mod 256) + 256) mod 256) / 16) != floor((((y0 mod 256) + 256) mod 256) / 16))
            {
                if (scr_en_floor()) { e_yv = 0; e_state = 3; e_t = 0; e_n = (e_n + 1) mod 4; e_pic = g.en_walk[e_n]; }
            }
        }
    }
    if (e_state == 1 && (st == 1 || st == 0))           // walks 32 pixels to and fro, 1 pixel per frame
    {
        t = e_t;
        if ((t mod 8) == 0)
        {
            if ((t mod 32) == 0 && t > 0) { e_face = 1 - e_face; e_xv = -e_xv; }
            e_pic = g.en_walk[(t div 8) mod 4];
        }
        scr_en_move_x();
        e_t += 1;
    }
}

// ---- 3) once it has been on the screen, it is removed when it leaves it -------------------
// (measured with the camera position before this frame)
sx = e_wx - cam0;
if (e_seen)
{
    if (sx < 0 || sx > 255 || e_y < -72 || e_y >= 237) { e_gone = true; g.lv_slot_k[e_slot] = 0; }
}
else if (sx >= 0 && sx <= 255 && e_y >= 0 && e_y <= 255) e_seen = true;

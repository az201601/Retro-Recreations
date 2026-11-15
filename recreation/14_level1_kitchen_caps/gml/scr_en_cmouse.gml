/// scr_en_cmouse(state)
// Called by obj_enemy User Defined 0: one frame of the mouse that hides under a crate (e_kind 6).
// e_state: 0 waits until it has been on the screen, 1 hides, 2 gets up, 3 walks, 4 in the air
var st = argument0;
var g = stage;
var t;
if (st == -1)
{
    e_wx -= 8; e_pic = 76; e_hp = 1; e_dmg = 1; e_w = 8; e_h = 15;
    e_hide = false; e_state = 0; e_ok = e_seen;
}
else if (st == 0)
{
    if (e_ok) { scr_en_face_player(); e_state = 1; }
    else e_ok = e_seen;
}
else if (st == 1)
{
    // the player comes within 80 pixels on its level: it gets up
    if (scr_en_near_player()) { e_state = 2; e_t = 0; e_h = 24; e_pic = 15; g.lv_snd = 17; }
}
else if (st == 2)
{
    e_t += 1;
    t = e_t;
    if (t == 5) e_pic = 16;
    else if (t == 10) e_pic = 17;
    else if (t == 15) e_pic = 18;
    else if (t == 24) { e_pic = 20; e_yv = -48; }       // a little hop
    else if (t == 33) { e_state = 4; e_n = 0; }
}
else if (st == 3)
{
    // walks 1 pixel a frame; at a wall or at the end of the floor it jumps
    scr_en_move_x();
    t = scr_en_wall();
    if (!t) t = !scr_en_floor();
    if (t) { e_pic = 20; e_yv = -64; e_state = 4; }
    else
    {
        e_t += 1;
        if (e_t == 8) { e_t = 0; e_n = (e_n + 1) mod 4; e_pic = g.en_cwalk[e_n]; }
    }
}
if (st == 4)
{
    if (scr_en_air())
    {
        if (e_xv == 0)                                  // after the hop: off it goes, the way it looks
        {
            if (e_face == 1) e_xv = 16; else e_xv = -16;
            e_n = 0; e_pic = 19;
        }
        else { e_n = (e_n + 1) mod 4; e_pic = g.en_cwalk[e_n]; }
        e_state = 3; e_t = 0;
    }
}

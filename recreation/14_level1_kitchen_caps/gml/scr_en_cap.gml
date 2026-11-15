/// scr_en_cap(state)
// Called by obj_enemy (User Defined 0) for a bottle cap (e_kind 7). The caps sit on the three bottles of the
// kitchen's last screens. A cap is solid for the player (scr_pl_solid_at): he stands on it and cannot walk or
// jump through it. Nothing else touches it: crates and thrown mice fly through it.
// Every landing on it presses it down a step (pictures 80, 81, 82; heights 7, 4, 2); with the third landing it
// flies off (picture 83, height 15): 1 pixel to the right every frame, up at 4 pixels a frame, 3/16 of a pixel
// less each frame until it falls at 5 pixels a frame. It leaves the picture at the bottom and is gone.
// e_state  0: the player has to be off it first, 1: waiting for him to land, 2: flying
// e_n      1: he stood on it when the cap last looked. It looks after the player's move (it comes after him in
//          the object list), on every frame but the one it flies off on.
// So a landing is noticed one frame later; the player is then put down with the cap (or up, with the third).
// While it flies the player on it is put on its top BEFORE it moves, so he is always one frame behind it: when
// it rises he is inside it and stays on; as soon as it sinks a whole pixel in a frame it has left him, and he
// falls. He falls faster than it does, so he can catch up and land on it again. It does not carry him sideways:
// to stay on it he has to walk along.
var st = argument0;
var g = stage;
var pl = g.pl;
var on = 0;
if (pl.p_on == id) on = 1;
if (st == -1)
{
    e_wx += 8;              // the list has the bottle's column; the cap is in the middle of it
    e_pic = 80; e_w = 8; e_h = 7;
    e_hide = false;
    e_state = 0; e_n = 0;
}
else if (st == 2)
{
    if (e_yv < 80) e_yv += 3;
    e_n = on;
    if (on) { pl.p_late = pl.p_y - (e_y - 16); pl.p_y = e_y - 16; scr_en_cap_carry(); }
    e_wx += 1;
    scr_en_move_y();
}
else
{
    if (st == 0)
    {
        if (e_n == 0) e_state = 1;
    }
    else if (e_n != 0)
    {
        // a landing: a step down, and the player with it
        e_pic += 1;
        e_h = g.en_cap_h[e_pic - 80];
        e_state = 0;
        pl.p_late = pl.p_y - (e_y - e_h - 1);       // (the picture shows it a frame later: see obj_stage1 End Step)
        pl.p_y = e_y - e_h - 1;
        scr_en_cap_carry();
        if (e_pic == 83)
        {
            // the third: it flies off (and does not look on this frame)
            g.lv_snd = 18;
            e_yv = -64;
            e_state = 2;
            e_wx += 1;
            scr_en_move_y();
            exit;
        }
    }
    e_n = on;
}

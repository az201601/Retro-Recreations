/// scr_en_crate_ahead(reach)
// Called by obj_enemy (the mouse with the spoon). Looks for a thrown crate that comes at its face, less than
// `reach` pixels away and on its level. Returns the obj_crate, or noone.
// (A crate thrown on this frame whose turn is still to come has no direction yet: it counts as not coming.)
var j, c, dx, dy, cd;
for (j = 11; j >= 3; j -= 1)
{
    if (stage.lv_slot_k[j] != 1) continue;
    c = stage.lv_slot[j];
    if (!c.c_hot || c.c_mode == 5) continue;
    dx = e_wx - c.c_wx;
    dy = e_y - c.c_y;
    if (c.c_mode == 2 || c.c_t == 0) cd = 0; else cd = c.c_dir;
    if (dx >= 0)
    {
        if (e_face == 1 || cd < 0 || dx >= argument0) continue;
    }
    else if (e_face == 0 || cd >= 0 || -dx > argument0) continue;
    if ((dy >= 0 && dy < e_h) || (dy < 0 && -dy <= 15)) return c;
}
return noone;

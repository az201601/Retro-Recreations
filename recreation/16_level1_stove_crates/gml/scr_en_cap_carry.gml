/// scr_en_cap_carry()
// Called by scr_en_cap (so by a bottle cap) right after it has moved the player up or down.
// What he carries (a crate, a stunned mouse) takes its place over his head on its own turn in the object
// list: if that turn comes after the cap's, it goes with him on this same frame; if it was before, it
// follows on the next frame (the player's own step puts it there).
// (Measured with a crate, in both orders. A carried mouse on a cap was not seen; it uses the same rule.)
var pl = stage.pl;
var c = pl.p_carry;
if (c == noone) exit;
if (pl.p_h == 0) exit;
if (c.object_index == obj_enemy)
{
    if (c.e_slot > e_slot && c.e_n != 0) c.e_y = pl.p_y - pl.p_h - 1;
}
else
{
    if (c.c_slot > e_slot) c.c_y = pl.p_y - pl.p_h - 1;
}

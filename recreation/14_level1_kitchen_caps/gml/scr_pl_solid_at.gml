/// scr_pl_solid_at(dy)
// Called by obj_player. The solid thing the player is in, with his feet line moved down by dy pixels (0, or 1 to
// ask what is under his feet). Returns the instance, or noone.
// Solid things are the bottle caps (e_kind 7) and a stunned mouse with a spoon (e_kind 5): lying on the ground
// (state 6), and also while it is still in the air from the crate's hit (state 5).
// He is in one if his middle is at most 6 + its half width from its middle (14 pixels for both) and his feet line
// is anywhere from its height above its line (so 1 above that he stands on it) down to his own body height below
// it (22 standing, 16 crouching). The object list is searched from its last place down; the first one found counts.
// A player without hearts is in nothing.
// Uses where the player was before this frame's step sideways, and where the thing was after the frame before.
var j, e, d;
if (p_hp == 0) return noone;
for (j = 11; j >= 3; j -= 1)
{
    if (stage.lv_slot_k[j] != 2) continue;
    e = stage.lv_slot[j];
    if (e.e_hide || e.e_gone) continue;
    if (e.e_kind != 7 && !(e.e_kind == 5 && (e.e_state == 5 || e.e_state == 6))) continue;
    if (abs(e.e_wx - stage.lv_cam_x - p_x) > 6 + e.e_w) continue;
    d = p_y + argument0 - e.e_y;
    if (d >= -e.e_h && d <= p_h) return e;
}
return noone;

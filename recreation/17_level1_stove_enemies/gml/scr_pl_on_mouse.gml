/// scr_pl_on_mouse()
// Called by obj_player. A solid thing (a bottle cap, a stunned mouse: see scr_pl_solid_at) carries the player
// like a block. True if it is under his feet or he is in it; he is then put on top of it (his feet line 1 above
// its top: 25 above a mouse's line, 8 / 5 / 3 above a cap's as it is pressed down, 16 above a flying cap's).
// The fraction of his height stays. p_on remembers what he stands on for the rest of this frame (the cap asks).
var e = scr_pl_solid_at(1);
if (e == noone) return false;
p_y = e.e_y - e.e_h - 1;
p_on = e;
return true;

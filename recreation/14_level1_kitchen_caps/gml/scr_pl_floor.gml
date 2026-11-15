/// scr_pl_floor()
// Called by obj_player. Is the player standing on something?
// Only true when the feet are exactly on the top edge of a block row - or when a stunned mouse carries the player.
if (scr_pl_on_mouse()) { p_yv = 0; return true; }
if (p_y < 0 || p_y > 255) return false;
if (((p_y + stage.lv_cam_y) mod 16) != 0) return false;
if (!scr_pl_row(p_y, 1)) return false;
p_ysub = 0;
p_yv = 0;
return true;

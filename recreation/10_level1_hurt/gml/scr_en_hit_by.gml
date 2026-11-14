/// scr_en_hit_by(crate)
// Called by obj_enemy: true if the crate touches it. The crate's box is 6 wide to either side and 15 high.
// Positions are compared on the screen; a flying crate that had its turn before the enemy on this frame is
// placed with this frame's camera position, everything else with the one before.
var c = argument0;
var cx;
if (c.c_mode != 0 && c.c_slot < e_slot) cx = c.c_wx - stage.lv_cam_x;
else cx = c.c_wx - stage.lv_cam_show;
var dx = e_wx - stage.lv_cam_show - cx;
var dy = e_y - c.c_y;
return (abs(dx) <= e_w + 6 && dy >= -15 && dy <= e_h);

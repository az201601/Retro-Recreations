/// scr_pl_pick(pressed)
// Called by obj_player when it walked into the solid block (p_wc, p_wr).
// B newly pressed, nothing carried, not throwing, not crouching, and the block is a crate: pick it up.
if ((argument0 & 32) == 0 || p_carry != noone || p_throw != 0 || p_h == 16) return false;
var k = stage.lv_box[p_wr, p_wc];
if (k != 1 && k != 2) return false;
if (k == 2) scr_pl_open_box(p_wc, p_wr, 3);     // a crate with a bonus leaves the bonus box behind
else scr_pl_open_box(p_wc, p_wr, 0);

// from now on the crate is an object. It appears on the head at once.
var cr = instance_create(0, 0, obj_crate);
cr.stage = stage;
cr.c_wx = p_x + stage.lv_cam_x;
cr.c_y = p_y - 23;
cr.s_x = p_x;
cr.s_y = cr.c_y;
stage.lv_cr[stage.lv_cr_n] = cr;
stage.lv_cr_n += 1;
p_carry = cr;
p_snd = 1;
return true;

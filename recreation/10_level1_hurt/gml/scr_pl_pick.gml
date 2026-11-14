/// scr_pl_pick(pressed)
// Called by obj_player when it walked into the solid block (p_wc, p_wr).
// B newly pressed, nothing carried, not throwing, not crouching, and the block is a crate: pick it up.
if ((argument0 & 32) == 0 || p_carry != noone || p_throw != 0 || p_h == 16) return false;
var k = stage.lv_box[p_wr, p_wc];
if (k != 1 && k != 2) return false;
// from now on the crate is an object. It appears on the head at once.
// It takes the lowest free place in the stage's object list (if all 9 are taken it cannot be picked up: not measured).
var j;
with (stage) j = scr_lv_take_slot();
if (j < 0) return false;
if (k == 2) scr_pl_open_box(p_wc, p_wr, 3);     // a crate with a bonus leaves the bonus box behind
else scr_pl_open_box(p_wc, p_wr, 0);
var cr = instance_create(0, 0, obj_crate);
cr.stage = stage;
cr.c_slot = j;
stage.lv_slot[j] = cr;
stage.lv_slot_k[j] = 1;
cr.c_wx = p_x + stage.lv_cam_x;
cr.c_y = p_y - 23;
cr.s_x = p_x;
cr.s_y = cr.c_y;
stage.lv_cr[stage.lv_cr_n] = cr;
stage.lv_cr_n += 1;
p_carry = cr;
p_snd = 1;
return true;

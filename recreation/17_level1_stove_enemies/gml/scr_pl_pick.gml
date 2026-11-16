/// scr_pl_pick(pressed)
// Called by obj_player when it walked into the solid block (p_wc, p_wr).
// B newly pressed, nothing carried, not throwing, not crouching, and the block is a crate: pick it up.
if ((argument0 & 32) == 0 || p_carry != noone || p_throw != 0 || p_h == 16) return false;
var k = stage.lv_box[p_wr, p_wc];
if (k != 1 && k != 2 && k != 4) return false;
// From now on the crate is an object, and it appears on the head at once. The block is emptied first, whatever
// follows: if all 9 places of the stage's object list are taken, the crate is simply gone - nothing is carried
// and there is no sound.
var j;
if (k == 4)
{
    // The crate with the item inside: the item (an acorn) is left where the crate was. It takes its place in the
    // object list before the crate does. With one free place the item is there and nothing is carried; with none
    // there is no item either.
    scr_pl_open_box(p_wc, p_wr, 0);
    with (stage) j = scr_lv_take_slot();
    if (j >= 0)
    {
        var it = instance_create(0, 0, obj_item);
        it.stage = stage;
        it.i_kind = 0;
        it.e_wx = p_wc * 16 + 8;
        it.e_y = p_wr * 16 + 15 - stage.lv_cam_y;
        it.e_slot = j;
        stage.lv_slot[j] = it;
        stage.lv_slot_k[j] = 5;
        stage.lv_it[stage.lv_it_n] = it;
        stage.lv_it_n += 1;
    }
}
else if (k == 2) scr_pl_open_box(p_wc, p_wr, 3);     // a crate with a bonus leaves the bonus box behind
else scr_pl_open_box(p_wc, p_wr, 0);
with (stage) j = scr_lv_take_slot();
if (j < 0) return false;
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

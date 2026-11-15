/// scr_lv_spawn2(entry, camera y)
// Called by obj_stage1: entry i of the kitchen's object list (lv_ob2_*) enters.
var i = argument0;
var k = lv_ob2_k[i];
var wx = lv_ob2_c[i] * 16;
var yy = lv_ob2_r[i] * 16 - argument1;
var j, en;
if (k == 15 || k == 16) scr_lv_spawn(k - 10, wx, yy, 0);       // the mice
else
{
    j = scr_lv_take_slot();
    if (j < 0) return 0;
    if (k == 9) lv_slot_k[j] = 3;           // the exit (see lv_trig_on) only takes a place in the object list
    else if (k == 17)
    {
        // a bottle cap: in this step it only takes its place, until it has been on the screen and left it
        lv_slot_k[j] = 6;
        lv_cap_x[j] = wx + 8;
        lv_cap_seen[j] = false;
    }
    else
    {
        // the star that gives a life
        en = instance_create(0, 0, obj_item);
        en.stage = id;
        en.i_kind = 1;
        en.e_wx = wx;
        en.e_y = yy;
        en.e_slot = j;
        lv_slot[j] = en;
        lv_slot_k[j] = 5;
        lv_it[lv_it_n] = en;
        lv_it_n += 1;
    }
}

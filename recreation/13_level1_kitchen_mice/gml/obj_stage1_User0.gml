/// obj_stage1 : User Defined 0   (puts all crates and bonus boxes back, removes all enemies; run by Create and at every restart)
var r, c, i;
// (the block map of the section that is being played: lv_sec)
if (lv_sec == 0) lv_rows = 15; else lv_rows = 30;
for (r = 0; r < 30; r += 1)
{
    for (c = 0; c < 128; c += 1)
    {
        // 0 nothing, 1 can be stood on, 2 solid
        if (lv_sec == 1) lv_kind[r, c] = real(string_char_at(lv_map2[r], c + 1));
        else if (r < 15) lv_kind[r, c] = real(string_char_at(lv_map[r], c + 1));
        else lv_kind[r, c] = 0;
        lv_box[r, c] = 0;                   // 0 none, 1 crate, 2 crate with a bonus, 3 bonus box, 4 crate with the item
        lv_bi[r, c] = -1;                                           // its entry in the box table
    }
}
for (i = 0; i < lv_box_n && lv_sec == 0; i += 1)
{
    lv_box[lv_br[i], lv_bc[i]] = lv_bk[i];
    lv_bi[lv_br[i], lv_bc[i]] = i;
}
for (i = 0; i < lv_box2_n && lv_sec == 1; i += 1)      // the kitchen has its own table
{
    lv_box[lv_br2[i], lv_bc2[i]] = lv_bk2[i];
    lv_bi[lv_br2[i], lv_bc2[i]] = i;
}
lv_open_n = 0;         // boxes that are gone or changed: lv_open_i (entry), lv_open_t (lt when), lv_open_k (true: now a bonus box)
with (obj_crate) instance_destroy();
lv_cr_n = 0;           // the obj_crate instances, oldest first: lv_cr[0 .. lv_cr_n - 1]
with (obj_enemy) instance_destroy();
lv_en_n = 0;           // the obj_enemy instances, oldest first: lv_en[0 .. lv_en_n - 1]
with (obj_item) instance_destroy();
lv_it_n = 0;           // the obj_item instances (the acorn, the star, the sign "1UP")
// the object list: places 3..11. lv_slot_k: 0 free, 1 crate, 2 enemy, 3 the exit, 4 the star of a stunned player or mouse, 5 item,
// 6 bottle cap; lv_slot: the instance
for (i = 0; i < 12; i += 1) { lv_slot[i] = noone; lv_slot_k[i] = 0; }
lv_sp_i = 0;           // the next entry of lv_ob_* to enter
lv_sp_col = 16;        // the column 264 pixels right of the camera on the previous frame
lv_snd = 0;
lv_star = 0;           // no star
lv_dy = 0;
for (i = 0; i < 12; i += 1) { lv_cap_x[i] = 0; lv_cap_seen[i] = false; }      // bottle caps: see lv_slot_k 6
// the kitchen's first screen: what the object list has up to column 16 is there from the start
if (lv_sec == 1)
{
    while (lv_sp_i < lv_ob2_n)
    {
        if (lv_ob2_c[lv_sp_i] > 16) break;
        scr_lv_spawn2(lv_sp_i, 240);
        lv_sp_i += 1;
    }
}

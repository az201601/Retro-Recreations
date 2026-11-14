/// obj_stage1 : User Defined 0   (puts all crates and bonus boxes back; run by Create and at every restart)
var r, c, i;
for (r = 0; r < 15; r += 1)
{
    for (c = 0; c < 128; c += 1)
    {
        lv_kind[r, c] = real(string_char_at(lv_map[r], c + 1));     // 0 nothing, 1 can be stood on, 2 solid
        lv_box[r, c] = 0;                                           // 0 none, 1 crate, 2 crate with a bonus, 3 bonus box
        lv_bi[r, c] = -1;                                           // its entry in the box table
    }
}
for (i = 0; i < lv_box_n; i += 1)
{
    lv_box[lv_br[i], lv_bc[i]] = lv_bk[i];
    lv_bi[lv_br[i], lv_bc[i]] = i;
}
lv_open_n = 0;         // boxes that are gone or changed: lv_open_i (entry), lv_open_t (lt when), lv_open_k (true: now a bonus box)
with (obj_crate) instance_destroy();
lv_cr_n = 0;           // the obj_crate instances, oldest first: lv_cr[0 .. lv_cr_n - 1]

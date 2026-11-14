/// scr_lv_take_slot()
// Called by obj_stage1 (or "with (stage)"). The object list has the places 3..11 (0-2 are the players and the
// hearts); crates and enemies act and are drawn in the order of their places.
// Returns the lowest free place, or -1 if all are taken (never seen in the recordings). The caller fills in
// lv_slot[j] (the instance) and lv_slot_k[j] (1 crate, 2 enemy, 3 the exit).
var j;
for (j = 3; j < 12; j += 1)
{
    if (lv_slot_k[j] == 0) return j;
}
return -1;

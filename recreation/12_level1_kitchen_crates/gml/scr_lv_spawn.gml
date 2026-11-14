/// scr_lv_spawn(kind, wx, y, face)
// Called by obj_stage1 (or "with (stage)"). Creates an enemy (1 flyer, 2 what it drops, 3 cook, 4 fork) at the
// position (wx in the section, y on the screen) and gives it the lowest free place in the object list.
// Returns the instance, or noone if the list is full.
var j = scr_lv_take_slot();
if (j < 0) return noone;
var e = instance_create(0, 0, obj_enemy);
e.stage = id;
e.e_kind = argument0;
e.e_wx = argument1;
e.e_y = argument2;
e.e_face = argument3;
e.e_slot = j;
lv_slot[j] = e;
lv_slot_k[j] = 2;
lv_en[lv_en_n] = e;
lv_en_n += 1;
return e;

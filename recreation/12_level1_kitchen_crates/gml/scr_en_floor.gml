/// scr_en_floor()
// Called by obj_enemy: true if its feet are in a block that can be stood on; it is put on top of it.
if (e_y < 0 || e_y > 255) return false;
if (!scr_en_row(e_y, 1)) return false;
e_y = (e_y div 16) * 16;
e_ys = 0;
return true;

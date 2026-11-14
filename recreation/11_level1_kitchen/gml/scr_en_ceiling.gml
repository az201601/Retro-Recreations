/// scr_en_ceiling()
// Called by obj_enemy: true if its head is in a solid block; it is put below it.
if (e_y < e_h || e_y > 255) return false;
if (!scr_en_row(e_y - e_h, 2)) return false;
e_y = ((e_y - e_h) div 16) * 16 + 16 + e_h;
return true;

/// scr_en_next_pic()
// Called by obj_enemy (the mouse with the spoon): the next of its four walking pictures (0, 1, 2, 1); after the
// fourth it turns round. Each is shown for 8 steps. The count of the steps goes on over a swing of the spoon,
// so the walk after one is shorter.
e_i = (e_i + 1) mod 4;
if (e_i == 0) e_pic = 0; else if (e_i == 2) e_pic = 2; else e_pic = 1;
if (e_i == 0) { e_face = 1 - e_face; e_xv = -e_xv; }

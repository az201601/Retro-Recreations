/// obj_item : User Defined 0   (one NES frame; run by obj_stage1 in the order of the object list)
// The acorn and the star lie still. The sign "1UP" rises a pixel on every 4th frame, 15 times, and is gone 85
// frames after the star was taken.
if (i_kind != 2) exit;
i_t += 1;
if ((i_t mod 4) == 0 && i_t > 0 && i_t <= 60) e_y -= 1;
if (i_t == 85) { e_gone = true; stage.lv_slot_k[e_slot] = 0; }

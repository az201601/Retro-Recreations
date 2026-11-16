/// scr_en_move_y()
// Called by obj_enemy: moves by e_yv sixteenths of a pixel.
var t = e_y * 16 + e_ys + e_yv;
e_y = floor(t / 16);
e_ys = t - e_y * 16;

/// scr_en_move_x()
// Called by obj_enemy: moves by e_xv sixteenths of a pixel.
var t = e_wx * 16 + e_xs + e_xv;
e_wx = floor(t / 16);
e_xs = t - e_wx * 16;

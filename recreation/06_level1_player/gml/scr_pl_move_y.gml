/// scr_pl_move_y()
// Called by obj_player. Moves the player up or down by p_yv sixteenths of a pixel.
var t = p_y * 16 + p_ysub + p_yv;
p_y = floor(t / 16);
p_ysub = t - p_y * 16;

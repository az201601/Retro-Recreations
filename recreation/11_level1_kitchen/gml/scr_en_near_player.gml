/// scr_en_near_player()
// Called by obj_enemy (the cook): true if the player is on its level and less than 80 pixels away.
// (The distance is counted in one byte, as in the original.)
var p = stage.pl;
var dy = e_y - p.p_y;
if (dy >= e_h || dy < -p.p_h) return false;
var d = e_wx - stage.lv_cam_show - p.p_x;
var v = ((d mod 256) + 256) mod 256;
if (d < 0) v = (256 - v) mod 256;
return (v < 80);

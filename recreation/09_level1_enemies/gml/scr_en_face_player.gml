/// scr_en_face_player()
// Called by obj_enemy: turns towards the player (off the screen: towards the screen).
var sx = e_wx - stage.lv_cam_show;
if (sx < 0) e_face = 1;
else if (sx > 255) e_face = 0;
else if (stage.pl.p_x >= sx) e_face = 1;
else e_face = 0;

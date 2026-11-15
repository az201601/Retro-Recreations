/// scr_en_air()
// Called by obj_enemy (the mice): one frame in the air. Returns true when it lands.
// Gravity 3/16 pixel per frame, up to 5 pixels a frame. The floor is only looked for on a frame on which the feet
// come into another row of blocks.
scr_en_move_x();
scr_en_wall();
if (e_yv < 80) e_yv += 3;
if (e_yv < 0)
{
    scr_en_move_y();
    if (scr_en_ceiling()) e_yv = 1;
}
else
{
    var y0 = e_y;
    var cy = stage.lv_cam_y;
    scr_en_move_y();
    if (((e_y + cy) & 255) div 16 != ((y0 + cy) & 255) div 16)
    {
        if (scr_en_floor()) { e_yv = 0; return true; }
    }
}
return false;

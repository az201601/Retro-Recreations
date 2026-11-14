/// obj_crate : User Defined 1   (draws the crate; run by obj_stage1's Draw event)
// On the NES the crate is four 8x8 sprites. One that starts above the top of the screen, or left / right
// of it, is not shown at all, so the four quarters are drawn one by one.
// spr_crate: sub-image = (0 normal, 1 flash) * 7 + brightness.
// The eyes of a hiding player are a fifth sprite (spr_crate_eyes: sub-image = brightness). The NES lists its
// sprites forwards on one frame and backwards on the next, so the eyes are in front of the crate on odd
// frames and behind it (not to be seen) on even frames: they flicker, as in the original.
if (s_vis)
{
    var q, tx, ty;
    var ex = s_x - 6;                           // eyes to the left
    if (s_eyes == 2) ex = s_x - 2;              // eyes to the right
    var ey = s_y - 12;
    var eshow = (s_eyes != 0 && ey >= 0 && ex >= 0 && ex <= 255);
    if (eshow && (stage.lv_fc & 1) == 0) draw_sprite(spr_crate_eyes, stage.lv_bright, ex, ey + 1);     // behind the crate
    for (q = 0; q < 4; q += 1)                  // top left, bottom left, top right, bottom right
    {
        tx = s_x - 8 + (q div 2) * 8;
        ty = s_y - 17 + (q mod 2) * 8;
        if (ty >= 0 && tx >= 0 && tx <= 255)
        {
            draw_sprite_part(spr_crate, s_flash * 7 + stage.lv_bright, (q div 2) * 8, (q mod 2) * 8, 8, 8, tx, ty + 1);
        }
    }
    if (eshow && (stage.lv_fc & 1) != 0) draw_sprite(spr_crate_eyes, stage.lv_bright, ex, ey + 1);     // in front of the crate
}

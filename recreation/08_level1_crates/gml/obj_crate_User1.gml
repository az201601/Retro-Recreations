/// obj_crate : User Defined 1   (draws the crate; run by obj_stage1's Draw event)
// On the NES the crate is four 8x8 sprites. One that starts above the top of the screen, or left / right
// of it, is not shown at all, so the four quarters are drawn one by one.
// spr_crate: sub-image = (0 normal, 1 flash) * 7 + brightness.
if (s_vis)
{
    var q, tx, ty;
    for (q = 0; q < 4; q += 1)                  // top left, bottom left, top right, bottom right
    {
        tx = s_x - 8 + (q div 2) * 8;
        ty = s_y - 17 + (q mod 2) * 8;
        if (ty >= 0 && tx >= 0 && tx <= 255)
        {
            draw_sprite_part(spr_crate, s_flash * 7 + stage.lv_bright, (q div 2) * 8, (q mod 2) * 8, 8, 8, tx, ty + 1);
        }
    }
}

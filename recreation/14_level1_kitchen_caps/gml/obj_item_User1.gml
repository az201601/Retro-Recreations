/// obj_item : User Defined 1   (draws the item; run by obj_stage1's Draw event)
// On the NES the acorn and the star are four 8x8 sprites, the sign two. One that starts above the top of the
// screen, or left / right of it, is not shown at all, so the pieces are drawn one by one.
// spr_item, spr_lifestar (16x16) and spr_1up (16x8): sub-image = brightness.
if (s_vis)
{
    var q, tx, ty;
    if (s_kind == 2)
    {
        for (q = 0; q < 2; q += 1)
        {
            tx = s_x - 8 + q * 8;
            ty = s_y - 8;
            if (ty >= 0 && tx >= 0 && tx <= 255) draw_sprite_part(spr_1up, stage.lv_bright, q * 8, 0, 8, 8, tx, ty + 1);
        }
    }
    else
    {
        var sp = spr_item;
        if (s_kind == 1) sp = spr_lifestar;
        for (q = 0; q < 4; q += 1)                  // top left, bottom left, top right, bottom right
        {
            tx = s_x - 8 + (q div 2) * 8;
            ty = s_y - 16 + (q mod 2) * 8;
            if (ty >= 0 && tx >= 0 && tx <= 255) draw_sprite_part(sp, stage.lv_bright, (q div 2) * 8, (q mod 2) * 8, 8, 8, tx, ty + 1);
        }
    }
}

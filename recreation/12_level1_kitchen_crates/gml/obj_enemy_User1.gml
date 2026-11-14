/// obj_enemy : User Defined 1   (draws the enemy; run by obj_stage1's Draw event)
// Shows the state after the previous frame (s_ variables), like the NES. The picture is made of 8x8 tiles
// (tables en_t* in obj_stage1 Create, stored facing left). A tile that starts above the top of the screen, or
// left / right of it, is not drawn at all. stage.lv_ord == 0: the tiles are drawn in the opposite order.
// (The NES shows at most 8 sprites on a picture line and leaves the rest out; this draws them all.)
if (s_vis)
{
    var b = stage.lv_bright;
    var n = stage.en_tn[s_pic];
    var j, i, tx, ty;
    for (j = 0; j < n; j += 1)
    {
        if (stage.lv_ord == 0) i = n - 1 - j; else i = j;
        if (s_face == 1) tx = s_x - stage.en_tdx[s_pic, i] - 8; else tx = s_x + stage.en_tdx[s_pic, i];
        ty = s_y + stage.en_tdy[s_pic, i];
        if (ty >= 0 && tx >= 0 && tx <= 255)
        {
            draw_sprite(spr_enemy, (stage.en_tim[s_pic, i] * 2 + s_face) * 7 + b, tx, ty + 1);
        }
    }
}

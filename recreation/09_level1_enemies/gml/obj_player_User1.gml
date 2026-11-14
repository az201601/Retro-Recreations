/// obj_player : User Defined 1   (draws the player; run by obj_stage1's Draw event, which sets p_rev)
// Shows the state after the previous frame (s_ variables), like the NES.
// The picture is made of 8x8 tiles. A tile that starts above the top of the screen, or left / right of
// it, is not drawn at all (the NES cannot show it).
// p_rev: the tiles are drawn in the opposite order (which tile covers which changes every frame).
var b = stage.lv_bright;                        // 0..2 fade-in, 3 normal, 4..6 fade-out
if (s_vis)
{
    var n = p_tn[s_pic];
    var j, i, tx, ty;
    for (j = 0; j < n; j += 1)
    {
        if (p_rev) i = n - 1 - j; else i = j;
        if (s_face == 1) tx = s_x + p_tdx[s_pic, i]; else tx = s_x - p_tdx[s_pic, i] - 8;
        ty = s_y + p_tdy[s_pic, i];
        if (ty >= 0 && tx >= 0 && tx <= 255)
        {
            draw_sprite(p_spr, (p_tim[s_pic, i] * 2 + (1 - s_face)) * 7 + b, tx, ty + 1);
        }
    }
}

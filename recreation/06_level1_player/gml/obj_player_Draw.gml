/// obj_player : Draw
// Shows the state after the previous frame (s_ variables), like the NES.
// The picture is made of 8x8 tiles. A tile that starts above the top of the screen, or left / right of
// it, is not drawn at all (the NES cannot show it).
var b = stage.lv_bright;                        // 0..2 fade-in, 3 normal, 4..6 fade-out, -1 black
if (b >= 0 && s_vis)
{
    var i, tx, ty;
    for (i = 0; i < p_tn[s_pic]; i += 1)
    {
        if (s_face == 1) tx = s_x + p_tdx[s_pic, i]; else tx = s_x - p_tdx[s_pic, i] - 8;
        ty = s_y + p_tdy[s_pic, i];
        if (ty >= 0 && tx >= 0 && tx <= 255)
        {
            draw_sprite(spr_chip, (p_tim[s_pic, i] * 2 + (1 - s_face)) * 7 + b, tx, ty + 1);
        }
    }
    // the NES shows nothing in the left-most 8 pixels of this level, sprites included
    draw_set_color(c_black);
    draw_rectangle(0, 0, 7, 239, false);
    draw_set_color(c_white);
}

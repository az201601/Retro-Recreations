/// obj_title - Draw
// ============================================================================
if (spr_title >= 0) {
    draw_sprite_ext(spr_title, 0, 0, 0, 1, 1, 0, c_white, alpha);
}

// "PRESS START" hint, blinking once every 40 steps
if ((blink div 20) mod 2 == 0) {
    draw_set_colour(c_white);
    draw_set_halign(fa_center);
    draw_set_valign(fa_bottom);
    draw_set_font(-1);
    draw_text(room_width / 2, room_height - 12, "PRESS ENTER");
    draw_set_halign(fa_left);
    draw_set_valign(fa_top);
}

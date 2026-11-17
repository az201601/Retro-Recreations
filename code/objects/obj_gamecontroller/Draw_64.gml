/// obj_gamecontroller - Draw GUI
// Pause overlay.  Depth -10000 so it draws over the HUD.
// ============================================================================
if (global.game_state != "pause") exit;

draw_set_alpha(0.55);
draw_set_colour(c_black);
draw_rectangle(0, 0, room_width, room_height, false);
draw_set_alpha(1);

draw_set_colour(c_white);
draw_set_halign(fa_center);
draw_set_valign(fa_middle);
draw_set_font(-1);
draw_text(room_width / 2, room_height / 2, "PAUSED");

draw_set_halign(fa_left);
draw_set_valign(fa_top);

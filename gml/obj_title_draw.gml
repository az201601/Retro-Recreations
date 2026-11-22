// obj_title -- Draw event
// The NES title screen shows blinking text under the logo; approximate it.
draw_background(bg_title, 0, 0);
if ((blink div 30) mod 2 == 0) {
    draw_set_color(c_white);
    draw_set_halign(fa_center);
    draw_text(128, 200, "PRESS START");
    draw_set_halign(fa_left);
}

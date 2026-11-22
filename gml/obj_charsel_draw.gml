// obj_charsel -- Draw event
draw_background(bg_charsel, 0, 0);
// selection marker: the NES shows a small cursor beside the chosen chipmunk
draw_set_color(c_yellow);
if (choice == 0) draw_triangle(104, 226, 104, 238, 116, 232, false);
else draw_triangle(168, 226, 168, 238, 180, 232, false);

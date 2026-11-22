// obj_level -- Draw event
// Draws the extracted NES stage screen(s).
// screen_00.png = the kitchen start area (256x240, pixel-exact NES render).
// Each later screen sits at x = 256 * n from panorama.json.
var i;
for (i = 0; i < global.screens; i += 1) {
    draw_sprite(bg_stage, i, 256 * i, 0);
}
// If you imported a single background instead, use:
//   draw_background(bg_stage_start, 0, 0);

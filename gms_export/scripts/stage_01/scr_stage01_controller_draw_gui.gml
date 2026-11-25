/// scr_stage01_controller_draw_gui() | functional stand-in HUD (not NES HUD art)
var i, label;
draw_set_color(c_black);
draw_rectangle(0, 208, 255, 239, false);
draw_set_color(c_white);
label = "RR " + string(global.rre_count) + "   LIVES " + string(global.stage01_lives);
draw_text(5, 210, label);
draw_text(5, 223, "HP");
if (instance_exists(obj_player)) {
    for (i = 0; i < obj_player.hp; i += 1) {
        draw_set_color(c_red);
        draw_rectangle(27 + i * 12, 227, 34 + i * 12, 234, false);
    }
}
draw_set_color(c_white);
if (global.stage01_part == 2) {
    if (global.stage01_sink_fill >= 100) draw_text(100, 222, "SINK FULL - EXIT");
    else if (global.stage01_sink_active) draw_text(100, 222, "SINK " + string(floor(global.stage01_sink_fill)) + "%");
    else draw_text(100, 222, "X AT THE VALVE");
}
if (global.stage01_part == 3) {
    draw_text(16, 48, "MONTEREY JACK");
    draw_text(16, 63, "HEALTH RESTORED");
    draw_text(16, 78, "X TO CONTINUE");
}
if (global.stage01_part == 4 && instance_exists(obj_boss_water_rabbit)) {
    draw_text(134, 222, "RABBIT " + string(max(0, obj_boss_water_rabbit.hp)));
}
if (global.stage01_clear || global.stage01_game_over) {
    draw_set_color(c_black);
    draw_rectangle(10, 68, 246, 144, false);
    draw_set_color(c_white);
    if (global.stage01_clear) draw_text(76, 84, "STAGE 01 CLEAR");
    else draw_text(88, 84, "GAME OVER");
    draw_text(70, 110, "PRESS R TO RESTART");
}
draw_set_color(c_white);

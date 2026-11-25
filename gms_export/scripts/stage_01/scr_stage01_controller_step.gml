/// scr_stage01_controller_step() | scrolling, sink, refill, boss-clear phases
var player_x, player_y;
if (!instance_exists(obj_player)) exit;
player_x = obj_player.x;
player_y = obj_player.y;
if (global.stage01_part == 2 && global.stage01_sink_active) {
    global.stage01_sink_fill = min(100, global.stage01_sink_fill + 0.6);
}
if (global.stage01_part == 3) {
    refill_timer += 1;
    if (refill_timer == 90) obj_player.hp = 3;
    if (refill_timer >= 260 || (refill_timer >= 100 && keyboard_check_pressed(ord("X")))) {
        scr_stage01_enter(4);
    }
}
if (global.stage01_part == 4 && instance_exists(obj_boss_water_rabbit)) {
    if (obj_boss_water_rabbit.hp <= 0) {
        global.stage01_part = 5;
        global.stage01_clear = true;
        clear_timer = 0;
        // The captured clear WAV includes gameplay SFX; do not mislabel or
        // auto-play it as an isolated victory jingle.
    }
}
if (global.stage01_part == 5) clear_timer += 1;
switch (global.stage01_part) {
    case 0:
        view_xview[0] = clamp(player_x - 128, 0, 1792);
        view_yview[0] = 512;
        break;
    case 1:
        view_xview[0] = clamp(player_x - 128, 0, 1792);
        view_yview[0] = clamp(player_y - 192, 1536, 1792);
        break;
    case 2:
        view_xview[0] = clamp(player_x - 128, 0, 1536);
        view_yview[0] = 1280;
        break;
    case 3:
        view_xview[0] = 0;
        view_yview[0] = 1024;
        break;
    default:
        view_xview[0] = 1024;
        view_yview[0] = 256;
}
if (global.stage01_game_over && keyboard_check_pressed(ord("R"))) room_restart();
if (global.stage01_clear && keyboard_check_pressed(ord("R"))) room_restart();

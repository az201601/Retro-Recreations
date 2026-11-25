/// scr_stage01_enemy_step() | provisional room-gated patrol/bee/fake-crate AI
var active, speed;
if (hp <= 0) { instance_destroy(); exit; }
active = false;
if (global.stage01_part == 0 && home_y >= 512 && home_y < 768) active = true;
if (global.stage01_part == 1 && home_y >= 1536 && home_y < 2048) active = true;
if (global.stage01_part == 2 && home_y >= 1280 && home_y < 1536) active = true;
visible = active;
if (!active || global.stage01_game_over) exit;
timer += 1;
if (object_index == obj_enemy_honeybee) {
    x = home_x + sin(timer * 0.036) * 40;
    y = home_y + sin(timer * 0.07) * 11;
    exit;
}
if (object_index == obj_enemy_bottle_cork) {
    x = home_x + sin(timer * 0.06) * 22;
    exit;
}
speed = 0.65;
if (object_index == obj_enemy_fake_box) {
    speed = 0;
    if (instance_exists(obj_player) && abs(obj_player.x - x) < 72) speed = 1.25;
}
x += speed * dir;
if (x < home_x - 32 || x > home_x + 32) dir = -dir;
image_xscale = -dir;

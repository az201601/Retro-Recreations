/// scr_stage01_boss_step() | provisional three-level Water Rabbit pattern
var box;
if (global.stage01_part != 4 || hp <= 0 || global.stage01_game_over) {
    visible = false;
    exit;
}
visible = true;
timer += 1;
if (hit_cooldown > 0) hit_cooldown -= 1;
if (flash > 0) flash -= 1;
image_blend = c_white;
if (flash > 0 && (flash mod 4) < 2) image_blend = c_red;
x = 1144 + sin(timer * 0.021) * 90;
y = 320 + (floor(timer / 170) mod 3) * 64;
if (timer mod 115 == 1) {
    box = instance_create(1040 + irandom(25) * 8, 260, obj_boss_box);
    box.is_boss = true;
    box.falling = true;
    box.vy = 0.4;
}

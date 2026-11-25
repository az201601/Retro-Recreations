/// scr_stage01_player_step() | bounded tile-grid movement, jump, carry, throw
/// PROTOTYPE: coefficients/AI/contact boxes are not measured NES timings.
var axis, i, nx, ny, step_y, ground, box, foe, boss;
if (global.stage01_clear || global.stage01_game_over) exit;
if (global.stage01_part == 3) { image_speed = 0; exit; }
axis = keyboard_check(vk_right) - keyboard_check(vk_left);
hsp = 2 * axis;
if (axis != 0) facing = sign(axis);
if (global.stage01_part == 4 && y > 390 && y < 465 && x > 1080 && x < 1248) {
    // Approximate the boss's horizontal water pull; not a ROM physics claim.
    hsp += 0.45;
}
image_xscale = facing;
if (global.stage01_part == 0) sprite_index = spr_chip_seating;
if (global.stage01_part == 1) sprite_index = spr_chip_kitchen;
if (global.stage01_part == 2) sprite_index = spr_chip_grill;
if (global.stage01_part == 4) sprite_index = spr_chip_boss;
if (axis == 0) { image_speed = 0; image_index = 0; }
else image_speed = 0.16;
if (invuln > 0) invuln -= 1;
image_alpha = 1;
if (invuln > 0 && (invuln div 4) mod 2 == 0) image_alpha = 0.45;

// Collision uses an explicit 12 x 18 foot-based hitbox, not the large sprite.
ground = (scr_stage01_collision_at(x - 5, y + 1) > 0 ||
          scr_stage01_collision_at(x + 5, y + 1) > 0);
box = instance_nearest(x, y + 1, obj_crate);
if (box != noone && !box.carried && !box.flying &&
    abs((box.x + 8) - x) < 13 && abs(box.y - y) <= 1) ground = true;
if (ground && (keyboard_check_pressed(vk_space) || keyboard_check_pressed(ord("Z")))) {
    vsp = -5.6;
    y_fraction = 0;
}

// X picks a nearby crate up; the next X throws it. Boss boxes are also crates.
if (keyboard_check_pressed(ord("X"))) {
    if (instance_exists(held_id)) {
        with (held_id) {
            carried = false;
            flying = true;
            vx = other.facing * 5;
            vy = -1.3;
        }
        held_id = noone;
    } else {
        box = instance_nearest(x, y - 10, obj_crate);
        if (box != noone && !box.carried && !box.flying &&
            abs((box.x + 8) - x) < 22 && abs((box.y + 8) - (y - 10)) < 24) {
            held_id = box;
            box.carried = true;
            box.flying = false;
            box.falling = false;
            box.holder = id;
        }
    }
}
x_fraction += hsp;
for (i = 0; i < 4 && abs(x_fraction) >= 1; i += 1) {
    nx = x + sign(x_fraction);
    if (scr_stage01_collision_at(nx - 5, y - 16) == 2 ||
        scr_stage01_collision_at(nx + 5, y - 16) == 2 ||
        scr_stage01_collision_at(nx - 5, y - 2) == 2 ||
        scr_stage01_collision_at(nx + 5, y - 2) == 2) {
        x_fraction = 0; break;
    }
    x = nx;
    x_fraction -= sign(x_fraction);
}
if (global.stage01_part == 4) x = clamp(x, 1032, 1272);
else if (global.stage01_part == 2) x = clamp(x, 8, 1784);
else x = clamp(x, 8, 2040);
vsp = min(4.8, vsp + 0.30);
y_fraction += vsp;
for (i = 0; i < 8 && abs(y_fraction) >= 1; i += 1) {
    step_y = sign(y_fraction);
    ny = y + step_y;
    if (step_y > 0) {
        if (scr_stage01_collision_at(x - 5, ny) > 0 ||
            scr_stage01_collision_at(x + 5, ny) > 0) {
            vsp = 0; y_fraction = 0; break;
        }
        box = instance_nearest(x, ny, obj_crate);
        if (box != noone && !box.carried && !box.flying &&
            abs((box.x + 8) - x) < 13 && y <= box.y && ny >= box.y) {
            vsp = 0; y_fraction = 0; break;
        }
    } else {
        if (scr_stage01_collision_at(x - 5, ny - 18) == 2 ||
            scr_stage01_collision_at(x + 5, ny - 18) == 2) {
            vsp = 0; y_fraction = 0; break;
        }
    }
    y = ny;
    y_fraction -= step_y;
}

// Active chapter boundaries; the static layout of every chapter remains in
// one GMS room, but the view/player relocate as the original screens do.
switch (global.stage01_part) {
    case 0:
        if (x >= 2012) scr_stage01_enter(1);
        else if (y > 755) scr_stage01_player_pit();
        break;
    case 1:
        if (x >= 2012) scr_stage01_enter(2);
        else if (y > 2040) scr_stage01_player_pit();
        break;
    case 2:
        if (x >= 1750 && global.stage01_sink_fill >= 100) scr_stage01_enter(3);
        else if (y > 1535) scr_stage01_player_pit();
        break;
    case 4:
        if (y > 479) scr_stage01_player_pit();
        break;
}
if (global.stage01_game_over || global.stage01_part == 3) exit;
foe = instance_nearest(x, y - 8, obj_stage01_enemy);
if (foe != noone && foe.visible && abs(foe.x - x) < 14 &&
    abs((foe.y - 12) - (y - 8)) < 19) scr_stage01_player_hurt();
if (global.stage01_part == 4 && instance_exists(obj_boss_water_rabbit)) {
    boss = instance_nearest(x, y - 8, obj_boss_water_rabbit);
    if (boss != noone && abs(boss.x - x) < 26 &&
        abs((boss.y - 30) - (y - 8)) < 36) scr_stage01_player_hurt();
}

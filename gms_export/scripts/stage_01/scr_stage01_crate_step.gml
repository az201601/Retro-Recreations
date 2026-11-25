/// scr_stage01_crate_step() | stationary BG-prize becomes held/thrown object
var foe, boss, cx, cy, feet;
if (!is_boss) {
    if (hidden_drop == 1) sprite_index = spr_prize_crate_rr;
    else if (hidden_drop == 2) sprite_index = spr_prize_crate_acorn;
    else sprite_index = spr_prize_crate;
}
if (carried) {
    if (!instance_exists(holder)) { carried = false; }
    else {
        // Ordinary BG prize origin is top-left; observed boss-box OAM
        // origin is centered at its bottom (16,32) in a 32x40 cell.
        if (is_boss) {
            x = holder.x + holder.facing * 12;
            y = holder.y - 14;
        } else {
            x = holder.x + holder.facing * 12 - 8;
            y = holder.y - 30;
        }
        exit;
    }
}
if (!flying && !falling) exit;
if (global.stage01_part != 4 && is_boss) { instance_destroy(); exit; }
ttl += 1;
vy = min(5.5, vy + 0.24);
if (flying) x += vx;
y += vy;
// Both object types use visual centers for hits, despite differing origins.
cx = x + 8; cy = y + 8; feet = y + 16;
if (is_boss) { cx = x; cy = y - 8; feet = y; }
// In the captured battle, box OAM touches or overlaps Water Rabbit on hit
// frames even without B input. Allow falling and thrown boxes to damage it.
if (global.stage01_part == 4 && instance_exists(obj_boss_water_rabbit)) {
    boss = instance_nearest(cx, cy, obj_boss_water_rabbit);
    if (boss != noone && boss.hp > 0 && boss.hit_cooldown <= 0 &&
        abs(cx - boss.x) < 25 &&
        abs(cy - (boss.y - 32)) < 42) {
        boss.hp -= 1;
        boss.hit_cooldown = 36;
        boss.flash = 18;
        scr_stage01_crate_break();
        exit;
    }
}
if (flying) {
    foe = instance_nearest(cx, cy, obj_stage01_enemy);
    if (foe != noone && foe.visible &&
        abs(cx - foe.x) < 17 && abs(cy - (foe.y - 12)) < 22) {
        foe.hp -= 1;
        scr_stage01_crate_break();
        exit;
    }
}
if (scr_stage01_collision_at(cx, feet) > 0) {
    if (flying) { scr_stage01_crate_break(); exit; }
    falling = false;
    vy = 0;
    if (is_boss) y = floor(feet / 16) * 16;
    else y = floor(feet / 16) * 16 - 16;
}
if (ttl > 420 || x < 0 || x >= 2048 || y >= 2048) scr_stage01_crate_break();

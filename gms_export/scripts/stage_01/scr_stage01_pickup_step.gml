/// scr_stage01_pickup_step() | collectible collision, argument0 = 0 RR / 1 acorn
if (!instance_exists(obj_player)) exit;
if (abs(obj_player.x - (x + 8)) < 13 &&
    abs((obj_player.y - 9) - (y + 8)) < 16) {
    if (argument0 == 0) global.rre_count += 1;
    else obj_player.hp = min(3, obj_player.hp + 1);
    instance_destroy();
}

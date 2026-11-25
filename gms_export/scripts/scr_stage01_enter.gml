/// scr_stage01_enter(part) | prototype transition within one 2048x2048 room
/// 0 Seating, 1 Kitchen, 2 Grill, 3 Monterey, 4 Water Rabbit, 5 clear.
/// Spawn coordinates were checked against stable fceumm gameplay captures.
var part, px, py;
part = argument0;
px = 58; py = 704;
switch (part) {
    case 1: px = 24;   py = 1984; break;
    case 2: px = 60;   py = 1472; break;
    case 3: px = 24;   py = 1216; break;
    case 4: px = 1048; py = 320;  break;
}
global.stage01_part = part;
with (obj_player) {
    x = px; y = py;
    hsp = 0; vsp = 0; x_fraction = 0; y_fraction = 0;
    invuln = 60;
    if (instance_exists(held_id)) {
        with (held_id) instance_destroy();
        held_id = noone;
    }
    if (part == 3 || part == 4) hp = 3;
}
// Tossed boxes are not part of the static prize list; clear them on a scene change.
with (obj_boss_box) instance_destroy();
if (part == 4) with (obj_boss_water_rabbit) {
    hp = 6; hit_cooldown = 0; timer = 0;
}
switch (part) {
    case 0: view_xview[0] = 0;    view_yview[0] = 512;  break;
    case 1: view_xview[0] = 0;    view_yview[0] = 1792; break;
    case 2: view_xview[0] = 0;    view_yview[0] = 1280; break;
    case 3: view_xview[0] = 0;    view_yview[0] = 1024; break;
    case 4: view_xview[0] = 1024; view_yview[0] = 256;  break;
}

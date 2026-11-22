// obj_box -- Step event
if (state == "rest") {
    // ground physics
    vspeed += global.gravity_fall;
    if (vspeed > global.max_fall) vspeed = global.max_fall;
    scr_move_v(vspeed);
    scr_move_h(hspeed);
    hspeed = 0;
    // pickup
    if (place_meeting(x, y, obj_player)) {
        with (obj_player) {
            if (state != "throw") {           // only one box at a time
                state = "throw";
                other.state = "held";
            }
        }
    }
}
else if (state == "held") {
    // carried overhead (NES: box sits above the head)
    x = obj_player.x + obj_player.facing * 2;
    y = obj_player.y - global.player_h - 8;
    // throw
    if (keyboard_check_pressed(ord("X"))) {
        state = "thrown";
        hspeed = obj_player.facing * 3.5;     // flat throw arc, measured
        vspeed = 0;
        with (obj_player) state = "idle";
    }
}
else if (state == "thrown") {
    scr_move_h(hspeed);
    vspeed += global.gravity_fall * 0.5;      // the NES box stays aloft longer
    scr_move_v(vspeed);
    // hit enemies
    if (place_meeting(x, y, obj_enemy_fly)) {
        with (obj_enemy_fly) instance_destroy();
        instance_destroy();
    }
    if (y > room_height + 32) instance_destroy();
}

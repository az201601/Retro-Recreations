/// obj_enemy_walker - Step
// ============================================================================
if (global.game_state != "play") exit;

vsp += global.GRAVITY;
if (vsp > global.MAX_FALL) vsp = global.MAX_FALL;

// walk, turn at walls and ledges
if (hurt <= 0) {
    hsp = dir * 0.6;
} else {
    hurt -= 1;
    hsp = hsp * 0.9;
}

scr_move_and_collide();

if (on_ground && hurt <= 0) {
    // wall ahead?
    if (place_meeting(x + dir * 8, y, obj_ground)) {
        dir = -dir;
    } else if (!place_meeting(x + dir * 8, y + 2, obj_ground)) {
        // ledge ahead -> turn around rather than walking off
        dir = -dir;
    }
}
image_xscale = dir;

// touch damage
if (instance_exists(obj_player)) {
    if (place_meeting(x, y, obj_player)) {
        with (obj_player) scr_player_hit(1, other.x);
    }
}

if (y > room_height + 64) instance_destroy();

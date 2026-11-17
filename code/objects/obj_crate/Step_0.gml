/// obj_crate - Step
// ============================================================================
if (global.game_state != "play") exit;

switch (state) {
    case "idle":
        // fall + rest on the ground
        vsp += global.GRAVITY;
        if (vsp > global.MAX_FALL) vsp = global.MAX_FALL;
        scr_move_and_collide();
        hsp = hsp * 0.8;
        break;

    case "carried":
        hsp = 0;
        vsp = 0;
        break;

    case "thrown":
        life += 1;
        vsp += global.GRAVITY * 0.85;
        if (vsp > global.MAX_FALL) vsp = global.MAX_FALL;
        scr_move_and_collide();

        // bounce off walls a little, like the original crates
        if (hsp == 0) hsp = hsp * 0.5;

        // damage any walker we touch
        var _e;
        _e = instance_place(x, y, obj_enemy_walker);
        if (_e != noone) {
            with (_e) scr_enemy_hit(1, other.x);
            state = "broken";
            instance_destroy();
        }

        if (on_ground || life > global.THROW_LIFE) {
            // crates shatter, so the player can use the debris as a projectile
            state = "broken";
            instance_create(x, y - 8, obj_debris);
            instance_destroy();
        }
        break;
}

// drifting off the map
if (y > room_height + 48) instance_destroy();

//=============================================================================
// obj_player  --  Step event
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
//-----------------------------------------------------------------------------
// Paste this into the Step event of  obj_player.
// This is the heart of the game: NES-accurate movement driven by a clean
// state machine. All the "magic numbers" come from scr_init (global.*).
//=============================================================================

scr_input(); // read keyboard/gamepad into global.in_* (see scr_input.gml)

//--- Timers ---------------------------------------------------------------
if (state_timer > 0) state_timer -= 1;
if (invincible_timer > 0) invincible_timer -= 1;

//--- Gravity (always applies, like the original) --------------------------
vsp = min(vsp + global.P_GRAVITY, global.P_MAX_FALL);

//--- Horizontal movement ---------------------------------------------------
var move = global.in_move_x;
if (move != 0) {
    facing = sign(move);
    // Accelerate toward walk speed (snappy, low-skid -- like the original).
    if (abs(hsp) < global.P_WALK_SPEED) {
        hsp += sign(move) * global.P_ACCEL;
        hsp = clamp(hsp, -global.P_WALK_SPEED, global.P_WALK_SPEED);
    }
} else {
    // No input: friction brings us to a stop (move toward 0, don't overshoot).
    if (hsp > 0) hsp = max(0, hsp - global.P_FRICTION);
    else if (hsp < 0) hsp = min(0, hsp + global.P_FRICTION);
}

//--- Jumping ---------------------------------------------------------------
if (global.in_jump and on_ground and state != ST.DUCK) {
    vsp = global.P_JUMP_VEL;
    on_ground = false;
    state = ST.JUMP;
    audio_play_sound(snd_jump, 5, false); // (add this sound resource)
}

//--- Ducking ---------------------------------------------------------------
if (global.in_duck and on_ground) {
    state = ST.DUCK;
    hsp = 0; // can't move while ducking (original behaviour)
}

//--- Pick up / throw -------------------------------------------------------
if (global.in_throw) {
    if (held_object == noone) {
        // Try to pick up a block/acorn in front of us.
        var pickup = instance_nearest(x + facing * 10, y, obj_block);
        if (pickup != noone and abs(pickup.x - x) < 14 and abs(pickup.y - y) < 10) {
            held_object = pickup;
            with (pickup) { held = true; } // block stops being "free"
            state = ST.PICKUP;
            state_timer = 8;
        }
    } else {
        // Throw the held object.
        var blk = held_object;
        held_object = noone;
        with (blk) {
            held = false;
            thrown = true;   // (obj_block's own variable)
            hsp = other.facing * global.THROW_SPEED;
            vsp = -1.0;      // slight upward pop, like the original
        }
        state = ST.THROW;
        state_timer = 8;
        audio_play_sound(snd_throw, 5, false); // (add this sound resource)
    }
}

//--- Apply movement with tile collision ------------------------------------
move_x(hsp);
var hit_floor = move_y(vsp);
on_ground = hit_floor and vsp > 0;
if (on_ground) vsp = 0;

//--- State transitions (ground states) -------------------------------------
if (on_ground) {
    if (state == ST.JUMP or state == ST.FALL) state = ST.IDLE;
    if (state != ST.DUCK and state != ST.PICKUP and state != ST.THROW) {
        state = (abs(hsp) > 0.1) ? ST.WALK : ST.IDLE;
    }
} else {
    state = (vsp < 0) ? ST.JUMP : ST.FALL;
}

//--- Animation (NES timing: new frame every N steps) -----------------------
anim_timer += 1;
if (state == ST.WALK and anim_timer >= global.P_WALK_ANIM) {
    anim_timer = 0;
    anim_frame = 1 - anim_frame; // toggle between the 2 walk frames
}
switch (state) {
    case ST.IDLE:  image_index = 0; break;
    case ST.WALK:  image_index = 1 + anim_frame; break; // frames 1-2
    case ST.JUMP:  image_index = 3; break;
    case ST.FALL:  image_index = 4; break;
    case ST.DUCK:  image_index = 5; break;
    case ST.PICKUP: image_index = 6; break;
    case ST.THROW:  image_index = 7; break;
    default: image_index = 0; break;
}
image_xscale = facing; // flip the sprite to face left/right

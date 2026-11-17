/// obj_player - Step
// ============================================================================
if (global.game_state != "play") exit;

var _left, _right, _jump, _act;
_left  = global.IN[? "left"];
_right = global.IN[? "right"];
_jump  = global.IN[? "jump"];
_act   = global.IN[? "action_p"];

// ---- timers --------------------------------------------------------------
if (invuln > 0) invuln -= 1;
if (throw_cool > 0) throw_cool -= 1;
if (stun   > 0) stun   -= 1;
if (jump_buf > 0) jump_buf -= 1;
if (coyote > 0) coyote -= 1;

// ---- buffer a jump -------------------------------------------------------
if (global.IN[? "jump_p"]) jump_buf = global.JUMP_BUFFER;

// ---- stunned (hit) -> no control ----------------------------------------
if (stun > 0) {
    hsp = hsp * 0.94;
    vsp += global.GRAVITY;
    if (vsp > global.MAX_FALL) vsp = global.MAX_FALL;
    scr_anim_set("chip_hurt");
    scr_anim_update();
    exit;
}

// ---- horizontal movement -------------------------------------------------
var _accel, _target;
if (carrying != noone) {
    // carrying slows Chip down exactly like the original
    _target = global.RUN_SPEED * 0.62;
} else {
    _target = global.RUN_SPEED;
}
_accel = on_ground ? global.RUN_ACCEL : global.AIR_ACCEL;

if (_left && !_right) {
    hsp -= _accel;
    dir = -1;
    image_xscale = -1;
} else if (_right && !_left) {
    hsp += _accel;
    dir = 1;
    image_xscale = 1;
} else {
    // friction / stop
    if (on_ground) {
        if (abs(hsp) <= global.RUN_FRICTION) hsp = 0;
        else hsp -= sign(hsp) * global.RUN_FRICTION;
    }
}
if (hsp >  _target) hsp = max(_target, hsp - global.RUN_FRICTION);
if (hsp < -_target) hsp = min(-_target, hsp + global.RUN_FRICTION);

// ---- jump ----------------------------------------------------------------
if (jump_buf > 0 && (on_ground || coyote > 0)) {
    vsp     = global.JUMP_SPEED;
    jumping = true;
    on_ground = false;
    coyote    = 0;
    jump_buf  = 0;
}
// variable height: releasing early cuts the jump
if (jumping && global.IN[? "jump_r"] && vsp < 0) {
    vsp = vsp * global.JUMP_CUT;
    jumping = false;
}

// ---- gravity -------------------------------------------------------------
vsp += global.GRAVITY;
if (vsp > global.MAX_FALL) vsp = global.MAX_FALL;

// ---- collide & move ------------------------------------------------------
scr_move_and_collide();

// ---- landing feedback ----------------------------------------------------
if (on_ground) {
    jumping = false;
    coyote  = global.COYOTE_TIME;
}

// ---- pickup / throw ------------------------------------------------------
if (_act && throw_cool <= 0) {
    if (carrying == noone) {
        // grab a crate that overlaps the hands
        var _c;
        _c = instance_place(x, y - 12, obj_crate);
        if (_c != noone) {
            if (_c.state == "idle") {
                carrying = _c;
                _c.state = "carried";
                _c.carrier = id;
            }
        }
    } else {
        // throw it
        with (carrying) {
            state  = "thrown";
            hsp    = obj_player.dir * global.THROW_SPEED;
            vsp    = -1.2;
            image_index = 0;
        }
        carrying   = noone;
        throw_cool = 12;
        scr_anim_set("chip_throw");
    }
}

// keep the carried crate glued above the head
if (carrying != noone && instance_exists(carrying)) {
    carrying.x = x + dir * 2;
    carrying.y = y - 26;
    carrying.image_xscale = 1;
}

// ---- animation selection -------------------------------------------------
// The throw clip is non-looping; while it plays it must not be overridden.
if (anim_key == "chip_throw" && image_speed > 0) {
    // keep the current clip
} else if (!on_ground) {
    if (vsp < 0) scr_anim_set("chip_jump");
    else         scr_anim_set("chip_fall");
} else if (abs(hsp) > 0.12) {
    scr_anim_set("chip_walk");
} else if (carrying != noone) {
    scr_anim_set("chip_push");
} else {
    scr_anim_set("chip_idle");
}
scr_anim_update();

// ---- fell out of the room ------------------------------------------------
if (y > room_height + 64) {
    hp = 0;
    scr_player_die();
}

/// scr_player_step()
/// Starter GMS 1.4.1760 player step logic for Chip/Dale.
/// Attach to obj_player Step event (or call from it).
/// NOTE: Tune constants to match NES feel during GMS import.

var move_speed = 2;
var jump_speed = -6;
var grav = 0.35;
var max_fall = 6;

// --- Input (map these actions in GMS project) ---
var k_left  = keyboard_check(vk_left);
var k_right = keyboard_check(vk_right);
var k_jump  = keyboard_check_pressed(ord("Z")) || keyboard_check_pressed(vk_space);
var k_throw = keyboard_check_pressed(ord("X")) || keyboard_check_pressed(vk_control);

// --- Horizontal movement ---
var h = k_right - k_left;
hsp = h * move_speed;
if (h != 0) image_xscale = h;

// --- Ground check ---
var on_ground = place_meeting(x, y + 1, obj_solid);

// --- Jump ---
if (on_ground && k_jump) {
    vsp = jump_speed;
}

// --- Gravity ---
vsp += grav;
if (vsp > max_fall) vsp = max_fall;

// --- Horizontal collision ---
if (place_meeting(x + hsp, y, obj_solid)) {
    while (!place_meeting(x + sign(hsp), y, obj_solid)) x += sign(hsp);
    hsp = 0;
}
x += hsp;

// --- Vertical collision ---
if (place_meeting(x, y + vsp, obj_solid)) {
    while (!place_meeting(x, y + sign(vsp), obj_solid)) y += sign(vsp);
    vsp = 0;
}
y += vsp;

// --- Pickup / throw crate (starter) ---
if (k_throw) {
    if (holding_crate) {
        // Throw crate in facing direction
        with (held_crate_id) {
            held = false;
            thrown = true;
            hsp = other.image_xscale * 4;
            vsp = -2;
        }
        holding_crate = false;
        held_crate_id = noone;
    } else {
        var c = instance_place(x + image_xscale * 8, y, obj_crate);
        if (c != noone && !c.held) {
            holding_crate = true;
            held_crate_id = c;
            c.held = true;
            c.holder = id;
        }
    }
}

/// scr_enemy_honeybee_step()
/// Starter honeybee enemy for Stage 1 Restaurant.
/// Attach to obj_enemy_honeybee Step event.

var spd = 1.2;

// Simple horizontal patrol; replace with room-specific pathing.
x += dir * spd;

// Turn around on solid collision or patrol bounds.
if (place_meeting(x + dir, y, obj_solid)) dir *= -1;
if (x < patrol_left) { x = patrol_left; dir = 1; }
if (x > patrol_right) { x = patrol_right; dir = -1; }

image_xscale = dir;

// Damage player on contact
var p = instance_place(x, y, obj_player);
if (p != noone) {
    with (p) { event_user(0); } // player damage event
}

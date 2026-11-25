/// scr_enemy_slimeball_step()
/// Starter silverware slimeball for Stage 1 Restaurant.
/// Attach to obj_enemy_slimeball Step event.
/// Behavior: simple patrol + periodic lunge/attack placeholder.

var spd = 0.8;
var grav = 0.35;

vsp += grav;
if (vsp > 6) vsp = 6;

x += dir * spd;

// Turn on wall/patrol edge
if (place_meeting(x + dir, y, obj_solid)) dir *= -1;
if (x < patrol_left) { x = patrol_left; dir = 1; }
if (x > patrol_right) { x = patrol_right; dir = -1; }

// Floor collision
if (place_meeting(x, y + vsp, obj_solid)) {
    while (!place_meeting(x, y + sign(vsp), obj_solid)) y += sign(vsp);
    vsp = 0;
}
y += vsp;

image_xscale = dir;

// TODO: add fork attack timing/animation and projectile/hitbox per NES behavior.
var p = instance_place(x, y, obj_player);
if (p != noone) {
    with (p) { event_user(0); }
}

/// scr_crate_step()
/// Starter crate/box behavior for GMS 1.4.1760.
/// Attach to obj_crate Step event.

var grav = 0.35;
var max_fall = 6;

if (held) {
    // Follow holder above head; adjust offsets to sprite size.
    if (instance_exists(holder)) {
        x = holder.x;
        y = holder.y - 16;
        hsp = 0;
        vsp = 0;
        image_xscale = holder.image_xscale;
    } else {
        held = false;
    }
} else {
    // Gravity
    vsp += grav;
    if (vsp > max_fall) vsp = max_fall;

    // Horizontal collision
    if (place_meeting(x + hsp, y, obj_solid)) {
        while (!place_meeting(x + sign(hsp), y, obj_solid)) x += sign(hsp);
        hsp = 0;
        if (thrown) {
            // Break on impact - replace with animation/sfx as needed
            instance_destroy();
            exit;
        }
    }
    x += hsp;

    // Vertical collision
    if (place_meeting(x, y + vsp, obj_solid)) {
        while (!place_meeting(x, y + sign(vsp), obj_solid)) y += sign(vsp);
        if (thrown && abs(vsp) > 0) {
            instance_destroy();
            exit;
        }
        vsp = 0;
        // Ground friction for thrown crates
        if (abs(hsp) > 0.1) hsp *= 0.8; else hsp = 0;
    }
    y += vsp;

    // Hit enemy
    var e = instance_place(x, y, obj_enemy);
    if (e != noone && thrown) {
        with (e) { event_user(0); } // enemy hit event
        instance_destroy();
        exit;
    }
}

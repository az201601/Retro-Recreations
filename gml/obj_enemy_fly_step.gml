// obj_enemy_fly -- Step event
t += 1;
x = home_x + lengthdir_x(range, t * 0.8) * 1.0;      // slow horizontal patrol
x = home_x + sin(t * 0.02) * range;
y = home_y + sin(t * 0.12) * 10;                     // vertical bob

// wing animation ~6 frames per pose (measured from sprite captures)
if ((t mod 6) == 0) frame_i = (frame_i + 1) mod 2;

// contact damage (NES: 1 heart, knockback + invulnerability)
if (place_meeting(x, y, obj_player)) {
    with (obj_player) {
        if (invuln <= 0) {
            hearts -= 1;
            invuln = 90;                 // ~1.5 s of blinking, like the NES
            vspeed = -4;
            if (other.x < x) x += 8; else x -= 8;
        }
    }
}

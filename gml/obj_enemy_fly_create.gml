// obj_enemy_fly -- Create event
// The fly ("Randy") patrols horizontally with a sine bob, exactly like the
// NES behaviour observed in RAM watch (steady x drift + vertical oscillation).
// Import the fly frames from assets/sprites2/obj_XX.png as spr_fly_0..N.
home_x = x;
home_y = y;
t = irandom(60);
spd = 0.6;          // px/frame measured from gameplay captures
range = 48;         // patrol half-width
frame_i = 0;

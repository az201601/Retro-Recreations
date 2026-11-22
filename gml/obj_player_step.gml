// obj_player -- Step event
// Physics constants are all in scr_init.gml (measured from the NES game).

// ---------- input ----------
var move;
move = 0;
if (keyboard_check(vk_left)  || keyboard_check(ord("A"))) { move = -1; facing = -1; }
if (keyboard_check(vk_right) || keyboard_check(ord("D"))) { move =  1; facing =  1; }
var k_jump, k_throw;
k_jump  = keyboard_check(ord("Z")) || keyboard_check(vk_space) || keyboard_check(vk_up);
k_jump_p = keyboard_check_pressed(ord("Z")) || keyboard_check_pressed(vk_space) || keyboard_check_pressed(vk_up);
k_throw = keyboard_check_pressed(ord("X"));

// ---------- jump start (NES: jump initiates on the A press while grounded) ----------
if (on_ground && k_jump_p) {
    vspeed = global.jump_v0;
    jump_held = 0;
    on_ground = false;
}

// ---------- gravity (variable jump height, measured) ----------
var g;
if (vspeed < 0 && k_jump && jump_held < global.jump_hold_max) {
    g = global.gravity_hold;   // 0.38 px/f^2 while rising with jump held
    jump_held += 1;
} else {
    g = global.gravity_fall;   // 1.0 px/f^2
}
vspeed += g;
if (vspeed > global.max_fall) vspeed = global.max_fall;

// ---------- horizontal (instant 2 px/f, measured; no acceleration) ----------
scr_move_h(move * global.walk_speed);

// ---------- vertical ----------
scr_move_v(vspeed);

// ---------- animation state ----------
if (!on_ground) {
    state = "jump";
} else if (move != 0) {
    state = "walk";
    anim_timer += 1;
    if (anim_timer >= 8) {         // NES walk cycle ~8 frames per pose
        anim_timer = 0;
        anim_frame = (anim_frame + 1) mod 4;
    }
} else {
    state = "idle";
    anim_frame = 0;
    anim_timer = 0;
}

// ---------- fall off the screen (pit / death plane) ----------
if (y > room_height + 32) {
    hearts -= 1;
    if (hearts <= 0) {
        hearts = global.max_hearts;   // simple restart; swap in a game-over object if wanted
        x = 32; y = 128;
    } else {
        x = 32; y = 128;              // respawn at stage start
    }
    vspeed = 0;
}

if (invuln > 0) invuln -= 1;

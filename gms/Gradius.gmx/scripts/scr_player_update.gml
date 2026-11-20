/// scr_player_update()
// Player movement, Option trail ring buffer, weapons, and power-up gauge
// matching 6502 disassembly of sub_9FFC, sub_894B, sub_8974, and sub_9789.

var i, spd, dx, dy, moving, head, idx, want_spr;
var fire_a, fire_slot_base, s_idx, b_idx, m_idx, vx_shot, vy_shot;
var opt_idx, code_key;

// ---------------------------------------------------------------------------
// 1. Pause Konami Code ($9789: U U D D L R L R B A)
// ---------------------------------------------------------------------------
if (global.ram_paused != 0) {
    if (global.pad_pressed != 0) {
        code_key = 0;
        if (global.konami_step == 0 || global.konami_step == 1) code_key = $08;
        else if (global.konami_step == 2 || global.konami_step == 3) code_key = $04;
        else if (global.konami_step == 4 || global.konami_step == 6) code_key = $02;
        else if (global.konami_step == 5 || global.konami_step == 7) code_key = $01;
        else if (global.konami_step == 8) code_key = $40;
        else if (global.konami_step == 9) code_key = $80;

        if ((global.pad_pressed & code_key) != 0) {
            global.konami_step += 1;
            if (global.konami_step >= 10) {
                // sub_9C5E: full shield, missile, speed=1, 2 options
                global.p_shield = 5;
                global.p_missile = 1;
                if (global.p_speed < 1) global.p_speed = 1;
                global.p_options = 2;
                global.konami_step = 0;
            }
        } else {
            global.konami_step = 0;
        }
    }
    exit;
}

if (global.obj_state[0] != 1) {
    exit;
}

// Dev helper in skeleton: press F2 to advance power-up gauge ($0042) for testing
if (keyboard_check_pressed(vk_f2)) {
    global.p_power += 1;
    if (global.p_power > 6) global.p_power = 1;
}

// ---------------------------------------------------------------------------
// 2. Power-up activation on B button (sub_8974 / $8986)
// ---------------------------------------------------------------------------
if ((global.pad_pressed & $40) != 0 && global.p_power > 0) {
    if (global.p_power == 1) {
        if (global.p_speed < 14) global.p_speed += 1;
    } else if (global.p_power == 2) {
        global.p_missile = 1;
    } else if (global.p_power == 3) {
        global.p_weapon = 2; // Double
    } else if (global.p_power == 4) {
        global.p_weapon = 1; // Laser
    } else if (global.p_power == 5) {
        if (global.p_options < 2) global.p_options += 1;
    } else if (global.p_power == 6) {
        global.p_shield = 5;
    }
    global.p_power = 0;
}

// ---------------------------------------------------------------------------
// 3. Player movement: speed = min($0040 + 2, $10) * 0.5 px/frame
//    Clamped X in [16, 240], Y in [16, 192]
// ---------------------------------------------------------------------------
spd = min(global.p_speed + 2, 16) * 0.5;
dx = 0;
dy = 0;
if ((global.pad_held & $01) != 0) dx += spd; // Right
if ((global.pad_held & $02) != 0) dx -= spd; // Left
if ((global.pad_held & $04) != 0) dy += spd; // Down
if ((global.pad_held & $08) != 0) dy -= spd; // Up

moving = ((global.pad_held & $0F) != 0);

global.obj_x[0] = clamp(global.obj_x[0] + dx, 16, 240);
global.obj_y[0] = clamp(global.obj_y[0] + dy, 16, 192);

// Banking metasprite ($01=level, $02=down, $03=up; 8-frame transition delay)
if (dy > 0) {
    want_spr = 2;
} else if (dy < 0) {
    want_spr = 3;
} else {
    want_spr = 1;
}

if (want_spr != global.obj_spr[0]) {
    if (global.obj_anim_t[0] > 0) {
        global.obj_anim_t[0] -= 1;
    } else {
        global.obj_spr[0] = want_spr;
        global.obj_anim_t[0] = 8;
    }
} else {
    global.obj_anim_t[0] = 8;
}

// ---------------------------------------------------------------------------
// 4. 24-entry Option trail ring buffer ($07A0/$07C0, sub_A2A9)
// ---------------------------------------------------------------------------
if (moving) {
    head = (global.obj_anim_i[0] + 1) mod 24;
    global.obj_anim_i[0] = head;
    global.opt_trail_x[head] = floor(global.obj_x[0]);
    global.opt_trail_y[head] = floor(global.obj_y[0]);
} else {
    head = global.obj_anim_i[0];
}

for (opt_idx = 1; opt_idx <= 2; opt_idx += 1) {
    if (opt_idx <= global.p_options) {
        idx = (head + 24 - opt_idx * 11) mod 24;
        global.obj_state[opt_idx] = 1;
        global.obj_x[opt_idx] = global.opt_trail_x[idx];
        global.obj_y[opt_idx] = global.opt_trail_y[idx];
        global.obj_spr[opt_idx] = 4 + ((global.ram_frame_ctr >> 2) & 1);
    } else {
        global.obj_state[opt_idx] = 0;
        global.obj_spr[opt_idx] = 0;
    }
}

// ---------------------------------------------------------------------------
// 5. Weapons (slots 3..5 ShotA, 6..8 ShotB, 9..11 Missiles)
// ---------------------------------------------------------------------------
if (global.obj_cd[0] > 0) {
    global.obj_cd[0] -= 1;
}
if ((global.pad_pressed & $80) != 0 || ((global.pad_held & $80) != 0 && global.obj_cd[0] == 0)) {
    fire_a = true;
    global.obj_cd[0] = 6;
} else {
    fire_a = false;
}

if (fire_a) {
    // Spawn from Player (0) and any active Options (1..p_options)
    for (i = 0; i <= global.p_options; i += 1) {
        s_idx = 3 + i;
        b_idx = 6 + i;
        m_idx = 9 + i;

        // Primary Shot A (Normal=6 @ +7px/f, Laser=7 @ +12px/f, Double=6 @ +7px/f)
        if (global.obj_state[s_idx] == 0) {
            global.obj_state[s_idx] = 1;
            global.obj_x[s_idx] = global.obj_x[i] + 8;
            global.obj_y[s_idx] = global.obj_y[i];
            if (global.p_weapon == 1) {
                global.obj_spr[s_idx] = 7;
                global.obj_vx[s_idx] = 12;
                global.obj_vy[s_idx] = 0;
            } else {
                global.obj_spr[s_idx] = 6;
                global.obj_vx[s_idx] = 7;
                global.obj_vy[s_idx] = 0;
            }
        } else if (global.p_weapon != 2 && global.obj_state[b_idx] == 0) {
            // Second concurrent shot in stream B for Normal / Laser
            global.obj_state[b_idx] = 1;
            global.obj_x[b_idx] = global.obj_x[i] + 8;
            global.obj_y[b_idx] = global.obj_y[i];
            if (global.p_weapon == 1) {
                global.obj_spr[b_idx] = 7;
                global.obj_vx[b_idx] = 12;
                global.obj_vy[b_idx] = 0;
            } else {
                global.obj_spr[b_idx] = 6;
                global.obj_vx[b_idx] = 7;
                global.obj_vy[b_idx] = 0;
            }
        }

        // Double 45-degree diagonal shot in stream B (sid $24, dx=+4, dy=-4)
        if (global.p_weapon == 2 && global.obj_state[b_idx] == 0) {
            global.obj_state[b_idx] = 1;
            global.obj_x[b_idx] = global.obj_x[i] + 4;
            global.obj_y[b_idx] = global.obj_y[i] - 4;
            global.obj_spr[b_idx] = $24;
            global.obj_vx[b_idx] = 4;
            global.obj_vy[b_idx] = -4;
        }

        // Missile (slots 9..11, sid $0A falling dx=+0.5, dy=+2 -> ground $08 at y>=192)
        if (global.p_missile != 0 && global.obj_state[m_idx] == 0) {
            global.obj_state[m_idx] = 1;
            global.obj_x[m_idx] = global.obj_x[i];
            global.obj_y[m_idx] = global.obj_y[i] + 4;
            global.obj_spr[m_idx] = $0A;
            global.obj_vx[m_idx] = 0.5;
            global.obj_vy[m_idx] = 2.0;
        }
    }
}

// Integrate active projectile slots 3..11
for (i = 3; i <= 11; i += 1) {
    if (global.obj_state[i] != 0) {
        global.obj_x[i] += global.obj_vx[i];
        global.obj_y[i] += global.obj_vy[i];

        // Missile ground transition near bottom terrain floor (Stage 1 starfield baseline)
        if (i >= 9 && global.obj_spr[i] == $0A && global.obj_y[i] >= 188) {
            global.obj_y[i] = 188;
            global.obj_vx[i] = 2.0;
            global.obj_vy[i] = 0.0;
            global.obj_spr[i] = $08;
        }

        if (global.obj_x[i] > 256 || global.obj_x[i] < -16 || global.obj_y[i] < -16 || global.obj_y[i] > 208) {
            global.obj_state[i] = 0;
            global.obj_spr[i] = 0;
        }
    }
}

/// scr_nes_end_of_frame()
// Explicit End-of-Frame phase (End Step -> NES $8B10 / $8BAB).
// Builds $0200-$02FF OAM shadow and stages scroll/HUD registers for the NEXT
// frame's VBlank-begin. Nothing written here is visible until VBlank-begin.

var i, cur, used, s, sh_attr, sh_fr;

// 1. Clear all 64 OAM shadow slots to Y=$F4 (244 = offscreen)
for (i = 0; i < 64; i += 1) {
    global.oam_sh_y[i] = 244;
    global.oam_sh_sid[i] = 0;
    global.oam_sh_attr[i] = 0;
    global.oam_sh_x[i] = 244;
    global.oam_sh_frame[i] = 0;
}

// 2. Slot 0 ($0200-$0203): fixed Sprite-0 split marker ($8B08)
if (global.ram_mode >= 5 && global.ram_hud_visible != 0) {
    global.oam_sh_y[0] = 206;     // $CE -> scanline 207
    global.oam_sh_sid[0] = $6D;   // Sprite-0 marker
    global.oam_sh_attr[0] = $23;  // behind BG, sprite palette 3
    global.oam_sh_x[0] = 248;     // $F8
}

// 3. Advance rotating OAM start slot ($002F += $44 -> +17 slots mod 64, skip 0)
global.ram_oam_rot = (global.ram_oam_rot + 17) & 63;
if (global.ram_oam_rot == 0) {
    global.ram_oam_rot = 1;
}
cur = global.ram_oam_rot;
used = 0;

// 4. Stage active SoA object slots 0..31 into rotating OAM slots
if (global.ram_ppu_active != 0) {
    for (i = 0; i < 32; i += 1) {
        if (global.obj_state[i] != 0 && global.obj_spr[i] != 0 && used < 63) {
            s = global.obj_spr[i];
            sh_attr = global.obj_attr[i];
            // Metasprites in $8D9E set hardware behind-BG priority ($20) except explosion ($2D..$30)
            if (s != $2D) {
                sh_attr = sh_attr | $20;
            }
            if (s == 4 || s == 5) {
                // Option 2-frame sprite
                cur = scr_oam_push(cur, global.obj_y[i], 4, sh_attr, global.obj_x[i], s - 4);
            } else if (s == $0A) {
                cur = scr_oam_push(cur, global.obj_y[i], $0A, sh_attr, global.obj_x[i], 0);
            } else if (s == $08) {
                cur = scr_oam_push(cur, global.obj_y[i], $0A, sh_attr, global.obj_x[i], 1);
            } else {
                cur = scr_oam_push(cur, global.obj_y[i], s, sh_attr, global.obj_x[i], 0);
            }
            used += 1;
        }
    }

    // Player Shield metasprite ($5A..$5D) when active
    if (global.ram_mode >= 5 && global.obj_state[0] == 1 && global.p_shield > 0 && used < 63) {
        sh_attr = $20;
        if (global.p_shield == 1) sh_attr = $23;
        sh_fr = (global.ram_frame_ctr >> 1) & 3;
        cur = scr_oam_push(cur, global.obj_y[0], $5A, sh_attr, global.obj_x[0], sh_fr);
        used += 1;
    }
}

// 5. Stage PPU registers for next VBlank-begin
global.next_mode = global.ram_mode;
global.next_ppu_active = global.ram_ppu_active;
global.next_scroll_x = global.ram_scroll_x;
global.next_scroll_y = global.ram_scroll_y;
global.next_hud_visible = global.ram_hud_visible;
global.next_hud_power = global.p_power;
global.next_hud_lives = global.p_lives;
global.next_hud_score = global.p_score;
global.next_hud_hiscore = global.p_hiscore;
global.next_player_sel = global.ram_player_sel;
global.next_title_blink = (global.ram_mode == 3) && ((global.ram_timer & 8) != 0);

/// scr_nes_ppu_draw()
// Renders the 256x240 NTSC frame strictly from VBlank-latched global.ppu_* state.
// Sprites render at (ppu_oam_x, ppu_oam_y + 1) to match the NES PPU's +1 scanline
// OAM evaluation delay. Crisp integer pixel output (interpolation disabled).

var s, pass, sx, sy, w1, spr, fr, ox, oy, is_bg_prio;
var digit, tmp_val, k;

texture_set_interpolation(false);

if (!surface_exists(global.ppu_surface)) {
    global.ppu_surface = surface_create(256, 240);
}

surface_set_target(global.ppu_surface);
draw_clear_alpha(global.nes_pal[$0F], 1);

if (global.ppu_active != 0) {
    // Pass 0: behind-BG sprites ((attr & $20) != 0); Pass 1: foreground sprites
    // (In Stage 1, bg_stage1_stars has alpha=0 on color 0 so stars appear over behind-BG sprites.)
    for (pass = 0; pass <= 1; pass += 1) {
        if (pass == 1) {
            if (global.ppu_mode < 5) {
                sx = global.ppu_scroll_x & 255;
                if (sx == 0) {
                    draw_background(bg_title_screen, 0, 0);
                } else {
                    draw_background_part(bg_title_screen, sx, 0, 256 - sx, 240, 0, 0);
                }
                // Mode 3 Start confirmation: blink selected 1 PLAYER / 2 PLAYERS row ($814B..$815E)
                if (global.ppu_mode == 3 && global.ppu_title_blink) {
                    draw_set_colour(global.nes_pal[$0F]);
                    if (global.ppu_player_sel == 0) {
                        draw_rectangle(103, 135, 176, 144, false);
                    } else {
                        draw_rectangle(103, 151, 176, 160, false);
                    }
                    draw_set_colour(c_white);
                }
            } else {
                sx = global.ppu_scroll_x & 511;
                sy = global.ppu_scroll_y;
                w1 = min(256, 512 - sx);
                draw_background_part(bg_stage1_stars, sx, sy, w1, 208, 0, 0);
                if (w1 < 256) {
                    draw_background_part(bg_stage1_stars, 0, sy, 256 - w1, 208, w1, 0);
                }
            }
        }

        // In Title mode bg_title_screen is opaque black, so draw Title cursor in foreground pass
        for (s = 63; s >= 1; s -= 1) {
            oy = global.ppu_oam_y[s];
            if (oy >= 240) continue;

            is_bg_prio = ((global.ppu_oam_attr[s] & $20) != 0) && (global.ppu_mode >= 5);
            if ((pass == 0 && !is_bg_prio) || (pass == 1 && is_bg_prio)) continue;

            ox = global.ppu_oam_x[s];
            fr = global.ppu_oam_frame[s];
            spr = -1;

            switch (global.ppu_oam_sid[s]) {
                case 1:
                    if (global.ppu_mode < 5) spr = spr_title_cursor;
                    else spr = spr_vic_viper_level;
                    break;
                case 2: spr = spr_vic_viper_down; break;
                case 3: spr = spr_vic_viper_up; break;
                case 4: spr = spr_option; break;
                case 6: spr = spr_shot; break;
                case 7: spr = spr_laser; break;
                case $0A: spr = spr_missile; break;
                case $0C: spr = spr_fan; break;
                case $10: spr = spr_capsule_red; break;
                case $13: spr = spr_capsule_blue; break;
                case $24: spr = spr_double; break;
                case $2D: spr = spr_explosion; break;
                case $5A:
                    if ((global.ppu_oam_attr[s] & $03) == $03) spr = spr_shield_low;
                    else spr = spr_shield;
                    break;
            }

            if (spr != -1) {
                // +1 scanline NES hardware OAM vertical offset
                draw_sprite(spr, fr, ox, oy + 1);
            }
        }
    }

    // Sprite-0 HUD split at y=208..239 (CHR Bank 1, PPUSCROLL_X=0)
    if (global.ppu_mode >= 5 && global.ppu_hud_visible != 0) {
        draw_background(bg_hud_bar, 0, 208);

        // Active power-up box highlight ($0042 = 1..6)
        if (global.ppu_hud_power >= 1 && global.ppu_hud_power <= 6) {
            draw_sprite(spr_hud_slot_lit, global.ppu_hud_power - 1, 32 + (global.ppu_hud_power - 1) * 32, 212);
        }

        // Lives digit (col 5 = x 40, row 29 = y 220)
        digit = clamp(global.ppu_hud_lives, 0, 9);
        draw_sprite(spr_hud_digits, digit, 40, 220);

        // 7-digit 1P Score (cols 11..17 = x 88..136, y 220)
        tmp_val = max(0, floor(global.ppu_hud_score));
        for (k = 6; k >= 0; k -= 1) {
            digit = tmp_val mod 10;
            tmp_val = tmp_val div 10;
            draw_sprite(spr_hud_digits, digit, 88 + k * 8, 220);
        }

        // 7-digit HI Score (cols 23..29 = x 184..232, y 220)
        tmp_val = max(0, floor(global.ppu_hud_hiscore));
        for (k = 6; k >= 0; k -= 1) {
            digit = tmp_val mod 10;
            tmp_val = tmp_val div 10;
            draw_sprite(spr_hud_digits, digit, 184 + k * 8, 220);
        }
    }
}

surface_reset_target();

// Present 256x240 PPU output into the room canvas
draw_surface(global.ppu_surface, 0, 0);

// Optional debug HUD (F1)
if (global.debug_overlay) {
    draw_set_colour(global.nes_pal[$30]);
    draw_text(4, 4, "F:" + string(global.nes_frame) + " M:" + string(global.ppu_mode) +
        " SX:" + string(global.ppu_scroll_x) + " P:" + string(global.obj_x[0]) + "," + string(global.obj_y[0]) +
        " PWR:" + string(global.p_power) + " OPT:" + string(global.p_options) + " SHD:" + string(global.p_shield));
}

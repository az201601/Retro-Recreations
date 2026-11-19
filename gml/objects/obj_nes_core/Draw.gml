/// obj_nes_core - Draw
// State 1 (second screen) is the spotlight intro: pale disc drawn first,
// then the black-silhouette background over it, so the silhouettes knock
// out of the light exactly like the NES priority rules (docs/07).
// Needs resources: spr_spotlight1 (origin 32,32), spr_state1_bg (origin 0,0).
draw_set_color(c_black);
draw_rectangle(0, 0, global.NES_W, global.NES_H, false);

if (global.game_state == 1) {
    var px, py;
    px = floor(global.s1_x / 256);
    py = floor(global.s1_y / 256);
    draw_sprite(spr_spotlight1, 0, px, py);
    draw_sprite(spr_state1_bg, 0, 0, 0);
    // Palette fade-in at state entry takes ~16 frames in the ROM.
    if (global.game_state_timer < 16) {
        draw_set_alpha(1 - (global.game_state_timer / 16));
        draw_rectangle(0, 0, global.NES_W, global.NES_H, false);
        draw_set_alpha(1);
    }
}

// Temporary debug overlay. Remove when screen rendering is complete.
draw_set_color(c_white);
draw_text(8, 8, "FRAME " + string(global.NES_FRAME));
draw_text(8, 24, "PAD " + string(global.pad_held) + " PRESS " + string(global.pad_pressed));
draw_text(8, 40, "STATE " + string(global.game_state));

/// obj_nes_core - Draw
// Temporary M0 debug overlay. Remove when real screen rendering lands (M1/M2).
draw_set_color(c_black);
draw_rectangle(0, 0, global.NES_W, global.NES_H, false);
draw_set_color(c_white);
draw_text(8, 8, "FRAME " + string(global.NES_FRAME));
draw_text(8, 24, "PAD " + string(global.pad_held) + " PRESS " + string(global.pad_pressed));
draw_text(8, 40, "STATE " + string(global.game_state));

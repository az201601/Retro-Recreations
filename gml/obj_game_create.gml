// obj_game -- Create event (persistent controller for the stage)
// Place ONE instance in the room.  It loads the collision grid and
// keeps a global frame counter for animation timing.

scr_init();

frame = 0;

// ---- load collision.csv (32 x 30, comma-separated 0/1) ----
// Import collision.csv via Included Files (or paste it in the working dir).
global.solid = ds_grid_create(global.level_w_tiles, global.level_h_tiles);
var f, row, col, line, vals;
f = file_text_open_read("collision.csv");
row = 0;
while (!file_text_eof(f) && row < global.level_h_tiles) {
    line = file_text_read_string(f);
    file_text_readln(f);
    vals = string_split_vals(line);   // see scr_string_split_vals.gml
    for (col = 0; col < global.level_w_tiles; col += 1) {
        ds_grid_set(global.solid, col, row, real(vals[col]));
    }
    row += 1;
}
file_text_close(f);

// ---- draw settings ----
window_set_fullscreen(false);

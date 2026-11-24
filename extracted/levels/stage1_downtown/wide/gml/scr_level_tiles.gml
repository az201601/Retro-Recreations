/// scr_level_tiles(csv_file, tileset_bg, x0, y0, cell, depth)
///
/// Builds a GMS 1.4 tile layer from the exported tilemap CSV.
///
/// The CSV's first row is a header (`c0,c1,...`); every following row is one
/// 8-pixel tile row of the room, left to right. A cell of -1 is empty.
///
/// Requirements:
///   * the CSV must ship as an Included File (same name as passed here)
///   * `tileset_bg` must be a Background resource with "Use as tileset" ticked
///   * call this once, e.g. from the Create event of a level controller placed
///     at the room origin
///
/// GMS 1.4 note: tile_add() takes the *background resource* index, the source
/// rectangle inside it, the size, the room position and a depth. Tiles live in
/// the room, not in an instance, so nothing needs to be destroyed on restart
/// beyond leaving the room.
///
///   scr_level_tiles("tilemap.csv", bg_tileset_stage1, 0, 0, 8, 1000);

var f, line, row, col, cell_id, src_x, src_y;

f = file_text_open_read(argument0);
row = 0;
while (!file_text_eof(f))
{
    line = file_text_read_string(f);
    file_text_readln(f);

    // Skip the header row.
    if (row > 0)
    {
        col = 0;
        while (col < string_length(line))
        {
            // Cells are comma separated; -1 means no tile.
            var start, len, text;
            start = col;
            while (col < string_length(line) && string_char_at(line, col + 1) != ",")
                col += 1;
            text = string_copy(line, start + 1, col - start);
            col += 1; // skip the comma

            cell_id = real(text);
            if (cell_id >= 0)
            {
                // tileset.png holds 16 cells per row; tileset_strip.png would
                // use src_x = cell_id * 8 and src_y = 0 instead.
                src_x = (cell_id mod 16) * 8;
                src_y = (cell_id div 16) * 8;
                tile_add(argument1,
                         src_x, src_y, 8, 8,
                         argument2 + (col - 1) * 8,
                         argument3 + row * 8,
                         argument5);
            }
        }
    }
    row += 1;
}
file_text_close(f);

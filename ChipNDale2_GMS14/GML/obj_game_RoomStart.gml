//=============================================================================
// obj_game  --  Room Start event
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Room Start event of an object named  obj_game.
// Builds the tile-collision grid by scanning the room's "solid" tile layer.
// Paint solid tiles on the background named  bg_solid  in the room editor.
//=============================================================================

// Grid size from the room dimensions (8x8 tiles).
global.GRID_W = ceil(room_width / global.TILE);
global.GRID_H = ceil(room_height / global.TILE);
global.grid = ds_grid_create(global.GRID_W, global.GRID_H);
ds_grid_clear(global.grid, 0); // everything empty by default

// Scan every placed tile; tiles on bg_solid become solid (value 1).
var count = tile_get_count();
for (var i = 0; i < count; i += 1) {
    var t = tile_get_id(i);
    if (tile_get_background(t) == bg_solid) {
        var tx = floor(tile_get_x(t) / global.TILE);
        var ty = floor(tile_get_y(t) / global.TILE);
        if (tx >= 0 and ty >= 0 and tx < global.GRID_W and ty < global.GRID_H) {
            ds_grid_set(global.grid, tx, ty, 1);
        }
    }
}

//=============================================================================
// Script name:  scr_tile_solid_at
// GameMaker Studio 1.4.1760  |  Chip 'n Dale Rescue Rangers 2 recreation
//-----------------------------------------------------------------------------
// Create a Script resource named  scr_tile_solid_at  and paste this in.
// Returns true if the 8x8 tile containing pixel (argument0, argument1)
// is solid (value 1 in the level grid). Outside the level counts as solid.
//=============================================================================

var px = argument0;
var py = argument1;
var tx = floor(px / global.TILE);
var ty = floor(py / global.TILE);
if (tx < 0 or ty < 0 or tx >= global.GRID_W or ty >= global.GRID_H) {
    return true; // outside the level = solid wall
}
return (ds_grid_get(global.grid, tx, ty) == 1);

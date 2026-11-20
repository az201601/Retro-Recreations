//=============================================================================
// Script name:  scr_rect_solid
// GameMaker Studio 1.4.1760  |  Chip 'n Dale Rescue Rangers 2 recreation
//-----------------------------------------------------------------------------
// Create a Script resource named  scr_rect_solid  and paste this in.
// Returns true if the rectangle from (argument0,argument1) to
// (argument2,argument3) overlaps any solid tile. Used for collision.
//=============================================================================

var x1 = argument0, y1 = argument1, x2 = argument2, y2 = argument3;
var tx1 = floor(min(x1, x2) / global.TILE);
var ty1 = floor(min(y1, y2) / global.TILE);
var tx2 = floor(max(x1, x2) / global.TILE);
var ty2 = floor(max(y1, y2) / global.TILE);
for (var ty = ty1; ty <= ty2; ty += 1) {
    for (var tx = tx1; tx <= tx2; tx += 1) {
        if (tx < 0 or ty < 0 or tx >= global.GRID_W or ty >= global.GRID_H) {
            return true;
        }
        if (ds_grid_get(global.grid, tx, ty) == 1) return true;
    }
}
return false;

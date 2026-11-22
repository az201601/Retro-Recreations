/// scr_solid_at(px, py) -> true if the 8x8 tile at pixel (px,py) is solid
// Requires: global.solid ds_grid built by obj_level Create from collision.csv
var tx, ty;
tx = floor(argument0 / global.tile_size);
ty = floor(argument1 / global.tile_size);
if (tx < 0 || tx >= global.level_w_tiles) return true;   // side walls
if (ty < 0 || ty >= global.level_h_tiles) return false;  // open sky / pits
return ds_grid_get(global.solid, tx, ty) == 1;

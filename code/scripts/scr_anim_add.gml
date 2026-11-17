/// scr_anim_add  (GameMaker: Studio 1.4)
// Register one animation entry in the global animation table.
//
// @param key    string  lookup key, e.g. "chip_walk"
// @param strip  real    index of the sprite strip
// @param frames real    number of frames in the strip
// @param speed  real    image_speed (0 = static)
// @param loop   bool    loop the strip
// ============================================================================
var _d;
_d = ds_map_create();
ds_map_add(_d, "strip",  argument0);
ds_map_add(_d, "frames", argument1);
ds_map_add(_d, "speed",  argument2);
ds_map_add(_d, "loop",   argument3);
ds_map_add(global.anim_def, argument[0], _d);

/// scr_anim_get  (GameMaker: Studio 1.4)
// Returns the ds_map registered for an animation key, or -1.
//
// @param key  string
// ============================================================================
var _k, _d;
_k = argument0;

if (!ds_map_exists(global.anim_def, _k)) {
    show_debug_message("scr_anim_get: unknown animation '" + string(_k) + "'");
    return -1;
}

_d = global.anim_def[? _k];
return _d;

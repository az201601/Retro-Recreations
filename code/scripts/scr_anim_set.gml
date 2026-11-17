/// scr_anim_set  (GameMaker: Studio 1.4)
// Switch an instance to a named animation.
//
// Expected instance variables:
//   anim_key    string  current animation
//   anim_loop   bool
//   anim_count  real    frames in the strip
//
// @param key  string
// ============================================================================
var _d, _strip;
_d = scr_anim_get(argument0);
if (_d == -1) exit;

_strip = _d[? "strip"];

if (sprite_index != _strip || anim_key != argument0) {
    sprite_index = _strip;
    image_index  = 0;
    image_speed  = _d[? "speed"];
    anim_key     = argument0;
    anim_loop    = _d[? "loop"];
    anim_count   = _d[? "frames"];
}

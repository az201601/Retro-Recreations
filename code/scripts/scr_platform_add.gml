/// scr_platform_add  (GameMaker: Studio 1.4)
// Create one solid platform rectangle.
//
// @param x0,y0   top-left corner in room pixels
// @param w,h     size in pixels
// @return        the obj_ground instance id
//
// The instance uses the 1x1 white sprite (spr_pixel / spr_ui_pixel) with its
// origin at the top-left, so scaling the sprite by w/h gives both the mask and
// the drawn rectangle - collision is exact and no tile layer is required.
// ============================================================================
var _p;
_p = instance_create(argument0, argument1, obj_ground);
_p.image_xscale = argument2;
_p.image_yscale = argument3;
_p.visible      = false;
return _p;

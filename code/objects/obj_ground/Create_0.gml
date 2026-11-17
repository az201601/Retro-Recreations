/// obj_ground - Create
// Invisible solid.  One instance covers a whole platform: the sprite is a
// 1x1 white pixel (origin top-left) scaled by image_xscale / image_yscale, so
// the mask equals the rectangle that was asked for.  Create these with
// scr_platform_add(x, y, w, h) rather than placing them by hand.
// ---------------------------------------------------------------------------
sprite_index = asset_get_index("spr_pixel");
if (sprite_index < 0) sprite_index = asset_get_index("spr_ui_pixel");
if (sprite_index < 0) sprite_index = -1;

image_speed  = 0;
image_xscale = 1;
image_yscale = 1;
depth        = 100;
visible      = false;

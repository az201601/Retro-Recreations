/// obj_debris - Create
// Short lived particle burst when a crate or enemy is destroyed.
// ============================================================================
image_speed = 0;
image_angle = irandom(359);
hsp        = random_range(-1.8, 1.8);
vsp        = random_range(-2.4, -0.6);
life       = 40;
image_xscale = random_range(0.5, 1.0);
image_yscale = image_xscale;
sprite_index = asset_get_index("spr_debris");
if (sprite_index < 0) { sprite_index = -1; visible = false; }

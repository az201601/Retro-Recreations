/// obj_crate - Create
// ============================================================================
sprite_index = asset_get_index("spr_crate");
if (sprite_index < 0) { sprite_index = -1; visible = false; }
image_speed  = 0;

hsp    = 0;
vsp    = 0;
state  = "idle";      // idle | carried | thrown | broken
carrier = noone;
life   = 0;
on_ground = false;

// bbox comes from the sprite: 16 x 16, origin centre-bottom.

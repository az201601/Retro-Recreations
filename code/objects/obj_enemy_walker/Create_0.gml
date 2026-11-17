/// obj_enemy_walker - Create
// ============================================================================
sprite_index = asset_get_index("spr_enemy_walker");
if (sprite_index < 0) { sprite_index = -1; visible = false; }
image_speed  = 0.18;

dir        = -1;
hsp        = -0.6;
vsp        = 0;
hp         = 2;
hurt       = 0;
on_ground  = false;
turn_timer = 0;
anim_key   = "";
anim_loop  = true;
anim_count = 2;
image_xscale = -1;


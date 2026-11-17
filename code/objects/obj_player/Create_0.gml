/// obj_player - Create
// Chip / Dale, in-level.  Movement model taken from the NES game: run speed,
// jump arc, crate carry and throw.
// ============================================================================
if (!variable_global_exists("anim_def")) {
    scr_config_init();
    scr_input_init();
    scr_anim_init();
}

// ---- animation bookkeeping (used by scr_anim_set / scr_anim_update) ------
anim_key   = "";
anim_loop  = true;
anim_count = 1;

// ---- physics -------------------------------------------------------------
hsp        = 0;
vsp        = 0;
dir        = 1;          // facing: 1 right, -1 left
on_ground  = false;
coyote     = 0;
jump_buf   = 0;
jumping    = false;

// ---- combat --------------------------------------------------------------
hp         = 4;          // the NES HUD shows 4 hearts at the start
invuln     = 0;
stun       = 0;
carrying   = noone;      // crate instance held over the head
throw_cool = 0;

// ---- spawn / respawn -----------------------------------------------------
spawn_x = x;
spawn_y = y;

// ---- hitbox --------------------------------------------------------------
// bbox_* are read-only in GameMaker 1.4, the mask comes from the sprite:
// spr_chip_* 12 x 24, origin centre-bottom (see code/README_IMPORT.md).

scr_anim_set("chip_idle");

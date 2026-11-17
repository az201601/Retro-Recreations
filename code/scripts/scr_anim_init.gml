/// scr_anim_init  (GameMaker: Studio 1.4)
// Animation table: key -> (sprite strip, frame count, image_speed, loop).
// Call once from obj_gamecontroller Create.
//
// Sprite names follow assets_vec (see code/README_IMPORT.md):
//   assets_vec/sprites/<character>/<anim>.png  ->  spr_<character>_<anim>
// asset_get_index() is used so a renamed or not-yet-imported sprite simply
// disables that clip instead of crashing.  tools/check_assets.py lists every
// name the code needs.
// ============================================================================
if (variable_global_exists("anim_def")) exit;      // idempotent

global.anim_def = ds_map_create();

var s;

// ---- Chip, in-level -------------------------------------------------------
s = asset_get_index("spr_chip_idle");   if (s >= 0) scr_anim_add("chip_idle",  s, 2, 0.20, true);
s = asset_get_index("spr_chip_walk");   if (s >= 0) scr_anim_add("chip_walk",  s, 4, 0.40, true);
s = asset_get_index("spr_chip_jump");   if (s >= 0) scr_anim_add("chip_jump",  s, 2, 0.35, false);
s = asset_get_index("spr_chip_fall");   if (s >= 0) scr_anim_add("chip_fall",  s, 2, 0.25, true);
s = asset_get_index("spr_chip_land");   if (s >= 0) scr_anim_add("chip_land",  s, 1, 0.00, false);
s = asset_get_index("spr_chip_push");   if (s >= 0) scr_anim_add("chip_push",  s, 1, 0.00, false);
s = asset_get_index("spr_chip_throw");  if (s >= 0) scr_anim_add("chip_throw", s, 2, 0.40, false);

// no knock-back pose exists in the source art: reuse the fall clip
if (asset_get_index("spr_chip_hurt") >= 0) {
    scr_anim_add("chip_hurt", asset_get_index("spr_chip_hurt"), 1, 0.0, false);
} else {
    scr_anim_add("chip_hurt", asset_get_index("spr_chip_fall"), 2, 0.0, true);
}

// ---- cut scene cast -------------------------------------------------------
s = asset_get_index("spr_chip_scene_stand");  if (s >= 0) scr_anim_add("chip_scene_stand", s, 3, 0.15, true);
s = asset_get_index("spr_chip_scene_walk");   if (s >= 0) scr_anim_add("chip_scene_walk",  s, 2, 0.30, true);
s = asset_get_index("spr_chip_intro_walk");   if (s >= 0) scr_anim_add("chip_intro_walk",  s, 6, 0.25, true);
s = asset_get_index("spr_chip_intro_stand");  if (s >= 0) scr_anim_add("chip_intro_stand", s, 4, 0.15, true);
s = asset_get_index("spr_dale_intro_stand");  if (s >= 0) scr_anim_add("dale_stand",       s, 3, 0.15, true);
s = asset_get_index("spr_dale_intro_crouch"); if (s >= 0) scr_anim_add("dale_crouch",      s, 3, 0.15, true);
s = asset_get_index("spr_gadget_stand");      if (s >= 0) scr_anim_add("gadget_stand",     s, 3, 0.15, true);
s = asset_get_index("spr_gadget_talk");       if (s >= 0) scr_anim_add("gadget_talk",      s, 2, 0.20, true);
s = asset_get_index("spr_gadget_wave");       if (s >= 0) scr_anim_add("gadget_wave",      s, 3, 0.20, true);
s = asset_get_index("spr_doctor_talk");       if (s >= 0) scr_anim_add("doctor_talk",      s, 4, 0.20, true);

// ---- title / cut-scene artwork -------------------------------------------
s = asset_get_index("spr_cutscene_pair");     if (s >= 0) scr_anim_add("cutscene_pair",    s, 1, 0.00, true);
s = asset_get_index("spr_cutscene_logo");     if (s >= 0) scr_anim_add("cutscene_logo",    s, 3, 0.10, true);
s = asset_get_index("spr_logo_pair");         if (s >= 0) scr_anim_add("logo_pair",        s, 1, 0.00, true);

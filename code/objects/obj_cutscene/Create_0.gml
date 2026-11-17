/// obj_cutscene - Create
// Linear cut-scene player: a list of shots, each one an animation key plus a
// screen position and a duration in steps.  Used for the intro (Gadget, Dale,
// the doctor) and the ending.
// ============================================================================
if (!variable_global_exists("anim_def")) {
    scr_config_init();
    scr_input_init();
    scr_anim_init();
}

shots = ds_list_create();
cur   = 0;
t     = 0;
done  = false;

anim_key   = "";
anim_loop  = true;
anim_count = 1;
image_speed = 0;

depth = -900;

/// obj_title - Create
// Title screen: shows the extracted title art, START begins the stage.
// ============================================================================
scr_config_init();
scr_input_init();
scr_anim_init();

global.game_state = "title";

spr_title = asset_get_index("spr_title_screen");
if (spr_title < 0) spr_title = asset_get_index("spr_ui_title_screen");

alpha   = 0;
blink   = 0;
started = false;

/// obj_gamecontroller - Create
// Single owner of global setup: config, input, animation table.
// ============================================================================
randomize();

scr_config_init();          // NES constants, palette
scr_input_init();           // keyboard / pad bindings
scr_anim_init();            // animation table

global.game_state = "title";    // title | play | pause
global.score      = 0;
global.lives      = 3;
global.stage      = 1;
global.player_char = 0;         // 0 = Chip, 1 = Dale

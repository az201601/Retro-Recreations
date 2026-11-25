/// scr_stage01_controller_create() | GMS 1.4.1760 playable *prototype*
/// NES layout and art are exact static ROM data; gameplay timing is not.
global.stage01_part = 0;
global.stage01_sink_active = false;
global.stage01_sink_fill = 0;
global.stage01_clear = false;
global.stage01_game_over = false;
global.rre_count = 0;
global.stage01_lives = 3;
refill_timer = 0;
clear_timer = 0;
scr_stage01_place_static();
scr_stage01_spawn_prizes();
scr_stage01_spawn_actors();
instance_create(58, 704, obj_player);
display_set_gui_size(256, 240);
// This is a 23-second stationary music *reference*, not a seamless loop.
audio_play_sound(snd_restaurant_excerpt, 0, false);

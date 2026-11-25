/// scr_stage01_sink_step() | the Grill's faucet fills before the exit opens
if (global.stage01_part != 2 || global.stage01_sink_active) exit;
if (!instance_exists(obj_player)) exit;
if (abs(obj_player.x - x) < 65 && keyboard_check_pressed(ord("X"))) {
    global.stage01_sink_active = true;
    instance_create(x, 1310, obj_sink_water_jet);
}

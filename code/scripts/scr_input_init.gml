/// scr_input_init  (GameMaker: Studio 1.4)
// Keyboard + gamepad binding, plus the NES-style "pressed" edge flags.
// Call once in obj_gamecontroller Create.
// ============================================================================
if (variable_global_exists("KEY")) exit;           // idempotent

global.KEY = ds_map_create();

// ---- player 1 -------------------------------------------------------------
ds_map_add(global.KEY, "left",   vk_left);
ds_map_add(global.KEY, "right",  vk_right);
ds_map_add(global.KEY, "up",     vk_up);
ds_map_add(global.KEY, "down",   vk_down);
ds_map_add(global.KEY, "jump",   ord("X"));      // NES A
ds_map_add(global.KEY, "action", ord("Z"));      // NES B (pick up / throw)
ds_map_add(global.KEY, "start",  vk_enter);      // NES START
ds_map_add(global.KEY, "select", vk_shift);      // NES SELECT

// alternate keys (WASD style, common on keyboards without arrow clusters)
ds_map_add(global.KEY, "left2",  ord("A"));
ds_map_add(global.KEY, "right2", ord("D"));
ds_map_add(global.KEY, "up2",    ord("W"));
ds_map_add(global.KEY, "down2",  ord("S"));
ds_map_add(global.KEY, "jump2",  ord("K"));
ds_map_add(global.KEY, "action2",ord("J"));

// ---- runtime state --------------------------------------------------------
global.IN = ds_map_create();
global.IN[? "left"]   = false;   global.IN[? "left_p"]   = false;
global.IN[? "right"]  = false;   global.IN[? "right_p"]  = false;
global.IN[? "up"]     = false;   global.IN[? "up_p"]     = false;
global.IN[? "down"]   = false;   global.IN[? "down_p"]   = false;
global.IN[? "jump"]   = false;   global.IN[? "jump_p"]   = false;
global.IN[? "jump_r"] = false;
global.IN[? "action"] = false;   global.IN[? "action_p"] = false;
global.IN[? "start"]  = false;   global.IN[? "start_p"]  = false;
global.IN[? "select"] = false;   global.IN[? "select_p"] = false;

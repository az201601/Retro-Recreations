//=============================================================================
// scr_input.gml
// GameMaker Studio 1.4.1760  |  Chip 'n Dale Rescue Rangers 2 recreation
//-----------------------------------------------------------------------------
// WHAT THIS IS:
//   One place that reads ALL input (keyboard + gamepad) and turns it into
//   simple "intent" values the player object can use:
//       move_x   -> -1 (left), 0 (none), +1 (right)
//       move_y   -> -1 (up),   0 (none), +1 (down)
//       jump     -> true on the step the jump button is pressed
//       throw    -> true on the step the throw button is pressed
//       duck     -> true while down is held
//
// HOW TO USE IT:
//   1. Create a Script resource named  scr_input
//   2. Paste this whole file into it.
//   3. In obj_player's Step event, call  scr_input();  at the very top,
//      then use the global.in_* values below.
//
// NOTE ON GAMEPAD:
//   GMS 1.4 uses the joypad_* functions (the gamepad_* names are from the
//   newer GameMaker 2). Keyboard always works; a gamepad is a bonus.
//   joypad index 0 = first gamepad plugged in.
//=============================================================================

global.in_move_x = 0;
global.in_move_y = 0;
global.in_jump   = false;
global.in_throw  = false;
global.in_duck   = false;

//---------------- Keyboard ----------------
var k_left  = keyboard_check(vk_left)  or keyboard_check(ord('A'));
var k_right = keyboard_check(vk_right) or keyboard_check(ord('D'));
var k_up    = keyboard_check(vk_up)    or keyboard_check(ord('W'));
var k_down  = keyboard_check(vk_down)  or keyboard_check(ord('S'));
var k_jump  = keyboard_check_pressed(ord('X')) or keyboard_check_pressed(vk_space);
var k_throw = keyboard_check_pressed(ord('Z')) or keyboard_check_pressed(vk_control);

//---------------- Gamepad (optional) ----------------
var pad = 0; // first gamepad
var g_left = false, g_right = false, g_up = false, g_down = false;
var g_jump = false, g_throw = false;
if (joypad_is_connected(pad)) {
    g_left  = joypad_button_check(pad, joypad_button_15) or (joypad_axis_value(pad, joypad_axis_x) < -0.4);
    g_right = joypad_button_check(pad, joypad_button_14) or (joypad_axis_value(pad, joypad_axis_x) >  0.4);
    g_up    = joypad_button_check(pad, joypad_button_13) or (joypad_axis_value(pad, joypad_axis_y) < -0.4);
    g_down  = joypad_button_check(pad, joypad_button_12) or (joypad_axis_value(pad, joypad_axis_y) >  0.4);
    g_jump  = joypad_button_check_pressed(pad, joypad_button_1);   // A button
    g_throw = joypad_button_check_pressed(pad, joypad_button_2);   // B button
}

//---------------- Combine ----------------
global.in_move_x = (k_right or g_right) - (k_left or g_left);
global.in_move_y = (k_down  or g_down)  - (k_up    or g_up);
global.in_jump   = k_jump or g_jump;
global.in_throw  = k_throw or g_throw;
global.in_duck   = (k_down or g_down);

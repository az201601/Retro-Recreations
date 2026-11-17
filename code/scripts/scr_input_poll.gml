/// scr_input_poll  (GameMaker: Studio 1.4)
// Refresh the input map each step: "held" and "_p" (pressed this step) flags.
// NES semantics: a press only counts on the frame the button goes down.
// ============================================================================
var _was;

// ---- read raw state -------------------------------------------------------
_was = global.IN[? "left"];
global.IN[? "left"]  = keyboard_check(global.KEY[? "left"])  || keyboard_check(global.KEY[? "left2"]);
global.IN[? "left_p"] = (global.IN[? "left"] && !_was);

_was = global.IN[? "right"];
global.IN[? "right"]  = keyboard_check(global.KEY[? "right"]) || keyboard_check(global.KEY[? "right2"]);
global.IN[? "right_p"] = (global.IN[? "right"] && !_was);

_was = global.IN[? "up"];
global.IN[? "up"]  = keyboard_check(global.KEY[? "up"]) || keyboard_check(global.KEY[? "up2"]);
global.IN[? "up_p"] = (global.IN[? "up"] && !_was);

_was = global.IN[? "down"];
global.IN[? "down"]  = keyboard_check(global.KEY[? "down"]) || keyboard_check(global.KEY[? "down2"]);
global.IN[? "down_p"] = (global.IN[? "down"] && !_was);

_was = global.IN[? "jump"];
global.IN[? "jump"]  = keyboard_check(global.KEY[? "jump"]) || keyboard_check(global.KEY[? "jump2"]);
global.IN[? "jump_p"] = (global.IN[? "jump"] && !_was);
global.IN[? "jump_r"] = !global.IN[? "jump"];

_was = global.IN[? "action"];
global.IN[? "action"]  = keyboard_check(global.KEY[? "action"]) || keyboard_check(global.KEY[? "action2"]);
global.IN[? "action_p"] = (global.IN[? "action"] && !_was);

_was = global.IN[? "start"];
global.IN[? "start"]  = keyboard_check(global.KEY[? "start"]);
global.IN[? "start_p"] = (global.IN[? "start"] && !_was);

_was = global.IN[? "select"];
global.IN[? "select"]  = keyboard_check(global.KEY[? "select"]);
global.IN[? "select_p"] = (global.IN[? "select"] && !_was);

// ---- optional gamepad (slot 0) -------------------------------------------
if (gamepad_is_connected(0)) {
    if (gamepad_button_check(0, gp_padu)) global.IN[? "up"]    = true;
    if (gamepad_button_check(0, gp_padd)) global.IN[? "down"]  = true;
    if (gamepad_button_check(0, gp_padl)) global.IN[? "left"]  = true;
    if (gamepad_button_check(0, gp_padr)) global.IN[? "right"] = true;
    if (gamepad_button_check_pressed(0, gp_face1)) global.IN[? "jump_p"]   = true;
    if (gamepad_button_check_pressed(0, gp_face2)) global.IN[? "action_p"] = true;
    if (gamepad_button_check(0, gp_face1)) global.IN[? "jump"]   = true;
    if (gamepad_button_check(0, gp_face2)) global.IN[? "action"] = true;
    if (gamepad_button_check_pressed(0, gp_start)) global.IN[? "start_p"] = true;
}

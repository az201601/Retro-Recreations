/// scr_input_poll()
// Poll player 1 and derive held/pressed/released exactly like the ROM
// routine at $C17C: pressed = held & ~previous, released = previous & ~held.
// Bit order: A=$01 B=$02 Select=$04 Start=$08 Up=$10 Down=$20 Left=$40 Right=$80.

var held;
held = 0;

// Keyboard: X=A, Z=B, Shift=Select, Enter=Start, arrows=D-pad.
if (keyboard_check(ord('X'))) held = held | global.PAD_A;
if (keyboard_check(ord('Z'))) held = held | global.PAD_B;
if (keyboard_check(vk_shift)) held = held | global.PAD_SELECT;
if (keyboard_check(vk_enter)) held = held | global.PAD_START;
if (keyboard_check(vk_up)) held = held | global.PAD_UP;
if (keyboard_check(vk_down)) held = held | global.PAD_DOWN;
if (keyboard_check(vk_left)) held = held | global.PAD_LEFT;
if (keyboard_check(vk_right)) held = held | global.PAD_RIGHT;

// Gamepad device 0 (GMS 1.4 gamepad API), ORed with the keyboard.
if (gamepad_is_connected(0)) {
    if (gamepad_button_check(0, gp_face1)) held = held | global.PAD_A;
    if (gamepad_button_check(0, gp_face2)) held = held | global.PAD_B;
    if (gamepad_button_check(0, gp_select)) held = held | global.PAD_SELECT;
    if (gamepad_button_check(0, gp_start)) held = held | global.PAD_START;
    if (gamepad_button_check(0, gp_padu)) held = held | global.PAD_UP;
    if (gamepad_button_check(0, gp_padd)) held = held | global.PAD_DOWN;
    if (gamepad_button_check(0, gp_padl)) held = held | global.PAD_LEFT;
    if (gamepad_button_check(0, gp_padr)) held = held | global.PAD_RIGHT;
}

global.pad_pressed = held & ~global.pad_prev;
global.pad_released = global.pad_prev & ~held;
global.pad_held = held & $FF;
global.pad_pressed = global.pad_pressed & $FF;
global.pad_released = global.pad_released & $FF;
global.pad_prev = global.pad_held;

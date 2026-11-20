/// scr_nes_input_poll()
// NES controller latch ($81BF): polls keyboard into P1 bitmask
// Bit layout matching $0005 / $0007:
//   $80=A (Z / Space), $40=B (X / Shift), $20=Select (C / Backspace),
//   $10=Start (Enter), $08=Up, $04=Down, $02=Left, $01=Right.

var raw;
raw = 0;

if (keyboard_check(ord("Z")) || keyboard_check(vk_space)) raw |= $80;
if (keyboard_check(ord("X")) || keyboard_check(vk_shift)) raw |= $40;
if (keyboard_check(ord("C")) || keyboard_check(vk_backspace)) raw |= $20;
if (keyboard_check(vk_enter)) raw |= $10;
if (keyboard_check(vk_up) || keyboard_check(ord("W"))) raw |= $08;
if (keyboard_check(vk_down) || keyboard_check(ord("S"))) raw |= $04;
if (keyboard_check(vk_left) || keyboard_check(ord("A"))) raw |= $02;
if (keyboard_check(vk_right) || keyboard_check(ord("D"))) raw |= $01;

global.pad_raw = raw;
global.pad_pressed = (raw ^ global.pad_prev) & raw; // $0005 new presses
global.pad_held = raw;                               // $0007 held state
global.pad_prev = raw;

// Debug overlay toggle (F1) - non-NES helper
if (keyboard_check_pressed(vk_f1)) {
    global.debug_overlay = !global.debug_overlay;
}

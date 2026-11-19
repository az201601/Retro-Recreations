/// scr_nes_init()
// Initialise NES-equivalent global state.
// Source facts: NTSC NES frame = 16639 microseconds (60.0988 Hz);
// reference ROM boots with PPUCTRL shadow $29=$08, PPUMASK shadow $2A=$1E,
// MMC1 control $1E (see docs/01_rom_analysis.md).

global.NES_W = 256;
global.NES_H = 240;
global.NES_FRAME = 0;          // master frame counter, +1 per simulated NES frame
global.NES_FRAME_US = 16639;   // NTSC frame duration in microseconds
global.NES_ACC = 0;            // microsecond accumulator (used if accumulator stepping is enabled)

// Controller bit masks - NES order produced by the ROM routine at $C17C.
global.PAD_A = $01;
global.PAD_B = $02;
global.PAD_SELECT = $04;
global.PAD_START = $08;
global.PAD_UP = $10;
global.PAD_DOWN = $20;
global.PAD_LEFT = $40;
global.PAD_RIGHT = $80;

global.pad_held = 0;
global.pad_prev = 0;
global.pad_pressed = 0;
global.pad_released = 0;

// Game-state byte equivalent to RAM $40 in the ROM.
// PROJECT DECISION: skip ROM state 0 (the first/copyright screen: its whole
// script is WAIT 120 frames, then state 1). We boot at state 1, the second
// screen - exactly where the ROM arrives after state 0 fades out.
// See docs/06_screens_sequence.md for the decoded scripts.
global.game_state = 1;
global.game_state_timer = 0;

// State-1 spotlight anchor position, 8.8 fixed point (set again on state
// entry in scr_game_state_step). ROM start: X=192, Y=-64 (docs/06/07).
global.s1_x = 192 * 256;
global.s1_y = -64 * 256;

// Placeholder seed only. The ROM RNG routine has not been located yet;
// do not use this for gameplay until it is replaced (see TASKS.md).
global.nes_rng_state = $A5;

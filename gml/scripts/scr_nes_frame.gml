/// scr_nes_frame()
// Advance the recreation by exactly one NES frame.
// Order mirrors the ROM frame: NMI-side input poll happens before the
// main-loop game-state dispatch (input poll $C17C runs under NMI at $C031,
// the $C54E state dispatch runs in the main loop afterwards).
scr_input_poll();

// $C54E-equivalent state dispatch (shell; handlers land per milestone).
scr_game_state_step(global.game_state);

global.game_state_timer += 1;
global.NES_FRAME += 1;

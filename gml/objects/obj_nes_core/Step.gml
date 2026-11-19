/// obj_nes_core - Step
// Default mode: one simulated NES frame per Step event (set room speed 60).
// Accumulator mode: converts real elapsed time to whole NTSC frames using
// delta_time (microseconds in GMS 1.4). Logic always advances in whole
// frames either way; never scale physics by delta_time fractions.
if (use_accumulator) {
    var steps;
    global.NES_ACC += delta_time;
    steps = 0;
    while (global.NES_ACC >= global.NES_FRAME_US && steps < 4) {
        scr_nes_frame();
        global.NES_ACC -= global.NES_FRAME_US;
        steps += 1;
    }
    if (steps == 4) global.NES_ACC = 0; // drop backlog instead of spiralling
} else {
    scr_nes_frame();
}

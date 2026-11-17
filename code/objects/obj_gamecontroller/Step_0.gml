/// obj_gamecontroller - Step
// Refreshes the input map and owns the global pause flag.
// ============================================================================
scr_input_poll();

// Pause is a state change only: every gameplay object already exits its Step
// while global.game_state != "play", which freezes the game without
// deactivating instances (deactivating would also freeze this controller and
// make it impossible to unpause).  Draw events keep running, so the HUD and the
// overlay stay visible.
if (global.IN[? "start_p"]) {
    if (global.game_state == "play") {
        global.game_state = "pause";
    } else if (global.game_state == "pause") {
        global.game_state = "play";
    }
}

/// obj_title - Step
// ============================================================================
scr_input_poll();

if (alpha < 1) alpha += 0.05;

blink += 1;

if (!started && (global.IN[? "start_p"] || global.IN[? "jump_p"])) {
    started = true;
    room_goto(rm_level01);
}

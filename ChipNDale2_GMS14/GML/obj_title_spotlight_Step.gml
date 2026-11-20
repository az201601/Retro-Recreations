//=============================================================================
// obj_title_spotlight  --  Step event
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
//-----------------------------------------------------------------------------
// Runs the measured spotlight timeline, one NES frame per GMS step.
// All of the magic numbers are documented in scr_title_spotlight.gml.
//=============================================================================

if (scene_done) exit;

frame += 1;

//------------------------------------------------------ hand over to the mural
// At step 886 the game swaps the black stencil out for the colourful title mural
// (a different nametable on CHR bank 30) and fades its palette up over 18
// steps, finishing at step 904. The spotlight scene is finished at that point.
if (frame >= global.SPOT_MURAL_FRAME) {
    mural_on   = true;
    disk_on    = false;
    mural_fade = (frame - global.SPOT_MURAL_FRAME) / global.SPOT_MURAL_STEPS;
    if (mural_fade > 1) mural_fade = 1;

    if (frame >= global.SPOT_SCENE_END) {
        scene_done = true;
        room_goto(global.SPOT_NEXT_ROOM);
    }
    exit;
}

//------------------------------------------------------------ disk appears?
if (frame < global.SPOT_START_FRAME) {
    disk_on = false;
    exit;                                   // nothing on screen yet
}
disk_on = true;

//--------------------------------------------------------------- the path
if (frame <= 219) {
    // Stage 1: one row of sprites (16 px tall) slides down from the top.
    disk_x = 160;  disk_w = 64;  disk_h = 16;
    disk_y = 2 + 2 * (frame - 212);

} else if (frame <= 226) {
    // Stage 2: two rows.
    disk_x = 160;  disk_w = 64;  disk_h = 32;
    disk_y = 2 + 2 * (frame - 220);

} else if (frame <= 234) {
    // Stage 3: three rows.
    disk_x = 160;  disk_w = 64;  disk_h = 47;
    disk_y = 1 + 2 * (frame - 227);

} else if (frame <= 315) {
    // Stage 4: the full 64x63 disk, still falling.
    disk_x = 160;  disk_w = 64;  disk_h = 63;
    disk_y = 1 + 2 * (frame - 235);

} else if (frame <= 411) {
    // Diagonal up-left. Both axes use the same measured integer pattern.
    disk_x = 158 + scr_spot_pattern(global.SPOT_DIAG_X,  frame - 316);
    disk_y = 159 + scr_spot_pattern(global.SPOT_DIAG_Y,  frame - 316);

} else if (frame <= 475) {
    // Straight right, 2 px per step.
    disk_x = 30 + 2 * (frame - 412);
    disk_y = 29;

} else if (frame <= 522) {
    // Diagonal down-left: x uses the -1.375 pattern, y its mirror image.
    disk_x = 154 + scr_spot_pattern(global.SPOT_DIAG_X,  frame - 476);
    disk_y = 30  + scr_spot_pattern(global.SPOT_DIAG_Y2, frame - 476);

} else if (frame <= 596) {
    // Straight left, 2 px per step, leaves through the left edge.
    disk_x = 90 - 2 * (frame - 523);
    disk_y = 95;

} else if (frame <= 705) {
    // Fully off screen. The disk still exists; it just emits no sprites,
    // which is what gives the pause before it re-enters.
    disk_x = -56;
    disk_y = 95;

} else if (frame <= 785) {
    // Re-enters from the left edge, 2 px per step.
    disk_x = -56 + 2 * (frame - 706);
    disk_y = 73;

} else if (frame <= 801) {
    // Fast reversal: 4 px per step back to the left.
    disk_x = 98 - 4 * (frame - 786);
    disk_y = 73;

} else {
    // Parks on the logo and holds there until the scene ends.
    disk_x = 38;
    disk_y = 73;
}

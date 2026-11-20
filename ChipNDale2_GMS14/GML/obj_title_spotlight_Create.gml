//=============================================================================
// obj_title_spotlight  --  Create event
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
//-----------------------------------------------------------------------------
// The spotlight attract scene. Everything lives on this one object.
// Requires: scr_title_spotlight (globals) and scr_spot_pattern (helper).
//
// Room setup
//   * Room size 256 x 240, speed 60, no views.
//   * Background colour: black.
//   * "Interpolate colours between pixels" must be OFF.
//   * Every spr_spotlight_* sprite: interpolation OFF, origin Top Left.
//=============================================================================

frame      = 0;        // step counter, matches the NES frame numbers
disk_x     = 160;      // top-left of the light disk, screen pixels
disk_y     = 2;
disk_w     = 64;       // the disk is grown in from the top in 4 stages:
disk_h     = 16;       //   1 row -> 2 rows -> 3 rows -> all 8 rows
disk_on    = false;    // true between SPOT_START_FRAME and SPOT_END_FRAME
mural_on   = false;    // true once the colourful title mural replaces the stencil
mural_fade = 0;        // 0..1 fade-in of that mural (steps 892 onward)
scene_done = false;    // true once we hand over to the title room

//=============================================================================
// scr_init.gml
// GameMaker Studio 1.4.1760  |  Chip 'n Dale Rescue Rangers 2 recreation
//-----------------------------------------------------------------------------
// WHAT THIS IS:
//   A single "settings" script. Every physics / gameplay constant for the
//   whole game lives here, so you can tune the feel in ONE place.
//   All values are in NES units: pixels per step (the game runs at 60 steps
//   per second, exactly like the original NES at ~60 fps).
//
// HOW TO USE IT:
//   1. Create a Script resource named  scr_init
//   2. Paste this whole file into it.
//   3. Call  scr_init();  from the GAME START event (not Create!) so the
//      globals and the ST enum exist before any instance is created.
//      In the IDE: right-click your object -> Add Event -> Other -> Game Start.
//
// WHY GLOBALS?
//   GMS 1.4 has no "structs" or "config objects" like newer versions, so
//   global.* variables are the clean, modern way to share settings between
//   every object. This keeps the code readable and easy to tweak.
//=============================================================================

//------------------------------------------------------------------
// Screen / timing (matches the NES exactly)
//------------------------------------------------------------------
global.VIEW_W      = 256;    // NES visible width  (pixels)
global.VIEW_H      = 240;    // NES visible height (pixels)
global.ROOM_SPEED  = 60;     // steps per second (NTSC NES = ~60 fps)

//------------------------------------------------------------------
// Tile size (the NES world is built from 8x8 tiles)
//------------------------------------------------------------------
global.TILE = 8;

//------------------------------------------------------------------
// PLAYER physics  (Chip / Dale)  -- see PHYSICS_REFERENCE.md
//------------------------------------------------------------------
global.P_WALK_SPEED   = 1.5;   // max horizontal speed (px/step). 1.5 = 1,2,1,2...
global.P_ACCEL        = 0.5;   // how fast we reach walk speed (snappy = high)
global.P_FRICTION     = 0.5;   // how fast we stop when no input
global.P_JUMP_VEL     = -5.5;  // initial upward velocity when jumping
global.P_GRAVITY      = 0.30;  // downward acceleration each step
global.P_MAX_FALL     = 4.5;   // terminal (max) falling speed
global.P_JUMP_HEIGHT  = 43;    // approx. jump height in pixels (original value)

// Animation timing (in steps). image_speed = 1 / this value.
global.P_WALK_ANIM    = 4;     // walk cycle: new frame every 4 steps (15 fps)
global.P_ENEMY_ANIM   = 6;     // enemy walk cycle timing

//------------------------------------------------------------------
// ENEMY physics
//------------------------------------------------------------------
global.E_WALK_SPEED   = 0.75;  // patrol speed (px/step)
global.E_GRAVITY      = 0.30;  // same gravity as the player
global.E_MAX_FALL     = 4.5;

//------------------------------------------------------------------
// PROJECTILES / THROWABLES
//------------------------------------------------------------------
global.THROW_SPEED    = 3.0;   // horizontal throw speed (px/step)
global.BLOCK_GRAVITY  = 0.15;  // gentle arc for thrown blocks
global.ACORN_GRAVITY  = 0.10;  // acorns fly flatter than blocks

//------------------------------------------------------------------
// GAME RULES (original values)
//------------------------------------------------------------------
global.START_LIVES    = 3;     // Chip & Dale each start with 3 lives
global.START_HEALTH   = 3;     // ... and 3 hearts (hits) per life
global.SCORE_FLOWER   = 500;   // points for a flower
global.SCORE_STAR     = 1000;  // points for a star

//------------------------------------------------------------------
// States (used by the player / enemy state machines)
// Using an enum keeps the code self-documenting: state = ST.WALK
//------------------------------------------------------------------
enum ST {
    IDLE,      // standing still
    WALK,      // running on the ground
    JUMP,      // rising after a jump
    FALL,      // falling
    DUCK,      // crouching
    PICKUP,    // bending to pick something up
    THROW,     // throwing a held object
    HURT,      // knocked back / invincible frames
    DEAD       // game over / respawn
}

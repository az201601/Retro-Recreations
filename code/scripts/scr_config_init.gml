/// scr_config_init  (GameMaker: Studio 1.4)
// Global constants + NES palette. Kept as a script (not an object) so any
// room can be booted directly while debugging.
// ============================================================================
if (variable_global_exists("RR2_VERSION")) exit;   // idempotent

global.RR2_VERSION = "0.1";

// --- display --------------------------------------------------------------
global.NES_W      = 256;    // NES visible width
global.NES_H      = 240;    // NES visible height
global.VIEW_SCALE = 3;      // 3x = 768x720 window

// --- gameplay tuning ------------------------------------------------------
global.GRAVITY      = 0.28;
global.MAX_FALL     = 4.2;
global.RUN_SPEED    = 1.55;
global.RUN_ACCEL    = 0.30;
global.RUN_FRICTION = 0.42;
global.AIR_ACCEL    = 0.22;
global.JUMP_SPEED   = -4.2;
global.JUMP_CUT     = 0.45;
global.COYOTE_TIME  = 6;
global.JUMP_BUFFER  = 6;
global.THROW_SPEED  = 2.6;
global.THROW_LIFE   = 150;
global.PICKUP_SPEED = 3.4;

// --- draw layers (depth) ---------------------------------------------------
global.LAYER_BG      = -1000;
global.LAYER_GROUND  = -500;
global.LAYER_PICKUP  = -100;
global.LAYER_PLAYER  = 0;
global.LAYER_ENEMY   = 0;
global.LAYER_FX      = 100;
global.LAYER_HUD     = 1000;

// --- NES palette (index -> BGR, see scr_nes_color) ------------------------
// The extracted PNGs already carry the final colours, this is only needed for
// runtime recolouring / debug tinting.
global.NES_PAL = ds_map_create();
global.NES_PAL[?  0] = $7C7C7C;  global.NES_PAL[?  1] = $0000FC;
global.NES_PAL[?  2] = $0000BC;  global.NES_PAL[?  3] = $4428BC;
global.NES_PAL[?  4] = $940084;  global.NES_PAL[?  5] = $A80020;
global.NES_PAL[?  6] = $A81000;  global.NES_PAL[?  7] = $881400;
global.NES_PAL[?  8] = $503000;  global.NES_PAL[?  9] = $007800;
global.NES_PAL[? 10] = $006800;  global.NES_PAL[? 11] = $005800;
global.NES_PAL[? 12] = $004058;  global.NES_PAL[? 13] = $000000;
global.NES_PAL[? 16] = $BCBCBC;  global.NES_PAL[? 17] = $0078F8;
global.NES_PAL[? 18] = $0058F8;  global.NES_PAL[? 19] = $6844FC;
global.NES_PAL[? 20] = $D800CC;  global.NES_PAL[? 21] = $E40058;
global.NES_PAL[? 22] = $F83800;  global.NES_PAL[? 23] = $E45C10;
global.NES_PAL[? 24] = $AC7C00;  global.NES_PAL[? 25] = $00B800;
global.NES_PAL[? 26] = $00A800;  global.NES_PAL[? 27] = $00A844;
global.NES_PAL[? 28] = $008888;  global.NES_PAL[? 29] = $000000;
global.NES_PAL[? 32] = $F8F8F8;  global.NES_PAL[? 33] = $3CBCFC;
global.NES_PAL[? 34] = $6888FC;  global.NES_PAL[? 35] = $9878F8;
global.NES_PAL[? 36] = $F878F8;  global.NES_PAL[? 37] = $F85898;
global.NES_PAL[? 38] = $F87858;  global.NES_PAL[? 39] = $FCA044;
global.NES_PAL[? 40] = $F8B800;  global.NES_PAL[? 41] = $B8F818;
global.NES_PAL[? 42] = $58D854;  global.NES_PAL[? 43] = $58F898;
global.NES_PAL[? 44] = $00E8D8;  global.NES_PAL[? 45] = $787878;
global.NES_PAL[? 48] = $FCFCFC;  global.NES_PAL[? 49] = $A4E4FC;
global.NES_PAL[? 50] = $B8B8F8;  global.NES_PAL[? 51] = $D8B8F8;
global.NES_PAL[? 52] = $F8B8F8;  global.NES_PAL[? 53] = $F8A4C0;
global.NES_PAL[? 54] = $F0D0B0;  global.NES_PAL[? 55] = $FCE0A8;
global.NES_PAL[? 56] = $F8D878;  global.NES_PAL[? 57] = $D8F878;
global.NES_PAL[? 58] = $B8F8B8;  global.NES_PAL[? 59] = $B8F8D8;
global.NES_PAL[? 60] = $00FCFC;  global.NES_PAL[? 61] = $F8D8F8;

// ============================================================
// scr_init.gml  --  global constants for the CnD RR2 recreation
// Call this ONCE (e.g. from a persistent controller's Create event).
// All values are measured from the real NES game at 60 fps
// (Nestopia RAM watch + frame-by-frame position logging).
// ============================================================

// --- Physics (pixels per frame at room_speed=60) ---
global.walk_speed   = 2.0;    // horizontal speed while holding left/right
global.jump_v0      = -7.2;   // initial jump velocity (up)
global.gravity_hold = 0.38;   // gravity while A/jump is held AND still rising
global.gravity_fall = 1.0;    // gravity otherwise (falling / jump released)
global.max_fall     = 6.0;    // terminal fall velocity
global.jump_hold_max = 20;    // frames the low gravity can be held

// Measured jump profiles (for tuning reference):
//   tap A (2f):  apex 14 px, airtime ~11 frames
//   hold A(12f): apex 58 px, airtime ~31 frames
//   hold A(20f): apex 67 px, airtime ~39 frames

// --- Player size / collision box (measured from OAM composition) ---
global.player_w = 16;
global.player_h = 26;      // feet-anchored sprite: hat top .. shoes

// --- Level ---
// collision grid is loaded from collision.csv (32 cols x 30 rows),
// 1 = solid, 0 = empty. Cell size 8 px (NES tile size).
global.tile_size = 8;
global.level_w_tiles = 32;
global.level_h_tiles = 30;

// --- Camera ---
// The NES camera keeps the player near screen centre-x with a small
// dead zone; approximate as: cam = clamp(player.x - 128, 0, room_w-256)
global.cam_lead = 128;

// --- Gameplay ---
global.max_hearts = 3;

// --- Stage screens (assets/stage1/screen_NN.png, 256 px each) ---
global.screens = 1;   // raise as you import more panorama screens

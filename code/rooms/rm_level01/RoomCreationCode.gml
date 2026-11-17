/// rm_level01 - Room Creation Code
// Stage 1: the burger-counter house (Chip 'n Dale RR2, chapter 1).
//
// Author the room from assets_vec/backgrounds/level01:
//   screen_00.png   256x240 background  ->  GMS background "bg_level01"
//   tileset.png     16x16 metatiles      (optional real tile layer)
//   collision.json  the platform data used below
//
// Room settings in GMS 1.4:
//   Size        256 x 240, speed 60
//   Views       none (the stage is a single screen, like the NES)
//   Backgrounds bg_level01, depth 1000, "Stretch" off
//   Instances   obj_gamecontroller (persistent, from the title room)
// ============================================================================

global.game_state = "play";
global.stage      = 1;

// ---- colour of the level art ---------------------------------------------
// NES palette slots used by level01 (from info.json), handy for HUD text and
// for matching the background when it is drawn procedurally.
global.level_palette = [make_colour_rgb(0, 0, 0),
                        make_colour_rgb(248, 56, 0),
                        make_colour_rgb(184, 248, 24),
                        make_colour_rgb(248, 248, 248)];

// ---- platforms -----------------------------------------------------------
// x, y = top-left of the drawn surface, w, h = size.  Values come from
// assets_vec/backgrounds/level01/collision.json (y is the stand-on line).
scr_platform_add(128,  80, 128, 16);   // upper shelf
scr_platform_add( 65, 160, 174, 16);   // long table
scr_platform_add( 11, 192,  68, 16);   // low bench

// ---- player + hud --------------------------------------------------------
instance_create(50, 160, obj_player);
instance_create( 0,   0, obj_hud);

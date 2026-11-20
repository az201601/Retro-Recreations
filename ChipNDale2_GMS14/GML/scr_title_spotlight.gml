//=============================================================================
// scr_title_spotlight.gml
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
//-----------------------------------------------------------------------------
// WHAT THIS IS
//   The settings script for the ATTRACT SCENE that plays immediately after the
//   copyright screen: a black screen with a circular "spotlight" sweeping
//   around behind a 1-bit black stencil of the title mural.
//
//   Every number here was MEASURED from the running ROM (see tools/nes_emu.py
//   and tools/extract_spotlight_scene.py). Frame numbers are NTSC video frames
//   at ~60 fps, so they map 1:1 onto GMS steps at room speed 60.
//
// HOW TO USE IT
//   1. Create a Script resource named  scr_title_spotlight
//   2. Paste this whole file into it.
//   3. Call  scr_title_spotlight();  from the GAME START event, right after
//      scr_init();  so the globals exist before any instance is created.
//   4. Put  obj_title_spotlight  in the title room. Its three events live in
//          obj_title_spotlight_Create.gml
//          obj_title_spotlight_Step.gml
//          obj_title_spotlight_Draw.gml
//
//-----------------------------------------------------------------------------
// HOW THE SCENE REALLY WORKS  (this was verified against the running ROM -
//                              do not "simplify" it based on screenshots)
//-----------------------------------------------------------------------------
//   There are TWO different backgrounds in this sequence and it is easy to
//   mix them up:
//
//   1. THE SPOTLIGHT STENCIL (steps 0 - 885)
//      A separate 32x30 nametable of 45 tiles taken from CHR bank 31. It uses
//      ONLY colour indices 0 and 1 with the palette  $0F $0F $0F $20, so it
//      renders as a 1-bit stencil: colour 0 = the NES backdrop (black),
//      colour 1 = black.
//
//      Running the ROM at step 480 and dumping that nametable shows it is a
//      stencil silhouette of the title mural itself - Chip, Dale, the logo and
//      the brick frame all appear as solid black shapes against the backdrop.
//      (See EXTRACTED/spotlight/spotlight_mask.png.)
//
//   2. THE TITLE MURAL (step 886 onward)
//      A completely different nametable (241 tiles, CHR bank 30) with the
//      colourful brick/star/logo art. This is backdrop_bricks.png.
//
//   The light disk is 32 hardware sprites flagged "behind background". The PPU
//   therefore only shows the disk on colour index 0 and hides it under colour
//   index 1. So the disk is glimpsed everywhere EXCEPT where the stencil's
//   black mural silhouette sits - which is what makes the logo "appear"
//   gradually as the disk sweeps over it.
//
//   Verified numerically on step 480: of the disc pixels that landed on
//   background colour 0, 2198/2198 were visible; of those that landed on
//   colour 1, 0/738 were visible.
//
//   GameMaker has no "sprite behind the background" layer, so we reproduce it
//   by drawing in this order:
//        1. the light disk            spr_spotlight_disk
//        2. the stencil ON TOP        spr_spotlight_mask
//   spr_spotlight_mask is the stencil with every colour-0 pixel transparent and
//   every colour-1 pixel opaque black. That recipe was checked against the ROM
//   and is 100% pixel-identical: 0 differing pixels out of 61440.
//
//   At step 886 the stencil is replaced by the colourful mural, whose palette
//   is then faded up over 18 steps (finishing at step 904). That reveal is the
//   title screen proper; this object hands over to it.
//
// ASSETS THIS SCRIPT EXPECTS
//   Sprites (in EXTRACTED/spotlight/; origin Top Left; interpolation OFF):
//     spr_spotlight_disk     64x63     spotlight_circle.png
//     spr_spotlight_mask    256x240    spotlight_mask.png   (the 1-bit stencil)
//     spr_spotlight_wall    256x240    backdrop_bricks.png  (the mural)
//=============================================================================

//-----------------------------------------------------------------------------
// SCENE TIMING  (measured, in steps)
//-----------------------------------------------------------------------------
global.SPOT_START_FRAME  = 212;   // first step the light disk is on screen
global.SPOT_END_FRAME    = 885;   // last step the light disk is on screen
global.SPOT_MURAL_FRAME  = 886;   // step the colourful title mural is swapped in
global.SPOT_MURAL_STEPS  = 18;    // steps the mural palette takes to fade in
global.SPOT_SCENE_END    = 905;   // step the scene is finished

// Where the scene goes when it finishes. Point this at your title/menu room.
global.SPOT_NEXT_ROOM    = rm_title_menu;

//-----------------------------------------------------------------------------
// NES PALETTE -> GameMaker colours
//-----------------------------------------------------------------------------
// Spotlight backdrop palette (all four background palettes are identical):
//     $0F $0F $0F $20
//       $0F = #545454 (the NES "black")
//       $20 = #FCFCFC (white - the colour-3 slot, which the stencil never
//                      actually uses: it only ever writes indices 0 and 1)
//
// The light disk uses sprite palette 2: $00 $36 $16 $26.
// $00 is the sprites' transparent index, so the disk is $36 / $16 / $26.
//
// The title mural (after the swap) uses:
//   BG0: $0F $17 $37 $20     BG1: $0F $17 $05 $20
//   BG2: $0F $15 $32 $05     BG3: $0F $17 $27 $20
//-----------------------------------------------------------------------------
global.SPOT_COL_BLACK    = make_color_rgb( 84,  84,  84);  // $0F
global.SPOT_COL_WHITE    = make_color_rgb(252, 252, 252);  // $20
global.SPOT_COL_BRICK    = make_color_rgb(120,  60,   0);  // $17
global.SPOT_COL_TAN      = make_color_rgb(216, 136,  32);  // $37
global.SPOT_COL_PLUM     = make_color_rgb( 92,   0,  48);  // $05
global.SPOT_COL_MAGENTA  = make_color_rgb(160,  20, 100);  // $15
global.SPOT_COL_BLUE     = make_color_rgb( 76,  50, 236);  // $32
global.SPOT_COL_DKBROWN  = make_color_rgb(120,  82,   0);  // $27
global.SPOT_COL_DISC     = make_color_rgb(236, 106, 100);  // $36 body
global.SPOT_COL_DISC_RIM = make_color_rgb(152,  34,  32);  // $26 outer rim

//-----------------------------------------------------------------------------
// THE MEASURED DISK PATH
//-----------------------------------------------------------------------------
// The disk is 64 wide x 63 tall. All coordinates are the TOP-LEFT corner of
// the unclipped disk in screen pixels.
//
//   step range   motion
//   ----------   ------------------------------------------------------------
//    212 -  219   x = 160           y = 2  + 2*(f-212)   only 1 of 8 rows on
//    220 -  226   x = 160           y = 2  + 2*(f-220)   only 2 of 8 rows on
//    227 -  234   x = 160           y = 1  + 2*(f-227)   only 3 of 8 rows on
//    235 -  315   x = 160           y = 1  + 2*(f-235)   full disk, falling
//    316 -  411   diagonal up-left   (SPOT_DIAG_X and SPOT_DIAG_Y)
//    412 -  475   x = 30  + 2*(f-412)   y = 29            straight right
//    476 -  522   diagonal down-left (SPOT_DIAG_X and SPOT_DIAG_Y2)
//    523 -  596   x = 90  - 2*(f-523)   y = 95            straight left
//    597 -  705   x = -56,              y = 95            off screen, alive
//    706 -  785   x = -56 + 2*(f-706)   y = 73            re-enters from left
//    786 -  801   x = 98  - 4*(f-786)   y = 73            fast reversal
//    802 -  885   x = 38,               y = 73            parks on the logo
//
// The diagonals are NOT a float speed. The ROM emits a repeating integer
// pattern, so we copy the pattern instead of accumulating a float - that keeps
// the path bit-exact however long the scene runs. Verified: these tables
// reproduce all 566 measured frames with zero mismatches.
//   diag 1 (up-left)   both axes: [-1,-2,-1,-1,-2,-1,-1,-2]  (sum -11 per 8)
//   diag 2 (down-left) x axis   : [-1,-2,-1,-1,-2,-1,-1,-2]
//                      y axis   : [+1,+2,+1,+1,+2,+1,+2,+1]  (sum +11 per 8)
//-----------------------------------------------------------------------------
global.SPOT_DIAG_X  = [-1, -2, -1, -1, -2, -1, -1, -2];
global.SPOT_DIAG_Y  = [-1, -2, -1, -1, -2, -1, -1, -2];
global.SPOT_DIAG_Y2 = [ 1,  2,  1,  1,  2,  1,  2,  1];

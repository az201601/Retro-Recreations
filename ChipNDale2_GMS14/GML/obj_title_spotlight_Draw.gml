//=============================================================================
// obj_title_spotlight  --  Draw event
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
//-----------------------------------------------------------------------------
// Draw order is the whole trick:
//
//      1. black screen
//      2. the light disk
//      3. the stencil ON TOP of the disk
//
// spr_spotlight_mask is the scene's 1-bit stencil (a black silhouette of the
// title mural) with every background colour-0 pixel at alpha 0 and every
// colour-1 pixel opaque black. The disk therefore shows through everywhere
// except where the silhouette is - which is exactly what the NES does with its
// "behind background" sprites.
//
// This recipe was verified against the running ROM at frame 480 and is
// 100% pixel-identical: 0 differing pixels out of 61440.
//=============================================================================

// In the IDE this object should have a Draw event only.
// Do NOT add a Draw Begin / Draw End.

//------------------------------------------------------------- 1. black screen
draw_clear(global.SPOT_COL_BLACK);

//--------------------------------------------------------------- 2. light disk
if (disk_on) {
    var sw = min(disk_w, sprite_get_width(spr_spotlight_disk));
    var sh = min(disk_h, sprite_get_height(spr_spotlight_disk));
    draw_sprite_part(spr_spotlight_disk, 0, 0, 0, sw, sh, disk_x, disk_y);
}

//--------------------------------------------- 3. the stencil, on top of it all
if (mural_on) {
    // The scene has handed over to the colourful title mural by now.
    draw_sprite_ext(spr_spotlight_wall, 0, 0, 0, 1, 1, 0, c_white, mural_fade);
} else {
    draw_sprite(spr_spotlight_mask, 0, 0, 0);
}

/// obj_chip_dale_silhouette — Create Event (OPTIONAL ALTERNATIVE TO -10 TILE LAYER)
// ============================================================================
// You have two ways to place Chip & Dale's silhouette in rm_spotlight_intro:
//
//   Method A (Pure Room Editor Tiles — matches your workflow):
//     1. Tile the entire 16x15 grid (256x240) at Tile Layer Depth = 0 using
//        Brick Wall Tiles 1 & 2 from `ts_spotlight_mask_16x16.png`.
//     2. On Tile Layer Depth = -10, paint the 6x4 block (grid X = 2..7, Y = 5..8,
//        pixel X = 32..127, Y = 80..143) using Silhouette Tiles 3..21.
//     `obj_spotlight_beam` automatically calls `tile_layer_hide(-10)` in Phase 1
//     and `tile_layer_show(-10)` in Phase 2!
//
//   Method B (Reusable Object — if you don't want to paint 24 silhouette tiles):
//     1. Only tile the repeating Brick Wall (Tiles 1 & 2) at Depth = 0.
//     2. Assign `spr_chip_dale_silhouette_mask.png` (Origin 0, 0) to
//        `obj_chip_dale_silhouette` with Depth = -10, and place it at (x = 32, y = 80).
//     `obj_spotlight_beam` automatically toggles `obj_chip_dale_silhouette.visible`!
// ============================================================================

image_speed = 0;
visible     = false; // Revealed automatically by obj_spotlight_beam at Phase 2 (frame 477)

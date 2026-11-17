/// obj_spotlight_beam — Create Event
// ============================================================================
// Scene 01: Pre-Title Spotlight Intro (right after Copyright screen)
// Target: GameMaker Studio 1.4.1760 (Room size: 256x240, Room speed: 60)
//
// Object Setup in GMS 1.4.1760:
//   - Name:   obj_spotlight_beam
//   - Sprite: spr_spotlight_beam   (imported from spr_spotlight_beam_strip4.png,
//                                   4 subimages of 64x64, Origin X = 32, Y = 32)
//   - Depth:  100                  (BEHIND the 16x16 mortar/silhouette tiles!
//                                   Paint your Brick Wall tiles at Depth 0 and
//                                   Silhouette tiles at Depth -10)
//   - Place 1 instance anywhere in rm_spotlight_intro (Create Event sets x, y)
// ============================================================================

image_speed = 0;
image_index = 3;      // Start at dimmest NES palette step during initial fade-in
visible     = true;

// Frame counter matching NES hardware timeline (t = 0 corresponds to NES Frame 176)
timer     = 0;
skipping  = false;
skip_step = 0;

// Exact 8.8 signed fixed-point coordinates & velocity from NES RAM ($0314/$02FC)
pos_x  = 192;
sub_x  = 0;
pos_y  = -62;
sub_y  = 0;
vx_256 = 0;
vy_256 = 0;

// Apply initial screen coordinates (NES OAM renders sprites at Y + 1 scanline)
x = pos_x;
y = pos_y + 1;

// Hide the Phase 2 silhouette tile layer (Depth -10) during Phase 1!
// When you paint the 24 Chip & Dale silhouette 16x16 tiles in the GMS Room Editor,
// set their Tile Layer Depth to -10 (while the full 256x240 Brick Wall tiles are at Depth 0).
tile_layer_hide(-10);

// Optional fallback: if you prefer placing obj_chip_dale_silhouette instead of a -10 tile layer,
// hide it during Phase 1 as well:
if (instance_exists(obj_chip_dale_silhouette)) {
    obj_chip_dale_silhouette.visible = false;
}

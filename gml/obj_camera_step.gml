// obj_camera -- Step event (place one instance; it drives the view)
// Approximates the NES camera: player held near screen centre-x,
// clamped to the level.  Vertical view is fixed (the kitchen never scrolls
// vertically in the first section).

var px;
px = obj_player.x;
view_xview[0] = clamp(px - global.cam_lead, 0, room_width - 256);
view_yview[0] = 0;

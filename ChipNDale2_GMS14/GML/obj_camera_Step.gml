//=============================================================================
// obj_camera  --  Step event
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Step event of  obj_camera.
// Centres the view on the player, clamped so we never show outside the room.
//=============================================================================

if (instance_exists(target)) {
    var tx = target.x - view_wview / 2;
    var ty = target.y - view_hview / 2;
    // Clamp to room bounds (if the room is smaller than the view, centre it).
    view_xview = clamp(tx, 0, max(0, room_width - view_wview));
    view_yview = clamp(ty, 0, max(0, room_height - view_hview));
}

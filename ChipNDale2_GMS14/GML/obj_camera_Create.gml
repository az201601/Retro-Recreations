//=============================================================================
// obj_camera  --  Create event
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Create event of an object named  obj_camera.
// The camera follows the player and keeps the 256x240 view inside the room.
// (Make sure the room's View tab has view enabled, 256x240.)
//=============================================================================

target = obj_player; // who to follow
view_enabled = true;
view_wview = global.VIEW_W;   // 256
view_hview = global.VIEW_H;   // 240

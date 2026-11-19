//=============================================================================
// obj_block  --  Create event   (throwable crate / barrel / ball)
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Create event of an object named  obj_block.
//=============================================================================

hsp = 0;
vsp = 0;
held = false;        // true while the player is carrying it
thrown = false;      // true once it has been thrown at least once
bbox_left_offset  = 7;
bbox_right_offset = 7;
bbox_top_offset   = 7;
bbox_bottom_offset = 0;

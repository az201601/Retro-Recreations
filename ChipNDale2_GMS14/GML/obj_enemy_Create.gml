//=============================================================================
// obj_enemy  --  Create event   (patrol enemy, e.g. the mouse/rat)
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Create event of an object named  obj_enemy.
//=============================================================================

hsp = global.E_WALK_SPEED;   // start walking right
vsp = 0;
facing = 1;
on_ground = false;
bbox_left_offset  = 5;
bbox_right_offset = 5;
bbox_top_offset   = 12;
bbox_bottom_offset = 0;
image_speed = 0;
anim_timer = 0;
anim_frame = 0;

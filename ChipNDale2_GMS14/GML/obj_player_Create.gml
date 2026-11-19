//=============================================================================
// obj_player  --  Create event
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
//-----------------------------------------------------------------------------
// Paste this into the Create event of an object named  obj_player.
// This sets up all the variables the Step event uses.
//=============================================================================

//--- Physics state ---
hsp = 0;                 // horizontal speed (px/step)
vsp = 0;                 // vertical speed   (px/step)
facing = 1;              // 1 = right, -1 = left
on_ground = false;       // true while standing on a floor

//--- State machine ---
state = ST.IDLE;         // current state (see enum in scr_init)
state_timer = 0;         // counts steps spent in the current state
held_object = noone;     // the block/acorn the player is carrying (if any)

//--- Bounding box offsets (so collision matches the sprite, not the origin) ---
// The sprite's origin is its centre-bottom. These are half-width / heights.
bbox_left_offset  = 5;   // pixels from centre to the left edge
bbox_right_offset = 5;   // pixels from centre to the right edge
bbox_top_offset   = 14;  // pixels from centre up to the head
bbox_bottom_offset = 0;  // feet are at the origin

//--- Health / lives (per-player, like the original) ---
health = global.START_HEALTH;
lives  = global.START_LIVES;
invincible_timer = 0;    // >0 means "ignore hits" (brief mercy period)

//--- Animation ---
image_speed = 0;         // we drive animation manually for NES-accurate timing
anim_timer = 0;
anim_frame = 0;

//--- Which character? (0 = Chip, 1 = Dale) -- set by the character select ---
character = 0;

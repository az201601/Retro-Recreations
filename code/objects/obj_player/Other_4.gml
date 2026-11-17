/// obj_player - Other / Room Start
// Runs after the room is created: place on the ground, reset motion.
// ============================================================================
hsp       = 0;
vsp       = 0;
on_ground = false;
jumping   = false;
carrying  = noone;
image_xscale = 1;
dir = 1;

// snap down to the floor so the player never spawns inside geometry
var _i;
_i = 0;
while (!place_meeting(x, y + 1, obj_ground) && y < room_height && _i < 240) {
    y += 1;
    _i += 1;
}
